import os
from typing import Optional, List

class Settings:
    # Neon PostgreSQL
    database_url: Optional[str] = os.getenv("DATABASE_URL")  # postgresql://user:password@host/dbname
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    database_timeout: int = int(os.getenv("DATABASE_TIMEOUT", "30"))

    # App Settings
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cache_duration_minutes: int = int(os.getenv("CACHE_DURATION_MINUTES", "5"))

    # Server
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # Security Settings
    admin_api_key: Optional[str] = os.getenv("ADMIN_API_KEY")
    admin_allowed_ips: List[str] = os.getenv("ADMIN_ALLOWED_IPS", "127.0.0.1,::1").split(",")
    enable_admin_endpoints: bool = os.getenv("ENABLE_ADMIN_ENDPOINTS", "true" if os.getenv("APP_ENV", "development") == "development" else "false").lower() == "true"
    enable_ownership_endpoints: bool = os.getenv("ENABLE_OWNERSHIP_ENDPOINTS", "true" if os.getenv("APP_ENV", "development") == "development" else "false").lower() == "true"
    enable_docs: bool = os.getenv("ENABLE_DOCS", "true" if os.getenv("APP_ENV", "development") == "development" else "false").lower() == "true"

    # Production security flags
    require_admin_auth: bool = os.getenv("REQUIRE_ADMIN_AUTH", "true" if os.getenv("APP_ENV", "production") == "production" else "false").lower() == "true"
    strict_cors: bool = os.getenv("STRICT_CORS", "true" if os.getenv("APP_ENV", "production") == "production" else "false").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    def validate_security_config(self) -> List[str]:
        """Validate security configuration and return list of warnings/errors."""
        warnings = []

        if self.is_production:
            if not self.admin_api_key:
                warnings.append("CRITICAL: ADMIN_API_KEY not set in production")
            if self.enable_docs:
                warnings.append("WARNING: API docs enabled in production")
            if not self.require_admin_auth:
                warnings.append("CRITICAL: Admin authentication disabled in production")
            if not self.database_url:
                warnings.append("CRITICAL: DATABASE_URL not set in production")

        if self.enable_admin_endpoints and not self.admin_api_key:
            warnings.append("WARNING: Admin endpoints enabled without API key")

        return warnings

settings = Settings()
