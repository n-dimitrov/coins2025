from typing import Optional, Dict, Any, List
import logging
from app.services.bigquery_service import BigQueryService

logger = logging.getLogger(__name__)

class GroupService:
    def __init__(self):
        self.bigquery_service = BigQueryService()
    
    async def validate_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Validate if group exists and return group data."""
        try:
            group = await self.bigquery_service.get_group_by_name(group_name)
            return group
        except Exception as e:
            logger.error(f"Error validating group {group_name}: {str(e)}")
            return None
    
    async def get_group_context(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get complete group context including members and stats."""
        try:
            group = await self.validate_group(group_name)
            if not group:
                return None
            
            # Get group members
            members = await self.bigquery_service.get_group_users(group['id'])
            
            # Get group stats
            stats = await self.bigquery_service.get_group_stats(group['id'])
            
            return {
                'id': group['id'],
                'name': group['name'],
                'group': group['group'],
                'members': members,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Error getting group context for {group_name}: {str(e)}")
            return None
    
    async def enrich_coins_with_ownership(self, coins: List[Dict], group_id: int) -> List[Dict]:
        """Enrich coin data with ownership information for the group."""
        try:
            enriched_coins = []
            
            for coin in coins:
                # Get ownership info for this coin
                ownership = await self.bigquery_service.get_coin_ownership_by_group(
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
    
    async def get_group_coins(self, group_id: int, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get coins with ownership information for a group."""
        try:
            return await self.bigquery_service.get_coins_with_ownership(
                group_id, filters, limit, offset
            )
        except Exception as e:
            logger.error(f"Error getting group coins: {str(e)}")
            return []
