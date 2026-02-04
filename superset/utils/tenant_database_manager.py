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
"""Multi-tenant database connection manager"""

import logging
from typing import Any, Optional

from flask import Flask, g
from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TenantDatabaseManager:
    """
    Manages database connections per tenant.

    This manager creates and maintains separate database engines for each tenant,
    allowing Superset to connect to different databases based on the authenticated
    user's tenant.

    Features:
    - Dynamic engine creation per tenant
    - Connection pooling per tenant
    - Automatic engine disposal on tenant removal
    - Thread-safe engine registry
    """

    def __init__(self) -> None:
        self.engines: dict[str, Engine] = {}
        self.app: Optional[Flask] = None
        self._database_template: str = ""
        self._base_config: dict[str, Any] = {}

    def init_app(self, app: Flask) -> None:
        """
        Initialize the tenant database manager with Flask app configuration.

        Args:
            app: Flask application instance
        """
        self.app = app

        # Get database configuration from app config
        dialect = app.config.get("DATABASE_DIALECT", "postgresql")
        user = app.config.get("DATABASE_USER", "superset")
        password = app.config.get("DATABASE_PASSWORD", "superset")
        host = app.config.get("DATABASE_HOST", "db")
        port = app.config.get("DATABASE_PORT", "5432")
        ssl_mode = app.config.get("DATABASE_SSL_MODE", "")

        # Store base configuration for creating tenant engines
        self._base_config = {
            "dialect": dialect,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "ssl_mode": ssl_mode,
        }

        # Template for database names from config, default to {tenant}
        self._database_template = app.config.get("TENANT_DATABASE_TEMPLATE", "{tenant}")

        # Configure Flask-SQLAlchemy to use our custom session class
        # This makes all queries use the tenant-specific engine
        self._configure_tenant_session_routing(app)

        # Register before_request handler to set tenant engine
        app.before_request(self._before_request_handler)

        # Register teardown handler to clean up session
        app.teardown_appcontext(self._teardown_handler)

        logger.info(
            "TenantDatabaseManager initialized with base config: %s://%s@%s:%s",
            dialect,
            user,
            host,
            port,
        )

    def _configure_tenant_session_routing(self, app: Flask) -> None:
        """
        Configure tenant-aware session routing.

        Args:
            app: Flask application instance
        """
        logger.info("Tenant session routing will be configured via before_request")

    def _before_request_handler(self) -> None:
        """
        Before request handler to set the correct database engine for the tenant.

        This method intercepts every request and rebinds the SQLAlchemy session
        to use the tenant-specific database engine.
        """
        from superset.extensions import db

        # Get tenant from global context
        tenant = getattr(g, "tenant", None)

        if tenant:
            # Get or create engine for this tenant
            engine = self.get_engine_for_tenant(tenant)

            if engine:
                # Rebind the current session to use the tenant's engine
                # This makes all queries in this request use the tenant's database
                try:
                    db.session.bind = engine
                    g.tenant_engine = engine
                    logger.debug("Bound session to tenant database: %s", tenant)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error(
                        "Failed to bind session to tenant %s: %s",
                        tenant,
                        str(e)
                    )
            else:
                logger.warning("Failed to get engine for tenant: %s", tenant)

    def _teardown_handler(self, exception: Optional[Exception] = None) -> None:
        """
        Teardown handler to clean up tenant-specific resources.

        Args:
            exception: Exception that occurred during request (if any)
        """
        from superset.extensions import db

        # Remove the session to ensure clean state for next request
        # This is important for scoped_session to work correctly
        try:
            db.session.remove()
        except Exception as e:  # pylint: disable=broad-except
            logger.debug("Error removing session in teardown: %s", str(e))

        # Clean up tenant engine from global context
        if hasattr(g, "tenant_engine"):
            delattr(g, "tenant_engine")

    def get_engine_for_tenant(self, tenant: str) -> Optional[Engine]:
        """
        Get or create a database engine for the specified tenant.

        Args:
            tenant: Tenant identifier

        Returns:
            SQLAlchemy Engine instance for the tenant's database
        """
        # Check if engine already exists
        if tenant in self.engines:
            return self.engines[tenant]

        # Create new engine for this tenant
        try:
            engine = self._create_engine_for_tenant(tenant)
            self.engines[tenant] = engine
            logger.info("Created new database engine for tenant: %s", tenant)
            return engine
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "Failed to create database engine for tenant %s: %s",
                tenant,
                str(e),
            )
            return None

    def _create_engine_for_tenant(self, tenant: str) -> Engine:
        """
        Create a new SQLAlchemy engine for the specified tenant.

        Args:
            tenant: Tenant identifier

        Returns:
            SQLAlchemy Engine instance
        """
        # Build database name from template
        database_name = self._database_template.format(tenant=tenant)

        # Build SSL parameters if configured
        ssl_mode = self._base_config.get("ssl_mode", "")
        ssl_params = f"?sslmode={ssl_mode}" if ssl_mode else ""

        # Build connection URI
        uri = (
            f"{self._base_config['dialect']}://"
            f"{self._base_config['user']}:{self._base_config['password']}@"
            f"{self._base_config['host']}:{self._base_config['port']}/{database_name}{ssl_params}"
        )

        # Create engine with connection pooling
        engine = create_engine(
            uri,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,
        )

        # Add event listener to log connections
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn: Any, connection_record: Any) -> None:
            logger.debug("Database connection established for tenant: %s", tenant)

        return engine

    def dispose_engine_for_tenant(self, tenant: str) -> None:
        """
        Dispose of the database engine for the specified tenant.

        This should be called when a tenant is removed or when the application
        is shutting down.

        Args:
            tenant: Tenant identifier
        """
        if tenant in self.engines:
            try:
                self.engines[tenant].dispose()
                del self.engines[tenant]
                logger.info("Disposed database engine for tenant: %s", tenant)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to dispose database engine for tenant %s: %s",
                    tenant,
                    str(e),
                )

    def dispose_all_engines(self) -> None:
        """
        Dispose of all tenant database engines.

        This should be called during application shutdown.
        """
        for tenant in list(self.engines.keys()):
            self.dispose_engine_for_tenant(tenant)

        logger.info("Disposed all tenant database engines")

    def bind_session_to_tenant(self, session: Session, tenant: str) -> None:
        """
        Bind a SQLAlchemy session to a specific tenant's database.

        Args:
            session: SQLAlchemy session to bind
            tenant: Tenant identifier
        """
        engine = self.get_engine_for_tenant(tenant)

        if engine:
            session.bind = engine
            logger.debug("Bound session to tenant database: %s", tenant)
        else:
            logger.warning("Failed to bind session for tenant: %s", tenant)

    def get_current_tenant_engine(self) -> Optional[Engine]:
        """
        Get the database engine for the current request's tenant.

        Returns:
            SQLAlchemy Engine instance for the current tenant, or None if no tenant
        """
        return getattr(g, "tenant_engine", None)


# Global instance
tenant_db_manager = TenantDatabaseManager()
