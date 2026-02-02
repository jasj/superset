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
"""Custom authentication views with JWT and multi-tenant support"""

import logging
from typing import Optional

from flask import flash, g, redirect, request
from flask_appbuilder import expose
from flask_appbuilder.security.decorators import no_cache
from flask_appbuilder.security.views import AuthView
from flask_babel import lazy_gettext
from flask_login import login_user
from werkzeug.wrappers import Response as WerkzeugResponse

from superset.views.base import BaseSupersetView

logger = logging.getLogger(__name__)


class JWTAuthView(BaseSupersetView, AuthView):
    """
    Custom authentication view that handles JWT-based login with tenant support.
    """

    route_base = "/login"
    login_template = "superset/login_jwt.html"

    @expose("/", methods=["GET", "POST"])
    @no_cache
    def login(self, provider: Optional[str] = None) -> WerkzeugResponse:
        """
        Handle login with tenant, email, and password.
        """
        # Check if user is already authenticated
        if g.user is not None and g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_index)

        # Handle POST request (form submission)
        if request.method == "POST":
            tenant = request.form.get("tenant", "").strip()
            email = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            # Validate required fields
            if not tenant:
                flash(lazy_gettext("Please enter your tenant"), "warning")
                return self.render_template(
                    self.login_template,
                    title=self.title,
                    appbuilder=self.appbuilder,
                )

            if not email:
                flash(lazy_gettext("Please enter your email"), "warning")
                return self.render_template(
                    self.login_template,
                    title=self.title,
                    appbuilder=self.appbuilder,
                )

            if not password:
                flash(lazy_gettext("Please enter your password"), "warning")
                return self.render_template(
                    self.login_template,
                    title=self.title,
                    appbuilder=self.appbuilder,
                )

            # Authenticate user via JWT service
            user = self.appbuilder.sm.auth_user_jwt(tenant, email, password)

            if user:
                login_user(user, remember=False)
                logger.info("User %s logged in successfully", user.username)
                
                # Redirect to the original requested page or index
                next_url = request.args.get("next", "")
                if next_url and self._is_safe_url(next_url):
                    return redirect(next_url)
                return redirect(self.appbuilder.get_url_for_index)
            else:
                flash(
                    lazy_gettext("Invalid tenant, email, or password"), 
                    "danger"
                )
                logger.warning(
                    "Failed login attempt for tenant=%s, email=%s", 
                    tenant, 
                    email
                )

        # Render login form for GET request or failed POST
        return self.render_template(
            self.login_template,
            title=self.title,
            appbuilder=self.appbuilder,
        )

    def _is_safe_url(self, target: str) -> bool:
        """
        Check if the redirect URL is safe.
        
        Args:
            target: Target URL to check
            
        Returns:
            True if URL is safe, False otherwise
        """
        from urllib.parse import urlparse, urljoin

        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
