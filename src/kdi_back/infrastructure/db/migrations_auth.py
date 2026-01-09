# -*- coding: utf-8 -*-
"""
Sistema de migraciones para las tablas de autenticación

Este módulo permite crear y gestionar las tablas relacionadas con autenticación de usuarios.

Tablas gestionadas:
- user (modificación: agregar campos de autenticación)
- auth_tokens (tokens JWT)
"""
try:
    from .database import Database, init_database
    from ...infrastructure.config import settings
except ImportError:
    # Si se ejecuta directamente como script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database
    from kdi_back.infrastructure.config import settings
import psycopg2


def add_auth_columns_to_user_table():
    """
    Agrega columnas de autenticación a la tabla user.
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Verificando existencia de tabla 'user'...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user'
                );
            """)
            if not cur.fetchone()['exists']:
                raise Exception("La tabla 'user' no existe. Créala primero con migrations_player.py")
            
            print("Agregando columnas de autenticación a 'user'...")
            
            # Agregar password_hash si no existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='password_hash';
            """)
            if not cur.fetchone():
                cur.execute("""
                    ALTER TABLE "user" 
                    ADD COLUMN password_hash TEXT;
                """)
                print("  ✓ Columna 'password_hash' agregada")
            else:
                print("  - Columna 'password_hash' ya existe")
            
            # Agregar oauth_provider si no existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='oauth_provider';
            """)
            if not cur.fetchone():
                cur.execute("""
                    ALTER TABLE "user" 
                    ADD COLUMN oauth_provider TEXT CHECK (oauth_provider IN ('google', 'instagram'));
                """)
                print("  ✓ Columna 'oauth_provider' agregada")
            else:
                print("  - Columna 'oauth_provider' ya existe")
            
            # Agregar oauth_id si no existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='oauth_id';
            """)
            if not cur.fetchone():
                cur.execute("""
                    ALTER TABLE "user" 
                    ADD COLUMN oauth_id TEXT;
                """)
                print("  ✓ Columna 'oauth_id' agregada")
            else:
                print("  - Columna 'oauth_id' ya existe")
            
            # Agregar password_reset_token si no existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='password_reset_token';
            """)
            if not cur.fetchone():
                cur.execute("""
                    ALTER TABLE "user" 
                    ADD COLUMN password_reset_token TEXT;
                """)
                print("  ✓ Columna 'password_reset_token' agregada")
            else:
                print("  - Columna 'password_reset_token' ya existe")
            
            # Agregar password_reset_expires si no existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='password_reset_expires';
            """)
            if not cur.fetchone():
                cur.execute("""
                    ALTER TABLE "user" 
                    ADD COLUMN password_reset_expires TIMESTAMP;
                """)
                print("  ✓ Columna 'password_reset_expires' agregada")
            else:
                print("  - Columna 'password_reset_expires' ya existe")
            
            # Crear índice único compuesto para OAuth
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'user' AND indexname = 'idx_user_oauth';
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE UNIQUE INDEX idx_user_oauth 
                    ON "user"(oauth_provider, oauth_id) 
                    WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL;
                """)
                print("  ✓ Índice único 'idx_user_oauth' creado")
            else:
                print("  - Índice 'idx_user_oauth' ya existe")
            
            # Crear índice para password_reset_token
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'user' AND indexname = 'idx_user_reset_token';
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE INDEX idx_user_reset_token 
                    ON "user"(password_reset_token) 
                    WHERE password_reset_token IS NOT NULL;
                """)
                print("  ✓ Índice 'idx_user_reset_token' creado")
            else:
                print("  - Índice 'idx_user_reset_token' ya existe")
            
            print("✓ Columnas de autenticación agregadas exitosamente")
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_auth_tokens_table(drop_if_exists=False):
    """
    Crea la tabla auth_tokens en la base de datos.
    
    Args:
        drop_if_exists: Si es True, elimina la tabla si existe antes de crearla
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            if drop_if_exists:
                print("Eliminando tabla 'auth_tokens' si existe...")
                cur.execute("DROP TABLE IF EXISTS auth_tokens CASCADE;")
                print("Tabla 'auth_tokens' eliminada (si existía)")
            
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
            
            print("Creando tabla 'auth_tokens'...")
            cur.execute("""
                CREATE TABLE auth_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    token TEXT UNIQUE NOT NULL,
                    token_type TEXT DEFAULT 'Bearer',
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_revoked BOOLEAN DEFAULT FALSE
                );
            """)
            
            # Crear índices
            print("Creando índices en 'auth_tokens'...")
            cur.execute("""
                CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
            """)
            cur.execute("""
                CREATE INDEX idx_auth_tokens_token ON auth_tokens(token);
            """)
            cur.execute("""
                CREATE INDEX idx_auth_tokens_expires_at ON auth_tokens(expires_at);
            """)
            cur.execute("""
                CREATE INDEX idx_auth_tokens_active ON auth_tokens(user_id, is_revoked, expires_at) 
                WHERE is_revoked = FALSE;
            """)
            
            print("✓ Tabla 'auth_tokens' creada exitosamente")
            print("\nEstructura de la tabla:")
            print("  - id: SERIAL PRIMARY KEY")
            print("  - user_id: INT NOT NULL REFERENCES user(id)")
            print("  - token: TEXT UNIQUE NOT NULL")
            print("  - token_type: TEXT DEFAULT 'Bearer'")
            print("  - expires_at: TIMESTAMP NOT NULL")
            print("  - created_at: TIMESTAMP")
            print("  - last_used_at: TIMESTAMP")
            print("  - is_revoked: BOOLEAN DEFAULT FALSE")
            
            return True
            
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def create_all_auth_tables(recreate=False):
    """
    Crea todas las tablas de autenticación.
    
    Args:
        recreate: Si es True, elimina previamente las tablas existentes.
    """
    if recreate:
        print("→ Recreando todas las tablas de autenticación (drop + create)...")
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("DROP TABLE IF EXISTS auth_tokens CASCADE;")
    
    print("→ Agregando columnas de autenticación a 'user'...")
    if not add_auth_columns_to_user_table():
        return False
    
    print("→ Creando tabla 'auth_tokens'...")
    if not create_auth_tokens_table(drop_if_exists=False):
        return False
    
    print("✓ Todas las tablas de autenticación han sido creadas correctamente")
    return True


if __name__ == '__main__':
    """
    Script para ejecutar migraciones desde la línea de comandos
    
    Uso:
        python migrations_auth.py create_all       # Crea todas las tablas
        python migrations_auth.py recreate_all      # Elimina y crea todas las tablas
    """
    import sys
    
    print("=" * 60)
    print("Sistema de Migraciones - Autenticación")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=False):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        sys.exit(1)
    
    # Procesar comando
    if len(sys.argv) < 2:
        print("\nUso: python migrations_auth.py [create_all|recreate_all]")
        print("\nComandos:")
        print("  create_all   - Agrega columnas de auth a user y crea auth_tokens")
        print("  recreate_all - Elimina y recrea auth_tokens")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create_all':
        print("\n→ Creando todas las tablas de autenticación...")
        success = create_all_auth_tables(recreate=False)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al crear las tablas")
            sys.exit(1)
            
    elif command == 'recreate_all':
        print("\n→ Recreando todas las tablas de autenticación...")
        success = create_all_auth_tables(recreate=True)
        if success:
            print("\n✓ Migración completada exitosamente")
        else:
            print("\n✗ Error al recrear las tablas")
            sys.exit(1)
            
    else:
        print(f"\n✗ Comando desconocido: {command}")
        print("Usa: create_all o recreate_all")
        sys.exit(1)
    
    print("\n" + "=" * 60)

