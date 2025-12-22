# -*- coding: utf-8 -*-
"""
Sistema de migraciones para la base de datos PostgreSQL/PostGIS

Este módulo permite crear y recrear tablas de forma controlada.

Tablas gestionadas:
- golf_course
- hole
- hole_point
- obstacle
- optimal_shot
"""
try:
    from .database import Database, init_database, install_postgis, check_postgis
    from ...infrastructure.config import settings
except ImportError:
    # Si se ejecuta directamente como script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database, install_postgis, check_postgis
    from kdi_back.infrastructure.config import settings
import psycopg2


def create_golf_course_table(drop_if_exists=False):
    """
    Crea la tabla golf_course en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Eliminar la tabla si existe y se solicita
            if drop_if_exists:
                print("Eliminando tabla 'golf_course' si existe...")
                cur.execute("DROP TABLE IF EXISTS golf_course CASCADE;")
                print("Tabla eliminada (si existía)")
            
            # Verificar que PostGIS esté disponible
            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    print("Por favor, instálalo manualmente ejecutando:")
                    print("  python -c \"from database import install_postgis; install_postgis()\"")
                    print("\nO en PostgreSQL:")
                    print("  CREATE EXTENSION IF NOT EXISTS postgis;")
                    return False
                postgis_version = check_postgis()
            
            print(f"✓ PostGIS disponible: versión {postgis_version}")
            
            # Crear la tabla golf_course
            print("Creando tabla 'golf_course'...")
            cur.execute("""
                CREATE TABLE golf_course (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    location GEOGRAPHY(Point, 4326)
                );
            """)
            
            # Crear índice espacial para optimizar consultas geoespaciales
            print("Creando índice espacial en 'location'...")
            cur.execute("""
                CREATE INDEX idx_golf_course_location 
                ON golf_course USING GIST(location);
            """)
            
            print("✓ Tabla 'golf_course' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - name: TEXT NOT NULL")
            print("  - location: GEOGRAPHY(Point, 4326)")
            print("  - Índice espacial: idx_golf_course_location (GIST)")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_hole_table(drop_if_exists=False):
    """
    Crea la tabla hole en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'hole' si existe...")
                cur.execute("DROP TABLE IF EXISTS hole CASCADE;")
                print("Tabla 'hole' eliminada (si existía)")

            # Asegurarnos de que existe la tabla padre
            print("Verificando existencia de tabla 'golf_course'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'golf_course'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'golf_course' no existe. Créala primero.")

            # Verificar PostGIS
            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    return False
                postgis_version = check_postgis()
            print(f"✓ PostGIS disponible: versión {postgis_version}")

            print("Creando tabla 'hole'...")
            cur.execute("""
                CREATE TABLE hole (
                    id SERIAL PRIMARY KEY,
                    course_id INT REFERENCES golf_course(id),
                    hole_number INT NOT NULL,
                    par INT,
                    length INT,
                    fairway_polygon GEOGRAPHY(Polygon, 4326),
                    green_polygon GEOGRAPHY(Polygon, 4326)
                );
            """)

            print("Creando índices espaciales en 'hole'...")
            cur.execute("""
                CREATE INDEX idx_hole_fairway_polygon 
                ON hole USING GIST(fairway_polygon);
            """)
            cur.execute("""
                CREATE INDEX idx_hole_green_polygon 
                ON hole USING GIST(green_polygon);
            """)

            print("✓ Tabla 'hole' creada exitosamente")
            return True

    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_hole_point_table(drop_if_exists=False):
    """
    Crea la tabla hole_point en la base de datos
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'hole_point' si existe...")
                cur.execute("DROP TABLE IF EXISTS hole_point CASCADE;")
                print("Tabla 'hole_point' eliminada (si existía)")

            print("Verificando existencia de tabla 'hole'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")

            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    return False
                postgis_version = check_postgis()
            print(f"✓ PostGIS disponible: versión {postgis_version}")

            print("Creando tabla 'hole_point'...")
            cur.execute("""
                CREATE TABLE hole_point (
                    id SERIAL PRIMARY KEY,
                    hole_id INT REFERENCES hole(id) ON DELETE CASCADE,
                    type TEXT CHECK (type IN (
                        'tee', 'flag', 'green_start', 'tee_white', 'tee_yellow'
                    )),
                    position GEOGRAPHY(Point, 4326)
                );
            """)

            print("Creando índice espacial en 'position' de 'hole_point'...")
            cur.execute("""
                CREATE INDEX idx_hole_point_position 
                ON hole_point USING GIST(position);
            """)

            print("✓ Tabla 'hole_point' creada exitosamente")
            return True

    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_obstacle_table(drop_if_exists=False):
    """
    Crea la tabla obstacle en la base de datos
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'obstacle' si existe...")
                cur.execute("DROP TABLE IF EXISTS obstacle CASCADE;")
                print("Tabla 'obstacle' eliminada (si existía)")

            print("Verificando existencia de tabla 'hole'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")

            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    return False
                postgis_version = check_postgis()
            print(f"✓ PostGIS disponible: versión {postgis_version}")

            print("Creando tabla 'obstacle'...")
            cur.execute("""
                CREATE TABLE obstacle (
                    id SERIAL PRIMARY KEY,
                    hole_id INT REFERENCES hole(id) ON DELETE CASCADE,
                    type TEXT CHECK (
                        type IN ('bunker', 'water', 'trees', 'rough_heavy', 'out_of_bounds')
                    ),
                    shape GEOGRAPHY(Geometry, 4326),
                    name TEXT
                );
            """)

            print("Creando índice espacial en 'shape' de 'obstacle'...")
            cur.execute("""
                CREATE INDEX idx_obstacle_shape 
                ON obstacle USING GIST(shape);
            """)

            print("✓ Tabla 'obstacle' creada exitosamente")
            return True

    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_optimal_shot_table(drop_if_exists=False):
    """
    Crea la tabla optimal_shot en la base de datos
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'optimal_shot' si existe...")
                cur.execute("DROP TABLE IF EXISTS optimal_shot CASCADE;")
                print("Tabla 'optimal_shot' eliminada (si existía)")

            print("Verificando existencia de tabla 'hole'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")

            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    return False
                postgis_version = check_postgis()
            print(f"✓ PostGIS disponible: versión {postgis_version}")

            print("Creando tabla 'optimal_shot'...")
            cur.execute("""
                CREATE TABLE optimal_shot (
                    id SERIAL PRIMARY KEY,
                    hole_id INT REFERENCES hole(id) ON DELETE CASCADE,
                    description TEXT,
                    path GEOGRAPHY(LineString, 4326)
                );
            """)

            print("Creando índice espacial en 'path' de 'optimal_shot'...")
            cur.execute("""
                CREATE INDEX idx_optimal_shot_path 
                ON optimal_shot USING GIST(path);
            """)

            print("✓ Tabla 'optimal_shot' creada exitosamente")
            return True

    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_strategic_point_table(drop_if_exists=False):
    """
    Crea la tabla strategic_point en la base de datos.
    
    Puntos estratégicos son ubicaciones de interés en el hoyo (landing zones,
    layup points, etc.) que ayudan a calcular trayectorias alternativas.
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'strategic_point' si existe...")
                cur.execute("DROP TABLE IF EXISTS strategic_point CASCADE;")
                print("Tabla 'strategic_point' eliminada (si existía)")

            print("Verificando existencia de tabla 'hole'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")

            postgis_version = check_postgis()
            if not postgis_version:
                print("⚠ PostGIS no está instalado. Intentando instalar...")
                if not install_postgis():
                    print("\n✗ No se pudo instalar PostGIS automáticamente.")
                    return False
                postgis_version = check_postgis()
            print(f"✓ PostGIS disponible: versión {postgis_version}")

            print("Creando tabla 'strategic_point'...")
            cur.execute("""
                CREATE TABLE strategic_point (
                    id SERIAL PRIMARY KEY,
                    hole_id INT REFERENCES hole(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    name VARCHAR(100),
                    description TEXT,
                    position GEOGRAPHY(Point, 4326) NOT NULL,
                    distance_to_flag INT,
                    priority INT DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            print("Creando índice espacial en 'position' de 'strategic_point'...")
            cur.execute("""
                CREATE INDEX idx_strategic_point_position 
                ON strategic_point USING GIST(position);
            """)

            print("Creando índice en 'hole_id' de 'strategic_point'...")
            cur.execute("""
                CREATE INDEX idx_strategic_point_hole_id 
                ON strategic_point(hole_id);
            """)

            print("Creando índice en 'type' de 'strategic_point'...")
            cur.execute("""
                CREATE INDEX idx_strategic_point_type 
                ON strategic_point(type);
            """)

            print("✓ Tabla 'strategic_point' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - hole_id: INT REFERENCES hole(id)")
            print("  - type: VARCHAR(50) - fairway_center_far, fairway_center_mid, layup_zone, etc.")
            print("  - name: VARCHAR(100)")
            print("  - description: TEXT")
            print("  - position: GEOGRAPHY(Point, 4326)")
            print("  - distance_to_flag: INT")
            print("  - priority: INT (mayor = más importante)")
            print("  - created_at: TIMESTAMP")
            return True

    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def verify_golf_course_table():
    """
    Verifica que la tabla golf_course existe y tiene la estructura correcta
    
    Returns:
        dict: Información sobre la tabla o None si no existe
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la tabla existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'golf_course'
                );
            """)
            exists = cur.fetchone()['exists']
            
            if not exists:
                print("✗ La tabla 'golf_course' no existe")
                return None
            
            # Obtener información de las columnas
            cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'golf_course'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            # Obtener información de índices
            cur.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = 'golf_course';
            """)
            indexes = cur.fetchall()
            
            print("✓ La tabla 'golf_course' existe")
            print("\nColumnas:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            if indexes:
                print("\nÍndices:")
                for idx in indexes:
                    print(f"  - {idx['indexname']}")
            
            return {
                'exists': True,
                'columns': columns,
                'indexes': indexes
            }
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        return None
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return None


def drop_golf_course_table():
    """
    Elimina la tabla golf_course de la base de datos
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Eliminando tabla 'golf_course'...")
            cur.execute("DROP TABLE IF EXISTS golf_course CASCADE;")
            print("✓ Tabla 'golf_course' eliminada exitosamente")
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def drop_all_golf_tables():
    """
    Elimina todas las tablas relacionadas con el campo de golf
    en el orden correcto para respetar las claves foráneas.
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Eliminando tablas de golf en orden correcto...")
            cur.execute("DROP TABLE IF EXISTS strategic_point CASCADE;")
            cur.execute("DROP TABLE IF EXISTS optimal_shot CASCADE;")
            cur.execute("DROP TABLE IF EXISTS obstacle CASCADE;")
            cur.execute("DROP TABLE IF EXISTS hole_point CASCADE;")
            cur.execute("DROP TABLE IF EXISTS hole CASCADE;")
            cur.execute("DROP TABLE IF EXISTS golf_course CASCADE;")
            print("✓ Todas las tablas de golf han sido eliminadas")
            return True
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_all_golf_tables(recreate=False):
    """
    Crea todas las tablas del modelo de golf en el orden correcto.
    
    Args:
        recreate: Si es True, elimina previamente las tablas existentes.
    """
    if recreate:
        print("→ Recreando todas las tablas de golf (drop + create)...")
        if not drop_all_golf_tables():
            return False

    print("→ Creando tabla 'golf_course'...")
    if not create_golf_course_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'hole'...")
    if not create_hole_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'hole_point'...")
    if not create_hole_point_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'obstacle'...")
    if not create_obstacle_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'optimal_shot'...")
    if not create_optimal_shot_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'strategic_point'...")
    if not create_strategic_point_table(drop_if_exists=False):
        return False

    print("✓ Todas las tablas de golf han sido creadas correctamente")
    return True


if __name__ == '__main__':
    """
    Script para ejecutar migraciones desde la línea de comandos
    
    Uso:
        python migrations.py create          # Crea la tabla (si no existe, falla)
        python migrations.py recreate        # Elimina y crea la tabla
        python migrations.py verify          # Verifica que la tabla existe
        python migrations.py drop            # Elimina la tabla
    """
    import sys
    
    print("=" * 60)
    print("Sistema de Migraciones - golf_course")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos (intentar instalar PostGIS si falta)
    if not init_database(install_postgis_if_missing=True):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        print("\nSolución:")
        print("1. Verifica tu configuración en el archivo .env")
        print("2. Asegúrate de que la base de datos existe:")
        print(f"   CREATE DATABASE {settings.DB_NAME};")
        print("3. Instala PostGIS manualmente:")
        print("   python -c \"from database import install_postgis; install_postgis()\"")
        sys.exit(1)
    
    # Procesar comando
    if len(sys.argv) < 2:
        print("\nUso: python migrations.py [create|recreate|verify|drop|create_all|recreate_all|drop_all]")
        print("\nComandos sobre 'golf_course' únicamente:")
        print("  create       - Crea la tabla (falla si ya existe)")
        print("  recreate     - Elimina y recrea la tabla")
        print("  verify       - Verifica que la tabla existe y muestra su estructura")
        print("  drop         - Elimina la tabla")
        print("\nComandos sobre TODO el modelo de golf:")
        print("  create_all   - Crea todas las tablas (golf_course, hole, hole_point, obstacle, optimal_shot)")
        print("  recreate_all - Elimina y recrea todas las tablas")
        print("  drop_all     - Elimina todas las tablas de golf")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        print("\n→ Creando tabla 'golf_course'...")
        success = create_golf_course_table(drop_if_exists=False)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al crear la tabla")
            sys.exit(1)
            
    elif command == 'recreate':
        print("\n→ Recreando tabla 'golf_course'...")
        success = create_golf_course_table(drop_if_exists=True)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al recrear la tabla")
            sys.exit(1)
            
    elif command == 'verify':
        print("\n→ Verificando tabla 'golf_course'...")
        result = verify_golf_course_table()
        if result:
            print("\n✓ Verificación completada")
        else:
            print("\n✗ La tabla no existe o hubo un error")
            sys.exit(1)
            
    elif command == 'drop':
        confirm = input("\n¿Estás seguro de que quieres eliminar la tabla 'golf_course'? (s/N): ")
        if confirm.lower() == 's':
            print("\n→ Eliminando tabla 'golf_course'...")
            success = drop_golf_course_table()
            if success:
                print("\n✓ Tabla eliminada exitosamente")
            else:
                print("\n✗ Error al eliminar la tabla")
                sys.exit(1)
        else:
            print("Operación cancelada")
    elif command == 'create_all':
        print("\n→ Creando todas las tablas de golf...")
        success = create_all_golf_tables(recreate=False)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al crear las tablas de golf")
            sys.exit(1)
    elif command == 'recreate_all':
        print("\n→ Recreando todas las tablas de golf...")
        success = create_all_golf_tables(recreate=True)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al recrear las tablas de golf")
            sys.exit(1)
    elif command == 'drop_all':
        confirm = input("\n¿Estás seguro de que quieres eliminar TODAS las tablas de golf? (s/N): ")
        if confirm.lower() == 's':
            print("\n→ Eliminando todas las tablas de golf...")
            success = drop_all_golf_tables()
            if success:
                print("\n✓ Tablas eliminadas exitosamente")
            else:
                print("\n✗ Error al eliminar las tablas")
                sys.exit(1)
        else:
            print("Operación cancelada")
            
    else:
        print(f"\n✗ Comando desconocido: {command}")
        print("Usa: create, recreate, verify o drop")
        sys.exit(1)
    
    print("\n" + "=" * 60)

