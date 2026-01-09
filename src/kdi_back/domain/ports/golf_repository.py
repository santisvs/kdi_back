# -*- coding: utf-8 -*-
"""
Puerto (interfaz) para el repositorio de golf.

Define las operaciones que el dominio necesita sin depender de la implementación.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class GolfRepository(ABC):
    """
    Interfaz para el repositorio de golf.
    
    Define las operaciones que el dominio necesita para trabajar con
    campos de golf, hoyos, etc.
    """
    
    @abstractmethod
    def find_hole_by_position(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el hoyo en el que se encuentra una bola según su posición GPS.
        
        Args:
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con la información del hoyo si se encuentra, None si no
        """
        pass
    
    @abstractmethod
    def get_hole_by_id(self, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por su ID.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con la información del hoyo si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_hole_by_course_and_number(self, course_id: int, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un hoyo por course_id y hole_number.
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo (1, 2, 3, etc.)
            
        Returns:
            Diccionario con la información del hoyo si existe, None si no
        """
        pass
    
    @abstractmethod
    def find_terrain_type_by_position(self, hole_id: int, latitude: float, longitude: float) -> Optional[str]:
        """
        Determina el tipo de terreno donde se encuentra una bola según su posición GPS.
        
        Busca en la tabla obstacle si el punto está dentro de algún obstáculo.
        
        Args:
            hole_id: ID del hoyo donde buscar
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Tipo de terreno (bunker, water, trees, rough_heavy, out_of_bounds) si se encuentra,
            None si la bola está en terreno normal (fairway/green)
        """
        pass
    
    @abstractmethod
    def calculate_distance_to_hole(self, hole_id: int, latitude: float, longitude: float) -> Optional[float]:
        """
        Calcula la distancia desde la posición de la bola hasta la bandera del hoyo.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Distancia en metros si se encuentra la bandera, None si no
        """
        pass
    
    @abstractmethod
    def find_obstacles_between_ball_and_flag(self, hole_id: int, latitude: float, longitude: float) -> list[Dict[str, Any]]:
        """
        Encuentra los obstáculos que intersectan con la línea entre la bola y la bandera.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Lista de diccionarios con información de los obstáculos encontrados
        """
        pass
    
    @abstractmethod
    def find_nearest_optimal_shot(self, hole_id: int, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el golpe óptimo más cercano a la posición actual de la bola.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con información del golpe óptimo más cercano, None si no se encuentra
        """
        pass
    
    @abstractmethod
    def get_all_optimal_shots(self, hole_id: int) -> list[Dict[str, Any]]:
        """
        Obtiene todos los golpes óptimos de un hoyo en orden.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los golpes óptimos ordenados
        """
        pass
    
    @abstractmethod
    def find_next_optimal_waypoint(self, hole_id: int, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra el siguiente waypoint óptimo desde la posición actual de la bola.
        
        Este método determina cuál es el siguiente punto objetivo siguiendo la secuencia
        de optimal_shots del hoyo (útil para hoyos con curvas/dogleg).
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            Diccionario con:
            - waypoint_lat: Latitud del siguiente punto objetivo
            - waypoint_lon: Longitud del siguiente punto objetivo
            - distance_to_waypoint: Distancia en metros hasta el waypoint
            - waypoint_description: Descripción del objetivo (ej: "vértice de la curva")
            - is_flag: True si el waypoint es la bandera, False si es un punto intermedio
        """
        pass
    
    @abstractmethod
    def find_obstacles_between_points(self, hole_id: int, 
                                      from_lat: float, from_lon: float,
                                      to_lat: float, to_lon: float) -> list[Dict[str, Any]]:
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
        pass
    
    @abstractmethod
    def get_strategic_points(self, hole_id: int) -> list[Dict[str, Any]]:
        """
        Obtiene todos los puntos estratégicos de un hoyo.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los puntos estratégicos, ordenados por
            distancia a la bandera (más cercanos primero)
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def is_ball_on_green(self, hole_id: int, latitude: float, longitude: float) -> bool:
        """
        Determina si la bola está en el green.
        
        Se considera que está en el green si la distancia a la bandera es menor a 30 metros
        y no está en ningún obstáculo.
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud de la posición de la bola
            longitude: Longitud de la posición de la bola
            
        Returns:
            True si la bola está en el green, False si no
        """
        pass
    
    @abstractmethod
    def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los campos de golf.
        
        Returns:
            Lista de diccionarios con información de los campos (id, name, location)
        """
        pass
    
    @abstractmethod
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
        
        Útil para corregir posiciones GPS basándose en descripciones del jugador.
        Por ejemplo, si el jugador dice "estoy entre los árboles" pero el GPS lo sitúa
        en el fairway, buscar el polígono de árboles más cercano y corregir la posición.
        
        Args:
            hole_id: ID del hoyo donde buscar
            obstacle_type: Tipo de obstáculo (trees, bunker, water, rough_heavy, etc.)
            latitude: Latitud GPS aproximada
            longitude: Longitud GPS aproximada
            max_distance_meters: Distancia máxima para buscar (por defecto 100m)
            
        Returns:
            Diccionario con:
            - id: ID del obstáculo
            - hole_id: ID del hoyo
            - type: Tipo de obstáculo
            - name: Nombre del obstáculo (si tiene)
            - corrected_latitude: Latitud corregida (centro del polígono o punto más cercano)
            - corrected_longitude: Longitud corregida
            - distance_meters: Distancia desde la posición GPS original
            - shape_wkt: WKT del polígono (para referencia)
            None si no se encuentra ningún obstáculo del tipo especificado
        """
        pass
    
    @abstractmethod
    def get_hole_bbox(self, hole_id: int) -> Optional[Dict[str, float]]:
        """
        Obtiene el bbox (bounding box) de un hoyo como min/max lat/lng.
        
        Extrae los valores mínimo y máximo de latitud y longitud del polígono bbox_polygon.
        
        Args:
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con min_lat, max_lat, min_lng, max_lng si existe bbox,
            None si no existe
        """
        pass
    
    @abstractmethod
    def get_hole_geometry(self, course_id: int, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene toda la información geométrica de un hoyo.
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            
        Returns:
            Diccionario con toda la geometría del hoyo (bbox, tees, green, fairway, 
            obstacles, strategic_points, optimal_shots), None si el hoyo no existe
        """
        pass

