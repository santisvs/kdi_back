# -*- coding: utf-8 -*-
"""
Ejemplos de uso de PostgreSQL/PostGIS con el módulo database.py

Este archivo contiene ejemplos prácticos de cómo usar las funciones geoespaciales
de PostGIS desde Python.
"""

try:
    from .database import Database, init_database
except ImportError:
    # Si se ejecuta directamente como script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database


def ejemplo_crear_punto():
    """
    Ejemplo: Crear un punto geográfico usando PostGIS
    """
    print("\n=== Ejemplo: Crear un punto geográfico ===")
    
    with Database.get_cursor(commit=True) as (conn, cur):
        # Crear un punto para Madrid (lat: 40.4168, lon: -3.7038)
        cur.execute("""
            SELECT 
                ST_GeomFromText('POINT(-3.7038 40.4168)', 4326) AS punto,
                ST_AsText(ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)) AS texto,
                ST_X(ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)) AS longitud,
                ST_Y(ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)) AS latitud;
        """)
        resultado = cur.fetchone()
        print(f"Punto: {resultado['texto']}")
        print(f"Longitud: {resultado['longitud']}")
        print(f"Latitud: {resultado['latitud']}")


def ejemplo_calcular_distancia():
    """
    Ejemplo: Calcular distancia entre dos puntos
    """
    print("\n=== Ejemplo: Calcular distancia entre puntos ===")
    
    with Database.get_cursor(commit=True) as (conn, cur):
        # Madrid: POINT(-3.7038 40.4168)
        # Barcelona: POINT(2.1734 41.3851)
        cur.execute("""
            SELECT 
                ST_Distance(
                    ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)::geography,
                    ST_GeomFromText('POINT(2.1734 41.3851)', 4326)::geography
                ) / 1000 AS distancia_km;
        """)
        resultado = cur.fetchone()
        print(f"Distancia Madrid-Barcelona: {resultado['distancia_km']:.2f} km")


def ejemplo_buscar_puntos_cercanos():
    """
    Ejemplo: Buscar puntos cercanos a una ubicación
    Este ejemplo asume que tienes una tabla 'ubicaciones' con una columna 'geom' de tipo geometry
    """
    print("\n=== Ejemplo: Buscar puntos cercanos ===")
    print("(Nota: Requiere una tabla 'ubicaciones' con columna 'geom')")
    
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si existe la tabla
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ubicaciones'
                );
            """)
            existe = cur.fetchone()['exists']
            
            if existe:
                # Punto de referencia (Madrid)
                punto_referencia = "ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)"
                
                cur.execute(f"""
                    SELECT 
                        id,
                        nombre,
                        ST_Distance(
                            geom::geography,
                            {punto_referencia}::geography
                        ) / 1000 AS distancia_km
                    FROM ubicaciones
                    ORDER BY geom <-> {punto_referencia}
                    LIMIT 5;
                """)
                
                resultados = cur.fetchall()
                print(f"Encontrados {len(resultados)} puntos cercanos:")
                for r in resultados:
                    print(f"  - {r.get('nombre', 'Sin nombre')}: {r['distancia_km']:.2f} km")
            else:
                print("La tabla 'ubicaciones' no existe. Puedes crearla con:")
                print("""
                CREATE TABLE ubicaciones (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255),
                    geom GEOMETRY(POINT, 4326)
                );
                
                CREATE INDEX idx_ubicaciones_geom ON ubicaciones USING GIST(geom);
                
                -- Insertar ejemplo
                INSERT INTO ubicaciones (nombre, geom) VALUES
                ('Madrid', ST_GeomFromText('POINT(-3.7038 40.4168)', 4326)),
                ('Barcelona', ST_GeomFromText('POINT(2.1734 41.3851)', 4326));
                """)
                
    except Exception as e:
        print(f"Error: {e}")


def ejemplo_crear_tabla_geoespacial():
    """
    Ejemplo: Crear una tabla con columnas geoespaciales
    """
    print("\n=== Ejemplo: Crear tabla geoespacial ===")
    
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # Crear tabla de campos de golf con ubicación
            cur.execute("""
                CREATE TABLE IF NOT EXISTS campos_golf (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    ubicacion GEOMETRY(POINT, 4326),
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Crear índice espacial para búsquedas rápidas
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campos_golf_ubicacion 
                ON campos_golf USING GIST(ubicacion);
            """)
            
            print("Tabla 'campos_golf' creada exitosamente")
            print("Incluye:")
            print("  - id: Identificador único")
            print("  - nombre: Nombre del campo de golf")
            print("  - ubicacion: Punto geográfico (PostGIS GEOMETRY)")
            print("  - creado_en: Timestamp de creación")
            
    except Exception as e:
        print(f"Error al crear tabla: {e}")


def ejemplo_insertar_datos_geoespaciales():
    """
    Ejemplo: Insertar datos con geometrías
    """
    print("\n=== Ejemplo: Insertar datos geoespaciales ===")
    
    try:
        # Primero crear la tabla si no existe
        ejemplo_crear_tabla_geoespacial()
        
        with Database.get_cursor(commit=True) as (conn, cur):
            # Insertar un campo de golf
            cur.execute("""
                INSERT INTO campos_golf (nombre, ubicacion) VALUES
                ('Campo Las Matas', ST_GeomFromText('POINT(-3.91623 40.54727)', 4326))
                ON CONFLICT DO NOTHING;
            """)
            
            # Verificar inserción
            cur.execute("SELECT COUNT(*) as total FROM campos_golf;")
            total = cur.fetchone()['total']
            print(f"Total de campos de golf en la base de datos: {total}")
            
            # Mostrar los campos
            cur.execute("""
                SELECT 
                    id,
                    nombre,
                    ST_AsText(ubicacion) AS ubicacion_texto,
                    ST_X(ubicacion) AS longitud,
                    ST_Y(ubicacion) AS latitud
                FROM campos_golf;
            """)
            campos = cur.fetchall()
            
            print("\nCampos de golf:")
            for campo in campos:
                print(f"  {campo['nombre']}: ({campo['latitud']}, {campo['longitud']})")
                
    except Exception as e:
        print(f"Error al insertar datos: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Ejemplos de uso de PostgreSQL/PostGIS")
    print("=" * 60)
    
    # Inicializar conexión
    if init_database():
        # Ejecutar ejemplos
        ejemplo_crear_punto()
        ejemplo_calcular_distancia()
        ejemplo_buscar_puntos_cercanos()
        ejemplo_crear_tabla_geoespacial()
        ejemplo_insertar_datos_geoespaciales()
        
        print("\n" + "=" * 60)
        print("Ejemplos completados")
        print("=" * 60)
    else:
        print("Error: No se pudo conectar a la base de datos")
        print("Verifica tu configuración en el archivo .env")

