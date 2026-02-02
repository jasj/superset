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
"""Custom Security Manager with JWT authentication and multi-tenant support"""

import logging
from typing import Any, Optional

import jwt
import requests
from flask import g, request, session
from flask_appbuilder.security.sqla.models import User
from flask_login import login_user

from superset.security.manager import SupersetSecurityManager

logger = logging.getLogger(__name__)


class JWTSecurityManager(SupersetSecurityManager):
    """
    Custom Security Manager that authenticates users via an external JWT service.
    
    Features:
    - Consumes external Node.js login service
    - Supports multi-tenant architecture
    - JWT token validation
    - Automatic user creation/update from JWT claims
    """

    def __init__(self, appbuilder: Any) -> None:
        super().__init__(appbuilder)
        # These should be configured in superset_config.py
        self.jwt_login_url = appbuilder.app.config.get(
            "JWT_LOGIN_SERVICE_URL", "http://localhost:3000/api/auth/login"
        )
        self.jwt_secret = appbuilder.app.config.get("JWT_SECRET_KEY")
        self.jwt_algorithm = appbuilder.app.config.get("JWT_ALGORITHM", "HS256")
        self.jwt_verify = appbuilder.app.config.get("JWT_VERIFY", True)

    def authenticate_with_jwt_service(
        self, tenant: str, email: str, password: str
    ) -> Optional[dict[str, Any]]:
        """
        Authenticate user against external JWT service.
        
        Args:
            tenant: Tenant identifier
            email: User email
            password: User password
            
        Returns:
            JWT token data if authentication successful, None otherwise
        """
        try:
            response = requests.post(
                self.jwt_login_url,
                json={"tenant": tenant, "email": email, "password": password},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                
                if token:
                    # Decode and validate JWT token
                    decoded_token = self.decode_jwt(token)
                    if decoded_token:
                        return {
                            "token": token,
                            "decoded": decoded_token,
                        }
            else:
                logger.warning(
                    "JWT authentication failed with status %s: %s",
                    response.status_code,
                    response.text,
                )
        except requests.RequestException as e:
            logger.error("Error connecting to JWT service: %s", str(e))
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Unexpected error during JWT authentication: %s", str(e))

        return None

    def decode_jwt(self, token: str) -> Optional[dict[str, Any]]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            if self.jwt_verify and self.jwt_secret:
                decoded = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=[self.jwt_algorithm],
                )
            else:
                # For development: decode without verification
                decoded = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token: %s", str(e))
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error decoding JWT token: %s", str(e))

        return None

    def auth_user_jwt(
        self, tenant: str, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user via JWT service and create/update local user.
        
        Args:
            tenant: Tenant identifier
            email: User email
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Authenticate with external JWT service
        jwt_data = self.authenticate_with_jwt_service(tenant, email, password)
        
        if not jwt_data:
            return None

        decoded_token = jwt_data["decoded"]
        token = jwt_data["token"]

        # Extract user information from JWT claims
        username = decoded_token.get("email") or decoded_token.get("username")
        user_tenant = decoded_token.get("tenant")
        first_name = decoded_token.get("firstName", "")
        last_name = decoded_token.get("lastName", "")
        roles = decoded_token.get("roles", [])

        if not username or not user_tenant:
            logger.error("JWT token missing required claims (email/username or tenant)")
            return None

        # Verify tenant matches
        if user_tenant != tenant:
            logger.warning(
                "Tenant mismatch: requested=%s, token=%s", tenant, user_tenant
            )
            return None

        # Create username with tenant prefix for isolation
        full_username = f"{tenant}_{username}"

        # Find or create user
        user = self.find_user(username=full_username)

        if not user:
            # Determine default role for new users
            default_role_name = self.auth_user_registration_role or "Alpha"
            default_role = self.find_role(default_role_name)

            if not default_role:
                logger.warning(
                    "Default role '%s' not found, falling back to Public",
                    default_role_name
                )
                default_role = self.find_role("Public")

            # Create new user
            user = self.add_user(
                username=full_username,
                first_name=first_name,
                last_name=last_name,
                email=username,
                role=default_role,
            )
            logger.info("Created new user: %s with role: %s", full_username, default_role.name if default_role else "None")
        else:
            # Update existing user info
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.email = username
            self.update_user(user)

        # Assign roles from JWT if configured
        if roles and self.appbuilder.app.config.get("JWT_SYNC_ROLES", False):
            self.sync_user_roles(user, roles)
            logger.info("Synced roles for user %s: %s", user.username, roles)
        elif not user.roles:
            # If user has no roles and sync is disabled, log a warning
            logger.warning(
                "User %s has no roles. Consider enabling JWT_SYNC_ROLES or setting AUTH_USER_REGISTRATION_ROLE",
                user.username
            )

        # Store JWT token and tenant in session
        if user:
            session["jwt_token"] = token
            session["tenant"] = tenant
            g.jwt_token = token
            g.tenant = tenant

        return user

    def sync_user_roles(self, user: User, role_names: list[str]) -> None:
        """
        Synchronize user roles from JWT claims.
        
        Args:
            user: User object
            role_names: List of role names from JWT
        """
        roles = []
        for role_name in role_names:
            role = self.find_role(role_name)
            if role:
                roles.append(role)
            else:
                logger.warning("Role not found: %s", role_name)

        if roles:
            user.roles = roles
            self.update_user(user)
            logger.info("Updated roles for user %s: %s", user.username, role_names)

    def load_user_from_jwt(self) -> Optional[User]:
        """
        Load user from JWT token in session.
        
        Returns:
            User object if valid JWT in session, None otherwise
        """
        token = session.get("jwt_token")
        
        if not token:
            return None

        decoded = self.decode_jwt(token)
        
        if not decoded:
            # Invalid or expired token, clear session
            session.pop("jwt_token", None)
            session.pop("tenant", None)
            return None

        username = decoded.get("email") or decoded.get("username")
        tenant = decoded.get("tenant")
        
        if not username or not tenant:
            return None

        full_username = f"{tenant}_{username}"
        user = self.find_user(username=full_username)

        if user:
            g.jwt_token = token
            g.tenant = tenant

        return user

    def oauth_user_info(  # pylint: disable=unused-argument
        self, provider: str, response: Any = None
    ) -> dict[str, Any]:
        """
        Override to prevent OAuth usage since we're using JWT.
        """
        return {}

    def register_views(self) -> None:
        """
        Register custom JWT authentication views.
        """
        # Import here to avoid circular imports
        from superset.views.jwt_auth import JWTAuthView

        # Register the custom JWT auth view
        self.auth_view = self.appbuilder.add_view_no_menu(JWTAuthView)

        # Apply rate limiting to auth view if enabled
        if (
            self.is_auth_limited
            and getattr(self.auth_view, "blueprint", None) is not None
        ):
            self.limiter.limit(self.auth_rate_limit, methods=["POST"])(
                self.auth_view.blueprint
            )

        # Continue with parent's view registration (excluding default auth view)
        from flask_appbuilder.security.views import AuthView as FABAuthView

        # Temporarily remove the parent's auth view registration
        original_auth_view = None
        for view in list(self.appbuilder.baseviews):
            if isinstance(view, FABAuthView) and view != self.auth_view:
                original_auth_view = view
                self.appbuilder.baseviews.remove(view)

        # Call parent's register_views to set up other views
        # but with AUTH_RATE_LIMITED disabled to avoid duplicate rate limiting
        original_auth_rate_limited = self.appbuilder.app.config["AUTH_RATE_LIMITED"]
        self.appbuilder.app.config["AUTH_RATE_LIMITED"] = False

        try:
            super().register_views()
        finally:
            self.appbuilder.app.config["AUTH_RATE_LIMITED"] = original_auth_rate_limited
