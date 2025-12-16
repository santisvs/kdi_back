# -*- coding: utf-8 -*-
"""
Script de migración para agregar el campo gender a la tabla player_profile.

Este script puede ejecutarse si la tabla player_profile ya existe y necesita
agregar el campo gender.
"""
try:
    from .database import Database, init_database
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database
import psycopg2


def add_gender_column():
    """
    Agrega el campo gender a la tabla player_profile si no existe.
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la columna ya existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'player_profile' 
                AND column_name = 'gender';
            """)
            
            if cur.fetchone():
                print("✓ La columna 'gender' ya existe en la tabla 'player_profile'")
                return True
            
            print("Agregando columna 'gender' a la tabla 'player_profile'...")
            
            # Agregar la columna con el constraint CHECK
            cur.execute("""
                ALTER TABLE player_profile
                ADD COLUMN gender TEXT CHECK (gender IN ('male', 'female'));
            """)
            
            print("✓ Columna 'gender' agregada exitosamente")
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


if __name__ == '__main__':
    """
    Script para agregar la columna gender a player_profile
    """
    import sys
    
    print("=" * 60)
    print("Migración: Agregar campo gender a player_profile")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=False):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        sys.exit(1)
    
    print("\n→ Agregando columna 'gender'...")
    success = add_gender_column()
    
    if success:
        print("\n✓ Migración completada exitosamente")
    else:
        print("\n✗ Error al agregar la columna")
        sys.exit(1)
    
    print("\n" + "=" * 60)


