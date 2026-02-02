# 🚀 Instrucciones Rápidas - JWT en Docker

## Paso 1: Instalar Dependencias en el Container

Necesitas instalar PyJWT y requests en el container de Superset:

```bash
# Ejecutar en tu terminal
docker compose exec superset pip install PyJWT>=2.0.0 requests>=2.25.0
```

## Paso 2: Configurar el Servicio Node.js

### Opción A: En tu máquina host (recomendado para desarrollo)

```bash
# 1. Ve a la carpeta del servicio
cd nodejs-jwt-service-example

# 2. Instala dependencias
npm install

# 3. Configura variables de entorno
cp .env.example .env.dev
# Edita .env.dev si necesitas cambiar el JWT_SECRET

# 4. Inicia el servicio
npm start
```

El servicio correrá en `http://localhost:3000`

### Opción B: Verificar que host.docker.internal funciona

```bash
# Desde dentro del container, prueba conectar al host
docker compose exec superset curl http://host.docker.internal:3000/health
```

## Paso 3: Reiniciar Superset en Docker

```bash
# Desde la raíz del proyecto
docker compose down
docker compose up -d
```

## Paso 4: Verificar los Logs

```bash
# Ver logs de Superset para verificar que cargó la configuración JWT
docker compose logs superset | grep -i jwt

# Ver logs en tiempo real
docker compose logs -f superset
```

## Paso 5: Probar el Login

1. Abre tu navegador en: http://localhost:8088/login
2. Deberías ver el formulario con 3 campos: **Tenant**, **Email**, **Password**
3. Usa las credenciales de prueba:
   - Tenant: `company1`
   - Email: `user1@example.com`
   - Password: `demo123`

## 🔧 Troubleshooting

### Problema 1: Sigue mostrando el login antiguo

**Solución:**
```bash
# Limpiar cache de navegador (Ctrl+Shift+Del)
# O forzar rebuild:
docker compose build --no-cache superset
docker compose up -d
```

### Problema 2: Error de import al iniciar Superset

**Solución:**
```bash
# Instalar dependencias dentro del container
docker compose exec superset pip install PyJWT requests

# Reiniciar
docker compose restart superset
```

### Problema 3: No conecta al servicio Node.js

**Verificar:**
```bash
# 1. ¿El servicio Node.js está corriendo?
curl http://localhost:3000/health

# 2. ¿El container puede ver el host?
docker compose exec superset curl http://host.docker.internal:3000/health

# 3. Si no funciona host.docker.internal, usa la IP del host:
# En Linux:
ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
# Luego actualiza JWT_LOGIN_SERVICE_URL en docker/.env
```

### Problema 4: Error "Invalid credentials" pero las credenciales son correctas

**Verificar:**
```bash
# 1. Ver logs del servicio Node.js
# Buscar mensajes de login failed

# 2. Verificar JWT_SECRET coincide en ambos lados
# docker/.env: JWT_SECRET_KEY=xxx
# nodejs-jwt-service-example/.env.dev: JWT_SECRET=xxx
```

### Problema 5: Usuario se crea pero no puede acceder a nada

**Solución:**
```bash
# El usuario nuevo necesita permisos, asignar rol manualmente:
docker compose exec superset superset fab reset-password --username company1_user1@example.com

# O desde la UI de Superset con el usuario admin
```

## 📋 Verificación Completa

Lista de chequeo:

- [ ] **Node.js service corriendo** - `curl http://localhost:3000/health` retorna 200
- [ ] **PyJWT instalado** - `docker compose exec superset pip show PyJWT`
- [ ] **requests instalado** - `docker compose exec superset pip show requests`
- [ ] **docker/.env tiene JWT_SECRET_KEY** - `grep JWT_SECRET_KEY docker/.env`
- [ ] **Superset reiniciado** - `docker compose ps` muestra superset "healthy"
- [ ] **Logs sin errores** - `docker compose logs superset | tail -50` sin errores
- [ ] **Login page correcta** - http://localhost:8088/login muestra 3 campos

## 🎯 Comandos Útiles

```bash
# Ver todos los containers
docker compose ps

# Ver logs en tiempo real
docker compose logs -f superset

# Entrar al container de Superset
docker compose exec superset bash

# Reiniciar solo Superset
docker compose restart superset

# Rebuild completo (si hay cambios en código)
docker compose build superset
docker compose up -d

# Ver variables de entorno en el container
docker compose exec superset env | grep JWT
```

## 🔑 Credenciales de Prueba

Una vez que el servicio Node.js esté corriendo, puedes usar estas credenciales:

| Tenant | Email | Password | Roles |
|--------|-------|----------|-------|
| company1 | user1@example.com | demo123 | Admin, Analyst |
| company1 | user2@example.com | demo123 | Analyst |
| company2 | admin@example.com | demo123 | Admin |

## 🆘 Si Nada Funciona

```bash
# 1. Para y elimina todo
docker compose down -v

# 2. Rebuild desde cero
docker compose build --no-cache

# 3. Inicia todo de nuevo
docker compose up -d

# 4. Instala dependencias Python
docker compose exec superset pip install PyJWT requests

# 5. Reinicia Superset
docker compose restart superset

# 6. Verifica logs
docker compose logs -f superset
```
