from google.cloud import bigquery
from typing import List, Dict, Optional, Any
import os
from datetime import datetime, timedelta
import logging
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

class BigQueryService:
    # Shared cache across all service instances to avoid stale reads after reset
    _global_cache: Dict[str, Any] = {}
    def __init__(self):
        self.client = bigquery.Client(project=settings.google_cloud_project)
        self.dataset_id = settings.bq_dataset
        self.table_id = settings.bq_table
        # Use a shared cache so clearing in one place affects all instances
        self._cache = self.__class__._global_cache
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
        """Get group by group_key (legacy method for backward compatibility)."""
        return await self.get_group_by_key(group_name)

    async def get_group_users(self, group_id: str) -> List[Dict[str, Any]]:
        """Get active users for a specific group."""
        query = f"""
        SELECT gu.*, g.name as group_name 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu
        JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}` g 
            ON gu.group_id = g.id
        WHERE gu.group_id = @group_id AND gu.is_active = true AND g.is_active = true
        ORDER BY gu.alias
        """
        
        return await self._get_cached_or_query(query, {'group_id': group_id})

    async def get_coin_ownership_by_group(self, coin_id: str, group_id: str) -> List[Dict[str, Any]]:
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
            COALESCE(gu.alias, lo.name) as alias,
            lo.date as acquired_date
        FROM latest_ownership lo
        JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu 
            ON lo.name = gu.name AND gu.group_id = @group_id
        WHERE lo.rn = 1 AND lo.is_active = true AND gu.is_active = true
        ORDER BY lo.date DESC
        """
        
        return await self._get_cached_or_query(query, {
            'coin_id': coin_id, 
            'group_id': group_id
        })

    async def get_coins_with_ownership(self, group_id: str, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
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
                COALESCE(gu.alias, lo.name) as owner_alias,
                lo.date as acquired_date
            FROM `{self.client.project}.{self.dataset_id}.{self.table_id}` c
            LEFT JOIN latest_ownership lo 
                ON c.coin_id = lo.coin_id AND lo.rn = 1 AND lo.is_active = true
            LEFT JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu 
                ON lo.name = gu.name AND gu.group_id = @group_id AND gu.is_active = true
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

    async def get_group_stats(self, group_id: str) -> Dict[str, int]:
        """Get statistics for a group."""
        query = f"""
        WITH latest_ownership AS (
            SELECT 
                h.name, h.coin_id, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.date DESC, h.created_at DESC) as rn
            FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        )
        SELECT 
            COUNT(DISTINCT gu.name) as total_members,
            COUNT(DISTINCT CASE WHEN lo.is_active = true THEN lo.coin_id END) as total_coins_owned,
            COUNT(CASE WHEN lo.is_active = true THEN 1 END) as total_ownership_records
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu
        LEFT JOIN latest_ownership lo 
            ON gu.name = lo.name AND lo.rn = 1
        WHERE gu.group_id = @group_id AND gu.is_active = true
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

    async def get_user_owned_coins(self, name: str, group_id: str = None) -> List[Dict[str, Any]]:
        """Get all coins currently owned by a user."""
        group_join = ""
        group_where = ""
        params = {'name': name}
        
        if group_id:
            group_join = f"JOIN `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}` gu ON lr.name = gu.name AND gu.is_active = true"
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

    async def _invalidate_ownership_cache(self, coin_id: str = None, user_name: str = None, group_id: str = None):
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

    # Group management methods
    async def create_group(self, group_key: str, name: str) -> str:
        """Create a new group."""
        import uuid
        from datetime import datetime as dt
        
        # Check if group_key already exists
        existing = await self.get_group_by_key(group_key)
        if existing:
            raise ValueError(f"Group with key '{group_key}' already exists")
        
        group_id = str(uuid.uuid4())
        
        query = f"""
        INSERT INTO `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        (id, group_key, name, is_active)
        VALUES (@id, @group_key, @name, true)
        """
        
        params = {
            'id': group_id,
            'group_key': group_key,
            'name': name
        }
        
        def execute_insert():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [
                bigquery.ScalarQueryParameter("id", "STRING", group_id),
                bigquery.ScalarQueryParameter("group_key", "STRING", group_key),
                bigquery.ScalarQueryParameter("name", "STRING", name)
            ]
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_insert)
        
        # Invalidate group cache
        self._invalidate_group_cache()
        
        return group_id

    async def update_group(self, group_id: str, name: str) -> bool:
        """Update group name."""
        # Check if group exists and is active
        existing = await self.get_group_by_id(group_id)
        if not existing or not existing.get('is_active'):
            raise ValueError(f"Group with id '{group_id}' not found or inactive")
        
        query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        SET name = @name
        WHERE id = @group_id AND is_active = true
        """
        
        def execute_update():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [
                bigquery.ScalarQueryParameter("name", "STRING", name),
                bigquery.ScalarQueryParameter("group_id", "STRING", group_id)
            ]
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_update)
        
        # Invalidate group cache
        self._invalidate_group_cache()
        
        return True

    async def delete_group(self, group_id: str) -> bool:
        """Soft delete a group and all its members."""
        # Check if group exists and is active
        existing = await self.get_group_by_id(group_id)
        if not existing or not existing.get('is_active'):
            raise ValueError(f"Group with id '{group_id}' not found or inactive")
        
        # Soft delete group
        group_query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        SET is_active = false
        WHERE id = @group_id
        """
        
        # Soft delete all group members
        users_query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        SET is_active = false
        WHERE group_id = @group_id
        """
        
        def execute_deletes():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [bigquery.ScalarQueryParameter("group_id", "STRING", group_id)]
            job_config.query_parameters = query_parameters
            
            # Delete group
            query_job = self.client.query(group_query, job_config=job_config)
            query_job.result()
            
            # Delete group members
            query_job = self.client.query(users_query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_deletes)
        
        # Invalidate cache
        self._invalidate_group_cache()
        
        return True

    async def get_group_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group by ID."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        WHERE id = @group_id AND is_active = true
        """
        
        results = await self._get_cached_or_query(query, {'group_id': group_id})
        return results[0] if results else None

    async def get_group_by_key(self, group_key: str) -> Optional[Dict[str, Any]]:
        """Get active group by key."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        WHERE group_key = @group_key AND is_active = true
        """
        
        results = await self._get_cached_or_query(query, {'group_key': group_key})
        return results[0] if results else None

    async def list_active_groups(self) -> List[Dict[str, Any]]:
        """List all active groups."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_groups_table}`
        WHERE is_active = true
        ORDER BY name
        """
        
        return await self._get_cached_or_query(query, {})

    # Group user management methods
    async def add_user_to_group(self, group_id: str, name: str, alias: str) -> str:
        """Add user to group."""
        import uuid
        
        # Check if group exists and is active
        group = await self.get_group_by_id(group_id)
        if not group:
            raise ValueError(f"Group with id '{group_id}' not found or inactive")
        
        # Check if user already exists in group
        existing_user = await self.get_group_user(group_id, name)
        if existing_user:
            raise ValueError(f"User '{name}' already exists in group")
        
        user_id = str(uuid.uuid4())
        
        query = f"""
        INSERT INTO `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        (id, group_id, name, alias, is_active)
        VALUES (@id, @group_id, @name, @alias, true)
        """
        
        def execute_insert():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [
                bigquery.ScalarQueryParameter("id", "STRING", user_id),
                bigquery.ScalarQueryParameter("group_id", "STRING", group_id),
                bigquery.ScalarQueryParameter("name", "STRING", name),
                bigquery.ScalarQueryParameter("alias", "STRING", alias)
            ]
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_insert)
        
        # Invalidate cache
        self._invalidate_group_cache()
        
        return user_id

    async def update_group_user(self, group_id: str, name: str, alias: str) -> bool:
        """Update user alias in group."""
        # Check if user exists in group
        existing_user = await self.get_group_user(group_id, name)
        if not existing_user:
            raise ValueError(f"User '{name}' not found in group")
        
        query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        SET alias = @alias
        WHERE group_id = @group_id AND name = @name AND is_active = true
        """
        
        def execute_update():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [
                bigquery.ScalarQueryParameter("alias", "STRING", alias),
                bigquery.ScalarQueryParameter("group_id", "STRING", group_id),
                bigquery.ScalarQueryParameter("name", "STRING", name)
            ]
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_update)
        
        # Invalidate cache
        self._invalidate_group_cache()
        
        return True

    async def remove_user_from_group(self, group_id: str, name: str) -> bool:
        """Remove user from group."""
        # Check if user exists in group
        existing_user = await self.get_group_user(group_id, name)
        if not existing_user:
            raise ValueError(f"User '{name}' not found in group")
        
        query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        SET is_active = false
        WHERE group_id = @group_id AND name = @name
        """
        
        def execute_update():
            job_config = bigquery.QueryJobConfig()
            query_parameters = [
                bigquery.ScalarQueryParameter("group_id", "STRING", group_id),
                bigquery.ScalarQueryParameter("name", "STRING", name)
            ]
            job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, execute_update)
        
        # Invalidate cache
        self._invalidate_group_cache()
        
        return True

    async def get_group_user(self, group_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Get specific user in group."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        WHERE group_id = @group_id AND name = @name AND is_active = true
        """
        
        results = await self._get_cached_or_query(query, {'group_id': group_id, 'name': name})
        return results[0] if results else None

    async def get_active_group_users(self, group_id: str) -> List[Dict[str, Any]]:
        """Get all active users in group."""
        query = f"""
        SELECT * 
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_group_users_table}`
        WHERE group_id = @group_id AND is_active = true
        ORDER BY alias
        """
        
        return await self._get_cached_or_query(query, {'group_id': group_id})

    async def _invalidate_group_cache(self):
        """Invalidate cache entries related to groups."""
        keys_to_remove = []
        
        for cache_key in list(self._cache.keys()):
            if 'group' in cache_key.lower():
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._cache[key]
            
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries due to group change")

    async def get_existing_coin_ids(self, coin_ids: List[str]) -> List[str]:
        """Get existing coin IDs from the database."""
        if not coin_ids:
            return []
        
        # Create parameterized query for coin IDs
        placeholders = ', '.join([f"@coin_id_{i}" for i in range(len(coin_ids))])
        params = {f"coin_id_{i}": coin_id for i, coin_id in enumerate(coin_ids)}
        
        query = f"""
        SELECT DISTINCT coin_id
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE coin_id IN ({placeholders})
        """
        
        results = await self._get_cached_or_query(query, params)
        return [row['coin_id'] for row in results]

    async def import_coins(self, coins: List[Dict[str, Any]]) -> int:
        """Import coins to BigQuery table."""
        if not coins:
            return 0
        
        def execute_import():
            try:
                table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
                table = self.client.get_table(table_ref)
                
                # Prepare rows for BigQuery
                rows_to_insert = []
                current_time = datetime.utcnow().isoformat() + 'Z'  # ISO format with Z suffix for UTC
                
                for coin in coins:
                    row = {
                        'coin_type': coin['coin_type'],
                        'year': coin['year'],
                        'country': coin['country'],
                        'series': coin['series'],
                        'value': coin['value'],
                        'coin_id': coin['coin_id'],
                        'image_url': coin.get('image_url'),
                        'feature': coin.get('feature'),
                        'volume': coin.get('volume'),
                        'created_at': current_time,
                        'updated_at': current_time
                    }
                    rows_to_insert.append(row)
                
                # Insert rows
                errors = self.client.insert_rows_json(table, rows_to_insert)
                
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    raise Exception(f"Failed to insert rows: {errors}")
                
                logger.info(f"Successfully imported {len(rows_to_insert)} coins to BigQuery")
                
                # Clear cache to force refresh
                self._cache.clear()
                
                return len(rows_to_insert)
                
            except Exception as e:
                logger.error(f"Error importing coins to BigQuery: {str(e)}")
                raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, execute_import)

    async def get_all_coins_for_export(self) -> List[Dict[str, Any]]:
        """Get all coins sorted by year, series, country for export."""
        query = f"""
        SELECT 
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        ORDER BY year ASC, series ASC, country ASC
        """
        
        return await self._get_cached_or_query(query, {})

    async def get_coins_for_admin_view(self, filters: dict = None, limit: int = 100, offset: int = 0, search: str = None) -> List[Dict[str, Any]]:
        """Get coins for admin view with filtering and pagination."""
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = @coin_type")
                params['coin_type'] = filters['coin_type']
            
            if filters.get('country'):
                where_clauses.append("country = @country")
                params['country'] = filters['country']

        if search:
            where_clauses.append("(LOWER(country) LIKE @search OR LOWER(series) LIKE @search OR LOWER(feature) LIKE @search)")
            params['search'] = f"%{search.lower()}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE {where_sql}
        ORDER BY year DESC, country ASC, series ASC
        LIMIT {limit} OFFSET {offset}
        """
        
        return await self._get_cached_or_query(query, params)

    # Catalog reset utilities
    async def delete_catalog_table(self) -> dict:
        """Delete the main catalog table if it exists."""
        def _delete():
            try:
                table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
                self.client.delete_table(table_ref, not_found_ok=True)
                logger.info(f"Deleted table {self.dataset_id}.{self.table_id}")
                return {'success': True, 'message': 'Table deleted'}
            except Exception as e:
                logger.error(f"Error deleting table: {str(e)}")
                return {'success': False, 'message': str(e)}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _delete)

    async def create_catalog_table(self) -> dict:
        """Create the catalog table with schema matching the importer expectations."""
        def _create():
            try:
                table_ref = self.client.dataset(self.dataset_id).table(self.table_id)

                # Define schema similar to tools/import_catalog.py
                schema = [
                    bigquery.SchemaField("coin_type", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("year", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("country", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("series", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("value", "FLOAT", mode="REQUIRED"),
                    bigquery.SchemaField("coin_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("image_url", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("feature", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("volume", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                ]

                table = bigquery.Table(table_ref, schema=schema)
                # Partition by created_at and cluster for performance
                table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY, field="created_at")
                table.clustering_fields = ["country", "coin_type", "year"]

                self.client.create_table(table)
                logger.info(f"Created table {self.dataset_id}.{self.table_id}")
                return {'success': True, 'message': 'Table created'}
            except Exception as e:
                logger.error(f"Error creating table: {str(e)}")
                return {'success': False, 'message': str(e)}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _create)

    async def reset_catalog_table(self) -> dict:
        """Delete and recreate the catalog table. Returns dict with success/message."""
        # Optionally, we could backup table here before deletion.
        delete_res = await self.delete_catalog_table()
        if not delete_res.get('success'):
            return {'success': False, 'message': f"Delete failed: {delete_res.get('message')}"}

        create_res = await self.create_catalog_table()
        if not create_res.get('success'):
            return {'success': False, 'message': f"Create failed: {create_res.get('message')}"}

        # Clear caches
        self._cache.clear()
        return {'success': True, 'message': 'Catalog table deleted and recreated'}

    async def get_coins_count(self, filters: dict = None, search: str = None) -> int:
        """Get total count of coins for pagination."""
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = @coin_type")
                params['coin_type'] = filters['coin_type']
            
            if filters.get('country'):
                where_clauses.append("country = @country")
                params['country'] = filters['country']

        if search:
            where_clauses.append("(LOWER(country) LIKE @search OR LOWER(series) LIKE @search OR LOWER(feature) LIKE @search)")
            params['search'] = f"%{search.lower()}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT COUNT(*) as total
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE {where_sql}
        """
        
        result = await self._get_cached_or_query(query, params)
        return result[0]['total'] if result else 0

    async def get_coins_filter_options(self) -> Dict[str, Any]:
        """Get filter options for coins admin view."""
        # Get unique countries
        countries_query = f"""
        SELECT DISTINCT country
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE country IS NOT NULL AND country != ''
        ORDER BY country ASC
        """
        
        countries_result = await self._get_cached_or_query(countries_query, {})
        countries = [row['country'] for row in countries_result]
        
        return {
            "countries": countries
        }

    # History management methods
    async def get_all_history(self) -> List[Dict[str, Any]]:
        """Get all history entries with coin identifiers."""
        query = f"""
        SELECT 
            h.name, 
            COALESCE(h.coin_id, h.id) as id,  -- Use coin_id if available, fallback to id for legacy data
            h.date
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        ORDER BY h.date DESC
        """
        
        return await self._get_cached_or_query(query, {})

    async def import_history_batch(self, history_entries: List) -> int:
        """Import a batch of history entries."""
        def execute_batch_insert():
            import uuid
            from datetime import datetime as dt
            
            table_ref = self.client.dataset(self.dataset_id).table(settings.bq_history_table)
            table = self.client.get_table(table_ref)
            
            rows_to_insert = []
            current_time = dt.now().isoformat() + 'Z'  # ISO format for BigQuery
            
            for entry in history_entries:
                row = {
                    'id': str(uuid.uuid4()),  # Generate unique UUID for each record
                    'name': entry.name,
                    'coin_id': entry.id,  # The coin identifier from CSV is stored in coin_id field
                    'date': entry.date.isoformat() + 'Z' if hasattr(entry.date, 'isoformat') else str(entry.date),
                    'created_at': current_time,
                    'created_by': 'import',
                    'is_active': True
                }
                rows_to_insert.append(row)
            
            errors = self.client.insert_rows_json(table, rows_to_insert)
            if errors:
                raise Exception(f"Error inserting history batch: {errors}")
            
            return len(rows_to_insert)

        loop = asyncio.get_event_loop()
        imported_count = await loop.run_in_executor(None, execute_batch_insert)
        
        # Clear cache after import
        self.clear_cache()
        
        return imported_count

    async def get_history_paginated(self, page: int = 1, limit: int = 50, filters: dict = None) -> Dict[str, Any]:
        """Get paginated history entries with optional filters."""
        offset = (page - 1) * limit
        
        # Build WHERE clauses
        where_clauses = []
        params = {}
        
        if filters:
            if filters.get('search'):
                where_clauses.append("(LOWER(h.name) LIKE @search OR LOWER(COALESCE(h.coin_id, h.id)) LIKE @search)")
                params['search'] = f"%{filters['search'].lower()}%"
            
            if filters.get('name'):
                where_clauses.append("LOWER(h.name) = LOWER(@name)")
                params['name'] = filters['name']
            
            if filters.get('date_filter'):
                # Filter by year-month (e.g., "2024-02")
                where_clauses.append("FORMAT_DATE('%Y-%m', h.date) = @date_filter")
                params['date_filter'] = filters['date_filter']

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"""
        SELECT COUNT(*) as total
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        WHERE {where_sql}
        """
        
        count_result = await self._get_cached_or_query(count_query, params)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Get paginated data
        data_query = f"""
        SELECT 
            h.name, 
            COALESCE(h.coin_id, h.id) as id,  -- Use coin_id if available, fallback to id for legacy data
            h.date
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        WHERE {where_sql}
        ORDER BY h.date DESC
        LIMIT @limit OFFSET @offset
        """
        
        params.update({
            'limit': limit,
            'offset': offset
        })
        
        data = await self._get_cached_or_query(data_query, params)
        
        total_pages = (total_count + limit - 1) // limit
        
        return {
            'data': data,
            'total_count': total_count,
            'total_pages': total_pages
        }

    async def get_history_filter_options(self) -> Dict[str, Any]:
        """Get filter options for history admin view."""
        # Get unique names
        names_query = f"""
        SELECT DISTINCT h.name
        FROM `{self.client.project}.{self.dataset_id}.{settings.bq_history_table}` h
        WHERE h.name IS NOT NULL AND h.name != ''
        ORDER BY h.name ASC
        """
        
        names_result = await self._get_cached_or_query(names_query, {})
        names = [row['name'] for row in names_result]
        
        return {
            "names": names
        }
