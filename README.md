# KDI Back - Sistema de Recomendaciones de Golf con Agentes IA

Servicio en Python 3 con Flask que expone endpoints para consultas del clima y recomendaciones de golf usando AWS Bedrock.

## Estructura del Proyecto

El proyecto sigue una arquitectura hexagonal/clean architecture:

```
kdi_back/
├── src/kdi_back/          # Código fuente principal
│   ├── api/                # Capa de entrada HTTP
│   │   ├── main.py         # Aplicación Flask
│   │   └── routes/         # Endpoints (health, weather, golf)
│   ├── domain/             # Lógica de negocio
│   │   ├── models/         # Entidades del dominio
│   │   ├── services/       # Casos de uso
│   │   └── ports/          # Interfaces
│   ├── infrastructure/     # Implementaciones técnicas
│   │   ├── db/             # Base de datos (PostgreSQL/PostGIS)
│   │   ├── agents/         # Agentes IA (Bedrock/Strands)
│   │   └── config/         # Configuración
│   └── common/             # Utilidades compartidas
├── tests/                  # Tests (unit, integration, e2e)
├── scripts/                # Scripts de utilidad
├── data/                   # Datos de configuración
│   ├── campos/             # JSONs con WKT (generados)
│   └── campos_info/        # JSONs con lat/lon (editables)
└── pyproject.toml          # Configuración del proyecto
```

## Requisitos

- Python 3.8 o superior
- Credenciales de AWS configuradas en un archivo `.env`
- PostgreSQL con extensión PostGIS instalada

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

O usando el proyecto como paquete:
```bash
pip install -e .
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-east-1

# Configuración de AWS Bedrock Knowledge Base (opcional)
# IMPORTANTE: La Knowledge Base se encuentra en la región eu-south-2
AWS_KNOWLEDGE_BASE_ID=tu_knowledge_base_id
AWS_KNOWLEDGE_BASE_REGION=eu-south-2  # Por defecto es eu-south-2, pero puede configurarse si es diferente

# Configuración de PostgreSQL/PostGIS
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_kdi_test
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
```

### Instalación de PostGIS

**Opción 1: Instalación automática (recomendado)**

Ejecuta desde Python:
```python
from kdi_back.infrastructure.db.database import install_postgis
install_postgis()
```

**Opción 2: Instalación manual**

```sql
-- Conectarse a tu base de datos
\c db_kdi_test

-- Crear la extensión PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verificar la instalación
SELECT PostGIS_version();
```

## Ejecución

### Modo Desarrollo

**Opción 1: Usando el script de desarrollo (recomendado)**
```bash
python scripts/run_dev.py
```

**Opción 2: Ejecutar directamente**
```bash
python -m kdi_back.api.main
```

**Opción 3: Desde la raíz del proyecto**
```bash
cd src
python -m kdi_back.api.main
```

El servicio estará disponible en: `http://localhost:5000`

## Endpoints

### GET /hola-mundo
Responde con "adios mundo"

**Ejemplo de respuesta:**
```json
{
  "mensaje": "adios mundo"
}
```

### GET /health
Endpoint de salud para verificar que el servicio está corriendo

**Ejemplo de respuesta:**
```json
{
  "status": "ok"
}
```

### POST /weather
Endpoint para consultar información del clima usando el agente de Bedrock

**Ejemplo de petición:**
```bash
curl -X POST http://localhost:5000/weather \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué tiempo hace en Madrid?"}'
```

**Ejemplo de respuesta:**
```json
{
  "query": "¿Qué tiempo hace en Madrid?",
  "response": "La respuesta del agente de clima..."
}
```

### GET /weather
Endpoint para consultar información del clima usando parámetros de URL

**Ejemplo de petición:**
```bash
curl "http://localhost:5000/weather?query=¿Qué tiempo hace en Madrid?"
```

### POST /golf
Endpoint para obtener recomendaciones de palo de golf basadas en GPS y situación

**Ejemplo de petición:**
```bash
curl -X POST http://localhost:5000/golf \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.4168,
    "longitude": -3.7038,
    "query": "Estoy a 150 metros del hoyo, hay viento en contra y estoy en el rough"
  }'
```

**Ejemplo de respuesta:**
```json
{
  "recommendation": "Te recomiendo utilizar el hierro siete intentando botar la bola en green, con el objetivo de hacer 150 metros"
}
```

## Base de Datos PostgreSQL/PostGIS

### Sistema de Migraciones

El proyecto incluye un sistema de migraciones para crear y gestionar las tablas de la base de datos.

#### Crear todas las tablas
```bash
python -m kdi_back.infrastructure.db.migrations create_all
```

#### Recrear todas las tablas (elimina y vuelve a crear)
```bash
python -m kdi_back.infrastructure.db.migrations recreate_all
```

#### Verificar tablas
```bash
python -m kdi_back.infrastructure.db.migrations verify_all
```

#### Eliminar todas las tablas
```bash
python -m kdi_back.infrastructure.db.migrations drop_all
```

### Importar Campos de Golf

1. **Crear fichero de info** en `data/campos_info/` con formato lat/lon:
```json
{
  "name": "Mi Campo",
  "location": { "lat": 40.44, "lon": -3.87 },
  "holes": [...]
}
```

2. **Generar JSON con WKT**:
```bash
python scripts/generate_golf_config_from_info.py data/campos_info/mi_campo_info.json data/campos/mi_campo.json
```

3. **Importar en la base de datos**:
```bash
python -m kdi_back.infrastructure.db.seeders.import_golf_course_from_config data/campos/mi_campo.json
```

## Desarrollo

### Estructura de Código

- **API Layer** (`src/kdi_back/api/`): Maneja HTTP, validación, serialización
- **Domain Layer** (`src/kdi_back/domain/`): Lógica de negocio pura
- **Infrastructure Layer** (`src/kdi_back/infrastructure/`): Implementaciones técnicas (DB, AWS, etc.)
- **Agents** (`src/kdi_back/agents/`): Orquestación de agentes IA

### Tests

```bash
# Ejecutar todos los tests
pytest

# Tests unitarios
pytest tests/unit

# Tests de integración
pytest tests/integration

# Tests E2E
pytest tests/e2e
```

## Scripts Útiles

- `scripts/run_dev.py`: Ejecutar servidor en modo desarrollo
- `scripts/generate_golf_config_from_info.py`: Generar JSONs con WKT desde info

## Notas

- La base de datos por defecto es `db_kdi_test`. Puedes cambiarla en el archivo `.env` o en `src/kdi_back/infrastructure/config/settings.py`.
- Los datos de configuración de campos (`data/campos/` y `data/campos_info/`) están fuera de `src/` porque son datos, no código.


## Info adicional
topografia las matas
https://es-es.topographic-map.com/map-dgdm2/Majadahonda/?center=40.54727%2C-3.91623&zoom=18&
base=5&popup=40.54715%2C-3.91705
topografia las rejas
https://es-es.topographic-map.com/map-ml9gp/Torrelodones/?center=40.44459%2C-3.87058&zoom=18&
popup=40.44452%2C-3.86842
info las rejas
https://fedgolfmadrid.com/club/CM22
Diseño
https://chatgpt.com/c/693ab5ed-df04-8325-bde8-de459d690a15
https://geojson.io/#new&map=18.09/40.444619/-3.871407
