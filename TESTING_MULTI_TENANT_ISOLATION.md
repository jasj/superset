# Guía de Pruebas: Aislamiento Multi-Tenant

## 🐛 Problema Resuelto

**Síntoma Original**:
- Usuario se logueaba con `company1` y creaba un dashboard
- Usuario se logueaba con `company2` y veía el mismo dashboard
- La BD `company1` existía pero `company2` NO existía
- No había error al conectarse con `company2`

**Causa del Problema**:
El `TenantDatabaseManager` creaba engines por tenant, pero `db.session` de Flask-SQLAlchemy seguía usando el engine principal (`superset` BD). Las queries de metadatos (dashboards, charts) no usaban los engines por tenant.

**Solución Implementada**:
Modificado `_before_request_handler()` para **rebind** `db.session` al engine del tenant en cada request:

```python
db.session.bind = engine  # Cambia el engine de la sesión activa
```

Ahora TODAS las queries (incluyendo metadatos) usan la BD correcta del tenant.

## ✅ Pasos de Prueba

### Preparación: Crear Bases de Datos

```bash
cd /home/optikubuntu/projects/sibuBI/superset

# Crear BD para company1
./scripts/create_tenant_db.sh company1

# Crear BD para company2
./scripts/create_tenant_db.sh company2

# Verificar que existen
docker exec -it superset-db-1 psql -U superset -l | grep company
```

Deberías ver:
```
company1 | superset | UTF8
company2 | superset | UTF8
```

### Prueba 1: Aislamiento de Dashboards

**Objetivo**: Verificar que dashboards creados en un tenant NO aparecen en otro.

#### Paso 1: Login como company1

```bash
# Abrir navegador en modo incógnito
# Ir a: http://localhost:8088

# Login:
Tenant: company1
Email: user@company1.com
Password: tu_password
```

#### Paso 2: Crear Dashboard en company1

1. Ir a "Dashboards" → "+" (Create Dashboard)
2. Nombre: "Dashboard Company 1"
3. Guardar

#### Paso 3: Verificar en BD company1

```bash
docker exec -it superset-db-1 psql -U superset -d company1 -c "SELECT * FROM dashboards;"
```

Deberías ver el dashboard "Dashboard Company 1".

#### Paso 4: Logout y Login como company2

```bash
# Cerrar sesión
# Abrir NUEVA ventana incógnito (o borrar cookies)

# Login:
Tenant: company2
Email: user@company2.com
Password: tu_password
```

#### Paso 5: Verificar Aislamiento

1. Ir a "Dashboards"
2. **NO deberías ver** "Dashboard Company 1"
3. La lista debe estar vacía (o solo tus dashboards de company2)

#### Paso 6: Crear Dashboard en company2

1. Crear dashboard: "Dashboard Company 2"
2. Guardar

#### Paso 7: Verificar BDs Separadas

```bash
# Ver dashboard en company1
docker exec -it superset-db-1 psql -U superset -d company1 -c "SELECT dashboard_title FROM dashboards;"
# Output: Dashboard Company 1

# Ver dashboard en company2
docker exec -it superset-db-1 psql -U superset -d company2 -c "SELECT dashboard_title FROM dashboards;"
# Output: Dashboard Company 2
```

✅ **Resultado Esperado**: Cada tenant ve solo sus propios dashboards.

### Prueba 2: Error con Tenant sin Base de Datos

**Objetivo**: Verificar que si un tenant NO tiene BD, se produce un error apropiado.

#### Paso 1: Intentar Login con Tenant sin BD

```bash
# Login:
Tenant: company3
Email: user@company3.com
Password: tu_password
```

#### Paso 2: Observar Logs

```bash
docker logs superset_app -f
```

Deberías ver:
```
ERROR: Failed to create database engine for tenant company3: ...
WARNING: Failed to get engine for tenant: company3
```

#### Paso 3: Verificar Comportamiento

Dependiendo de la implementación, deberías ver:
- Error de conexión
- Mensaje de "database does not exist"
- O fallback al engine por defecto (con warning en logs)

🔴 **Si NO ves errores**: El sistema está cayendo back al engine por defecto (`superset` BD), lo cual es un problema de seguridad.

**Solución**: Modificar `_before_request_handler` para lanzar excepción si el tenant no tiene BD.

### Prueba 3: Múltiples Usuarios Simultáneos

**Objetivo**: Verificar que múltiples usuarios de diferentes tenants pueden usar el sistema simultáneamente.

#### Setup

```bash
# Abrir 3 navegadores diferentes (o 3 ventanas incógnito):
# Browser 1: Login como company1
# Browser 2: Login como company2
# Browser 3: Login como company1 (otro usuario)
```

#### Acciones Simultáneas

1. **Browser 1**: Crear dashboard "Test 1" en company1
2. **Browser 2**: Crear dashboard "Test 2" en company2
3. **Browser 3**: Ver dashboards de company1 (debe ver "Test 1" y anteriores)

#### Verificación

```bash
# Ver conexiones activas por BD
docker exec -it superset-db-1 psql -U superset -c "
SELECT datname, count(*) as connections
FROM pg_stat_activity
WHERE datname IN ('company1', 'company2')
GROUP BY datname;
"
```

Deberías ver conexiones activas a ambas bases de datos.

✅ **Resultado Esperado**: Cada usuario se conecta a su BD sin interferencias.

### Prueba 4: Verificar Connection Pooling

**Objetivo**: Asegurar que el sistema no crea demasiadas conexiones.

```bash
# Ver engines activos en memoria
docker exec -it superset_app bash

python3 << 'EOF'
from superset.utils.tenant_database_manager import tenant_db_manager
print(f"Engines activos: {list(tenant_db_manager.engines.keys())}")
for tenant, engine in tenant_db_manager.engines.items():
    print(f"  {tenant}: {engine.pool.status()}")
EOF
```

Deberías ver info del pool para cada tenant activo.

## 🐛 Troubleshooting

### Problema: Dashboards aún se comparten entre tenants

**Diagnóstico**:
```bash
# Ver logs cuando haces una query
docker logs superset_app -f

# Busca esta línea cuando navegues a Dashboards:
# "Bound session to tenant database: company1"
```

**Si NO ves el log**:
- El tenant no se está estableciendo en `g.tenant`
- Verifica que el JWT contiene el campo `tenant`
- Verifica que `setup_tenant_context()` se ejecuta

**Si ves el log pero aún hay problemas**:
- El bind puede estar siendo ignorado
- Verifica que `db.session.remove()` se ejecuta en teardown

**Solución Nuclear**:
```bash
# Reiniciar todo
docker-compose restart
docker logs superset_app -f
```

### Problema: "database does not exist" para tenant válido

**Causa**: La BD del tenant no fue creada.

**Solución**:
```bash
./scripts/create_tenant_db.sh company1
docker-compose restart superset_app
```

### Problema: Queries van a BD incorrecta

**Diagnóstico**:
```bash
# Habilitar SQL echo en logs
# En superset_config.py:
# SQLALCHEMY_ECHO = True

# Ver qué BD se usa:
docker logs superset_app 2>&1 | grep "SELECT" | head -20
```

**Solución**: Verifica el orden de los `before_request` handlers:
```python
# JWTSecurityManager.setup_tenant_context() DEBE ejecutarse ANTES que
# TenantDatabaseManager._before_request_handler()
```

## 📊 Métricas de Aislamiento

### Verificar Aislamiento Completo

```sql
-- En cada BD de tenant, contar objetos:
docker exec -it superset-db-1 psql -U superset << 'EOF'
\c company1
SELECT 'company1 dashboards' as source, count(*) FROM dashboards;

\c company2
SELECT 'company2 dashboards' as source, count(*) FROM dashboards;

\c superset
SELECT 'superset dashboards' as source, count(*) FROM dashboards;
EOF
```

✅ **Ideal**:
- `company1` y `company2` tienen sus propios dashboards
- `superset` BD tiene 0 dashboards (o solo metadatos de autenticación)

❌ **Problema**:
- Si `superset` BD tiene dashboards de todos los tenants = NO hay aislamiento

## 🎯 Checklist de Validación

- [ ] Creadas BDs para company1 y company2
- [ ] Reiniciado Superset después de cambios
- [ ] Login con company1 exitoso
- [ ] Dashboard creado en company1
- [ ] Dashboard existe en BD company1 (verificado con SQL)
- [ ] Login con company2 exitoso
- [ ] Dashboard de company1 NO visible en company2
- [ ] Dashboard creado en company2
- [ ] Dashboard existe en BD company2 (verificado con SQL)
- [ ] Ambos dashboards existen en BDs separadas
- [ ] Login con company3 (sin BD) produce error o warning

## 🚀 Próximos Pasos

1. **Ejecutar todas las pruebas anteriores**
2. **Verificar logs**: `docker logs superset_app -f`
3. **Si hay problemas**: Reportar los logs específicos
4. **Si funciona**: Proceder con migración de datos a tenants

## 📝 Notas Importantes

- **Session binding**: El `db.session.bind` se cambia en cada request
- **Scoped session**: Flask-SQLAlchemy usa `scoped_session`, por eso hacemos `remove()` en teardown
- **Thread safety**: Cada request tiene su propia sesión, por eso es thread-safe
- **Performance**: El pool de conexiones es por tenant, así que múltiples users del mismo tenant comparten pool

## 🔒 Validación de Seguridad

### Test de Cross-Tenant Access

Intenta acceder a un dashboard de otro tenant directamente por URL:

```
1. Login como company1
2. Crear dashboard, anotar el ID (ej: 123)
3. Logout, login como company2
4. Intentar acceder: http://localhost:8088/superset/dashboard/123/
```

✅ **Resultado Esperado**: Error 404 o Access Denied (el dashboard no existe en company2)

❌ **Problema de Seguridad**: Si ves el dashboard, hay un leak cross-tenant.
