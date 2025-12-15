# -*- coding: utf-8 -*-
"""
Puerto (interfaz) para el repositorio de golf.

Define las operaciones que el dominio necesita sin depender de la implementación.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


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

