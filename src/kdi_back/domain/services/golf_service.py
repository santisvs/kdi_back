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

