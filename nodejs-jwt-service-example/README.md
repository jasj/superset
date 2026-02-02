# JWT Authentication Service for Superset

Example Node.js authentication service with Express and Serverless Framework 4 for Apache Superset multi-tenant JWT authentication.

## Features

- ✅ Express.js REST API
- ✅ JWT token generation and validation
- ✅ Multi-tenant support
- ✅ Password hashing with bcrypt
- ✅ Serverless Framework 4 ready
- ✅ AWS Lambda compatible
- ✅ Local development with serverless-offline
- ✅ CORS configured
- ✅ Health check endpoint

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.dev
   # Edit .env.dev with your values
   ```

3. **Start server:**
   ```bash
   npm start
   # or for auto-reload:
   npm run dev
   ```

4. **Test the service:**
   ```bash
   curl -X POST http://localhost:3000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"tenant":"company1","email":"user1@example.com","password":"demo123"}'
   ```

### Deploy to AWS

1. **Install Serverless Framework:**
   ```bash
   npm install -g serverless
   ```

2. **Configure AWS credentials:**
   ```bash
   serverless config credentials --provider aws --key YOUR_KEY --secret YOUR_SECRET
   ```

3. **Deploy:**
   ```bash
   # Development
   npm run deploy:dev
   
   # Production
   npm run deploy:prod
   ```

## API Endpoints

### POST /api/auth/login

Authenticate user and return JWT token.

**Request:**
```json
{
  "tenant": "company1",
  "email": "user1@example.com",
  "password": "demo123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "user1@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "tenant": "company1",
    "roles": ["Admin", "Analyst"]
  }
}
```

### GET /api/auth/verify

Verify JWT token validity.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "valid": true,
  "decoded": {
    "email": "user1@example.com",
    "tenant": "company1",
    "firstName": "John",
    "lastName": "Doe",
    "roles": ["Admin"],
    "exp": 1234567890,
    "iat": 1234567800
  }
}
```

### POST /api/auth/register

Register new user (optional).

**Request:**
```json
{
  "tenant": "company1",
  "email": "newuser@example.com",
  "password": "securepass123",
  "firstName": "New",
  "lastName": "User"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-30T12:00:00.000Z",
  "service": "jwt-auth-service"
}
```

## Test Credentials

The service comes with pre-configured test users:

| Tenant | Email | Password | Roles |
|--------|-------|----------|-------|
| company1 | user1@example.com | demo123 | Admin, Analyst |
| company1 | user2@example.com | demo123 | Analyst |
| company2 | admin@example.com | demo123 | Admin |

## Configuration

### Environment Variables

- `JWT_SECRET`: Secret key for signing JWT tokens (required)
- `JWT_EXPIRATION`: Token expiration time (default: 1h)
- `CORS_ORIGIN`: Allowed CORS origin (default: http://localhost:8088)
- `PORT`: Server port for local development (default: 3000)
- `NODE_ENV`: Environment (development/production)

### Database Integration

Replace the mock user database in `server.js` with your actual database:

```javascript
async function getUserFromDatabase(tenant, email) {
  // Example with PostgreSQL
  const result = await db.query(
    'SELECT * FROM users WHERE tenant = $1 AND email = $2',
    [tenant, email]
  );
  return result.rows[0];
}
```

## Utilities

### Generate Password Hash

To create password hashes for your users:

```bash
npm run hash-password your-password-here
# or
node server.js hash-password your-password-here
```

## Security Notes

- **Change JWT_SECRET**: Use a strong random secret in production
- **Use HTTPS**: Always use HTTPS in production
- **Rate Limiting**: Add rate limiting to prevent brute force attacks
- **Input Validation**: Validate and sanitize all inputs
- **Password Policy**: Enforce strong password requirements
- **Token Expiration**: Set appropriate token expiration times
- **Secure Storage**: Store passwords using bcrypt (already implemented)

## Testing with Superset

1. **Start this service:**
   ```bash
   npm start
   ```

2. **Configure Superset** (`superset_config.py`):
   ```python
   from superset.security.jwt_manager import JWTSecurityManager
   
   CUSTOM_SECURITY_MANAGER = JWTSecurityManager
   JWT_LOGIN_SERVICE_URL = "http://localhost:3000/api/auth/login"
   JWT_SECRET_KEY = "your-very-secure-secret-key-change-me"
   ```

3. **Access Superset login:** http://localhost:8088/login

## Serverless Offline

Test the Lambda function locally:

```bash
npm run offline
```

This starts the service at `http://localhost:3000` with hot reload.

## Project Structure

```
nodejs-jwt-service-example/
├── server.js           # Express application
├── handler.js          # Serverless handler
├── serverless.yml      # Serverless configuration
├── package.json        # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Troubleshooting

### CORS Errors

Make sure `CORS_ORIGIN` matches your Superset URL:
```bash
export CORS_ORIGIN=http://localhost:8088
```

### JWT Secret Mismatch

Ensure `JWT_SECRET` is identical in both services:
- Node.js service: `.env` file or environment variable
- Superset: `JWT_SECRET_KEY` in `superset_config.py`

### Password Doesn't Work

Test users use password `demo123`. For custom users:
```bash
npm run hash-password your-password
# Copy the hash to mockUsers in server.js
```

## Production Checklist

- [ ] Change `JWT_SECRET` to a secure random value
- [ ] Set `NODE_ENV=production`
- [ ] Use a real database instead of mock data
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Add request validation
- [ ] Set up monitoring and logging
- [ ] Configure proper CORS origins
- [ ] Add error tracking (e.g., Sentry)
- [ ] Set appropriate token expiration
- [ ] Use AWS Secrets Manager for secrets

## License

Apache License 2.0
