# Configuración de SQL Server para Superset

## 📋 Requisitos

Para conectar Superset a Microsoft SQL Server necesitas instalar uno de estos drivers:

### Opción 1: pyodbc (Recomendado)
```bash
# En el host (si usas instalación local)
pip install pyodbc

# En Docker (agregar a requirements)
echo "pyodbc>=4.0.39" >> requirements/local.txt
```

### Opción 2: pymssql (Alternativa)
```bash
# En el host
pip install pymssql

# En Docker
echo "pymssql>=2.2.8" >> requirements/local.txt
```

## 🔧 Instalación en Docker

1. **Editar `requirements/local.txt`** (crear si no existe):
```bash
cat >> requirements/local.txt << 'EOF'
# SQL Server drivers
pyodbc>=4.0.39
EOF
```

2. **Reconstruir la imagen Docker**:
```bash
docker compose down
docker compose build --no-cache superset
docker compose up -d
```

## 🔗 Connection Strings (SQLAlchemy)

### Con pyodbc (Autenticación SQL Server)
```python
# Formato básico
mssql+pyodbc://username:password@hostname:port/database?driver=ODBC+Driver+17+for+SQL+Server

# Ejemplos reales:
# SQL Server local
mssql+pyodbc://sa:MyP@ssw0rd@localhost:1433/mydatabase?driver=ODBC+Driver+17+for+SQL+Server

# SQL Server remoto
mssql+pyodbc://dbuser:SecurePass123@192.168.1.100:1433/sales_db?driver=ODBC+Driver+17+for+SQL+Server

# Con nombre de servidor
mssql+pyodbc://username:password@SERVERNAME\\INSTANCENAME/database?driver=ODBC+Driver+17+for+SQL+Server
```

### Con pyodbc (Autenticación de Windows)
```python
# Windows Authentication
mssql+pyodbc://hostname:port/database?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

### Con pymssql
```python
# Formato básico
mssql+pymssql://username:password@hostname:port/database

# Ejemplo:
mssql+pymssql://sa:MyP@ssw0rd@localhost:1433/mydatabase
```

## 🐳 Drivers ODBC en Docker

Si usas `pyodbc`, necesitas que el contenedor tenga instalado el driver ODBC de Microsoft.

### Opción A: Usar imagen base con drivers

Modifica el `Dockerfile` para incluir:

```dockerfile
# Instalar Microsoft ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

### Opción B: Usar pymssql (No requiere drivers adicionales)

Es más simple porque no necesita drivers ODBC instalados en el sistema.

## 📝 Ejemplo de Configuración en Superset UI

1. Ve a **Data** → **Databases** → **+ Database**
2. Selecciona **Microsoft SQL Server**
3. Ingresa los datos:

**Configuración básica:**
```
Host: 192.168.1.100
Port: 1433
Database: sales_db
Username: dbuser
Password: SecurePass123
```

**Connection String avanzada:**
```
mssql+pyodbc://dbuser:SecurePass123@192.168.1.100:1433/sales_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

## 🔐 Parámetros Adicionales del Connection String

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `driver` | Driver ODBC a usar | `ODBC+Driver+17+for+SQL+Server` |
| `TrustServerCertificate` | Confiar en certificados SSL autofirmados | `yes` / `no` |
| `Encrypt` | Forzar encriptación | `yes` / `no` |
| `trusted_connection` | Windows Authentication | `yes` |
| `autocommit` | Auto commit de transacciones | `True` / `False` |
| `ApplicationName` | Nombre de aplicación en logs | `Superset` |
| `MultipleActiveResultSets` | Soporte MARS | `True` / `False` |

### Connection String con múltiples parámetros:
```python
mssql+pyodbc://user:pass@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes&ApplicationName=Superset
```

## ✅ Verificar Instalación

### Verificar si pyodbc está instalado:
```bash
docker compose exec superset python -c "import pyodbc; print('pyodbc version:', pyodbc.version)"
```

### Verificar drivers ODBC disponibles:
```bash
docker compose exec superset odbcinst -q -d
```

### Probar conexión desde Python:
```bash
docker compose exec superset python << 'EOF'
import pyodbc
# Lista drivers disponibles
print("Drivers ODBC instalados:")
for driver in pyodbc.drivers():
    print(f"  - {driver}")
EOF
```

## 🚨 Troubleshooting

### Error: "Can't open lib 'ODBC Driver 17 for SQL Server'"
**Solución**: Instalar el driver ODBC en el contenedor (ver sección anterior)

### Error: "Login failed for user"
**Solución**: Verificar usuario/contraseña y permisos en SQL Server

### Error: "Unable to connect: Adaptive Server is unavailable"
**Solución**: 
- Verificar que SQL Server esté corriendo
- Verificar firewall (puerto 1433)
- Verificar que SQL Server acepte conexiones TCP/IP

### Error: "SSL Security error"
**Solución**: Agregar `TrustServerCertificate=yes` al connection string

## 📦 Instalación Rápida (Docker)

Si quieres instalar pyodbc rápidamente sin reconstruir:

```bash
# Instalar en el contenedor corriendo
docker compose exec superset pip install pyodbc

# Reiniciar Superset
docker compose restart superset
```

**Nota**: Esta instalación se perderá al recrear el contenedor. Para hacerla permanente, agrégala a `requirements/local.txt`.

## 🔍 Connection String para diferentes escenarios

### SQL Server en Azure
```python
mssql+pyodbc://username@servername:password@servername.database.windows.net:1433/databasename?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

### SQL Server Express (instancia nombrada)
```python
mssql+pyodbc://sa:password@localhost\\SQLEXPRESS/database?driver=ODBC+Driver+17+for+SQL+Server
```

### SQL Server con IP y puerto no estándar
```python
mssql+pyodbc://user:pass@10.0.0.50:14330/mydb?driver=ODBC+Driver+17+for+SQL+Server
```

---

**Última actualización**: Enero 2026
