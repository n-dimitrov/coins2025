from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from app.services.bigquery_service import BigQueryService
from app.services.group_service import GroupService
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
bigquery_service = BigQueryService()
group_service = GroupService()

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with statistics."""
    try:
        stats = await bigquery_service.get_stats()
        # Fetch latest coins from BigQuery (this year and last year)
        try:
            coins_batch = await bigquery_service.get_latest_coins()
            latest_coins = []
            seen_ids = set()
            for c in coins_batch:
                coin_id = c.get('coin_id') or c.get('id')
                if not coin_id or coin_id in seen_ids:
                    continue
                seen_ids.add(coin_id)
                try:
                    year_val = int(c.get('year') or 0)
                except Exception:
                    year_val = 0

                latest_coins.append({
                    'coin_id': coin_id,
                    'image': c.get('image_url') or c.get('image') or '',
                    'country': c.get('country') or '',
                    'series': c.get('series') or '',
                    'coin_type': c.get('coin_type') or '',
                    'year': year_val,
                    'value': c.get('value')
                })
            # Randomize order so the hero shows different coins on each page load.
            # Do not slice here; allow the caller or upstream logic to decide how many
            # coins should be displayed in the hero. The BigQueryService already accepts
            # a `limit` parameter and can be called with None for no limit.
            try:
                random.shuffle(latest_coins)
            except Exception:
                # If shuffle fails for any reason, fall back to original order
                pass
        except Exception:
            latest_coins = []
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "latest_coins": latest_coins
        })
    except Exception as e:
        logger.error(f"Error loading homepage: {str(e)}")
        # Return template with default stats if BigQuery fails
        default_stats = {
            "total_coins": 0,
            "total_countries": 0,
            "regular_coins": 0,
            "commemorative_coins": 0
        }
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": default_stats,
            "error": "Unable to load statistics"
        })

@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(request: Request):
    """Catalog page with coin browsing."""
    try:
        filter_options = await bigquery_service.get_filter_options()
        return templates.TemplateResponse("catalog.html", {
            "request": request,
            "filter_options": filter_options
        })
    except Exception as e:
        logger.error(f"Error loading catalog: {str(e)}")
        return templates.TemplateResponse("catalog.html", {
            "request": request,
            "filter_options": {"countries": [], "years": [], "denominations": []},
            "error": "Unable to load filter options"
        })

@router.get("/coin/{coin_id}", response_class=HTMLResponse)
async def coin_detail(request: Request, coin_id: str):
    """Individual coin detail page."""
    try:
        coin_data = await bigquery_service.get_coin_by_id(coin_id)
        if not coin_data:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Coin with ID '{coin_id}' not found"
            }, status_code=404)
        
        return templates.TemplateResponse("coin_detail.html", {
            "request": request,
            "coin": coin_data
        })
    except Exception as e:
        logger.error(f"Error loading coin detail {coin_id}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load coin details"
        }, status_code=500)


@router.get("/Admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin page for managing groups and other administrative tasks."""
    try:
        # Get all groups for admin interface
        groups_data = await bigquery_service.list_active_groups()
        
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "groups": groups_data
        })
    except Exception as e:
        logger.error(f"Error loading admin page: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load admin page"
        }, status_code=500)

@router.get("/favicon.ico")
async def favicon():
    """Serve favicon.ico for browsers that request it directly."""
    return FileResponse("static/images/favicon-32x32.png", media_type="image/png")


# Group routes - Order matters! These should come after specific routes
@router.get("/{group_name}/catalog", response_class=HTMLResponse)
async def group_catalog_page(request: Request, group_name: str):
    """Group catalog page with ownership information."""
    try:
        # Validate group
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Group '{group_name}' not found"
            }, status_code=404)
        
        # Get filter options (same as regular catalog)
        filter_options = await bigquery_service.get_filter_options()
        
        return templates.TemplateResponse("catalog.html", {
            "request": request,
            "filter_options": filter_options,
            "group_context": group_context,
            "group_mode": True
        })
    except Exception as e:
        logger.error(f"Error loading group catalog {group_name}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load group catalog"
        }, status_code=500)

@router.get("/{group_name}/coin/{coin_id}", response_class=HTMLResponse)
async def group_coin_detail(request: Request, group_name: str, coin_id: str):
    """Individual coin detail page with group ownership information."""
    try:
        # Validate group
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Group '{group_name}' not found"
            }, status_code=404)
        
        # Get coin data
        coin_data = await bigquery_service.get_coin_by_id(coin_id)
        if not coin_data:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Coin with ID '{coin_id}' not found"
            }, status_code=404)
        
        # Get ownership information for this coin in the group
        ownership = await bigquery_service.get_coin_ownership_by_group(
            coin_id, group_context['id']
        )
        coin_data['owners'] = ownership
        coin_data['is_owned'] = len(ownership) > 0
        
        return templates.TemplateResponse("coin_detail.html", {
            "request": request,
            "coin": coin_data,
            "group_context": group_context,
            "group_mode": True
        })
    except Exception as e:
        logger.error(f"Error loading group coin detail {group_name}/{coin_id}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load coin details"
        }, status_code=500)

@router.get("/{group_name}", response_class=HTMLResponse)
async def group_homepage(request: Request, group_name: str):
    """Group homepage with statistics."""
    try:
        # Validate group
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Group '{group_name}' not found"
            }, status_code=404)
        
        # Get general stats (same as regular homepage)
        stats = await bigquery_service.get_stats()
        # Fetch latest coins for this group so the hero shows coins
        try:
            coins_batch = await bigquery_service.get_coins_with_ownership(group_context['id'], limit=40)
            latest_coins = []
            seen_ids = set()
            for c in coins_batch:
                coin_id = c.get('coin_id') or c.get('id')
                if not coin_id or coin_id in seen_ids:
                    continue
                seen_ids.add(coin_id)
                try:
                    year_val = int(c.get('year') or 0)
                except Exception:
                    year_val = 0

                latest_coins.append({
                    'coin_id': coin_id,
                    'image': c.get('image_url') or c.get('image') or '',
                    'country': c.get('country') or '',
                    'series': c.get('series') or '',
                    'coin_type': c.get('coin_type') or '',
                    'year': year_val,
                    'value': c.get('value')
                })
            try:
                random.shuffle(latest_coins)
            except Exception:
                pass
        except Exception:
            latest_coins = []

        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "group_context": group_context,
            "group_mode": True,
            "latest_coins": latest_coins
        })
    except Exception as e:
        logger.error(f"Error loading group homepage {group_name}: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": {"total_coins": 0, "total_countries": 0, "regular_coins": 0, "commemorative_coins": 0},
            "error": "Unable to load group statistics"
        })
