#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script helper para ejecutar scripts de campos contra RDS de AWS.

Este script configura las variables de entorno de conexión a RDS
y ejecuta los scripts de campos con esas configuraciones.

Uso:
    # Opción 1: Ejecutar interactivo (solicita datos de conexión)
    python scripts/run_campos_aws.py
    
    # Opción 2: Pasar datos como argumentos
    python scripts/run_campos_aws.py --host ENDPOINT --port 5432 --db DATABASE --user USER --password PASSWORD
    
    # Opción 3: Usar variables de entorno (si ya están configuradas)
    export DB_HOST=... DB_USER=... DB_PASSWORD=... DB_NAME=... DB_PORT=...
    python scripts/run_campos_aws.py
"""
import os
import sys
import argparse
from pathlib import Path

# Agregar paths necesarios
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
for path_to_add in [str(project_root), str(src_dir)]:
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)


def get_rds_connection_info():
    """
    Obtiene la información de conexión a RDS desde variables de entorno o argumentos.
    """
    parser = argparse.ArgumentParser(
        description='Ejecutar scripts de campos contra RDS de AWS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Modo interactivo (solicita datos)
  python scripts/run_campos_aws.py
  
  # Con argumentos
  python scripts/run_campos_aws.py --host mydb.xxxxx.us-east-1.rds.amazonaws.com \\
                                    --db kdi_production \\
                                    --user kdi_admin \\
                                    --password mypassword
  
  # Con variables de entorno (desde PowerShell)
  $env:DB_HOST="mydb.xxxxx.us-east-1.rds.amazonaws.com"
  $env:DB_NAME="kdi_production"
  $env:DB_USER="kdi_admin"
  $env:DB_PASSWORD="mypassword"
  python scripts/run_campos_aws.py
        """
    )
    
    parser.add_argument('--host', help='Endpoint de RDS (ej: mydb.xxxxx.us-east-1.rds.amazonaws.com)')
    parser.add_argument('--port', help='Puerto (por defecto 5432)', default='5432')
    parser.add_argument('--db', '--database', dest='database', help='Nombre de la base de datos')
    parser.add_argument('--user', help='Usuario de la base de datos')
    parser.add_argument('--password', help='Contraseña de la base de datos')
    parser.add_argument('--script', choices=['update_geojson', 'upsert_json', 'delete_hole', 'convert'], 
                       help='Script específico a ejecutar')
    parser.add_argument('--file', help='Archivo a procesar (depende del script)')
    parser.add_argument('--all', action='store_true', help='Procesar todos los campos disponibles')
    
    args = parser.parse_args()
    
    # Obtener valores desde argumentos, variables de entorno, o solicitar interactivamente
    host = args.host or os.getenv('DB_HOST')
    port = args.port or os.getenv('DB_PORT', '5432')
    database = args.database or os.getenv('DB_NAME')
    user = args.user or os.getenv('DB_USER')
    password = args.password or os.getenv('DB_PASSWORD')
    
    # Si faltan valores, solicitar interactivamente
    if not host:
        host = input("Endpoint de RDS (ej: mydb.xxxxx.us-east-1.rds.amazonaws.com): ").strip()
    if not database:
        database = input("Nombre de la base de datos (ej: kdi_production): ").strip()
    if not user:
        user = input("Usuario de la base de datos (ej: kdi_admin): ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Contraseña de la base de datos: ")
    
    # Establecer variables de entorno
    os.environ['DB_HOST'] = host
    os.environ['DB_PORT'] = port
    os.environ['DB_NAME'] = database
    os.environ['DB_USER'] = user
    os.environ['DB_PASSWORD'] = password
    
    print("=" * 60)
    print("Configuración de Conexión:")
    print("=" * 60)
    print(f"DB_HOST: {host}")
    print(f"DB_PORT: {port}")
    print(f"DB_NAME: {database}")
    print(f"DB_USER: {user}")
    print(f"DB_PASSWORD: {'*' * len(password)}")
    print("=" * 60)
    print()
    
    return {
        'script': args.script,
        'file': args.file,
        'all': args.all
    }


def run_update_geojson(geojson_file):
    """Ejecuta el script update_golf_from_geojson.py"""
    print(f"Ejecutando: update_golf_from_geojson.py {geojson_file}")
    print()
    
    try:
        from scripts.campos.update_golf_from_geojson import main
        # Pasar el archivo como parámetro en lugar de usar sys.argv
        success = main(geojson_file_path=geojson_file)
        return success
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_upsert_json(json_file):
    """Ejecuta upsert_golf_course_from_config.py"""
    print(f"Ejecutando upsert desde: {json_file}")
    print()
    
    try:
        from kdi_back.infrastructure.db.database import init_database
        from scripts.campos.upsert_golf_course_from_config import upsert_golf_course_from_file
        
        if not init_database():
            print("Error: No se pudo inicializar la base de datos")
            return False
        
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"Error: No se encontró el archivo {json_file}")
            return False
        
        upsert_golf_course_from_file(json_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_delete_hole(hole_id):
    """Ejecuta delete_hole_data.py"""
    print(f"Ejecutando: delete_hole_data.py {hole_id}")
    print()
    
    try:
        # Ejecutar como subprocess para mantener el comportamiento original
        import subprocess
        script_path = project_root / "scripts" / "campos" / "delete_hole_data.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(hole_id)],
            cwd=str(project_root),
            env=os.environ.copy()
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_convert_geojson(input_file, output_file):
    """Ejecuta convert_geojson_to_wkt.py"""
    print(f"Convirtiendo: {input_file} -> {output_file}")
    print()
    
    try:
        from scripts.campos.convert_geojson_to_wkt import convert_geojson_to_wkt_format
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            print(f"Error: No se encontró el archivo {input_file}")
            return False
        
        # Crear directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        convert_geojson_to_wkt_format(input_path, output_path)
        print(f"✓ Conversión completada: {output_file}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_campos():
    """Procesa todos los archivos JSON disponibles en data/campos"""
    campos_dir = project_root / "data" / "campos"
    
    if not campos_dir.exists():
        print(f"Error: No se encontró el directorio {campos_dir}")
        return False
    
    json_files = list(campos_dir.glob("*.json"))
    
    if not json_files:
        print(f"No se encontraron archivos JSON en {campos_dir}")
        print("Primero convierte tus archivos GeoJSON a JSON")
        return False
    
    print(f"Encontrados {len(json_files)} archivo(s) JSON:")
    for json_file in json_files:
        print(f"  - {json_file.name}")
    print()
    
    respuesta = input("¿Deseas procesar todos estos archivos? (s/N): ")
    if respuesta.lower() != 's':
        print("Operación cancelada")
        return False
    
    success_count = 0
    for json_file in json_files:
        print()
        print("=" * 60)
        print(f"Procesando: {json_file.name}")
        print("=" * 60)
        
        if run_upsert_json(str(json_file)):
            success_count += 1
            print(f"✓ {json_file.name} procesado exitosamente")
        else:
            print(f"✗ Error al procesar {json_file.name}")
    
    print()
    print(f"Procesados: {success_count}/{len(json_files)} archivos")
    return success_count == len(json_files)


def main():
    """Función principal"""
    print("=" * 60)
    print("  Ejecutar Scripts de Campos en AWS RDS")
    print("=" * 60)
    print()
    
    # Obtener información de conexión
    options = get_rds_connection_info()
    
    # Ejecutar script según opción
    if options['script']:
        if options['script'] == 'update_geojson':
            if not options['file']:
                options['file'] = input("Archivo GeoJSON (ej: data/campos_info/las_rejas.geojson): ").strip()
            success = run_update_geojson(options['file'])
        elif options['script'] == 'upsert_json':
            if not options['file']:
                options['file'] = input("Archivo JSON (ej: data/campos/las_rejas.json): ").strip()
            success = run_upsert_json(options['file'])
        elif options['script'] == 'delete_hole':
            if not options['file']:
                options['file'] = input("ID del hoyo a eliminar: ").strip()
            success = run_delete_hole(options['file'])
        elif options['script'] == 'convert':
            input_file = options['file'] or input("Archivo GeoJSON de entrada: ").strip()
            output_file = input("Archivo JSON de salida: ").strip()
            success = run_convert_geojson(input_file, output_file)
        else:
            success = False
    elif options['all']:
        success = run_all_campos()
    else:
        # Modo interactivo
        print("Scripts disponibles:")
        print("1. Actualizar campo desde GeoJSON")
        print("2. Actualizar campo desde JSON config")
        print("3. Eliminar datos de un hoyo")
        print("4. Convertir GeoJSON a WKT")
        print("5. Procesar todos los campos disponibles")
        print()
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == '1':
            geojson_file = input("Archivo GeoJSON (ej: data/campos_info/las_rejas.geojson): ").strip()
            if not geojson_file:
                geojson_file = "data/campos_info/las_rejas.geojson"
            success = run_update_geojson(geojson_file)
        elif opcion == '2':
            json_file = input("Archivo JSON (ej: data/campos/las_rejas.json): ").strip()
            if not json_file:
                print("Debes especificar un archivo JSON")
                return False
            success = run_upsert_json(json_file)
        elif opcion == '3':
            hole_id = input("ID del hoyo a eliminar: ").strip()
            if not hole_id:
                print("Debes especificar un ID de hoyo")
                return False
            success = run_delete_hole(hole_id)
        elif opcion == '4':
            input_file = input("Archivo GeoJSON de entrada: ").strip()
            output_file = input("Archivo JSON de salida: ").strip()
            if not input_file or not output_file:
                print("Debes especificar archivo de entrada y salida")
                return False
            success = run_convert_geojson(input_file, output_file)
        elif opcion == '5':
            success = run_all_campos()
        else:
            print("Opción no válida")
            return False
    
    print()
    print("=" * 60)
    if success:
        print("✓ Proceso completado exitosamente")
    else:
        print("✗ El proceso terminó con errores")
    print("=" * 60)
    
    return success


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

