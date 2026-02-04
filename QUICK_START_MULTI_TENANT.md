# Quick Start - Multi-Tenant con Bases de Datos Dinámicas

## 🚀 Inicio Rápido (5 minutos)

### Paso 1: Crear Bases de Datos para tus Tenants

```bash
cd /home/optikubuntu/projects/sibuBI/superset

# Crear BD para tenant "acme"
./scripts/create_tenant_db.sh acme

# Crear BD para tenant "demo"
./scripts/create_tenant_db.sh demo
```

### Paso 2: Reiniciar Superset

```bash
docker-compose restart superset_app
```

### Paso 3: Verificar Configuración

```bash
# Ver logs de inicialización
docker logs superset_app 2>&1 | grep -i "tenant"
```

Deberías ver:
```
INFO: Multi-tenant database manager configured
INFO: TenantDatabaseManager initialized
```

### Paso 4: Probar Login con Tenant

Tu servicio JWT Node.js ya está configurado. Prueba:

```bash
# Login como tenant "acme"
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "acme",
    "email": "user1@example.com",
    "password": "tu_password"
  }'
```

Superset se conectará automáticamente a la base de datos `acme`.

## ✅ Verificación

### Ver bases de datos creadas

```bash
docker exec -it superset-db-1 psql -U superset -l
```

Deberías ver:
```
acme     | superset | UTF8
demo     | superset | UTF8
superset | superset | UTF8
```

### Ver logs de conexión

```bash
docker logs superset_app -f
```

Cuando hagas login, verás:
```
DEBUG: Loaded tenant from session: acme
INFO: Created new database engine for tenant: acme
DEBUG: Set tenant engine for tenant: acme
```

## 🎯 ¿Qué hace cada tenant?

```
Usuario con tenant="acme"     →  BD: acme
Usuario con tenant="demo"     →  BD: demo
Usuario con tenant="cliente1" →  BD: cliente1
```

Cada tenant está **completamente aislado** en su propia base de datos.

## 📝 Notas Importantes

1. **Debes crear la BD antes del primer login**
   - Usa: `./scripts/create_tenant_db.sh <tenant_name>`

2. **El tenant viene del JWT**
   - Tu servicio Node.js ya lo incluye
   - Verifica que el JWT tenga: `"tenant": "nombre"`

3. **Los nombres de tenant deben ser válidos como nombres de BD**
   - Solo letras, números y guión bajo
   - Ejemplo válido: `acme`, `demo`, `cliente_1`
   - Ejemplo inválido: `cliente-1`, `mi tenant`

## 🐛 Solución Rápida de Problemas

### "database does not exist"
```bash
./scripts/create_tenant_db.sh <nombre_tenant>
```

### Verificar que el JWT incluye tenant
```bash
# En el servicio Node.js (nodejs-jwt-service-example/server.js)
# Verifica línea donde se firma el token:
const token = jwt.sign({
  email: user.email,
  tenant: tenant,  // ← Debe estar presente
  ...
}, SECRET_KEY);
```

### Reiniciar todo si algo falla
```bash
docker-compose restart superset_app
docker logs superset_app -f
```

## 📚 Documentación Completa

- **Guía detallada**: [MULTI_TENANT_DATABASE_GUIDE.md](MULTI_TENANT_DATABASE_GUIDE.md)
- **Resumen de implementación**: [MULTI_TENANT_IMPLEMENTATION_SUMMARY.md](MULTI_TENANT_IMPLEMENTATION_SUMMARY.md)

## ✨ ¡Listo!

Tu Superset ahora soporta multi-tenancy con bases de datos dinámicas. Cada login con un tenant diferente se conecta a una base de datos diferente automáticamente.
