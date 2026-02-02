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
"""
Example Superset Configuration for JWT Authentication with Multi-Tenant Support

Copy this file to your PYTHONPATH as superset_config.py and customize as needed.
"""

import os

# ==============================================================================
# JWT AUTHENTICATION CONFIGURATION
# ==============================================================================

# Import the custom JWT Security Manager
from superset.security.jwt_manager import JWTSecurityManager

# Set the custom security manager
CUSTOM_SECURITY_MANAGER = JWTSecurityManager

# JWT Service Configuration
# URL of your Node.js serverless authentication service
JWT_LOGIN_SERVICE_URL = os.environ.get(
    "JWT_LOGIN_SERVICE_URL",
    "http://localhost:3000/api/auth/login"
)

# JWT Secret Key - MUST match the secret used by your Node.js service
# For production, use environment variable or secure secret management
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY",
    "your-secret-key-here"  # CHANGE THIS!
)

# JWT Algorithm (common: HS256, RS256)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# JWT Verification
# Set to False for development if you want to skip signature verification
# For production, ALWAYS set to True
JWT_VERIFY = os.environ.get("JWT_VERIFY", "True").lower() == "true"

# Sync user roles from JWT claims
# If True, user roles will be updated based on 'roles' claim in JWT
JWT_SYNC_ROLES = os.environ.get("JWT_SYNC_ROLES", "False").lower() == "true"

# ==============================================================================
# BASIC SUPERSET CONFIGURATION
# ==============================================================================

# Flask App Secret Key
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY") or "CHANGE_ME_TO_A_COMPLEX_RANDOM_SECRET"

# Database URI
# For production, use PostgreSQL or MySQL
SQLALCHEMY_DATABASE_URI = os.environ.get("SUPERSET_DATABASE_URI") or \
    "sqlite:////path/to/superset.db"

# ==============================================================================
# AUTHENTICATION TYPE
# ==============================================================================

# Use database authentication (our custom manager will handle JWT)
AUTH_TYPE = 1  # AUTH_DB

# Default role for new users
AUTH_USER_REGISTRATION_ROLE = "Public"

# Allow user self-registration
AUTH_USER_REGISTRATION = False

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================

FEATURE_FLAGS = {
    # Enable any features you need
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# ==============================================================================
# CORS CONFIGURATION (if your Node.js service is on different domain)
# ==============================================================================

ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["http://localhost:3000"],  # Add your Node.js service URL
}

# ==============================================================================
# LOGGING
# ==============================================================================

# Logging configuration
import logging

LOGGING_CONFIGURATOR = None  # Use default

# Enable debug mode for development
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

# ==============================================================================
# CACHE CONFIGURATION
# ==============================================================================

# For production, configure Redis or Memcached
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# ==============================================================================
# SESSION CONFIGURATION
# ==============================================================================

# Session configuration for storing JWT tokens
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = "Lax"

# Session lifetime
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds

# ==============================================================================
# ADDITIONAL CONFIGURATION
# ==============================================================================

# Superset webserver timeout
SUPERSET_WEBSERVER_TIMEOUT = 300

# SQL Lab configuration
SQLLAB_TIMEOUT = 300
SQLLAB_ASYNC_TIME_LIMIT_SEC = 3600

# CSV export encoding
CSV_EXPORT = {"encoding": "utf-8"}

# Row limit for queries
ROW_LIMIT = 50000

# ==============================================================================
# CUSTOM MIDDLEWARE (Optional)
# ==============================================================================

# You can add custom middleware to validate JWT on every request
# Example:
# ADDITIONAL_MIDDLEWARE = [YourJWTMiddleware]

# ==============================================================================
# NOTES FOR PRODUCTION
# ==============================================================================
"""
Production Checklist:

1. Change SECRET_KEY to a strong random value
2. Set JWT_SECRET_KEY to match your Node.js service
3. Use PostgreSQL or MySQL instead of SQLite
4. Enable HTTPS and set SESSION_COOKIE_SECURE = True
5. Configure Redis for caching and session storage
6. Set up proper logging
7. Enable rate limiting
8. Configure firewall to restrict access to JWT service
9. Use environment variables for all secrets
10. Test JWT token expiration and refresh logic
"""
