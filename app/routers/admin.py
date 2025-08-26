from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
import csv
import io
import logging
from app.services.bigquery_service import BigQueryService
from app.models.coin import Coin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")
bigquery_service = BigQueryService()

@router.post("/coins/upload")
async def upload_coins_csv(file: UploadFile = File(...)):
    """Upload and process CSV file for coin import."""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        uploaded_coins = []
        
        expected_headers = ['type', 'year', 'country', 'series', 'value', 'id', 'image', 'feature', 'volume']
        
        # Validate headers
        if not all(header in csv_reader.fieldnames for header in expected_headers):
            missing_headers = [h for h in expected_headers if h not in csv_reader.fieldnames]
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required CSV headers: {', '.join(missing_headers)}"
            )
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Map CSV columns to coin model
                coin_data = {
                    'coin_type': row['type'],
                    'year': int(row['year']),
                    'country': row['country'],
                    'series': row['series'],
                    'value': float(row['value']),
                    'coin_id': row['id'],
                    'image_url': row['image'] if row['image'] else None,
                    'feature': row['feature'] if row['feature'] else None,
                    'volume': row['volume'] if row['volume'] else None,
                    'owners': [],
                    'is_owned': False
                }
                
                # Validate coin data
                coin = Coin(**coin_data)
                uploaded_coins.append(coin.dict())
                
            except Exception as e:
                logger.error(f"Error processing row {row_num}: {str(e)}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error processing row {row_num}: {str(e)}"
                )
        
        if not uploaded_coins:
            raise HTTPException(status_code=400, detail="No valid coins found in CSV file")
        
        # Check for duplicates against database
        coin_ids = [coin['coin_id'] for coin in uploaded_coins]
        existing_coins = await bigquery_service.get_existing_coin_ids(coin_ids)
        existing_ids = set(existing_coins)
        
        # Categorize coins
        new_coins = []
        duplicate_coins = []
        
        for coin in uploaded_coins:
            if coin['coin_id'] in existing_ids:
                coin['status'] = 'duplicate'
                coin['selected_for_import'] = False
                duplicate_coins.append(coin)
            else:
                coin['status'] = 'new'
                coin['selected_for_import'] = True
                new_coins.append(coin)
        
        return {
            "success": True,
            "total_uploaded": len(uploaded_coins),
            "new_coins": len(new_coins),
            "duplicates": len(duplicate_coins),
            "coins": new_coins + duplicate_coins
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CSV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/coins/import")
async def import_selected_coins(coins: List[Dict[str, Any]]):
    """Import selected coins to the database."""
    try:
        # Filter only selected coins that are new (not duplicates)
        coins_to_import = [
            coin for coin in coins 
            if coin.get('selected_for_import', False) and coin.get('status') == 'new'
        ]
        
        if not coins_to_import:
            raise HTTPException(status_code=400, detail="No coins selected for import")
        
        # Validate each coin before import
        validated_coins = []
        for coin in coins_to_import:
            try:
                # Remove import-specific fields
                coin_data = {k: v for k, v in coin.items() 
                           if k not in ['status', 'selected_for_import']}
                validated_coin = Coin(**coin_data)
                validated_coins.append(validated_coin.dict())
            except Exception as e:
                logger.error(f"Validation error for coin {coin.get('coin_id', 'unknown')}: {str(e)}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Validation error for coin {coin.get('coin_id', 'unknown')}: {str(e)}"
                )
        
        # Import to BigQuery
        imported_count = await bigquery_service.import_coins(validated_coins)
        
        return {
            "success": True,
            "imported_count": imported_count,
            "message": f"Successfully imported {imported_count} coins"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing coins: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing coins: {str(e)}")

@router.get("/coins/export")
async def export_coins_csv():
    """Export all coins to CSV file sorted by year, series, country."""
    try:
        # Get all coins from BigQuery sorted by year, series, country
        all_coins = await bigquery_service.get_all_coins_for_export()
        
        if not all_coins:
            raise HTTPException(status_code=404, detail="No coins found to export")
        
        # Create CSV content
        output = io.StringIO()
        fieldnames = ['type', 'year', 'country', 'series', 'value', 'id', 'image', 'feature', 'volume']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write coin data
        for coin in all_coins:
            writer.writerow({
                'type': coin.get('coin_type', ''),
                'year': coin.get('year', ''),
                'country': coin.get('country', ''),
                'series': coin.get('series', ''),
                'value': coin.get('value', ''),
                'id': coin.get('coin_id', ''),
                'image': coin.get('image_url', ''),
                'feature': coin.get('feature', ''),
                'volume': coin.get('volume', '')
            })
        
        # Prepare the response
        csv_content = output.getvalue()
        output.close()
        
        # Create streaming response
        response = StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type='text/csv',
            headers={"Content-Disposition": "attachment; filename=coins_export.csv"}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting coins: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting coins: {str(e)}")

@router.get("/coins/view")
async def view_coins(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    country: Optional[str] = None,
    coin_type: Optional[str] = None
):
    """Get coins for viewing in admin panel with pagination and filtering."""
    try:
        # Build filters
        filters = {}
        if country:
            filters['country'] = country
        if coin_type:
            filters['coin_type'] = coin_type
        
        # Get coins with filters and pagination
        coins_data = await bigquery_service.get_coins_for_admin_view(filters, limit, offset, search)
        
        # Get total count for pagination
        total_count = await bigquery_service.get_coins_count(filters, search)
        
        return {
            "success": True,
            "coins": coins_data,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error viewing coins: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error viewing coins: {str(e)}")

@router.get("/coins/filter-options")
async def get_coins_filter_options():
    """Get available filter options for coins (countries, etc)."""
    try:
        filter_options = await bigquery_service.get_coins_filter_options()
        
        return {
            "success": True,
            "countries": filter_options.get("countries", []),
            "coin_types": ["RE", "CC"]
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")
