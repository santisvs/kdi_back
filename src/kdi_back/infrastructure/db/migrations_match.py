# -*- coding: utf-8 -*-
"""
Sistema de migraciones para las tablas de partidos (matches)

Este módulo permite crear y gestionar las tablas relacionadas con partidos de golf.

Tablas gestionadas:
- match (partidos)
- match_player (relación entre partidos y jugadores)
- match_hole_score (puntuación de cada jugador en cada hoyo)
- match_stroke (golpes individuales con información para evaluación)
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


def create_match_table(drop_if_exists=False):
    """
    Crea la tabla match en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'match' si existe...")
                cur.execute("DROP TABLE IF EXISTS match CASCADE;")
                print("Tabla 'match' eliminada (si existía)")

            # Verificar que existe la tabla golf_course
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

            print("Creando tabla 'match'...")
            cur.execute("""
                CREATE TABLE match (
                    id SERIAL PRIMARY KEY,
                    course_id INT NOT NULL REFERENCES golf_course(id) ON DELETE CASCADE,
                    name TEXT,
                    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'cancelled')),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Crear índices
            print("Creando índices en 'match'...")
            cur.execute("""
                CREATE INDEX idx_match_course_id ON match(course_id);
            """)
            cur.execute("""
                CREATE INDEX idx_match_status ON match(status);
            """)
            cur.execute("""
                CREATE INDEX idx_match_started_at ON match(started_at);
            """)

            print("✓ Tabla 'match' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - course_id: INT NOT NULL REFERENCES golf_course(id)")
            print("  - name: TEXT (nombre opcional del partido)")
            print("  - status: TEXT NOT NULL DEFAULT 'in_progress' (in_progress, completed, cancelled)")
            print("  - started_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("  - completed_at: TIMESTAMP (cuando se completó el partido)")
            print("  - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("  - updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_match_player_table(drop_if_exists=False):
    """
    Crea la tabla match_player (relación muchos a muchos entre match y user)
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'match_player' si existe...")
                cur.execute("DROP TABLE IF EXISTS match_player CASCADE;")
                print("Tabla 'match_player' eliminada (si existía)")

            # Verificar que existen las tablas necesarias
            print("Verificando existencia de tablas 'match' y 'user'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'match'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'match' no existe. Créala primero.")
            
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'user' no existe. Créala primero.")

            print("Creando tabla 'match_player'...")
            cur.execute("""
                CREATE TABLE match_player (
                    id SERIAL PRIMARY KEY,
                    match_id INT NOT NULL REFERENCES match(id) ON DELETE CASCADE,
                    user_id INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    starting_hole_number INT NOT NULL DEFAULT 1,
                    total_strokes INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(match_id, user_id)
                );
            """)

            # Crear índices
            print("Creando índices en 'match_player'...")
            cur.execute("""
                CREATE INDEX idx_match_player_match_id ON match_player(match_id);
            """)
            cur.execute("""
                CREATE INDEX idx_match_player_user_id ON match_player(user_id);
            """)

            print("✓ Tabla 'match_player' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - match_id: INT NOT NULL REFERENCES match(id)")
            print("  - user_id: INT NOT NULL REFERENCES user(id)")
            print("  - starting_hole_number: INT NOT NULL DEFAULT 1 (hoyo donde empieza el jugador)")
            print("  - total_strokes: INT DEFAULT 0 (total de golpes al finalizar)")
            print("  - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("  - UNIQUE(match_id, user_id): Un jugador solo puede estar una vez en un partido")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_match_hole_score_table(drop_if_exists=False):
    """
    Crea la tabla match_hole_score (puntuación de cada jugador en cada hoyo)
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'match_hole_score' si existe...")
                cur.execute("DROP TABLE IF EXISTS match_hole_score CASCADE;")
                print("Tabla 'match_hole_score' eliminada (si existía)")

            # Verificar que existen las tablas necesarias
            print("Verificando existencia de tablas 'match_player' y 'hole'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'match_player'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'match_player' no existe. Créala primero.")
            
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")

            print("Creando tabla 'match_hole_score'...")
            cur.execute("""
                CREATE TABLE match_hole_score (
                    id SERIAL PRIMARY KEY,
                    match_player_id INT NOT NULL REFERENCES match_player(id) ON DELETE CASCADE,
                    hole_id INT NOT NULL REFERENCES hole(id) ON DELETE CASCADE,
                    strokes INT NOT NULL CHECK (strokes > 0),
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(match_player_id, hole_id)
                );
            """)

            # Crear índices
            print("Creando índices en 'match_hole_score'...")
            cur.execute("""
                CREATE INDEX idx_match_hole_score_match_player_id ON match_hole_score(match_player_id);
            """)
            cur.execute("""
                CREATE INDEX idx_match_hole_score_hole_id ON match_hole_score(hole_id);
            """)

            print("✓ Tabla 'match_hole_score' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - match_player_id: INT NOT NULL REFERENCES match_player(id)")
            print("  - hole_id: INT NOT NULL REFERENCES hole(id)")
            print("  - strokes: INT NOT NULL CHECK (strokes > 0) (número de golpes en el hoyo)")
            print("  - completed_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("  - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("  - UNIQUE(match_player_id, hole_id): Un jugador solo puede tener una puntuación por hoyo")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_match_stroke_table(drop_if_exists=False):
    """
    Crea la tabla match_stroke (golpes individuales con información para evaluación)
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'match_stroke' si existe...")
                cur.execute("DROP TABLE IF EXISTS match_stroke CASCADE;")
                print("Tabla 'match_stroke' eliminada (si existía)")

            # Verificar que existen las tablas necesarias
            print("Verificando existencia de tablas 'match_player', 'hole' y 'golf_club'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'match_player'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'match_player' no existe. Créala primero.")
            
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hole'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'hole' no existe. Créala primero.")
            
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'golf_club'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'golf_club' no existe. Créala primero.")

            print("Creando tabla 'match_stroke'...")
            cur.execute("""
                CREATE TABLE match_stroke (
                    id SERIAL PRIMARY KEY,
                    match_player_id INT NOT NULL REFERENCES match_player(id) ON DELETE CASCADE,
                    hole_id INT NOT NULL REFERENCES hole(id) ON DELETE CASCADE,
                    stroke_number INT NOT NULL,
                    
                    -- Posición inicial de la bola
                    ball_start_latitude DECIMAL(10, 8) NOT NULL,
                    ball_start_longitude DECIMAL(10, 8) NOT NULL,
                    
                    -- Información del golpe ejecutado
                    club_used_id INT REFERENCES golf_club(id),
                    trajectory_type TEXT CHECK (trajectory_type IN ('conservadora', 'riesgo', 'optima')),
                    
                    -- Información de la propuesta (para comparación)
                    proposed_distance_meters DECIMAL(8,2),
                    proposed_club_id INT REFERENCES golf_club(id),
                    
                    -- Estado de evaluación
                    evaluated BOOLEAN DEFAULT FALSE,
                    evaluation_quality DECIMAL(5,2),
                    evaluation_distance_error DECIMAL(8,2),
                    evaluation_direction_error DECIMAL(8,2),
                    
                    -- Posición final (se completa cuando se evalúa)
                    ball_end_latitude DECIMAL(10, 8),
                    ball_end_longitude DECIMAL(10, 8),
                    ball_end_distance_meters DECIMAL(8,2),
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    evaluated_at TIMESTAMP
                );
            """)

            # Crear índices
            print("Creando índices en 'match_stroke'...")
            cur.execute("""
                CREATE INDEX idx_match_stroke_match_player_id ON match_stroke(match_player_id);
            """)
            cur.execute("""
                CREATE INDEX idx_match_stroke_hole_id ON match_stroke(hole_id);
            """)
            cur.execute("""
                CREATE INDEX idx_match_stroke_evaluated ON match_stroke(evaluated);
            """)
            cur.execute("""
                CREATE INDEX idx_match_stroke_match_player_hole ON match_stroke(match_player_id, hole_id, evaluated);
            """)

            print("✓ Tabla 'match_stroke' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - match_player_id: INT NOT NULL REFERENCES match_player(id)")
            print("  - hole_id: INT NOT NULL REFERENCES hole(id)")
            print("  - stroke_number: INT NOT NULL (número de golpe en el hoyo)")
            print("  - ball_start_latitude/longitude: Posición inicial de la bola")
            print("  - club_used_id: Palo utilizado (opcional)")
            print("  - trajectory_type: Trayectoria escogida (conservadora, riesgo, optima)")
            print("  - proposed_distance_meters: Distancia propuesta")
            print("  - proposed_club_id: Palo propuesto")
            print("  - evaluated: Si ya fue evaluado")
            print("  - evaluation_quality: Calidad del golpe (0-100)")
            print("  - evaluation_distance_error: Error en distancia (metros)")
            print("  - evaluation_direction_error: Error en dirección")
            print("  - ball_end_latitude/longitude: Posición final de la bola")
            print("  - ball_end_distance_meters: Distancia real alcanzada")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def drop_all_match_tables():
    """
    Elimina todas las tablas relacionadas con partidos
    en el orden correcto para respetar las claves foráneas.
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Eliminando tablas de partidos en orden correcto...")
            cur.execute("DROP TABLE IF EXISTS match_stroke CASCADE;")
            cur.execute("DROP TABLE IF EXISTS match_hole_score CASCADE;")
            cur.execute("DROP TABLE IF EXISTS match_player CASCADE;")
            cur.execute("DROP TABLE IF EXISTS match CASCADE;")
            print("✓ Todas las tablas de partidos han sido eliminadas")
            return True
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_all_match_tables(recreate=False):
    """
    Crea todas las tablas del modelo de partidos en el orden correcto.
    
    Args:
        recreate: Si es True, elimina previamente las tablas existentes.
    """
    if recreate:
        print("→ Recreando todas las tablas de partidos (drop + create)...")
        if not drop_all_match_tables():
            return False

    print("→ Creando tabla 'match'...")
    if not create_match_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'match_player'...")
    if not create_match_player_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'match_hole_score'...")
    if not create_match_hole_score_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'match_stroke'...")
    if not create_match_stroke_table(drop_if_exists=False):
        return False

    print("✓ Todas las tablas de partidos han sido creadas correctamente")
    return True


if __name__ == '__main__':
    """
    Script para ejecutar migraciones desde la línea de comandos
    
    Uso:
        python migrations_match.py create_all       # Crea todas las tablas
        python migrations_match.py recreate_all      # Elimina y crea todas las tablas
        python migrations_match.py drop_all         # Elimina todas las tablas
    """
    import sys
    
    print("=" * 60)
    print("Sistema de Migraciones - Partidos (Matches)")
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
        print("\nUso: python migrations_match.py [create_all|recreate_all|drop_all]")
        print("\nComandos:")
        print("  create_all   - Crea todas las tablas (match, match_player, match_hole_score, match_stroke)")
        print("  recreate_all - Elimina y recrea todas las tablas")
        print("  drop_all     - Elimina todas las tablas de partidos")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create_all':
        print("\n→ Creando todas las tablas de partidos...")
        success = create_all_match_tables(recreate=False)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al crear las tablas de partidos")
            sys.exit(1)
    elif command == 'recreate_all':
        print("\n→ Recreando todas las tablas de partidos...")
        success = create_all_match_tables(recreate=True)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al recrear las tablas de partidos")
            sys.exit(1)
    elif command == 'drop_all':
        confirm = input("\n¿Estás seguro de que quieres eliminar TODAS las tablas de partidos? (s/N): ")
        if confirm.lower() == 's':
            print("\n→ Eliminando todas las tablas de partidos...")
            success = drop_all_match_tables()
            if success:
                print("\n✓ Tablas eliminadas exitosamente")
            else:
                print("\n✗ Error al eliminar las tablas")
                sys.exit(1)
        else:
            print("Operación cancelada")
    else:
        print(f"\n✗ Comando desconocido: {command}")
        print("Usa: create_all, recreate_all o drop_all")
        sys.exit(1)
    
    print("\n" + "=" * 60)

