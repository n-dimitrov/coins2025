#!/usr/bin/env python3
"""
Import coin catalog data into BigQuery database.

This script reads the catalog.csv file and imports the data into a BigQuery table
with appropriate schema design for coin data management.
"""

import os
import logging
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoinCatalogImporter:
    """
    Handles importing coin catalog data into BigQuery.
    
    This class manages the connection to BigQuery and provides methods
    to create tables and import data with proper error handling and logging.
    """
    
    def __init__(self, project_id: str, dataset_id: str, service_account_path: str, table_id: str = "catalog"):
        """
        Initialize the importer with BigQuery configuration.
        
        Args:
            project_id: Google Cloud project ID
            dataset_id: BigQuery dataset ID
            service_account_path: Path to service account JSON file
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.service_account_path = service_account_path
        self.client = None
        self.table_id = table_id  # Default table name for coin catalog
        
    def _authenticate(self) -> bool:
        """
        Authenticate with Google Cloud using service account.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
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
            
            # Test connection
            self.client.query("SELECT 1").result()
            logger.info("Successfully authenticated with BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def _create_dataset_if_not_exists(self) -> bool:
        """
        Create the dataset if it doesn't already exist.
        
        Returns:
            bool: True if dataset exists or was created successfully
        """
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            
            try:
                self.client.get_dataset(dataset_ref)
                logger.info(f"Dataset {self.dataset_id} already exists")
                return True
            except Exception:
                # Dataset doesn't exist, create it
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"  # Change as needed
                dataset.description = "Coin catalog data storage"
                
                self.client.create_dataset(dataset)
                logger.info(f"Created dataset {self.dataset_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create dataset: {str(e)}")
            return False
    
    def _get_table_schema(self) -> list:
        """
        Define the BigQuery table schema for coin catalog data.
        
        Returns:
            List of BigQuery SchemaField objects
        """
        return [
            bigquery.SchemaField("coin_type", "STRING", mode="REQUIRED", 
                                description="Type of coin: RE (regular) or CC (commemorative)"),
            bigquery.SchemaField("year", "INTEGER", mode="REQUIRED", 
                                description="Year the coin was issued"),
            bigquery.SchemaField("country", "STRING", mode="REQUIRED", 
                                description="Country that issued the coin"),
            bigquery.SchemaField("series", "STRING", mode="REQUIRED", 
                                description="Series identifier for the coin"),
            bigquery.SchemaField("value", "FLOAT", mode="REQUIRED", 
                                description="Denomination value of the coin"),
            bigquery.SchemaField("coin_id", "STRING", mode="REQUIRED", 
                                description="Unique identifier for the coin"),
            bigquery.SchemaField("image_url", "STRING", mode="NULLABLE", 
                                description="URL to the coin image"),
            bigquery.SchemaField("feature", "STRING", mode="NULLABLE", 
                                description="Special feature description (mainly for commemorative coins)"),
            bigquery.SchemaField("volume", "STRING", mode="NULLABLE", 
                                description="Volume information (mainly for commemorative coins)"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", 
                                description="Timestamp when the record was imported"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", 
                                description="Timestamp when the record was last updated")
        ]
    
    def _create_table_if_not_exists(self) -> bool:
        """
        Create the coin catalog table if it doesn't exist.
        
        Returns:
            bool: True if table exists or was created successfully
        """
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            
            try:
                self.client.get_table(table_ref)
                logger.info(f"Table {self.table_id} already exists")
                return True
            except Exception:
                # Table doesn't exist, create it
                schema = self._get_table_schema()
                table = bigquery.Table(table_ref, schema=schema)
                
                # Add partitioning by year for better performance
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="created_at"
                )
                
                # Add clustering for better query performance
                table.clustering_fields = ["country", "coin_type", "year"]
                
                self.client.create_table(table)
                logger.info(f"Created table {self.table_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            return False
    
    def _prepare_data(self, csv_file_path: str) -> Optional[pd.DataFrame]:
        """
        Read and prepare the CSV data for BigQuery import.
        
        Args:
            csv_file_path: Path to the catalog CSV file
            
        Returns:
            Prepared DataFrame or None if error
        """
        try:
            if not os.path.exists(csv_file_path):
                logger.error(f"CSV file not found: {csv_file_path}")
                return None
            
            # Read CSV with proper data types
            df = pd.read_csv(csv_file_path)
            
            # Validate required columns
            required_columns = ['type', 'year', 'country', 'series', 'value', 'id', 'image']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return None
            
            # Rename columns to match BigQuery schema
            df = df.rename(columns={
                'type': 'coin_type',
                'id': 'coin_id',
                'image': 'image_url'
            })
            
            # Clean and validate data
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Remove rows with invalid year or value
            initial_count = len(df)
            df = df.dropna(subset=['year', 'value'])
            if len(df) < initial_count:
                logger.warning(f"Removed {initial_count - len(df)} rows with invalid year or value")
            
            # Convert year to integer
            df['year'] = df['year'].astype(int)
            
            # Fill empty feature and volume columns with None
            df['feature'] = df['feature'].fillna('')
            df['volume'] = df['volume'].fillna('')
            
            # Add timestamps
            current_timestamp = pd.Timestamp.now(tz='UTC')
            df['created_at'] = current_timestamp
            df['updated_at'] = current_timestamp
            
            # Validate coin types
            valid_types = ['RE', 'CC']
            invalid_types = df[~df['coin_type'].isin(valid_types)]
            if not invalid_types.empty:
                logger.warning(f"Found {len(invalid_types)} rows with invalid coin types")
                df = df[df['coin_type'].isin(valid_types)]
            
            logger.info(f"Prepared {len(df)} records for import")
            return df
            
        except Exception as e:
            logger.error(f"Failed to prepare data: {str(e)}")
            return None
    
    def import_data(self, csv_file_path: str, replace_existing: bool = False) -> bool:
        """
        Import coin catalog data from CSV to BigQuery.
        
        Args:
            csv_file_path: Path to the catalog CSV file
            replace_existing: If True, replace existing table data
            
        Returns:
            bool: True if import successful, False otherwise
        """
        try:
            # Authenticate
            if not self._authenticate():
                return False
            
            # Create dataset and table
            if not self._create_dataset_if_not_exists():
                return False
            
            if not self._create_table_if_not_exists():
                return False
            
            # Prepare data
            df = self._prepare_data(csv_file_path)
            if df is None:
                return False
            
            # Configure job settings
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                source_format=bigquery.SourceFormat.PARQUET,  # More efficient than CSV
                autodetect=False,  # Use our defined schema
                schema=self._get_table_schema()
            )
            
            # Import data
            logger.info(f"Starting import of {len(df)} records...")
            job = self.client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            
            # Wait for completion
            job.result()
            
            if job.errors:
                logger.error(f"Import job completed with errors: {job.errors}")
                return False
            
            logger.info(f"Successfully imported {len(df)} records to {self.dataset_id}.{self.table_id}")
            
            # Verify import
            query = f"""
            SELECT 
                coin_type,
                COUNT(*) as count,
                MIN(year) as min_year,
                MAX(year) as max_year
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            GROUP BY coin_type
            ORDER BY coin_type
            """
            
            results = self.client.query(query).result()
            logger.info("Import summary:")
            for row in results:
                logger.info(f"  {row.coin_type}: {row.count} coins ({row.min_year}-{row.max_year})")
            
            return True
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return False

def main():
    """
    Main function to run the import process.
    """
    # Configuration
    PROJECT_ID = "coins2025"  # Update if different
    DATASET_ID = "db"
    SERVICE_ACCOUNT_PATH = "service_account.json"
    CSV_FILE_PATH = "data/catalog.csv"
    
    # Check if running with replace flag
    replace_existing = "--replace" in sys.argv
    replace_existing = True
    
    if replace_existing:
        logger.info("Running in REPLACE mode - existing data will be replaced")
    else:
        logger.info("Running in APPEND mode - data will be added to existing table")
    
    # Initialize importer
    importer = CoinCatalogImporter(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        service_account_path=SERVICE_ACCOUNT_PATH,
        table_id="catalog"  
    )

    # Run import
    success = importer.import_data(CSV_FILE_PATH, replace_existing=replace_existing)
    
    if success:
        logger.info("Data import completed successfully!")
        print("\nImport completed successfully!")
    else:
        logger.error("Data import failed!")
        print("\nImport failed! Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
