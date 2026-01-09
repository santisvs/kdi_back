# Guía: Importar Campos de Golf a RDS de AWS

Esta guía te explica cómo ejecutar los scripts de campos contra tu base de datos RDS de AWS.

## Prerrequisitos

1. **RDS configurado y disponible** en AWS
2. **Security Group configurado** para permitir conexiones desde tu IP
3. **PostGIS instalado** en RDS (ver `DESPLIEGUE_AWS.md`)
4. **Migraciones ejecutadas** en la base de datos

## Opción 1: Script PowerShell (Windows) - Recomendado

### Paso 1: Ejecutar el script

```powershell
cd C:\Users\Usuario\Desarrollo\kdi_back
.\scripts\run_campos_aws.ps1
```

### Paso 2: Proporcionar datos de conexión

El script te pedirá:
- **Endpoint de RDS**: Ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`
- **Puerto**: `5432` (por defecto)
- **Nombre de la base de datos**: Ej: `kdi_production`
- **Usuario**: Ej: `kdi_admin`
- **Contraseña**: Tu contraseña de RDS

### Paso 3: Seleccionar acción

El script mostrará un menú con opciones:
1. Actualizar campo desde GeoJSON
2. Actualizar campo desde JSON config
3. Eliminar datos de un hoyo
4. Convertir GeoJSON a WKT
5. Ejecutar todos los campos disponibles

## Opción 2: Script Python (Multiplataforma)

### Paso 1: Modo interactivo

```powershell
cd C:\Users\Usuario\Desarrollo\kdi_back
python scripts/run_campos_aws.py
```

El script te solicitará los datos de conexión y mostrará un menú de opciones.

### Paso 2: Con argumentos

```powershell
python scripts/run_campos_aws.py `
    --host kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com `
    --port 5432 `
    --db kdi_production `
    --user kdi_admin `
    --password tu_contraseña `
    --script upsert_json `
    --file data/campos/las_rejas.json
```

### Paso 3: Con variables de entorno

```powershell
$env:DB_HOST="kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com"
$env:DB_PORT="5432"
$env:DB_NAME="kdi_production"
$env:DB_USER="kdi_admin"
$env:DB_PASSWORD="tu_contraseña"

python scripts/run_campos_aws.py --script upsert_json --file data/campos/las_rejas.json
```

## Opción 3: Ejecutar scripts directamente con variables de entorno

Si prefieres ejecutar los scripts directamente sin el helper:

### Paso 1: Configurar variables de entorno

**PowerShell:**
```powershell
$env:DB_HOST="kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com"
$env:DB_PORT="5432"
$env:DB_NAME="kdi_production"
$env:DB_USER="kdi_admin"
$env:DB_PASSWORD="tu_contraseña"
```

**Bash (Linux/Mac/Git Bash):**
```bash
export DB_HOST="kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com"
export DB_PORT="5432"
export DB_NAME="kdi_production"
export DB_USER="kdi_admin"
export DB_PASSWORD="tu_contraseña"
```

### Paso 2: Ejecutar scripts

```powershell
# Actualizar desde GeoJSON
python scripts/campos/update_golf_from_geojson.py data/campos_info/las_rejas.geojson

# Actualizar desde JSON (directo)
python -c "from pathlib import Path; from scripts.campos.upsert_golf_course_from_config import upsert_golf_course_from_file; from kdi_back.infrastructure.db.database import init_database; init_database(); upsert_golf_course_from_file(Path('data/campos/las_rejas.json'))"
```

## Obtener Datos de Conexión de RDS

### Endpoint de RDS

1. Ve a la consola de AWS → **RDS** → **Databases**
2. Selecciona tu instancia
3. En **Connectivity & security**, copia el **Endpoint**
   - Ejemplo: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`
   - ⚠️ **NO uses el nombre de la instancia**, usa el endpoint completo

### Nombre de la Base de Datos

1. En la misma página de RDS
2. Ve a la pestaña **Configuration**
3. Busca **DB name** o **Database name**
   - Ejemplo: `kdi_production`
   - Si no aparece, puede ser `postgres` (base de datos por defecto)

### Usuario y Contraseña

- Son los que configuraste al crear la instancia RDS
- Si no los recuerdas, tendrás que resetear la contraseña desde la consola de AWS

## Ejemplos de Uso

### Ejemplo 1: Procesar un campo desde GeoJSON

```powershell
# Con script helper
python scripts/run_campos_aws.py `
    --host tu-endpoint.rds.amazonaws.com `
    --db kdi_production `
    --user kdi_admin `
    --password tu_password `
    --script update_geojson `
    --file data/campos_info/las_rejas.geojson
```

### Ejemplo 2: Procesar un campo desde JSON

```powershell
python scripts/run_campos_aws.py `
    --host tu-endpoint.rds.amazonaws.com `
    --db kdi_production `
    --user kdi_admin `
    --password tu_password `
    --script upsert_json `
    --file data/campos/las_rejas.json
```

### Ejemplo 3: Procesar todos los campos disponibles

```powershell
python scripts/run_campos_aws.py `
    --host tu-endpoint.rds.amazonaws.com `
    --db kdi_production `
    --user kdi_admin `
    --password tu_password `
    --all
```

### Ejemplo 4: Convertir GeoJSON a JSON con WKT

```powershell
python scripts/run_campos_aws.py `
    --script convert `
    --file data/campos_info/las_rejas.geojson
# Luego te pedirá el archivo de salida
```

## Solución de Problemas

### Error: "No se pudo conectar a la base de datos"

1. **Verifica el Security Group**:
   - Ve a EC2 → Security Groups
   - Encuentra el security group de tu RDS
   - Asegúrate de que permite conexiones desde tu IP en el puerto 5432

2. **Verifica el endpoint**:
   - Asegúrate de usar el endpoint completo, no solo el nombre de la instancia

3. **Verifica las credenciales**:
   - Usuario y contraseña deben ser correctos
   - El usuario debe tener permisos en la base de datos

### Error: "PostGIS no está instalado"

Ejecuta el script de instalación de PostGIS:

```powershell
python scripts/setup_rds_postgis.py
```

Asegúrate de tener las variables de entorno configuradas antes de ejecutarlo.

### Error: "No se encontró el archivo"

- Verifica que estás en el directorio raíz del proyecto
- Verifica que los archivos existen en `data/campos/` o `data/campos_info/`
- Usa rutas relativas desde la raíz del proyecto

## Archivos de Campos

Los scripts trabajan con archivos en:

- **`data/campos_info/`**: Archivos GeoJSON editables
  - Ejemplo: `las_rejas.geojson`

- **`data/campos/`**: Archivos JSON con WKT (generados)
  - Ejemplo: `las_rejas.json`

Para crear un nuevo campo:

1. Crea un archivo GeoJSON en `data/campos_info/`
2. Conviértelo a JSON con WKT usando el script de conversión
3. Importa a la base de datos usando el script de upsert

## Notas Importantes

⚠️ **Seguridad**:
- No compartas tus credenciales de RDS
- No commitees archivos `.env` con contraseñas
- Usa variables de entorno o archivos de configuración seguros

⚠️ **Backups**:
- Antes de importar datos, considera hacer un backup de tu base de datos
- Puedes usar `pg_dump` o las herramientas de backup de AWS RDS

⚠️ **Permisos**:
- El usuario de RDS debe tener permisos para:
  - INSERT, UPDATE, DELETE en las tablas
  - CREATE, ALTER en extensiones (si es necesario)

