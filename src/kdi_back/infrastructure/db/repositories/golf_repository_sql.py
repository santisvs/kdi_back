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
        
        Usa una estrategia de detección en cascada:
        1. Primero busca si el punto está dentro del polígono del fairway
        2. Si no encuentra, busca si está dentro del polígono del green
        3. Si aún no encuentra, busca el hoyo más cercano por distancia a la bandera (fallback)
        
        Args:
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con la información del hoyo si se encuentra, None si no
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # ESTRATEGIA 1: Buscar en fairway_polygon
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
            
            # ESTRATEGIA 2: Buscar en green_polygon
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
                WHERE h.green_polygon IS NOT NULL
                  AND ST_Contains(
                      h.green_polygon::geometry,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry
                  )
                LIMIT 1;
            """, (longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            if result:
                return dict(result)
            
            # ESTRATEGIA 3: Fallback - Buscar el hoyo más cercano por distancia a la bandera
            # Si el punto no está dentro de ningún polígono, buscamos el hoyo más cercano
            # dentro de un radio razonable (500 metros)
            cur.execute("""
                SELECT 
                    h.id,
                    h.course_id,
                    h.hole_number,
                    h.par,
                    h.length,
                    gc.name AS course_name,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        hp.position
                    ) AS distance_to_flag
                FROM hole h
                INNER JOIN golf_course gc ON h.course_id = gc.id
                INNER JOIN hole_point hp ON h.id = hp.hole_id
                WHERE hp.type = 'flag'
                  AND hp.position IS NOT NULL
                  AND ST_Distance(
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                      hp.position
                  ) <= 500.0  -- Radio máximo de 500 metros
                ORDER BY distance_to_flag ASC
                LIMIT 1;
            """, (longitude, latitude, longitude, latitude))  # PostGIS usa (lon, lat)
            
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
    
    def get_last_optimal_shot(self, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último optimal_shot de un hoyo (el de mayor shot_number).
        El punto final de este optimal_shot representa el inicio del green.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con información del último optimal_shot, incluyendo:
            - end_lat: Latitud del punto final (inicio del green)
            - end_lon: Longitud del punto final (inicio del green)
            None si no hay optimal_shots
        """
        optimal_shots = self.get_all_optimal_shots(hole_id)
        if not optimal_shots:
            return None
        
        # El último optimal_shot es el último en la lista (ya están ordenados por id)
        # O podemos ordenarlos por shot_number si está disponible
        # Por ahora, asumimos que el último en la lista es el último optimal_shot
        return optimal_shots[-1]
    
    def calculate_distance_to_green_start(self, hole_id: int, latitude: float, longitude: float) -> Optional[float]:
        """
        Calcula la distancia desde la posición de la bola hasta el inicio del green.
        El inicio del green es el punto final del último optimal_shot del hoyo.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Distancia en metros al inicio del green si se encuentra, None si no
        """
        last_optimal_shot = self.get_last_optimal_shot(hole_id)
        if not last_optimal_shot:
            return None
        
        end_lat = last_optimal_shot.get('end_lat')
        end_lon = last_optimal_shot.get('end_lon')
        
        if end_lat is None or end_lon is None:
            return None
        
        # Calcular distancia usando PostGIS
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance_meters
            """, (longitude, latitude, end_lon, end_lat))
            
            result = cur.fetchone()
            if result and result['distance_meters'] is not None:
                return float(result['distance_meters'])
            
            return None
    
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
    
    def is_ball_on_green(self, hole_id: int, latitude: float, longitude: float) -> bool:
        """
        Determina si la bola está en el green.
        
        Verifica si el punto está dentro del polígono green_polygon del hoyo usando PostGIS.
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Consulta usando PostGIS para verificar si el punto está dentro del polígono del green
            # Nota: green_polygon es GEOGRAPHY, pero ST_Contains trabaja con GEOMETRY
            # Hacemos cast a geometry para la comparación
            cur.execute("""
                SELECT 1
                FROM hole h
                WHERE h.id = %s
                  AND h.green_polygon IS NOT NULL
                  AND ST_Contains(
                      h.green_polygon::geometry,
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry
                  );
            """, (hole_id, longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            return result is not None
    
    def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los campos de golf.
        
        Returns:
            Lista de diccionarios con información de los campos (id, name)
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    id,
                    name
                FROM golf_course
                ORDER BY name;
            """)
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def find_nearest_obstacle_by_type(
        self,
        hole_id: int,
        obstacle_type: str,
        latitude: float,
        longitude: float,
        max_distance_meters: float = 100.0
    ) -> Optional[Dict[str, Any]]:
        """
        Encuentra el obstáculo más cercano de un tipo específico cerca de una posición GPS.
        
        Args:
            hole_id: ID del hoyo donde buscar
            obstacle_type: Tipo de obstáculo (trees, bunker, water, rough_heavy, etc.)
            latitude: Latitud GPS aproximada
            longitude: Longitud GPS aproximada
            max_distance_meters: Distancia máxima para buscar (por defecto 100m)
            
        Returns:
            Diccionario con información del obstáculo más cercano y posición corregida
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Buscar obstáculos del tipo especificado cercanos a la posición GPS
            # Calculamos la distancia al polígono y obtenemos el más cercano
            cur.execute("""
                SELECT 
                    o.id,
                    o.hole_id,
                    o.type,
                    o.name,
                    ST_AsText(o.shape::geometry) AS shape_wkt,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        o.shape
                    ) AS distance_meters,
                    ST_X(ST_Centroid(o.shape::geometry)) AS corrected_longitude,
                    ST_Y(ST_Centroid(o.shape::geometry)) AS corrected_latitude
                FROM obstacle o
                WHERE o.hole_id = %s
                  AND o.type = %s
                  AND o.shape IS NOT NULL
                  AND ST_Distance(
                      ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                      o.shape
                  ) <= %s
                ORDER BY ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    o.shape
                )
                LIMIT 1;
            """, (longitude, latitude, hole_id, obstacle_type, longitude, latitude, 
                  max_distance_meters, longitude, latitude))  # PostGIS usa (lon, lat)
            
            result = cur.fetchone()
            
            if result:
                return {
                    'id': result['id'],
                    'hole_id': result['hole_id'],
                    'type': result['type'],
                    'name': result['name'],
                    'corrected_latitude': float(result['corrected_latitude']),
                    'corrected_longitude': float(result['corrected_longitude']),
                    'distance_meters': float(result['distance_meters']),
                    'shape_wkt': result['shape_wkt']
                }
            
            return None
    
    def get_hole_bbox(self, hole_id: int) -> Optional[Dict[str, float]]:
        """
        Obtiene el bbox (bounding box) de un hoyo como min/max lat/lng.
        
        Extrae los valores mínimo y máximo de latitud y longitud del polígono bbox_polygon
        usando PostGIS ST_XMin, ST_XMax, ST_YMin, ST_YMax.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con min_lat, max_lat, min_lng, max_lng si existe bbox,
            None si no existe
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    ST_YMin(bbox_polygon::geometry) AS min_lat,
                    ST_YMax(bbox_polygon::geometry) AS max_lat,
                    ST_XMin(bbox_polygon::geometry) AS min_lng,
                    ST_XMax(bbox_polygon::geometry) AS max_lng
                FROM hole
                WHERE id = %s 
                  AND bbox_polygon IS NOT NULL;
            """, (hole_id,))
            
            result = cur.fetchone()
            
            if result and result['min_lat'] is not None:
                return {
                    'min_lat': float(result['min_lat']),
                    'max_lat': float(result['max_lat']),
                    'min_lng': float(result['min_lng']),
                    'max_lng': float(result['max_lng'])
                }
            
            return None
    
    def get_hole_geometry(self, course_id: int, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene toda la información geométrica de un hoyo para el endpoint de geometría.
        
        Incluye:
        - bbox (bounding box)
        - tees (tee, tee_red, tee_yellow, tee_white)
        - green (polygon y flag)
        - fairway (polygon)
        - obstacles (bunker, water, trees, rough_heavy, out_of_bounds)
        - strategic_points (fairway_center, layup_zone, approach_zone, etc.)
        - optimal_shots (LineStrings)
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            
        Returns:
            Diccionario con toda la geometría del hoyo en formato estructurado,
            None si el hoyo no existe
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # 1. Obtener información básica del hoyo
            cur.execute("""
                SELECT 
                    h.id,
                    h.course_id,
                    h.hole_number,
                    h.par,
                    h.length
                FROM hole h
                WHERE h.course_id = %s AND h.hole_number = %s
                LIMIT 1;
            """, (course_id, hole_number))
            
            hole_result = cur.fetchone()
            if not hole_result:
                return None
            
            hole_id = hole_result['id']
            
            # 2. Obtener bbox
            bbox = self.get_hole_bbox(hole_id)
            
            # 3. Obtener tees (puntos)
            cur.execute("""
                SELECT 
                    type,
                    ST_X(position::geometry) AS longitude,
                    ST_Y(position::geometry) AS latitude
                FROM hole_point
                WHERE hole_id = %s 
                  AND type IN ('tee', 'tee_red', 'tee_yellow', 'tee_white')
                  AND position IS NOT NULL
                ORDER BY 
                    CASE type
                        WHEN 'tee_white' THEN 1
                        WHEN 'tee_yellow' THEN 2
                        WHEN 'tee_red' THEN 3
                        WHEN 'tee' THEN 4
                    END;
            """, (hole_id,))
            
            tees = []
            for row in cur.fetchall():
                tee_type = row['type']
                # Normalizar nombres: tee_red -> red, tee_yellow -> yellow, tee_white -> white, tee -> red (default)
                if tee_type == 'tee_red' or tee_type == 'tee':
                    normalized_type = 'red'
                elif tee_type == 'tee_yellow':
                    normalized_type = 'yellow'
                elif tee_type == 'tee_white':
                    normalized_type = 'white'
                else:
                    normalized_type = 'red'
                
                tees.append({
                    'type': normalized_type,
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                })
            
            # 4. Obtener flag (punto)
            cur.execute("""
                SELECT 
                    ST_X(position::geometry) AS longitude,
                    ST_Y(position::geometry) AS latitude
                FROM hole_point
                WHERE hole_id = %s AND type = 'flag'
                LIMIT 1;
            """, (hole_id,))
            
            flag_result = cur.fetchone()
            flag = None
            if flag_result:
                flag = {
                    'latitude': float(flag_result['latitude']),
                    'longitude': float(flag_result['longitude'])
                }
            
            # 5. Obtener green polygon
            cur.execute("""
                SELECT 
                    ST_AsGeoJSON(green_polygon::geometry)::json AS polygon_geojson
                FROM hole
                WHERE id = %s AND green_polygon IS NOT NULL;
            """, (hole_id,))
            
            green_result = cur.fetchone()
            green_polygon = None
            if green_result and green_result['polygon_geojson']:
                green_polygon = green_result['polygon_geojson']
            
            # 6. Obtener fairway polygon
            cur.execute("""
                SELECT 
                    ST_AsGeoJSON(fairway_polygon::geometry)::json AS polygon_geojson
                FROM hole
                WHERE id = %s AND fairway_polygon IS NOT NULL;
            """, (hole_id,))
            
            fairway_result = cur.fetchone()
            fairway_polygon = None
            if fairway_result and fairway_result['polygon_geojson']:
                fairway_polygon = fairway_result['polygon_geojson']
            
            # 7. Obtener obstacles
            cur.execute("""
                SELECT 
                    id,
                    type,
                    name,
                    ST_AsGeoJSON(shape::geometry)::json AS polygon_geojson
                FROM obstacle
                WHERE hole_id = %s AND shape IS NOT NULL
                ORDER BY type, id;
            """, (hole_id,))
            
            obstacles = []
            for row in cur.fetchall():
                obstacles.append({
                    'id': row['id'],
                    'type': row['type'],
                    'name': row['name'],
                    'polygon': row['polygon_geojson']
                })
            
            # 8. Obtener strategic_points
            strategic_points = self.get_strategic_points(hole_id)
            # Convertir a formato GeoJSON Point
            strategic_points_formatted = []
            for sp in strategic_points:
                strategic_points_formatted.append({
                    'id': sp['id'],
                    'type': sp['type'],
                    'name': sp['name'],
                    'description': sp.get('description'),
                    'distance_to_flag': sp.get('distance_to_flag'),
                    'priority': sp.get('priority'),
                    'point': {
                        'type': 'Point',
                        'coordinates': [sp['longitude'], sp['latitude']]
                    }
                })
            
            # 9. Obtener optimal_shots
            optimal_shots_raw = self.get_all_optimal_shots(hole_id)
            optimal_shots = []
            for shot in optimal_shots_raw:
                # Convertir WKT LineString a GeoJSON
                cur.execute("""
                    SELECT ST_AsGeoJSON(path::geometry)::json AS linestring_geojson
                    FROM optimal_shot
                    WHERE id = %s;
                """, (shot['id'],))
                
                shot_geom = cur.fetchone()
                if shot_geom and shot_geom['linestring_geojson']:
                    optimal_shots.append({
                        'id': shot['id'],
                        'description': shot['description'],
                        'linestring': shot_geom['linestring_geojson']
                    })
            
            # Construir respuesta
            result = {
                'hole_id': hole_id,
                'course_id': course_id,
                'hole_number': hole_number,
                'par': hole_result['par'],
                'length': hole_result['length'],
                'bbox': bbox,
                'tees': tees,
                'green': {
                    'flag': flag,
                    'polygon': green_polygon
                },
                'fairway': {
                    'polygon': fairway_polygon
                },
                'obstacles': obstacles,
                'strategic_points': strategic_points_formatted,
                'optimal_shots': optimal_shots
            }
            
            return result

