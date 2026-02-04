# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#
import logging
import os
import sys

from celery.schedules import crontab
from flask_caching.backends.filesystemcache import FileSystemCache

logger = logging.getLogger()

DATABASE_DIALECT = os.getenv("DATABASE_DIALECT")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_DB = os.getenv("DATABASE_DB")
DATABASE_SSL_MODE = os.getenv("DATABASE_SSL_MODE", "")

EXAMPLES_USER = os.getenv("EXAMPLES_USER")
EXAMPLES_PASSWORD = os.getenv("EXAMPLES_PASSWORD")
EXAMPLES_HOST = os.getenv("EXAMPLES_HOST")
EXAMPLES_PORT = os.getenv("EXAMPLES_PORT")
EXAMPLES_DB = os.getenv("EXAMPLES_DB")

# The SQLAlchemy connection string.
_ssl_params = f"?sslmode={DATABASE_SSL_MODE}" if DATABASE_SSL_MODE else ""
SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}{_ssl_params}"
)

# Use environment variable if set, otherwise construct from components
# This MUST take precedence over any other configuration
SQLALCHEMY_EXAMPLES_URI = os.getenv(
    "SUPERSET__SQLALCHEMY_EXAMPLES_URI",
    (
        f"{DATABASE_DIALECT}://"
        f"{EXAMPLES_USER}:{EXAMPLES_PASSWORD}@"
        f"{EXAMPLES_HOST}:{EXAMPLES_PORT}/{EXAMPLES_DB}"
    ),
)


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_CELERY_DB = os.getenv("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = os.getenv("REDIS_RESULTS_DB", "1")

RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG


class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
    }


CELERY_CONFIG = CeleryConfig

FEATURE_FLAGS = {"ALERT_REPORTS": True}
ALERT_REPORTS_NOTIFICATION_DRY_RUN = True
WEBDRIVER_BASEURL = f"http://superset_app{os.environ.get('SUPERSET_APP_ROOT', '/')}/"  # When using docker compose baseurl should be http://superset_nginx{ENV{BASEPATH}}/  # noqa: E501
# The base URL for the email report hyperlinks.
WEBDRIVER_BASEURL_USER_FRIENDLY = (
    f"http://localhost:8888/{os.environ.get('SUPERSET_APP_ROOT', '/')}/"
)
SQLLAB_CTAS_NO_LIMIT = True

log_level_text = os.getenv("SUPERSET_LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, log_level_text.upper(), logging.INFO)

if os.getenv("CYPRESS_CONFIG") == "true":
    # When running the service as a cypress backend, we need to import the config
    # located @ tests/integration_tests/superset_test_config.py
    base_dir = os.path.dirname(__file__)
    module_folder = os.path.abspath(
        os.path.join(base_dir, "../../tests/integration_tests/")
    )
    sys.path.insert(0, module_folder)
    from superset_test_config import *  # noqa

    sys.path.pop(0)

# ==============================================================================
# LANGUAGE/LOCALE CONFIGURATION
# ==============================================================================
# Set the default language to Spanish
BABEL_DEFAULT_LOCALE = "es"

# Available languages - make sure Spanish is included
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

# ==============================================================================
# JWT AUTHENTICATION CONFIGURATION
# ==============================================================================
# Import the custom JWT Security Manager
from superset.security.jwt_manager import JWTSecurityManager

# Set the custom security manager
CUSTOM_SECURITY_MANAGER = JWTSecurityManager

# JWT Service Configuration
# URL of your Node.js serverless authentication service
JWT_LOGIN_SERVICE_URL = os.getenv(
    "JWT_LOGIN_SERVICE_URL",
   # "http://host.docker.internal:3000/api/auth/login"
    "https://z7jtx5k2g7.execute-api.us-east-1.amazonaws.com/dev/login"
)

# JWT Secret Key - MUST match the secret used by your Node.js service
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "your-secret-key-here"  # CHANGE THIS!
)

# JWT Algorithm (common: HS256, RS256)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# JWT Verification
JWT_VERIFY = os.getenv("JWT_VERIFY", "True").lower() == "true"

# Sync user roles from JWT claims
JWT_SYNC_ROLES = os.getenv("JWT_SYNC_ROLES", "False").lower() == "true"

# Default role for new users when JWT_SYNC_ROLES is False
# Options: Admin, Alpha, Gamma, sql_lab, Public
# Alpha: Can create and edit dashboards/charts (recommended default)
# Gamma: Can only view assigned dashboards
# Public: Very limited access
AUTH_USER_REGISTRATION_ROLE = os.getenv("AUTH_USER_REGISTRATION_ROLE", "Alpha")

# ==============================================================================
# EMBEDDED DASHBOARD / GUEST TOKEN CONFIGURATION
# ==============================================================================
# Guest token settings for embedded dashboards
GUEST_TOKEN_JWT_SECRET = os.getenv("GUEST_TOKEN_JWT_SECRET", "test-guest-secret-change-me")
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutes
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"

# Allow guest users to apply filters (workaround for "cannot modify chart payload" error)
# This overrides the strict payload validation for guest users
# WARNING: Only enable this in development or if you understand the security implications
GUEST_ROLE_NAME = "Public"

# DEVELOPMENT ONLY: Allow guest tokens to modify chart payloads
# This bypasses the security check that prevents guest users from modifying chart queries
# Set to True to fix "Guest user cannot modify chart payload" errors in embedded dashboards
GUEST_TOKEN_ALLOW_MODIFIED_PAYLOAD = os.getenv(
    "GUEST_TOKEN_ALLOW_MODIFIED_PAYLOAD", "True"
).lower() == "true"

# Enable embedded superset feature flag
FEATURE_FLAGS = {
    **FEATURE_FLAGS,
    "EMBEDDED_SUPERSET": True,
}

# ==============================================================================
# MULTI-TENANT DATABASE CONFIGURATION
# ==============================================================================
# Enable multi-tenant database routing
# Each tenant will connect to a database named after the tenant identifier
# Example: tenant "acme" connects to database "acme"

MULTI_TENANT_ENABLED = os.getenv("MULTI_TENANT_ENABLED", "True").lower() == "true"

# Database name template for tenants
# Available placeholders: {tenant}
# Example: "{tenant}_db" would create databases like "acme_db", "demo_db"
TENANT_DATABASE_TEMPLATE = os.getenv("TENANT_DATABASE_TEMPLATE", "{tenant}")

# ==============================================================================

#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    import superset_config_docker
    from superset_config_docker import *  # noqa: F403

    logger.info(
        "Loaded your Docker configuration at [%s]", superset_config_docker.__file__
    )
except ImportError:
    logger.info("Using default Docker config...")
