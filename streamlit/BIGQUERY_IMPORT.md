# BigQuery Coin Catalog Import

This script imports coin catalog data from CSV files into Google BigQuery with proper schema design and error handling.

## Features

- **Automatic Schema Creation**: Creates optimized BigQuery tables with proper data types
- **Data Validation**: Validates and cleans data before import
- **Performance Optimization**: Uses partitioning and clustering for better query performance
- **Error Handling**: Comprehensive error handling with retry logic
- **Flexible Import Modes**: Support for append or replace operations
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Table Schema

The script creates a `coin_catalog` table with the following schema:

| Column | Type | Mode | Description |
|--------|------|------|-------------|
| coin_type | STRING | REQUIRED | Type of coin: RE (regular) or CC (commemorative) |
| year | INTEGER | REQUIRED | Year the coin was issued |
| country | STRING | REQUIRED | Country that issued the coin |
| series | STRING | REQUIRED | Series identifier for the coin |
| value | FLOAT | REQUIRED | Denomination value of the coin |
| coin_id | STRING | REQUIRED | Unique identifier for the coin |
| image_url | STRING | NULLABLE | URL to the coin image |
| feature | STRING | NULLABLE | Special feature description (mainly for commemorative coins) |
| volume | STRING | NULLABLE | Volume information (mainly for commemorative coins) |
| created_at | TIMESTAMP | REQUIRED | Timestamp when the record was imported |
| updated_at | TIMESTAMP | REQUIRED | Timestamp when the record was last updated |

## Performance Optimizations

- **Partitioning**: Table is partitioned by `created_at` (daily partitions)
- **Clustering**: Clustered by `country`, `coin_type`, and `year` for optimal query performance
- **Data Types**: Optimized data types for storage efficiency

## Setup

1. **Install Dependencies**:
   ```bash
   ./setup.sh
   ```
   Or manually:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Service Account**:
   - Ensure `service_account.json` is present with proper permissions:
     - BigQuery Data Editor
     - BigQuery Job User
     - BigQuery Data Viewer

3. **Verify Data File**:
   - Ensure `data/catalog.csv` exists with the expected format

## Usage

### Basic Import (Append Mode)
```bash
python import_db.py
```
This will append new data to the existing table.

### Replace Existing Data
```bash
python import_db.py --replace
```
This will replace all existing data in the table.

## Example Queries

After importing, you can run these example queries in BigQuery:

### 1. Count coins by type
```sql
SELECT coin_type, COUNT(*) as count
FROM `coins2025.coin_catalog_db.coin_catalog`
GROUP BY coin_type
ORDER BY coin_type;
```

### 2. Find commemorative coins from 2004
```sql
SELECT country, feature, volume
FROM `coins2025.coin_catalog_db.coin_catalog`
WHERE coin_type = 'CC' AND year = 2004
ORDER BY country;
```

### 3. Count coins by country
```sql
SELECT country, COUNT(*) as coin_count
FROM `coins2025.coin_catalog_db.coin_catalog`
GROUP BY country
ORDER BY coin_count DESC;
```

### 4. Find all 2 Euro coins
```sql
SELECT country, year, coin_type, feature
FROM `coins2025.coin_catalog_db.coin_catalog`
WHERE value = 2.0
ORDER BY year, country;
```

### 5. Average number of coins per year
```sql
SELECT year, COUNT(*) as coin_count
FROM `coins2025.coin_catalog_db.coin_catalog`
GROUP BY year
ORDER BY year;
```

## Configuration

You can customize the import settings by copying `config_template.py` to `config.py` and modifying the values:

```python
# Copy config_template.py to config.py and customize
PROJECT_ID = "your-project-id"
DATASET_ID = "your-dataset-id"
DATASET_LOCATION = "US"  # or "EU", "asia-southeast1", etc.
```

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Verify `service_account.json` exists and has correct permissions
   - Check if the service account has access to the specified project

2. **Permission Denied**:
   - Ensure service account has BigQuery Data Editor and Job User roles
   - Verify the project ID is correct

3. **Dataset Not Found**:
   - The script will automatically create the dataset if it doesn't exist
   - Ensure you have permission to create datasets

4. **Data Validation Errors**:
   - Check the CSV file format matches the expected schema
   - Verify year and value columns contain valid numeric data

### Logs

The script provides detailed logging to help diagnose issues:
- INFO level: General progress information
- WARNING level: Data quality issues (non-fatal)
- ERROR level: Critical errors that prevent import

## Security Best Practices

- Never commit `service_account.json` to version control
- Use least-privilege permissions for the service account
- Regularly rotate service account keys
- Monitor BigQuery usage and costs
- Enable audit logging for compliance requirements
