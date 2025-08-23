from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.services.bigquery_service import BigQueryService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
bigquery_service = BigQueryService()

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with statistics."""
    try:
        stats = await bigquery_service.get_stats()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats
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
