# -*- coding: utf-8 -*-
"""
Puerto (interfaz) para el repositorio de jugadores.

Define las operaciones que el dominio necesita sin depender de la implementación.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class PlayerRepository(ABC):
    """
    Interfaz para el repositorio de jugadores.
    
    Define las operaciones que el dominio necesita para trabajar con
    usuarios y perfiles de jugadores.
    """
    
    @abstractmethod
    def create_user(self, email: str, username: str, first_name: Optional[str] = None,
                   last_name: Optional[str] = None, phone: Optional[str] = None,
                   date_of_birth: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            email: Email del usuario (debe ser único)
            username: Nombre de usuario (debe ser único)
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            phone: Teléfono de contacto
            date_of_birth: Fecha de nacimiento (formato YYYY-MM-DD)
            
        Returns:
            Diccionario con la información del usuario creado
            
        Raises:
            ValueError: Si el email o username ya existen
        """
        pass
    
    @abstractmethod
    def create_player_profile(self, user_id: int, handicap: Optional[float] = None,
                            preferred_hand: Optional[str] = None, years_playing: Optional[int] = None,
                            skill_level: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un perfil de jugador asociado a un usuario.
        
        Args:
            user_id: ID del usuario al que pertenece el perfil
            handicap: Handicap del jugador
            preferred_hand: Mano preferida (right, left, ambidextrous)
            years_playing: Años de experiencia jugando golf
            skill_level: Nivel de habilidad (beginner, intermediate, advanced, professional)
            notes: Notas adicionales
            
        Returns:
            Diccionario con la información del perfil creado
            
        Raises:
            ValueError: Si el usuario no existe o ya tiene un perfil
        """
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su username.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_player_profile_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el perfil de jugador asociado a un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con la información del perfil si existe, None si no
        """
        pass
    
    @abstractmethod
    def create_player_profile(self, user_id: int, handicap: Optional[float] = None,
                            gender: Optional[str] = None,
                            preferred_hand: Optional[str] = None, years_playing: Optional[int] = None,
                            skill_level: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un perfil de jugador asociado a un usuario.
        
        Args:
            user_id: ID del usuario al que pertenece el perfil
            handicap: Handicap del jugador
            gender: Género del jugador (male, female)
            preferred_hand: Mano preferida (right, left, ambidextrous)
            years_playing: Años de experiencia jugando golf
            skill_level: Nivel de habilidad (beginner, intermediate, advanced, professional)
            notes: Notas adicionales
            
        Returns:
            Diccionario con la información del perfil creado
            
        Raises:
            ValueError: Si el usuario no existe o ya tiene un perfil
        """
        pass
    
    @abstractmethod
    def initialize_club_statistics(self, player_profile_id: int, club_distances: Dict[str, float]) -> None:
        """
        Inicializa las estadísticas de distancia por palo para un jugador.
        
        Args:
            player_profile_id: ID del perfil de jugador
            club_distances: Diccionario con nombre de palo como clave y distancia en metros como valor
            
        Raises:
            ValueError: Si algún palo no existe en la base de datos
        """
        pass
    
    @abstractmethod
    def get_golf_club_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un palo de golf por su nombre.
        
        Args:
            name: Nombre del palo
            
        Returns:
            Diccionario con la información del palo si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_player_club_statistics(self, player_profile_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las estadísticas de palos de un jugador.
        
        Args:
            player_profile_id: ID del perfil de jugador
            
        Returns:
            Lista de diccionarios con información de estadísticas por palo
        """
        pass
    
    @abstractmethod
    def update_club_statistics_after_stroke(self, player_profile_id: int, club_id: int,
                                           actual_distance: float, target_distance: float,
                                           quality_score: float) -> None:
        """
        Actualiza las estadísticas de un palo después de evaluar un golpe.
        
        Usa media móvil ponderada para actualizar:
        - average_distance_meters
        - average_error_meters
        - shots_recorded
        
        Args:
            player_profile_id: ID del perfil de jugador
            club_id: ID del palo utilizado
            actual_distance: Distancia real alcanzada en metros
            target_distance: Distancia objetivo en metros
            quality_score: Calidad del golpe (0-100)
        """
        pass
    
    @abstractmethod
    def update_user_data(self, user_id: int, email: Optional[str] = None,
                        username: Optional[str] = None, first_name: Optional[str] = None,
                        last_name: Optional[str] = None, phone: Optional[str] = None,
                        date_of_birth: Optional[str] = None) -> Dict[str, Any]:
        """
        Actualiza los datos de un usuario.
        
        Args:
            user_id: ID del usuario a actualizar
            email: Nuevo email (opcional)
            username: Nuevo username (opcional)
            first_name: Nuevo nombre (opcional)
            last_name: Nuevo apellido (opcional)
            phone: Nuevo teléfono (opcional)
            date_of_birth: Nueva fecha de nacimiento (opcional, formato YYYY-MM-DD)
            
        Returns:
            Diccionario con la información del usuario actualizado
            
        Raises:
            ValueError: Si el usuario no existe o los datos no son válidos
        """
        pass
    
    @abstractmethod
    def update_player_profile(self, user_id: int, handicap: Optional[float] = None,
                            gender: Optional[str] = None,
                            preferred_hand: Optional[str] = None,
                            years_playing: Optional[int] = None,
                            skill_level: Optional[str] = None,
                            notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Actualiza el perfil de jugador de un usuario.
        
        Args:
            user_id: ID del usuario
            handicap: Nuevo handicap (opcional)
            gender: Nuevo género (opcional)
            preferred_hand: Nueva mano preferida (opcional)
            years_playing: Nuevos años jugando (opcional)
            skill_level: Nuevo nivel de habilidad (opcional)
            notes: Nuevas notas (opcional)
            
        Returns:
            Diccionario con la información del perfil actualizado
            
        Raises:
            ValueError: Si el usuario no existe o no tiene perfil
        """
        pass
    
    @abstractmethod
    def create_player_club(self, player_profile_id: int, club_name: str,
                          club_type: Optional[str] = None,
                          average_distance_meters: Optional[float] = None,
                          min_distance_meters: Optional[float] = None,
                          max_distance_meters: Optional[float] = None,
                          average_error_meters: Optional[float] = None) -> Dict[str, Any]:
        """
        Crea un nuevo palo personalizado para un jugador.
        
        Args:
            player_profile_id: ID del perfil de jugador
            club_name: Nombre del palo
            club_type: Tipo del palo (opcional)
            average_distance_meters: Distancia promedio en metros (opcional)
            min_distance_meters: Distancia mínima en metros (opcional)
            max_distance_meters: Distancia máxima en metros (opcional)
            average_error_meters: Error promedio en metros (opcional)
            
        Returns:
            Diccionario con la información del palo creado
            
        Raises:
            ValueError: Si el perfil no existe o los datos no son válidos
        """
        pass
    
    @abstractmethod
    def update_player_club(self, club_statistics_id: int, player_profile_id: int,
                          club_name: Optional[str] = None,
                          club_type: Optional[str] = None,
                          average_distance_meters: Optional[float] = None,
                          min_distance_meters: Optional[float] = None,
                          max_distance_meters: Optional[float] = None,
                          average_error_meters: Optional[float] = None) -> Dict[str, Any]:
        """
        Actualiza un palo de un jugador.
        
        Args:
            club_statistics_id: ID de la estadística del palo
            player_profile_id: ID del perfil de jugador (para verificación)
            club_name: Nuevo nombre del palo (opcional)
            club_type: Nuevo tipo del palo (opcional)
            average_distance_meters: Nueva distancia promedio (opcional)
            min_distance_meters: Nueva distancia mínima (opcional)
            max_distance_meters: Nueva distancia máxima (opcional)
            average_error_meters: Nuevo error promedio (opcional)
            
        Returns:
            Diccionario con la información del palo actualizado
            
        Raises:
            ValueError: Si el palo no existe o no pertenece al jugador
        """
        pass
    
    @abstractmethod
    def delete_player_club(self, club_statistics_id: int, player_profile_id: int) -> None:
        """
        Elimina un palo de un jugador.
        
        Args:
            club_statistics_id: ID de la estadística del palo
            player_profile_id: ID del perfil de jugador (para verificación)
            
        Raises:
            ValueError: Si el palo no existe o no pertenece al jugador
        """
        pass
    
    @abstractmethod
    def get_player_club_by_id(self, club_statistics_id: int, player_profile_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un palo específico de un jugador por su ID.
        
        Args:
            club_statistics_id: ID de la estadística del palo
            player_profile_id: ID del perfil de jugador
            
        Returns:
            Diccionario con la información del palo si existe, None si no
        """
        pass

