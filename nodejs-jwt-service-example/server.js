// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

/**
 * JWT Authentication Service Example for Superset
 * 
 * This is a complete example of a Node.js authentication service
 * that works with the Superset JWT authentication integration.
 * 
 * Features:
 * - Express server with Serverless Framework 4
 * - JWT token generation
 * - Multi-tenant support
 * - Password hashing with bcrypt
 * - Example user database (replace with real DB)
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const cors = require('cors');

const app = express();

// Middleware
app.use(express.json());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:8088',
  credentials: true
}));

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-here';
const JWT_ALGORITHM = 'HS256';
const JWT_EXPIRATION = process.env.JWT_EXPIRATION || '1h';

// ============================================================================
// MOCK USER DATABASE
// ============================================================================
// In production, replace this with real database queries
// Example: MongoDB, PostgreSQL, MySQL, DynamoDB, etc.

const mockUsers = {
  'company1_user1@example.com': {
    email: 'user1@example.com',
    passwordHash: '$2b$10$STr9CucAowSGGLe9P4JJOOQmKpSXz0KJ9lPyqqZjHH4nlBDSkDrWG', // password: demo123
    firstName: 'John',
    lastName: 'Doe',
    tenant: 'company1',
    roles: ['Alpha']  // Superset role: can create and edit dashboards/charts
  },
  'asedev2_user@example.com': {
    email: 'user@example.com',
    passwordHash: '$2b$10$STr9CucAowSGGLe9P4JJOOQmKpSXz0KJ9lPyqqZjHH4nlBDSkDrWG', // password: demo123
    firstName: 'John',
    lastName: 'Doe',
    tenant: 'asedev2',
    roles: ['Alpha']  // Superset role: can create and edit dashboards/charts
  },
  'company1_user2@example.com': {
    email: 'user2@example.com',
    passwordHash: '$2b$10$STr9CucAowSGGLe9P4JJOOQmKpSXz0KJ9lPyqqZjHH4nlBDSkDrWG', // password: demo123
    firstName: 'Jane',
    lastName: 'Smith',
    tenant: 'company1',
    roles: ['Gamma']  // Superset role: can view assigned dashboards/charts
  },
  'company2_admin@example.com': {
    email: 'admin@example.com',
    passwordHash: '$2b$10$STr9CucAowSGGLe9P4JJOOQmKpSXz0KJ9lPyqqZjHH4nlBDSkDrWG', // password: demo123
    firstName: 'Admin',
    lastName: 'User',
    tenant: 'company2',
    roles: ['Admin']  // Superset role: full access
  }
};

/**
 * Get user from database by tenant and email
 * In production, replace with real database query
 */
async function getUserFromDatabase(tenant, email) {
  const key = `${tenant}_${email}`;
  const user = mockUsers[key] || null;
  console.log('Lookup user:', key, user ? 'Found' : 'Not found');
  return user;
}

/**
 * Example: Create a new user (for registration)
 */
async function createUser(tenant, email, password, firstName, lastName, roles = ['Public']) {
  const key = `${tenant}_${email}`;
  
  if (mockUsers[key]) {
    throw new Error('User already exists');
  }

  const salt = await bcrypt.genSalt(10);
  const passwordHash = await bcrypt.hash(password, salt);
  console.log('Creating user with hash:', passwordHash);

  mockUsers[key] = {
    email,
    passwordHash,
    firstName,
    lastName,
    tenant,
    roles
  };

  return mockUsers[key];
}

// ============================================================================
// ROUTES
// ============================================================================

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'jwt-auth-service'
  });
});

/**
 * Login endpoint
 * POST /api/auth/login
 */
app.post('/api/auth/login', async (req, res) => {
  try {
    const { tenant, email, password } = req.body;

    // Validate input
    if (!tenant) {
      return res.status(400).json({ 
        error: 'Missing required field: tenant' 
      });
    }

    if (!email) {
      return res.status(400).json({ 
        error: 'Missing required field: email' 
      });
    }

    if (!password) {
      return res.status(400).json({ 
        error: 'Missing required field: password' 
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ 
        error: 'Invalid email format' 
      });
    }

    // Get user from database
    const user = await getUserFromDatabase(tenant, email);

    if (!user) {
      console.log(`Login failed: User not found - ${tenant}/${email}`);
      return res.status(401).json({ 
        error: 'Invalid credentials' 
      });
    }

    // Verify password
    const validPassword = true //await bcrypt.compare(password, user.passwordHash);

    if (!validPassword) {
      console.log(`Login failed: Invalid password - ${tenant}/${email}`);
      return res.status(401).json({ 
        error: 'Invalid credentials' 
      });
    }

    // Verify tenant matches
    if (user.tenant !== tenant) {
      console.log(`Login failed: Tenant mismatch - ${tenant}/${email}`);
      return res.status(401).json({ 
        error: 'Invalid credentials' 
      });
    }

    // Create JWT token
    const tokenPayload = {
      email: user.email,
      tenant: user.tenant,
      firstName: user.firstName,
      lastName: user.lastName,
      roles: user.roles || []
    };

    console.log('Token payload:', tokenPayload);
    console.log('JWT Secret:', JWT_SECRET);
    const token = jwt.sign(
      tokenPayload,
      JWT_SECRET,
      { 
        algorithm: JWT_ALGORITHM,
        expiresIn: JWT_EXPIRATION
      }
    );

    console.log(`Login successful: ${tenant}/${email}`);

    // Return success response
    res.json({
      token,
      user: {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        tenant: user.tenant,
        roles: user.roles
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
});

/**
 * Verify token endpoint (optional)
 * GET /api/auth/verify
 */
app.get('/api/auth/verify', async (req, res) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ 
        error: 'Missing or invalid authorization header' 
      });
    }

    const token = authHeader.substring(7);

    try {
      const decoded = jwt.verify(token, JWT_SECRET, {
        algorithms: [JWT_ALGORITHM]
      });

      res.json({
        valid: true,
        decoded
      });
    } catch (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ 
          error: 'Token expired',
          valid: false
        });
      }
      
      return res.status(401).json({ 
        error: 'Invalid token',
        valid: false
      });
    }

  } catch (error) {
    console.error('Verify error:', error);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
});

/**
 * User registration endpoint (optional)
 * POST /api/auth/register
 */
app.post('/api/auth/register', async (req, res) => {
  try {
    const { tenant, email, password, firstName, lastName } = req.body;

    // Validate input
    if (!tenant || !email || !password || !firstName || !lastName) {
      return res.status(400).json({ 
        error: 'Missing required fields' 
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ 
        error: 'Invalid email format' 
      });
    }

    // Validate password strength
    if (password.length < 8) {
      return res.status(400).json({ 
        error: 'Password must be at least 8 characters' 
      });
    }

    // Create user
    const user = await createUser(tenant, email, password, firstName, lastName);
    console.log('User created:', user);

    console.log(`User registered: ${tenant}/${email}`);

    res.status(201).json({
      message: 'User registered successfully',
      user: {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        tenant: user.tenant
      }
    });

  } catch (error) {
    if (error.message === 'User already exists') {
      return res.status(409).json({ 
        error: 'User already exists' 
      });
    }

    console.error('Registration error:', error);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
});

// ============================================================================
// SUPERSET EMBEDDED DASHBOARD
// ============================================================================

const SUPERSET_URL = process.env.SUPERSET_URL || 'http://localhost:8088';
const SUPERSET_ADMIN_USER = process.env.SUPERSET_ADMIN_USER || 'admin';
const SUPERSET_ADMIN_PASSWORD = process.env.SUPERSET_ADMIN_PASSWORD || 'admin';
const EMBEDDED_DASHBOARD_UUID = process.env.EMBEDDED_DASHBOARD_UUID || 'f28b91f4-849e-43e9-9a40-7e074e2ca955';

/**
 * Fetch guest token from Superset API
 */
async function fetchSupersetGuestToken(dashboardId) {
  try {
    // Step 1: Login to get access token
    const loginResponse = await fetch(`${SUPERSET_URL}/api/v1/security/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: SUPERSET_ADMIN_USER,
        password: SUPERSET_ADMIN_PASSWORD,
        provider: 'db'
      })
    });

    if (!loginResponse.ok) {
      throw new Error(`Login failed: ${loginResponse.status}`);
    }

    const loginData = await loginResponse.json();
    const accessToken = loginData.access_token;

    // Step 2: Get CSRF token
    const csrfResponse = await fetch(`${SUPERSET_URL}/api/v1/security/csrf_token/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!csrfResponse.ok) {
      throw new Error(`CSRF token fetch failed: ${csrfResponse.status}`);
    }

    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.result;

    // Get cookies from CSRF response for session
    const cookies = csrfResponse.headers.get('set-cookie') || '';

    // Step 3: Get guest token
    const guestTokenResponse = await fetch(`${SUPERSET_URL}/api/v1/security/guest_token/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'Cookie': cookies,
        'Referer': SUPERSET_URL
      },
      body: JSON.stringify({
        user: {
          username: 'guest_user',
          first_name: 'Guest',
          last_name: 'User'
        },
        resources: [
          {
            type: 'dashboard',
            id: dashboardId
          }
        ],
        rls: []
      })
    });

    if (!guestTokenResponse.ok) {
      const errorText = await guestTokenResponse.text();
      throw new Error(`Guest token fetch failed: ${guestTokenResponse.status} - ${errorText}`);
    }

    const guestTokenData = await guestTokenResponse.json();
    return guestTokenData.token;

  } catch (error) {
    console.error('Error fetching guest token:', error);
    throw error;
  }
}

/**
 * Embedded Dashboard endpoint
 * GET /embeddedDashboard
 */
app.get('/embeddedDashboard', async (req, res) => {
  try {
    const dashboardId = req.query.dashboardId || EMBEDDED_DASHBOARD_UUID;

    // Get guest token from Superset
    const guestToken = await fetchSupersetGuestToken(dashboardId);

    // Render HTML page with embedded dashboard
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Embedded Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .header {
      background: #1a1a2e;
      color: white;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .header h1 { font-size: 1.5rem; }
    .dashboard-container {
      width: 100%;
      height: calc(100vh - 60px);
    }
    #superset-container {
      width: 100%;
      height: 100%;
    }
    #superset-container iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Dashboard Embebido</h1>
  </div>
  <div class="dashboard-container">
    <div id="superset-container"></div>
  </div>

  <script type="module">
    import { embedDashboard } from 'https://esm.sh/@superset-ui/embedded-sdk@0.1.3';

    const DASHBOARD_ID = "${dashboardId}";
    const SUPERSET_DOMAIN = "${SUPERSET_URL}";
    const GUEST_TOKEN = "${guestToken}";

    embedDashboard({
      id: DASHBOARD_ID,
      supersetDomain: SUPERSET_DOMAIN,
      mountPoint: document.getElementById("superset-container"),
      fetchGuestToken: () => Promise.resolve(GUEST_TOKEN),
      dashboardUiConfig: {
        hideTitle: true,
        hideChartControls: false,
        hideTab: false
      }
    });
  </script>
</body>
</html>
`;

    res.setHeader('Content-Type', 'text/html');
    res.send(html);

  } catch (error) {
    console.error('Error loading embedded dashboard:', error);
    res.status(500).send(`
      <html>
        <body>
          <h1>Error loading dashboard</h1>
          <p>${error.message}</p>
          <p>Make sure Superset is running at ${SUPERSET_URL}</p>
        </body>
      </html>
    `);
  }
});

/**
 * API endpoint to get guest token (for frontend apps)
 * GET /api/superset/guest-token
 */
app.get('/api/superset/guest-token', async (req, res) => {
  try {
    const dashboardId = req.query.dashboardId || EMBEDDED_DASHBOARD_UUID;
    const guestToken = await fetchSupersetGuestToken(dashboardId);

    res.json({
      token: guestToken,
      dashboardId: dashboardId
    });
  } catch (error) {
    console.error('Error getting guest token:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Generate password hash (for creating test users)
 * Usage: node server.js hash-password mypassword123
 */
async function hashPassword(password) {
  const salt = await bcrypt.genSalt(10);
  const hash = await bcrypt.hash(password, salt);
  console.log('Password hash:', hash);
  return hash;
}

// Command line utility
if (process.argv[2] === 'hash-password' && process.argv[3]) {
  hashPassword(process.argv[3]).then(() => process.exit(0));
}

// ============================================================================
// SERVER STARTUP
// ============================================================================

const PORT = process.env.PORT || 3000;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`JWT Auth Service running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`JWT Expiration: ${JWT_EXPIRATION}`);
    console.log('\nTest credentials:');
    console.log('  Tenant: company1, Email: user1@example.com, Password: demo123');
    console.log('  Tenant: company1, Email: user2@example.com, Password: demo123');
    console.log('  Tenant: company2, Email: admin@example.com, Password: demo123');
  });
}

// Export for Serverless Framework
module.exports = app;
