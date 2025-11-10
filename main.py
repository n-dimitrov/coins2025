from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import configuration and security
from app.config import settings
from app.security import SecurityMiddleware

logger.info("Starting My EuroCoins application...")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Environment: {settings.app_env}")
logger.info(f"Port: {settings.port}")
logger.info(f"Production mode: {settings.is_production}")

# Validate security configuration
security_warnings = settings.validate_security_config()
for warning in security_warnings:
    if "CRITICAL" in warning:
        logger.error(warning)
    else:
        logger.warning(warning)

# Initialize BigQueryService before importing routers so modules that lazily
# request the service (via get_bigquery_service) will find it initialized.
from app.services.bigquery_service import BigQueryService, init_bigquery_service

# Create and initialize the service instance for the process
_bq_instance = BigQueryService()
init_bigquery_service(_bq_instance)

# Import routers
from app.routers import coins, health, pages, ownership, groups, admin

# Create FastAPI instance with environment-based configuration
docs_url = "/api/docs" if settings.enable_docs else None
redoc_url = "/api/redoc" if settings.enable_docs else None

app = FastAPI(
    title="My EuroCoins",
    description="Interactive Euro coins catalog application",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url
)

# Security and endpoint control middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Combined security and endpoint access control middleware."""

    # Check if endpoint should be accessible
    try:
        SecurityMiddleware.check_endpoint_access(request)
    except HTTPException as e:
        # If endpoint is disabled, return proper 404 response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

    # Continue with request
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Add HTTPS enforcement for production
    if settings.is_production or "myeurocoins.org" in str(request.url):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"

    return response

# Configure CORS based on environment
if settings.strict_cors:
    # Production CORS - only allow specific origins
    allowed_origins = [
        "https://myeurocoins.org",
        "https://www.myeurocoins.org"
    ]
    allowed_methods = ["GET", "OPTIONS"]  # Only safe methods in production
else:
    # Development CORS - more permissive
    allowed_origins = [
        "https://myeurocoins.org",
        "https://www.myeurocoins.org",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # Common dev ports
        "http://localhost:3001"
    ]
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers based on configuration
logger.info("Configuring application routes...")

# Always include safe, read-only endpoints
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(coins.router, prefix="/api", tags=["coins"])
app.include_router(pages.router, tags=["pages"])

# Groups router for basic group information (read operations are safe)
app.include_router(groups.router, tags=["groups"])

# Conditionally include admin endpoints
if settings.enable_admin_endpoints:
    logger.info("Including admin endpoints (authentication required)")
    app.include_router(admin.router, prefix="/api", tags=["admin"])
else:
    logger.info("Admin endpoints disabled")

# Conditionally include ownership endpoints
if settings.enable_ownership_endpoints:
    logger.info("Including ownership endpoints (authentication required)")
    app.include_router(ownership.router, tags=["ownership"])
else:
    logger.info("Ownership endpoints disabled")

# Log final configuration
logger.info(f"API Documentation: {'Enabled' if settings.enable_docs else 'Disabled'}")
logger.info(f"Admin endpoints: {'Enabled' if settings.enable_admin_endpoints else 'Disabled'}")
logger.info(f"Ownership endpoints: {'Enabled' if settings.enable_ownership_endpoints else 'Disabled'}")
logger.info(f"Admin authentication: {'Required' if settings.require_admin_auth else 'Optional'}")
logger.info(f"Allowed admin IPs: {settings.admin_allowed_ips}")

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(app, host=settings.host, port=settings.port)
