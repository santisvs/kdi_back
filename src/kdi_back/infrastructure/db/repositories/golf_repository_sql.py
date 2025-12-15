# -*- coding: utf-8 -*-
"""
Implementación SQL del repositorio de golf usando PostgreSQL/PostGIS.
"""
from typing import Optional, Dict, Any, List
from kdi_back.domain.ports.golf_repository import GolfRepository
from kdi_back.infrastructure.db.database import Database


class GolfRepositorySQL(GolfRepository):
    """
    Implementación concreta del repositorio de golf usando SQL/PostGIS.
    """
    
    def find_hole_by_position(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el hoyo en el que se encuentra una bola según su posición GPS.
        
        Usa PostGIS para verificar si el punto está dentro del polígono del fairway.
        
        Args:
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con la información del hoyo si se encuentra, None si no
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Consulta usando PostGIS para verificar si el punto está dentro del fairway
            # Nota: fairway_polygon es GEOGRAPHY, pero ST_Contains trabaja con GEOMETRY
            # Hacemos cast a geometry para la comparación
            cur.execute("""
                SELECT 
                    h.id,
                    h.course_id,
                    h.hole_number,
                    h.par,
                    h.length,
                    gc.name AS course_name
                FROM hole h
                INNER JOIN golf_course gc ON h.course_id = gc.id
                WHERE h.fairway_polygon IS NOT NULL
                  AND ST_Contains(
                      h.fairway_polygon::geometry,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry
                  )
                LIMIT 1;
            """, (longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result:
                return dict(result)
            
            return None
    
    def get_hole_by_id(self, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por su ID.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con la información del hoyo si existe, None si no
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    h.id,
                    h.course_id,
                    h.hole_number,
                    h.par,
                    h.length,
                    gc.name AS course_name
                FROM hole h
                INNER JOIN golf_course gc ON h.course_id = gc.id
                WHERE h.id = %s;
            """, (hole_id,))
            
            result = cur.fetchone()
            
            if result:
                return dict(result)
            
            return None
    
    def find_terrain_type_by_position(self, hole_id: int, latitude: float, longitude: float) -> Optional[str]:
        """
        Determina el tipo de terreno donde se encuentra una bola según su posición GPS.
        
        Busca en la tabla obstacle si el punto está dentro de algún obstáculo.
        Si hay múltiples obstáculos, devuelve el primero encontrado.
        
        Args:
            hole_id: ID del hoyo donde buscar
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Tipo de terreno (bunker, water, trees, rough_heavy, out_of_bounds) si se encuentra,
            None si la bola está en terreno normal (fairway/green)
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Consulta usando PostGIS para verificar si el punto está dentro de algún obstáculo
            # Nota: shape es GEOGRAPHY(Geometry), pero ST_Contains trabaja con GEOMETRY
            # Hacemos cast a geometry para la comparación
            cur.execute("""
                SELECT o.type
                FROM obstacle o
                WHERE o.hole_id = %s
                  AND o.shape IS NOT NULL
                  AND ST_Contains(
                      o.shape::geometry,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry
                  )
                LIMIT 1;
            """, (hole_id, longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result:
                return result['type']
            
            return None
    
    def calculate_distance_to_hole(self, hole_id: int, latitude: float, longitude: float) -> Optional[float]:
        """
        Calcula la distancia desde la posición de la bola hasta la bandera del hoyo.
        
        Usa PostGIS ST_Distance con geography para calcular la distancia en metros.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Distancia en metros si se encuentra la bandera, None si no
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Consulta usando PostGIS ST_Distance con geography para obtener distancia en metros
            cur.execute("""
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    hp.position
                ) AS distance_meters
                FROM hole_point hp
                WHERE hp.hole_id = %s 
                  AND hp.type = 'flag'
                LIMIT 1;
            """, (longitude, latitude, hole_id))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result and result['distance_meters'] is not None:
                # ST_Distance con geography devuelve metros
                return float(result['distance_meters'])
            
            return None
    
    def find_obstacles_between_ball_and_flag(self, hole_id: int, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Encuentra los obstáculos que intersectan con la línea entre la bola y la bandera.
        
        Usa PostGIS ST_Intersects para verificar si algún obstáculo intersecta con
        la línea recta desde la posición de la bola hasta la bandera.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Lista de diccionarios con información de los obstáculos encontrados
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Buscamos obstáculos que intersecten con la línea bola-bandera
            # Usamos ST_MakeLine para crear la línea y ST_Intersects para verificar intersecciones
            # La subconsulta obtiene la posición de la bandera y la convierte a geometry
            cur.execute("""
                SELECT 
                    o.id,
                    o.hole_id,
                    o.type,
                    o.name,
                    ST_AsText(o.shape::geometry) AS shape_wkt
                FROM obstacle o
                CROSS JOIN LATERAL (
                    SELECT position::geometry AS flag_position
                    FROM hole_point
                    WHERE hole_id = %s AND type = 'flag'
                    LIMIT 1
                ) AS flag
                WHERE o.hole_id = %s
                  AND o.shape IS NOT NULL
                  AND flag.flag_position IS NOT NULL
                  AND ST_Intersects(
                      o.shape::geometry,
                      ST_MakeLine(
                          ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry,
                          flag.flag_position
                      )
                  )
                ORDER BY o.id;
            """, (hole_id, hole_id, longitude, latitude))  # PostGIS usa (lon, lat)
            
            results = cur.fetchall()
            
            # Convertir a lista de diccionarios
            obstacles = []
            for result in results:
                obstacles.append({
                    'id': result['id'],
                    'hole_id': result['hole_id'],
                    'type': result['type'],
                    'name': result['name'],
                    'shape_wkt': result['shape_wkt']
                })
            
            return obstacles
    
    def find_nearest_optimal_shot(self, hole_id: int, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el golpe óptimo más cercano a la posición actual de la bola.
        
        Usa PostGIS ST_Distance para calcular la distancia entre el path (LINESTRING) 
        y el punto de la bola, ordenando por distancia y devolviendo el más cercano.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con información del golpe óptimo más cercano, None si no se encuentra
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Consulta usando PostGIS ST_Distance para encontrar el golpe óptimo más cercano
            # path es GEOGRAPHY(LineString), calculamos distancia con geography para obtener metros
            cur.execute("""
                SELECT 
                    os.id,
                    os.hole_id,
                    os.description,
                    ST_AsText(os.path::geometry) AS path_wkt,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        os.path
                    ) AS distance_meters
                FROM optimal_shot os
                WHERE os.hole_id = %s
                  AND os.path IS NOT NULL
                ORDER BY ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    os.path
                )
                LIMIT 1;
            """, (longitude, latitude, hole_id, longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result:
                return {
                    'id': result['id'],
                    'hole_id': result['hole_id'],
                    'description': result['description'],
                    'path_wkt': result['path_wkt'],
                    'distance_meters': float(result['distance_meters']) if result['distance_meters'] is not None else None
                }
            
            return None

