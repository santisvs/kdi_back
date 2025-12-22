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
    
    def get_hole_by_course_and_number(self, course_id: int, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por course_id y hole_number.
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo (1, 2, 3, etc.)
            
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
                WHERE h.course_id = %s AND h.hole_number = %s;
            """, (course_id, hole_number))
            
            result = cur.fetchone()
            
            if result:
                return dict(result)
            
            return None
    
    def find_terrain_type_by_position(self, hole_id: int, latitude: float, longitude: float) -> Optional[str]:
        """
        Determina el tipo de terreno donde se encuentra una bola según su posición GPS.
        
        Primero verifica si está en el tee (dentro de 10 metros de un punto de tipo 'tee').
        Luego busca en la tabla obstacle si el punto está dentro de algún obstáculo.
        Si hay múltiples obstáculos, devuelve el primero encontrado.
        
        Args:
            hole_id: ID del hoyo donde buscar
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Tipo de terreno ('tee', bunker, water, trees, rough_heavy, out_of_bounds) si se encuentra,
            None si la bola está en terreno normal (fairway/green)
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # PRIMERO: Verificar si está en el tee (dentro de 10 metros de un punto de tipo 'tee')
            cur.execute("""
                SELECT hp.type
                FROM hole_point hp
                WHERE hp.hole_id = %s
                  AND hp.type IN ('tee', 'tee_white', 'tee_yellow')
                  AND hp.position IS NOT NULL
                  AND ST_Distance(
                      hp.position::geography,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                  ) <= 10.0
                LIMIT 1;
            """, (hole_id, longitude, latitude))  # PostGIS usa (lon, lat)
            
            tee_result = cur.fetchone()
            if tee_result:
                return 'tee'
            
            # SEGUNDO: Consulta usando PostGIS para verificar si el punto está dentro de algún obstáculo
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
    
    def get_all_optimal_shots(self, hole_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los golpes óptimos de un hoyo en orden.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los golpes óptimos ordenados
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    os.id,
                    os.hole_id,
                    os.description,
                    ST_AsText(os.path::geometry) AS path_wkt,
                    ST_AsText(ST_StartPoint(os.path::geometry)) AS start_point_wkt,
                    ST_AsText(ST_EndPoint(os.path::geometry)) AS end_point_wkt,
                    ST_X(ST_StartPoint(os.path::geometry)) AS start_lon,
                    ST_Y(ST_StartPoint(os.path::geometry)) AS start_lat,
                    ST_X(ST_EndPoint(os.path::geometry)) AS end_lon,
                    ST_Y(ST_EndPoint(os.path::geometry)) AS end_lat
                FROM optimal_shot os
                WHERE os.hole_id = %s
                  AND os.path IS NOT NULL
                ORDER BY os.id;
            """, (hole_id,))
            
            results = cur.fetchall()
            
            optimal_shots = []
            for result in results:
                optimal_shots.append({
                    'id': result['id'],
                    'hole_id': result['hole_id'],
                    'description': result['description'],
                    'path_wkt': result['path_wkt'],
                    'start_lat': float(result['start_lat']),
                    'start_lon': float(result['start_lon']),
                    'end_lat': float(result['end_lat']),
                    'end_lon': float(result['end_lon'])
                })
            
            return optimal_shots
    
    def find_next_optimal_waypoint(self, hole_id: int, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el siguiente waypoint óptimo desde la posición actual de la bola.
        
        Lógica:
        1. Obtiene todos los optimal_shots del hoyo en orden
        2. Encuentra el punto más cercano en la secuencia de optimal_shots
        3. Determina el siguiente waypoint objetivo (endpoint del optimal_shot actual o flag)
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con información del siguiente waypoint o None si no hay optimal_shots
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Obtener todos los optimal_shots ordenados
            optimal_shots = self.get_all_optimal_shots(hole_id)
            
            if not optimal_shots:
                # Si no hay optimal_shots, el waypoint es la bandera
                cur.execute("""
                    SELECT 
                        ST_X(hp.position::geometry) AS flag_lon,
                        ST_Y(hp.position::geometry) AS flag_lat,
                        ST_Distance(
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                            hp.position
                        ) AS distance_meters
                    FROM hole_point hp
                    WHERE hp.hole_id = %s AND hp.type = 'flag'
                    LIMIT 1;
                """, (longitude, latitude, hole_id))
                
                result = cur.fetchone()
                if result:
                    return {
                        'waypoint_lat': float(result['flag_lat']),
                        'waypoint_lon': float(result['flag_lon']),
                        'distance_to_waypoint': float(result['distance_meters']),
                        'waypoint_description': 'Bandera (sin optimal_shots definidos)',
                        'is_flag': True
                    }
                return None
            
            # Encontrar el optimal_shot más cercano a la posición de la bola
            ball_point = f"POINT({longitude} {latitude})"
            min_distance = float('inf')
            closest_shot_index = 0
            
            for i, shot in enumerate(optimal_shots):
                # Calcular distancia al path del optimal_shot
                cur.execute("""
                    SELECT ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        ST_GeomFromText(%s, 4326)::geography
                    ) AS distance_meters;
                """, (longitude, latitude, shot['path_wkt']))
                
                result = cur.fetchone()
                distance = float(result['distance_meters'])
                
                if distance < min_distance:
                    min_distance = distance
                    closest_shot_index = i
            
            # Determinar el siguiente waypoint
            # Si estamos cerca del optimal_shot, el waypoint es el endpoint de ese shot
            # Si es el último optimal_shot, el waypoint es la bandera
            closest_shot = optimal_shots[closest_shot_index]
            
            # Calcular si la bola está más cerca del inicio o del final del optimal_shot
            cur.execute("""
                SELECT 
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) AS distance_to_start,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) AS distance_to_end;
            """, (
                longitude, latitude, 
                closest_shot['start_lon'], closest_shot['start_lat'],
                longitude, latitude,
                closest_shot['end_lon'], closest_shot['end_lat']
            ))
            
            result = cur.fetchone()
            distance_to_start = float(result['distance_to_start'])
            distance_to_end = float(result['distance_to_end'])
            
            # Si estamos cerca del final del optimal_shot actual, pasar al siguiente
            # Umbral: 20 metros (ajustable)
            if distance_to_end < 20 and closest_shot_index < len(optimal_shots) - 1:
                # Pasar al siguiente optimal_shot
                next_shot = optimal_shots[closest_shot_index + 1]
                return {
                    'waypoint_lat': next_shot['end_lat'],
                    'waypoint_lon': next_shot['end_lon'],
                    'distance_to_waypoint': distance_to_end,
                    'waypoint_description': f'Siguiente punto estratégico: {next_shot["description"]}',
                    'is_flag': False
                }
            
            # Si es el último optimal_shot o estamos lejos del final, el objetivo es el endpoint actual
            # Verificar si el endpoint del último optimal_shot es la bandera
            is_last_shot = closest_shot_index == len(optimal_shots) - 1
            
            if is_last_shot:
                # Verificar si el endpoint está muy cerca de la bandera
                cur.execute("""
                    SELECT 
                        ST_X(hp.position::geometry) AS flag_lon,
                        ST_Y(hp.position::geometry) AS flag_lat,
                        ST_Distance(
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                            hp.position
                        ) AS distance_endpoint_to_flag
                    FROM hole_point hp
                    WHERE hp.hole_id = %s AND hp.type = 'flag'
                    LIMIT 1;
                """, (closest_shot['end_lon'], closest_shot['end_lat'], hole_id))
                
                flag_result = cur.fetchone()
                if flag_result and float(flag_result['distance_endpoint_to_flag']) < 10:
                    # El endpoint es prácticamente la bandera
                    return {
                        'waypoint_lat': float(flag_result['flag_lat']),
                        'waypoint_lon': float(flag_result['flag_lon']),
                        'distance_to_waypoint': distance_to_end,
                        'waypoint_description': 'Bandera',
                        'is_flag': True
                    }
            
            # Waypoint es el endpoint del optimal_shot actual
            return {
                'waypoint_lat': closest_shot['end_lat'],
                'waypoint_lon': closest_shot['end_lon'],
                'distance_to_waypoint': distance_to_end,
                'waypoint_description': f'Punto estratégico: {closest_shot["description"]}',
                'is_flag': is_last_shot
            }
    
    def find_obstacles_between_points(self, hole_id: int, 
                                      from_lat: float, from_lon: float,
                                      to_lat: float, to_lon: float) -> List[Dict[str, Any]]:
        """
        Encuentra los obstáculos que intersectan con la línea entre dos puntos cualesquiera.
        
        Args:
            hole_id: ID del hoyo
            from_lat: Latitud del punto de origen
            from_lon: Longitud del punto de origen
            to_lat: Latitud del punto destino
            to_lon: Longitud del punto destino
            
        Returns:
            Lista de diccionarios con información de los obstáculos encontrados
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    o.id,
                    o.hole_id,
                    o.type,
                    o.name,
                    ST_AsText(o.shape::geometry) AS shape_wkt
                FROM obstacle o
                WHERE o.hole_id = %s
                  AND o.shape IS NOT NULL
                  AND ST_Intersects(
                      o.shape::geometry,
                      ST_MakeLine(
                          ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry,
                          ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry
                      )
                  )
                ORDER BY o.id;
            """, (hole_id, from_lon, from_lat, to_lon, to_lat))  # PostGIS usa (lon, lat)
            
            results = cur.fetchall()
            
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
    
    def get_strategic_points(self, hole_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los puntos estratégicos de un hoyo.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los puntos estratégicos, ordenados por
            distancia a la bandera (más cercanos primero)
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    sp.id,
                    sp.hole_id,
                    sp.type,
                    sp.name,
                    sp.description,
                    sp.distance_to_flag,
                    sp.priority,
                    ST_X(sp.position::geometry) AS longitude,
                    ST_Y(sp.position::geometry) AS latitude
                FROM strategic_point sp
                WHERE sp.hole_id = %s
                ORDER BY sp.distance_to_flag ASC NULLS LAST, sp.priority DESC;
            """, (hole_id,))
            
            results = cur.fetchall()
            
            strategic_points = []
            for result in results:
                strategic_points.append({
                    'id': result['id'],
                    'hole_id': result['hole_id'],
                    'type': result['type'],
                    'name': result['name'],
                    'description': result['description'],
                    'distance_to_flag': result['distance_to_flag'],
                    'priority': result['priority'],
                    'latitude': float(result['latitude']),
                    'longitude': float(result['longitude'])
                })
            
            return strategic_points
    
    def calculate_distance_between_points(self, from_lat: float, from_lon: float,
                                          to_lat: float, to_lon: float) -> float:
        """
        Calcula la distancia entre dos puntos GPS en metros.
        
        Args:
            from_lat: Latitud del punto de origen
            from_lon: Longitud del punto de origen
            to_lat: Latitud del punto destino
            to_lon: Longitud del punto destino
            
        Returns:
            Distancia en metros
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance_meters;
            """, (from_lon, from_lat, to_lon, to_lat))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result and result['distance_meters'] is not None:
                return float(result['distance_meters'])
            
            return 0.0

