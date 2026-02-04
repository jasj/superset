#
# Production Superset configuration for AWS ECS Fargate
#
import logging
import os
from datetime import timedelta
from typing import Optional
from superset.superset_typing import CacheConfig

logger = logging.getLogger()

# =============================================================================
# General Configuration
# =============================================================================
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "CHANGE_ME_TO_A_COMPLEX_RANDOM_SECRET")
SUPERSET_WEBSERVER_PORT = int(os.environ.get("SUPERSET_PORT", 8088))

# Application root for proxied deployments
APPLICATION_ROOT = os.environ.get("SUPERSET_APP_ROOT", "/")

# =============================================================================
# Database Configuration (RDS Aurora PostgreSQL)
# =============================================================================
DATABASE_DIALECT = os.environ.get("DATABASE_DIALECT", "postgresql")
DATABASE_USER = os.environ.get("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
DATABASE_HOST = os.environ.get("DATABASE_HOST", "localhost")
DATABASE_PORT = os.environ.get("DATABASE_PORT", "5432")
DATABASE_DB = os.environ.get("DATABASE_DB", "superset")

SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

# SQLAlchemy pool configuration for production
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_POOL_TIMEOUT = 300
SQLALCHEMY_MAX_OVERFLOW = 20

# =============================================================================
# Redis/Valkey Configuration (ElastiCache)
# =============================================================================
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_CELERY_DB = os.environ.get("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = os.environ.get("REDIS_RESULTS_DB", "1")
REDIS_SSL = os.environ.get("REDIS_SSL", "true").lower() == "true"

# Build Redis URL
REDIS_PROTOCOL = "rediss" if REDIS_SSL else "redis"
REDIS_URL = f"{REDIS_PROTOCOL}://{REDIS_HOST}:{REDIS_PORT}"

# Cache configuration using Valkey/Redis
CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": f"{REDIS_URL}/{REDIS_RESULTS_DB}",
}

DATA_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_data_",
    "CACHE_REDIS_URL": f"{REDIS_URL}/{REDIS_RESULTS_DB}",
}

FILTER_STATE_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_filter_",
    "CACHE_REDIS_URL": f"{REDIS_URL}/{REDIS_RESULTS_DB}",
}

EXPLORE_FORM_DATA_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_explore_",
    "CACHE_REDIS_URL": f"{REDIS_URL}/{REDIS_RESULTS_DB}",
}

# =============================================================================
# Celery Configuration
# =============================================================================
class CeleryConfig:
    broker_url = f"{REDIS_URL}/{REDIS_CELERY_DB}"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    result_backend = f"{REDIS_URL}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": timedelta(minutes=1),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": timedelta(hours=24),
        },
    }

CELERY_CONFIG = CeleryConfig

# =============================================================================
# JWT Authentication Configuration (Lambda integration)
# =============================================================================
# Import the custom JWT Security Manager
from superset.security.jwt_manager import JWTSecurityManager

# Set the custom security manager
CUSTOM_SECURITY_MANAGER = JWTSecurityManager

# JWT Service Configuration
JWT_LOGIN_SERVICE_URL = os.environ.get(
    "JWT_LOGIN_SERVICE_URL",
    "https://z7jtx5k2g7.execute-api.us-east-1.amazonaws.com/dev/login"
)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_VERIFY = os.environ.get("JWT_VERIFY", "true").lower() == "true"
JWT_SYNC_ROLES = os.environ.get("JWT_SYNC_ROLES", "false").lower() == "true"

# Auth configuration
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = os.environ.get("AUTH_USER_REGISTRATION_ROLE", "Alpha")

# =============================================================================
# Guest Token Configuration (for embedded dashboards)
# =============================================================================
GUEST_TOKEN_JWT_SECRET = os.environ.get("GUEST_TOKEN_JWT_SECRET", "test-guest-secret-change-me")
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_ROLE_NAME = "Public"
GUEST_TOKEN_ALLOW_MODIFIED_PAYLOAD = os.environ.get(
    "GUEST_TOKEN_ALLOW_MODIFIED_PAYLOAD", "True"
).lower() == "true"

# =============================================================================
# Multi-Tenant Configuration
# =============================================================================
MULTI_TENANT_ENABLED = os.environ.get("MULTI_TENANT_ENABLED", "true").lower() == "true"
TENANT_DATABASE_TEMPLATE = os.environ.get("TENANT_DATABASE_TEMPLATE", "{tenant}")

# =============================================================================
# Feature Flags
# =============================================================================
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_TEMPLATE_REMOVE_FILTERS": True,
    "EMBEDDED_SUPERSET": True,
    "ALERT_REPORTS": True,
    "DYNAMIC_PLUGINS": True,
}

# =============================================================================
# Security Configuration
# =============================================================================
# CORS configuration for production
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["*"],
}

# CSRF configuration
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = ["superset.views.core.log", "superset.views.core.explore_json"]
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL = os.environ.get("SUPERSET_LOG_LEVEL", "INFO")
ENABLE_CHUNK_ENCODING = False

# =============================================================================
# Alert/Report Configuration
# =============================================================================
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False

# SMTP configuration (set via environment variables)
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 25))
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "true").lower() == "true"
SMTP_SSL = os.environ.get("SMTP_SSL", "false").lower() == "true"
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "superset@example.com")

# =============================================================================
# Webserver Configuration
# =============================================================================
WEBSERVER_THREADS = 8
SUPERSET_WEBSERVER_TIMEOUT = 300

# Enable async queries
GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {
    "port": int(REDIS_PORT),
    "host": REDIS_HOST,
    "password": "",
    "db": 0,
    "ssl": REDIS_SSL,
}

# =============================================================================
# Language/Locale Configuration
# =============================================================================
BABEL_DEFAULT_LOCALE = "es"

LANGUAGES = {
    "en": {"flag": "us", "name": "English"},
    "es": {"flag": "es", "name": "Spanish"},
    "it": {"flag": "it", "name": "Italian"},
    "fr": {"flag": "fr", "name": "French"},
    "zh": {"flag": "cn", "name": "Chinese"},
    "ja": {"flag": "jp", "name": "Japanese"},
    "de": {"flag": "de", "name": "German"},
    "pt": {"flag": "pt", "name": "Portuguese"},
    "pt_BR": {"flag": "br", "name": "Brazilian Portuguese"},
    "ru": {"flag": "ru", "name": "Russian"},
    "ko": {"flag": "kr", "name": "Korean"},
}
