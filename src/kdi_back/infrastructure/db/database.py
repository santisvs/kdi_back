# -*- coding: utf-8 -*-
"""
Módulo para manejar la conexión y operaciones con PostgreSQL/PostGIS
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from kdi_back.infrastructure.config import settings
from contextlib import contextmanager


class Database:
    """
    Clase para manejar conexiones a PostgreSQL/PostGIS
    """
    _connection_pool = None

    @classmethod
    def initialize_pool(cls, minconn=1, maxconn=10):
        """
        Inicializa el pool de conexiones a la base de datos
        
        Args:
            minconn: Número mínimo de conexiones en el pool
            maxconn: Número máximo de conexiones en el pool
        """
        try:
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
            
            if cls._connection_pool:
                print("Pool de conexiones a PostgreSQL creado exitosamente")
            else:
                raise Exception("No se pudo crear el pool de conexiones")
                
        except (Exception, psycopg2.Error) as error:
            print(f"Error al crear el pool de conexiones: {error}")
            raise

    @classmethod
    def get_connection(cls):
        """
        Obtiene una conexión del pool
        
        Returns:
            Objeto de conexión de psycopg2
        """
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        """
        Devuelve una conexión al pool
        
        Args:
            connection: Objeto de conexión a devolver
        """
        if cls._connection_pool:
            cls._connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        """
        Cierra todas las conexiones del pool
        """
        if cls._connection_pool:
            cls._connection_pool.closeall()
            print("Todas las conexiones del pool han sido cerradas")

    @classmethod
    @contextmanager
    def get_cursor(cls, commit=False, dict_cursor=True):
        """
        Context manager para obtener un cursor de la base de datos
        
        Args:
            commit: Si es True, hace commit automático al finalizar
            dict_cursor: Si es True, retorna un cursor que devuelve diccionarios
        
        Yields:
            Tupla (connection, cursor)
        """
        connection = None
        cursor = None
        try:
            connection = cls.get_connection()
            if dict_cursor:
                cursor = connection.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = connection.cursor()
            
            yield (connection, cursor)
            
            if commit:
                connection.commit()
                
        except (Exception, psycopg2.Error) as error:
            if connection:
                connection.rollback()
            print(f"Error en la operación de base de datos: {error}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                cls.return_connection(connection)


def install_postgis():
    """
    Instala la extensión PostGIS en la base de datos actual
    
    Returns:
        bool: True si la instalación fue exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            print("Instalando extensión PostGIS...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            print("✓ Extensión PostGIS instalada exitosamente")
            
            # Verificar la instalación
            cur.execute("SELECT PostGIS_version();")
            version = cur.fetchone()
            print(f"  Versión instalada: {version['postgis_version']}")
            return True
            
    except psycopg2.Error as e:
        error_code = getattr(e, 'pgcode', None)
        error_message = str(e).lower()
        
        # Detectar si PostGIS no está instalado a nivel del sistema
        if error_code == '58P01' or 'no such file or directory' in error_message or 'postgis.control' in error_message:
            print("\n" + "=" * 60)
            print("✗ ERROR: PostGIS no está instalado en el sistema")
            print("=" * 60)
            print("\nEl error indica que PostGIS no está instalado en tu sistema Windows.")
            print("No es suficiente con tener PostgreSQL instalado; PostGIS debe instalarse por separado.")
            print("\nSOLUCIÓN: Instalar PostGIS en Windows")
            print("\nOpción 1: Usando Stack Builder (Recomendado)")
            print("1. Abre 'Stack Builder' que viene con PostgreSQL")
            print("2. Selecciona tu instalación de PostgreSQL")
            print("3. Busca 'PostGIS' en la lista de extensiones")
            print("4. Instálalo siguiendo el asistente")
            print("\nOpción 2: Descargar instalador independiente")
            print("1. Visita: https://postgis.net/windows_downloads/")
            print("2. Descarga el instalador para tu versión de PostgreSQL")
            print("3. Ejecuta el instalador (asegúrate de que coincida con tu versión de PostgreSQL)")
            print("\nOpción 3: Usar PostgreSQL con PostGIS preinstalado")
            print("Considera usar una distribución como 'Postgres.app' o reinstalar PostgreSQL")
            print("desde una distribución que incluya PostGIS (ej: BigSQL, EnterpriseDB)")
            print("\nDespués de instalar PostGIS en el sistema, vuelve a ejecutar este script.")
            print("=" * 60)
            return False
        elif error_code == '42501':  # insufficient_privilege
            print("✗ Error: No tienes permisos para instalar extensiones")
            print("\nInstrucciones:")
            print("1. Conéctate a PostgreSQL como superusuario (postgres)")
            print(f"2. Ejecuta: CREATE EXTENSION IF NOT EXISTS postgis;")
            print(f"3. O ejecuta: psql -U postgres -d {settings.DB_NAME} -c 'CREATE EXTENSION IF NOT EXISTS postgis;'")
        elif error_code == 'P0001':  # raise_exception
            print(f"✗ Error: {e.pgerror}")
        else:
            print(f"✗ Error al instalar PostGIS: {e}")
            print(f"  Código de error: {error_code}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado al instalar PostGIS: {e}")
        return False


def check_postgis():
    """
    Verifica si PostGIS está instalado en la base de datos
    
    Returns:
        str|None: Versión de PostGIS si está instalado, None en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("SELECT PostGIS_version();")
            version = cur.fetchone()
            return version['postgis_version']
    except psycopg2.Error:
        return None
    except Exception:
        return None


def init_database(install_postgis_if_missing=False):
    """
    Inicializa la conexión a la base de datos y verifica que PostGIS esté disponible
    
    Args:
        install_postgis_if_missing: Si es True, intenta instalar PostGIS si no está disponible
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        Database.initialize_pool()
        
        # Verificar que PostGIS esté instalado
        postgis_version = check_postgis()
        
        if postgis_version:
            print(f"✓ PostGIS disponible. Versión: {postgis_version}")
            return True
        else:
            print("⚠ PostGIS no está instalado en la base de datos")
            
            if install_postgis_if_missing:
                print("Intentando instalar PostGIS automáticamente...")
                if install_postgis():
                    return True
                else:
                    print("\nNo se pudo instalar PostGIS automáticamente.")
                    print("Por favor, instálalo manualmente siguiendo las instrucciones anteriores.")
                    return False
            else:
                print("\nPara instalar PostGIS, ejecuta:")
                print(f"  python -c \"from database import install_postgis; install_postgis()\"")
                print("\nO manualmente en PostgreSQL:")
                print(f"  CREATE EXTENSION IF NOT EXISTS postgis;")
                return False
            
    except psycopg2.Error as e:
        print(f"✗ Error al inicializar la base de datos: {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def test_connection():
    """
    Prueba la conexión a la base de datos
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"Conexión exitosa a PostgreSQL: {version['version'][:50]}...")
            return True
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return False

