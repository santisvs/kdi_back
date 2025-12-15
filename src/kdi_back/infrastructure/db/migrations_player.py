# -*- coding: utf-8 -*-
"""
Sistema de migraciones para las tablas de perfil de jugador

Este módulo permite crear y gestionar las tablas relacionadas con usuarios y perfiles de jugadores.

Tablas gestionadas:
- user (usuarios/jugadores)
- player_profile (perfil de jugador)
- golf_club (catálogo de palos de golf)
- player_club_statistics (estadísticas de distancia y error por palo)
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


def create_user_table(drop_if_exists=False):
    """
    Crea la tabla user en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'user' si existe...")
                cur.execute("DROP TABLE IF EXISTS user CASCADE;")
                print("Tabla 'user' eliminada (si existía)")

            print("Creando tabla 'user'...")
            cur.execute("""
                CREATE TABLE "user" (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    date_of_birth DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Crear índices para búsquedas frecuentes
            print("Creando índices en 'user'...")
            cur.execute("""
                CREATE INDEX idx_user_email ON "user"(email);
            """)
            cur.execute("""
                CREATE INDEX idx_user_username ON "user"(username);
            """)

            print("✓ Tabla 'user' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - email: TEXT UNIQUE NOT NULL")
            print("  - username: TEXT UNIQUE NOT NULL")
            print("  - first_name: TEXT")
            print("  - last_name: TEXT")
            print("  - phone: TEXT")
            print("  - date_of_birth: DATE")
            print("  - created_at: TIMESTAMP")
            print("  - updated_at: TIMESTAMP")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_player_profile_table(drop_if_exists=False):
    """
    Crea la tabla player_profile en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'player_profile' si existe...")
                cur.execute("DROP TABLE IF EXISTS player_profile CASCADE;")
                print("Tabla 'player_profile' eliminada (si existía)")

            # Verificar que existe la tabla user
            print("Verificando existencia de tabla 'user'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'user' no existe. Créala primero.")

            print("Creando tabla 'player_profile'...")
            cur.execute("""
                CREATE TABLE player_profile (
                    id SERIAL PRIMARY KEY,
                    user_id INT UNIQUE NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    handicap DECIMAL(5,2),
                    gender TEXT CHECK (gender IN ('male', 'female')),
                    preferred_hand TEXT CHECK (preferred_hand IN ('right', 'left', 'ambidextrous')),
                    years_playing INT,
                    skill_level TEXT CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'professional')),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Crear índice para búsquedas por usuario
            print("Creando índice en 'player_profile'...")
            cur.execute("""
                CREATE INDEX idx_player_profile_user_id ON player_profile(user_id);
            """)

            print("✓ Tabla 'player_profile' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - user_id: INT UNIQUE NOT NULL REFERENCES user(id)")
            print("  - handicap: DECIMAL(5,2)")
            print("  - gender: TEXT (male, female)")
            print("  - preferred_hand: TEXT (right, left, ambidextrous)")
            print("  - years_playing: INT")
            print("  - skill_level: TEXT (beginner, intermediate, advanced, professional)")
            print("  - notes: TEXT")
            print("  - created_at: TIMESTAMP")
            print("  - updated_at: TIMESTAMP")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_golf_club_table(drop_if_exists=False):
    """
    Crea la tabla golf_club (catálogo de palos de golf) en la base de datos
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'golf_club' si existe...")
                cur.execute("DROP TABLE IF EXISTS golf_club CASCADE;")
                print("Tabla 'golf_club' eliminada (si existía)")

            print("Creando tabla 'golf_club'...")
            cur.execute("""
                CREATE TABLE golf_club (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL CHECK (type IN (
                        'driver', 'wood', 'hybrid', 'iron', 'wedge', 'putter'
                    )),
                    number INT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Crear índices
            print("Creando índices en 'golf_club'...")
            cur.execute("""
                CREATE INDEX idx_golf_club_name ON golf_club(name);
            """)
            cur.execute("""
                CREATE INDEX idx_golf_club_type ON golf_club(type);
            """)

            print("✓ Tabla 'golf_club' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - name: TEXT UNIQUE NOT NULL (ej: 'Driver', 'Hierro 7', 'Wedge')")
            print("  - type: TEXT NOT NULL (driver, wood, hybrid, iron, wedge, putter)")
            print("  - number: INT (número del palo, ej: 3, 5, 7, 9)")
            print("  - description: TEXT")
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


def create_player_club_statistics_table(drop_if_exists=False):
    """
    Crea la tabla player_club_statistics en la base de datos
    
    Esta tabla almacena las estadísticas de distancia y error por cada palo para cada jugador.
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'player_club_statistics' si existe...")
                cur.execute("DROP TABLE IF EXISTS player_club_statistics CASCADE;")
                print("Tabla 'player_club_statistics' eliminada (si existía)")

            # Verificar que existen las tablas necesarias
            print("Verificando existencia de tablas necesarias...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'player_profile'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'player_profile' no existe. Créala primero.")

            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'golf_club'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'golf_club' no existe. Créala primero.")

            print("Creando tabla 'player_club_statistics'...")
            cur.execute("""
                CREATE TABLE player_club_statistics (
                    id SERIAL PRIMARY KEY,
                    player_profile_id INT NOT NULL REFERENCES player_profile(id) ON DELETE CASCADE,
                    golf_club_id INT NOT NULL REFERENCES golf_club(id) ON DELETE CASCADE,
                    average_distance_meters DECIMAL(8,2) NOT NULL,
                    min_distance_meters DECIMAL(8,2),
                    max_distance_meters DECIMAL(8,2),
                    average_error_meters DECIMAL(8,2) NOT NULL,
                    error_std_deviation DECIMAL(8,2),
                    shots_recorded INT DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(player_profile_id, golf_club_id)
                );
            """)

            # Crear índices para búsquedas frecuentes
            print("Creando índices en 'player_club_statistics'...")
            cur.execute("""
                CREATE INDEX idx_player_club_stats_profile ON player_club_statistics(player_profile_id);
            """)
            cur.execute("""
                CREATE INDEX idx_player_club_stats_club ON player_club_statistics(golf_club_id);
            """)
            cur.execute("""
                CREATE INDEX idx_player_club_stats_distance ON player_club_statistics(average_distance_meters);
            """)

            print("✓ Tabla 'player_club_statistics' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - player_profile_id: INT NOT NULL REFERENCES player_profile(id)")
            print("  - golf_club_id: INT NOT NULL REFERENCES golf_club(id)")
            print("  - average_distance_meters: DECIMAL(8,2) NOT NULL (distancia promedio)")
            print("  - min_distance_meters: DECIMAL(8,2) (distancia mínima)")
            print("  - max_distance_meters: DECIMAL(8,2) (distancia máxima)")
            print("  - average_error_meters: DECIMAL(8,2) NOT NULL (error promedio)")
            print("  - error_std_deviation: DECIMAL(8,2) (desviación estándar del error)")
            print("  - shots_recorded: INT DEFAULT 0 (número de golpes registrados)")
            print("  - last_updated: TIMESTAMP")
            print("  - created_at: TIMESTAMP")
            print("  - UNIQUE(player_profile_id, golf_club_id)")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def seed_golf_clubs():
    """
    Inserta los palos de golf más comunes en la tabla golf_club
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Verificando si ya existen palos en 'golf_club'...")
            cur.execute("SELECT COUNT(*) FROM golf_club;")
            count = cur.fetchone()['count']
            
            if count > 0:
                print(f"✓ Ya existen {count} palos en la tabla. No se insertarán datos.")
                return True

            print("Insertando palos de golf comunes...")
            
            clubs = [
                # Drivers
                ('Driver', 'driver', None, 'Palo de salida para distancias largas'),
                
                # Woods
                ('Madera 3', 'wood', 3, 'Madera de calle para distancias largas'),
                ('Madera 5', 'wood', 5, 'Madera de calle para distancias medias-largas'),
                
                # Hybrids
                ('Híbrido 3', 'hybrid', 3, 'Híbrido para reemplazar hierro 3'),
                ('Híbrido 4', 'hybrid', 4, 'Híbrido para reemplazar hierro 4'),
                ('Híbrido 5', 'hybrid', 5, 'Híbrido para reemplazar hierro 5'),
                
                # Irons
                ('Hierro 3', 'iron', 3, 'Hierro largo para distancias largas'),
                ('Hierro 4', 'iron', 4, 'Hierro largo para distancias medias-largas'),
                ('Hierro 5', 'iron', 5, 'Hierro medio para distancias medias'),
                ('Hierro 6', 'iron', 6, 'Hierro medio para distancias medias'),
                ('Hierro 7', 'iron', 7, 'Hierro medio-corto para distancias medias-cortas'),
                ('Hierro 8', 'iron', 8, 'Hierro corto para distancias cortas'),
                ('Hierro 9', 'iron', 9, 'Hierro corto para distancias cortas'),
                
                # Wedges
                ('Pitching Wedge', 'wedge', None, 'Wedge para aproximaciones'),
                ('Sand Wedge', 'wedge', None, 'Wedge para salir de bunkers'),
                ('Gap Wedge', 'wedge', None, 'Wedge para distancias intermedias'),
                ('Lob Wedge', 'wedge', None, 'Wedge para golpes altos y cortos'),
                
                # Putter
                ('Putter', 'putter', None, 'Palo para golpes en el green'),
            ]
            
            cur.executemany("""
                INSERT INTO golf_club (name, type, number, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, clubs)
            
            print(f"✓ {len(clubs)} palos de golf insertados exitosamente")
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def drop_all_player_tables():
    """
    Elimina todas las tablas relacionadas con jugadores
    en el orden correcto para respetar las claves foráneas.
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Eliminando tablas de jugadores en orden correcto...")
            cur.execute("DROP TABLE IF EXISTS player_club_statistics CASCADE;")
            cur.execute("DROP TABLE IF EXISTS player_profile CASCADE;")
            cur.execute("DROP TABLE IF EXISTS golf_club CASCADE;")
            cur.execute("DROP TABLE IF EXISTS \"user\" CASCADE;")
            print("✓ Todas las tablas de jugadores han sido eliminadas")
            return True
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_all_player_tables(recreate=False):
    """
    Crea todas las tablas del modelo de jugador en el orden correcto.
    
    Args:
        recreate: Si es True, elimina previamente las tablas existentes.
    """
    if recreate:
        print("→ Recreando todas las tablas de jugadores (drop + create)...")
        if not drop_all_player_tables():
            return False

    print("→ Creando tabla 'user'...")
    if not create_user_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'player_profile'...")
    if not create_player_profile_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'golf_club'...")
    if not create_golf_club_table(drop_if_exists=False):
        return False

    print("→ Creando tabla 'player_club_statistics'...")
    if not create_player_club_statistics_table(drop_if_exists=False):
        return False

    print("→ Insertando palos de golf comunes...")
    if not seed_golf_clubs():
        return False

    print("✓ Todas las tablas de jugadores han sido creadas correctamente")
    return True


if __name__ == '__main__':
    """
    Script para ejecutar migraciones desde la línea de comandos
    
    Uso:
        python migrations_player.py create_all       # Crea todas las tablas
        python migrations_player.py recreate_all      # Elimina y crea todas las tablas
        python migrations_player.py drop_all          # Elimina todas las tablas
        python migrations_player.py seed_clubs        # Inserta palos de golf comunes
    """
    import sys
    
    print("=" * 60)
    print("Sistema de Migraciones - Perfil de Jugador")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=True):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        print("\nSolución:")
        print("1. Verifica tu configuración en el archivo .env")
        print("2. Asegúrate de que la base de datos existe:")
        print(f"   CREATE DATABASE {settings.DB_NAME};")
        sys.exit(1)
    
    # Procesar comando
    if len(sys.argv) < 2:
        print("\nUso: python migrations_player.py [create_all|recreate_all|drop_all|seed_clubs]")
        print("\nComandos:")
        print("  create_all   - Crea todas las tablas (user, player_profile, golf_club, player_club_statistics)")
        print("  recreate_all - Elimina y recrea todas las tablas")
        print("  drop_all     - Elimina todas las tablas de jugadores")
        print("  seed_clubs   - Inserta palos de golf comunes en la tabla golf_club")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create_all':
        print("\n→ Creando todas las tablas de jugadores...")
        success = create_all_player_tables(recreate=False)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al crear las tablas")
            sys.exit(1)
            
    elif command == 'recreate_all':
        print("\n→ Recreando todas las tablas de jugadores...")
        success = create_all_player_tables(recreate=True)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al recrear las tablas")
            sys.exit(1)
            
    elif command == 'drop_all':
        confirm = input("\n¿Estás seguro de que quieres eliminar TODAS las tablas de jugadores? (s/N): ")
        if confirm.lower() == 's':
            print("\n→ Eliminando todas las tablas de jugadores...")
            success = drop_all_player_tables()
            if success:
                print("\n✓ Tablas eliminadas exitosamente")
            else:
                print("\n✗ Error al eliminar las tablas")
                sys.exit(1)
        else:
            print("Operación cancelada")
            
    elif command == 'seed_clubs':
        print("\n→ Insertando palos de golf comunes...")
        success = seed_golf_clubs()
        if success:
            print("\n✓ Palos insertados exitosamente")
        else:
            print("\n✗ Error al insertar los palos")
            sys.exit(1)
            
    else:
        print(f"\n✗ Comando desconocido: {command}")
        print("Usa: create_all, recreate_all, drop_all o seed_clubs")
        sys.exit(1)
    
    print("\n" + "=" * 60)

