# Neon Database Migration Guide - COMPLETED ✅

This guide documents the migration from Google BigQuery to Neon (serverless PostgreSQL) for the coins2025 application.

**Status:** Migration is complete. The application is now running on Neon PostgreSQL exclusively.
All BigQuery references have been removed from the codebase.

## Overview

This application has been successfully migrated from Google BigQuery to Neon, a serverless PostgreSQL database.
Data was loaded from CSV files in the `data/` folder.

**Key Points:**
- Data loaded from CSV files in the `data/` folder
- No BigQuery setup or data export needed
- Application now uses Neon PostgreSQL exclusively
- Uses psycopg3 (modern PostgreSQL client)

## Prerequisites

1. **Neon Account**: Sign up at https://neon.tech
2. **PostgreSQL Client**: `psycopg` (psycopg3) - included in requirements
3. **Python 3.8+**: Already in use
4. **Environment File**: Update `.env` with Neon credentials

## Step-by-Step Migration

### Step 1: Create Neon Project

1. Go to https://neon.tech and sign up
2. Create a new project (e.g., "coins2025")
3. Create a database (default name is usually `neondb`)
4. Copy the connection string in format: `postgresql://user:password@hostname/dbname`

### Step 2: Update Environment Configuration

Add to your `.env` file:

```bash
# Switch to Neon database
DATABASE_TYPE=neon
DATABASE_URL=postgresql://your_username:your_password@your_neon_host/coins2025

# Optional connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30

# Keep these unchanged
APP_ENV=development
CACHE_DURATION_MINUTES=5
```

**For Production Cloud Run:**

```bash
DATABASE_TYPE=neon
DATABASE_URL=postgresql://prod_user:prod_password@prod_neon_host/coins2025
APP_ENV=production
```

### Step 3: Create Database Schema

Execute the schema file on your Neon database:

```bash
# Connect to Neon
psql postgresql://user:password@your_neon_host/coins2025 < tools/neon_schema.sql
```

Or if using the application's initialization:

The schema will be created automatically when you run the import script (Step 4).

### Step 4: Import Data from CSVs

Run the import script to load your CSV data into Neon:

```bash
# Make sure DATABASE_URL is set in .env
python tools/neon_import.py
```

This script will:
- Load groups from `data/groups.csv`
- Load group users from `data/group_users.csv`
- Load coins catalog from `data/catalog.csv`
- Load ownership history from `data/history.csv`

**Import Order:** Important! Groups → Group Users → Catalog → History (respects foreign key constraints)

### Step 5: Update Requirements.txt

Add psycopg dependency:

```
psycopg[binary]==3.1.x
```

Installation:

```bash
pip install -r requirements.txt
```

### Step 6: Test the Connection

```python
# Quick test script
import asyncio
from app.services.neon_service import NeonService

async def test():
    service = NeonService()
    coins = await service.get_coins(limit=5)
    print(f"Found {len(coins)} coins")

asyncio.run(test())
```

### Step 7: Run Application with Neon

```bash
# Development with Neon
python main.py

# OR using Docker
docker-compose up
```

Verify the logs show:
```
Database type: neon
NeonService initialized successfully
```

## Database Schema

### Tables

#### catalog
- **coin_type**: VARCHAR(10) - Type of coin (RE/CC)
- **year**: INTEGER - Year issued
- **country**: VARCHAR(100) - Country
- **series**: VARCHAR(100) - Series identifier
- **value**: FLOAT - Denomination
- **coin_id**: VARCHAR(100) PRIMARY KEY - Unique ID
- **image_url**: TEXT - Image URL
- **feature**: TEXT - Special feature
- **volume**: TEXT - Volume info
- **created_at**: TIMESTAMP - Record creation time
- **updated_at**: TIMESTAMP - Last update time

#### history
- **id**: UUID PRIMARY KEY - Unique record ID
- **name**: VARCHAR(100) - Owner name
- **coin_id**: VARCHAR(100) FOREIGN KEY - Reference to catalog
- **date**: TIMESTAMP - Acquisition date
- **created_at**: TIMESTAMP - Record creation time
- **created_by**: VARCHAR(50) - Who added the record
- **is_active**: BOOLEAN - true = owned, false = sold

#### groups
- **id**: UUID PRIMARY KEY - Group ID
- **group_key**: VARCHAR(100) UNIQUE - URL-friendly identifier
- **name**: VARCHAR(100) - Display name
- **is_active**: BOOLEAN - Active status
- **created_at**: TIMESTAMP - Creation time
- **updated_at**: TIMESTAMP - Last update time

#### group_users
- **id**: UUID PRIMARY KEY - User ID
- **group_id**: UUID FOREIGN KEY - Reference to groups
- **name**: VARCHAR(100) - User name
- **alias**: VARCHAR(100) - Display alias
- **is_active**: BOOLEAN - Active status
- **created_at**: TIMESTAMP - Creation time
- **updated_at**: TIMESTAMP - Last update time

### Indexes

Optimized indexes for query performance:
- `idx_catalog_year` - Year queries
- `idx_catalog_country` - Country filtering
- `idx_history_name_coin_id` - Ownership lookups
- `idx_history_created_at` - Recent records
- `idx_groups_group_key` - Group lookups
- `idx_group_users_group_id` - Member lookups

## Switching Between Databases

To switch between BigQuery and Neon:

```bash
# Use BigQuery (default)
export DATABASE_TYPE=bigquery

# Use Neon
export DATABASE_TYPE=neon
export DATABASE_URL=postgresql://...
```

The application will initialize the appropriate service automatically.

## Performance Considerations

### BigQuery vs Neon

| Aspect | BigQuery | Neon |
|--------|----------|------|
| **Query Model** | OLAP (analytical) | OLTP (transactional) |
| **Connection** | REST API | Native PostgreSQL |
| **Scaling** | Auto (query-based) | Auto (storage-based) |
| **Cost** | Per-query | Monthly subscription |
| **Concurrency** | High | High (auto-scaling) |
| **Response Time** | 1-5s per query | <100ms typical |

### Optimization Tips

1. **Connection Pooling**: Enabled by default (20 connections)
2. **Indexing**: Schema includes optimized indexes
3. **Caching**: In-memory cache still active (5-15 min TTL)
4. **Batch Inserts**: History imports use batching

## Troubleshooting

### Connection Issues

```
Error: "SCRAM authentication failed"
```

Check:
- DATABASE_URL syntax is correct
- Password contains special characters (must be URL-encoded)
- Neon database is active and not sleeping

### Foreign Key Errors

```
Error: "INSERT violates foreign key constraint"
```

Solution:
- Ensure groups are imported before group_users
- Ensure catalog coins exist before adding history

### Performance Issues

1. Check indexes are created: `\d catalog` in psql
2. Verify connection pooling: `DATABASE_POOL_SIZE=20`
3. Check cache configuration: `CACHE_DURATION_MINUTES=5`

### Data Mismatch

If data doesn't match expected counts:

```bash
# Verify imports with counts
python tools/neon_import.py  # Shows summary at end
```

## Rolling Back

If you need to return to BigQuery:

```bash
# Just change the environment variable
export DATABASE_TYPE=bigquery
# Restart application
```

All BigQuery data remains unchanged.

## Monitoring

### Check Neon Dashboard

1. Visit https://console.neon.tech
2. View query usage and performance
3. Monitor storage consumption
4. Check connection status

### Application Logs

```bash
# Check service initialization
grep -i "service initialized" logs/app.log

# Check query performance
grep -i "query executed" logs/app.log
```

## Environment Variables Reference

```bash
# Database Selection
DATABASE_TYPE=neon                          # or "bigquery"

# Neon Configuration
DATABASE_URL=postgresql://user:pass@host/db
DATABASE_POOL_SIZE=20                       # Connection pool size
DATABASE_TIMEOUT=30                         # Query timeout in seconds

# BigQuery (if using)
GOOGLE_CLOUD_PROJECT=coins2025
BQ_DATASET=db
BQ_TABLE=catalog
BQ_HISTORY_TABLE=history
BQ_GROUPS_TABLE=groups
BQ_GROUP_USERS_TABLE=group_users

# Application
APP_ENV=development                         # or "production"
CACHE_DURATION_MINUTES=5                   # Cache TTL (dev) or 15 (prod)
```

## Files Created/Modified

### New Files
- `tools/neon_schema.sql` - PostgreSQL schema definition
- `tools/neon_import.py` - CSV data import script
- `app/services/neon_service.py` - Neon database service

### Modified Files
- `app/config.py` - Added Neon configuration options
- `main.py` - Added database type selection logic

### Unchanged
- All router files
- All model files
- All existing .env templates
- BigQuery service (still available)

## Next Steps

1. ✅ Create Neon project
2. ✅ Set up environment variables
3. ✅ Import data from CSVs
4. ✅ Test application with Neon
5. ✅ Update CI/CD pipelines if needed
6. ✅ Monitor performance in production
7. (Optional) Decommission BigQuery after validation

## Support

For issues:
1. Check the troubleshooting section above
2. Review application logs
3. Verify Neon connection string format
4. Check CSV file formats in `data/` directory

For Neon-specific help: https://neon.tech/docs
For PostgreSQL help: https://www.postgresql.org/docs/
