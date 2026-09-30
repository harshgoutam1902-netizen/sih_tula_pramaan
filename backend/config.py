"""
Application configuration loaded from environment variables.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # ========== Application ==========
    app_name: str = "TulaPramaan"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ========== Database (DEMO: SQLite) ==========
    database_url: str = "sqlite:///./tulapramaan_demo.db"
    db_echo: bool = False
    # Pool settings ignored for SQLite but kept for config compatibility
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # ========== Security ==========
    secret_key: str = "change-this-secret-key-in-production"
    jwt_secret_key: str = "change-this-jwt-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    
    # ========== CORS ==========
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    
    # ========== Rulepack ==========
    rulepack_dir: str = "./rulepacks"
    default_rulepack_version: str = "R76-1:2006"
    rulepack_cache_enabled: bool = True
    rulepack_auto_reload: bool = False
    
    # ========== AI/LLM Services ==========
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.1
    vision_service_enabled: bool = True
    vision_model: str = "gpt-4-vision-preview"
    vision_max_image_size: int = 4  # MB
    
    # ========== File Storage ==========
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760  # 10MB
    allowed_image_types: str = "image/jpeg,image/png,image/webp"
    allowed_document_types: str = "application/pdf"
    
    # ========== Logging ==========
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "./logs/app.log"
    log_rotation: str = "daily"
    log_retention_days: int = 30
    
    # ========== Audit Trail ==========
    audit_log_enabled: bool = True
    audit_log_hash_chain: bool = True
    audit_log_table: str = "audit_trail"
    
    # ========== Redis (Optional) ==========
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_cache_ttl: int = 3600
    
    # ========== Email (Optional) ==========
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@tulapramaan.com"
    smtp_tls: bool = True
    
    # ========== Report Generation ==========
    report_output_dir: str = "./reports"
    report_template_dir: str = "./templates/reports"
    report_logo_path: str = "./assets/logo.png"
    report_formats: str = "pdf,docx"
    wkhtmltopdf_path: str = "/usr/local/bin/wkhtmltopdf"
    
    # ========== Performance ==========
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    request_timeout_seconds: int = 30
    
    # ========== Monitoring ==========
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    metrics_enabled: bool = False
    metrics_port: int = 9090
    
    # ========== Feature Flags ==========
    feature_ocr_enabled: bool = True
    feature_live_mpe_feedback: bool = True
    feature_multi_range_support: bool = True
    feature_batch_repetitive_tests: bool = True
    feature_environment_auto_propagation: bool = True
    
    # ========== Frontend ==========
    frontend_url: str = "http://localhost:3000"
    
    # ========== Decimal Precision ==========
    decimal_precision: int = 6
    mpe_rounding_mode: str = "ROUND_HALF_UP"
    
    # ========== Session ==========
    session_timeout_minutes: int = 120
    session_storage: str = "database"
    
    # ========== Development ==========
    reload: bool = True
    docs_enabled: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # ========== Backup ==========
    backup_enabled: bool = True
    backup_dir: str = "./backups"
    backup_schedule: str = "daily"
    backup_retention_days: int = 30
    
    # ========== i18n ==========
    default_language: str = "en"
    supported_languages: str = "en"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
