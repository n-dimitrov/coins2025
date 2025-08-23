# BigQuery Import Configuration
# Copy this file to config.py and modify as needed

# Google Cloud Project Configuration
PROJECT_ID = "coins2025"
DATASET_ID = "coin_catalog_db"
TABLE_ID = "coin_catalog"

# File paths
SERVICE_ACCOUNT_PATH = "service_account.json"
CSV_FILE_PATH = "data/catalog.csv"

# BigQuery Settings
DATASET_LOCATION = "US"  # Change to your preferred location (e.g., "EU", "US", "asia-southeast1")

# Table Configuration
ENABLE_PARTITIONING = True  # Partition by created_at for better performance
ENABLE_CLUSTERING = True    # Cluster by country, coin_type, year for better query performance

# Import Settings
BATCH_SIZE = 1000          # Number of rows to process in each batch
MAX_RETRIES = 3            # Maximum number of retry attempts for failed operations
RETRY_DELAY = 5            # Delay in seconds between retry attempts
