# JWT Authentication with Multi-Tenant Support - Quick Start

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install PyJWT>=2.0.0 requests>=2.25.0
```

### 2. Create Configuration File

Create `superset_config.py` in your `PYTHONPATH`:

```python
from superset.security.jwt_manager import JWTSecurityManager

# Custom Security Manager
CUSTOM_SECURITY_MANAGER = JWTSecurityManager

# JWT Service Configuration
JWT_LOGIN_SERVICE_URL = "http://localhost:3000/api/auth/login"
JWT_SECRET_KEY = "your-secret-key-here"  # MUST match your Node.js service
JWT_ALGORITHM = "HS256"
JWT_VERIFY = True
JWT_SYNC_ROLES = False

# Basic Superset Config
SECRET_KEY = "CHANGE_ME_TO_A_COMPLEX_RANDOM_SECRET"
SQLALCHEMY_DATABASE_URI = "sqlite:////path/to/superset.db"
```

### 3. Start Superset

```bash
superset db upgrade
superset init
superset run -p 8088
```

### 4. Access Login

Navigate to: `http://localhost:8088/login`

Login form fields:
- **Tenant**: Your organization identifier
- **Email**: User email
- **Password**: User password

## 📋 Node.js Service Requirements

Your Node.js authentication service must:

### Endpoint: `POST /api/auth/login`

**Request:**
```json
{
  "tenant": "company1",
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "tenant": "company1"
  }
}
```

### JWT Token Structure

```json
{
  "email": "user@example.com",
  "tenant": "company1",
  "firstName": "John",
  "lastName": "Doe",
  "roles": ["Admin", "Analyst"],
  "exp": 1234567890,
  "iat": 1234567800
}
```

## 📁 Files Created

- `superset/security/jwt_manager.py` - Custom Security Manager
- `superset/views/jwt_auth.py` - Custom Auth View
- `superset/templates/superset/login_jwt.html` - Login Template
- `superset_config_jwt_example.py` - Configuration Example
- `JWT_AUTH_DOCUMENTATION.md` - Full Documentation

## 🔒 Security Checklist for Production

- [ ] Use HTTPS everywhere
- [ ] Set `JWT_VERIFY = True`
- [ ] Use strong random `JWT_SECRET_KEY` (32+ characters)
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Configure token expiration (1-2 hours)
- [ ] Enable rate limiting
- [ ] Use environment variables for secrets
- [ ] Monitor failed login attempts
- [ ] Restrict JWT service access with firewall

## 🧪 Testing

### Test JWT Token Manually

```python
import jwt

token = "your-token-here"
secret = "your-secret-key"

decoded = jwt.decode(token, secret, algorithms=["HS256"])
print(decoded)
```

### Debug Logs

Enable debug logging in `superset_config.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ❓ Common Issues

### "Invalid credentials"
- Check JWT service is running
- Verify `JWT_LOGIN_SERVICE_URL` is correct
- Check Node.js service logs

### "Invalid JWT token"
- Verify `JWT_SECRET_KEY` matches between Superset and Node.js
- Check `JWT_ALGORITHM` is the same
- Ensure token hasn't expired

### CORS Errors
```python
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["http://localhost:3000"],
}
```

## 📖 Full Documentation

See [JWT_AUTH_DOCUMENTATION.md](JWT_AUTH_DOCUMENTATION.md) for complete documentation including:
- Detailed architecture
- Node.js implementation examples
- Advanced configuration
- Troubleshooting guide
- Migration instructions

## 🎯 How It Works

1. User fills login form (tenant, email, password)
2. Superset calls your Node.js JWT service
3. Service validates credentials and returns JWT token
4. Superset validates JWT and extracts user info
5. User is created/updated locally with `{tenant}_{email}` username
6. JWT token stored in session
7. User authenticated and redirected to dashboard

## 🛠️ Environment Variables

```bash
export JWT_LOGIN_SERVICE_URL="https://api.yourapp.com/auth/login"
export JWT_SECRET_KEY="your-very-secure-secret-key"
export JWT_ALGORITHM="HS256"
export JWT_VERIFY="True"
export JWT_SYNC_ROLES="False"
```

## 📞 Support

For issues or questions, check:
1. Superset logs: `logs/superset.log`
2. Node.js service logs
3. Configuration in `superset_config.py`
4. Full documentation in `JWT_AUTH_DOCUMENTATION.md`
