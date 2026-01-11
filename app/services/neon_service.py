import psycopg
from psycopg import sql
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import asyncio
import uuid
from app.config import settings

logger = logging.getLogger(__name__)


class NeonService:
    """PostgreSQL database service for Neon (replaces BigQueryService)."""

    # Shared cache across all service instances
    _global_cache: Dict[str, Any] = {}

    def __init__(self):
        try:
            logger.info(f"Initializing Neon service with DATABASE_URL")
            self.connection_string = settings.database_url
            # Use a shared cache so clearing in one place affects all instances
            self._cache = self.__class__._global_cache
            self._cache_duration = timedelta(minutes=settings.cache_duration_minutes)
            logger.info("Neon service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neon service: {str(e)}")
            raise

    async def _get_connection(self):
        """Get an async connection to the database."""
        return await psycopg.AsyncConnection.connect(self.connection_string)

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
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_data

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    logger.debug(f"Executing query: {query[:100]}...")
                    await cur.execute(query, params or {})

                    # Fetch all results and convert to list of dicts
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    results = []
                    async for row in cur:
                        results.append(dict(zip(columns, row)))

                    logger.debug(f"Query executed successfully, got {len(results)} results")

                    # Cache results
                    self._cache[cache_key] = (results, datetime.now())
                    return results

        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            raise

    async def get_coins(self, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get coins with optional filters."""
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = %(coin_type)s")
                params['coin_type'] = filters['coin_type']

            if filters.get('value'):
                where_clauses.append("value = %(value)s")
                params['value'] = float(filters['value'])

            if filters.get('country'):
                where_clauses.append("country = %(country)s")
                params['country'] = filters['country']

            if filters.get('series'):
                where_clauses.append("series = %(series)s")
                params['series'] = filters['series']

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM catalog
        WHERE {where_sql}
        ORDER BY year DESC, country ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """

        params['limit'] = limit
        params['offset'] = offset

        return await self._get_cached_or_query(query, params)

    async def get_latest_coins(self, limit: Optional[int] = 40) -> List[Dict[str, Any]]:
        """Get coins from this year or last year, ordered by year desc then country."""
        current_year = datetime.now().year
        last_year = current_year - 1

        limit_sql = f"LIMIT %(limit)s" if limit is not None else ""

        query = f"""
        SELECT
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM catalog
        WHERE year IN (%(y1)s, %(y2)s)
        ORDER BY year DESC, country ASC
        {limit_sql}
        """

        params = {'y1': current_year, 'y2': last_year}
        if limit is not None:
            params['limit'] = limit

        return await self._get_cached_or_query(query, params)

    async def get_coin_by_id(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific coin by ID."""
        query = """
        SELECT *
        FROM catalog
        WHERE coin_id = %(coin_id)s
        """

        results = await self._get_cached_or_query(query, {'coin_id': coin_id})
        return results[0] if results else None

    async def get_stats(self) -> Dict[str, int]:
        """Get collection statistics."""
        query = """
        SELECT
            COUNT(*) as total_coins,
            COUNT(DISTINCT country) as total_countries,
            COUNT(CASE WHEN coin_type = 'RE' THEN 1 END) as regular_coins,
            COUNT(CASE WHEN coin_type = 'CC' THEN 1 END) as commemorative_coins
        FROM catalog
        """

        results = await self._get_cached_or_query(query)
        return dict(results[0]) if results else {}

    async def get_filter_options(self) -> Dict[str, List]:
        """Get available filter options."""
        # Get countries and denominations from all coins
        general_query = """
        SELECT
            ARRAY_AGG(DISTINCT country ORDER BY country) as countries,
            ARRAY_AGG(DISTINCT value ORDER BY value DESC) as denominations
        FROM catalog
        """

        # Get commemorative series only from CC coins
        commemorative_query = """
        SELECT
            ARRAY_AGG(DISTINCT series ORDER BY series) as commemoratives
        FROM catalog
        WHERE series LIKE 'CC-%%'
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
        """Deprecated compatibility wrapper. Delegates to get_group_by_key."""
        return await self.get_group_by_key(group_name)

    async def get_group_users(self, group_id: str) -> List[Dict[str, Any]]:
        """Get active users for a specific group."""
        query = """
        SELECT gu.*, g.name as group_name
        FROM group_users gu
        JOIN groups g ON gu.group_id = g.id
        WHERE gu.group_id = %(group_id)s AND gu.is_active = true AND g.is_active = true
        ORDER BY gu.alias
        """

        return await self._get_cached_or_query(query, {'group_id': group_id})

    async def get_group_member_stats_by_user(self, group_id: str) -> List[Dict[str, Any]]:
        """Return per-user stats for a group."""
        # Get canonical list of group users
        users = await self.get_group_users(group_id)

        # Get aggregated statistics
        agg_stats = await self.get_group_member_stats(group_id)

        # Build a mapping from name -> stats for quick lookup
        stats_by_name: Dict[str, Dict[str, Any]] = {}
        for s in agg_stats:
            key = s.get('name')
            if key:
                stats_by_name[key] = s

        # Merge: ensure every user appears in output
        results: List[Dict[str, Any]] = []
        for u in users:
            uname = u.get('name')
            alias = u.get('alias') if isinstance(u, dict) else None
            base = {
                'name': uname,
                'alias': alias,
                'owned_coins_count': 0,
                'owned_countries_count': 0,
                'regular_coins_count': 0,
                'commemorative_coins_count': 0,
                'last_added_date': None,
                'last_added_date_coins': 0
            }

            if uname and uname in stats_by_name:
                st = stats_by_name[uname]
                base['owned_coins_count'] = int(st.get('owned_coins_count') or 0)
                base['owned_countries_count'] = int(st.get('owned_countries_count') or 0)
                base['regular_coins_count'] = int(st.get('regular_coins_count') or 0)
                base['commemorative_coins_count'] = int(st.get('commemorative_coins_count') or 0)
                base['last_added_date'] = st.get('last_added_date')
                base['last_added_date_coins'] = int(st.get('last_added_date_coins') or 0)

            results.append(base)

        # Helper to convert values to timestamps for sorting
        def _to_ts(v):
            if v is None:
                return float('-inf')
            if isinstance(v, datetime):
                return v.timestamp()
            try:
                return datetime.fromisoformat(str(v)).timestamp()
            except Exception:
                return float('-inf')

        # Sort by last_added_date descending (newest first), None last
        results.sort(key=lambda r: _to_ts(r.get('last_added_date')), reverse=True)

        return results

    async def get_coin_ownership_by_group(self, coin_id: str, group_id: str) -> List[Dict[str, Any]]:
        """Get ownership information for a specific coin within a group."""
        query = """
        WITH latest_ownership AS (
            SELECT
                h.name, h.coin_id, h.date, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) as rn
            FROM history h
            WHERE h.coin_id = %(coin_id)s
        )
        SELECT
            gu.name as owner,
            COALESCE(gu.alias, gu.name) as alias,
            lo.date as acquired_date
        FROM latest_ownership lo
        JOIN group_users gu ON LOWER(TRIM(lo.name)) = LOWER(TRIM(gu.name)) AND gu.group_id = %(group_id)s
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
                where_clauses.append("c.coin_type = %(coin_type)s")
                params['coin_type'] = filters['coin_type']

            if filters.get('value'):
                where_clauses.append("c.value = %(value)s")
                params['value'] = float(filters['value'])

            if filters.get('country'):
                where_clauses.append("c.country = %(country)s")
                params['country'] = filters['country']

            if filters.get('series'):
                where_clauses.append("c.series = %(series)s")
                params['series'] = filters['series']

            if filters.get('owned_by'):
                where_clauses.append("lo.name = %(owned_by)s")
                params['owned_by'] = filters['owned_by']

            if filters.get('ownership_status'):
                if filters['ownership_status'] == 'owned':
                    where_clauses.append("lo.coin_id IS NOT NULL")
                elif filters['ownership_status'] == 'missing':
                    where_clauses.append("lo.coin_id IS NULL")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        WITH latest_ownership AS (
            SELECT
                h.name, h.coin_id, h.date, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) as rn
            FROM history h
        ),
        coin_ownership AS (
            SELECT
                c.*,
                gu.name as owner,
                COALESCE(gu.alias, lo.name) as owner_alias,
                lo.date as acquired_date
            FROM catalog c
            LEFT JOIN latest_ownership lo
                ON c.coin_id = lo.coin_id AND lo.rn = 1 AND lo.is_active = true
            LEFT JOIN group_users gu
                ON LOWER(TRIM(lo.name)) = LOWER(TRIM(gu.name)) AND gu.group_id = %(group_id)s AND gu.is_active = true
            WHERE {where_sql}
        )
        SELECT
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume,
            JSON_AGG(
                JSON_BUILD_OBJECT('owner', owner, 'alias', owner_alias, 'acquired_date', acquired_date)
                ORDER BY acquired_date DESC
            ) FILTER (WHERE owner IS NOT NULL) as owners
        FROM coin_ownership
        GROUP BY coin_type, year, country, series, value, coin_id, image_url, feature, volume
        ORDER BY year DESC, country ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """

        params['limit'] = limit
        params['offset'] = offset

        return await self._get_cached_or_query(query, params)

    async def get_group_stats(self, group_id: str) -> Dict[str, int]:
        """Get statistics for a group."""
        query = """
        WITH latest_ownership AS (
            SELECT
                h.name, h.coin_id, h.is_active,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) as rn
            FROM history h
        )
        SELECT
            COUNT(DISTINCT gu.name) as total_members,
            COUNT(DISTINCT CASE WHEN lo.is_active = true THEN lo.coin_id END) as total_coins_owned,
            COUNT(CASE WHEN lo.is_active = true THEN 1 END) as total_ownership_records
        FROM group_users gu
        LEFT JOIN latest_ownership lo
            ON gu.name = lo.name AND lo.rn = 1
        WHERE gu.group_id = %(group_id)s AND gu.is_active = true
        """

        results = await self._get_cached_or_query(query, {'group_id': group_id})
        return dict(results[0]) if results else {}

    # Ownership management methods
    async def add_coin_ownership(self, name: str, coin_id: str, date: datetime, created_by: str = None) -> str:
        """Add a new coin ownership record."""
        record_id = str(uuid.uuid4())
        current_time = datetime.now()

        # Lightweight existence check
        check_query = """
        SELECT is_active
        FROM history
        WHERE coin_id = %(coin_id)s AND name = %(name)s
        ORDER BY created_at DESC, date DESC
        LIMIT 1
        """

        start_check = datetime.now()
        latest = await self._get_cached_or_query(check_query, {'coin_id': coin_id, 'name': name})
        check_duration = (datetime.now() - start_check).total_seconds()
        logger.info(f"Lightweight ownership check took {check_duration:.3f}s for {name}/{coin_id}")

        if latest:
            is_active = latest[0].get('is_active')
            is_active_flag = bool(is_active)

            if is_active_flag:
                raise ValueError(f"User {name} already owns coin {coin_id}")

        # Insert new ownership record
        record_id = str(uuid.uuid4())
        insert_query = """
        INSERT INTO history (id, name, coin_id, date, created_at, created_by, is_active)
        VALUES (%(id)s, %(name)s, %(coin_id)s, %(date)s, %(created_at)s, %(created_by)s, true)
        """

        params = {
            'id': record_id,
            'name': name,
            'coin_id': coin_id,
            'date': date,
            'created_at': current_time,
            'created_by': created_by or 'api'
        }

        start_insert = datetime.now()
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(insert_query, params)
            insert_duration = (datetime.now() - start_insert).total_seconds()
            logger.info(f"Insert succeeded in {insert_duration:.3f}s for {record_id}")
        except Exception as e:
            logger.error(f"Insert failed: {str(e)}")
            raise

        # Invalidate related cache
        start_invalidate = datetime.now()
        await self._invalidate_ownership_cache(coin_id=coin_id, user_name=name)
        invalidate_duration = (datetime.now() - start_invalidate).total_seconds()
        logger.info(f"Cache invalidation took {invalidate_duration:.3f}s for {name}/{coin_id}")

        total_duration = (datetime.now() - start_check).total_seconds()
        logger.info(f"Total add_coin_ownership duration: {total_duration:.3f}s for {name}/{coin_id}")

        return record_id

    async def remove_coin_ownership(self, name: str, coin_id: str, removal_date: datetime, created_by: str = None) -> str:
        """Permanently delete ownership record from database (hard delete)."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    # Check if any records exist for this user and coin
                    check_query = """
                    SELECT id FROM history
                    WHERE name = %(name)s AND coin_id = %(coin_id)s
                    LIMIT 1
                    """
                    await cur.execute(check_query, {'name': name, 'coin_id': coin_id})
                    result = await cur.fetchone()

                    if not result:
                        raise ValueError(f"User {name} does not own coin {coin_id}")

                    # Delete all records for this user and coin
                    delete_query = """
                    DELETE FROM history
                    WHERE name = %(name)s AND coin_id = %(coin_id)s
                    """
                    await cur.execute(delete_query, {'name': name, 'coin_id': coin_id})

            # Invalidate cache
            await self._invalidate_ownership_cache(coin_id=coin_id, user_name=name)
            logger.info(f"Permanently deleted ownership: {name} -> {coin_id}")
            return ""

        except ValueError as e:
            logger.warning(f"Remove ownership failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remove ownership error: {str(e)}")
            raise

    async def get_current_coin_ownership(self, coin_id: str, name: str = None) -> List[Dict[str, Any]]:
        """Get current owners of a coin (latest active record per user)."""
        where_clause = "WHERE h.coin_id = %(coin_id)s"
        params = {'coin_id': coin_id}

        if name:
            where_clause += " AND h.name = %(name)s"
            params['name'] = name

        query = f"""
        WITH latest_records AS (
            SELECT
                h.name, h.coin_id, h.date, h.is_active, h.created_at,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) as rn
            FROM history h
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
            group_join = "JOIN group_users gu ON lr.name = gu.name AND gu.is_active = true"
            group_where = "AND gu.group_id = %(group_id)s"
            params['group_id'] = group_id

        query = f"""
        WITH latest_records AS (
            SELECT
                h.name, h.coin_id, h.date, h.is_active, h.created_at,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) as rn
            FROM history h
            WHERE h.name = %(name)s
        )
        SELECT lr.coin_id, lr.date as acquired_date, c.coin_type, c.year, c.country, c.series, c.value
        FROM latest_records lr
        {group_join}
        JOIN catalog c ON lr.coin_id = c.coin_id
        WHERE lr.rn = 1 AND lr.is_active = true {group_where}
        ORDER BY lr.date DESC
        """

        return await self._get_cached_or_query(query, params)

    async def _invalidate_ownership_cache(self, coin_id: str = None, user_name: str = None, group_id: str = None):
        """Invalidate cache entries related to ownership changes."""
        keys_to_remove = []

        for cache_key in list(self._cache.keys()):
            if (coin_id and coin_id in cache_key) or \
               (user_name and user_name in cache_key) or \
               (group_id and str(group_id) in cache_key) or \
               'ownership' in cache_key.lower() or \
               'coins_with_ownership' in cache_key.lower() or \
               'member' in cache_key.lower() or \
               'history' in cache_key.lower() or \
               'activity' in cache_key.lower():  # Invalidate activities too
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self._cache[key]

        logger.info(f"Invalidated {len(keys_to_remove)} cache entries due to ownership change")

    # Group management methods
    async def create_group(self, group_key: str, name: str) -> str:
        """Create a new group."""
        # Check if group_key already exists
        existing = await self.get_group_by_key(group_key)
        if existing:
            raise ValueError(f"Group with key '{group_key}' already exists")

        group_id = str(uuid.uuid4())

        query = """
        INSERT INTO groups (id, group_key, name, is_active)
        VALUES (%(id)s, %(group_key)s, %(name)s, true)
        """

        params = {
            'id': group_id,
            'group_key': group_key,
            'name': name
        }

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
        except Exception as e:
            logger.error(f"Error creating group: {str(e)}")
            raise

        # Invalidate group cache
        self._invalidate_group_cache()

        return group_id

    async def update_group(self, group_id: str, name: str) -> bool:
        """Update group name."""
        # Check if group exists and is active
        existing = await self.get_group_by_id(group_id)
        if not existing or not existing.get('is_active'):
            raise ValueError(f"Group with id '{group_id}' not found or inactive")

        query = """
        UPDATE groups
        SET name = %(name)s
        WHERE id = %(group_id)s AND is_active = true
        """

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, {'name': name, 'group_id': group_id})
        except Exception as e:
            logger.error(f"Error updating group: {str(e)}")
            raise

        # Invalidate group cache
        self._invalidate_group_cache()

        return True

    async def delete_group(self, group_id: str) -> bool:
        """Soft delete a group and all its members."""
        # Check if group exists and is active
        existing = await self.get_group_by_id(group_id)
        if not existing or not existing.get('is_active'):
            raise ValueError(f"Group with id '{group_id}' not found or inactive")

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    # Soft delete group
                    group_query = "UPDATE groups SET is_active = false WHERE id = %(group_id)s"
                    await cur.execute(group_query, {'group_id': group_id})

                    # Soft delete all group members
                    users_query = "UPDATE group_users SET is_active = false WHERE group_id = %(group_id)s"
                    await cur.execute(users_query, {'group_id': group_id})
        except Exception as e:
            logger.error(f"Error deleting group: {str(e)}")
            raise

        # Invalidate cache
        self._invalidate_group_cache()

        return True

    async def get_group_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group by ID."""
        query = """
        SELECT *
        FROM groups
        WHERE id = %(group_id)s AND is_active = true
        """

        results = await self._get_cached_or_query(query, {'group_id': group_id})
        return results[0] if results else None

    async def get_group_by_key(self, group_key: str) -> Optional[Dict[str, Any]]:
        """Get active group by key."""
        query = """
        SELECT *
        FROM groups
        WHERE group_key = %(group_key)s AND is_active = true
        """

        results = await self._get_cached_or_query(query, {'group_key': group_key})
        return results[0] if results else None

    async def list_active_groups(self) -> List[Dict[str, Any]]:
        """List all active groups."""
        query = """
        SELECT *
        FROM groups
        WHERE is_active = true
        ORDER BY name
        """

        return await self._get_cached_or_query(query, {})

    # Group user management methods
    async def add_user_to_group(self, group_id: str, name: str, alias: str) -> str:
        """Add user to group."""
        # Check if group exists and is active
        group = await self.get_group_by_id(group_id)
        if not group:
            raise ValueError(f"Group with id '{group_id}' not found or inactive")

        # Check if user already exists in group
        existing_user = await self.get_group_user(group_id, name)
        if existing_user:
            raise ValueError(f"User '{name}' already exists in group")

        user_id = str(uuid.uuid4())

        query = """
        INSERT INTO group_users (id, group_id, name, alias, is_active)
        VALUES (%(id)s, %(group_id)s, %(name)s, %(alias)s, true)
        """

        params = {
            'id': user_id,
            'group_id': group_id,
            'name': name,
            'alias': alias
        }

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
        except Exception as e:
            logger.error(f"Error adding user to group: {str(e)}")
            raise

        # Invalidate cache
        self._invalidate_group_cache()

        return user_id

    async def update_group_user(self, group_id: str, name: str, alias: str) -> bool:
        """Update user alias in group."""
        # Check if user exists in group
        existing_user = await self.get_group_user(group_id, name)
        if not existing_user:
            raise ValueError(f"User '{name}' not found in group")

        query = """
        UPDATE group_users
        SET alias = %(alias)s
        WHERE group_id = %(group_id)s AND name = %(name)s AND is_active = true
        """

        params = {
            'alias': alias,
            'group_id': group_id,
            'name': name
        }

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
        except Exception as e:
            logger.error(f"Error updating group user: {str(e)}")
            raise

        # Invalidate cache
        self._invalidate_group_cache()

        return True

    async def remove_user_from_group(self, group_id: str, name: str) -> bool:
        """Remove user from group."""
        # Check if user exists in group
        existing_user = await self.get_group_user(group_id, name)
        if not existing_user:
            raise ValueError(f"User '{name}' not found in group")

        query = """
        UPDATE group_users
        SET is_active = false
        WHERE group_id = %(group_id)s AND name = %(name)s
        """

        params = {
            'group_id': group_id,
            'name': name
        }

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params)
        except Exception as e:
            logger.error(f"Error removing user from group: {str(e)}")
            raise

        # Invalidate cache
        self._invalidate_group_cache()

        return True

    async def get_group_user(self, group_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Get specific user in group."""
        query = """
        SELECT *
        FROM group_users
        WHERE group_id = %(group_id)s AND name = %(name)s AND is_active = true
        """

        results = await self._get_cached_or_query(query, {'group_id': group_id, 'name': name})
        return results[0] if results else None

    async def get_active_group_users(self, group_id: str) -> List[Dict[str, Any]]:
        """Get all active users in group."""
        query = """
        SELECT *
        FROM group_users
        WHERE group_id = %(group_id)s AND is_active = true
        ORDER BY alias
        """

        return await self._get_cached_or_query(query, {'group_id': group_id})

    def _invalidate_group_cache(self):
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
        placeholders = ', '.join([f'%s'] * len(coin_ids))
        query = f"""
        SELECT DISTINCT coin_id
        FROM catalog
        WHERE coin_id IN ({placeholders})
        """

        results = await self._get_cached_or_query(query, dict(enumerate(coin_ids)))
        return [row['coin_id'] for row in results]

    async def get_existing_coins_features(self, coin_ids: List[str]) -> Dict[str, Optional[str]]:
        """Get existing coins' features for a list of coin_ids."""
        if not coin_ids:
            return {}

        placeholders = ', '.join([f'%s'] * len(coin_ids))
        query = f"""
        SELECT DISTINCT coin_id, feature
        FROM catalog
        WHERE coin_id IN ({placeholders})
        """

        results = await self._get_cached_or_query(query, dict(enumerate(coin_ids)))
        # Build mapping
        mapping: Dict[str, Optional[str]] = {}
        for row in results:
            mapping[row['coin_id']] = row.get('feature')
        return mapping

    async def import_coins(self, coins: List[Dict[str, Any]]) -> int:
        """Import coins to PostgreSQL."""
        if not coins:
            return 0

        current_time = datetime.now()

        rows_to_insert = []
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

        logger.info(f"Preparing to insert {len(rows_to_insert)} coin rows")

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    for row in rows_to_insert:
                        query = """
                        INSERT INTO catalog (coin_type, year, country, series, value, coin_id, image_url, feature, volume, created_at, updated_at)
                        VALUES (%(coin_type)s, %(year)s, %(country)s, %(series)s, %(value)s, %(coin_id)s, %(image_url)s, %(feature)s, %(volume)s, %(created_at)s, %(updated_at)s)
                        ON CONFLICT (coin_id) DO NOTHING
                        """
                        await cur.execute(query, row)

            logger.info(f"Successfully imported {len(rows_to_insert)} coins")

            # Clear cache to force refresh
            self._cache.clear()

            return len(rows_to_insert)

        except Exception as e:
            logger.error(f"Error importing coins: {str(e)}")
            raise

    async def get_all_coins_for_export(self) -> List[Dict[str, Any]]:
        """Get all coins sorted by year, series, country for export."""
        query = """
        SELECT
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM catalog
        ORDER BY year ASC, series ASC, country ASC
        """

        return await self._get_cached_or_query(query, {})

    async def get_coins_for_admin_view(self, filters: dict = None, limit: int = 100, offset: int = 0, search: str = None) -> List[Dict[str, Any]]:
        """Get coins for admin view with filtering and pagination."""
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = %(coin_type)s")
                params['coin_type'] = filters['coin_type']

            if filters.get('country'):
                where_clauses.append("country = %(country)s")
                params['country'] = filters['country']

        if search:
            where_clauses.append("(LOWER(country) LIKE %(search)s OR LOWER(series) LIKE %(search)s OR LOWER(feature) LIKE %(search)s)")
            params['search'] = f"%{search.lower()}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM catalog
        WHERE {where_sql}
        ORDER BY year DESC, country ASC, series ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """

        params['limit'] = limit
        params['offset'] = offset

        return await self._get_cached_or_query(query, params)

    # Catalog reset utilities
    async def delete_catalog_table(self) -> dict:
        """Delete the catalog table if it exists."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DROP TABLE IF EXISTS catalog CASCADE")
            logger.info("Deleted catalog table")
            return {'success': True, 'message': 'Table deleted'}
        except Exception as e:
            logger.error(f"Error deleting table: {str(e)}")
            return {'success': False, 'message': str(e)}

    async def create_catalog_table(self) -> dict:
        """Create the catalog table with schema."""
        try:
            schema_file = '/Users/din1sf/d/develop-personal/coins2025/tools/neon_schema.sql'
            with open(schema_file, 'r') as f:
                schema_sql = f.read()

            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(schema_sql)

            logger.info("Created catalog table")
            return {'success': True, 'message': 'Table created'}
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return {'success': False, 'message': str(e)}

    async def reset_catalog_table(self) -> dict:
        """Delete and recreate the catalog table."""
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
                where_clauses.append("coin_type = %(coin_type)s")
                params['coin_type'] = filters['coin_type']

            if filters.get('country'):
                where_clauses.append("country = %(country)s")
                params['country'] = filters['country']

        if search:
            where_clauses.append("(LOWER(country) LIKE %(search)s OR LOWER(series) LIKE %(search)s OR LOWER(feature) LIKE %(search)s)")
            params['search'] = f"%{search.lower()}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT COUNT(*) as total
        FROM catalog
        WHERE {where_sql}
        """

        result = await self._get_cached_or_query(query, params)
        return result[0]['total'] if result else 0

    async def get_coins_filter_options(self) -> Dict[str, Any]:
        """Get filter options for coins admin view."""
        # Get unique countries
        countries_query = """
        SELECT DISTINCT country
        FROM catalog
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
        query = """
        SELECT
            h.name,
            COALESCE(h.coin_id, h.id::text) as id,
            h.date,
            h.created_at,
            h.is_active
        FROM history h
        ORDER BY h.created_at DESC
        """

        return await self._get_cached_or_query(query, {})

    async def import_history_batch(self, history_entries: List) -> int:
        """Import a batch of history entries."""
        current_time = datetime.now()

        rows_to_insert = []
        for entry in history_entries:
            row = {
                'id': str(uuid.uuid4()),
                'name': entry.name,
                'coin_id': entry.id,
                'date': entry.date,
                'created_at': current_time,
                'created_by': 'import',
                'is_active': True
            }
            rows_to_insert.append(row)

        logger.info(f"Inserting {len(rows_to_insert)} history entries")

        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    for row in rows_to_insert:
                        query = """
                        INSERT INTO history (id, name, coin_id, date, created_at, created_by, is_active)
                        VALUES (%(id)s, %(name)s, %(coin_id)s, %(date)s, %(created_at)s, %(created_by)s, %(is_active)s)
                        """
                        await cur.execute(query, row)

            # Clear cache after import
            self.clear_cache()

            return len(rows_to_insert)

        except Exception as e:
            logger.error(f"Error importing history batch: {str(e)}")
            raise

    async def get_history_paginated(self, page: int = 1, limit: int = 50, filters: dict = None) -> Dict[str, Any]:
        """Get paginated history entries with optional filters."""
        offset = (page - 1) * limit

        # Build WHERE clauses
        where_clauses = []
        params = {}

        if filters:
            if filters.get('search'):
                where_clauses.append("(LOWER(h.name) LIKE %(search)s OR LOWER(COALESCE(h.coin_id, h.id::text)) LIKE %(search)s)")
                params['search'] = f"%{filters['search'].lower()}%"

            if filters.get('name'):
                where_clauses.append("LOWER(h.name) = LOWER(%(name)s)")
                params['name'] = filters['name']

            if filters.get('date_filter'):
                where_clauses.append("TO_CHAR(h.date, 'YYYY-MM') = %(date_filter)s")
                params['date_filter'] = filters['date_filter']

        include_inactive = bool(filters and filters.get('include_inactive'))

        where_sql_base = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        if include_inactive:
            count_query = f"""
            SELECT COUNT(*) as total
            FROM history h
            WHERE {where_sql_base}
            """
            count_result = await self._get_cached_or_query(count_query, params)
            total_count = count_result[0]['total'] if count_result else 0
        else:
            count_query = f"""
            WITH latest_records AS (
                SELECT
                    h.name,
                    COALESCE(h.coin_id, h.id::text) as id,
                    ROW_NUMBER() OVER (PARTITION BY h.name, COALESCE(h.coin_id, h.id::text) ORDER BY h.created_at DESC, h.date DESC) as rn,
                    h.is_active
                FROM history h
                WHERE {where_sql_base}
            )
            SELECT COUNT(*) as total
            FROM latest_records
            WHERE rn = 1 AND is_active = TRUE
            """
            count_result = await self._get_cached_or_query(count_query, params)
            total_count = count_result[0]['total'] if count_result else 0

        # Get paginated data
        params.update({
            'limit': limit,
            'offset': offset
        })

        if not include_inactive:
            data_query = f"""
            WITH latest_records AS (
                SELECT
                    h.name,
                    COALESCE(h.coin_id, h.id::text) as id,
                    h.date,
                    h.created_at,
                    h.is_active,
                    ROW_NUMBER() OVER (PARTITION BY h.name, COALESCE(h.coin_id, h.id::text) ORDER BY h.created_at DESC, h.date DESC) as rn
                FROM history h
                WHERE {where_sql_base}
            )
            SELECT name, id, date, created_at
            FROM latest_records
            WHERE rn = 1 AND is_active = TRUE
            ORDER BY date DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """

            data = await self._get_cached_or_query(data_query, params)
        else:
            data_query = f"""
            SELECT
                h.name,
                COALESCE(h.coin_id, h.id::text) as id,
                h.date,
                h.created_at
            FROM history h
            WHERE {where_sql_base}
            ORDER BY h.date DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """

            data = await self._get_cached_or_query(data_query, params)

        total_pages = (total_count + limit - 1) // limit

        return {
            'data': data,
            'total_count': total_count,
            'total_pages': total_pages
        }

    async def get_history_filter_options(self) -> Dict[str, Any]:
        """Get filter options for history admin view."""
        names_query = """
        SELECT DISTINCT h.name
        FROM history h
        WHERE h.name IS NOT NULL AND h.name != ''
        ORDER BY h.name ASC
        """

        names_result = await self._get_cached_or_query(names_query, {})
        names = [row['name'] for row in names_result]

        return {
            "names": names
        }

    # History reset utilities
    async def delete_history_table(self) -> dict:
        """Delete the history table if it exists."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DROP TABLE IF EXISTS history CASCADE")
            logger.info("Deleted history table")
            return {'success': True, 'message': 'History table deleted'}
        except Exception as e:
            logger.error(f"Error deleting history table: {str(e)}")
            return {'success': False, 'message': str(e)}

    async def create_history_table(self) -> dict:
        """Create the history table with appropriate schema."""
        try:
            schema_file = '/Users/din1sf/d/develop-personal/coins2025/tools/neon_schema.sql'
            with open(schema_file, 'r') as f:
                schema_sql = f.read()

            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(schema_sql)

            logger.info("Created history table")
            return {'success': True, 'message': 'History table created'}
        except Exception as e:
            logger.error(f"Error creating history table: {str(e)}")
            return {'success': False, 'message': str(e)}

    async def reset_history_table(self) -> dict:
        """Delete and recreate the history table."""
        delete_res = await self.delete_history_table()
        if not delete_res.get('success'):
            return {'success': False, 'message': f"Delete failed: {delete_res.get('message')}"}

        create_res = await self.create_history_table()
        if not create_res.get('success'):
            return {'success': False, 'message': f"Create failed: {create_res.get('message')}"}

        # Clear caches
        self._cache.clear()
        return {'success': True, 'message': 'History table deleted and recreated'}

    async def get_group_member_stats(self, group_id: str) -> List[Dict[str, Any]]:
        """Get statistics for each member in a group."""
        query = """
        WITH latest_ownership AS (
            SELECT
                h.name,
                h.coin_id,
                h.date,
                h.is_active,
                c.country,
                c.series,
                c.coin_type,
                c.year,
                ROW_NUMBER() OVER (PARTITION BY h.name, h.coin_id ORDER BY h.created_at DESC, h.date DESC) AS rn
            FROM history h
            JOIN catalog c ON h.coin_id = c.coin_id
        ),
        member_events AS (
            SELECT
                gu.name AS name,
                gu.alias AS alias,
                lo.coin_id,
                lo.country,
                lo.coin_type,
                lo.year,
                lo.is_active,
                lo.date
            FROM group_users gu
            LEFT JOIN latest_ownership lo
              ON lo.rn = 1 AND LOWER(TRIM(lo.name)) = LOWER(TRIM(gu.name))
            WHERE gu.group_id = %(group_id)s AND gu.is_active = true
        ),
        member_agg AS (
            SELECT
                name,
                alias,
                COUNT(DISTINCT CASE WHEN is_active = true THEN coin_id END) AS owned_coins_count,
                COUNT(DISTINCT CASE WHEN is_active = true THEN country END) AS owned_countries_count,
                COUNT(DISTINCT CASE WHEN is_active = true AND coin_type = 'RE' THEN coin_id END) AS regular_coins_count,
                COUNT(DISTINCT CASE WHEN is_active = true AND coin_type = 'CC' THEN coin_id END) AS commemorative_coins_count,
                MAX(CASE WHEN is_active = true THEN date END) AS last_added_date
            FROM member_events
            GROUP BY name, alias
        ),
        last_day_counts AS (
            SELECT
                me.name,
                COUNT(DISTINCT me.coin_id) AS last_added_date_coins
            FROM member_events me
            JOIN (
                SELECT name, MAX(CASE WHEN is_active = true THEN date END) AS last_added_date
                FROM member_events
                GROUP BY name
            ) m2
              ON me.name = m2.name
            WHERE me.is_active = true AND DATE(me.date) = DATE(m2.last_added_date)
            GROUP BY me.name
        )
        SELECT
            ma.name,
            ma.alias,
            ma.owned_coins_count,
            ma.owned_countries_count,
            ma.regular_coins_count,
            ma.commemorative_coins_count,
            ma.last_added_date,
            COALESCE(ldc.last_added_date_coins, 0) AS last_added_date_coins
        FROM member_agg ma
        LEFT JOIN last_day_counts ldc ON ma.name = ldc.name
        ORDER BY ma.last_added_date DESC NULLS LAST, ma.alias
        """

        member_data = await self._get_cached_or_query(query, {'group_id': group_id})

        # Fetch recent activities for each member
        activities_query = """
        SELECT
            h.name,
            DATE(h.date) as activity_date,
            COUNT(DISTINCT h.coin_id) as coins_count
        FROM history h
        JOIN group_users gu ON LOWER(TRIM(h.name)) = LOWER(TRIM(gu.name))
        WHERE gu.group_id = %(group_id)s AND gu.is_active = true AND h.is_active = true
        GROUP BY h.name, DATE(h.date)
        ORDER BY h.name, activity_date DESC
        """

        activities_data = await self._get_cached_or_query(activities_query, {'group_id': group_id})

        # Group activities by member name
        activities_by_member = {}
        for activity in activities_data:
            name = activity['name']
            if name not in activities_by_member:
                activities_by_member[name] = []
            # Limit to recent 10 activities per member
            if len(activities_by_member[name]) < 10:
                activities_by_member[name].append({
                    'date': activity['activity_date'],
                    'coins_count': activity['coins_count']
                })

        # Add recent_activities to member data
        for member in member_data:
            member['recent_activities'] = activities_by_member.get(member['name'], [])

        return member_data


# Process-global singleton holder + initializer
_neon_singleton: Optional[NeonService] = None


def init_neon_service(instance: NeonService) -> None:
    """Initialize the module-level singleton. Call this once during app startup."""
    global _neon_singleton
    _neon_singleton = instance


def get_neon_service() -> NeonService:
    """Return the startup-initialized NeonService.

    Raises RuntimeError if `init_neon_service` was not called.
    """
    if _neon_singleton is None:
        raise RuntimeError(
            "NeonService not initialized. Ensure app startup called init_neon_service()."
        )
    return _neon_singleton
