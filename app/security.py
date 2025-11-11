"""
Security middleware and authentication dependencies for My EuroCoins application.
"""
import logging
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)

def get_client_ip(request: Request) -> str:
    """Extract the real client IP address from request, considering proxies."""
    # Check common proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, the first is the original client
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    if hasattr(request, "client") and request.client:
        return request.client.host

    return "unknown"

def verify_admin_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """
    Verify admin authentication and IP restrictions.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (optional)

    Returns:
        bool: True if authenticated and authorized

    Raises:
        HTTPException: If authentication fails
    """
    # Skip authentication in development if not required
    if settings.is_development and not settings.require_admin_auth:
        logger.info("Admin auth skipped (development mode)")
        return True

    # Check IP restrictions
    client_ip = get_client_ip(request)
    logger.info(f"Admin access attempt from IP: {client_ip}")

    if client_ip not in settings.admin_allowed_ips and "0.0.0.0" not in settings.admin_allowed_ips:
        logger.warning(f"Admin access denied for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: IP not authorized for admin access"
        )

    # Check API key authentication
    if not settings.admin_api_key:
        if settings.is_production:
            logger.error("Admin API key not configured in production")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin authentication not properly configured"
            )
        else:
            logger.warning("Admin API key not configured (development)")
            return True

    if not credentials:
        logger.warning(f"Admin access attempt without credentials from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.admin_api_key:
        logger.warning(f"Invalid admin API key from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Admin authentication successful for {client_ip}")
    return True

def verify_ownership_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """
    Verify authentication for ownership modification endpoints.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (optional)

    Returns:
        bool: True if authenticated and authorized

    Raises:
        HTTPException: If authentication fails
    """
    # If admin auth is not required (public mode), allow access
    if not settings.require_admin_auth:
        logger.info(f"Public ownership access allowed from {get_client_ip(request)}")
        return True

    # Otherwise, require admin authentication
    return verify_admin_auth(request, credentials)

class SecurityMiddleware:
    """Security middleware for IP and endpoint restrictions."""

    @staticmethod
    def check_endpoint_access(request: Request):
        """
        Check if the requested endpoint should be accessible based on configuration.

        Args:
            request: FastAPI request object

        Raises:
            HTTPException: If endpoint is disabled
        """
        path = request.url.path

        # Check admin endpoints
        if path.startswith("/api/admin"):
            if not settings.enable_admin_endpoints:
                logger.warning(f"Admin endpoints disabled, blocking: {path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endpoint not available"
                )

        # Check ownership endpoints
        elif path.startswith("/api/ownership"):
            if not settings.enable_ownership_endpoints:
                logger.warning(f"Ownership endpoints disabled, blocking: {path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endpoint not available"
                )

        # Check docs endpoints
        elif path in ["/api/docs", "/api/redoc", "/docs", "/redoc"]:
            if not settings.enable_docs:
                logger.warning(f"API docs disabled, blocking: {path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Documentation not available"
                )

def get_admin_dependency():
    """Get the admin authentication dependency."""
    return Depends(verify_admin_auth)

def get_ownership_dependency():
    """Get the ownership authentication dependency."""
    return Depends(verify_ownership_auth)