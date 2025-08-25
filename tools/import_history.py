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
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoryImporter:
    """Import ownership history with simple schema matching CSV structure."""
    
    def __init__(self, project_id: str, dataset_id: str, table_name: str, service_account_path: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
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
        """Enhanced schema for add/remove operations."""
        return [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED", 
                                description="Primary key (UUID)"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", 
                                description="Owner name"),
            bigquery.SchemaField("coin_id", "STRING", mode="REQUIRED", 
                                description="Coin identifier"),
            bigquery.SchemaField("date", "TIMESTAMP", mode="REQUIRED", 
                                description="Acquisition date and time"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", 
                                description="When this record was added to system"),
            bigquery.SchemaField("created_by", "STRING", mode="NULLABLE", 
                                description="Who added this record"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED", 
                                description="true = owned, false = removed/sold")
        ]
    
    def _create_history_table(self) -> bool:
        """Create the ownership history table."""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_name)
            
            try:
                self.client.get_table(table_ref)
                logger.info(f"Table {self.table_name} already exists")
                return True
            except Exception:
                schema = self._get_history_schema()
                table = bigquery.Table(table_ref, schema=schema)
                
                # Add clustering for better query performance
                table.clustering_fields = ["name", "coin_id"]
                
                self.client.create_table(table)
                logger.info(f"Created table {self.table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            return False
    
    def import_history(self, csv_file_path: str) -> bool:
        """Import history.csv to BigQuery with enhanced schema."""
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
            
            # Convert date column and drop the redundant date_only column
            df['date'] = pd.to_datetime(df['date'])
            df = df.drop(columns=['date_only'])
            
            # Add new fields for enhanced schema
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df['created_at'] = datetime.now()
            df['created_by'] = 'import_script'
            df['is_active'] = True  # All imported records are active (owned)
            
            # Reorder columns to match schema
            df = df[['id', 'name', 'coin_id', 'date', 'created_at', 'created_by', 'is_active']]
            
            # Import to BigQuery
            table_ref = self.client.dataset(self.dataset_id).table(self.table_name)
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
                MIN(DATE(date)) as first_acquisition,
                MAX(DATE(date)) as last_acquisition
            FROM `{self.project_id}.{self.dataset_id}.{self.table_name}`
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
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "coins2025")
    DATASET_ID = os.getenv("BQ_DATASET", "db")
    HISTORY_TABLE = os.getenv("BQ_HISTORY_TABLE", "history")
    SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    HISTORY_CSV_PATH = "data/history.csv"
    
    importer = HistoryImporter(PROJECT_ID, DATASET_ID, HISTORY_TABLE, SERVICE_ACCOUNT_PATH)
    
    if importer.import_history(HISTORY_CSV_PATH):
        logger.info("History import completed successfully!")
        print("\nHistory import completed successfully!")
    else:
        logger.error("History import failed!")
        print("\nHistory import failed! Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()