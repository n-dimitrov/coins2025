#!/usr/bin/env python3
"""
Import ownership history from history.csv to BigQuery.
Simple implementation matching the existing CSV structure.
"""

import os
import logging
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoryImporter:
    """Import ownership history with simple schema matching CSV structure."""
    
    def __init__(self, project_id: str, dataset_id: str, service_account_path: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.service_account_path = service_account_path
        self.client = None
        
    def _authenticate(self) -> bool:
        """Authenticate with Google Cloud."""
        try:
            if not os.path.exists(self.service_account_path):
                logger.error(f"Service account file not found: {self.service_account_path}")
                return False
                
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/bigquery']
            )
            
            self.client = bigquery.Client(
                project=self.project_id,
                credentials=credentials
            )
            
            self.client.query("SELECT 1").result()
            logger.info("Successfully authenticated with BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def _get_history_schema(self):
        """Simple schema matching history.csv structure."""
        return [
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", 
                                description="Owner name"),
            bigquery.SchemaField("coin_id", "STRING", mode="REQUIRED", 
                                description="Coin identifier"),
            bigquery.SchemaField("date", "TIMESTAMP", mode="REQUIRED", 
                                description="Acquisition date and time"),
            bigquery.SchemaField("date_only", "DATE", mode="REQUIRED", 
                                description="Acquisition date only")
        ]
    
    def _create_history_table(self) -> bool:
        """Create the ownership history table."""
        try:
            table_ref = self.client.dataset(self.dataset_id).table("ownership_history")
            
            try:
                self.client.get_table(table_ref)
                logger.info("Table ownership_history already exists")
                return True
            except Exception:
                schema = self._get_history_schema()
                table = bigquery.Table(table_ref, schema=schema)
                
                # Add clustering for better query performance
                table.clustering_fields = ["name", "coin_id"]
                
                self.client.create_table(table)
                logger.info("Created table ownership_history")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            return False
    
    def import_history(self, csv_file_path: str) -> bool:
        """Import history.csv to BigQuery."""
        try:
            if not self._authenticate():
                return False
            
            if not self._create_history_table():
                return False
            
            if not os.path.exists(csv_file_path):
                logger.error(f"CSV file not found: {csv_file_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(csv_file_path)
            logger.info(f"Found {len(df)} ownership records")
            
            # Rename id column to coin_id to match schema
            df = df.rename(columns={'id': 'coin_id'})
            
            # Convert date columns
            df['date'] = pd.to_datetime(df['date'])
            
            # Handle empty date_only values by extracting from date column
            df['date_only'] = df['date_only'].fillna('')
            mask = df['date_only'] == ''
            df.loc[mask, 'date_only'] = df.loc[mask, 'date'].dt.strftime('%Y-%m-%d')
            df['date_only'] = pd.to_datetime(df['date_only']).dt.date
            
            # Import to BigQuery
            table_ref = self.client.dataset(self.dataset_id).table("ownership_history")
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=self._get_history_schema()
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            if job.errors:
                logger.error(f"Import job completed with errors: {job.errors}")
                return False
            
            logger.info(f"Successfully imported {len(df)} ownership records")
            
            # Show summary
            query = f"""
            SELECT 
                name,
                COUNT(*) as coin_count,
                MIN(date_only) as first_acquisition,
                MAX(date_only) as last_acquisition
            FROM `{self.project_id}.{self.dataset_id}.ownership_history`
            GROUP BY name
            ORDER BY coin_count DESC
            """
            
            results = self.client.query(query).result()
            logger.info("Ownership summary:")
            for row in results:
                logger.info(f"  {row.name}: {row.coin_count} coins ({row.first_acquisition} to {row.last_acquisition})")
            
            return True
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return False

def main():
    """Main function to import ownership history."""
    PROJECT_ID = "coins2025"
    DATASET_ID = "db"
    SERVICE_ACCOUNT_PATH = "service_account.json"
    HISTORY_CSV_PATH = "data/history.csv"
    
    importer = HistoryImporter(PROJECT_ID, DATASET_ID, SERVICE_ACCOUNT_PATH)
    
    if importer.import_history(HISTORY_CSV_PATH):
        logger.info("History import completed successfully!")
        print("\nHistory import completed successfully!")
    else:
        logger.error("History import failed!")
        print("\nHistory import failed! Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()