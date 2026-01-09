#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para probar la conexión a RDS de AWS.

Uso:
    # Con variables de entorno
    $env:DB_HOST="endpoint.rds.amazonaws.com"
    $env:DB_NAME="kdi_production"
    $env:DB_USER="kdi_admin"
    $env:DB_PASSWORD="password"
    python scripts/test_rds_connection.py
    
    # O pasando argumentos
    python scripts/test_rds_connection.py --host endpoint.rds.amazonaws.com --db kdi_production --user kdi_admin --password password
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


def main():
    parser = argparse.ArgumentParser(description='Probar conexión a RDS de AWS')
    parser.add_argument('--host', help='Endpoint de RDS')
    parser.add_argument('--port', help='Puerto (por defecto 5432)', default='5432')
    parser.add_argument('--db', '--database', dest='database', help='Nombre de la base de datos')
    parser.add_argument('--user', help='Usuario de la base de datos')
    parser.add_argument('--password', help='Contraseña de la base de datos')
    
    args = parser.parse_args()
    
    # Obtener valores desde argumentos o variables de entorno
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
    print("Probando conexión a RDS...")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print("=" * 60)
    print()
    
    try:
        from kdi_back.infrastructure.db.database import init_database, test_connection, check_postgis
        
        if not init_database():
            print("✗ Error: No se pudo inicializar la conexión")
            return False
        
        if not test_connection():
            print("✗ Error: La prueba de conexión falló")
            return False
        
        postgis_version = check_postgis()
        if postgis_version:
            print(f"✓ PostGIS instalado: {postgis_version}")
        else:
            print("⚠ Advertencia: PostGIS no está instalado en la base de datos")
            print("  Ejecuta: python scripts/setup_rds_postgis.py")
        
        print()
        print("=" * 60)
        print("✓ Conexión exitosa a RDS")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


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

