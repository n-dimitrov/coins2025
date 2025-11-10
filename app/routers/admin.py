from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
import csv
import io
import logging
from datetime import datetime
from app.services.bigquery_service import BigQueryService, get_bigquery_service as get_bq_provider
from app.services.history_service import HistoryService
from app.models.coin import Coin
from app.models.history import History, HistoryCreate
from app.security import get_admin_dependency
import pandas as pd
import uuid
from datetime import timezone
from google.cloud import bigquery
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")
bigquery_service = get_bq_provider()
history_service = HistoryService()

# Admin authentication dependency
admin_required = get_admin_dependency()

@router.post("/coins/upload")
async def upload_coins_csv(file: UploadFile = File(...), _auth: bool = admin_required):
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
        
        # Check for duplicates against database and compare features
        coin_ids = [coin['coin_id'] for coin in uploaded_coins]
        existing_features = await bigquery_service.get_existing_coins_features(coin_ids)
        existing_ids = set(existing_features.keys())

        # Categorize coins. If coin_id exists but feature differs -> 'conflict'.
        new_coins = []
        duplicate_coins = []
        conflict_coins = []

        for coin in uploaded_coins:
            cid = coin['coin_id']
            if cid in existing_ids:
                # database feature may be None; normalize to empty string for comparison
                db_feature = existing_features.get(cid) or ''
                upload_feature = coin.get('feature') or ''
                if db_feature != upload_feature:
                    # Conflict: same id but different feature -> requires ID change or manual review
                    coin['status'] = 'conflict'
                    coin['existing_feature'] = db_feature
                    coin['selected_for_import'] = False
                    conflict_coins.append(coin)
                else:
                    coin['status'] = 'duplicate'
                    coin['existing_feature'] = db_feature
                    coin['selected_for_import'] = False
                    duplicate_coins.append(coin)
            else:
                coin['status'] = 'new'
                coin['selected_for_import'] = True
                new_coins.append(coin)
        
        # Return combined list: new first, then duplicates, then conflicts so UI can surface conflicts
        return {
            "success": True,
            "total_uploaded": len(uploaded_coins),
            "new_coins": len(new_coins),
            "duplicates": len(duplicate_coins),
            "conflicts": len(conflict_coins),
            "coins": new_coins + duplicate_coins + conflict_coins
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CSV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/coins/import")
async def import_selected_coins(coins: List[Dict[str, Any]], _auth: bool = admin_required):
    """Import selected coins to the database."""
    try:
        # Filter only selected coins (allow new or previously conflicted rows that were edited)
        coins_to_import = [
            coin for coin in coins 
            if coin.get('selected_for_import', False)
        ]
        
        if not coins_to_import:
            raise HTTPException(status_code=400, detail="No coins selected for import")
        
        # Validate selected coin_ids do not already exist in DB (prevent accidental overwrite)
        selected_ids = [coin.get('coin_id') for coin in coins_to_import]
        existing_ids = set(await bigquery_service.get_existing_coin_ids(selected_ids))
        if existing_ids:
            # Inform user which IDs are already present
            raise HTTPException(status_code=400, detail=f"The following coin_ids already exist: {', '.join(sorted(existing_ids))}")

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
async def export_coins_csv(_auth: bool = admin_required):
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
    coin_type: Optional[str] = None,
    _auth: bool = admin_required
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
async def reset_catalog(recreate: bool = True, _auth: bool = admin_required):
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


@router.post("/history/reset")
async def reset_history(recreate: bool = True, _auth: bool = admin_required):
    """Delete and recreate the history table. Destructive operation."""
    try:
        if not recreate:
            raise HTTPException(status_code=400, detail="Missing recreate flag")

        result = await bigquery_service.reset_history_table()

        if result.get('success'):
            return {"success": True, "message": result.get('message', 'History reset successfully')}
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to reset history'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting history: {str(e)}")


@router.post("/clear-cache")
async def clear_service_cache(_auth: bool = admin_required):
    """Clear the BigQuery service cache (admin utility to force fresh queries)."""
    try:
        bigquery_service.clear_cache()
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/coins/filter-options")
async def get_coins_filter_options(_auth: bool = admin_required):
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
async def upload_history_csv(file: UploadFile = File(...), _auth: bool = admin_required):
    """Upload and process CSV file for history import - using HistoryService."""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse CSV using pandas
        df = pd.read_csv(io.StringIO(content_str))
        
        # Validate required columns
        expected_headers = ['name', 'id', 'date']
        if not all(header in df.columns for header in expected_headers):
            missing_headers = [h for h in expected_headers if h not in df.columns]
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required CSV headers: {', '.join(missing_headers)}"
            )
        
        logger.info(f"Processing {len(df)} history records from uploaded CSV")
        
        # Process using HistoryService
        processed_df = history_service.process_history_csv_dataframe(df, 'admin_upload')
        history_list = history_service.dataframe_to_history_create_list(processed_df)
        
        # Validate and check duplicates
        validation_result = await history_service.validate_and_check_duplicates(history_list)
        
        logger.info(f"Upload validation: {len(validation_result['new_entries'])} new, {len(validation_result['duplicate_entries'])} duplicates")
        
        return {
            "success": True,
            "total_uploaded": len(history_list),
            "new_entries": len(validation_result['new_entries']),
            "duplicate_entries": len(validation_result['duplicate_entries']),
            "data": validation_result['new_entries'] + validation_result['duplicate_entries']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing history CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@router.post("/history/import")
async def import_history_entries(history_data: List[Dict[str, Any]], _auth: bool = admin_required):
    """Import selected history entries to BigQuery - using HistoryService."""
    try:
        if not history_data:
            raise HTTPException(status_code=400, detail="No history data provided")
        
        logger.info(f"Importing {len(history_data)} history entries")
        
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
        
        # Use HistoryService for bulk import (follows tools/import_history.py pattern)
        imported_count = await history_service.bulk_import_history(validated_history, 'admin_import')
        
        logger.info(f"Successfully imported {imported_count} history entries")
        
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
async def export_history_csv(name: Optional[str] = None, _auth: bool = admin_required):
    """Export ownership CSV. If `name` is provided, export only coins currently owned by that user.

    CSV columns: name, id, date
    """
    try:
        # Use HistoryService for export (filter by name if provided)
        export_df = await history_service.export_to_csv_format(name=name)

        if len(export_df) == 0:
            raise HTTPException(status_code=404, detail="No ownership entries found for export")

        # Create CSV content
        output = io.StringIO()
        # Ensure columns order
        export_df = export_df[['name', 'id', 'date']]
        export_df.to_csv(output, index=False)
        output.seek(0)

        logger.info(f"Exporting {len(export_df)} ownership entries to CSV (name={name})")

        def iter_csv():
            yield output.getvalue()

        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ownership_export.csv"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting ownership CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting ownership CSV: {str(e)}")


@router.post("/history/import-csv-direct")
async def import_history_csv_direct(file: UploadFile = File(...), _auth: bool = admin_required):
    """
    Direct CSV import following tools/import_history.py workflow.
    Combines upload, validation, and import in one step.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        logger.info(f"Starting direct CSV import from file: {file.filename}")
        
        # Use HistoryService for complete import workflow
        result = await history_service.import_from_csv_content(content_str, 'admin_direct_import')
        
        logger.info(f"Direct CSV import completed: {result['imported_count']} records")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direct CSV import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")


@router.get("/history/view")
async def view_history(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    name: Optional[str] = None,
    date_filter: Optional[str] = None,
    _auth: bool = admin_required
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
async def get_history_filter_options(_auth: bool = admin_required):
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
