from typing import Optional, Dict, Any, List
import logging
from uuid import UUID
from datetime import datetime
from app.services.neon_service import get_neon_service

logger = logging.getLogger(__name__)

def _serialize_for_json(obj: Any) -> Any:
    """Convert non-JSON-serializable objects to JSON-compatible types."""
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    return obj

class GroupService:
    def __init__(self):
        # Use cached provider to avoid repeated client initializations
        # Don't obtain the service at import time. Resolve it lazily
        # on first use so the service can be initialized at FastAPI startup.
        self.database_service = None

    @property
    def bq(self):
        """Lazily return the initialized Neon database service instance."""
        if self.database_service is None:
            self.database_service = get_neon_service()
        return self.database_service
    
    async def validate_group(self, group_key: str) -> Optional[Dict[str, Any]]:
        """Validate if group exists by group_key and return raw group data.

        Note: this delegates to BigQueryService which historically accepted
        both 'name' and 'group_key' terms; here we normalize the parameter
        name to 'group_key' to be explicit.
        """
        try:
            group = await self.bq.get_group_by_key(group_key)
            return group
        except Exception as e:
            logger.error(f"Error validating group {group_key}: {str(e)}")
            return None
    
    async def get_group_context(self, group_key: str) -> Optional[Dict[str, Any]]:
        """Get complete group context including members and stats.

        Input is a canonical group_key. Returned context always includes a
        canonical 'group_key' field regardless of legacy column names.
        """
        try:
            group = await self.validate_group(group_key)
            if not group:
                logger.error(f"Group '{group_key}' not found in validate_group")
                return None

            logger.debug(f"Group found: {group}")

            # Get group members
            members = await self.bq.get_group_users(group['id'])

            # Get group stats
            stats = await self.bq.get_group_stats(group['id'])

            # Normalize to canonical keys
            canonical_group_key = group.get('group_key') or group.get('group') or group_key

            context = {
                'id': str(group['id']),  # Convert UUID to string for JSON serialization
                'name': group.get('name'),
                'group_key': canonical_group_key,
                'members': _serialize_for_json(members),
                'stats': _serialize_for_json(stats)
            }

            logger.debug(f"Group context created: {context}")
            return context
        except Exception as e:
            logger.error(f"Error getting group context for {group_key}: {str(e)}")
            return None
    
    async def enrich_coins_with_ownership(self, coins: List[Dict], group_id: str) -> List[Dict]:
        """Enrich coin data with ownership information for the group."""
        try:
            enriched_coins = []
            
            for coin in coins:
                # Get ownership info for this coin
                ownership = await self.bq.get_coin_ownership_by_group(
                    coin['coin_id'], group_id
                )
                
                # Add ownership info to coin
                coin_copy = coin.copy()
                coin_copy['owners'] = ownership
                coin_copy['is_owned'] = len(ownership) > 0
                coin_copy['owner_count'] = len(ownership)
                
                enriched_coins.append(coin_copy)
            
            return enriched_coins
        except Exception as e:
            logger.error(f"Error enriching coins with ownership: {str(e)}")
            return coins
    
    async def get_group_coins(self, group_id: str, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get coins with ownership information for a group."""
        try:
            return await self.bq.get_coins_with_ownership(
                group_id, filters, limit, offset
            )
        except Exception as e:
            logger.error(f"Error getting group coins: {str(e)}")
            return []
