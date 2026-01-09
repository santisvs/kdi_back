# -*- coding: utf-8 -*-
"""
Migración para agregar estado persistente del partido a match_player

Agrega el campo current_hole_number para indicar en qué hoyo está jugando actualmente cada jugador.
"""
try:
    from .database import Database, init_database
    from ...infrastructure.config import settings
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database
    from kdi_back.infrastructure.config import settings
import psycopg2


def add_current_hole_number_to_match_player():
    """
    Agrega el campo current_hole_number a la tabla match_player.
    
    Este campo indica en qué hoyo está jugando actualmente cada jugador.
    Se inicializa con el starting_hole_number cuando se crea el jugador.
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la columna ya existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match_player' 
                AND column_name = 'current_hole_number';
            """)
            
            if cur.fetchone():
                print("✓ La columna 'current_hole_number' ya existe en 'match_player'")
                return True
            
            print("Agregando columna 'current_hole_number' a la tabla 'match_player'...")
            
            # Agregar la columna
            cur.execute("""
                ALTER TABLE match_player 
                ADD COLUMN current_hole_number INT;
            """)
            
            # Inicializar el valor con starting_hole_number para registros existentes
            print("Inicializando 'current_hole_number' con 'starting_hole_number' para registros existentes...")
            cur.execute("""
                UPDATE match_player 
                SET current_hole_number = starting_hole_number 
                WHERE current_hole_number IS NULL;
            """)
            
            # Hacer la columna NOT NULL después de inicializar
            cur.execute("""
                ALTER TABLE match_player 
                ALTER COLUMN current_hole_number SET NOT NULL;
            """)
            
            # Agregar valor por defecto para futuros registros
            cur.execute("""
                ALTER TABLE match_player 
                ALTER COLUMN current_hole_number SET DEFAULT 1;
            """)
            
            # Crear índice para mejorar consultas
            print("Creando índice en 'current_hole_number'...")
            cur.execute("""
                CREATE INDEX idx_match_player_current_hole_number 
                ON match_player(current_hole_number);
            """)
            
            print("✓ Columna 'current_hole_number' agregada exitosamente")
            print("\nEstructura actualizada:")
            print("  - current_hole_number: INT NOT NULL DEFAULT 1")
            print("    Indica en qué hoyo está jugando actualmente el jugador")
            print("    Se inicializa con starting_hole_number al crear el jugador")
            
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
    Script para ejecutar la migración desde la línea de comandos
    """
    print("=" * 60)
    print("Migración: Estado Persistente del Partido")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=False):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        print("\nSolución:")
        print("1. Verifica tu configuración en el archivo .env")
        print("2. Asegúrate de que la base de datos existe")
        sys.exit(1)
    
    print("\n→ Ejecutando migración...")
    success = add_current_hole_number_to_match_player()
    
    if success:
        print("\n✓ Migración completada exitosamente")
    else:
        print("\n✗ Error al ejecutar la migración")
        sys.exit(1)
    
    print("\n" + "=" * 60)

