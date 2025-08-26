from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
import csv
import io
import logging
from datetime import datetime
from app.services.bigquery_service import BigQueryService
from app.models.coin import Coin
from app.models.history import History, HistoryCreate

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


@router.post("/coins/reset")
async def reset_catalog(recreate: bool = True):
    """Delete and recreate the catalog table. This is destructive and requires caution."""
    try:
        # Basic safety: require explicit recreate flag
        if not recreate:
            raise HTTPException(status_code=400, detail="Missing recreate flag")

        result = await bigquery_service.reset_catalog_table()

        if result.get('success'):
            return {"success": True, "message": result.get('message', 'Catalog reset successfully')}
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to reset catalog'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting catalog: {str(e)}")

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


# History endpoints
@router.post("/history/upload")
async def upload_history_csv(file: UploadFile = File(...)):
    """Upload and process CSV file for history import."""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        uploaded_history = []
        
        expected_headers = ['name', 'id', 'date']
        
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
                # Parse date
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S')
                
                # Map CSV columns to history model
                history_data = {
                    'name': row['name'],
                    'id': row['id'],  # coin_id
                    'date': date_obj
                }
                
                uploaded_history.append(history_data)
                
            except ValueError as e:
                logger.warning(f"Skipping row {row_num}: Invalid data - {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Skipping row {row_num}: {str(e)}")
                continue
        
        if not uploaded_history:
            raise HTTPException(status_code=400, detail="No valid history entries found in CSV")
        
        # Check for duplicates against existing data
        existing_history = await bigquery_service.get_all_history()
        existing_keys = {f"{h['name']}_{h['id']}_{h['date'].strftime('%Y-%m-%d %H:%M:%S')}" for h in existing_history}
        
        new_entries = []
        duplicate_entries = []
        
        for history in uploaded_history:
            key = f"{history['name']}_{history['id']}_{history['date'].strftime('%Y-%m-%d %H:%M:%S')}"
            if key in existing_keys:
                duplicate_entries.append({**history, 'status': 'duplicate'})
            else:
                new_entries.append({**history, 'status': 'new'})
        
        return {
            "success": True,
            "total_uploaded": len(uploaded_history),
            "new_entries": len(new_entries),
            "duplicate_entries": len(duplicate_entries),
            "data": new_entries + duplicate_entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing history CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@router.post("/history/import")
async def import_history_entries(history_data: List[Dict[str, Any]]):
    """Import selected history entries to BigQuery."""
    try:
        if not history_data:
            raise HTTPException(status_code=400, detail="No history data provided")
        
        # Convert to HistoryCreate objects and validate
        validated_history = []
        for item in history_data:
            try:
                # Ensure date is properly formatted
                if isinstance(item['date'], str):
                    item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                
                history_obj = HistoryCreate(**item)
                validated_history.append(history_obj)
            except Exception as e:
                logger.warning(f"Invalid history data: {item}. Error: {str(e)}")
                continue
        
        if not validated_history:
            raise HTTPException(status_code=400, detail="No valid history entries to import")
        
        # Import to BigQuery
        imported_count = await bigquery_service.import_history_batch(validated_history)
        
        return {
            "success": True,
            "imported_count": imported_count,
            "message": f"Successfully imported {imported_count} history entries"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing history: {str(e)}")


@router.get("/history/export")
async def export_history_csv():
    """Export all history entries to CSV."""
    try:
        # Get all history from BigQuery
        history_data = await bigquery_service.get_all_history()
        
        if not history_data:
            raise HTTPException(status_code=404, detail="No history entries found")
        
        # Create CSV content
        output = io.StringIO()
        fieldnames = ['name', 'id', 'date']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in history_data:
            # Format date for CSV
            date_str = entry['date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(entry['date'], datetime) else str(entry['date'])
            
            writer.writerow({
                'name': entry['name'],
                'id': entry['id'],
                'date': date_str
            })
        
        # Prepare response
        output.seek(0)
        
        def iter_csv():
            yield output.getvalue()
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=history_export.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting history: {str(e)}")


@router.get("/history/view")
async def view_history(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    name: Optional[str] = None,
    date_filter: Optional[str] = None
):
    """Get paginated history entries with optional filters."""
    try:
        # Build filters
        filters = {}
        if search:
            filters['search'] = search
        if name:
            filters['name'] = name
        if date_filter:
            filters['date_filter'] = date_filter
        
        # Get paginated data
        result = await bigquery_service.get_history_paginated(
            page=page,
            limit=limit,
            filters=filters
        )
        
        return {
            "success": True,
            "data": result['data'],
            "pagination": {
                "current_page": page,
                "total_pages": result['total_pages'],
                "total_count": result['total_count'],
                "limit": limit,
                "has_next": page < result['total_pages'],
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")


@router.get("/history/filter-options")
async def get_history_filter_options():
    """Get available filter options for history."""
    try:
        filter_options = await bigquery_service.get_history_filter_options()
        
        return {
            "success": True,
            "names": filter_options.get("names", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting history filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting history filter options: {str(e)}")
