#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

set -e

# Script para crear bases de datos de tenants en PostgreSQL

TENANT=$1
CONTAINER_NAME=${2:-"superset-db-1"}
DB_USER=${3:-"superset"}

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función de ayuda
usage() {
    echo "Uso: $0 <nombre_tenant> [container_name] [db_user]"
    echo ""
    echo "Argumentos:"
    echo "  nombre_tenant    Nombre del tenant (requerido)"
    echo "  container_name   Nombre del contenedor PostgreSQL (default: superset-db-1)"
    echo "  db_user          Usuario de base de datos (default: superset)"
    echo ""
    echo "Ejemplo:"
    echo "  $0 acme"
    echo "  $0 demo superset-db-1 superset"
    exit 1
}

# Validar argumentos
if [ -z "$TENANT" ]; then
    echo -e "${RED}Error: Nombre del tenant es requerido${NC}"
    usage
fi

# Validar nombre del tenant (solo alfanuméricos y guión bajo)
if ! [[ "$TENANT" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo -e "${RED}Error: Nombre del tenant solo puede contener letras, números y guión bajo${NC}"
    exit 1
fi

# Validar que no sea un nombre de BD del sistema
RESERVED_NAMES=("postgres" "template0" "template1" "superset")
for reserved in "${RESERVED_NAMES[@]}"; do
    if [ "$TENANT" = "$reserved" ]; then
        echo -e "${RED}Error: '$TENANT' es un nombre reservado del sistema${NC}"
        exit 1
    fi
done

echo -e "${YELLOW}Creando base de datos para tenant: $TENANT${NC}"

# Verificar que el contenedor existe
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Contenedor '$CONTAINER_NAME' no encontrado o no está corriendo${NC}"
    echo "Contenedores disponibles:"
    docker ps --format "  - {{.Names}}"
    exit 1
fi

# Verificar si la base de datos ya existe
DB_EXISTS=$(docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$TENANT'")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}Base de datos '$TENANT' ya existe${NC}"
    read -p "¿Deseas recrearla? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}Eliminando base de datos existente...${NC}"
        docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -c "DROP DATABASE $TENANT;" || {
            echo -e "${RED}Error al eliminar la base de datos${NC}"
            exit 1
        }
    else
        echo -e "${GREEN}Operación cancelada${NC}"
        exit 0
    fi
fi

# Crear la base de datos
echo -e "${YELLOW}Creando base de datos...${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $TENANT;" || {
    echo -e "${RED}Error al crear la base de datos${NC}"
    exit 1
}

# Otorgar privilegios
echo -e "${YELLOW}Otorgando privilegios...${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -c "GRANT ALL PRIVILEGES ON DATABASE $TENANT TO $DB_USER;" || {
    echo -e "${RED}Error al otorgar privilegios${NC}"
    exit 1
}

# Verificar creación
echo -e "${YELLOW}Verificando base de datos...${NC}"
DB_CHECK=$(docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$TENANT'")

if [ "$DB_CHECK" = "1" ]; then
    echo -e "${GREEN}✓ Base de datos '$TENANT' creada exitosamente${NC}"
    echo ""
    echo "Información de conexión:"
    echo "  - Base de datos: $TENANT"
    echo "  - Usuario: $DB_USER"
    echo "  - Host: db (interno) / localhost:5432 (externo)"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Inicia sesión con tenant='$TENANT' en Superset"
    echo "  2. El sistema se conectará automáticamente a esta base de datos"
    echo ""
    echo -e "${YELLOW}Nota:${NC} Esta base de datos está vacía. Si necesitas las tablas de metadatos"
    echo "de Superset, ejecuta las migraciones o copia el esquema desde otra BD."
else
    echo -e "${RED}✗ Error: No se pudo verificar la creación de la base de datos${NC}"
    exit 1
fi
