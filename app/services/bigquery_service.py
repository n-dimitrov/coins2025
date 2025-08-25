from google.cloud import bigquery
from typing import List, Dict, Optional, Any
import os
from datetime import datetime, timedelta
import logging
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.google_cloud_project)
        self.dataset_id = settings.bq_dataset
        self.table_id = settings.bq_table
        self._cache = {}
        self._cache_duration = timedelta(minutes=settings.cache_duration_minutes)

    def _get_cache_key(self, query: str, params: dict) -> str:
        """Generate cache key from query and parameters."""
        return f"{query}:{str(sorted(params.items()))}"

    async def _get_cached_or_query(self, query: str, params: dict = None) -> List[Dict[str, Any]]:
        """Get cached results or execute query."""
        cache_key = self._get_cache_key(query, params or {})
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_duration:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_data

        # Execute query in thread pool since BigQuery client is synchronous
        def execute_query():
            job_config = bigquery.QueryJobConfig()
            if params:
                query_parameters = []
                for k, v in params.items():
                    if isinstance(v, int):
                        query_parameters.append(bigquery.ScalarQueryParameter(k, "INT64", v))
                    elif isinstance(v, float):
                        query_parameters.append(bigquery.ScalarQueryParameter(k, "FLOAT64", v))
                    else:
                        query_parameters.append(bigquery.ScalarQueryParameter(k, "STRING", str(v)))
                job_config.query_parameters = query_parameters

            try:
                logger.info(f"Executing BigQuery: {query[:100]}...")
                query_job = self.client.query(query, job_config=job_config)
                results = [dict(row) for row in query_job.result()]
                logger.info(f"Query executed successfully, got {len(results)} results")
                return results
                
            except Exception as e:
                logger.error(f"BigQuery error: {str(e)}")
                raise

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, execute_query)
        
        # Cache results
        self._cache[cache_key] = (results, datetime.now())
        logger.info(f"Query executed successfully, cached {len(results)} results")
        return results

    async def get_coins(self, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get coins with optional filters."""
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = @coin_type")
                params['coin_type'] = filters['coin_type']
            
            if filters.get('value'):
                where_clauses.append("value = @value")
                params['value'] = str(filters['value'])
            
            if filters.get('country'):
                where_clauses.append("country = @country")
                params['country'] = filters['country']
            
            if filters.get('series'):
                where_clauses.append("series = @series")
                params['series'] = filters['series']

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE {where_sql}
        ORDER BY year DESC, country ASC
        LIMIT {limit} OFFSET {offset}
        """

        return await self._get_cached_or_query(query, params)

    async def get_coin_by_id(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific coin by ID."""
        query = f"""
        SELECT *
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE coin_id = @coin_id
        """
        
        results = await self._get_cached_or_query(query, {'coin_id': coin_id})
        return results[0] if results else None

    async def get_stats(self) -> Dict[str, int]:
        """Get collection statistics."""
        query = f"""
        SELECT 
            COUNT(*) as total_coins,
            COUNT(DISTINCT country) as total_countries,
            COUNTIF(coin_type = 'RE') as regular_coins,
            COUNTIF(coin_type = 'CC') as commemorative_coins
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        """
        
        results = await self._get_cached_or_query(query)
        return dict(results[0]) if results else {}

    async def get_filter_options(self) -> Dict[str, List]:
        """Get available filter options."""
        # Get countries and denominations from all coins
        general_query = f"""
        SELECT 
            ARRAY_AGG(DISTINCT country ORDER BY country) as countries,
            ARRAY_AGG(DISTINCT value ORDER BY value DESC) as denominations
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        """
        
        # Get commemorative series only from CC coins
        commemorative_query = f"""
        SELECT 
            ARRAY_AGG(DISTINCT series ORDER BY series) as commemoratives
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE series LIKE 'CC-%'
        """
        
        general_results = await self._get_cached_or_query(general_query)
        commemorative_results = await self._get_cached_or_query(commemorative_query)
        
        result = {}
        if general_results:
            result.update(general_results[0])
        if commemorative_results:
            result.update(commemorative_results[0])
            
        return result

    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    # Group-related methods
    async def get_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get group by name."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        WHERE `group` = @group_name
        """
        
        results = await self._get_cached_or_query(query, {'group_name': group_name})
        return results[0] if results else None

    async def get_group_users(self, group_id: int) -> List[Dict[str, Any]]:
        """Get users for a specific group."""
        query = f"""
        SELECT gu.*, g.name as group_name 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu
        JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}` g 
            ON gu.group_id = g.id
        WHERE gu.group_id = @group_id
        ORDER BY gu.alias
        """
        
        return await self._get_cached_or_query(query, {'group_id': group_id})

    async def get_coin_ownership_by_group(self, coin_id: str, group_id: int) -> List[Dict[str, Any]]:
        """Get ownership information for a specific coin within a group."""
        query = f"""
        WITH latest_ownership AS (
            SELECT 
                h.name, h.coin_id, h.date, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
            WHERE h.coin_id = @coin_id
        )
        SELECT 
            lo.name as owner,
            gu.alias as alias,
            lo.date as acquired_date
        FROM latest_ownership lo
        JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu 
            ON lo.name = gu.user AND gu.group_id = @group_id
        WHERE lo.rn = 1 AND lo.is_active = true
        ORDER BY lo.date DESC
        """
        
        return await self._get_cached_or_query(query, {
            'coin_id': coin_id, 
            'group_id': group_id
        })

    async def get_coins_with_ownership(self, group_id: int, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get coins with ownership information for a group."""
        where_clauses = []
        params = {'group_id': group_id}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("c.coin_type = @coin_type")
                params['coin_type'] = filters['coin_type']
            
            if filters.get('value'):
                where_clauses.append("c.value = @value")
                params['value'] = str(filters['value'])
            
            if filters.get('country'):
                where_clauses.append("c.country = @country")
                params['country'] = filters['country']
            
            if filters.get('series'):
                where_clauses.append("c.series = @series")
                params['series'] = filters['series']
            
            if filters.get('owned_by'):
                where_clauses.append("h.name = @owned_by")
                params['owned_by'] = filters['owned_by']
            
            if filters.get('ownership_status'):
                if filters['ownership_status'] == 'owned':
                    where_clauses.append("h.coin_id IS NOT NULL")
                elif filters['ownership_status'] == 'missing':
                    where_clauses.append("h.coin_id IS NULL")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        WITH latest_ownership AS (
            SELECT 
                h.name, h.coin_id, h.date, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        ),
        coin_ownership AS (
            SELECT 
                c.*,
                lo.name as owner,
                gu.alias as owner_alias,
                lo.date as acquired_date
            FROM `{self.client.project}.{self.dataset_id}.{self.table_id}` c
            LEFT JOIN latest_ownership lo 
                ON c.coin_id = lo.coin_id AND lo.rn = 1 AND lo.is_active = true
            LEFT JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu 
                ON lo.name = gu.user AND gu.group_id = @group_id
            WHERE {where_sql}
        )
        SELECT 
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume,
            ARRAY_AGG(
                CASE WHEN owner IS NOT NULL THEN
                    STRUCT(owner, owner_alias as alias, acquired_date)
                ELSE NULL END
                IGNORE NULLS
                ORDER BY acquired_date DESC
            ) as owners
        FROM coin_ownership
        GROUP BY coin_type, year, country, series, value, coin_id, image_url, feature, volume
        ORDER BY year DESC, country ASC
        LIMIT {limit} OFFSET {offset}
        """

        return await self._get_cached_or_query(query, params)

    async def get_group_stats(self, group_id: int) -> Dict[str, int]:
        """Get statistics for a group."""
        query = f"""
        WITH latest_ownership AS (
            SELECT 
                h.name, h.coin_id, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        )
        SELECT 
            COUNT(DISTINCT gu.user) as total_members,
            COUNT(DISTINCT CASE WHEN lo.is_active = true THEN lo.coin_id END) as total_coins_owned,
            COUNT(CASE WHEN lo.is_active = true THEN 1 END) as total_ownership_records
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu
        LEFT JOIN latest_ownership lo 
            ON gu.user = lo.name AND lo.rn = 1
        WHERE gu.group_id = @group_id
        """
        
        results = await self._get_cached_or_query(query, {'group_id': group_id})
        return dict(results[0]) if results else {}

    # Ownership management methods
    async def add_coin_ownership(self, name: str, coin_id: str, date: datetime, created_by: str = None) -> str:
        """Add a new coin ownership record."""
        import uuid
        from datetime import datetime as dt
        
        record_id = str(uuid.uuid4())
        current_time = dt.now()
        
        # First check if user already owns this coin
        existing = await self.get_current_coin_ownership(coin_id, name)
        if existing:
            raise ValueError(f"User {name} already owns coin {coin_id}")
        
        query = f"""
        INSERT INTO `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}`
        (id, name, coin_id, date, created_at, created_by, is_active)
        VALUES (@id, @name, @coin_id, @date, @created_at, @created_by, true)
        """
        
        params = {
            'id': record_id,
            'name': name,
            'coin_id': coin_id,
            'date': date,
            'created_at': current_time,
            'created_by': created_by or 'api',
        }
        
        # Execute query in thread pool
        def execute_insert():
            job_config = bigquery.QueryJobConfig()
            query_parameters = []
            for k, v in params.items():
                if k in ['date', 'created_at']:
                    query_parameters.append(bigquery.ScalarQueryParameter(k, "TIMESTAMP", v))
                elif k == 'is_active':
                    query_parameters.append(bigquery.ScalarQueryParameter(k, "BOOL", v))
                else:
                    query_parameters.append(bigquery.ScalarQueryParameter(k, "STRING", str(v)))
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_insert)
        
        # Invalidate related cache
        await self._invalidate_ownership_cache(coin_id=coin_id, user_name=name)
        
        return record_id

    async def remove_coin_ownership(self, name: str, coin_id: str, removal_date: datetime, created_by: str = None) -> str:
        """Remove coin ownership by adding a removal record."""
        import uuid
        from datetime import datetime as dt
        
        # Check if user currently owns this coin
        current_ownership = await self.get_current_coin_ownership(coin_id, name)
        if not current_ownership:
            raise ValueError(f"User {name} does not currently own coin {coin_id}")
        
        record_id = str(uuid.uuid4())
        current_time = dt.now()
        
        query = f"""
        INSERT INTO `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}`
        (id, name, coin_id, date, created_at, created_by, is_active)
        VALUES (@id, @name, @coin_id, @removal_date, @created_at, @created_by, false)
        """
        
        params = {
            'id': record_id,
            'name': name,
            'coin_id': coin_id,
            'removal_date': removal_date,
            'created_at': current_time,
            'created_by': created_by or 'api',
        }
        
        # Execute query in thread pool
        def execute_insert():
            job_config = bigquery.QueryJobConfig()
            query_parameters = []
            for k, v in params.items():
                if k in ['removal_date', 'created_at']:
                    query_parameters.append(bigquery.ScalarQueryParameter(k, "TIMESTAMP", v))
                else:
                    query_parameters.append(bigquery.ScalarQueryParameter(k, "STRING", str(v)))
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_insert)
        
        # Invalidate related cache
        await self._invalidate_ownership_cache(coin_id=coin_id, user_name=name)
        
        return record_id

    async def get_current_coin_ownership(self, coin_id: str, name: str = None) -> List[Dict[str, Any]]:
        """Get current owners of a coin (latest active record per user)."""
        where_clause = "WHERE h.coin_id = @coin_id"
        params = {'coin_id': coin_id}
        
        if name:
            where_clause += " AND h.name = @name"
            params['name'] = name
            
        query = f"""
        WITH latest_records AS (
            SELECT 
                h.name, h.coin_id, h.date, h.is_active, h.created_at,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
            {where_clause}
        )
        SELECT name, date as acquired_date
        FROM latest_records
        WHERE rn = 1 AND is_active = true
        """
        
        return await self._get_cached_or_query(query, params)

    async def get_user_owned_coins(self, name: str, group_id: int = None) -> List[Dict[str, Any]]:
        """Get all coins currently owned by a user."""
        group_join = ""
        group_where = ""
        params = {'name': name}
        
        if group_id:
            group_join = f"JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu ON lr.name = gu.user"
            group_where = "AND gu.group_id = @group_id"
            params['group_id'] = group_id
            
        query = f"""
        WITH latest_records AS (
            SELECT 
                h.name, h.coin_id, h.date, h.is_active, h.created_at,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
            WHERE h.name = @name
        )
        SELECT lr.coin_id, lr.date as acquired_date, c.coin_type, c.year, c.country, c.series, c.value
        FROM latest_records lr
        {group_join}
        JOIN `{self.client.project}.{self.dataset_id}.{self.table_id}` c ON lr.coin_id = c.coin_id
        WHERE lr.rn = 1 AND lr.is_active = true {group_where}
        ORDER BY lr.date DESC
        """
        
        return await self._get_cached_or_query(query, params)

    async def _invalidate_ownership_cache(self, coin_id: str = None, user_name: str = None, group_id: int = None):
        """Invalidate cache entries related to ownership changes."""
        keys_to_remove = []
        
        for cache_key in list(self._cache.keys()):
            # Invalidate if cache key contains the affected coin_id or user_name
            if (coin_id and coin_id in cache_key) or \
               (user_name and user_name in cache_key) or \
               (group_id and str(group_id) in cache_key) or \
               'ownership' in cache_key.lower() or \
               'coins_with_ownership' in cache_key.lower():
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._cache[key]
            
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries due to ownership change")
