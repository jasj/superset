# Guía de Configuración Multi-Tenant con Bases de Datos Dinámicas

## Descripción General

Este sistema permite que Superset se conecte a bases de datos diferentes según el tenant del usuario autenticado mediante JWT. Cada tenant tiene su propia base de datos PostgreSQL aislada.

## Arquitectura

### Flujo de Autenticación y Conexión

```
1. Usuario inicia sesión → JWT con tenant
2. JWTSecurityManager extrae tenant del JWT
3. Tenant se almacena en sesión y g.tenant
4. TenantDatabaseManager crea/obtiene engine para el tenant
5. Todas las queries usan la base de datos del tenant
```

### Componentes

- **JWTSecurityManager** ([superset/security/jwt_manager.py](superset/security/jwt_manager.py))
  - Autentica usuarios contra servicio JWT externo
  - Extrae tenant del token JWT
  - Almacena tenant en sesión y contexto global

- **TenantDatabaseManager** ([superset/utils/tenant_database_manager.py](superset/utils/tenant_database_manager.py))
  - Gestiona engines de SQLAlchemy por tenant
  - Crea conexiones dinámicamente
  - Mantiene pool de conexiones por tenant
  - Rutea queries a la base de datos correcta

## Configuración

### 1. Variables de Entorno

Edita [docker/.env](docker/.env):

```bash
# Habilitar modo multi-tenant
MULTI_TENANT_ENABLED=true

# Patrón de nombres de bases de datos
# {tenant} será reemplazado por el tenant del usuario
TENANT_DATABASE_TEMPLATE={tenant}

# Ejemplos alternativos:
# TENANT_DATABASE_TEMPLATE={tenant}_db    # Para "acme_db", "demo_db"
# TENANT_DATABASE_TEMPLATE=superset_{tenant}  # Para "superset_acme", "superset_demo"
```

### 2. Configuración de Superset

La configuración en [docker/pythonpath_dev/superset_config.py](docker/pythonpath_dev/superset_config.py) ya está lista:

```python
# Multi-tenant habilitado
MULTI_TENANT_ENABLED = os.getenv("MULTI_TENANT_ENABLED", "True").lower() == "true"

# Template de nombres de BD
TENANT_DATABASE_TEMPLATE = os.getenv("TENANT_DATABASE_TEMPLATE", "{tenant}")
```

## Creación de Bases de Datos por Tenant

### Opción 1: Crear Manualmente en PostgreSQL

Conéctate al contenedor de PostgreSQL:

```bash
docker exec -it superset-db-1 psql -U superset
```

Crea una base de datos para cada tenant:

```sql
-- Para tenant "acme"
CREATE DATABASE acme;
GRANT ALL PRIVILEGES ON DATABASE acme TO superset;

-- Para tenant "demo"
CREATE DATABASE demo;
GRANT ALL PRIVILEGES ON DATABASE demo TO superset;

-- Verificar bases de datos creadas
\l
```

### Opción 2: Script de Creación Automática

Crea un script `create_tenant_db.sh`:

```bash
#!/bin/bash

TENANT=$1

if [ -z "$TENANT" ]; then
    echo "Uso: ./create_tenant_db.sh <nombre_tenant>"
    exit 1
fi

docker exec -it superset-db-1 psql -U superset -c "CREATE DATABASE ${TENANT};"
docker exec -it superset-db-1 psql -U superset -c "GRANT ALL PRIVILEGES ON DATABASE ${TENANT} TO superset;"

echo "✓ Base de datos '${TENANT}' creada exitosamente"
```

Uso:

```bash
chmod +x create_tenant_db.sh
./create_tenant_db.sh acme
./create_tenant_db.sh demo
```

### Opción 3: Creación Dinámica desde la Aplicación

Puedes crear las bases de datos dinámicamente cuando un usuario hace login por primera vez. Agrega esto al JWTSecurityManager:

```python
def create_tenant_database_if_not_exists(self, tenant: str) -> bool:
    """Create tenant database if it doesn't exist"""
    from superset.extensions import db
    from sqlalchemy import text

    try:
        # Conectar a la base de datos por defecto
        with db.engine.connect() as conn:
            # No se puede crear DB dentro de transacción
            conn.execute(text("COMMIT"))

            # Verificar si la base de datos existe
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": tenant}
            )

            if not result.fetchone():
                # Crear base de datos
                conn.execute(text(f"CREATE DATABASE {tenant}"))
                conn.execute(text(f"GRANT ALL PRIVILEGES ON DATABASE {tenant} TO superset"))
                logger.info(f"Created database for tenant: {tenant}")
                return True

    except Exception as e:
        logger.error(f"Failed to create database for tenant {tenant}: {e}")
        return False
```

## Verificación

### 1. Verificar Configuración

```bash
# En el contenedor de Superset
docker exec -it superset_app bash

# Verificar que el tenant se carga correctamente
python3 -c "
from flask import Flask, g, session
from superset import app
with app.app_context():
    print('✓ App inicializada')
    from superset.utils.tenant_database_manager import tenant_db_manager
    print(f'✓ TenantDatabaseManager: {tenant_db_manager}')
"
```

### 2. Probar Login con Tenant

```bash
# Ejemplo de login con tenant "acme"
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "acme",
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 3. Verificar Conexión a BD por Tenant

En los logs de Superset deberías ver:

```
INFO:superset.utils.tenant_database_manager:Created new database engine for tenant: acme
DEBUG:superset.utils.tenant_database_manager:Set tenant engine for tenant: acme
```

## Estructura de Datos por Tenant

Cada base de datos de tenant debe contener:

### Esquema de Metadatos de Superset

Si quieres que cada tenant tenga su propio conjunto de dashboards y charts:

```bash
# Opción 1: Copiar estructura desde base de datos principal
docker exec -it superset-db-1 bash
pg_dump -U superset -s superset | psql -U superset -d acme

# Opción 2: Ejecutar migraciones en cada tenant
# (Requiere modificar el sistema de migraciones)
```

### Datos Específicos del Tenant

Cada tenant puede tener:
- Sus propias tablas de datos de negocio
- Dashboards y visualizaciones independientes
- Usuarios y permisos aislados

## Solución de Problemas

### Error: "database does not exist"

**Causa**: La base de datos del tenant no está creada.

**Solución**: Crea la base de datos usando alguna de las opciones anteriores.

```bash
docker exec -it superset-db-1 psql -U superset -c "CREATE DATABASE acme;"
```

### Error: "could not connect to server"

**Causa**: Problemas de conexión con PostgreSQL.

**Solución**: Verifica que el contenedor de PostgreSQL esté corriendo:

```bash
docker ps | grep postgres
docker logs superset-db-1
```

### Tenant no se establece en g.tenant

**Causa**: El usuario no está autenticado o la sesión expiró.

**Solución**: Vuelve a hacer login. Verifica que el JWT contiene el campo `tenant`:

```python
import jwt
token = "tu_jwt_token_aquí"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded.get("tenant"))  # Debe mostrar el tenant
```

### Connection pool issues

**Causa**: Demasiados tenants o conexiones no se liberan.

**Solución**: Ajusta los parámetros de pool en [superset/utils/tenant_database_manager.py](superset/utils/tenant_database_manager.py:158-163):

```python
engine = create_engine(
    uri,
    poolclass=pool.QueuePool,
    pool_size=3,      # Reducir si hay muchos tenants
    max_overflow=5,   # Reducir overflow
    pool_pre_ping=True,
    pool_recycle=1800,  # Reciclar más frecuentemente
)
```

## Monitoreo y Logs

### Habilitar Logs Detallados

En [docker/.env](docker/.env):

```bash
SUPERSET_LOG_LEVEL=debug
```

### Ver Logs de Conexiones

```bash
# Ver logs del TenantDatabaseManager
docker logs superset_app 2>&1 | grep "tenant_database_manager"

# Ver logs de SQLAlchemy
docker logs superset_app 2>&1 | grep "sqlalchemy"
```

### Verificar Engines Activos

```python
from superset.utils.tenant_database_manager import tenant_db_manager

# Listar todos los tenants con engines activos
print(f"Tenants activos: {list(tenant_db_manager.engines.keys())}")

# Ver engine específico
engine = tenant_db_manager.get_engine_for_tenant("acme")
print(f"Engine para acme: {engine.url}")
```

## Seguridad

### Aislamiento de Datos

- ✅ **Aislamiento completo**: Cada tenant tiene su propia base de datos PostgreSQL
- ✅ **No hay posibilidad de cross-tenant queries**: Las conexiones están completamente separadas
- ✅ **Autenticación obligatoria**: El tenant solo se establece después de autenticación JWT exitosa

### Mejores Prácticas

1. **Validar nombres de tenant**:
   - Solo caracteres alfanuméricos y guiones bajos
   - No permitir nombres de bases de datos del sistema (postgres, template0, etc.)

2. **Limitar tenants activos**:
   - Implementar límite de engines simultáneos
   - Dispose de engines inactivos después de N minutos

3. **Auditoría**:
   - Loguear todos los cambios de tenant
   - Monitorear intentos de acceso no autorizado

## Migración de Datos

### De Mono-Tenant a Multi-Tenant

Si ya tienes datos en una base de datos única:

```sql
-- 1. Exportar datos de un tenant específico
pg_dump -U superset -t 'tabla_tenant_acme_*' superset > acme_data.sql

-- 2. Crear nueva BD para el tenant
CREATE DATABASE acme;

-- 3. Importar datos
psql -U superset -d acme < acme_data.sql
```

## Referencias

- Documentación JWT: [JWT_AUTH_DOCUMENTATION.md](JWT_AUTH_DOCUMENTATION.md)
- Security Manager: [superset/security/jwt_manager.py](superset/security/jwt_manager.py)
- Tenant DB Manager: [superset/utils/tenant_database_manager.py](superset/utils/tenant_database_manager.py)
- Configuración: [docker/pythonpath_dev/superset_config.py](docker/pythonpath_dev/superset_config.py)
