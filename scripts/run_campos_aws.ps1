# Script para ejecutar scripts de campos contra RDS de AWS
# Uso: .\scripts\run_campos_aws.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ejecutar Scripts de Campos en AWS RDS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si ya existen variables de entorno configuradas
$dbHost = $env:DB_HOST
$dbPort = $env:DB_PORT
$dbName = $env:DB_NAME
$dbUser = $env:DB_USER
$dbPassword = $env:DB_PASSWORD

# Si no están configuradas, solicitar al usuario
if (-not $dbHost -or -not $dbName -or -not $dbUser -or -not $dbPassword) {
    Write-Host "No se encontraron variables de entorno de base de datos configuradas." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Necesitas proporcionar los datos de conexión a tu RDS de AWS:" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $dbHost) {
        $dbHost = Read-Host "Endpoint de RDS (ej: kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com)"
    } else {
        Write-Host "DB_HOST: $dbHost" -ForegroundColor Green
    }
    
    if (-not $dbPort) {
        $dbPort = Read-Host "Puerto (por defecto 5432)"
        if ([string]::IsNullOrWhiteSpace($dbPort)) { $dbPort = "5432" }
    } else {
        Write-Host "DB_PORT: $dbPort" -ForegroundColor Green
    }
    
    if (-not $dbName) {
        $dbName = Read-Host "Nombre de la base de datos (ej: kdi_production)"
    } else {
        Write-Host "DB_NAME: $dbName" -ForegroundColor Green
    }
    
    if (-not $dbUser) {
        $dbUser = Read-Host "Usuario de la base de datos (ej: kdi_admin)"
    } else {
        Write-Host "DB_USER: $dbUser" -ForegroundColor Green
    }
    
    if (-not $dbPassword) {
        $securePassword = Read-Host "Contraseña de la base de datos" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $dbPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    } else {
        Write-Host "DB_PASSWORD: ********" -ForegroundColor Green
    }
    
    Write-Host ""
}

# Establecer variables de entorno para esta sesión
$env:DB_HOST = $dbHost
$env:DB_PORT = $dbPort
$env:DB_NAME = $dbName
$env:DB_USER = $dbUser
$env:DB_PASSWORD = $dbPassword

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Configuración de Conexión:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DB_HOST: $dbHost"
Write-Host "DB_PORT: $dbPort"
Write-Host "DB_NAME: $dbName"
Write-Host "DB_USER: $dbUser"
Write-Host "DB_PASSWORD: ********"
Write-Host ""

# Obtener el directorio del script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

# Mostrar menú de opciones
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Scripts Disponibles:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Actualizar campo desde GeoJSON (update_golf_from_geojson.py)"
Write-Host "2. Actualizar campo desde JSON config (upsert_golf_course_from_config.py)"
Write-Host "3. Eliminar datos de un hoyo (delete_hole_data.py)"
Write-Host "4. Convertir GeoJSON a WKT (convert_geojson_to_wkt.py)"
Write-Host "5. Ejecutar todos los campos disponibles"
Write-Host "0. Salir"
Write-Host ""

$opcion = Read-Host "Selecciona una opción (0-5)"

switch ($opcion) {
    "1" {
        Write-Host ""
        Write-Host "Actualizar campo desde GeoJSON" -ForegroundColor Yellow
        $geojsonFile = Read-Host "Ruta al archivo GeoJSON (ej: data/campos_info/las_rejas.geojson)"
        
        if (-not $geojsonFile) {
            $geojsonFile = "data/campos_info/las_rejas.geojson"
            Write-Host "Usando archivo por defecto: $geojsonFile" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Ejecutando script..." -ForegroundColor Cyan
        python scripts/campos/update_golf_from_geojson.py $geojsonFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ Script ejecutado exitosamente" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Error al ejecutar el script" -ForegroundColor Red
        }
    }
    "2" {
        Write-Host ""
        Write-Host "Actualizar campo desde JSON config" -ForegroundColor Yellow
        $jsonFile = Read-Host "Ruta al archivo JSON (ej: data/campos/las_rejas.json)"
        
        if (-not $jsonFile) {
            Write-Host "Debes especificar un archivo JSON" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "Ejecutando script..." -ForegroundColor Cyan
        python -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from scripts.campos.upsert_golf_course_from_config import upsert_golf_course_from_file; from kdi_back.infrastructure.db.database import init_database; init_database(); upsert_golf_course_from_file(Path('$jsonFile'))"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ Script ejecutado exitosamente" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Error al ejecutar el script" -ForegroundColor Red
        }
    }
    "3" {
        Write-Host ""
        Write-Host "Eliminar datos de un hoyo" -ForegroundColor Yellow
        $holeId = Read-Host "ID del hoyo a eliminar"
        
        if (-not $holeId) {
            Write-Host "Debes especificar un ID de hoyo" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "Ejecutando script..." -ForegroundColor Cyan
        python scripts/campos/delete_hole_data.py $holeId
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ Script ejecutado exitosamente" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Error al ejecutar el script" -ForegroundColor Red
        }
    }
    "4" {
        Write-Host ""
        Write-Host "Convertir GeoJSON a WKT" -ForegroundColor Yellow
        $geojsonFile = Read-Host "Archivo GeoJSON de entrada (ej: data/campos_info/las_rejas.geojson)"
        $jsonFile = Read-Host "Archivo JSON de salida (ej: data/campos/las_rejas.json)"
        
        if (-not $geojsonFile -or -not $jsonFile) {
            Write-Host "Debes especificar archivo de entrada y salida" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "Ejecutando script..." -ForegroundColor Cyan
        python -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from scripts.campos.convert_geojson_to_wkt import convert_geojson_to_wkt_format; convert_geojson_to_wkt_format(Path('$geojsonFile'), Path('$jsonFile'))"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ Conversión completada exitosamente" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Error al ejecutar el script" -ForegroundColor Red
        }
    }
    "5" {
        Write-Host ""
        Write-Host "Ejecutando todos los campos disponibles..." -ForegroundColor Yellow
        
        # Buscar todos los archivos JSON en data/campos
        $camposDir = Join-Path $projectRoot "data\campos"
        if (Test-Path $camposDir) {
            $jsonFiles = Get-ChildItem -Path $camposDir -Filter "*.json"
            
            if ($jsonFiles.Count -eq 0) {
                Write-Host "No se encontraron archivos JSON en data/campos" -ForegroundColor Yellow
                Write-Host "Primero convierte tus archivos GeoJSON a JSON usando la opción 4" -ForegroundColor Yellow
            } else {
                Write-Host "Encontrados $($jsonFiles.Count) archivo(s) JSON:" -ForegroundColor Cyan
                foreach ($file in $jsonFiles) {
                    Write-Host "  - $($file.Name)" -ForegroundColor Cyan
                }
                Write-Host ""
                
                $confirm = Read-Host "¿Deseas procesar todos estos archivos? (s/N)"
                if ($confirm -eq "s" -or $confirm -eq "S") {
                    foreach ($file in $jsonFiles) {
                        Write-Host ""
                        Write-Host "========================================" -ForegroundColor Cyan
                        Write-Host "  Procesando: $($file.Name)" -ForegroundColor Cyan
                        Write-Host "========================================" -ForegroundColor Cyan
                        
                        python -c "import sys; sys.path.insert(0, 'src'); from pathlib import Path; from scripts.campos.upsert_golf_course_from_config import upsert_golf_course_from_file; from kdi_back.infrastructure.db.database import init_database; init_database(); upsert_golf_course_from_file(Path('$($file.FullName)'))"
                        
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "✓ $($file.Name) procesado exitosamente" -ForegroundColor Green
                        } else {
                            Write-Host "✗ Error al procesar $($file.Name)" -ForegroundColor Red
                        }
                    }
                    
                    Write-Host ""
                    Write-Host "✓ Todos los campos procesados" -ForegroundColor Green
                }
            }
        } else {
            Write-Host "No se encontró el directorio data/campos" -ForegroundColor Red
        }
    }
    "0" {
        Write-Host "Saliendo..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Opción no válida" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Proceso completado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

