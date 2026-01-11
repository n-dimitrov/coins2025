#!/usr/bin/env python3
"""
Neon Database Import Script

Loads CSV data from the data/ folder into a Neon PostgreSQL database.
Run this after setting up your Neon database and running neon_schema.sql.

Usage:
    python tools/neon_import.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string (e.g., postgresql://user:password@host/dbname)
"""

import asyncio
import csv
from datetime import datetime
import logging
import psycopg
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def import_catalog(conn, csv_path: str) -> int:
    """Import coins from catalog.csv"""
    logger.info(f"Starting catalog import from {csv_path}")

    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"Catalog file not found: {csv_path}")

    rows_imported = 0
    current_time = datetime.now()

    try:
        async with conn.cursor() as cur:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    try:
                        # Map CSV columns to database columns
                        query = """
                        INSERT INTO catalog (coin_type, year, country, series, value, coin_id, image_url, feature, volume, created_at, updated_at)
                        VALUES (%(coin_type)s, %(year)s, %(country)s, %(series)s, %(value)s, %(coin_id)s, %(image_url)s, %(feature)s, %(volume)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (coin_id) DO NOTHING
                        """

                        params = {
                            'coin_type': row.get('type', '').strip() or None,
                            'year': int(row.get('year', 0)) if row.get('year') else None,
                            'country': row.get('country', '').strip() or None,
                            'series': row.get('series', '').strip() or None,
                            'value': float(row.get('value', 0)) if row.get('value') else None,
                            'coin_id': row.get('id', '').strip() or None,
                            'image_url': row.get('image', '').strip() or None,
                            'feature': row.get('feature', '').strip() or None,
                            'volume': row.get('volume', '').strip() or None,
                            'created_at': current_time,
                            'updated_at': current_time
                        }

                        # Skip if required fields are missing
                        if not all([params['coin_type'], params['year'], params['country'], params['series'], params['value'], params['coin_id']]):
                            logger.warning(f"Row {row_num} has missing required fields, skipping")
                            continue

                        await cur.execute(query, params)
                        rows_imported += 1

                        if row_num % 100 == 0:
                            logger.info(f"Imported {rows_imported} coins so far...")

                    except Exception as e:
                        logger.error(f"Error importing row {row_num}: {str(e)}")
                        logger.error(f"Row data: {row}")
                        raise

        logger.info(f"Successfully imported {rows_imported} coins to catalog table")
        return rows_imported

    except Exception as e:
        logger.error(f"Error importing catalog: {str(e)}")
        raise


async def import_groups(conn, csv_path: str) -> int:
    """Import groups from groups.csv"""
    logger.info(f"Starting groups import from {csv_path}")

    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"Groups file not found: {csv_path}")

    rows_imported = 0

    try:
        async with conn.cursor() as cur:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    try:
                        group_key = row.get('group', '').strip()
                        name = row.get('name', '').strip()

                        if not group_key or not name:
                            logger.warning(f"Row {row_num} has missing fields, skipping")
                            continue

                        query = """
                        INSERT INTO groups (group_key, name, is_active)
                        VALUES (%(group_key)s, %(name)s, true)
                        ON CONFLICT (group_key) DO NOTHING
                        """

                        await cur.execute(query, {'group_key': group_key, 'name': name})
                        rows_imported += 1

                        if row_num % 10 == 0:
                            logger.info(f"Imported {rows_imported} groups so far...")

                    except Exception as e:
                        logger.error(f"Error importing row {row_num}: {str(e)}")
                        logger.error(f"Row data: {row}")
                        raise

        logger.info(f"Successfully imported {rows_imported} groups")
        return rows_imported

    except Exception as e:
        logger.error(f"Error importing groups: {str(e)}")
        raise


async def import_group_users(conn, csv_path: str) -> int:
    """Import group users from group_users.csv"""
    logger.info(f"Starting group_users import from {csv_path}")

    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"Group users file not found: {csv_path}")

    rows_imported = 0

    try:
        async with conn.cursor() as cur:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    try:
                        user_name = row.get('user', '').strip()
                        alias = row.get('alias', '').strip()

                        if not user_name:
                            logger.warning(f"Row {row_num} has missing user field, skipping")
                            continue

                        # Get group_id for 'hippo' group (assuming it exists from groups.csv import)
                        get_group_query = "SELECT id FROM groups WHERE group_key = 'hippo' LIMIT 1"
                        async with conn.cursor() as get_cur:
                            await get_cur.execute(get_group_query)
                            result = await get_cur.fetchone()

                        if not result:
                            logger.warning(f"Group 'hippo' not found, skipping user {user_name}")
                            continue

                        group_id = result[0]

                        query = """
                        INSERT INTO group_users (group_id, name, alias, is_active)
                        VALUES (%(group_id)s, %(name)s, %(alias)s, true)
                        ON CONFLICT (group_id, name) DO NOTHING
                        """

                        await cur.execute(query, {
                            'group_id': str(group_id),
                            'name': user_name,
                            'alias': alias
                        })
                        rows_imported += 1

                        if row_num % 10 == 0:
                            logger.info(f"Imported {rows_imported} group users so far...")

                    except Exception as e:
                        logger.error(f"Error importing row {row_num}: {str(e)}")
                        logger.error(f"Row data: {row}")
                        raise

        logger.info(f"Successfully imported {rows_imported} group users")
        return rows_imported

    except Exception as e:
        logger.error(f"Error importing group_users: {str(e)}")
        raise


async def import_history(conn, csv_path: str) -> int:
    """Import history from history.csv"""
    logger.info(f"Starting history import from {csv_path}")

    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"History file not found: {csv_path}")

    rows_imported = 0
    current_time = datetime.now()

    try:
        async with conn.cursor() as cur:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    try:
                        name = row.get('name', '').strip()
                        coin_id = row.get('id', '').strip()
                        date_str = row.get('date', '').strip()

                        if not all([name, coin_id, date_str]):
                            logger.warning(f"Row {row_num} has missing fields, skipping")
                            continue

                        # Parse timestamp
                        try:
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except ValueError:
                            logger.warning(f"Row {row_num} has invalid date format '{date_str}', skipping")
                            continue

                        query = """
                        INSERT INTO history (name, coin_id, date, created_at, created_by, is_active)
                        VALUES (%(name)s, %(coin_id)s, %(date)s, %(created_at)s, 'import', true)
                        """

                        await cur.execute(query, {
                            'name': name,
                            'coin_id': coin_id,
                            'date': date_obj,
                            'created_at': current_time
                        })
                        rows_imported += 1

                        if row_num % 100 == 0:
                            logger.info(f"Imported {rows_imported} history records so far...")

                    except Exception as e:
                        logger.error(f"Error importing row {row_num}: {str(e)}")
                        logger.error(f"Row data: {row}")
                        raise

        logger.info(f"Successfully imported {rows_imported} history records")
        return rows_imported

    except Exception as e:
        logger.error(f"Error importing history: {str(e)}")
        raise


async def main():
    """Main import function"""
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Determine data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'

    logger.info(f"Database URL: {database_url[:50]}...")
    logger.info(f"Data directory: {data_dir}")

    try:
        # Connect to database
        logger.info("Connecting to Neon database...")
        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            logger.info("Connected successfully!")

            # Import data in order (groups before group_users due to FK, catalog before history)
            logger.info("\n=== Starting data import ===\n")

            groups_count = await import_groups(conn, str(data_dir / 'groups.csv'))
            group_users_count = await import_group_users(conn, str(data_dir / 'group_users.csv'))
            catalog_count = await import_catalog(conn, str(data_dir / 'catalog.csv'))
            history_count = await import_history(conn, str(data_dir / 'history.csv'))

            # Commit all changes
            await conn.commit()

            logger.info("\n=== Import Summary ===")
            logger.info(f"Groups imported: {groups_count}")
            logger.info(f"Group users imported: {group_users_count}")
            logger.info(f"Catalog entries imported: {catalog_count}")
            logger.info(f"History records imported: {history_count}")
            logger.info("\nImport completed successfully!")

    except Exception as e:
        logger.error(f"\nFatal error during import: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
