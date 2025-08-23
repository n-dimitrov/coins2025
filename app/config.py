import os
from typing import Optional

class Settings:
    # Google Cloud
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "coins2025")
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # BigQuery
    bq_dataset: str = os.getenv("BQ_DATASET", "db")
    bq_table: str = os.getenv("BQ_TABLE", "catalog")
    
    # App Settings
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cache_duration_minutes: int = int(os.getenv("CACHE_DURATION_MINUTES", "5"))
    
    # Server
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

settings = Settings()
