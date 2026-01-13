# -*- coding: utf-8 -*-
"""
Servicio de dominio para lógica de negocio relacionada con partidos.

Contiene los casos de uso del dominio sin depender de implementaciones técnicas.
"""
from typing import Optional, Dict, Any, List
from kdi_back.domain.ports.match_repository import MatchRepository
from kdi_back.domain.ports.golf_repository import GolfRepository


class MatchService:
    """
    Servicio de dominio para operaciones de partidos.
    
    Contiene la lógica de negocio pura, sin dependencias técnicas.
    """
    
    def __init__(self, match_repository: MatchRepository, golf_repository: Optional[GolfRepository] = None):
        """
        Inicializa el servicio con un repositorio.
        
        Args:
            match_repository: Implementación del repositorio de partidos
            golf_repository: Implementación del repositorio de golf (opcional, para convertir course_id/hole_number a hole_id)
        """
        self.match_repository = match_repository
        self.golf_repository = golf_repository
    
    def _get_hole_id_from_course_and_number(self, course_id: int, hole_number: int) -> int:
        """
        Obtiene el hole_id desde course_id y hole_number.
        
        Args:
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            
        Returns:
            ID del hoyo
            
        Raises:
            ValueError: Si el hoyo no existe o no se puede obtener
        """
        if not self.golf_repository:
            raise ValueError("golf_repository no está disponible. No se puede convertir course_id/hole_number a hole_id.")
        
        hole = self.golf_repository.get_hole_by_course_and_number(course_id, hole_number)
        if not hole:
            raise ValueError(f"No existe un hoyo con course_id={course_id} y hole_number={hole_number}")
        
        return hole['id']
    
    def create_match(self, course_id: int, name: Optional[str] = None, 
                    player_ids: Optional[List[int]] = None,
                    starting_holes: Optional[Dict[int, int]] = None) -> Dict[str, Any]:
        """
        Crea un nuevo partido con jugadores opcionales.
        
        Args:
            course_id: ID del campo de golf
            name: Nombre opcional del partido
            player_ids: Lista opcional de IDs de jugadores a añadir
            starting_holes: Diccionario opcional {user_id: starting_hole_number}
            
        Returns:
            Diccionario con la información del partido creado y sus jugadores
        """
        # Validaciones de negocio
        if not isinstance(course_id, int) or course_id <= 0:
            raise ValueError("El course_id debe ser un entero positivo")
        
        if name and not isinstance(name, str):
            raise ValueError("El nombre del partido debe ser una cadena de texto")
        
        # Crear el partido
        match = self.match_repository.create_match(course_id, name)
        
        # Añadir jugadores si se proporcionaron
        players = []
        if player_ids:
            for user_id in player_ids:
                starting_hole = starting_holes.get(user_id, 1) if starting_holes else 1
                try:
                    player = self.match_repository.add_player_to_match(
                        match['id'], user_id, starting_hole
                    )
                    players.append(player)
                except ValueError as e:
                    # Si hay error añadiendo un jugador, continuar con los demás
                    print(f"Advertencia: No se pudo añadir el jugador {user_id}: {e}")
        
        return {
            "match": match,
            "players": players
        }
    
    def add_player_to_match(self, match_id: int, user_id: int, starting_hole_number: int = 1) -> Dict[str, Any]:
        """
        Añade un jugador a un partido existente.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            starting_hole_number: Número del hoyo donde empieza el jugador (default: 1)
            
        Returns:
            Diccionario con la información de la relación match_player creada
        """
        # Validaciones de negocio
        if not isinstance(match_id, int) or match_id <= 0:
            raise ValueError("El match_id debe ser un entero positivo")
        
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("El user_id debe ser un entero positivo")
        
        if not isinstance(starting_hole_number, int) or starting_hole_number < 1:
            raise ValueError("El starting_hole_number debe ser un entero mayor o igual a 1")
        
        # Verificar que el partido existe y no está completado
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError("No se pueden añadir jugadores a un partido completado")
        
        if match['status'] == 'cancelled':
            raise ValueError("No se pueden añadir jugadores a un partido cancelado")
        
        return self.match_repository.add_player_to_match(match_id, user_id, starting_hole_number)
    
    def record_hole_score(self, match_id: int, user_id: int, course_id: int, hole_number: int, strokes: int) -> Dict[str, Any]:
        """
        Registra la puntuación de un jugador en un hoyo.
        
        Cuando se setea el total de golpes de un hoyo (en lugar de incrementar uno a uno),
        se eliminan todos los strokes pendientes de evaluación de ese hoyo, ya que el hoyo
        está finalizado y no se necesitan evaluar golpes individuales.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            strokes: Número total de golpes en el hoyo (setea el valor, no incrementa)
            
        Returns:
            Diccionario con la información del score registrado
        """
        # Validaciones de negocio
        if not isinstance(match_id, int) or match_id <= 0:
            raise ValueError("El match_id debe ser un entero positivo")
        
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("El user_id debe ser un entero positivo")
        
        if not isinstance(course_id, int) or course_id <= 0:
            raise ValueError("El course_id debe ser un entero positivo")
        
        if not isinstance(hole_number, int) or hole_number <= 0:
            raise ValueError("El hole_number debe ser un entero positivo")
        
        if not isinstance(strokes, int) or strokes <= 0:
            raise ValueError("El número de golpes debe ser un entero positivo")
        
        # Verificar que el partido existe y no está completado o cancelado
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError("No se pueden registrar golpes en un partido completado")
        
        if match['status'] == 'cancelled':
            raise ValueError("No se pueden registrar golpes en un partido cancelado")
        
        # Convertir course_id y hole_number a hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        # Registrar el score
        score = self.match_repository.record_hole_score(match_id, user_id, hole_id, strokes)
        
        # Actualizar el hoyo actual al siguiente (si se completó un hoyo)
        # Obtener el estado actual para determinar el siguiente hoyo
        match_state = self.match_repository.get_match_state(match_id, user_id)
        if match_state:
            # Calcular el siguiente hoyo
            # Si el hoyo completado es el actual, avanzar al siguiente
            if match_state['current_hole_number'] == hole_number:
                # Verificar cuántos hoyos tiene el campo (asumiendo 18, pero debería obtenerse de la BD)
                # Por ahora, avanzamos al siguiente hoyo
                next_hole = hole_number + 1
                # Actualizar el estado (solo si hay más hoyos, pero por ahora siempre actualizamos)
                self.match_repository.update_current_hole(match_id, user_id, next_hole)
        
        return score
    
    def increment_hole_strokes(self, match_id: int, user_id: int, course_id: int, hole_number: int, strokes: int = 1) -> Dict[str, Any]:
        """
        Incrementa el número de golpes de un jugador en un hoyo.
        
        Si el jugador no tiene registro en ese hoyo, crea uno con el número de golpes especificado.
        Si ya tiene registro, incrementa el valor existente.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            strokes: Número de golpes a incrementar (default: 1)
            
        Returns:
            Diccionario con la información del score actualizado
        """
        # Validaciones de negocio
        if not isinstance(match_id, int) or match_id <= 0:
            raise ValueError("El match_id debe ser un entero positivo")
        
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("El user_id debe ser un entero positivo")
        
        if not isinstance(course_id, int) or course_id <= 0:
            raise ValueError("El course_id debe ser un entero positivo")
        
        if not isinstance(hole_number, int) or hole_number <= 0:
            raise ValueError("El hole_number debe ser un entero positivo")
        
        if not isinstance(strokes, int) or strokes <= 0:
            raise ValueError("El número de golpes a incrementar debe ser un entero positivo")
        
        # Verificar que el partido existe y no está completado o cancelado
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError("No se pueden registrar golpes en un partido completado")
        
        if match['status'] == 'cancelled':
            raise ValueError("No se pueden registrar golpes en un partido cancelado")
        
        # Convertir course_id y hole_number a hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        return self.match_repository.increment_hole_strokes(match_id, user_id, hole_id, strokes)
    
    def get_match_details(self, match_id: int) -> Dict[str, Any]:
        """
        Obtiene los detalles completos de un partido, incluyendo jugadores y leaderboard.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con información completa del partido
        """
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        players = self.match_repository.get_match_players(match_id)
        leaderboard = self.match_repository.get_match_leaderboard(match_id)
        
        return {
            "match": match,
            "players": players,
            "leaderboard": leaderboard
        }
    
    def complete_match(self, match_id: int) -> Dict[str, Any]:
        """
        Completa un partido, calculando los totales y determinando el ganador.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con información del partido completado y el ganador
        """
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError("El partido ya está completado")
        
        if match['status'] == 'cancelled':
            raise ValueError("No se puede completar un partido cancelado")
        
        # Completar el partido
        completed_match = self.match_repository.complete_match(match_id)
        
        # Obtener el leaderboard para determinar el ganador
        leaderboard = self.match_repository.get_match_leaderboard(match_id)
        
        # El ganador es el que tiene menos golpes (primer lugar en el leaderboard)
        winner = leaderboard[0] if leaderboard else None
        
        return {
            "match": completed_match,
            "leaderboard": leaderboard,
            "winner": winner
        }
    
    def get_match_leaderboard(self, match_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene el ranking de jugadores de un partido.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Lista de jugadores ordenados por total de golpes
        """
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        return self.match_repository.get_match_leaderboard(match_id)
    
    def get_player_scores(self, match_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las puntuaciones de un jugador en un partido.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Lista de puntuaciones por hoyo
        """
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        return self.match_repository.get_player_scores(match_id, user_id)
    
    def get_matches_by_course(self, course_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de un campo de golf.
        
        Args:
            course_id: ID del campo de golf
            status: Filtro opcional por estado
            
        Returns:
            Lista de partidos
        """
        if status and status not in ['in_progress', 'completed', 'cancelled']:
            raise ValueError("El status debe ser: in_progress, completed o cancelled")
        
        return self.match_repository.get_matches_by_course(course_id, status)
    
    def get_matches_by_player(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de un jugador.
        
        Args:
            user_id: ID del usuario/jugador
            status: Filtro opcional por estado
            
        Returns:
            Lista de partidos
        """
        if status and status not in ['in_progress', 'completed', 'cancelled']:
            raise ValueError("El status debe ser: in_progress, completed o cancelled")
        
        return self.match_repository.get_matches_by_player(user_id, status)
    
    def complete_hole(self, match_id: int, user_id: int, course_id: int, hole_number: int) -> Dict[str, Any]:
        """
        Marca el final de un hoyo para un jugador y retorna estadísticas.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            
        Returns:
            Diccionario con:
            - hole_strokes: Total de golpes en ese hoyo
            - total_strokes: Total de golpes del jugador en la partida
            - ranking: Información del ranking del jugador
        """
        # Validaciones de negocio
        if not isinstance(match_id, int) or match_id <= 0:
            raise ValueError("El match_id debe ser un entero positivo")
        
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("El user_id debe ser un entero positivo")
        
        if not isinstance(course_id, int) or course_id <= 0:
            raise ValueError("El course_id debe ser un entero positivo")
        
        if not isinstance(hole_number, int) or hole_number <= 0:
            raise ValueError("El hole_number debe ser un entero positivo")
        
        # Verificar que el partido existe
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError("No se pueden completar hoyos en un partido completado")
        
        if match['status'] == 'cancelled':
            raise ValueError("No se pueden completar hoyos en un partido cancelado")
        
        # Convertir course_id y hole_number a hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        # Obtener golpes en ese hoyo
        hole_strokes = self.match_repository.get_hole_strokes_for_player(match_id, user_id, hole_id)
        
        # Evaluar el último golpe que metió la bola en el hoyo
        green_evaluation = None
        if self.golf_repository:
            # Obtener todos los golpes del hoyo para contar los del green
            all_strokes = self.match_repository.get_all_strokes_in_hole(match_id, user_id, hole_id)
            
            if all_strokes:
                # Contar golpes en el green (golpes que comenzaron en el green)
                green_strokes = 0
                last_stroke = all_strokes[-1] if all_strokes else None
                
                # Recorrer todos los golpes contando los que comenzaron en el green
                for stroke in all_strokes:
                    ball_start_on_green = self.golf_repository.is_ball_on_green(
                        hole_id,
                        stroke['ball_start_latitude'],
                        stroke['ball_start_longitude']
                    )
                    
                    if ball_start_on_green:
                        green_strokes += 1
                
                # Si hay golpes en el green, evaluar el último golpe que metió la bola
                if green_strokes > 0:
                    # El último golpe que no comenzó en el green es el que metió la bola en el green
                    # O si todos comenzaron en el green, el primero es el que metió la bola
                    stroke_to_evaluate = None
                    for stroke in reversed(all_strokes):
                        ball_start_on_green = self.golf_repository.is_ball_on_green(
                            hole_id,
                            stroke['ball_start_latitude'],
                            stroke['ball_start_longitude']
                        )
                        if not ball_start_on_green:
                            stroke_to_evaluate = stroke
                            break
                    
                    # Si no encontramos uno que no comenzó en el green, usar el primero (el que metió la bola)
                    if not stroke_to_evaluate and all_strokes:
                        stroke_to_evaluate = all_strokes[0]
                    
                    # Evaluar con las reglas del green
                    if stroke_to_evaluate and not stroke_to_evaluate.get('evaluated'):
                        green_evaluation = self.evaluate_green_strokes(
                            match_id=match_id,
                            user_id=user_id,
                            course_id=course_id,
                            hole_number=hole_number,
                            total_green_strokes=green_strokes,
                            stroke_to_evaluate=stroke_to_evaluate
                        )
                elif last_stroke and not last_stroke.get('evaluated'):
                    # Si no hay golpes en el green pero hay un golpe sin evaluar, evaluarlo normalmente
                    # Esto puede pasar si el último golpe fue desde fuera del green
                    try:
                        # Evaluar el golpe que metió la bola
                        green_evaluation = self.evaluate_stroke(
                            match_id=match_id,
                            user_id=user_id,
                            course_id=course_id,
                            hole_number=hole_number,
                            ball_end_latitude=last_stroke['ball_start_latitude'],  # Aproximación
                            ball_end_longitude=last_stroke['ball_start_longitude'],  # Aproximación
                            is_on_green=True  # Asumimos que terminó en el hoyo
                        )
                    except Exception as e:
                        print(f"Advertencia: No se pudo evaluar el último golpe: {e}")
        
        # Obtener total de golpes en la partida
        total_strokes = self.match_repository.calculate_player_total_strokes(match_id, user_id)
        
        # Obtener ranking
        ranking = self.match_repository.get_player_ranking(match_id, user_id)
        if not ranking:
            raise ValueError(f"El jugador {user_id} no está en el partido {match_id}")
        
        # Actualizar el hoyo actual al siguiente (si se completó el hoyo actual)
        # Obtener el estado actual para determinar el siguiente hoyo
        match_state = self.match_repository.get_match_state(match_id, user_id)
        if match_state:
            # Si el hoyo completado es el actual, avanzar al siguiente
            if match_state['current_hole_number'] == hole_number:
                # Verificar cuántos hoyos tiene el campo (asumiendo 18, pero debería obtenerse de la BD)
                # Por ahora, avanzamos al siguiente hoyo
                next_hole = hole_number + 1
                # Actualizar el estado (solo si hay más hoyos, pero por ahora siempre actualizamos)
                self.match_repository.update_current_hole(match_id, user_id, next_hole)
        
        result = {
            "hole_strokes": hole_strokes,
            "total_strokes": total_strokes,
            "ranking": ranking
        }
        
        # Agregar evaluación del green si existe
        if green_evaluation:
            result["green_evaluation"] = {
                "stroke_id": green_evaluation.get('id'),
                "evaluation_quality": green_evaluation.get('evaluation_quality'),
                "evaluation_distance_error": green_evaluation.get('evaluation_distance_error'),
                "evaluation_direction_error": green_evaluation.get('evaluation_direction_error')
            }
        
        return result
    
    def create_stroke(self, match_id: int, user_id: int, course_id: int, hole_number: int,
                     ball_start_latitude: float, ball_start_longitude: float,
                     stroke_number: int, club_used_id: Optional[int] = None,
                     club_used_name: Optional[str] = None,
                     trajectory_type: Optional[str] = None,
                     proposed_distance_meters: Optional[float] = None,
                     proposed_club_id: Optional[int] = None,
                     proposed_club_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un registro de golpe individual para evaluación posterior.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            ball_start_latitude: Latitud inicial de la bola
            ball_start_longitude: Longitud inicial de la bola
            stroke_number: Número de golpe en el hoyo
            club_used_id: ID del palo utilizado (opcional)
            club_used_name: Nombre del palo utilizado (opcional, se busca si no se proporciona club_used_id)
            trajectory_type: Tipo de trayectoria escogida (conservadora, riesgo, optima) (opcional)
            proposed_distance_meters: Distancia propuesta en metros (opcional)
            proposed_club_id: ID del palo propuesto (opcional)
            proposed_club_name: Nombre del palo propuesto (opcional, se busca si no se proporciona proposed_club_id)
            
        Returns:
            Diccionario con la información del golpe creado
        """
        # Validaciones
        if not isinstance(match_id, int) or match_id <= 0:
            raise ValueError("El match_id debe ser un entero positivo")
        
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("El user_id debe ser un entero positivo")
        
        if not (-90 <= ball_start_latitude <= 90):
            raise ValueError(f"Latitud inválida: {ball_start_latitude}")
        
        if not (-180 <= ball_start_longitude <= 180):
            raise ValueError(f"Longitud inválida: {ball_start_longitude}")
        
        if not isinstance(stroke_number, int) or stroke_number <= 0:
            raise ValueError("El stroke_number debe ser un entero positivo")
        
        # Obtener hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        # Buscar club_used_id si se proporciona el nombre
        if club_used_name and not club_used_id:
            # Necesitamos acceso al player_repository para buscar el palo
            # Por ahora, si no se proporciona el ID, no lo guardamos
            pass
        
        # Buscar proposed_club_id si se proporciona el nombre
        if proposed_club_name and not proposed_club_id:
            # Similar al anterior
            pass
        
        # Validar trajectory_type
        if trajectory_type and trajectory_type not in ('conservadora', 'riesgo', 'optima'):
            raise ValueError(f"trajectory_type debe ser 'conservadora', 'riesgo' o 'optima', recibido: {trajectory_type}")
        
        # Crear el golpe
        return self.match_repository.create_stroke(
            match_id=match_id,
            user_id=user_id,
            hole_id=hole_id,
            stroke_number=stroke_number,
            ball_start_latitude=ball_start_latitude,
            ball_start_longitude=ball_start_longitude,
            club_used_id=club_used_id,
            trajectory_type=trajectory_type,
            proposed_distance_meters=proposed_distance_meters,
            proposed_club_id=proposed_club_id
        )
    
    def _validate_stroke_makes_sense(
        self,
        stroke: Dict[str, Any],
        ball_end_latitude: float,
        ball_end_longitude: float,
        hole_id: int,
        current_strokes: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Valida que un golpe tiene sentido antes de evaluarlo.
        
        Validaciones:
        1. El stroke_number corresponde al golpe anterior al actual (stroke_number == current_strokes - 1)
        2. La distancia es alcanzable: no mayor a un 30% más de la mayor distancia promedio del jugador
        3. La trayectoria es razonablemente recta (no hay desviaciones extremas)
        4. El hoyo es el mismo (ya verificado por hole_id)
        
        Args:
            stroke: Diccionario con información del stroke pendiente
            ball_end_latitude: Latitud final de la bola
            ball_end_longitude: Longitud final de la bola
            hole_id: ID del hoyo
            current_strokes: Número actual de golpes en el hoyo
            user_id: ID del usuario (opcional, para validación de estadísticas)
            
        Returns:
            Diccionario con:
            - is_valid: bool - Si el golpe tiene sentido
            - validation_errors: List[str] - Lista de errores de validación
            - actual_distance: float - Distancia real calculada
        """
        validation_errors = []
        actual_distance = 0.0
        
        # 1. Validar que el stroke_number corresponde al golpe anterior
        stroke_number = stroke.get('stroke_number', 0)
        expected_stroke_number = current_strokes - 1
        
        if stroke_number != expected_stroke_number:
            validation_errors.append(
                f"El stroke_number ({stroke_number}) no corresponde al golpe anterior esperado ({expected_stroke_number}). "
                f"Golpes actuales en el hoyo: {current_strokes}"
            )
            return {
                'is_valid': False,
                'validation_errors': validation_errors,
                'actual_distance': 0.0
            }
        
        # 2. Calcular distancia real
        if not self.golf_repository:
            validation_errors.append("No se puede calcular la distancia: golf_repository no disponible")
            return {
                'is_valid': False,
                'validation_errors': validation_errors,
                'actual_distance': 0.0
            }
        
        actual_distance = self.golf_repository.calculate_distance_between_points(
            stroke['ball_start_latitude'],
            stroke['ball_start_longitude'],
            ball_end_latitude,
            ball_end_longitude
        )
        
        # 3. Validar distancia alcanzable
        # La distancia máxima permitida es: mayor distancia promedio del jugador * 1.3 (30% más)
        if actual_distance > 0:
            max_allowed_distance = None
            
            # Intentar obtener estadísticas del jugador para calcular distancia máxima permitida
            try:
                # Importar aquí para evitar dependencia circular
                from kdi_back.api.dependencies import get_player_service
                player_service = get_player_service()
                
                if user_id:
                    # Obtener perfil del jugador
                    player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
                    
                    if player_profile:
                        # Obtener estadísticas de todos los palos del jugador
                        player_club_statistics = player_service.player_repository.get_player_club_statistics(
                            player_profile['id']
                        )
                        
                        if player_club_statistics and len(player_club_statistics) > 0:
                            # Encontrar la mayor distancia promedio entre todas las estadísticas
                            max_avg_distance = 0.0
                            for stat in player_club_statistics:
                                avg_distance = stat.get('average_distance_meters', 0)
                                if avg_distance > max_avg_distance:
                                    max_avg_distance = avg_distance
                            
                            # Calcular distancia máxima permitida: mayor distancia promedio * 1.3 (30% más)
                            if max_avg_distance > 0:
                                max_allowed_distance = max_avg_distance * 1.3
            except Exception as e:
                # Si hay error obteniendo estadísticas, continuar sin validación personalizada
                print(f"Advertencia: No se pudieron obtener estadísticas del jugador para validación: {e}")
            
            # Si no se pudo obtener distancia máxima personalizada, usar valor conservador por defecto
            if max_allowed_distance is None:
                max_allowed_distance = 350.0  # Valor conservador por defecto (350m)
            
            # Validar que la distancia no exceda el máximo permitido
            if actual_distance > max_allowed_distance:
                validation_errors.append(
                    f"La distancia alcanzada ({actual_distance:.1f}m) excede el máximo permitido "
                    f"({max_allowed_distance:.1f}m). Puede ser un error de GPS."
                )
        
        # 4. Validar trayectoria razonablemente recta
        # Calcular ángulo de desviación desde la posición inicial hacia el objetivo
        # Si hay distancia propuesta, verificar que la desviación no sea extrema
        proposed_distance = stroke.get('proposed_distance_meters')
        if proposed_distance and actual_distance > 0:
            # Calcular distancia al objetivo (bandera) desde posición inicial
            distance_to_flag_start = self.golf_repository.calculate_distance_to_hole(
                hole_id,
                stroke['ball_start_latitude'],
                stroke['ball_start_longitude']
            )
            
            if distance_to_flag_start:
                # Calcular distancia al objetivo desde posición final
                distance_to_flag_end = self.golf_repository.calculate_distance_to_hole(
                    hole_id,
                    ball_end_latitude,
                    ball_end_longitude
                )
                
                if distance_to_flag_end is not None:
                    # La trayectoria es razonable si la bola se acercó al objetivo
                    # o si la desviación lateral no es excesiva
                    # Calcular desviación lateral aproximada usando ley de cosenos
                    # Si la distancia final al objetivo es mucho mayor que la esperada, puede ser un error
                    expected_final_distance = max(0, distance_to_flag_start - proposed_distance)
                    
                    # Permitir hasta 50m de desviación lateral adicional
                    max_lateral_deviation = 50.0
                    if distance_to_flag_end > expected_final_distance + max_lateral_deviation:
                        # Verificar si la desviación es realmente excesiva
                        deviation_ratio = distance_to_flag_end / max(expected_final_distance, 1)
                        if deviation_ratio > 2.0:  # Más del doble de lo esperado
                            validation_errors.append(
                                f"La trayectoria parece tener una desviación excesiva. "
                                f"Distancia esperada al objetivo: {expected_final_distance:.1f}m, "
                                f"distancia real: {distance_to_flag_end:.1f}m. Puede ser un error de GPS."
                            )
        
        return {
            'is_valid': len(validation_errors) == 0,
            'validation_errors': validation_errors,
            'actual_distance': actual_distance
        }
    
    def evaluate_stroke(self, match_id: int, user_id: int, course_id: int, hole_number: int,
                       ball_end_latitude: float, ball_end_longitude: float,
                       target_latitude: Optional[float] = None,
                       target_longitude: Optional[float] = None,
                       is_on_green: Optional[bool] = None,
                       current_strokes: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Evalúa el último golpe no evaluado de un jugador en un hoyo.
        
        Antes de evaluar, valida que:
        1. El stroke pendiente es realmente el anterior al golpe actual (verifica stroke_number)
        2. La distancia es alcanzable según el palo usado
        3. La trayectoria es razonablemente recta
        4. El hoyo es el mismo
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            ball_end_latitude: Latitud final de la bola
            ball_end_longitude: Longitud final de la bola
            target_latitude: Latitud del objetivo (bandera o waypoint) (opcional, se calcula si no se proporciona)
            target_longitude: Longitud del objetivo (opcional, se calcula si no se proporciona)
            is_on_green: Si la bola terminó en el green (opcional, se detecta si no se proporciona)
            current_strokes: Número actual de golpes en el hoyo (opcional, se obtiene si no se proporciona)
            
        Returns:
            Diccionario con la información de la evaluación si se encontró un golpe válido, None si no
        """
        # Validaciones básicas
        if not (-90 <= ball_end_latitude <= 90):
            raise ValueError(f"Latitud inválida: {ball_end_latitude}")
        
        if not (-180 <= ball_end_longitude <= 180):
            raise ValueError(f"Longitud inválida: {ball_end_longitude}")
        
        # Obtener hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        # Obtener número actual de golpes si no se proporciona
        if current_strokes is None:
            current_strokes = self.match_repository.get_hole_strokes_for_player(match_id, user_id, hole_id)
        
        # Buscar el último golpe no evaluado
        stroke = self.match_repository.get_last_unevaluated_stroke(match_id, user_id, hole_id)
        if not stroke:
            return None
        
        # VALIDACIÓN: Verificar que el golpe tiene sentido antes de evaluarlo
        validation = self._validate_stroke_makes_sense(
            stroke=stroke,
            ball_end_latitude=ball_end_latitude,
            ball_end_longitude=ball_end_longitude,
            hole_id=hole_id,
            current_strokes=current_strokes,
            user_id=user_id
        )
        
        # Si la validación falla, retornar None (no evaluar)
        if not validation['is_valid']:
            print(f"⚠️ Golpe no evaluado - Errores de validación: {', '.join(validation['validation_errors'])}")
            return None
        
        # Usar la distancia calculada en la validación
        actual_distance = validation['actual_distance']
        
        # Detectar si la bola terminó en el green
        if is_on_green is None:
            is_on_green = self.golf_repository.is_ball_on_green(hole_id, ball_end_latitude, ball_end_longitude)
        
        # Detectar si el golpe comenzó en el green
        ball_start_on_green = self.golf_repository.is_ball_on_green(
            hole_id, stroke['ball_start_latitude'], stroke['ball_start_longitude']
        )
        
        # Si el golpe comenzó Y terminó en el green, NO evaluar (solo marcar como evaluado)
        if ball_start_on_green and is_on_green:
            # Marcar como evaluado sin calidad (los golpes en el green no se evalúan)
            evaluated_stroke = self.match_repository.evaluate_stroke(
                stroke_id=stroke['id'],
                ball_end_latitude=ball_end_latitude,
                ball_end_longitude=ball_end_longitude,
                ball_end_distance_meters=0,  # No relevante para green
                evaluation_quality=None,  # Sin evaluación
                evaluation_distance_error=0,
                evaluation_direction_error=0
            )
            return evaluated_stroke
        
        # Obtener distancia objetivo
        # Prioridad: 1) distancia propuesta, 2) distancia a bandera calculada, 3) distancia real como fallback
        if stroke.get('proposed_distance_meters'):
            target_distance = float(stroke['proposed_distance_meters'])
        else:
            # Calcular distancia a la bandera desde la posición inicial
            distance_to_flag = self.golf_repository.calculate_distance_to_hole(
                hole_id,
                stroke['ball_start_latitude'],
                stroke['ball_start_longitude']
            )
            if distance_to_flag is not None:
                target_distance = distance_to_flag
            else:
                # Si no hay bandera, usar la distancia real como referencia (no ideal pero funcional)
                target_distance = actual_distance
        
        # Calcular errores
        # Usar distancia propuesta si está disponible, sino usar target_distance
        reference_distance = stroke.get('proposed_distance_meters') or target_distance
        distance_error = abs(actual_distance - reference_distance) if reference_distance else 0
        
        # Calcular calidad del golpe (0-100)
        # Basado en el error de distancia: 100 si es perfecto, disminuye con el error
        if reference_distance and reference_distance > 0:
            # Error porcentual respecto a la distancia de referencia
            error_percentage = (distance_error / reference_distance) * 100
        else:
            # Si no hay distancia de referencia, calidad neutra
            error_percentage = 50
        
        # Calidad: 100 - error_percentage, con un mínimo de 0
        quality_score = max(0, min(100, 100 - error_percentage))
        
        # Calcular error de dirección (simplificado: distancia al objetivo final)
        if target_latitude and target_longitude:
            direction_error = self.golf_repository.calculate_distance_between_points(
                ball_end_latitude,
                ball_end_longitude,
                target_latitude,
                target_longitude
            )
        else:
            direction_error = 0  # No podemos calcular sin objetivo
        
        # Evaluar el golpe
        evaluated_stroke = self.match_repository.evaluate_stroke(
            stroke_id=stroke['id'],
            ball_end_latitude=ball_end_latitude,
            ball_end_longitude=ball_end_longitude,
            ball_end_distance_meters=actual_distance,
            evaluation_quality=quality_score,
            evaluation_distance_error=distance_error,
            evaluation_direction_error=direction_error
        )
        
        return evaluated_stroke
    
    def evaluate_green_strokes(self, match_id: int, user_id: int, course_id: int, hole_number: int,
                               total_green_strokes: int, stroke_to_evaluate: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Evalúa los golpes en el green cuando se completa el hoyo.
        
        Reglas de evaluación del green:
        - 0 golpes: muy bueno (100) - no debería pasar aquí
        - 1 golpe: bueno (80)
        - 2 golpes: correcto (60)
        - 3 golpes: malo (40)
        - 4+ golpes: muy malo (20 - (strokes - 4) * 5, mínimo 0)
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            course_id: ID del campo de golf
            hole_number: Número del hoyo
            total_green_strokes: Total de golpes en el green
            stroke_to_evaluate: Golpe específico a evaluar (opcional, se busca si no se proporciona)
            
        Returns:
            Diccionario con la evaluación del green si hay golpes en el green, None si no
        """
        if total_green_strokes == 0:
            return None
        
        # Obtener hole_id
        hole_id = self._get_hole_id_from_course_and_number(course_id, hole_number)
        
        # Buscar el golpe a evaluar
        if not stroke_to_evaluate:
            # Buscar el último golpe (evaluado o no) que metió la bola en el hoyo
            stroke_to_evaluate = self.match_repository.get_last_stroke_in_hole(match_id, user_id, hole_id)
        
        if not stroke_to_evaluate:
            return None
        
        # Si ya está evaluado, no hacer nada
        if stroke_to_evaluate.get('evaluated'):
            return None
        
        # Calcular calidad según reglas del green
        if total_green_strokes == 1:
            quality_score = 80  # Bueno
        elif total_green_strokes == 2:
            quality_score = 60  # Correcto
        elif total_green_strokes == 3:
            quality_score = 40  # Malo
        else:
            # 4+ golpes: muy malo, disminuye con cada golpe adicional
            quality_score = max(0, 20 - (total_green_strokes - 4) * 5)
        
        # Obtener posición de la bandera para la posición final
        if self.golf_repository:
            # Intentar obtener posición de la bandera
            distance_to_flag = self.golf_repository.calculate_distance_to_hole(
                hole_id,
                stroke_to_evaluate['ball_start_latitude'],
                stroke_to_evaluate['ball_start_longitude']
            )
            # Usar posición inicial como aproximación si no hay bandera
            ball_end_lat = stroke_to_evaluate['ball_start_latitude']
            ball_end_lon = stroke_to_evaluate['ball_start_longitude']
        else:
            ball_end_lat = stroke_to_evaluate['ball_start_latitude']
            ball_end_lon = stroke_to_evaluate['ball_start_longitude']
        
        # Marcar como evaluado con la calidad del green
        evaluated_stroke = self.match_repository.evaluate_stroke(
            stroke_id=stroke_to_evaluate['id'],
            ball_end_latitude=ball_end_lat,
            ball_end_longitude=ball_end_lon,
            ball_end_distance_meters=0,  # En el hoyo
            evaluation_quality=quality_score,
            evaluation_distance_error=0,
            evaluation_direction_error=0
        )
        
        return evaluated_stroke
    
    def get_match_state(self, match_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual del partido para un jugador.
        
        Incluye:
        - course_id: ID del campo
        - current_hole_number: Hoyo actual en el que está jugando
        - current_hole_id: ID del hoyo actual
        - strokes_in_current_hole: Número de golpes en el hoyo actual
        - completed_holes: Lista de hoyos completados con sus puntuaciones
        - total_strokes: Total de golpes en el partido
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Diccionario con el estado del partido o None si no existe
        """
        return self.match_repository.get_match_state(match_id, user_id)
    
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
        return self.match_repository.update_current_hole(match_id, user_id, hole_number)

