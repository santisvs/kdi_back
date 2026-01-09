#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para configurar PostGIS en una instancia RDS PostgreSQL
Ejecuta este script después de crear la instancia RDS
"""
import psycopg2
import sys
from kdi_back.infrastructure.config import settings

def setup_postgis():
    """Instala PostGIS en la base de datos RDS"""
    try:
        print("=" * 50)
        print("Configurando PostGIS en RDS...")
        print("=" * 50)
        print(f"Conectando a: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Instalar PostGIS
        print("\nInstalando extensión PostGIS...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        print("✓ PostGIS instalado correctamente")
        
        # Verificar instalación
        print("\nVerificando instalación...")
        cursor.execute("SELECT PostGIS_version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostGIS versión: {version}")
        
        # Verificar otras extensiones útiles
        print("\nVerificando extensiones disponibles...")
        cursor.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname LIKE 'postgis%';
        """)
        extensions = cursor.fetchall()
        print("Extensiones PostGIS instaladas:")
        for ext_name, ext_version in extensions:
            print(f"  - {ext_name}: {ext_version}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✓ Configuración completada exitosamente")
        print("=" * 50)
        
    except psycopg2.Error as e:
        print(f"\n✗ Error al conectar a la base de datos: {e}")
        print("\nVerifica:")
        print("  1. Que la instancia RDS esté creada y disponible")
        print("  2. Que el security group permita conexiones desde tu IP")
        print("  3. Que las credenciales en .env sean correctas")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_postgis()

