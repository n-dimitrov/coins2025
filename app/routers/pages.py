from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from app.services.bigquery_service import BigQueryService, get_bigquery_service as get_bq_provider
from app.services.group_service import GroupService
from app.config import settings
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
bigquery_service = get_bq_provider()
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
        except Exception:
            latest_coins = []
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "latest_coins": latest_coins,
            "canonical_path": "/"
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
            "filter_options": filter_options,
            "canonical_path": "/catalog"
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
            "coin": coin_data,
            "canonical_path": f"/coin/{coin_id}"
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
    # Check if admin endpoints are enabled
    if not settings.enable_admin_endpoints:
        logger.warning(f"Admin page access blocked - admin endpoints disabled")
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        # Get all groups for admin interface
        groups_data = await bigquery_service.list_active_groups()

        return templates.TemplateResponse("admin.html", {
            "request": request,
            "groups": groups_data,
            "canonical_path": "/Admin"
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
            "group_mode": True,
            # No specific selected member for this route
            "selected_member": None,
            "canonical_path": f"/{group_context.get('group_key')}/catalog"
        })
    except Exception as e:
        logger.error(f"Error loading group catalog {group_name}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load group catalog"
        }, status_code=500)


@router.get("/{group_name}/{member_name}/catalog", response_class=HTMLResponse)
async def group_member_catalog_page(request: Request, group_name: str, member_name: str):
    """Group catalog page scoped to a specific member (extender mode).

    This route validates both the group and the member, then passes
    `selected_member` into the template so the frontend can pre-filter the
    catalog (and update links) for the member.
    """
    try:
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Group '{group_name}' not found"
            }, status_code=404)

        # Validate member exists in group (case-insensitive match)
        members = [m for m in group_context.get('members', [])]
        matched = None
        for m in members:
            # member record may have 'user' or 'name' fields depending on source
            candidate = m.get('user') if isinstance(m, dict) and 'user' in m else (m.get('name') if isinstance(m, dict) else None)
            if candidate and candidate.lower() == member_name.lower():
                matched = candidate
                break

        if not matched:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Member '{member_name}' not found in group '{group_name}'"
            }, status_code=404)

        filter_options = await bigquery_service.get_filter_options()
        return templates.TemplateResponse("catalog.html", {
            "request": request,
            "filter_options": filter_options,
            "group_context": group_context,
            "group_mode": True,
            "selected_member": matched,
            "canonical_path": f"/{group_context.get('group_key')}/{matched}/catalog"
        })
    except Exception as e:
        logger.error(f"Error loading group member catalog {group_name}/{member_name}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Unable to load group member catalog"
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
            "group_mode": True,
            "canonical_path": f"/{group_context.get('group_key')}/coin/{coin_id}"
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
        
        # Get member statistics for the group
        member_stats = await bigquery_service.get_group_member_stats(group_context['id'])
        
        # Fetch latest coins for this group so the hero shows coins
        try:
            # Use the same latest-coins query as the public homepage so the hero
            # shows recent coins (this year and last year) regardless of group
            # context. Ownership info is not required for the hero.
            coins_batch = await bigquery_service.get_latest_coins(limit=40)
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
        except Exception:
            latest_coins = []

        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "group_context": group_context,
            "group_mode": True,
            "latest_coins": latest_coins,
            "member_stats": member_stats,
            "selected_member": None,
            "canonical_path": f"/{group_context.get('group_key')}"
        })
    except Exception as e:
        logger.error(f"Error loading group homepage {group_name}: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": {"total_coins": 0, "total_countries": 0, "regular_coins": 0, "commemorative_coins": 0},
            "error": "Unable to load group statistics",
            "selected_member": None
        })


@router.get("/{group_name}/{member_name}", response_class=HTMLResponse)
async def group_member_homepage(request: Request, group_name: str, member_name: str):
    """Group homepage scoped to a member (extender mode). Shows group homepage but
    with `selected_member` prefilled so templates/scripts can act accordingly.
    """
    try:
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Group '{group_name}' not found"
            }, status_code=404)

        # Validate member exists
        members = [m for m in group_context.get('members', [])]
        matched = None
        for m in members:
            candidate = m.get('user') if isinstance(m, dict) and 'user' in m else (m.get('name') if isinstance(m, dict) else None)
            if candidate and candidate.lower() == member_name.lower():
                matched = candidate
                break

        if not matched:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": f"Member '{member_name}' not found in group '{group_name}'"
            }, status_code=404)

        stats = await bigquery_service.get_stats()
        
        # Get member statistics for the group
        member_stats = await bigquery_service.get_group_member_stats(group_context['id'])
        
        try:
            # Same behavior as the public homepage: show recent coins only.
            coins_batch = await bigquery_service.get_latest_coins(limit=40)
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
        except Exception:
            latest_coins = []

        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "group_context": group_context,
            "group_mode": True,
            "latest_coins": latest_coins,
            "member_stats": member_stats,
            "selected_member": matched,
            "canonical_path": f"/{group_context.get('group_key')}/{matched}"
        })
    except Exception as e:
        logger.error(f"Error loading group member homepage {group_name}/{member_name}: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": {"total_coins": 0, "total_countries": 0, "regular_coins": 0, "commemorative_coins": 0},
            "error": "Unable to load group member statistics",
            "selected_member": None
        })
