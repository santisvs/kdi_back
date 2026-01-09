# -*- coding: utf-8 -*-
"""
Puerto (interfaz) para el repositorio de partidos.

Define las operaciones que el dominio necesita sin depender de la implementación.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class MatchRepository(ABC):
    """
    Interfaz para el repositorio de partidos.
    
    Define las operaciones que el dominio necesita para trabajar con
    partidos de golf.
    """
    
    @abstractmethod
    def create_match(self, course_id: int, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo partido en la base de datos.
        
        Args:
            course_id: ID del campo de golf donde se juega el partido
            name: Nombre opcional del partido
            
        Returns:
            Diccionario con la información del partido creado
            
        Raises:
            ValueError: Si el campo de golf no existe
        """
        pass
    
    @abstractmethod
    def add_player_to_match(self, match_id: int, user_id: int, starting_hole_number: int = 1) -> Dict[str, Any]:
        """
        Añade un jugador a un partido.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            starting_hole_number: Número del hoyo donde empieza el jugador (default: 1)
            
        Returns:
            Diccionario con la información de la relación match_player creada
            
        Raises:
            ValueError: Si el partido o el usuario no existen, o si el jugador ya está en el partido
        """
        pass
    
    @abstractmethod
    def get_match_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un partido por su ID.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con la información del partido si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_match_players(self, match_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los jugadores de un partido.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Lista de diccionarios con información de los jugadores del partido
        """
        pass
    
    @abstractmethod
    def record_hole_score(self, match_id: int, user_id: int, hole_id: int, strokes: int) -> Dict[str, Any]:
        """
        Registra la puntuación de un jugador en un hoyo.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            strokes: Número de golpes en el hoyo
            
        Returns:
            Diccionario con la información del score registrado
            
        Raises:
            ValueError: Si el partido, jugador o hoyo no existen, o si el jugador no está en el partido
        """
        pass
    
    @abstractmethod
    def increment_hole_strokes(self, match_id: int, user_id: int, hole_id: int, strokes: int = 1) -> Dict[str, Any]:
        """
        Incrementa el número de golpes de un jugador en un hoyo.
        
        Si el jugador no tiene registro en ese hoyo, crea uno con el número de golpes especificado.
        Si ya tiene registro, incrementa el valor existente.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            strokes: Número de golpes a incrementar (default: 1)
            
        Returns:
            Diccionario con la información del score actualizado
            
        Raises:
            ValueError: Si el partido, jugador o hoyo no existen, o si el jugador no está en el partido
        """
        pass
    
    @abstractmethod
    def get_player_scores(self, match_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las puntuaciones de un jugador en un partido.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Lista de diccionarios con información de las puntuaciones por hoyo
        """
        pass
    
    @abstractmethod
    def calculate_player_total_strokes(self, match_id: int, user_id: int) -> int:
        """
        Calcula el total de golpes de un jugador en un partido.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Total de golpes del jugador en el partido
        """
        pass
    
    @abstractmethod
    def get_match_leaderboard(self, match_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene el ranking de jugadores de un partido ordenado por total de golpes (menor a mayor).
        
        Args:
            match_id: ID del partido
            
        Returns:
            Lista de diccionarios con información de jugadores ordenados por total de golpes
        """
        pass
    
    @abstractmethod
    def complete_match(self, match_id: int) -> Dict[str, Any]:
        """
        Marca un partido como completado y calcula los totales de golpes de todos los jugadores.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con la información del partido actualizado
            
        Raises:
            ValueError: Si el partido no existe o ya está completado
        """
        pass
    
    @abstractmethod
    def get_matches_by_course(self, course_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de un campo de golf.
        
        Args:
            course_id: ID del campo de golf
            status: Filtro opcional por estado (in_progress, completed, cancelled)
            
        Returns:
            Lista de diccionarios con información de los partidos
        """
        pass
    
    @abstractmethod
    def get_matches_by_player(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de un jugador.
        
        Args:
            user_id: ID del usuario/jugador
            status: Filtro opcional por estado (in_progress, completed, cancelled)
            
        Returns:
            Lista de diccionarios con información de los partidos
        """
        pass
    
    @abstractmethod
    def get_hole_strokes_for_player(self, match_id: int, user_id: int, hole_id: int) -> int:
        """
        Obtiene el número de golpes de un jugador en un hoyo específico.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            
        Returns:
            Número de golpes en ese hoyo (0 si no tiene registro)
        """
        pass
    
    @abstractmethod
    def get_player_ranking(self, match_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el ranking de un jugador en un partido.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Diccionario con información del ranking del jugador, None si no está en el partido
        """
        pass
    
    @abstractmethod
    def create_stroke(self, match_id: int, user_id: int, hole_id: int, stroke_number: int,
                     ball_start_latitude: float, ball_start_longitude: float,
                     club_used_id: Optional[int] = None, trajectory_type: Optional[str] = None,
                     proposed_distance_meters: Optional[float] = None,
                     proposed_club_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Crea un registro de golpe individual para evaluación posterior.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            stroke_number: Número de golpe en el hoyo
            ball_start_latitude: Latitud inicial de la bola
            ball_start_longitude: Longitud inicial de la bola
            club_used_id: ID del palo utilizado (opcional)
            trajectory_type: Tipo de trayectoria escogida (conservadora, riesgo, optima) (opcional)
            proposed_distance_meters: Distancia propuesta en metros (opcional)
            proposed_club_id: ID del palo propuesto (opcional)
            
        Returns:
            Diccionario con la información del golpe creado
        """
        pass
    
    @abstractmethod
    def get_last_unevaluated_stroke(self, match_id: int, user_id: int, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último golpe no evaluado de un jugador en un hoyo.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con la información del golpe si existe, None si no
        """
        pass
    
    @abstractmethod
    def evaluate_stroke(self, stroke_id: int, ball_end_latitude: float, ball_end_longitude: float,
                      ball_end_distance_meters: float, evaluation_quality: Optional[float],
                      evaluation_distance_error: float, evaluation_direction_error: float) -> Dict[str, Any]:
        """
        Evalúa un golpe con la posición final de la bola.
        
        Args:
            stroke_id: ID del golpe
            ball_end_latitude: Latitud final de la bola
            ball_end_longitude: Longitud final de la bola
            ball_end_distance_meters: Distancia real alcanzada en metros
            evaluation_quality: Calidad del golpe (0-100)
            evaluation_distance_error: Error en distancia (metros)
            evaluation_direction_error: Error en dirección
            
        Returns:
            Diccionario con la información del golpe evaluado
        """
        pass
    
    @abstractmethod
    def get_last_stroke_in_hole(self, match_id: int, user_id: int, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último golpe (evaluado o no) de un jugador en un hoyo.
        Útil para evaluar el golpe que metió la bola en el hoyo.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            
        Returns:
            Diccionario con la información del golpe si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_all_strokes_in_hole(self, match_id: int, user_id: int, hole_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los golpes de un jugador en un hoyo.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los golpes
        """
        pass
    
    @abstractmethod
    def get_match_state(self, match_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual del partido para un jugador.
        
        Incluye:
        - course_id: ID del campo
        - current_hole_number: Hoyo actual en el que está jugando
        - strokes_in_current_hole: Número de golpes en el hoyo actual
        - completed_holes: Lista de hoyos completados con sus puntuaciones
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Diccionario con el estado del partido o None si no existe
        """
        pass
    
    @abstractmethod
    def update_current_hole(self, match_id: int, user_id: int, hole_number: int) -> bool:
        """
        Actualiza el hoyo actual en el que está jugando un jugador.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_number: Número del hoyo actual
            
        Returns:
            True si se actualizó correctamente, False si no
        """
        pass
        """
        Obtiene todos los golpes de un jugador en un hoyo, ordenados por fecha de creación.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_id: ID del hoyo
            
        Returns:
            Lista de diccionarios con información de los golpes, ordenados por created_at ASC
        """
        pass

