# -*- coding: utf-8 -*-
"""
Servicio de dominio para lógica de negocio relacionada con golf.

Contiene los casos de uso del dominio sin depender de implementaciones técnicas.
"""
from typing import Optional, Dict, Any, List
from kdi_back.domain.ports.golf_repository import GolfRepository


class GolfService:
    """
    Servicio de dominio para operaciones de golf.
    
    Contiene la lógica de negocio pura, sin dependencias técnicas.
    """
    
    def __init__(self, golf_repository: GolfRepository):
        """
        Inicializa el servicio con un repositorio.
        
        Args:
            golf_repository: Implementación del repositorio de golf
        """
        self.golf_repository = golf_repository
    
    def identify_hole_by_ball_position(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Identifica en qué hoyo se encuentra una bola según su posición GPS.
        
        Esta es la lógica de negocio: "identificar el hoyo de una bola".
        La implementación técnica (SQL, PostGIS) está en el repositorio.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            
        Returns:
            Diccionario con información del hoyo si se encuentra, None si no
            
        Raises:
            ValueError: Si las coordenadas no son válidas
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        # Delegar al repositorio (implementación técnica)
        hole = self.golf_repository.find_hole_by_position(latitude, longitude)
        
        return hole
    
    def get_hole_by_id(self, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por su ID.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con información del hoyo si existe, None si no
            
        Raises:
            ValueError: Si hole_id no es válido
        """
        # Validación de negocio
        if hole_id <= 0:
            raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Delegar al repositorio (implementación técnica)
        hole = self.golf_repository.get_hole_by_id(hole_id)
        
        return hole
    
    def get_hole_by_course_and_number(self, course_id: int, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por course_id y hole_number.
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo (1, 2, 3, etc.)
            
        Returns:
            Diccionario con información del hoyo si existe, None si no
            
        Raises:
            ValueError: Si course_id o hole_number no son válidos
        """
        # Validación de negocio
        if course_id <= 0:
            raise ValueError(f"course_id debe ser un número positivo, recibido: {course_id}")
        
        if hole_number <= 0:
            raise ValueError(f"hole_number debe ser un número positivo, recibido: {hole_number}")
        
        # Delegar al repositorio (implementación técnica)
        hole = self.golf_repository.get_hole_by_course_and_number(course_id, hole_number)
        
        return hole
    
    def _get_hole_id_from_course_and_number(self, course_id: Optional[int], hole_number: Optional[int]) -> Optional[int]:
        """
        Método helper interno para obtener hole_id desde course_id y hole_number.
        
        Args:
            course_id: ID del campo de golf (opcional)
            hole_number: Número del hoyo (opcional)
            
        Returns:
            hole_id si se encuentra, None si no
        """
        if course_id is None or hole_number is None:
            return None
        
        hole = self.get_hole_by_course_and_number(course_id, hole_number)
        if hole:
            return hole['id']
        return None
    
    def determine_terrain_type(self, latitude: float, longitude: float, hole_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Determina el tipo de terreno donde se encuentra una bola según su posición GPS.
        
        Si no se proporciona hole_id, primero identifica el hoyo automáticamente.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
            
        Returns:
            Diccionario con:
            - terrain_type: Tipo de terreno encontrado o None si es terreno normal
            - hole_id: ID del hoyo usado para la búsqueda
            - hole_info: Información del hoyo (si se identificó automáticamente)
            
        Raises:
            ValueError: Si las coordenadas no son válidas o no se encuentra el hoyo
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        # Si no se proporciona hole_id, identificarlo primero
        hole_info = None
        if hole_id is None:
            hole = self.golf_repository.find_hole_by_position(latitude, longitude)
            if not hole:
                raise ValueError(f"No se encontró ningún hoyo en la posición ({latitude}, {longitude})")
            hole_id = hole['id']
            hole_info = hole
        else:
            # Validar que hole_id sea positivo
            if hole_id <= 0:
                raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Buscar el tipo de terreno
        terrain_type = self.golf_repository.find_terrain_type_by_position(hole_id, latitude, longitude)
        
        result = {
            "terrain_type": terrain_type,
            "hole_id": hole_id,
        }
        
        if hole_info:
            result["hole_info"] = hole_info
        
        return result
    
    def calculate_distance_to_hole(self, latitude: float, longitude: float, hole_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calcula la distancia desde la posición de la bola hasta la bandera del hoyo.
        
        Si no se proporciona hole_id, primero identifica el hoyo automáticamente.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
            
        Returns:
            Diccionario con:
            - distance_meters: Distancia en metros hasta la bandera
            - distance_yards: Distancia en yardas (conversión aproximada)
            - hole_id: ID del hoyo usado para el cálculo
            - hole_info: Información del hoyo (si se identificó automáticamente)
            
        Raises:
            ValueError: Si las coordenadas no son válidas, no se encuentra el hoyo o la bandera
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        # Si no se proporciona hole_id, identificarlo primero
        hole_info = None
        if hole_id is None:
            hole = self.golf_repository.find_hole_by_position(latitude, longitude)
            if not hole:
                raise ValueError(f"No se encontró ningún hoyo en la posición ({latitude}, {longitude})")
            hole_id = hole['id']
            hole_info = hole
        else:
            # Validar que hole_id sea positivo
            if hole_id <= 0:
                raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Calcular la distancia
        distance_meters = self.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        
        if distance_meters is None:
            raise ValueError(f"No se encontró la bandera para el hoyo {hole_id}")
        
        # Convertir a yardas (1 metro ≈ 1.09361 yardas)
        distance_yards = distance_meters * 1.09361
        
        result = {
            "distance_meters": round(distance_meters, 2),
            "distance_yards": round(distance_yards, 2),
            "hole_id": hole_id,
        }
        
        if hole_info:
            result["hole_info"] = hole_info
        
        return result
    
    def find_obstacles_between_ball_and_flag(self, latitude: float, longitude: float, hole_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Encuentra los obstáculos que intersectan con la línea entre la bola y la bandera.
        
        Si no se proporciona hole_id, primero identifica el hoyo automáticamente.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
            
        Returns:
            Diccionario con:
            - obstacles: Lista de obstáculos encontrados
            - obstacle_count: Número de obstáculos encontrados
            - hole_id: ID del hoyo usado para la búsqueda
            - hole_info: Información del hoyo (si se identificó automáticamente)
            
        Raises:
            ValueError: Si las coordenadas no son válidas o no se encuentra el hoyo
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        # Si no se proporciona hole_id, identificarlo primero
        hole_info = None
        if hole_id is None:
            hole = self.golf_repository.find_hole_by_position(latitude, longitude)
            if not hole:
                raise ValueError(f"No se encontró ningún hoyo en la posición ({latitude}, {longitude})")
            hole_id = hole['id']
            hole_info = hole
        else:
            # Validar que hole_id sea positivo
            if hole_id <= 0:
                raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Buscar obstáculos
        obstacles = self.golf_repository.find_obstacles_between_ball_and_flag(hole_id, latitude, longitude)
        
        result = {
            "obstacles": obstacles,
            "obstacle_count": len(obstacles),
            "hole_id": hole_id,
        }
        
        if hole_info:
            result["hole_info"] = hole_info
        
        return result
    
    def find_nearest_optimal_shot(self, latitude: float, longitude: float, hole_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Encuentra el golpe óptimo más cercano a la posición actual de la bola.
        
        Si no se proporciona hole_id, primero identifica el hoyo automáticamente.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
            
        Returns:
            Diccionario con:
            - optimal_shot: Información del golpe óptimo más cercano
            - distance_meters: Distancia en metros desde la bola hasta el path del golpe óptimo
            - distance_yards: Distancia en yardas (conversión aproximada)
            - hole_id: ID del hoyo usado para la búsqueda
            - hole_info: Información del hoyo (si se identificó automáticamente)
            
        Raises:
            ValueError: Si las coordenadas no son válidas, no se encuentra el hoyo o no hay golpes óptimos
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        # Si no se proporciona hole_id, identificarlo primero
        hole_info = None
        if hole_id is None:
            hole = self.golf_repository.find_hole_by_position(latitude, longitude)
            if not hole:
                raise ValueError(f"No se encontró ningún hoyo en la posición ({latitude}, {longitude})")
            hole_id = hole['id']
            hole_info = hole
        else:
            # Validar que hole_id sea positivo
            if hole_id <= 0:
                raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Buscar el golpe óptimo más cercano
        optimal_shot = self.golf_repository.find_nearest_optimal_shot(hole_id, latitude, longitude)
        
        if optimal_shot is None:
            raise ValueError(f"No se encontraron golpes óptimos para el hoyo {hole_id}")
        
        # Extraer distancia y convertir a yardas
        distance_meters = optimal_shot.get('distance_meters')
        distance_yards = None
        if distance_meters is not None:
            distance_yards = distance_meters * 1.09361  # 1 metro ≈ 1.09361 yardas
        
        result = {
            "optimal_shot": {
                "id": optimal_shot['id'],
                "hole_id": optimal_shot['hole_id'],
                "description": optimal_shot['description'],
                "path_wkt": optimal_shot['path_wkt']
            },
            "distance_meters": round(distance_meters, 2) if distance_meters is not None else None,
            "distance_yards": round(distance_yards, 2) if distance_yards is not None else None,
            "hole_id": hole_id,
        }
        
        if hole_info:
            result["hole_info"] = hole_info
        
        return result
    
    def _get_max_accessible_distance(self, player_club_statistics: Optional[List[Dict[str, Any]]] = None) -> float:
        """
        Obtiene la distancia máxima accesible del jugador.
        
        Args:
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            
        Returns:
            Distancia máxima en metros que el jugador puede alcanzar
        """
        # Distancia máxima por defecto (Driver estándar)
        DEFAULT_MAX_DISTANCE = 250.0
        
        if not player_club_statistics or len(player_club_statistics) == 0:
            return DEFAULT_MAX_DISTANCE
        
        # Buscar la distancia máxima entre todas las estadísticas
        max_distance = 0.0
        for stat in player_club_statistics:
            # Usar max_distance_meters si está disponible, sino average_distance_meters
            distance = stat.get('max_distance_meters') or stat.get('average_distance_meters', 0)
            if distance > max_distance:
                max_distance = distance
        
        # Si no se encontró ninguna distancia, usar el valor por defecto
        if max_distance == 0:
            return DEFAULT_MAX_DISTANCE
        
        return float(max_distance)
    
    def evaluate_shot_trajectories(self, latitude: float, longitude: float, hole_id: int,
                                   player_club_statistics: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Evalúa múltiples trayectorias de golpe según el algoritmo basado en riesgo numérico:
        
        ALGORITMO:
        PASO 0: Verificar optimal_shot
           - Buscar optimal_shots cuyo inicio esté a menos de 10m de la bola
           - Si hay exactamente 1: usar su endpoint como punto estratégico prioritario
           - Si hay múltiples: desestimar optimal_shots (error) y continuar normal
        
        1. Si distancia al green es alcanzable:
           - Calcular riesgo de trayectoria directa al green
           - Si riesgo < 75: directa al green → ÓPTIMA
              - Si hay optimal_shot válido: optimal_shot → CONSERVADORA
           - Si riesgo ≥ 75: buscar optimal_shot o strategic_points
        2. Si distancia al green NO es alcanzable:
           - Si hay optimal_shot válido: usarlo como óptima
           - Si no: buscar strategic_point más cercano al green
        3. Si el riesgo del optimal_shot > 75:
           - Descartar optimal_shot y buscar solo strategic_points
        4. Si no se encuentra ninguna trayectoria con riesgo ≤ 75:
           - Ofrecer mensaje: "Juega un hierro rodado y busca la calle"
        5. Trayectoria conservadora:
           - Solo buscar si la óptima tiene riesgo entre 30-75
           - Buscar cualquier strategic_point con riesgo < 30
           - Si encontramos uno con riesgo < 30: intercambiar roles (nuevo = óptima, anterior = conservadora)
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            
        Returns:
            Diccionario con:
            - direct_trajectory: Información de la trayectoria óptima (o mensaje de hierro rodado)
            - conservative_trajectory: Información de la trayectoria conservadora (si aplica)
            - recommended_trajectory: 'direct' o 'conservative' según el análisis de riesgo
            
        Raises:
            ValueError: Si las coordenadas no son válidas o no se encuentra el hoyo
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}. Debe estar entre -90 y 90.")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}. Debe estar entre -180 y 180.")
        
        if hole_id <= 0:
            raise ValueError(f"hole_id debe ser un número positivo, recibido: {hole_id}")
        
        # Obtener distancia máxima accesible del jugador
        max_distance = self._get_max_accessible_distance(player_club_statistics)
        
        # Obtener terreno donde está la bola
        terrain_type_at_ball = self.golf_repository.find_terrain_type_by_position(
            hole_id, latitude, longitude
        )
        
        # Calcular distancia directa a la bandera
        distance_to_flag = self.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        if distance_to_flag is None:
            raise ValueError(f"No se encontró la bandera para el hoyo {hole_id}")
        
        # Obtener todos los strategic_points del hoyo (ordenados por distance_to_flag ASC - más cercano al green primero)
        strategic_points = self.golf_repository.get_strategic_points(hole_id)
        
        # ===== VERIFICAR SI DISTANCIA AL GREEN ES ALCANZABLE =====
        is_green_reachable = distance_to_flag <= max_distance
        
        # ===== BUSCAR TRAYECTORIA ÓPTIMA =====
        direct_trajectory = None
        conservative_trajectory = None
        optimal_strategic_point = None
        should_search_conservative = False  # Flag para indicar si buscar conservadora
        optimal_shot_is_final = False  # Flag para indicar si optimal_shot con riesgo ≤ 30 es la óptima final
        
        # ===== CASO 1: VERIFICAR OPTIMAL_SHOT =====
        optimal_shots = self.golf_repository.get_all_optimal_shots(hole_id)
        optimal_shots_near_start = []
        
        for optimal_shot in optimal_shots:
            distance_to_start = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                optimal_shot['start_lat'], optimal_shot['start_lon']
            )
            if distance_to_start <= 10.0:  # Menos o igual a 10 metros
                optimal_shots_near_start.append(optimal_shot)
        
        # Si hay exactamente 1 optimal_shot a menos de 10m, evaluarlo
        if len(optimal_shots_near_start) == 1:
            optimal_shot = optimal_shots_near_start[0]
            optimal_shot_endpoint = {
                'latitude': optimal_shot['end_lat'],
                'longitude': optimal_shot['end_lon'],
                'description': optimal_shot.get('description', 'Endpoint de optimal_shot')
            }
            
            # Calcular distancia desde la bola al endpoint del optimal_shot
            distance_to_optimal_endpoint = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                optimal_shot_endpoint['latitude'], optimal_shot_endpoint['longitude']
            )
            
            # Solo considerar si es alcanzable
            if distance_to_optimal_endpoint <= max_distance:
                # Evaluar obstáculos en la trayectoria al endpoint del optimal_shot
                obstacles_optimal = self.golf_repository.find_obstacles_between_points(
                    hole_id,
                    latitude, longitude,
                    optimal_shot_endpoint['latitude'], optimal_shot_endpoint['longitude']
                )
                
                # Calcular recomendación de palo
                club_rec_optimal = self.calculate_club_recommendation(
                    distance_meters=distance_to_optimal_endpoint,
                    player_club_statistics=player_club_statistics
                )
                
                # Calcular riesgo numérico completo
                numeric_risk_optimal = self._calculate_risk_score_detailed(
                    obstacles=obstacles_optimal,
                    distance_to_target=distance_to_optimal_endpoint,
                    target_type="waypoint",
                    terrain_type=terrain_type_at_ball,
                    recommended_club=club_rec_optimal.get("recommended_club"),
                    player_club_statistics=player_club_statistics
                )
                
                risk_optimal_total = numeric_risk_optimal["total"]
                
                # CASO 1: Evaluar según riesgo del optimal_shot
                if risk_optimal_total > 75.0:
                    # Descartar esta trayectoria y pasar al Caso 2
                    pass  # No hacer nada, continuar con Caso 2
                elif 30.0 < risk_optimal_total <= 75.0:
                    # Ofrecer como óptima y pasar al Caso 2
                    direct_trajectory = {
                        "distance_meters": round(distance_to_optimal_endpoint, 2),
                        "distance_yards": round(distance_to_optimal_endpoint * 1.09361, 2),
                        "target": "waypoint",
                        "waypoint_description": optimal_shot_endpoint['description'],
                        "obstacles": [
                            {
                                'id': obs.get('id'),
                                'type': obs.get('type'),
                                'name': obs.get('name')
                            }
                            for obs in obstacles_optimal
                        ],
                        "obstacle_count": len(obstacles_optimal),
                        "risk_level": numeric_risk_optimal,
                        "description": f"Trayectoria a optimal_shot: {optimal_shot_endpoint['description']}",
                        "numeric_risk": numeric_risk_optimal
                    }
                    should_search_conservative = True  # Buscar conservadora después
                elif risk_optimal_total <= 30.0:
                    # Ofrecer como óptima + NO buscar conservadora
                    # IMPORTANTE: Si optimal_shot tiene riesgo ≤ 30, NO buscar otras trayectorias
                    direct_trajectory = {
                        "distance_meters": round(distance_to_optimal_endpoint, 2),
                        "distance_yards": round(distance_to_optimal_endpoint * 1.09361, 2),
                        "target": "waypoint",
                        "waypoint_description": optimal_shot_endpoint['description'],
                        "obstacles": [
                            {
                                'id': obs.get('id'),
                                'type': obs.get('type'),
                                'name': obs.get('name')
                            }
                            for obs in obstacles_optimal
                        ],
                        "obstacle_count": len(obstacles_optimal),
                        "risk_level": numeric_risk_optimal,
                        "description": f"Trayectoria a optimal_shot: {optimal_shot_endpoint['description']}",
                        "numeric_risk": numeric_risk_optimal
                    }
                    should_search_conservative = False  # NO buscar conservadora
                    optimal_shot_is_final = True  # Marcar que optimal_shot es la óptima final, no buscar más
        
        # ===== CASO 2: DISTANCIA AL GREEN ES ALCANZABLE =====
        # Solo ejecutar si NO hay optimal_shot con riesgo ≤ 30 (que ya sería la óptima final)
        if is_green_reachable and not optimal_shot_is_final:
            # Evaluar trayectoria directa al green (flag)
            obstacles_direct_flag = self.golf_repository.find_obstacles_between_ball_and_flag(hole_id, latitude, longitude)
            club_rec_flag = self.calculate_club_recommendation(
                distance_meters=distance_to_flag,
                player_club_statistics=player_club_statistics
            )
            numeric_risk_flag = self._calculate_risk_score_detailed(
                obstacles=obstacles_direct_flag,
                distance_to_target=distance_to_flag,
                target_type="flag",
                terrain_type=terrain_type_at_ball,
                recommended_club=club_rec_flag.get("recommended_club"),
                player_club_statistics=player_club_statistics
            )
            
            risk_flag_total = numeric_risk_flag["total"]
            trajectory_flag = {
                "distance_meters": round(distance_to_flag, 2),
                "distance_yards": round(distance_to_flag * 1.09361, 2),
                "target": "flag",
                "obstacles": [
                    {
                        'id': obs.get('id'),
                        'type': obs.get('type'),
                        'name': obs.get('name')
                    }
                    for obs in obstacles_direct_flag
                ],
                "obstacle_count": len(obstacles_direct_flag),
                "risk_level": numeric_risk_flag,
                "description": "Trayectoria directa a la bandera",
                "numeric_risk": numeric_risk_flag
            }
            
            # Si riesgo ≤ 75
            if risk_flag_total <= 75.0:
                has_existing_optimal = direct_trajectory is not None
                
                if 30.0 < risk_flag_total <= 75.0:
                    if not has_existing_optimal:
                        # Ofrecer como óptima + Buscar conservadora
                        direct_trajectory = trajectory_flag
                        should_search_conservative = True
                    else:
                        # Pasar la óptima existente a conservadora + Ofrecer como óptima
                        conservative_trajectory = direct_trajectory
                        direct_trajectory = trajectory_flag
                        should_search_conservative = True
                elif risk_flag_total <= 30.0:
                    if not has_existing_optimal:
                        # Ofrecer como óptima + NO buscar conservadora
                        direct_trajectory = trajectory_flag
                        should_search_conservative = False
                    else:
                        # Pasar la óptima existente a conservadora + Ofrecer como óptima
                        conservative_trajectory = direct_trajectory
                        direct_trajectory = trajectory_flag
                        should_search_conservative = False
            # Si riesgo > 75
            else:
                # Buscar strategic_point más cercano al green
                for point in strategic_points:
                    distance_to_point = self.golf_repository.calculate_distance_between_points(
                        latitude, longitude,
                        point['latitude'], point['longitude']
                    )
                    
                    if distance_to_point > max_distance:
                        continue
                    
                    obstacles = self.golf_repository.find_obstacles_between_points(
                        hole_id,
                        latitude, longitude,
                        point['latitude'], point['longitude']
                    )
                    
                    club_rec = self.calculate_club_recommendation(
                        distance_meters=distance_to_point,
                        player_club_statistics=player_club_statistics
                    )
                    
                    numeric_risk = self._calculate_risk_score_detailed(
                        obstacles=obstacles,
                        distance_to_target=distance_to_point,
                        target_type="waypoint",
                        terrain_type=terrain_type_at_ball,
                        recommended_club=club_rec.get("recommended_club"),
                        player_club_statistics=player_club_statistics
                    )
                    
                    risk_total = numeric_risk["total"]
                    
                    # Si encontramos uno con riesgo < 75
                    if risk_total <= 75.0:
                        trajectory_point = {
                            "distance_meters": round(distance_to_point, 2),
                            "distance_yards": round(distance_to_point * 1.09361, 2),
                            "target": "waypoint",
                            "waypoint_description": point.get('description') or point.get('name', 'Punto estratégico'),
                            "obstacles": [
                                {
                                    'id': obs.get('id'),
                                    'type': obs.get('type'),
                                    'name': obs.get('name')
                                }
                                for obs in obstacles
                            ],
                            "obstacle_count": len(obstacles),
                            "risk_level": numeric_risk,
                            "description": f"Trayectoria a punto estratégico: {point.get('name', 'Punto estratégico')}",
                            "numeric_risk": numeric_risk
                        }
                        
                        has_existing_optimal = direct_trajectory is not None
                        
                        if 30.0 < risk_total <= 75.0:
                            if not has_existing_optimal:
                                # Ofrecer como óptima + Buscar conservadora
                                direct_trajectory = trajectory_point
                                should_search_conservative = True
                            else:
                                # Pasar la óptima existente a conservadora + Ofrecer como óptima
                                conservative_trajectory = direct_trajectory
                                direct_trajectory = trajectory_point
                                should_search_conservative = True
                        elif risk_total <= 30.0:
                            if not has_existing_optimal:
                                # Ofrecer como óptima + NO buscar conservadora
                                direct_trajectory = trajectory_point
                                should_search_conservative = False
                            else:
                                # Pasar la óptima existente a conservadora + Ofrecer como óptima
                                conservative_trajectory = direct_trajectory
                                direct_trajectory = trajectory_point
                                should_search_conservative = False
                        
                        optimal_strategic_point = point
                        break
        else:
            # ===== CASO 3: DISTANCIA AL GREEN NO ES ALCANZABLE =====
            # Solo ejecutar si NO hay optimal_shot con riesgo ≤ 30 (que ya sería la óptima final)
            if not optimal_shot_is_final:
                # Buscar strategic_point más cercano al green
                for point in strategic_points:
                    distance_to_point = self.golf_repository.calculate_distance_between_points(
                        latitude, longitude,
                        point['latitude'], point['longitude']
                    )
                    
                    if distance_to_point > max_distance:
                        continue
                    
                    obstacles = self.golf_repository.find_obstacles_between_points(
                        hole_id,
                        latitude, longitude,
                        point['latitude'], point['longitude']
                    )
                    
                    club_rec = self.calculate_club_recommendation(
                        distance_meters=distance_to_point,
                        player_club_statistics=player_club_statistics
                    )
                    
                    numeric_risk = self._calculate_risk_score_detailed(
                        obstacles=obstacles,
                        distance_to_target=distance_to_point,
                        target_type="waypoint",
                        terrain_type=terrain_type_at_ball,
                        recommended_club=club_rec.get("recommended_club"),
                        player_club_statistics=player_club_statistics
                    )
                    
                    risk_total = numeric_risk["total"]
                    
                    # Si riesgo > 75, continuar iterando
                    if risk_total > 75.0:
                        continue
                    
                    # Si riesgo ≤ 75
                    trajectory_point = {
                        "distance_meters": round(distance_to_point, 2),
                        "distance_yards": round(distance_to_point * 1.09361, 2),
                        "target": "waypoint",
                        "waypoint_description": point.get('description') or point.get('name', 'Punto estratégico'),
                        "obstacles": [
                            {
                                'id': obs.get('id'),
                                'type': obs.get('type'),
                                'name': obs.get('name')
                            }
                            for obs in obstacles
                        ],
                        "obstacle_count": len(obstacles),
                        "risk_level": numeric_risk,
                        "description": f"Trayectoria a punto estratégico: {point.get('name', 'Punto estratégico')}",
                        "numeric_risk": numeric_risk
                    }
                    
                    has_existing_optimal = direct_trajectory is not None
                    
                    if 30.0 < risk_total <= 75.0:
                        if not has_existing_optimal:
                            # Ofrecer como óptima + Buscar conservadora
                            direct_trajectory = trajectory_point
                            should_search_conservative = True
                        else:
                            # Pasar la óptima existente a conservadora + Ofrecer como óptima
                            conservative_trajectory = direct_trajectory
                            direct_trajectory = trajectory_point
                            should_search_conservative = True
                    elif risk_total <= 30.0:
                        if not has_existing_optimal:
                            # Ofrecer como óptima + NO buscar conservadora
                            direct_trajectory = trajectory_point
                            should_search_conservative = False
                        else:
                            # Pasar la óptima existente a conservadora + Ofrecer como óptima
                            conservative_trajectory = direct_trajectory
                            direct_trajectory = trajectory_point
                            should_search_conservative = False
                    
                    optimal_strategic_point = point
                    break
        
        # Si no encontramos ninguna trayectoria con riesgo ≤ 75, ofrecer mensaje de hierro rodado
        if direct_trajectory is None:
            direct_trajectory = {
                "distance_meters": None,
                "distance_yards": None,
                "target": None,
                "obstacles": [],
                "obstacle_count": 0,
                "risk_level": None,
                "description": "Juega un hierro rodado y busca la calle",
                "numeric_risk": None,
                "special_message": "Juega un hierro rodado y busca la calle"
            }
        
        # ===== BUSCAR TRAYECTORIA CONSERVADORA =====
        # Si la trayectoria óptima es el mensaje de hierro rodado, no buscar conservadora
        if direct_trajectory.get("special_message"):
            conservative_trajectory = None
        # Si should_search_conservative es True, buscar conservadora
        elif should_search_conservative:
            # Buscar CUALQUIER strategic_point con riesgo < 30
            # Si encontramos uno, intercambiar roles (nuevo = óptima, anterior = conservadora)
            better_trajectory = None
            
            for point in strategic_points:
                # Calcular distancia desde la bola al punto
                distance_to_point = self.golf_repository.calculate_distance_between_points(
                    latitude, longitude,
                    point['latitude'], point['longitude']
                )
                
                # Solo considerar puntos alcanzables
                if distance_to_point > max_distance:
                    continue
                
                # Evaluar obstáculos
                obstacles = self.golf_repository.find_obstacles_between_points(
                    hole_id,
                    latitude, longitude,
                    point['latitude'], point['longitude']
                )
                
                # Calcular recomendación de palo
                club_rec_cons = self.calculate_club_recommendation(
                    distance_meters=distance_to_point,
                    player_club_statistics=player_club_statistics
                )
                
                # Calcular riesgo numérico completo
                numeric_risk_cons = self._calculate_risk_score_detailed(
                    obstacles=obstacles,
                    distance_to_target=distance_to_point,
                    target_type="waypoint",
                    terrain_type=terrain_type_at_ball,
                    recommended_club=club_rec_cons.get("recommended_club"),
                    player_club_statistics=player_club_statistics
                )
                
                risk_total_cons = numeric_risk_cons["total"]
                
                # Si encontramos una con riesgo < 30, guardarla
                if risk_total_cons < 30.0:
                    better_trajectory = {
                        "distance_meters": round(distance_to_point, 2),
                        "distance_yards": round(distance_to_point * 1.09361, 2),
                        "target": "waypoint",
                        "waypoint_description": point.get('description') or point.get('name', 'Punto estratégico'),
                        "obstacles": [
                            {
                                'id': obs.get('id'),
                                'type': obs.get('type'),
                                'name': obs.get('name')
                            }
                            for obs in obstacles
                        ],
                        "obstacle_count": len(obstacles),
                        "risk_level": numeric_risk_cons,
                        "description": f"Trayectoria a punto estratégico: {point.get('name', 'Punto estratégico')}",
                        "numeric_risk": numeric_risk_cons
                    }
                    break
            
            # Si encontramos una trayectoria mejor (riesgo < 30), intercambiar roles
            if better_trajectory:
                # La nueva trayectoria (riesgo < 30) se convierte en óptima
                # La anterior óptima (riesgo 30-75) se convierte en conservadora
                if conservative_trajectory is None:
                    conservative_trajectory = direct_trajectory
                direct_trajectory = better_trajectory
        
        # ===== Determinar trayectoria recomendada =====
        recommended = "direct"
        
        # Si la trayectoria óptima es el mensaje de hierro rodado, siempre recomendar directa
        if direct_trajectory.get("special_message"):
            recommended = "direct"
        elif conservative_trajectory:
            r_direct = direct_trajectory.get("numeric_risk", {}).get("total", float('inf'))
            r_cons = conservative_trajectory.get("numeric_risk", {}).get("total", float('inf'))
            
            # Si la directa tiene riesgo entre 30 y 75 y la conservadora es < 30, recomendar conservadora
            if 30.0 <= r_direct <= 75.0 and r_cons < 30.0:
                recommended = "conservative"
            # Si ambas están disponibles, preferir la de menor riesgo (siempre que sea <= 75)
            elif r_direct <= 75.0 and r_cons <= 75.0:
                recommended = "conservative" if r_cons < r_direct else "direct"
            # Si solo una está <= 75, elegir esa
            elif r_cons <= 75.0:
                recommended = "conservative"
            elif r_direct <= 75.0:
                recommended = "direct"
            # Si ambas superan 75, elegir la menos mala
            else:
                recommended = "conservative" if r_cons < r_direct else "direct"
        
        result = {
            "direct_trajectory": direct_trajectory,
            "conservative_trajectory": conservative_trajectory,
            "recommended_trajectory": recommended,
            "hole_id": hole_id,
        }
        
        return result
    
    def _find_conservative_trajectory_to_green(self, latitude: float, longitude: float, hole_id: int,
                                                strategic_points: List[Dict[str, Any]], max_distance: float) -> Optional[Dict[str, Any]]:
        """
        Busca una trayectoria conservadora (riesgo bajo) hacia el green desde strategic_points.
        
        Args:
            latitude: Latitud de la bola
            longitude: Longitud de la bola
            hole_id: ID del hoyo
            strategic_points: Lista de puntos estratégicos
            max_distance: Distancia máxima accesible
            
        Returns:
            Diccionario con información de la trayectoria conservadora o None
        """
        best_option = None
        best_score = -1
        
        for point in strategic_points:
            # Calcular distancia desde la bola al punto
            distance_to_point = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            
            # Solo considerar puntos alcanzables
            if distance_to_point > max_distance:
                continue
            
            # Evaluar obstáculos
            obstacles = self.golf_repository.find_obstacles_between_points(
                hole_id,
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            risk_level = self._calculate_risk_level(obstacles)
            
            # Solo considerar opciones de riesgo bajo
            if risk_level != 'low':
                continue
            
            # Calcular score: priorizar puntos más cercanos al green (menor distance_to_flag)
            # y con mayor prioridad
            distance_to_flag = point.get('distance_to_flag', float('inf'))
            priority = point.get('priority', 0)
            
            # Score: inverso de distancia al green + prioridad (mayor es mejor)
            score = priority * 10 - distance_to_flag if distance_to_flag else priority * 10
            
            if score > best_score:
                best_score = score
                best_option = {
                    'point': point,
                    'distance_from_ball': distance_to_point,
                    'obstacles': obstacles,
                    'risk_level': risk_level
                }
        
        if best_option:
            return {
                "distance_meters": round(best_option['distance_from_ball'], 2),
                "distance_yards": round(best_option['distance_from_ball'] * 1.09361, 2),
                "target": "waypoint",
                "waypoint_description": best_option['point'].get('description') or best_option['point'].get('name', 'Punto estratégico'),
                "obstacles": [
                    {
                        'id': obs.get('id'),
                        'type': obs.get('type'),
                        'name': obs.get('name')
                    }
                    for obs in best_option['obstacles']
                ],
                "obstacle_count": len(best_option['obstacles']),
                "risk_level": best_option['risk_level'],
                "description": f"Trayectoria conservadora a punto estratégico: {best_option['point'].get('name', 'Punto estratégico')}"
            }
        
        return None
    
    def _find_reachable_strategic_point_closest_to_green(self, latitude: float, longitude: float, hole_id: int,
                                                         strategic_points: List[Dict[str, Any]], max_distance: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el strategic_point alcanzable más cercano al green.
        
        Args:
            latitude: Latitud de la bola
            longitude: Longitud de la bola
            hole_id: ID del hoyo
            strategic_points: Lista de puntos estratégicos
            max_distance: Distancia máxima accesible
            
        Returns:
            Diccionario con información del strategic_point encontrado o None
        """
        best_point = None
        min_distance_to_flag = float('inf')
        
        for point in strategic_points:
            # Calcular distancia desde la bola al punto
            distance_to_point = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            
            # Solo considerar puntos alcanzables
            if distance_to_point > max_distance:
                continue
            
            # Obtener distancia al green del punto
            distance_to_flag = point.get('distance_to_flag')
            if distance_to_flag is None:
                continue
            
            # Buscar el punto más cercano al green
            if distance_to_flag < min_distance_to_flag:
                min_distance_to_flag = distance_to_flag
                best_point = {
                    **point,
                    'distance_from_ball': distance_to_point
                }
        
        return best_point
    
    def _find_conservative_trajectory_to_strategic_point(self, latitude: float, longitude: float, hole_id: int,
                                                         strategic_points: List[Dict[str, Any]], max_distance: float,
                                                         target_point: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca una trayectoria conservadora (riesgo bajo) al strategic_point más cercano al punto objetivo.
        
        Args:
            latitude: Latitud de la bola
            longitude: Longitud de la bola
            hole_id: ID del hoyo
            strategic_points: Lista de puntos estratégicos
            max_distance: Distancia máxima accesible
            target_point: Punto estratégico objetivo
            
        Returns:
            Diccionario con información de la trayectoria conservadora o None
        """
        best_option = None
        min_distance_to_target = float('inf')
        
        for point in strategic_points:
            # No considerar el mismo punto objetivo
            if point['id'] == target_point['id']:
                continue
            
            # Calcular distancia desde la bola al punto
            distance_to_point = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            
            # Solo considerar puntos alcanzables
            if distance_to_point > max_distance:
                continue
            
            # Evaluar obstáculos
            obstacles = self.golf_repository.find_obstacles_between_points(
                hole_id,
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            risk_level = self._calculate_risk_level(obstacles)
            
            # Solo considerar opciones de riesgo bajo
            if risk_level != 'low':
                continue
            
            # Calcular distancia desde este punto al punto objetivo
            distance_to_target = self.golf_repository.calculate_distance_between_points(
                point['latitude'], point['longitude'],
                target_point['latitude'], target_point['longitude']
            )
            
            # Buscar el punto más cercano al objetivo con riesgo bajo
            if distance_to_target < min_distance_to_target:
                min_distance_to_target = distance_to_target
                best_option = {
                    'point': point,
                    'distance_from_ball': distance_to_point,
                    'obstacles': obstacles,
                    'risk_level': risk_level
                }
        
        if best_option:
            return {
                "distance_meters": round(best_option['distance_from_ball'], 2),
                "distance_yards": round(best_option['distance_from_ball'] * 1.09361, 2),
                "target": "waypoint",
                "waypoint_description": best_option['point'].get('description') or best_option['point'].get('name', 'Punto estratégico'),
                "obstacles": [
                    {
                        'id': obs.get('id'),
                        'type': obs.get('type'),
                        'name': obs.get('name')
                    }
                    for obs in best_option['obstacles']
                ],
                "obstacle_count": len(best_option['obstacles']),
                "risk_level": best_option['risk_level'],
                "description": f"Trayectoria conservadora a punto estratégico: {best_option['point'].get('name', 'Punto estratégico')}"
            }
        
        return None
    
    def _find_conservative_trajectory_to_optimal_shot_waypoint(self, latitude: float, longitude: float, hole_id: int,
                                                                strategic_points: List[Dict[str, Any]], max_distance: float,
                                                                waypoint_lat: float, waypoint_lon: float) -> Optional[Dict[str, Any]]:
        """
        Busca una trayectoria conservadora (riesgo bajo) al strategic_point más cercano al waypoint del optimal_shot.
        
        Args:
            latitude: Latitud de la bola
            longitude: Longitud de la bola
            hole_id: ID del hoyo
            strategic_points: Lista de puntos estratégicos
            max_distance: Distancia máxima accesible
            waypoint_lat: Latitud del waypoint del optimal_shot
            waypoint_lon: Longitud del waypoint del optimal_shot
            
        Returns:
            Diccionario con información de la trayectoria conservadora o None
        """
        best_option = None
        min_distance_to_waypoint = float('inf')
        
        for point in strategic_points:
            # Calcular distancia desde la bola al punto
            distance_to_point = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            
            # Solo considerar puntos alcanzables
            if distance_to_point > max_distance:
                continue
            
            # Evaluar obstáculos
            obstacles = self.golf_repository.find_obstacles_between_points(
                hole_id,
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            risk_level = self._calculate_risk_level(obstacles)
            
            # Solo considerar opciones de riesgo bajo
            if risk_level != 'low':
                continue
            
            # Calcular distancia desde este punto al waypoint del optimal_shot
            distance_to_waypoint = self.golf_repository.calculate_distance_between_points(
                point['latitude'], point['longitude'],
                waypoint_lat, waypoint_lon
            )
            
            # Buscar el punto más cercano al waypoint con riesgo bajo
            if distance_to_waypoint < min_distance_to_waypoint:
                min_distance_to_waypoint = distance_to_waypoint
                best_option = {
                    'point': point,
                    'distance_from_ball': distance_to_point,
                    'obstacles': obstacles,
                    'risk_level': risk_level
                }
        
        if best_option:
            return {
                "distance_meters": round(best_option['distance_from_ball'], 2),
                "distance_yards": round(best_option['distance_from_ball'] * 1.09361, 2),
                "target": "waypoint",
                "waypoint_description": best_option['point'].get('description') or best_option['point'].get('name', 'Punto estratégico'),
                "obstacles": [
                    {
                        'id': obs.get('id'),
                        'type': obs.get('type'),
                        'name': obs.get('name')
                    }
                    for obs in best_option['obstacles']
                ],
                "obstacle_count": len(best_option['obstacles']),
                "risk_level": best_option['risk_level'],
                "description": f"Trayectoria conservadora a punto estratégico: {best_option['point'].get('name', 'Punto estratégico')}"
            }
        
        return None
    
    def _calculate_risk_level(self, obstacles: List[Dict[str, Any]]) -> str:
        """
        Calcula el nivel de riesgo basándose en los obstáculos encontrados.
        
        Args:
            obstacles: Lista de obstáculos en la trayectoria
            
        Returns:
            Nivel de riesgo: 'low', 'medium' o 'high'
        """
        if not obstacles:
            return "low"
        
        # Clasificar obstáculos por peligrosidad
        high_risk_types = ['water', 'out_of_bounds']
        medium_risk_types = ['trees', 'rough_heavy']
        low_risk_types = ['bunker']
        
        high_risk_count = sum(1 for obs in obstacles if obs.get('type') in high_risk_types)
        medium_risk_count = sum(1 for obs in obstacles if obs.get('type') in medium_risk_types)
        
        if high_risk_count > 0:
            return "high"
        elif medium_risk_count > 0:
            return "medium"
        else:
            return "medium"  # Si hay bunkers, riesgo medio
    
    def _determine_recommended_trajectory(self, direct: Dict[str, Any], 
                                         conservative: Optional[Dict[str, Any]]) -> str:
        """
        Determina qué trayectoria recomendar basándose en el análisis de riesgo.
        
        Args:
            direct: Información de la trayectoria directa
            conservative: Información de la trayectoria conservadora (puede ser None)
            
        Returns:
            'direct' o 'conservative'
        """
        # Si no hay trayectoria conservadora, recomendar directa
        if not conservative:
            return "direct"
        
        # Si la trayectoria conservadora lleva a la bandera, compararlas
        if conservative.get('is_flag'):
            # Si la directa es de bajo riesgo, recomendarla
            if direct['risk_level'] == 'low':
                return "direct"
            # Si la conservadora es significativamente más segura, recomendarla
            elif conservative['risk_level'] == 'low' and direct['risk_level'] in ['medium', 'high']:
                return "conservative"
            else:
                return "direct"
        
        # Si la conservadora NO lleva a la bandera (es un waypoint intermedio)
        # Recomendar conservadora si la directa tiene riesgo alto
        if direct['risk_level'] == 'high':
            return "conservative"
        
        # En otros casos, recomendar directa
        return "direct"
    
    def calculate_club_recommendation(self, distance_meters: float, 
                                     player_club_statistics: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Calcula el palo recomendado basándose en la distancia objetivo.
        
        Args:
            distance_meters: Distancia objetivo en metros
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            
        Returns:
            Diccionario con:
            - recommended_club: Nombre del palo recomendado
            - club_avg_distance: Distancia promedio del palo
            - distance_to_target: Distancia objetivo
            - distance_difference: Diferencia entre distancia del palo y objetivo
            - swing_type: Tipo de swing recomendado (completo, 3/4, 1/2)
            - all_club_options: Lista de todos los palos con sus distancias
        """
        # Distancias estándar de palos (en metros) - se usan si no hay perfil del jugador
        STANDARD_CLUB_DISTANCES = {
            'Driver': 230,
            'Madera 3': 210,
            'Madera 5': 195,
            'Híbrido 3': 185,
            'Híbrido 4': 175,
            'Hierro 3': 170,
            'Hierro 4': 160,
            'Hierro 5': 150,
            'Hierro 6': 140,
            'Hierro 7': 130,
            'Hierro 8': 120,
            'Hierro 9': 110,
            'Pitching Wedge': 100,
            'Gap Wedge': 90,
            'Sand Wedge': 80,
            'Lob Wedge': 65
        }
        
        # Determinar qué distancias usar
        if player_club_statistics and len(player_club_statistics) > 0:
            # Usar estadísticas del jugador
            club_distances = {
                stat['club_name']: stat['average_distance_meters']
                for stat in player_club_statistics
                if stat.get('average_distance_meters', 0) > 0
            }
            source = 'player_profile'
        else:
            # Usar distancias estándar
            club_distances = STANDARD_CLUB_DISTANCES
            source = 'standard_distances'
        
        if not club_distances:
            # No hay datos de palos
            return {
                'recommended_club': None,
                'club_avg_distance': None,
                'distance_to_target': distance_meters,
                'distance_difference': None,
                'swing_type': None,
                'all_club_options': [],
                'source': 'none',
                'message': 'No hay información de palos disponible'
            }
        
        # Encontrar el palo más cercano a la distancia objetivo
        best_club = None
        min_difference = float('inf')
        
        for club_name, club_distance in club_distances.items():
            difference = abs(club_distance - distance_meters)
            if difference < min_difference:
                min_difference = difference
                best_club = club_name
        
        best_distance = club_distances[best_club]
        
        # Determinar tipo de swing
        swing_type = self._determine_swing_type(distance_meters, best_distance)
        
        # Calcular distancia recomendada (máximo la distancia al objetivo)
        if best_distance >= distance_meters:
            recommended_distance = distance_meters
        else:
            recommended_distance = best_distance
        
        # Preparar lista de todas las opciones de palos ordenadas por proximidad
        all_options = []
        for club_name, club_distance in sorted(club_distances.items(), 
                                              key=lambda x: abs(x[1] - distance_meters)):
            diff = abs(club_distance - distance_meters)
            all_options.append({
                'club_name': club_name,
                'avg_distance_meters': round(club_distance, 1),
                'difference_meters': round(diff, 1),
                'is_recommended': club_name == best_club
            })
        
        return {
            'recommended_club': best_club,
            'club_avg_distance': round(best_distance, 1),
            'distance_to_target': round(distance_meters, 1),
            'recommended_distance': round(recommended_distance, 1),
            'distance_difference': round(min_difference, 1),
            'swing_type': swing_type,
            'all_club_options': all_options[:5],  # Top 5 opciones
            'source': source
        }
    
    def _determine_swing_type(self, target_distance: float, club_avg_distance: float) -> str:
        """
        Determina el tipo de swing recomendado basándose en la relación
        entre la distancia objetivo y la distancia promedio del palo.
        
        Args:
            target_distance: Distancia que se necesita alcanzar
            club_avg_distance: Distancia promedio del palo seleccionado
            
        Returns:
            'completo', '3/4', o '1/2'
        """
        if club_avg_distance == 0:
            return 'completo'
        
        ratio = target_distance / club_avg_distance
        
        if ratio >= 0.95:  # Necesita 95% o más de la distancia del palo
            return 'completo'
        elif ratio >= 0.70:  # Necesita entre 70% y 95%
            return '3/4'
        else:  # Necesita menos del 70%
            return '1/2'
    
    def _calculate_risk_score_detailed(
        self,
        obstacles: List[Dict[str, Any]],
        distance_to_target: float,
        target_type: str,
        terrain_type: Optional[str],
        recommended_club: Optional[str],
        player_club_statistics: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calcula un score de riesgo numérico detallado con desglose de componentes.
        
        Args:
            obstacles: Lista de obstáculos en la trayectoria
            distance_to_target: Distancia total de la trayectoria en metros
            terrain_type: Tipo de terreno donde está la bola (opcional)
            recommended_club: Nombre del palo recomendado (opcional)
            player_club_statistics: Estadísticas del jugador (opcional)
        
        Returns:
            Diccionario con:
            - total: Score de riesgo total entre 0.0 y 100.0
            - obstacle_risk: {
                value: Valor total del riesgo de obstáculos
                breakdown: {
                    base_risk: Riesgo base del obstáculo más peligroso
                    obstacle_penalty: Penalización por cantidad de obstáculos
                    precision_penalty: Penalización por precisión del jugador
                    coverage_penalty: Penalización por densidad de obstáculos
                }
            }
            - terrain_club_risk: {
                value: Valor del riesgo terreno-palo
            }
        """
        # 1. Base Risk (riesgo base por tipo de obstáculo)
        OBSTACLE_BASE_RISK = {
            'water': 50.0,
            'out_of_bounds': 45.0,
            'trees': 25.0,
            'rough_heavy': 20.0,
            'bunker': 15.0
        }
        
        base_risk = 0.0
        if obstacles:
            base_risk = max(OBSTACLE_BASE_RISK.get(obs.get('type'), 0) for obs in obstacles)
        
        # 2. Obstacle Penalty (cantidad de obstáculos)
        obstacle_count = len(obstacles)
        obstacle_penalty = 0.0
        if obstacle_count > 1:
            obstacle_penalty = sum(5.0 / (i + 1) for i in range(obstacle_count - 1))
            obstacle_penalty = min(obstacle_penalty, 15.0)  # Límite máximo
        
        # 3. Precision Penalty (simplificado)
        precision_penalty = 0.0
        if player_club_statistics and recommended_club and distance_to_target > 0:
            # Buscar estadísticas del palo recomendado
            club_stats = next(
                (stat for stat in player_club_statistics 
                 if stat.get('club_name') == recommended_club),
                None
            )
            
            if club_stats:
                avg_error = club_stats.get('average_error_meters', 0)
                error_percentage = avg_error / distance_to_target if distance_to_target > 0 else 0
                
                # Si el error es > 10% de la distancia, penalizar
                if error_percentage > 0.10:
                    precision_penalty = min(15.0, (error_percentage - 0.10) * 150)
        
        # 4. Coverage Penalty (simplificado - densidad de obstáculos)
        coverage_penalty = 0.0
        if obstacles and distance_to_target < 100.0:
            obstacle_density = len(obstacles) / max(distance_to_target, 1.0)
            if obstacle_density > 0.05:  # Más de 1 obstáculo cada 20m
                coverage_penalty = min(10.0, obstacle_density * 200)
        
        # Calcular riesgo total de obstáculos
        obstacle_risk_total = base_risk + obstacle_penalty + precision_penalty + coverage_penalty
        
        # 5. Terrain-Club Penalty (relación terreno-palo)
        terrain_club_penalty = 0.0
        club_type = None
        
        if recommended_club is not None:
            TERRAIN_CLUB_RISK = {
                'tee': {  # tee de salida
                    'wedge': 0.0,
                    'iron': 0.0,
                    'hybrid': 1.0,
                    'wood': 1.5,
                    'driver': 2.0  # Driver en tee: riesgo bajo (lugar diseñado para driver)
                },
                None: {  # fairway/green
                    'wedge': 0.0,
                    'iron': 2.0,
                    'hybrid': 5.0,
                    'wood': 60.0,  # Madera 3 en fairway: riesgo muy alto
                    'driver': 70.0  # Driver en fairway: riesgo muy alto
                },
                'bunker': {
                    'wedge': 0.0,
                    'iron': 8.0,
                    'hybrid': 15.0,
                    'wood': 100.0,  # Madera 3 en bunker: prácticamente prohibido
                    'driver': 100.0  # Driver en bunker: prácticamente prohibido
                },
                'rough_heavy': {
                    'wedge': 3.0,
                    'iron': 5.0,
                    'hybrid': 10.0,
                    'wood': 70.0,  # Madera 3 en rough pesado: riesgo extremo
                    'driver': 80.0  # Driver en rough pesado: riesgo extremo
                },
                'trees': {
                    'wedge': 5.0,
                    'iron': 8.0,
                    'hybrid': 12.0,
                    'wood': 80.0,  # Madera 3 entre árboles: riesgo extremo
                    'driver': 90.0  # Driver entre árboles: riesgo extremo
                }
                # 'water' y 'out_of_bounds' no se incluyen (ya penalizados en base_risk)
            }
            
            # Obtener tipo de palo desde estadísticas del jugador si es posible
            if player_club_statistics:
                for stat in player_club_statistics:
                    if stat.get('club_name') == recommended_club:
                        club_type = stat.get('club_type')
                        break
            
            # Fallback: heurísticas basadas en el nombre del palo
            if not club_type:
                club_name_lower = recommended_club.lower()
                if 'driver' in club_name_lower:
                    club_type = 'driver'
                elif 'madera' in club_name_lower or 'wood' in club_name_lower:
                    club_type = 'wood'
                elif 'híbrido' in club_name_lower or 'hybrid' in club_name_lower:
                    club_type = 'hybrid'
                elif 'wedge' in club_name_lower:
                    club_type = 'wedge'
                elif 'hierro' in club_name_lower or 'iron' in club_name_lower:
                    club_type = 'iron'
            
            # Aplicar penalización si tenemos tipo de palo
            if club_type:
                # Terreno normal (fairway/green) viene como None
                if terrain_type in TERRAIN_CLUB_RISK:
                    terrain_risks = TERRAIN_CLUB_RISK[terrain_type]
                    terrain_club_penalty = terrain_risks.get(club_type, 0.0)
                else:
                    # Si el terreno es None u otro no contemplado, tratarlo como fairway/green
                    terrain_risks = TERRAIN_CLUB_RISK.get(None, {})
                    terrain_club_penalty = terrain_risks.get(club_type, 0.0)
        
        # 6. Distance-Target Penalty (relación distancia-objetivo)
        distance_target_penalty = 0.0
        if distance_to_target > 0:
            if target_type == 'waypoint':
                # Waypoints son objetivos intermedios, más seguros
                # Penalización pequeña pero gradual que aumenta con la distancia
                if distance_to_target < 50.0:
                    # 0-50m: sin penalización
                    distance_target_penalty = 0.0
                elif distance_to_target < 100.0:
                    # 50-100m: penalización pequeña de 0 a 1.5 puntos
                    distance_target_penalty = (distance_to_target - 50.0) / 50.0 * 1.5
                elif distance_to_target < 150.0:
                    # 100-150m: penalización de 1.5 a 3.5 puntos
                    distance_target_penalty = 1.5 + (distance_to_target - 100.0) / 50.0 * 2.0
                else:
                    # >150m: penalización de 3.5 a 6.0 puntos máximo
                    distance_target_penalty = min(6.0, 3.5 + (distance_to_target - 150.0) / 50.0 * 2.5)
            else:
                # Cualquier otro valor se considera como objetivo de tipo bandera/green
                # El riesgo aumenta de forma no lineal con la distancia
                if distance_to_target < 50.0:
                    distance_target_penalty = 0.0
                elif distance_to_target < 100.0:
                    # 50-100m: riesgo crece linealmente de 0 a 5
                    distance_target_penalty = (distance_to_target - 50.0) / 50.0 * 5.0
                elif distance_to_target < 150.0:
                    # 100-150m: riesgo crece de 5 a 10
                    distance_target_penalty = 5.0 + (distance_to_target - 100.0) / 50.0 * 5.0
                elif distance_to_target < 200.0:
                    # 150-200m: riesgo crece de 10 a 15
                    distance_target_penalty = 10.0 + (distance_to_target - 150.0) / 50.0 * 5.0
                else:
                    # > 200m: riesgo alto, máximo 20 puntos
                    distance_target_penalty = min(20.0, 15.0 + (distance_to_target - 200.0) / 50.0 * 5.0)
        
        # Calcular score total
        total_risk = obstacle_risk_total + terrain_club_penalty + distance_target_penalty
        
        # Limitar al rango [0, 100]
        total_risk = min(100.0, max(0.0, total_risk))
        
        return {
            'total': round(total_risk, 2),
            'obstacle_risk': {
                'value': round(obstacle_risk_total, 2),
                'breakdown': {
                    'base_risk': round(base_risk, 2),
                    'obstacle_penalty': round(obstacle_penalty, 2),
                    'precision_penalty': round(precision_penalty, 2),
                    'coverage_penalty': round(coverage_penalty, 2)
                }
            },
            'terrain_club_risk': {
                'value': round(terrain_club_penalty, 2)
            },
            'distance_target_risk': {
                'value': round(distance_target_penalty, 2)
            }
        }

    def _get_distance_to_green(self, trayectoria: Dict[str, Any]) -> float:
        """
        Calcula la distancia al green de una trayectoria.
        
        Args:
            trayectoria: Diccionario con información de la trayectoria
            
        Returns:
            Distancia al green en metros. Para trayectorias con target "flag", 
            devuelve distance_meters. Para "waypoint", usa distance_meters como aproximación.
        """
        target = trayectoria.get('target', '')
        distance_meters = trayectoria.get('distance_meters', 0.0)
        
        # Si el objetivo es la bandera, la distancia al green es distance_meters
        if target == 'flag':
            return distance_meters
        
        # Para waypoints, usamos distance_meters como aproximación
        # (waypoints más lejanos generalmente están más lejos del green)
        return distance_meters
    
    def evaluacion_final(self, trayectorias: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ordena y clasifica las trayectorias según su valor de riesgo.
        Si dos o más trayectorias tienen el mismo riesgo, se ordenan por distancia al green
        (mayor distancia = más conservadora).
        
        Args:
            trayectorias: Lista de 0 a 3 trayectorias con información de riesgo
            
        Returns:
            Diccionario con las trayectorias clasificadas:
            - trayectoria_optima: Trayectoria óptima (o mensaje si no hay trayectorias)
            - trayectoria_riesgo: Trayectoria con mayor riesgo (si hay 2 o 3)
            - trayectoria_conservadora: Trayectoria con menor riesgo (si hay 3)
        """
        num_trayectorias = len(trayectorias)
        
        # Si no hay trayectorias
        if num_trayectorias == 0:
            return {
                "trayectoria_optima": "Buscar la calle utilizando un hierro y una bola rodada"
            }
        
        # Si hay 1 trayectoria
        if num_trayectorias == 1:
            return {
                "trayectoria_optima": trayectorias[0]
            }
        
        # Ordenar trayectorias por riesgo (de menor a mayor)
        # Si el riesgo es igual, ordenar por distancia al green (descendente: mayor = más conservadora)
        def sort_key(t):
            riesgo = t.get('risk_level', {}).get('total', 0.0) if isinstance(t.get('risk_level'), dict) else 0.0
            distancia_green = self._get_distance_to_green(t)
            # Retornar tupla: (riesgo, -distancia_green) para ordenar por riesgo ascendente
            # y por distancia descendente cuando el riesgo es igual
            return (riesgo, -distancia_green)
        
        trayectorias_ordenadas = sorted(trayectorias, key=sort_key)
        
        # Si hay 2 trayectorias
        if num_trayectorias == 2:
            menor_riesgo = trayectorias_ordenadas[0]
            mayor_riesgo = trayectorias_ordenadas[1]
            
            # Obtener valores de riesgo
            riesgo_menor_val = menor_riesgo.get('risk_level', {}).get('total', 0.0) if isinstance(menor_riesgo.get('risk_level'), dict) else 0.0
            riesgo_mayor_val = mayor_riesgo.get('risk_level', {}).get('total', 0.0) if isinstance(mayor_riesgo.get('risk_level'), dict) else 0.0
            
            # Caso 1: Si las dos trayectorias tienen riesgo < 30
            if riesgo_menor_val < 30 and riesgo_mayor_val < 30:
                return {
                    "trayectoria_optima": mayor_riesgo,
                    "trayectoria_conservadora": menor_riesgo
                }
            
            # Caso 2: Si la trayectoria con riesgo menor tiene riesgo > 30
            elif riesgo_menor_val > 30:
                return {
                    "trayectoria_optima": menor_riesgo,
                    "trayectoria_riesgo": mayor_riesgo
                }
            
            # Caso 3: Si la trayectoria con riesgo menor tiene riesgo <= 30
            # (esto implica que la menor <= 30 y la mayor >= 30)
            else:  # riesgo_menor_val <= 30
                return {
                    "trayectoria_optima": mayor_riesgo,
                    "trayectoria_riesgo": menor_riesgo
                }
        
        # Si hay 3 trayectorias
        if num_trayectorias == 3:
            menor_riesgo = trayectorias_ordenadas[0]
            intermedio_riesgo = trayectorias_ordenadas[1]
            mayor_riesgo = trayectorias_ordenadas[2]
            
            return {
                "trayectoria_optima": intermedio_riesgo,
                "trayectoria_riesgo": mayor_riesgo,
                "trayectoria_conservadora": menor_riesgo
            }
        
        # Caso por defecto (no debería llegar aquí)
        return {
            "trayectoria_optima": trayectorias[0] if trayectorias else "Buscar la calle utilizando un hierro y una bola rodada"
        }

    def is_trayectoria_valida(self, trayectoria: Dict[str, Any]) -> bool:
        """
        Comprueba si una trayectoria es válida según su valor de riesgo.
        
        Args:
            trayectoria: Diccionario con información de la trayectoria, debe incluir 'risk_level'
            
        Returns:
            True si el riesgo es <= 75, False si es > 75
        """
        risk_level = trayectoria.get('risk_level', {})
        
        # Obtener el valor total del riesgo
        if isinstance(risk_level, dict):
            riesgo_total = risk_level.get('total', 0.0)
        else:
            # Si risk_level no es un dict, asumir que es un número o 0
            riesgo_total = float(risk_level) if risk_level else 0.0
        
        # Si el riesgo es mayor de 75, descartar
        if riesgo_total > 75:
            return False
        
        # Si el riesgo es menor o igual a 75, guardar
        return True

    def calcular_trayectoria(
        self,
        punto_inicial: Dict[str, float],
        punto_final: Dict[str, float],
        hole_id: int,
        player_club_statistics: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula la trayectoria entre dos puntos y valida si es válida.
        
        Args:
            punto_inicial: Diccionario con 'latitude' y 'longitude' del punto inicial
            punto_final: Diccionario con 'latitude' y 'longitude' del punto final
            hole_id: ID del hoyo
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            
        Returns:
            Diccionario con información de la trayectoria si es válida (riesgo <= 75),
            None si no es válida (riesgo > 75)
        """
        lat_inicial = punto_inicial['latitude']
        lon_inicial = punto_inicial['longitude']
        lat_final = punto_final['latitude']
        lon_final = punto_final['longitude']
        
        # Calcular distancia entre los puntos
        distance_meters = self.golf_repository.calculate_distance_between_points(
            lat_inicial, lon_inicial,
            lat_final, lon_final
        )
        
        # Encontrar obstáculos en la trayectoria
        obstacles = self.golf_repository.find_obstacles_between_points(
            hole_id,
            lat_inicial, lon_inicial,
            lat_final, lon_final
        )
        
        # Determinar tipo de terreno donde está la bola
        terrain_type = self.golf_repository.find_terrain_type_by_position(
            hole_id, lat_inicial, lon_inicial
        )
        
        # Calcular recomendación de palo
        club_rec = self.calculate_club_recommendation(
            distance_meters=distance_meters,
            player_club_statistics=player_club_statistics
        )
        
        # Calcular riesgo numérico completo
        # Usar el target del punto_final si está disponible, por defecto "waypoint"
        target_type = punto_final.get('target', 'waypoint')
        
        numeric_risk = self._calculate_risk_score_detailed(
            obstacles=obstacles,
            distance_to_target=distance_meters,
            target_type=target_type,
            terrain_type=terrain_type,
            recommended_club=club_rec.get("recommended_club"),
            player_club_statistics=player_club_statistics
        )
        
        # Crear diccionario de trayectoria
        trayectoria = {
            "distance_meters": round(distance_meters, 2),
            "distance_yards": round(distance_meters * 1.09361, 2),
            "target": punto_final.get('target', 'waypoint'),
            "waypoint_description": punto_final.get('description', punto_final.get('name', 'Punto estratégico')),
            "obstacles": [
                {
                    'id': obs.get('id'),
                    'type': obs.get('type'),
                    'name': obs.get('name')
                }
                for obs in obstacles
            ],
            "obstacle_count": len(obstacles),
            "risk_level": numeric_risk,
            "description": f"Trayectoria desde ({lat_inicial}, {lon_inicial}) hasta ({lat_final}, {lon_final})",
            "club_recommendation": club_rec,
            "punto_inicial": punto_inicial,
            "punto_final": punto_final
        }
        
        # Aplicar validación de riesgo
        if self.is_trayectoria_valida(trayectoria):
            return trayectoria
        else:
            return None

    def bola_menos_10m_optimal_shot(
        self,
        latitude: float,
        longitude: float,
        hole_id: int,
        player_club_statistics: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Comprueba para todos los optimal_shot del hoyo si la bola está a menos de 10 metros
        del punto inicial de cada trayectoria optimal_shot.
        
        Si la bola está a menos de 10m, calcula la trayectoria desde la bola hasta el punto final
        del optimal_shot y la valida.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            
        Returns:
            Lista de trayectorias válidas calculadas desde la bola hasta los puntos finales
            de los optimal_shots que están a menos de 10m del punto inicial
        """
        trayectorias_validas = []
        
        # Obtener distancia máxima alcanzable del jugador
        max_distance = self._get_max_accessible_distance(player_club_statistics)
        
        # Obtener todos los optimal_shots del hoyo
        optimal_shots = self.golf_repository.get_all_optimal_shots(hole_id)
        
        for optimal_shot in optimal_shots:
            # Calcular distancia desde la bola al punto inicial del optimal_shot
            distance_to_start = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                optimal_shot['start_lat'], optimal_shot['start_lon']
            )
            
            # Si la bola está a menos de 10 metros del punto inicial
            if distance_to_start <= 10.0:
                # Calcular distancia desde la bola al punto final del optimal_shot
                distance_to_end = self.golf_repository.calculate_distance_between_points(
                    latitude, longitude,
                    optimal_shot['end_lat'], optimal_shot['end_lon']
                )
                
                # Verificar si la distancia al punto final es alcanzable
                if distance_to_end > max_distance:
                    # Si no es alcanzable, pasar al siguiente optimal_shot
                    continue
                
                # Preparar punto inicial (posición de la bola)
                punto_inicial = {
                    'latitude': latitude,
                    'longitude': longitude
                }
                
                # Preparar punto final (punto final del optimal_shot)
                punto_final = {
                    'latitude': optimal_shot['end_lat'],
                    'longitude': optimal_shot['end_lon'],
                    'description': optimal_shot.get('description', 'Endpoint de optimal_shot'),
                    'target': 'waypoint'
                }
                
                # Calcular trayectoria
                trayectoria = self.calcular_trayectoria(
                    punto_inicial=punto_inicial,
                    punto_final=punto_final,
                    hole_id=hole_id,
                    player_club_statistics=player_club_statistics
                )
                
                # Si la trayectoria es válida, agregarla a la lista
                if trayectoria is not None:
                    trayectorias_validas.append(trayectoria)
        
        return trayectorias_validas

    def find_strategic_shot(
        self,
        latitude: float,
        longitude: float,
        hole_id: int,
        player_club_statistics: Optional[List[Dict[str, Any]]] = None,
        trayectorias_existentes: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recorre una lista de puntos estratégicos en orden (primero el green, luego strategic_points
        ordenados por cercanía al green) y calcula trayectorias hasta encontrar 3 trayectorias válidas.
        
        Args:
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            hole_id: ID del hoyo
            player_club_statistics: Estadísticas de palos del jugador (opcional)
            trayectorias_existentes: Lista de trayectorias ya encontradas (opcional)
            
        Returns:
            Lista de trayectorias válidas encontradas (máximo 3 en total)
        """
        if trayectorias_existentes is None:
            trayectorias_existentes = []
        
        trayectorias = list(trayectorias_existentes)  # Copiar lista existente
        
        # Obtener distancia máxima alcanzable del jugador
        max_distance = self._get_max_accessible_distance(player_club_statistics)
        
        # Obtener información del green (flag)
        distance_to_flag = self.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        
        # Obtener terreno donde está la bola
        terrain_type = self.golf_repository.find_terrain_type_by_position(
            hole_id, latitude, longitude
        )
        
        # Primero evaluar trayectoria directa al green (flag) si existe y no tenemos 3 aún
        if len(trayectorias) < 3 and distance_to_flag is not None:
            # Verificar si la distancia al flag es alcanzable
            if distance_to_flag <= max_distance:
                obstacles_flag = self.golf_repository.find_obstacles_between_ball_and_flag(
                    hole_id, latitude, longitude
                )
                
                club_rec_flag = self.calculate_club_recommendation(
                    distance_meters=distance_to_flag,
                    player_club_statistics=player_club_statistics
                )
                
                numeric_risk_flag = self._calculate_risk_score_detailed(
                    obstacles=obstacles_flag,
                    distance_to_target=distance_to_flag,
                    target_type="flag",
                    terrain_type=terrain_type,
                    recommended_club=club_rec_flag.get("recommended_club"),
                    player_club_statistics=player_club_statistics
                )
                
                trayectoria_flag = {
                    "distance_meters": round(distance_to_flag, 2),
                    "distance_yards": round(distance_to_flag * 1.09361, 2),
                    "target": "flag",
                    "obstacles": [
                        {
                            'id': obs.get('id'),
                            'type': obs.get('type'),
                            'name': obs.get('name')
                        }
                        for obs in obstacles_flag
                    ],
                    "obstacle_count": len(obstacles_flag),
                    "risk_level": numeric_risk_flag,
                    "description": "Trayectoria directa a la bandera",
                    "club_recommendation": club_rec_flag
                }
                
                if self.is_trayectoria_valida(trayectoria_flag):
                    trayectorias.append(trayectoria_flag)
        
        # Obtener todos los strategic_points del hoyo (ordenados por distance_to_flag ASC)
        strategic_points = self.golf_repository.get_strategic_points(hole_id)
        
        # Recorrer strategic_points y calcular trayectorias hasta tener 3 válidas
        for point in strategic_points:
            if len(trayectorias) >= 3:
                break
            
            # Calcular distancia desde la bola al strategic_point
            distance_to_point = self.golf_repository.calculate_distance_between_points(
                latitude, longitude,
                point['latitude'], point['longitude']
            )
            
            # Verificar si la distancia es alcanzable
            if distance_to_point > max_distance:
                # Si no es alcanzable, pasar al siguiente punto
                continue
            
            # Preparar punto inicial (posición de la bola)
            punto_inicial = {
                'latitude': latitude,
                'longitude': longitude
            }
            
            # Preparar punto final
            punto_final = {
                'latitude': point['latitude'],
                'longitude': point['longitude'],
                'description': point.get('description') or point.get('name', 'Punto estratégico'),
                'target': 'waypoint'
            }
            
            # Calcular trayectoria
            trayectoria = self.calcular_trayectoria(
                punto_inicial=punto_inicial,
                punto_final=punto_final,
                hole_id=hole_id,
                player_club_statistics=player_club_statistics
            )
            
            # Si la trayectoria es válida, agregarla
            if trayectoria is not None:
                trayectorias.append(trayectoria)
        
        return trayectorias[:3]  # Retornar máximo 3 trayectorias

