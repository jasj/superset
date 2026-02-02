# ✅ Checklist de Implementación JWT Multi-Tenant

Usa este checklist para verificar que la implementación está completa y funcional.

## 📋 Pre-requisitos

- [ ] Python 3.8+ instalado
- [ ] Node.js 18+ instalado
- [ ] npm o yarn instalado
- [ ] Superset instalado
- [ ] Editor de código (VS Code, PyCharm, etc.)
- [ ] Terminal/CLI accesible

## 🔧 Instalación - Superset

### 1. Archivos Verificados

- [ ] `superset/security/jwt_manager.py` existe
- [ ] `superset/views/jwt_auth.py` existe  
- [ ] `superset/templates/superset/login_jwt.html` existe
- [ ] `superset_config_jwt_example.py` existe

### 2. Dependencias Python

```bash
pip install PyJWT>=2.0.0 requests>=2.25.0
```

- [ ] PyJWT instalado (verificar con `pip list | grep PyJWT`)
- [ ] requests instalado (verificar con `pip list | grep requests`)

### 3. Configuración

- [ ] Crear archivo `superset_config.py` en PYTHONPATH
- [ ] Copiar configuración de ejemplo: `cp superset_config_jwt_example.py superset_config.py`
- [ ] Editar `superset_config.py`:
  - [ ] `CUSTOM_SECURITY_MANAGER = JWTSecurityManager`
  - [ ] `JWT_LOGIN_SERVICE_URL` configurado (ej: `http://localhost:3000/api/auth/login`)
  - [ ] `JWT_SECRET_KEY` configurado (debe coincidir con Node.js)
  - [ ] `JWT_ALGORITHM = "HS256"`
  - [ ] `JWT_VERIFY = True`
  - [ ] `SECRET_KEY` cambiado (no usar CHANGE_ME_SECRET_KEY)
  - [ ] `SQLALCHEMY_DATABASE_URI` configurado

### 4. Base de Datos

```bash
superset db upgrade
superset init
```

- [ ] Migraciones ejecutadas sin errores
- [ ] Roles iniciales creados (Admin, Gamma, etc.)
- [ ] Usuario admin creado (si es primera vez)

## 🔧 Instalación - Node.js Service

### 1. Estructura de Archivos

```bash
cd nodejs-jwt-service-example
```

- [ ] `server.js` existe
- [ ] `handler.js` existe
- [ ] `serverless.yml` existe
- [ ] `package.json` existe
- [ ] `.env.example` existe

### 2. Dependencias Node.js

```bash
npm install
```

- [ ] `package.json` dependencies instaladas
- [ ] `node_modules/` creado
- [ ] Sin errores de instalación

### 3. Configuración

```bash
cp .env.example .env.dev
```

- [ ] Archivo `.env.dev` creado
- [ ] `JWT_SECRET` configurado (debe coincidir con Superset)
- [ ] `CORS_ORIGIN=http://localhost:8088`
- [ ] `PORT=3000`
- [ ] `NODE_ENV=development`

## 🧪 Pruebas - Node.js Service

### 1. Iniciar Servicio

```bash
npm start
```

- [ ] Servidor inicia sin errores
- [ ] Mensaje "JWT Auth Service running on port 3000" visible
- [ ] Sin errores en consola

### 2. Health Check

```bash
curl http://localhost:3000/health
```

- [ ] Respuesta 200 OK
- [ ] JSON con `{"status":"ok",...}`

### 3. Test Login

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"tenant":"company1","email":"user1@example.com","password":"demo123"}'
```

- [ ] Respuesta 200 OK
- [ ] JSON contiene `token`
- [ ] JSON contiene `user` con email, firstName, lastName, tenant
- [ ] Token es un JWT válido (verificar en jwt.io)

### 4. Test Credenciales Inválidas

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"tenant":"company1","email":"user1@example.com","password":"wrong"}'
```

- [ ] Respuesta 401 Unauthorized
- [ ] JSON contiene `{"error":"Invalid credentials"}`

## 🧪 Pruebas - Superset

### 1. Iniciar Superset

```bash
superset run -p 8088 --with-threads --reload
```

- [ ] Superset inicia sin errores
- [ ] Accesible en `http://localhost:8088`
- [ ] No hay errores de importación en consola

### 2. Verificar Login Page

```bash
# En navegador:
http://localhost:8088/login
```

- [ ] Página de login se carga
- [ ] Formulario tiene 3 campos: Tenant, Email, Password
- [ ] Diseño se ve correcto
- [ ] No hay errores 404 en consola del navegador

### 3. Test Login desde Navegador

Completar formulario:
- Tenant: `company1`
- Email: `user1@example.com`  
- Password: `demo123`

- [ ] Login exitoso
- [ ] Redirige a dashboard/home
- [ ] Usuario aparece como "John Doe" en UI
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs de Superset

### 4. Verificar Usuario en BD

```bash
# Si usas SQLite:
sqlite3 /path/to/superset.db
SELECT username, first_name, last_name, email FROM ab_user WHERE username LIKE 'company1_%';
```

- [ ] Usuario existe con username `company1_user1@example.com`
- [ ] Nombre y apellido correctos
- [ ] Email correcto

### 5. Test Multi-Tenant

Login con tenant diferente:
- Tenant: `company2`
- Email: `admin@example.com`
- Password: `demo123`

- [ ] Login exitoso
- [ ] Usuario creado como `company2_admin@example.com`
- [ ] Usuarios de company1 y company2 están separados

### 6. Test Logout

- [ ] Click en logout funciona
- [ ] Redirige a login
- [ ] Sesión eliminada correctamente

## 🔐 Verificación de Seguridad

### 1. JWT Token

Obtener token y verificar en https://jwt.io:

- [ ] Token tiene firma válida (si verificas con JWT_SECRET)
- [ ] Contiene claims: email, tenant, firstName, lastName
- [ ] Contiene exp (expiration)
- [ ] Contiene iat (issued at)
- [ ] Algoritmo es HS256

### 2. Password Hashing

Verificar en `server.js`:

- [ ] Passwords NO están en texto plano
- [ ] Se usa bcrypt para comparar
- [ ] Salt es automático

### 3. CORS

```bash
# Test CORS desde origen diferente
curl -H "Origin: http://malicious-site.com" \
  -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"tenant":"company1","email":"user1@example.com","password":"demo123"}'
```

- [ ] Respuesta no permite origen no configurado
- [ ] Solo `CORS_ORIGIN` configurado es permitido

### 4. Session Security

En Superset, verificar cookies en navegador (DevTools → Application → Cookies):

- [ ] Cookie de sesión tiene `HttpOnly` flag
- [ ] Cookie tiene `SameSite` attribute
- [ ] En producción: Cookie tiene `Secure` flag

## 📊 Verificación de Funcionalidad

### 1. Crear Dashboard

- [ ] Usuario puede crear dashboard
- [ ] Usuario puede ver sus dashboards
- [ ] Usuario NO puede ver dashboards de otro tenant

### 2. SQL Lab

- [ ] Usuario puede acceder a SQL Lab
- [ ] Usuario puede ejecutar queries
- [ ] Permisos correctos aplicados

### 3. Explorar Datos

- [ ] Usuario puede explorar datasets
- [ ] Usuario puede crear charts
- [ ] Permisos correctos aplicados

## 🚀 Preparación para Producción

### 1. Secrets

- [ ] `JWT_SECRET_KEY` es fuerte (32+ caracteres aleatorios)
- [ ] `SECRET_KEY` de Superset es fuerte
- [ ] Secrets NO están en código
- [ ] Secrets se cargan desde variables de entorno

### 2. HTTPS

- [ ] Certificado SSL configurado
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] Redirección HTTP → HTTPS configurada
- [ ] CORS origins usan HTTPS

### 3. Base de Datos

- [ ] Usar PostgreSQL o MySQL (no SQLite)
- [ ] Conexión cifrada a BD
- [ ] Credenciales de BD seguras
- [ ] Backups configurados

### 4. Node.js Service

- [ ] Implementada base de datos real (no mock)
- [ ] Rate limiting implementado
- [ ] Logging configurado
- [ ] Monitoreo configurado (CloudWatch, DataDog, etc.)
- [ ] Error tracking (Sentry, etc.)

### 5. Deploy

#### Serverless (AWS Lambda)

```bash
cd nodejs-jwt-service-example
npm run deploy:prod
```

- [ ] Deploy exitoso
- [ ] URL de API Gateway anotada
- [ ] Variables de entorno configuradas en Lambda
- [ ] Logs funcionando en CloudWatch

#### Superset

- [ ] `JWT_LOGIN_SERVICE_URL` apunta a URL de producción
- [ ] Docker image creada (si aplica)
- [ ] Kubernetes deployment configurado (si aplica)
- [ ] Variables de entorno configuradas

### 6. Testing en Producción

- [ ] Login funciona en producción
- [ ] Usuarios se crean correctamente
- [ ] JWT se valida correctamente
- [ ] Performance es aceptable
- [ ] Logs muestran información útil

## 📝 Documentación

- [ ] README actualizado con URLs de producción
- [ ] Documentación de API actualizada
- [ ] Runbook para troubleshooting creado
- [ ] Contactos de soporte documentados
- [ ] Proceso de onboarding de nuevos tenants documentado

## 🐛 Troubleshooting Realizado

- [ ] Test con credenciales inválidas
- [ ] Test con tenant inexistente
- [ ] Test con token expirado
- [ ] Test con JWT_SECRET incorrecto
- [ ] Test sin servicio Node.js corriendo
- [ ] Test con BD fuera de línea

## 📈 Monitoreo

- [ ] Métricas de login (exitosos/fallidos)
- [ ] Alertas configuradas (tasa de error alta)
- [ ] Dashboard de monitoreo
- [ ] Logs centralizados
- [ ] Health checks automatizados

## ✅ Sign-off

Una vez completado todo el checklist:

- [ ] Pruebas funcionales exitosas
- [ ] Pruebas de seguridad exitosas
- [ ] Performance aceptable
- [ ] Documentación completa
- [ ] Equipo entrenado
- [ ] Plan de rollback preparado
- [ ] Aprobación de stakeholders

---

**Fecha de completación**: _________________

**Implementado por**: _________________

**Revisado por**: _________________

**Notas adicionales**:

```
_______________________________________________________________

_______________________________________________________________

_______________________________________________________________
```
