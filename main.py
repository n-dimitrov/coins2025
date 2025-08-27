from fastapi import FastAPI
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

logger.info("Starting My EuroCoins application...")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
logger.info(f"Port: {os.getenv('PORT', '8000')}")

# Import routers
from app.routers import coins, health, pages, ownership, groups, admin

# Create FastAPI instance
app = FastAPI(
    title="My EuroCoins",
    description="Interactive Euro coins catalog application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Add HTTPS enforcement for production
    if "myeurocoins.org" in str(request.url):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myeurocoins.org",
        "https://www.myeurocoins.org", 
        "http://localhost:8000",  # For local development
        "http://127.0.0.1:8000"   # For local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(coins.router, prefix="/api", tags=["coins"])
app.include_router(ownership.router, tags=["ownership"])
app.include_router(groups.router, tags=["groups"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(pages.router, tags=["pages"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
