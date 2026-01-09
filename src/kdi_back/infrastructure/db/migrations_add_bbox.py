# -*- coding: utf-8 -*-
"""
Migración para agregar la columna bbox_polygon a la tabla hole.

Esta migración agrega:
- Columna bbox_polygon GEOGRAPHY(Polygon, 4326) a la tabla hole
- Índice GIST para optimizar consultas espaciales con bbox_polygon
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


def add_bbox_polygon_to_hole():
    """
    Agrega la columna bbox_polygon a la tabla hole si no existe.
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la columna ya existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole' 
                    AND column_name = 'bbox_polygon'
                );
            """)
            exists = cur.fetchone()['exists']
            
            if exists:
                print("✓ La columna 'bbox_polygon' ya existe en la tabla 'hole'")
                return True
            
            print("Agregando columna 'bbox_polygon' a la tabla 'hole'...")
            cur.execute("""
                ALTER TABLE hole 
                ADD COLUMN bbox_polygon GEOGRAPHY(Polygon, 4326);
            """)
            
            print("Creando índice espacial en 'bbox_polygon'...")
            cur.execute("""
                CREATE INDEX idx_hole_bbox_polygon 
                ON hole USING GIST(bbox_polygon);
            """)
            
            print("✓ Columna 'bbox_polygon' agregada exitosamente")
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
    import sys
    
    print("=" * 60)
    print("Migración: Agregar bbox_polygon a tabla hole")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=True):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        sys.exit(1)
    
    print("\n→ Ejecutando migración...")
    success = add_bbox_polygon_to_hole()
    
    if success:
        print("\n✓ Migración completada exitosamente")
    else:
        print("\n✗ Error al ejecutar la migración")
        sys.exit(1)
    
    print("\n" + "=" * 60)


