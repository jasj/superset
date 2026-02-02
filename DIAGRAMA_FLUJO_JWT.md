# Diagrama de Flujo - Autenticación JWT Multi-Tenant

## 🔄 Flujo de Autenticación Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         1. USUARIO ACCEDE AL LOGIN                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ http://localhost:8088/login
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    2. SUPERSET: Renderiza Formulario                    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Formulario de Login (login_jwt.html)                          │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Tenant:   [_____________]  (ej: company1)               │  │    │
│  │  │  Email:    [_____________]  (ej: user@example.com)       │  │    │
│  │  │  Password: [_____________]  (ej: ********)               │  │    │
│  │  │                                                           │  │    │
│  │  │                    [  Sign In  ]                         │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Usuario completa y envía
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               3. SUPERSET: JWTAuthView.login() recibe POST              │
│                                                                          │
│  JWTAuthView valida:                                                    │
│  ✓ tenant != ""                                                         │
│  ✓ email != ""                                                          │
│  ✓ password != ""                                                       │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Llama a auth_user_jwt()
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│         4. SUPERSET: JWTSecurityManager.auth_user_jwt()                 │
│                                                                          │
│  Prepara request:                                                       │
│  {                                                                      │
│    "tenant": "company1",                                                │
│    "email": "user@example.com",                                         │
│    "password": "password123"                                            │
│  }                                                                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ POST /api/auth/login
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              5. NODE.JS SERVICE: Recibe solicitud                        │
│                                                                          │
│  server.js:                                                             │
│  1. Valida campos requeridos                                            │
│  2. Busca usuario en base de datos                                      │
│     getUserFromDatabase(tenant, email)                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Consulta BD
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    6. BASE DE DATOS: Busca Usuario                      │
│                                                                          │
│  SELECT * FROM users                                                    │
│  WHERE tenant = 'company1'                                              │
│    AND email = 'user@example.com'                                       │
│                                                                          │
│  Resultado:                                                             │
│  {                                                                      │
│    email: "user@example.com",                                           │
│    passwordHash: "$2b$10$...",                                          │
│    firstName: "John",                                                   │
│    lastName: "Doe",                                                     │
│    tenant: "company1",                                                  │
│    roles: ["Admin", "Analyst"]                                          │
│  }                                                                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Usuario encontrado
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           7. NODE.JS SERVICE: Valida Password con bcrypt                │
│                                                                          │
│  bcrypt.compare(password, user.passwordHash)                            │
│                                                                          │
│  Si válido: ✓                                                           │
│  Si inválido: ✗ → return 401 Unauthorized                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Password correcto
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              8. NODE.JS SERVICE: Genera JWT Token                        │
│                                                                          │
│  jwt.sign({                                                             │
│    email: "user@example.com",                                           │
│    tenant: "company1",                                                  │
│    firstName: "John",                                                   │
│    lastName: "Doe",                                                     │
│    roles: ["Admin", "Analyst"],                                         │
│    exp: [timestamp + 1 hour],                                           │
│    iat: [timestamp now]                                                 │
│  }, JWT_SECRET, { algorithm: 'HS256' })                                 │
│                                                                          │
│  Token generado: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Return 200 OK + token
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              9. SUPERSET: Recibe JWT Token                               │
│                                                                          │
│  Response:                                                              │
│  {                                                                      │
│    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",                │
│    "user": {                                                            │
│      "email": "user@example.com",                                       │
│      "firstName": "John",                                               │
│      "lastName": "Doe",                                                 │
│      "tenant": "company1",                                              │
│      "roles": ["Admin", "Analyst"]                                      │
│    }                                                                    │
│  }                                                                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Decodifica y valida JWT
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            10. SUPERSET: JWTSecurityManager.decode_jwt()                │
│                                                                          │
│  jwt.decode(token, JWT_SECRET, algorithms=['HS256'])                    │
│                                                                          │
│  Validaciones:                                                          │
│  ✓ Firma válida (usando JWT_SECRET)                                    │
│  ✓ Token no expirado (exp > now)                                       │
│  ✓ Tenant coincide con el enviado                                      │
│                                                                          │
│  Resultado:                                                             │
│  {                                                                      │
│    email: "user@example.com",                                           │
│    tenant: "company1",                                                  │
│    firstName: "John",                                                   │
│    lastName: "Doe",                                                     │
│    roles: ["Admin", "Analyst"]                                          │
│  }                                                                      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ JWT válido
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│         11. SUPERSET: Busca/Crea Usuario Local                          │
│                                                                          │
│  Username: "company1_user@example.com"                                  │
│            (prefijo tenant para aislamiento)                            │
│                                                                          │
│  ¿Usuario existe?                                                       │
│  │                                                                       │
│  ├─ NO → Crear nuevo usuario:                                           │
│  │        - username: "company1_user@example.com"                       │
│  │        - first_name: "John"                                          │
│  │        - last_name: "Doe"                                            │
│  │        - email: "user@example.com"                                   │
│  │        - role: "Public" (default)                                    │
│  │                                                                       │
│  └─ SÍ → Actualizar información:                                        │
│           - first_name: "John"                                          │
│           - last_name: "Doe"                                            │
│                                                                          │
│  Si JWT_SYNC_ROLES=True:                                                │
│    → Sincronizar roles desde JWT                                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Usuario listo
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              12. SUPERSET: Guarda JWT en Sesión                          │
│                                                                          │
│  session['jwt_token'] = token                                           │
│  session['tenant'] = 'company1'                                         │
│  g.jwt_token = token                                                    │
│  g.tenant = 'company1'                                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Autenticar usuario
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              13. SUPERSET: login_user(user)                              │
│                                                                          │
│  Flask-Login autentica al usuario en la sesión                          │
│  Usuario ahora tiene acceso a Superset                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ Redirect a dashboard
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              14. SUPERSET: Redirige a Dashboard                          │
│                                                                          │
│  redirect(appbuilder.get_url_for_index)                                 │
│                                                                          │
│  Usuario ve:                                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Superset - Dashboard                                          │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Welcome, John Doe (company1_user@example.com)          │  │    │
│  │  │  [Dashboards] [Charts] [Datasets] [SQL Lab]             │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                                                                 │    │
│  │  [Dashboard content here...]                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

```

## 🔐 Aislamiento Multi-Tenant

```
┌───────────────────────────────────────────────────────────────┐
│                    BASE DE DATOS SUPERSET                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Usuarios con prefijo de tenant:                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Tenant: company1                                       │ │
│  │  ├─ company1_user1@example.com                          │ │
│  │  ├─ company1_user2@example.com                          │ │
│  │  └─ company1_admin@example.com                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Tenant: company2                                       │ │
│  │  ├─ company2_user1@example.com                          │ │
│  │  └─ company2_admin@example.com                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ⚠️ Los usuarios de company1 NO pueden ver ni acceder        │
│     a los recursos de company2 (y viceversa)                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## 🔄 Validación de Token en Cada Request

```
┌─────────────────────────────────────────────────────────────┐
│           Usuario ya autenticado hace request               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ GET /api/v1/dashboard/list
                        ▼
┌─────────────────────────────────────────────────────────────┐
│    SUPERSET: Middleware verifica sesión                     │
│                                                             │
│    ¿Existe session['jwt_token']?                           │
│    │                                                        │
│    ├─ NO → Redirect a /login                               │
│    │                                                        │
│    └─ SÍ → Validar JWT token                               │
│            jwt.decode(session['jwt_token'], JWT_SECRET)    │
│            │                                                │
│            ├─ Token expirado → Redirect a /login           │
│            │                                                │
│            └─ Token válido → Continuar request             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Token válido
                        ▼
┌─────────────────────────────────────────────────────────────┐
│    SUPERSET: Procesa request con usuario autenticado       │
│                                                             │
│    g.user = user_object                                    │
│    g.tenant = 'company1'                                   │
│                                                             │
│    Aplicar filtros por tenant si es necesario              │
└─────────────────────────────────────────────────────────────┘
```

## 🛡️ Seguridad del Proceso

```
┌─────────────────────────────────────────────────────────────┐
│                  CAPAS DE SEGURIDAD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PASSWORD HASHING (Node.js)                             │
│     • bcrypt con salt automático                           │
│     • Costo factor: 10 (2^10 = 1024 iteraciones)          │
│     • No se almacena password en texto plano               │
│                                                             │
│  2. JWT SIGNATURE (Node.js)                                │
│     • Token firmado con JWT_SECRET                         │
│     • Algoritmo: HS256 (HMAC-SHA256)                       │
│     • No se puede falsificar sin la clave                  │
│                                                             │
│  3. TOKEN VALIDATION (Superset)                            │
│     • Verifica firma con JWT_SECRET                        │
│     • Valida expiración (exp claim)                        │
│     • Valida tenant en token                               │
│                                                             │
│  4. TENANT ISOLATION (Superset)                            │
│     • Username con prefijo: tenant_email                   │
│     • Usuarios de diferentes tenants están separados       │
│                                                             │
│  5. SESSION MANAGEMENT (Superset)                          │
│     • Token almacenado en sesión del servidor              │
│     • Cookie HttpOnly (no accesible desde JS)              │
│     • Cookie Secure en HTTPS                               │
│                                                             │
│  6. HTTPS (Producción)                                     │
│     • Cifrado en tránsito                                  │
│     • Previene man-in-the-middle attacks                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Componentes del Sistema

```
┌────────────────────────────────────────────────────────────────┐
│                     COMPONENTES CREADOS                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  SUPERSET (Python/Flask)                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  JWTSecurityManager                                      │ │
│  │  • Extiende SupersetSecurityManager                      │ │
│  │  • authenticate_with_jwt_service()                       │ │
│  │  • decode_jwt()                                          │ │
│  │  • auth_user_jwt()                                       │ │
│  │  • sync_user_roles()                                     │ │
│  │  • load_user_from_jwt()                                  │ │
│  │  • register_views()                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  JWTAuthView                                             │ │
│  │  • Extiende AuthView                                     │ │
│  │  • login() GET/POST                                      │ │
│  │  • Renderiza login_jwt.html                             │ │
│  │  • Valida formulario                                     │ │
│  │  • Maneja autenticación                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  login_jwt.html                                          │ │
│  │  • Formulario con campos: tenant, email, password       │ │
│  │  • Bootstrap styling                                     │ │
│  │  • Responsive design                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  NODE.JS SERVICE (Express)                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  /api/auth/login                                         │ │
│  │  • Valida credenciales                                   │ │
│  │  • Consulta base de datos                                │ │
│  │  • Verifica password con bcrypt                          │ │
│  │  • Genera JWT token                                      │ │
│  │  • Retorna token + user info                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  /api/auth/verify                                        │ │
│  │  • Valida JWT token                                      │ │
│  │  • Retorna decoded claims                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  /health                                                 │ │
│  │  • Health check endpoint                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

Este diagrama muestra el flujo completo de autenticación desde que el usuario accede al login hasta que está autenticado y viendo el dashboard de Superset.
