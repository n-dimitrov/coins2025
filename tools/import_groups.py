#!/usr/bin/env python3
"""
Import groups and group_users from CSV files to BigQuery.
"""

import os
import logging
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GroupsImporter:
    """Import groups and group_users tables."""
    
    def __init__(self, project_id: str, dataset_id: str, groups_table: str, group_users_table: str, service_account_path: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.groups_table = groups_table
        self.group_users_table = group_users_table
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
    
    def _get_groups_schema(self):
        """Schema for groups table."""
        return [
            bigquery.SchemaField("group", "STRING", mode="REQUIRED", 
                                description="Group identifier"),
            bigquery.SchemaField("id", "INTEGER", mode="REQUIRED", 
                                description="Group ID"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", 
                                description="Group display name")
        ]
    
    def _get_group_users_schema(self):
        """Schema for group_users table."""
        return [
            bigquery.SchemaField("user", "STRING", mode="REQUIRED", 
                                description="User name"),
            bigquery.SchemaField("alias", "STRING", mode="REQUIRED", 
                                description="User alias/display name"),
            bigquery.SchemaField("group_id", "INTEGER", mode="REQUIRED", 
                                description="Group ID reference")
        ]
    
    def _create_table(self, table_name: str, schema) -> bool:
        """Create a table with the given schema."""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(table_name)
            
            try:
                self.client.get_table(table_ref)
                logger.info(f"Table {table_name} already exists")
                return True
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)
                logger.info(f"Created table {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            return False
    
    def import_groups(self, groups_csv_path: str) -> bool:
        """Import groups.csv to BigQuery."""
        try:
            if not os.path.exists(groups_csv_path):
                logger.error(f"CSV file not found: {groups_csv_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(groups_csv_path)
            logger.info(f"Found {len(df)} groups")
            
            # Import to BigQuery
            table_ref = self.client.dataset(self.dataset_id).table(self.groups_table)
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=self._get_groups_schema()
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            if job.errors:
                logger.error(f"Groups import job completed with errors: {job.errors}")
                return False
            
            logger.info(f"Successfully imported {len(df)} groups")
            return True
            
        except Exception as e:
            logger.error(f"Groups import failed: {str(e)}")
            return False
    
    def import_group_users(self, group_users_csv_path: str) -> bool:
        """Import group_users.csv to BigQuery."""
        try:
            if not os.path.exists(group_users_csv_path):
                logger.error(f"CSV file not found: {group_users_csv_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(group_users_csv_path)
            logger.info(f"Found {len(df)} group user associations")
            
            # Import to BigQuery
            table_ref = self.client.dataset(self.dataset_id).table(self.group_users_table)
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=self._get_group_users_schema()
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            if job.errors:
                logger.error(f"Group users import job completed with errors: {job.errors}")
                return False
            
            logger.info(f"Successfully imported {len(df)} group user associations")
            return True
            
        except Exception as e:
            logger.error(f"Group users import failed: {str(e)}")
            return False
    
    def import_all(self, groups_csv_path: str, group_users_csv_path: str) -> bool:
        """Import both groups and group_users tables."""
        try:
            if not self._authenticate():
                return False
            
            # Create tables
            if not self._create_table(self.groups_table, self._get_groups_schema()):
                return False
            
            if not self._create_table(self.group_users_table, self._get_group_users_schema()):
                return False
            
            # Import data
            if not self.import_groups(groups_csv_path):
                return False
            
            if not self.import_group_users(group_users_csv_path):
                return False
            
            # Show summary
            query = f"""
            SELECT 
                g.name as group_name,
                COUNT(gu.user) as user_count,
                STRING_AGG(gu.user, ', ' ORDER BY gu.user) as users
            FROM `{self.project_id}.{self.dataset_id}.{self.groups_table}` g
            LEFT JOIN `{self.project_id}.{self.dataset_id}.{self.group_users_table}` gu 
                ON g.id = gu.group_id
            GROUP BY g.id, g.name
            ORDER BY g.id
            """
            
            results = self.client.query(query).result()
            logger.info("Groups summary:")
            for row in results:
                logger.info(f"  {row.group_name}: {row.user_count} users ({row.users})")
            
            return True
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return False

def main():
    """Main function to import groups data."""
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "coins2025")
    DATASET_ID = os.getenv("BQ_DATASET", "db")
    GROUPS_TABLE = os.getenv("BQ_GROUPS_TABLE", "groups")
    GROUP_USERS_TABLE = os.getenv("BQ_GROUP_USERS_TABLE", "group_users")
    SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    
    GROUPS_CSV_PATH = "data/groups.csv"
    GROUP_USERS_CSV_PATH = "data/group_users.csv"
    
    importer = GroupsImporter(PROJECT_ID, DATASET_ID, GROUPS_TABLE, GROUP_USERS_TABLE, SERVICE_ACCOUNT_PATH)
    
    if importer.import_all(GROUPS_CSV_PATH, GROUP_USERS_CSV_PATH):
        logger.info("Groups import completed successfully!")
        print("\nGroups import completed successfully!")
    else:
        logger.error("Groups import failed!")
        print("\nGroups import failed! Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
