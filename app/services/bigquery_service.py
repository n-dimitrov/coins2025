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
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(k, "STRING", str(v)) 
                    for k, v in params.items()
                ]

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
            
            if filters.get('country'):
                where_clauses.append("country = @country")
                params['country'] = filters['country']
            
            if filters.get('year'):
                where_clauses.append("year = @year")
                params['year'] = str(filters['year'])

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
        query = f"""
        SELECT 
            ARRAY_AGG(DISTINCT country ORDER BY country) as countries,
            ARRAY_AGG(DISTINCT year ORDER BY year DESC) as years,
            ARRAY_AGG(DISTINCT value ORDER BY value) as denominations
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        """
        
        results = await self._get_cached_or_query(query)
        return dict(results[0]) if results else {}

    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()
        logger.info("Cache cleared")
