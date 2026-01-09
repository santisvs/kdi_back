#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para ejecutar todas las migraciones de la base de datos en el orden correcto.

Orden de ejecución:
1. migrations_player.py - Crea tablas de jugadores (user, player_profile, golf_club, player_club_statistics)
2. migrations_auth.py - Crea tablas de autenticación (modifica user, crea auth_tokens)
3. migrations.py - Crea tablas de golf (golf_course, hole, hole_point, obstacle, optimal_shot, strategic_point)
4. migrations_match.py - Crea tablas de partidos (match, match_player, match_hole_score, match_stroke)
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from kdi_back.infrastructure.db.database import init_database, install_postgis
from kdi_back.infrastructure.db import migrations_player
from kdi_back.infrastructure.db import migrations_auth
from kdi_back.infrastructure.db import migrations
from kdi_back.infrastructure.db import migrations_match
from kdi_back.infrastructure.config import settings


def run_all_migrations(recreate=False):
    """
    Ejecuta todas las migraciones en el orden correcto.
    
    Args:
        recreate: Si es True, elimina y recrea todas las tablas
    """
    print("=" * 70)
    print("EJECUTANDO TODAS LAS MIGRACIONES DE LA BASE DE DATOS")
    print("=" * 70)
    print(f"\nBase de datos: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 70)
    
    # Inicializar conexión a la base de datos
    print("\n→ Inicializando conexión a la base de datos...")
    if not init_database(install_postgis_if_missing=True):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        print("\nSolución:")
        print("1. Verifica tu configuración en el archivo .env")
        print("2. Asegúrate de que la base de datos existe")
        print(f"   CREATE DATABASE {settings.DB_NAME};")
        return False
    
    print("✓ Conexión establecida")
    
    # Paso 1: Migraciones de jugadores (debe ser primero porque crea la tabla 'user')
    print("\n" + "=" * 70)
    print("PASO 1: Migraciones de Jugadores")
    print("=" * 70)
    print("Creando: user, player_profile, golf_club, player_club_statistics")
    if not migrations_player.create_all_player_tables(recreate=recreate):
        print("\n✗ Error al crear las tablas de jugadores")
        return False
    print("✓ Tablas de jugadores creadas correctamente")
    
    # Paso 2: Migraciones de autenticación (modifica 'user' y crea 'auth_tokens')
    print("\n" + "=" * 70)
    print("PASO 2: Migraciones de Autenticación")
    print("=" * 70)
    print("Modificando: user (agregando columnas de auth)")
    print("Creando: auth_tokens")
    if not migrations_auth.create_all_auth_tables(recreate=recreate):
        print("\n✗ Error al crear las tablas de autenticación")
        return False
    print("✓ Tablas de autenticación creadas correctamente")
    
    # Paso 3: Migraciones de golf
    print("\n" + "=" * 70)
    print("PASO 3: Migraciones de Golf")
    print("=" * 70)
    print("Creando: golf_course, hole, hole_point, obstacle, optimal_shot, strategic_point")
    if not migrations.create_all_golf_tables(recreate=recreate):
        print("\n✗ Error al crear las tablas de golf")
        return False
    print("✓ Tablas de golf creadas correctamente")
    
    # Paso 4: Migraciones de partidos (depende de 'user' y 'golf_course')
    print("\n" + "=" * 70)
    print("PASO 4: Migraciones de Partidos")
    print("=" * 70)
    print("Creando: match, match_player, match_hole_score, match_stroke")
    if not migrations_match.create_all_match_tables(recreate=recreate):
        print("\n✗ Error al crear las tablas de partidos")
        return False
    print("✓ Tablas de partidos creadas correctamente")
    
    print("\n" + "=" * 70)
    print("✓ TODAS LAS MIGRACIONES COMPLETADAS EXITOSAMENTE")
    print("=" * 70)
    print("\nTablas creadas:")
    print("  ✓ user")
    print("  ✓ player_profile")
    print("  ✓ golf_club")
    print("  ✓ player_club_statistics")
    print("  ✓ auth_tokens")
    print("  ✓ golf_course")
    print("  ✓ hole")
    print("  ✓ hole_point")
    print("  ✓ obstacle")
    print("  ✓ optimal_shot")
    print("  ✓ strategic_point")
    print("  ✓ match")
    print("  ✓ match_player")
    print("  ✓ match_hole_score")
    print("  ✓ match_stroke")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ejecuta todas las migraciones de la base de datos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_all_migrations.py          # Crea todas las tablas (si no existen)
  python run_all_migrations.py --recreate  # Elimina y recrea todas las tablas
        """
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Elimina y recrea todas las tablas (CUIDADO: elimina todos los datos)'
    )
    
    args = parser.parse_args()
    
    if args.recreate:
        confirm = input("\n⚠️  ADVERTENCIA: Esto eliminará TODAS las tablas y datos. ¿Continuar? (s/N): ")
        if confirm.lower() != 's':
            print("Operación cancelada")
            sys.exit(0)
    
    success = run_all_migrations(recreate=args.recreate)
    
    if not success:
        print("\n✗ Hubo errores durante la ejecución de las migraciones")
        sys.exit(1)
    
    print("\n✓ Proceso completado exitosamente")

