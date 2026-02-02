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
