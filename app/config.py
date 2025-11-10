import os
from typing import Optional, List

class Settings:
    # Google Cloud
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "coins2025")
    # Only set credentials path if explicitly provided (not needed in Cloud Run)
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") else None

    # BigQuery
    bq_dataset: str = os.getenv("BQ_DATASET", "db")
    bq_table: str = os.getenv("BQ_TABLE", "catalog")
    bq_history_table: str = os.getenv("BQ_HISTORY_TABLE", "history")
    bq_groups_table: str = os.getenv("BQ_GROUPS_TABLE", "groups")
    bq_group_users_table: str = os.getenv("BQ_GROUP_USERS_TABLE", "group_users")

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

        if self.enable_admin_endpoints and not self.admin_api_key:
            warnings.append("WARNING: Admin endpoints enabled without API key")

        return warnings

settings = Settings()
