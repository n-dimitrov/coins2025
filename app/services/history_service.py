"""
History Management Service
Provides centralized history operations following tools/import_history.py patterns.
"""

import logging
import pandas as pd
import uuid
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from app.services.bigquery_service import BigQueryService, get_bigquery_service as get_bq_provider
from app.models.history import History, HistoryCreate
from app.config import settings

logger = logging.getLogger(__name__)

class HistoryService:
    """Service for managing history operations with enhanced schema support."""
    
    def __init__(self):
        # Use cached provider to avoid repeated BigQuery client initializations
        self.bigquery_service = get_bq_provider()
    
    def get_enhanced_history_schema(self) -> List[bigquery.SchemaField]:
        """Get the enhanced history schema - delegates to BigQueryService for consistency."""
        return self.bigquery_service._get_history_schema()
    
    def process_history_csv_dataframe(self, df: pd.DataFrame, created_by: str = 'admin') -> pd.DataFrame:
        """
        Process history CSV DataFrame following tools/import_history.py logic.
        
        Args:
            df: DataFrame with columns ['name', 'id', 'date', ...]
            created_by: String identifying who is importing the data
            
        Returns:
            Processed DataFrame with enhanced schema
        """
        logger.info(f"Processing {len(df)} history records")
        
        # Rename 'id' column to 'coin_id' to match enhanced schema
        df = df.rename(columns={'id': 'coin_id'})
        
        # Convert date column and drop redundant date_only column if present
        df['date'] = pd.to_datetime(df['date'])
        if 'date_only' in df.columns:
            df = df.drop(columns=['date_only'])
        
        # Add enhanced schema fields
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        df['created_at'] = datetime.now(timezone.utc)
        df['created_by'] = created_by
        df['is_active'] = True  # All imported records are active (owned)
        
        # Reorder columns to match enhanced schema
        df = df[['id', 'name', 'coin_id', 'date', 'created_at', 'created_by', 'is_active']]
        
        logger.info(f"Processed DataFrame with enhanced schema: {len(df)} records")
        return df
    
    def dataframe_to_history_create_list(self, df: pd.DataFrame) -> List[HistoryCreate]:
        """Convert processed DataFrame to list of HistoryCreate objects."""
        history_list = []
        
        for _, row in df.iterrows():
            history_data = HistoryCreate(
                name=row['name'],
                id=row['coin_id'],  # HistoryCreate expects 'id' field to be coin_id
                date=row['date'].to_pydatetime() if hasattr(row['date'], 'to_pydatetime') else row['date']
            )
            history_list.append(history_data)
        
        return history_list
    
    async def validate_and_check_duplicates(self, history_list: List[HistoryCreate]) -> Dict[str, Any]:
        """
        Validate history entries and check for duplicates.
        
        Returns:
            Dictionary with 'new_entries' and 'duplicate_entries' lists
        """
        # Get existing history for duplicate checking
        existing_history = await self.bigquery_service.get_all_history()
        existing_keys = {
            f"{h['name']}_{h['id']}_{h['date'].strftime('%Y-%m-%d %H:%M:%S')}" 
            for h in existing_history
        }
        
        new_entries = []
        duplicate_entries = []
        
        for history in history_list:
            # Convert to dict for easier handling
            history_dict = {
                'name': history.name,
                'id': history.id,
                'date': history.date
            }
            
            key = f"{history.name}_{history.id}_{history.date.strftime('%Y-%m-%d %H:%M:%S')}"
            if key in existing_keys:
                duplicate_entries.append({**history_dict, 'status': 'duplicate'})
            else:
                new_entries.append({**history_dict, 'status': 'new'})
        
        logger.info(f"Validation complete: {len(new_entries)} new, {len(duplicate_entries)} duplicates")
        
        return {
            'new_entries': new_entries,
            'duplicate_entries': duplicate_entries
        }
    
    async def bulk_import_history(self, history_list: List[HistoryCreate], created_by: str = 'admin') -> int:
        """
        Bulk import history entries using the BigQuery service method.
        This follows the same pattern as tools/import_history.py
        """
        logger.info(f"Starting bulk import of {len(history_list)} history entries")
        
        # Use the existing BigQuery service method which handles:
        # - Table creation with enhanced schema
        # - UUID generation
        # - Proper timestamp handling
        # - Error handling
        imported_count = await self.bigquery_service.import_history_batch(history_list)
        
        logger.info(f"Bulk import completed: {imported_count} records imported")
        return imported_count
    
    async def import_from_csv_content(self, csv_content: str, created_by: str = 'admin') -> Dict[str, Any]:
        """
        Import history from CSV content following tools/import_history.py workflow.
        
        Args:
            csv_content: CSV content as string
            created_by: String identifying who is importing
            
        Returns:
            Dictionary with import results
        """
        try:
            # Read CSV into DataFrame
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Validate required columns
            required_columns = ['name', 'id', 'date']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Missing required columns: {missing}")
            
            # Process DataFrame following import_history.py logic
            processed_df = self.process_history_csv_dataframe(df, created_by)
            
            # Convert to HistoryCreate objects
            history_list = self.dataframe_to_history_create_list(processed_df)
            
            # Import using bulk method
            imported_count = await self.bulk_import_history(history_list, created_by)
            
            return {
                'success': True,
                'imported_count': imported_count,
                'total_processed': len(history_list),
                'message': f"Successfully imported {imported_count} history entries"
            }
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {str(e)}")
            raise
    
    async def export_to_csv_format(self, name: Optional[str] = None) -> pd.DataFrame:
        """
        Export ownership data to CSV format matching the original structure.

        If `name` is provided, export only coins currently owned by that user
        (based on the latest active flag). If no name is provided, export all
        currently active ownerships across users.

        Returns:
            DataFrame in original CSV format (name, id, date)
        """
        # If a specific user is requested, use optimized method
        if name:
            # get_user_owned_coins returns current owned coins for the user
            owned = await self.bigquery_service.get_user_owned_coins(name)
            if not owned:
                return pd.DataFrame(columns=['name', 'id', 'date'])

            # Build DataFrame with name, id (coin_id), date (acquired_date)
            rows = []
            for r in owned:
                rows.append({
                    'name': name,
                    'id': r.get('coin_id') or r.get('coin_id'),
                    'date': r.get('acquired_date') or r.get('date')
                })

            export_df = pd.DataFrame(rows)
            # Format date
            if not export_df.empty:
                export_df['date'] = pd.to_datetime(export_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

            return export_df

        # No specific user: export all currently active ownerships
        # We'll query the history table to get latest active records per (name, coin_id)
        history_data = await self.bigquery_service.get_all_history()
        if not history_data:
            return pd.DataFrame(columns=['name', 'id', 'date'])

        df = pd.DataFrame(history_data)
        # Ensure coin_id exists
        if 'coin_id' in df.columns:
            df = df.rename(columns={'coin_id': 'id'})

        # Keep only latest active records per name+id. get_all_history may return raw records,
        # but the BigQueryService has other helpers — to keep this change minimal we
        # will compute latest by created_at/date locally.
        # Convert dates for proper sorting
        df['created_at'] = pd.to_datetime(df.get('created_at'))
        df['date'] = pd.to_datetime(df.get('date'))

        # Sort and drop duplicates keeping the latest created_at per name+id
        df = df.sort_values(['name', 'id', 'created_at', 'date'], ascending=[True, True, False, False])
        df_latest = df.drop_duplicates(subset=['name', 'id'], keep='first')

        # Filter by is_active == True
        if 'is_active' in df_latest.columns:
            df_latest = df_latest[df_latest['is_active'] == True]

        export_df = df_latest[['name', 'id', 'date']].copy()
        export_df['date'] = pd.to_datetime(export_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

        return export_df
