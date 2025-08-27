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
import uuid
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
        self._group_mapping = {}  # Store group key to UUID mapping
        
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
        """Enhanced schema for groups table."""
        return [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED", 
                                description="UUID primary key"),
            bigquery.SchemaField("group_key", "STRING", mode="REQUIRED", 
                                description="Group identifier (for URLs)"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", 
                                description="Group display name"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED", 
                                description="Soft delete flag")
        ]
    
    def _get_group_users_schema(self):
        """Enhanced schema for group_users table."""
        return [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED", 
                                description="UUID primary key"),
            bigquery.SchemaField("group_id", "STRING", mode="REQUIRED", 
                                description="Reference to groups.id"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED", 
                                description="User name"),
            bigquery.SchemaField("alias", "STRING", mode="REQUIRED", 
                                description="User alias/display name"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED", 
                                description="Soft delete flag")
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
                
                # Add clustering for better query performance
                if table_name == self.groups_table:
                    table.clustering_fields = ["group_key", "is_active"]
                elif table_name == self.group_users_table:
                    table.clustering_fields = ["group_id", "name", "is_active"]
                
                self.client.create_table(table)
                logger.info(f"Created table {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            return False
    
    def import_groups(self, groups_csv_path: str) -> bool:
        """Import groups.csv to BigQuery with enhanced schema."""
        try:
            if not os.path.exists(groups_csv_path):
                logger.error(f"CSV file not found: {groups_csv_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(groups_csv_path)
            logger.info(f"Found {len(df)} groups")
            
            # Add new fields for enhanced schema
            import uuid
            
            # Generate UUIDs and rename columns
            df['uuid_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df = df.rename(columns={'group': 'group_key', 'uuid_id': 'id'})
            df['is_active'] = True  # All imported groups are active
            
            # Reorder columns to match schema
            df = df[['id', 'group_key', 'name', 'is_active']]
            
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
            # Store group mapping for group_users import
            self._group_mapping = dict(zip(df['group_key'], df['id']))
            logger.info(f"Group mapping: {self._group_mapping}")
            return True
            
        except Exception as e:
            logger.error(f"Groups import failed: {str(e)}")
            return False
    
    def import_group_users(self, group_users_csv_path: str) -> bool:
        """Import group_users.csv to BigQuery with enhanced schema."""
        try:
            if not os.path.exists(group_users_csv_path):
                logger.error(f"CSV file not found: {group_users_csv_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(group_users_csv_path)
            logger.info(f"Found {len(df)} group user associations")
            
            # Since the CSV doesn't have group_id, we need to assign all users to the single group
            # Get the group ID from the groups table (should be the "hippo" group)
            if hasattr(self, '_group_mapping') and 'hippo' in self._group_mapping:
                # Use the mapping from the groups import
                hippo_group_id = self._group_mapping['hippo']
            else:
                # Fallback: query the groups table to get the hippo group ID
                query = f"SELECT id FROM `{self.project_id}.{self.dataset_id}.{self.groups_table}` WHERE group_key = 'hippo' AND is_active = true"
                result = self.client.query(query).result()
                hippo_group_id = None
                for row in result:
                    hippo_group_id = row.id
                    break
                
                if not hippo_group_id:
                    logger.error("Could not find hippo group ID")
                    return False
            
            # Add new fields for enhanced schema
            import uuid
            
            # Generate UUIDs and assign all users to the hippo group
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df['group_id'] = hippo_group_id  # All users belong to hippo group
            df = df.rename(columns={'user': 'name'})  # Rename user to name
            df['is_active'] = True  # All imported users are active
            
            # Reorder columns to match schema
            df = df[['id', 'group_id', 'name', 'alias', 'is_active']]
            
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
            
            logger.info(f"Successfully imported {len(df)} group user associations to hippo group")
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
                COUNT(gu.name) as user_count,
                STRING_AGG(gu.name, ', ' ORDER BY gu.name) as users
            FROM `{self.project_id}.{self.dataset_id}.{self.groups_table}` g
            LEFT JOIN `{self.project_id}.{self.dataset_id}.{self.group_users_table}` gu 
                ON g.id = gu.group_id AND gu.is_active = true
            WHERE g.is_active = true
            GROUP BY g.id, g.name
            ORDER BY g.name
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
