# Autenticación JWT Multi-Tenant para Superset

Esta documentación describe cómo configurar Superset para usar un servicio de autenticación JWT externo con soporte multi-tenant.

## Descripción General

Esta solución permite que Superset autentique usuarios contra un servicio externo Node.js que utiliza JWT (JSON Web Tokens) y soporta múltiples tenants. El formulario de login incluye tres campos:

- **Tenant**: Identificador del tenant
- **Email**: Correo electrónico del usuario
- **Password**: Contraseña del usuario

## Componentes

### 1. JWTSecurityManager (`superset/security/jwt_manager.py`)

Security Manager personalizado que extiende `SupersetSecurityManager` y proporciona:

- Autenticación contra servicio JWT externo
- Validación de tokens JWT
- Creación/actualización automática de usuarios locales
- Sincronización de roles desde JWT
- Aislamiento por tenant (usuarios con prefijo `{tenant}_{email}`)

### 2. JWTAuthView (`superset/views/jwt_auth.py`)

Vista de autenticación personalizada que:

- Renderiza formulario de login con campo tenant
- Maneja la validación de formularios
- Gestiona el proceso de autenticación
- Almacena el token JWT en la sesión

### 3. Plantilla de Login (`superset/templates/superset/login_jwt.html`)

Formulario HTML personalizado con:

- Campo para tenant
- Campo para email
- Campo para password
- Diseño responsive y accesible

## Instalación

### 1. Instalar Dependencias

```bash
pip install PyJWT>=2.0.0 requests>=2.25.0
```

### 2. Copiar Archivos

Los archivos ya están creados en:

- `superset/security/jwt_manager.py`
- `superset/views/jwt_auth.py`
- `superset/templates/superset/login_jwt.html`
- `superset_config_jwt_example.py` (archivo de ejemplo)

### 3. Configurar Superset

Copia el archivo de ejemplo a tu configuración:

```bash
cp superset_config_jwt_example.py superset_config.py
```

O crea tu propio `superset_config.py` con el siguiente contenido mínimo:

```python
from superset.security.jwt_manager import JWTSecurityManager

# Usar el Security Manager personalizado
CUSTOM_SECURITY_MANAGER = JWTSecurityManager

# URL del servicio de autenticación Node.js
JWT_LOGIN_SERVICE_URL = "http://localhost:3000/api/auth/login"

# Clave secreta JWT (debe coincidir con tu servicio Node.js)
JWT_SECRET_KEY = "tu-clave-secreta-aqui"

# Algoritmo JWT
JWT_ALGORITHM = "HS256"

# Verificar firma JWT
JWT_VERIFY = True

# Sincronizar roles desde JWT
JWT_SYNC_ROLES = False
```

## Servicio Node.js - Especificación

Tu servicio Node.js debe cumplir con las siguientes especificaciones:

### Endpoint de Login

**URL**: `POST /api/auth/login`

**Request Body**:
```json
{
  "tenant": "empresa1",
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

**Response Exitosa** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "usuario@ejemplo.com",
    "firstName": "Juan",
    "lastName": "Pérez",
    "tenant": "empresa1"
  }
}
```

**Response de Error** (401 Unauthorized):
```json
{
  "error": "Invalid credentials"
}
```

### Estructura del Token JWT

El token JWT debe contener las siguientes claims:

```json
{
  "email": "usuario@ejemplo.com",
  "tenant": "empresa1",
  "firstName": "Juan",
  "lastName": "Pérez",
  "roles": ["Admin", "Analyst"],  // Opcional
  "exp": 1234567890,  // Timestamp de expiración
  "iat": 1234567800   // Timestamp de emisión
}
```

### Ejemplo de Implementación Node.js

```javascript
// server.js - Ejemplo con Express y Serverless Framework
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

const app = express();
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || 'tu-clave-secreta-aqui';

// Endpoint de login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { tenant, email, password } = req.body;

    // Validar campos requeridos
    if (!tenant || !email || !password) {
      return res.status(400).json({ 
        error: 'Missing required fields' 
      });
    }

    // Buscar usuario en tu base de datos
    const user = await getUserFromDatabase(tenant, email);
    
    if (!user) {
      return res.status(401).json({ 
        error: 'Invalid credentials' 
      });
    }

    // Verificar password
    const validPassword = await bcrypt.compare(password, user.passwordHash);
    
    if (!validPassword) {
      return res.status(401).json({ 
        error: 'Invalid credentials' 
      });
    }

    // Crear token JWT
    const token = jwt.sign(
      {
        email: user.email,
        tenant: user.tenant,
        firstName: user.firstName,
        lastName: user.lastName,
        roles: user.roles,  // Opcional
      },
      JWT_SECRET,
      { 
        algorithm: 'HS256',
        expiresIn: '1h'
      }
    );

    // Responder con token
    res.json({
      token,
      user: {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        tenant: user.tenant,
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
});

// Función auxiliar (implementa según tu BD)
async function getUserFromDatabase(tenant, email) {
  // Implementa la lógica para buscar el usuario en tu base de datos
  // Debe retornar un objeto con: email, tenant, firstName, lastName, passwordHash, roles
  // o null si no se encuentra
}

module.exports = app;
```

### Serverless Framework Configuration

```yaml
# serverless.yml
service: auth-service

provider:
  name: aws
  runtime: nodejs18.x
  environment:
    JWT_SECRET: ${env:JWT_SECRET}

functions:
  auth:
    handler: handler.auth
    events:
      - http:
          path: api/auth/login
          method: post
          cors: true
```

## Configuración Avanzada

### Variables de Entorno

Puedes usar variables de entorno para configurar el sistema:

```bash
export JWT_LOGIN_SERVICE_URL="https://api.tudominio.com/auth/login"
export JWT_SECRET_KEY="tu-clave-secreta-muy-segura"
export JWT_ALGORITHM="HS256"
export JWT_VERIFY="True"
export JWT_SYNC_ROLES="True"
```

### Sincronización de Roles

Si quieres que los roles de los usuarios se sincronicen automáticamente desde el JWT:

1. Activa `JWT_SYNC_ROLES = True` en tu configuración
2. Asegúrate de que tu token JWT incluya una claim `roles` con una lista de nombres de roles
3. Crea los roles en Superset con los mismos nombres que usas en tu servicio

Los roles se actualizarán en cada login del usuario.

### Timeout y Reintentos

Puedes configurar timeouts para las llamadas al servicio JWT:

```python
# En jwt_manager.py, modifica el método authenticate_with_jwt_service:
response = requests.post(
    self.jwt_login_url,
    json={"tenant": tenant, "email": email, "password": password},
    timeout=10,  # Aumenta este valor si tu servicio es lento
)
```

### Algoritmos Soportados

Los algoritmos JWT más comunes son:

- **HS256** (HMAC con SHA-256): Simétrico, usa clave secreta
- **RS256** (RSA con SHA-256): Asimétrico, usa par de claves pública/privada

Para usar RS256:

```python
JWT_ALGORITHM = "RS256"
JWT_SECRET_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"""
```

## Flujo de Autenticación

1. Usuario accede a `/login`
2. Completa formulario (tenant, email, password)
3. Superset envía credenciales al servicio Node.js
4. Servicio Node.js valida credenciales y retorna JWT
5. Superset valida el JWT y extrae claims
6. Superset crea/actualiza usuario local con prefijo `{tenant}_{email}`
7. Superset almacena JWT en sesión
8. Usuario es autenticado y redirigido a la página principal

## Seguridad

### Producción

Para producción, asegúrate de:

1. **Usar HTTPS**: Configura SSL/TLS para todas las conexiones
2. **Clave Secreta Fuerte**: Usa una clave JWT de al menos 32 caracteres aleatorios
3. **Verificar Firma JWT**: Mantén `JWT_VERIFY = True`
4. **Token Expiration**: Configura tiempos de expiración apropiados (1-2 horas)
5. **Secure Cookies**: Activa `SESSION_COOKIE_SECURE = True`
6. **Rate Limiting**: Limita intentos de login
7. **Logging**: Monitorea intentos de login fallidos
8. **Firewall**: Restringe acceso al servicio JWT desde IPs conocidas

### Variables de Entorno

Nunca incluyas secrets en el código. Usa variables de entorno:

```python
import os

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
```

## Troubleshooting

### Error: "Invalid tenant, email, or password"

- Verifica que el servicio Node.js esté corriendo
- Verifica la URL del servicio en `JWT_LOGIN_SERVICE_URL`
- Revisa los logs del servicio Node.js para ver el error específico

### Error: "JWT token has expired"

- El token tiene un tiempo de expiración
- El usuario debe hacer login nuevamente
- Considera implementar refresh tokens si necesitas sesiones más largas

### Error: "Invalid JWT token"

- La clave secreta no coincide entre Superset y el servicio Node.js
- Verifica que `JWT_SECRET_KEY` sea idéntica en ambos sistemas
- Verifica que el algoritmo (`JWT_ALGORITHM`) sea el mismo

### Usuario no puede acceder a dashboards

- Verifica que el usuario tenga el rol correcto asignado
- Si usas `JWT_SYNC_ROLES`, asegúrate de que los roles existan en Superset
- Revisa los permisos del rol en Superset

### Error de CORS

Si tu servicio Node.js está en un dominio diferente:

```python
# En superset_config.py
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": ["https://tu-servicio-nodejs.com"],
}
```

## Testing

### Probar Localmente

1. Inicia tu servicio Node.js:
   ```bash
   node server.js
   # o
   serverless offline
   ```

2. Inicia Superset:
   ```bash
   superset run -p 8088 --with-threads --reload --debugger
   ```

3. Accede a `http://localhost:8088/login`

### Verificar JWT Manualmente

Puedes verificar tokens JWT en https://jwt.io o con Python:

```python
import jwt

token = "tu-token-aqui"
secret = "tu-clave-secreta"

decoded = jwt.decode(token, secret, algorithms=["HS256"])
print(decoded)
```

### Logs de Debug

Activa logs de debug en `superset_config.py`:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("superset.security.jwt_manager")
logger.setLevel(logging.DEBUG)
```

## Migración desde Autenticación Estándar

Si ya tienes usuarios en Superset:

1. Los usuarios existentes seguirán funcionando
2. Los nuevos usuarios se crearán con el prefijo `{tenant}_{email}`
3. Puedes migrar usuarios existentes manualmente o con un script

Ejemplo de script de migración:

```python
from superset import db
from superset.security import SupersetSecurityManager

# Obtener usuarios sin prefijo
users = db.session.query(User).filter(~User.username.contains('_')).all()

for user in users:
    # Asignar tenant por defecto o desde otra fuente
    tenant = "default"
    new_username = f"{tenant}_{user.username}"
    user.username = new_username
    db.session.commit()
```

## Soporte

Para problemas o preguntas:

1. Revisa los logs de Superset: `logs/superset.log`
2. Revisa los logs de tu servicio Node.js
3. Verifica la configuración en `superset_config.py`
4. Consulta la documentación de Superset: https://superset.apache.org/docs/

## License

Este código sigue la licencia Apache 2.0 de Apache Superset.
