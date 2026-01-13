# -*- coding: utf-8 -*-
"""
Servicio de dominio para procesar comandos de voz durante un partido de golf.

Este servicio actúa como router/dispatcher que:
1. Clasifica la intención de la petición
2. Enruta a la funcionalidad correspondiente
3. Formatea la respuesta en lenguaje natural
"""
from typing import Optional, Dict, Any, List
from kdi_back.infrastructure.agents.intent_classifier_agent import classify_intent
from kdi_back.domain.services.golf_service import GolfService
from kdi_back.domain.services.match_service import MatchService
from kdi_back.domain.services.player_service import PlayerService


class VoiceService:
    """
    Servicio de dominio para procesar comandos de voz durante un partido.
    
    Contiene la lógica de negocio para clasificar intenciones y enrutar peticiones.
    """
    
    def __init__(
        self,
        golf_service: GolfService,
        match_service: MatchService,
        player_service: Optional[PlayerService] = None
    ):
        """
        Inicializa el servicio con sus dependencias.
        
        Args:
            golf_service: Servicio de golf para operaciones del campo
            match_service: Servicio de partidos para operaciones del partido
            player_service: Servicio de jugadores (opcional)
        """
        self.golf_service = golf_service
        self.match_service = match_service
        self.player_service = player_service
    
    def process_voice_command(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Procesa un comando de voz durante un partido.
        
        Args:
            user_id: ID del usuario autenticado
            match_id: ID del partido
            course_id: ID del campo de golf
            latitude: Latitud GPS de la posición de la bola
            longitude: Longitud GPS de la posición de la bola
            query: Petición en lenguaje natural
            
        Returns:
            Diccionario con:
            - response: Respuesta en lenguaje natural
            - intent: Tipo de intención detectada
            - confidence: Nivel de confianza de la clasificación
            - data: Datos adicionales según el tipo de petición
            
        Raises:
            ValueError: Si los datos no son válidos o el usuario no está en el partido
        """
        # Validaciones básicas
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitud inválida: {latitude}")
        
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitud inválida: {longitude}")
        
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("El query debe ser una cadena de texto no vacía")
        
        # Verificar que el usuario está en el partido
        match = self.match_service.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        # Verificar que el partido está en progreso
        if match['status'] != 'in_progress':
            raise ValueError(f"El partido {match_id} no está en progreso (estado: {match['status']})")
        
        # Verificar que el usuario está en el partido
        match_players = self.match_service.match_repository.get_match_players(match_id)
        user_in_match = any(mp['user_id'] == user_id for mp in match_players)
        if not user_in_match:
            raise ValueError(f"El usuario {user_id} no está en el partido {match_id}")
        
        # Verificar que el course_id del partido coincide
        if match['course_id'] != course_id:
            raise ValueError(f"El partido {match_id} pertenece al campo {match['course_id']}, no al {course_id}")
        
        # Detectar si el query contiene múltiples confirmaciones de hoyos
        # Esto puede ser una respuesta a una solicitud de confirmación previa
        multiple_confirmations = self._extract_multiple_hole_confirmations(query)
        if len(multiple_confirmations) >= 2:
            # Si hay múltiples confirmaciones, procesar directamente como confirmación
            result = self._handle_require_hole_confirmation(
                user_id=user_id,
                match_id=match_id,
                course_id=course_id,
                latitude=latitude,
                longitude=longitude,
                query=query
            )
            return {
                'response': result['response'],
                'intent': 'require_hole_confirmation',
                'confidence': 1.0,
                'data': result.get('data', {})
            }
        
        # Clasificar intención
        intent_result = classify_intent(query)
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        
        # Detectar si el query menciona un hoyo específico
        # Esto es importante para validar consistencia antes de procesar
        mentioned_hole = self._extract_mentioned_hole_number(query)
        
        # Si se menciona un hoyo específico y es diferente al actual, verificar consistencia
        if mentioned_hole:
            match_state = self.match_service.get_match_state(match_id, user_id)
            if match_state:
                current_hole = match_state['current_hole_number']
                if mentioned_hole > current_hole:
                    # Verificar si hay hoyos sin completar
                    consistency = self._check_hole_consistency(
                        match_id, user_id, course_id, mentioned_hole
                    )
                    
                    if not consistency['is_consistent']:
                        # Hay hoyos sin completar, retornar respuesta especial
                        missing_holes = consistency['missing_holes']
                        if len(missing_holes) == 1:
                            response = f"Antes de continuar, necesito que confirmes el resultado del hoyo {missing_holes[0]}. ¿Cuántos golpes realizaste en el hoyo {missing_holes[0]}?"
                        else:
                            holes_str = ', '.join(map(str, missing_holes[:-1])) + f" y {missing_holes[-1]}"
                            response = f"Antes de continuar, necesito que confirmes el resultado de los hoyos {holes_str}. ¿Cuántos golpes realizaste en cada uno de estos hoyos?"
                        
                        return {
                            'response': response,
                            'intent': 'require_hole_confirmation',
                            'confidence': 1.0,
                            'data': {
                                'missing_holes': missing_holes,
                                'current_hole': current_hole,
                                'target_hole': mentioned_hole,
                                'requires_confirmation': True,
                                'original_query': query,  # Guardar query original para referencia
                                'original_intent': intent  # Guardar intención original
                            }
                        }
        
        # Enrutar según intención
        handler_method = getattr(self, f'_handle_{intent}', None)
        if not handler_method:
            # Si no hay handler, usar fallback
            intent = 'recommend_shot'
            handler_method = self._handle_recommend_shot
        
        # Ejecutar handler
        try:
            result = handler_method(
                user_id=user_id,
                match_id=match_id,
                course_id=course_id,
                latitude=latitude,
                longitude=longitude,
                query=query
            )
            
            return {
                'response': result['response'],
                'intent': intent,
                'confidence': confidence,
                'data': result.get('data', {})
            }
        except Exception as e:
            # Si hay error en el handler, retornar mensaje de error amigable
            return {
                'response': f"Lo siento, no pude procesar tu petición: {str(e)}",
                'intent': intent,
                'confidence': confidence,
                'error': str(e)
            }
    
    def _get_hole_info_from_state_or_gps(
        self,
        match_id: int,
        user_id: int,
        course_id: int,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del hoyo desde el estado persistido del partido o desde GPS.
        
        Prioriza el estado persistido si está disponible, usa GPS como fallback.
        
        Returns:
            Diccionario con información del hoyo (hole_info) o None si no se puede obtener.
        """
        hole_info = None
        hole_id = None
        hole_number = None
        
        # Intentar obtener el estado persistido del partido
        if match_id and user_id:
            try:
                match_state = self.match_service.get_match_state(match_id, user_id)
                
                if match_state:
                    # Usar el estado persistido del partido
                    course_id = match_state['course_id']
                    hole_number = match_state['current_hole_number']
                    hole_id = match_state['current_hole_id']
                    
                    # Obtener información completa del hoyo
                    hole_info = self.golf_service.get_hole_by_course_and_number(course_id, hole_number)
                    
                    if hole_info:
                        # Si hole_id no está en el estado, obtenerlo
                        if not hole_id:
                            hole_id = hole_info['id']
                        return hole_info
            except Exception as e:
                # Si hay error obteniendo el estado, continuar con la lógica normal
                print(f"Advertencia: No se pudo obtener el estado del partido, usando identificación GPS: {e}")
        
        # Fallback: Identificar el hoyo desde coordenadas GPS
        try:
            hole_info = self.golf_service.identify_hole_by_ball_position(latitude, longitude)
            return hole_info
        except Exception as e:
            print(f"Advertencia: No se pudo identificar el hoyo desde GPS: {e}")
            return None
    
    def _extract_mentioned_hole_number(self, query: str) -> Optional[int]:
        """
        Extrae el número de hoyo mencionado en el query, si existe.
        
        Busca patrones como:
        - "hoyo X"
        - "hoyo número X"
        - "en el hoyo X"
        - "para el hoyo X"
        - "del hoyo X"
        - "hoyo X" seguido de cualquier cosa
        
        Returns:
            Número del hoyo mencionado o None si no se menciona
        """
        import re
        
        query_lower = query.lower()
        
        # Patrón 1: "hoyo X" o "hoyo número X" (más general)
        pattern1 = r'hoyo\s+(?:n[úu]mero\s+)?(\d+)'
        match1 = re.search(pattern1, query_lower)
        if match1:
            return int(match1.group(1))
        
        # Patrón 2: "en el hoyo X" o "para el hoyo X" o "del hoyo X"
        pattern2 = r'(?:en|para|del)\s+(?:el\s+)?hoyo\s+(\d+)'
        match2 = re.search(pattern2, query_lower)
        if match2:
            return int(match2.group(1))
        
        # Patrón 3: "estoy en el X" o "jugando el X" (contexto de hoyo)
        pattern3 = r'(?:estoy\s+)?(?:en|jugando)\s+(?:el\s+)?(\d+)'
        match3 = re.search(pattern3, query_lower)
        if match3:
            hole_num = int(match3.group(1))
            # Validar que sea un número razonable de hoyo (1-18 típicamente)
            if 1 <= hole_num <= 18:
                return hole_num
        
        return None
    
    def _extract_hole_and_strokes_from_query(self, query: str) -> Dict[str, Any]:
        """
        Extrae número de hoyo y golpes de un query en lenguaje natural.
        
        Busca patrones como:
        - "hoyo X con Y golpes"
        - "hoyo X a Y golpes"
        - "X golpes en el hoyo Y"
        - "Y golpes" (solo golpes, para el hoyo actual)
        
        Returns:
            Diccionario con:
            - hole_number: Número del hoyo (None si no se especifica)
            - strokes: Número de golpes (None si no se especifica)
        """
        import re
        
        query_lower = query.lower()
        result = {'hole_number': None, 'strokes': None}
        
        # Patrón 1: "hoyo X con Y golpes" o "hoyo X a Y golpes"
        pattern1 = r'hoyo\s+(\d+)\s+(?:con|a)\s+(\d+)\s+golpes?'
        match1 = re.search(pattern1, query_lower)
        if match1:
            result['hole_number'] = int(match1.group(1))
            result['strokes'] = int(match1.group(2))
            return result
        
        # Patrón 2: "Y golpes en el hoyo X"
        pattern2 = r'(\d+)\s+golpes?\s+en\s+(?:el\s+)?hoyo\s+(\d+)'
        match2 = re.search(pattern2, query_lower)
        if match2:
            result['strokes'] = int(match2.group(1))
            result['hole_number'] = int(match2.group(2))
            return result
        
        # Patrón 3: "corrige/cambia/modifica el resultado del hoyo X (a/con) Y golpes"
        pattern3 = r'(?:corrige|cambia|modifica|actualiza)\s+(?:el\s+)?(?:resultado\s+)?(?:del\s+)?hoyo\s+(\d+)\s+(?:a|con|con\s+)?\s*(\d+)\s+golpes?'
        match3 = re.search(pattern3, query_lower)
        if match3:
            result['hole_number'] = int(match3.group(1))
            result['strokes'] = int(match3.group(2))
            return result
        
        # Patrón 4: Solo número de golpes (para el hoyo actual)
        pattern4 = r'(?:con|a|de)\s+(\d+)\s+golpes?'
        match4 = re.search(pattern4, query_lower)
        if match4:
            result['strokes'] = int(match4.group(1))
            return result
        
        # Patrón 5: Solo número al final (puede ser golpes)
        pattern5 = r'\b(\d+)\s*(?:golpes?)?\s*$'
        match5 = re.search(pattern5, query_lower)
        if match5 and not result['strokes']:
            # Si no hemos encontrado golpes antes, asumir que es golpes
            result['strokes'] = int(match5.group(1))
        
        return result
    
    def _extract_multiple_hole_confirmations(self, query: str) -> List[Dict[str, Any]]:
        """
        Extrae múltiples confirmaciones de hoyos del query.
        
        Busca patrones como:
        - "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes"
        - "5: 4 golpes, 6: 5 golpes"
        - "Hoyo 5: 4, hoyo 6: 5"
        
        Returns:
            Lista de diccionarios con 'hole_number' y 'strokes'
        """
        import re
        
        confirmations = []
        query_lower = query.lower()
        
        # Patrón 1: "Hoyo X con Y golpes" (múltiples, separados por comas o "y")
        pattern1 = r'hoyo\s+(\d+)\s+(?:con|:)\s+(\d+)\s*golpes?'
        matches1 = re.finditer(pattern1, query_lower)
        for match in matches1:
            confirmations.append({
                'hole_number': int(match.group(1)),
                'strokes': int(match.group(2))
            })
        
        # Si no se encontraron con el patrón completo, intentar patrones más flexibles
        if not confirmations:
            # Patrón 2: "X: Y golpes" o "X: Y" (asumiendo que X es hoyo si está en rango 1-18)
            pattern2 = r'(\d+)\s*:\s*(\d+)\s*(?:golpes?)?'
            matches2 = re.finditer(pattern2, query_lower)
            for match in matches2:
                num1 = int(match.group(1))
                num2 = int(match.group(2))
                # Validar que num1 sea un número razonable de hoyo (1-18) y num2 sea golpes (1-20)
                if 1 <= num1 <= 18 and 1 <= num2 <= 20:
                    confirmations.append({
                        'hole_number': num1,
                        'strokes': num2
                    })
        
        # Si aún no hay confirmaciones, intentar extraer pares "hoyo X Y golpes"
        if not confirmations:
            # Patrón 3: "hoyo X Y golpes" (sin preposición)
            pattern3 = r'hoyo\s+(\d+)\s+(\d+)\s+golpes?'
            matches3 = re.finditer(pattern3, query_lower)
            for match in matches3:
                confirmations.append({
                    'hole_number': int(match.group(1)),
                    'strokes': int(match.group(2))
                })
        
        return confirmations
    
    def _get_missing_holes_between(self, match_id: int, user_id: int, course_id: int, 
                                   from_hole: int, to_hole: int) -> List[int]:
        """
        Obtiene la lista de hoyos sin completar entre from_hole y to_hole (excluyendo to_hole).
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario
            course_id: ID del campo
            from_hole: Hoyo inicial (inclusive)
            to_hole: Hoyo objetivo (exclusive)
            
        Returns:
            Lista de números de hoyos sin completar
        """
        if from_hole >= to_hole:
            return []  # No hay hoyos entre ellos
        
        # Obtener estado del partido
        match_state = self.match_service.get_match_state(match_id, user_id)
        if not match_state:
            return list(range(from_hole, to_hole))
        
        # Obtener hoyos completados
        completed_holes = {h['hole_number'] for h in match_state.get('completed_holes', [])}
        
        # Encontrar hoyos sin completar entre from_hole y to_hole
        missing_holes = []
        for hole_num in range(from_hole, to_hole):
            if hole_num not in completed_holes:
                missing_holes.append(hole_num)
        
        return missing_holes
    
    def _check_hole_consistency(self, match_id: int, user_id: int, course_id: int,
                                target_hole_number: int) -> Dict[str, Any]:
        """
        Verifica la consistencia del hoyo objetivo con el estado actual del partido.
        
        Si el jugador está en el hoyo X pero pide algo para el hoyo Y (Y > X),
        verifica si hay hoyos sin completar entre X e Y.
        
        Returns:
            Diccionario con:
            - is_consistent: True si es consistente, False si hay hoyos sin completar
            - missing_holes: Lista de hoyos sin completar (vacía si es consistente)
            - current_hole: Hoyo actual del estado
            - target_hole: Hoyo objetivo
        """
        match_state = self.match_service.get_match_state(match_id, user_id)
        if not match_state:
            return {
                'is_consistent': True,
                'missing_holes': [],
                'current_hole': None,
                'target_hole': target_hole_number
            }
        
        current_hole = match_state['current_hole_number']
        
        # Si el hoyo objetivo es menor o igual al actual, es consistente
        if target_hole_number <= current_hole:
            return {
                'is_consistent': True,
                'missing_holes': [],
                'current_hole': current_hole,
                'target_hole': target_hole_number
            }
        
        # Si el hoyo objetivo es mayor, verificar si hay hoyos sin completar
        missing_holes = self._get_missing_holes_between(
            match_id, user_id, course_id, current_hole, target_hole_number
        )
        
        return {
            'is_consistent': len(missing_holes) == 0,
            'missing_holes': missing_holes,
            'current_hole': current_hole,
            'target_hole': target_hole_number
        }
    
    def _handle_recommend_shot(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones de recomendación de golpe.
        
        Usa el endpoint trajectory-options-evol para obtener recomendaciones.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás. Por favor, asegúrate de estar en el campo de golf.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        course_id = hole_info['course_id']
        hole_number = hole_info['hole_number']
        
        # Obtener estadísticas del jugador y perfil
        player_club_statistics = None
        player_profile = None
        if self.player_service:
            try:
                player_profile = self.player_service.player_repository.get_player_profile_by_user_id(user_id)
                if player_profile:
                    player_club_statistics = self.player_service.player_repository.get_player_club_statistics(
                        player_profile['id']
                    )
            except Exception as e:
                print(f"Advertencia: No se pudo obtener perfil del jugador: {e}")
        
        # Determinar si el jugador está en el green
        is_on_green = self.golf_service.golf_repository.is_ball_on_green(hole_id, latitude, longitude)
        
        # Determinar si el jugador está en el tee de salida y obtener el tee correcto
        tee_position = self._get_appropriate_tee_position(
            hole_id, course_id, hole_number, latitude, longitude, player_profile
        )
        
        # Usar posición del tee si está en el tee, sino usar posición actual
        calculation_latitude = tee_position['latitude'] if tee_position else latitude
        calculation_longitude = tee_position['longitude'] if tee_position else longitude
        
        # Obtener distancia según la posición del jugador
        if is_on_green:
            # Si está en el green, usar distancia al hoyo (flag)
            distance_to_target = self.golf_service.golf_repository.calculate_distance_to_hole(
                hole_id, calculation_latitude, calculation_longitude
            )
            distance_reference = "hoyo"
        else:
            # Si está fuera del green, usar distancia al inicio del green (punto final del último optimal_shot)
            distance_to_target = self.golf_service.golf_repository.calculate_distance_to_green_start(
                hole_id, calculation_latitude, calculation_longitude
            )
            distance_reference = "inicio del green"
        
        if distance_to_target is None:
            return {
                'response': f"El hoyo {hole_number} no tiene la información necesaria. No puedo darte una recomendación precisa.",
                'data': {'hole_number': hole_number}
            }
        
        # Usar posición de cálculo (tee si está en tee, sino posición actual)
        calculation_lat = calculation_latitude
        calculation_lon = calculation_longitude
        
        # Ejecutar algoritmo evolutivo (misma lógica que trajectory-options-evol)
        trayectorias_optimal = self.golf_service.bola_menos_10m_optimal_shot(
            latitude=calculation_lat,
            longitude=calculation_lon,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics
        )
        
        trayectorias_completas = self.golf_service.find_strategic_shot(
            latitude=calculation_lat,
            longitude=calculation_lon,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics,
            trayectorias_existentes=trayectorias_optimal
        )
        
        resultado_final = self.golf_service.evaluacion_final(trayectorias_completas)
        
        trayectoria_optima = resultado_final.get('trayectoria_optima')
        trayectoria_conservadora = resultado_final.get('trayectoria_conservadora')
        trayectoria_riesgo = resultado_final.get('trayectoria_riesgo')
        
        # Si no hay trayectoria válida
        if not isinstance(trayectoria_optima, dict):
            return {
                'response': "No pude calcular una trayectoria óptima para tu posición actual. Te recomiendo jugar conservador y buscar la calle.",
                'data': {'hole_info': hole_info}
            }
        
        # Guardar distancia para uso posterior
        distance_to_flag = distance_to_target  # Mantener nombre de variable para compatibilidad
        
        # Extraer información de la trayectoria óptima
        distance_meters = trayectoria_optima.get('distance_meters', 0)
        distance_yards = trayectoria_optima.get('distance_yards', 0)
        club_rec = trayectoria_optima.get('club_recommendation', {})
        recommended_club = club_rec.get('recommended_club', 'un palo apropiado')
        swing_type = club_rec.get('swing_type', 'completo')
        target = trayectoria_optima.get('target', 'flag')
        waypoint_desc = trayectoria_optima.get('waypoint_description')
        obstacles = trayectoria_optima.get('obstacles', [])
        risk_level = trayectoria_optima.get('risk_level', {})
        risk_total = risk_level.get('total', 0) if isinstance(risk_level, dict) else 0
        is_optimal_shot = trayectoria_optima.get('is_optimal_shot', False)
        
        # Construir respuesta en lenguaje natural según nuevo patrón
        response_parts = []
        
        # 2. Determinar objetivo del campo y tipo de swing (necesario antes de generar mensajes)
        if swing_type == 'completo':
            swing_text = "con swing completo"
        elif swing_type == '3/4':
            swing_text = "con swing de tres cuartos"
        elif swing_type == '1/2':
            swing_text = "con swing de medio"
        else:
            swing_text = "con swing completo"  # Default
        
        # Si está en el green, usar mensaje especial basado en golpes vs par
        if is_on_green:
            # Obtener número de golpes actuales y par del hoyo
            current_strokes = 0
            par = None
            try:
                current_strokes = self.match_service.match_repository.get_hole_strokes_for_player(
                    match_id, user_id, hole_id
                )
                par = hole_info.get('par')
            except Exception as e:
                print(f"Advertencia: No se pudo obtener golpes actuales: {e}")
            
            # Generar mensaje especial para green
            green_message = self._generate_green_message(
                current_strokes, par, distance_to_target, recommended_club, swing_text
            )
            if green_message:
                response_parts.append(green_message)
            else:
                # Fallback al mensaje normal si no se puede generar el especial
                response_parts.append(f"Estás a {distance_to_target:.0f} metros del {distance_reference}")
        else:
            # 1. Distancia al objetivo (inicio del green si está fuera)
            response_parts.append(f"Estás a {distance_to_target:.0f} metros del {distance_reference}")
        
        # Determinar objetivo del campo
        if target == 'flag':
            objetivo_campo = "el green"
        elif is_optimal_shot:
            # Para optimal_shots, siempre usar "centro de la calle" con referencias visuales si hay obstáculos
            objetivo_campo = self._format_optimal_shot_target(obstacles)
        elif waypoint_desc:
            # Para strategic_points, extraer el nombre descriptivo
            # waypoint_desc puede ser "Centro calle antes de bunkers a 170m de green"
            # Necesitamos extraer la parte relevante (ej: "centro de calle", "antegreen")
            objetivo_campo = self._extract_field_target(waypoint_desc)
        else:
            objetivo_campo = "el punto estratégico"
        
        # 3. Recomendación principal (solo si no está en el green, ya que en green tiene mensaje especial)
        if not is_on_green:
            # Calcular distancia que quedará después del golpe para determinar si alcanza el green
            distancia_despues = None
            if distance_to_target is not None:
                distancia_despues = distance_to_target - distance_meters
            
            # Si el golpe alcanza o pasa el green, no incluir la distancia del golpe
            if distancia_despues is not None and distancia_despues <= 0:
                # El golpe alcanzará o pasará el inicio del green - no incluir distancia
                if objetivo_campo == "el green":
                    response_parts.append(f"Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green")
                else:
                    response_parts.append(f"Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar {objetivo_campo}")
            else:
                # El golpe no alcanza el green - incluir distancia
                response_parts.append(f"Te recomiendo utilizar {recommended_club} {swing_text} para hacer {distance_meters:.0f} metros {objetivo_campo}")
        
        # 4. Calcular distancia que quedará después del golpe (solo si no está en el green)
        if not is_on_green and distance_to_target is not None:
            distancia_despues = distance_to_target - distance_meters
            
            # Si la distancia recomendada alcanza o pasa el objetivo
            if distancia_despues <= 0:
                # El golpe alcanzará o pasará el inicio del green
                if risk_total <= 30:
                    response_parts.append("Esta es una opción segura")
                else:
                    response_parts.append("Esta opción te permitirá alcanzar el green")
            elif distancia_despues > 0:
                # Determinar idea del siguiente golpe basado en la distancia restante
                siguiente_golpe = self._get_next_shot_description(distancia_despues, target, waypoint_desc, is_on_green)
                if siguiente_golpe:
                    # Determinar si es opción segura o de riesgo
                    if risk_total <= 30:
                        referencia = "inicio del green"
                        # Si distancia > 120m, no incluir tipo de golpe
                        if distancia_despues > 120:
                            response_parts.append(f"Esta es una opción segura que te dejará a {distancia_despues:.0f} metros del {referencia}")
                        else:
                            tipo_golpe = self._get_shot_type_from_distance(distancia_despues)
                            if tipo_golpe:
                                response_parts.append(f"Esta es una opción segura que te dejará a {distancia_despues:.0f} metros del {referencia} para {tipo_golpe}")
                            else:
                                response_parts.append(f"Esta es una opción segura que te dejará a {distancia_despues:.0f} metros del {referencia}")
                    else:
                        response_parts.append(f"Esta opción te permitirá {siguiente_golpe}")
        
        # 5. Otras opciones (conservadora o de riesgo)
        if trayectoria_conservadora and isinstance(trayectoria_conservadora, dict):
            opcion_alternativa = self._format_alternative_trajectory(trayectoria_conservadora, distance_to_target, "conservadora", is_on_green)
            if opcion_alternativa:
                response_parts.append(opcion_alternativa)
        elif trayectoria_riesgo and isinstance(trayectoria_riesgo, dict):
            opcion_alternativa = self._format_alternative_trajectory(trayectoria_riesgo, distance_to_target, "riesgo", is_on_green)
            if opcion_alternativa:
                response_parts.append(opcion_alternativa)
        
        response = ". ".join(response_parts) + "."
        
        return {
            'response': response,
            'data': {
                'distance_meters': distance_meters,
                'distance_yards': distance_yards,
                'recommended_club': recommended_club,
                'swing_type': swing_type,
                'target': target,
                'waypoint_description': waypoint_desc,
                'obstacles_count': len(obstacles),
                'risk_level': risk_total,
                'hole_info': hole_info
            }
        }
    
    def _format_optimal_shot_target(self, obstacles: List[Dict[str, Any]]) -> str:
        """
        Formatea el objetivo del campo para optimal_shots.
        Siempre usa "centro de la calle" y añade referencias visuales si hay obstáculos cercanos.
        
        Args:
            obstacles: Lista de obstáculos en la trayectoria
            
        Returns:
            String formateado como "al centro de la calle" o "buscando el centro de la calle a la altura del..."
        """
        if not obstacles or len(obstacles) == 0:
            return "al centro de la calle"
        
        # Buscar el obstáculo más relevante (bunkers son los más comunes para referencias visuales)
        bunker_obstacles = [obs for obs in obstacles if obs.get('type') == 'bunker']
        
        if bunker_obstacles:
            # Tomar el primer bunker encontrado
            bunker = bunker_obstacles[0]
            bunker_name = bunker.get('name', '')
            
            if bunker_name:
                referencia = self._parse_obstacle_reference(bunker_name)
                if referencia:
                    return f"buscando el centro de la calle a la altura de {referencia}"
        
        # Si no hay bunkers, usar el primer obstáculo relevante
        if obstacles:
            obs = obstacles[0]
            obs_name = obs.get('name', '')
            if obs_name and obs.get('type') in ['bunker', 'water', 'trees']:
                referencia = self._parse_obstacle_reference(obs_name)
                if referencia:
                    return f"buscando el centro de la calle a la altura de {referencia}"
        
        return "al centro de la calle"
    
    def _parse_obstacle_reference(self, obstacle_name: str) -> Optional[str]:
        """
        Parsea el nombre del obstáculo y lo convierte a lenguaje natural.
        
        Formato esperado: "{Tipo} {Lado} {Hoyo}_{Posición}"
        Ejemplos:
        - "Bunker derecho 1_1" → "el primer bunker que tienes a la derecha"
        - "Bunker izquierdo 2_2" → "el segundo bunker de la izquierda"
        - "Agua izquierdo 3_1" → "el agua que tienes a la izquierda"
        
        Args:
            obstacle_name: Nombre del obstáculo (ej: "Bunker derecho 1_1")
            
        Returns:
            String formateado en lenguaje natural o None si no se puede parsear
        """
        if not obstacle_name:
            return None
        
        # Dividir el nombre en partes
        parts = obstacle_name.split()
        if len(parts) < 2:
            return None
        
        # Extraer tipo, lado y posición
        tipo = parts[0].lower()  # "bunker", "agua", "trees", etc.
        lado = parts[1].lower() if len(parts) > 1 else None
        
        # Buscar posición (formato: "1_1", "2_2", etc.)
        posicion_str = None
        for part in parts:
            if '_' in part:
                posicion_str = part
                break
        
        # Convertir tipo a español
        tipo_espanol = {
            'bunker': 'bunker',
            'agua': 'agua',
            'water': 'agua',
            'trees': 'árboles',
            'arboles': 'árboles'
        }.get(tipo, tipo)
        
        # Convertir lado a español
        lado_espanol = {
            'derecho': 'derecha',
            'derecha': 'derecha',
            'izquierdo': 'izquierda',
            'izquierda': 'izquierda'
        }.get(lado, lado) if lado else None
        
        # Convertir posición a número ordinal
        posicion_num = None
        if posicion_str:
            try:
                # Extraer el número después del guion bajo
                posicion_num = int(posicion_str.split('_')[1])
            except (ValueError, IndexError):
                pass
        
        # Construir referencia
        if posicion_num and lado_espanol:
            # Números ordinales en español
            ordinales = {
                1: 'primer',
                2: 'segundo',
                3: 'tercer',
                4: 'cuarto',
                5: 'quinto',
                6: 'sexto',
                7: 'séptimo',
                8: 'octavo',
                9: 'noveno',
                10: 'décimo'
            }
            ordinal = ordinales.get(posicion_num, f'{posicion_num}º')
            
            if lado_espanol == 'derecha':
                return f"el {ordinal} {tipo_espanol} que tienes a la derecha"
            elif lado_espanol == 'izquierda':
                return f"el {ordinal} {tipo_espanol} de la izquierda"
        elif lado_espanol:
            # Si no hay posición, usar solo el lado
            if lado_espanol == 'derecha':
                return f"el {tipo_espanol} que tienes a la derecha"
            elif lado_espanol == 'izquierda':
                return f"el {tipo_espanol} de la izquierda"
        
        return None
    
    def _generate_green_message(
        self, 
        current_strokes: int, 
        par: Optional[int], 
        distance_to_hole: float,
        recommended_club: str,
        swing_text: str
    ) -> Optional[str]:
        """
        Genera un mensaje especial cuando el jugador está en el green.
        El mensaje depende del número de golpes actuales vs el par del hoyo.
        
        Args:
            current_strokes: Número de golpes actuales en el hoyo
            par: Par del hoyo (None si no está disponible)
            distance_to_hole: Distancia al hoyo en metros
            recommended_club: Palo recomendado
            swing_text: Texto del tipo de swing
            
        Returns:
            Mensaje formateado o None si no se puede generar
        """
        if par is None:
            # Si no hay par, usar mensaje genérico (sin distancia)
            return f"Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green."
        
        # Calcular resultado si mete la bola en este putt
        strokes_if_made = current_strokes + 1
        result_vs_par = strokes_if_made - par
        
        # Generar mensaje según el resultado (sin incluir distancia al hoyo)
        if result_vs_par < 0:
            # Birdie o mejor (eagle, albatross)
            if result_vs_par == -1:
                return f"Metiendo la bola haces un birdie, pero evalúa la posibilidad de un golpe de aproximación para asegurar el par."
            elif result_vs_par == -2:
                return f"Metiendo la bola haces un eagle, pero evalúa la posibilidad de un golpe de aproximación para asegurar el par."
            else:
                return f"Metiendo la bola haces un resultado excelente ({abs(result_vs_par)} bajo par), pero evalúa la posibilidad de un golpe de aproximación para asegurar el par."
        elif result_vs_par == 0:
            # Par
            return f"Metiendo la bola haces par. Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green."
        elif result_vs_par == 1:
            # Bogey
            return f"Metiendo la bola haces un bogey. Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green."
        elif result_vs_par == 2:
            # Doble bogey
            return f"Metiendo la bola haces un doble bogey. Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green."
        else:
            # Triple bogey o peor
            return f"Metiendo la bola haces {result_vs_par} sobre par. Te recomiendo utilizar {recommended_club} {swing_text} para alcanzar el green."
    
    def _get_appropriate_tee_position(
        self,
        hole_id: int,
        course_id: int,
        hole_number: int,
        latitude: float,
        longitude: float,
        player_profile: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Determina el tee de salida apropiado según el género y nivel del jugador.
        
        Reglas:
        - Mujer (no profesional) → Tee rojo
        - Hombre (no profesional) → Tee amarillo
        - Profesional (hombre o mujer) → Tee blanco
        
        Si el jugador está cerca del tee de salida, devuelve las coordenadas del tee correcto.
        Si no está en el tee, devuelve None.
        
        Args:
            hole_id: ID del hoyo
            course_id: ID del campo
            hole_number: Número del hoyo
            latitude: Latitud actual de la bola
            longitude: Longitud actual de la bola
            player_profile: Perfil del jugador (con gender y skill_level)
            
        Returns:
            Diccionario con 'latitude' y 'longitude' del tee apropiado si está en el tee,
            None si no está en el tee o no se puede determinar
        """
        if not player_profile:
            return None
        
        gender = player_profile.get('gender', '').lower() if player_profile.get('gender') else None
        skill_level = player_profile.get('skill_level', '').lower() if player_profile.get('skill_level') else None
        
        # Determinar tipo de tee según reglas
        is_professional = skill_level == 'professional'
        
        if is_professional:
            tee_type = 'tee_white'
        elif gender == 'female':
            tee_type = 'tee'  # tee rojo (tee sin sufijo es rojo)
        elif gender == 'male':
            tee_type = 'tee_yellow'
        else:
            # Si no hay género definido, usar tee amarillo por defecto
            tee_type = 'tee_yellow'
        
        # Obtener geometría del hoyo para encontrar los tees
        try:
            hole_geometry = self.golf_service.golf_repository.get_hole_geometry(course_id, hole_number)
            if not hole_geometry or 'tees' not in hole_geometry:
                return None
            
            # Buscar el tee apropiado
            tees = hole_geometry.get('tees', [])
            target_tee = None
            
            # Mapear tipo de tee a formato normalizado
            tee_type_map = {
                'tee_white': 'white',
                'tee_yellow': 'yellow',
                'tee': 'red',
                'tee_red': 'red'
            }
            target_tee_type = tee_type_map.get(tee_type, 'yellow')
            
            for tee in tees:
                if tee.get('type') == target_tee_type:
                    target_tee = tee
                    break
            
            if not target_tee:
                return None
            
            # Verificar si el jugador está cerca del tee (dentro de 10 metros)
            tee_lat = target_tee.get('latitude')
            tee_lon = target_tee.get('longitude')
            
            if tee_lat and tee_lon:
                distance_to_tee = self.golf_service.golf_repository.calculate_distance_between_points(
                    latitude, longitude, tee_lat, tee_lon
                )
                
                # Si está cerca del tee (dentro de 10 metros), usar el tee como posición de cálculo
                if distance_to_tee <= 10.0:
                    return {
                        'latitude': tee_lat,
                        'longitude': tee_lon,
                        'tee_type': target_tee_type
                    }
            
            return None
        except Exception as e:
            print(f"Advertencia: No se pudo obtener tee apropiado: {e}")
            return None
    
    def _extract_field_target(self, waypoint_desc: str) -> str:
        """
        Extrae el objetivo del campo desde la descripción del waypoint.
        Ejemplos:
        - "Centro calle antes de bunkers a 170m de green" -> "el centro de calle"
        - "Antegreen para chip a 12m de green" -> "el antegreen"
        - "Centro calle a 100m de green" -> "el centro de calle"
        """
        if not waypoint_desc:
            return "el punto estratégico"
        
        waypoint_lower = waypoint_desc.lower()
        
        # Buscar patrones comunes
        if "centro calle" in waypoint_lower or "centro de calle" in waypoint_lower:
            return "el centro de calle"
        elif "antegreen" in waypoint_lower:
            return "el antegreen"
        elif "approach" in waypoint_lower:
            return "la zona de approach"
        elif "layup" in waypoint_lower:
            return "la zona de layup"
        elif "green" in waypoint_lower:
            return "el green"
        else:
            # Si no coincide con ningún patrón, usar la descripción original
            # pero simplificada (tomar las primeras palabras)
            palabras = waypoint_desc.split()
            if len(palabras) > 3:
                return f"el {palabras[0].lower()}"
            return waypoint_desc.lower()
    
    def _get_next_shot_description(self, distancia_restante: float, target: str, waypoint_desc: Optional[str] = None, is_on_green: bool = False) -> Optional[str]:
        """
        Determina la descripción del siguiente golpe basado en la distancia restante.
        
        Args:
            distancia_restante: Distancia restante en metros
            target: Tipo de objetivo ('flag', 'waypoint', etc.)
            waypoint_desc: Descripción del waypoint (opcional)
            is_on_green: Si el jugador está en el green (usa "hoyo" en lugar de "inicio del green")
        """
        referencia = "hoyo" if is_on_green else "inicio del green"
        
        if distancia_restante <= 0:
            return f"alcanzar el {referencia}" if not is_on_green else "alcanzar el hoyo"
        
        # Si la distancia es mayor a 120m, no usar la palabra "approach"
        if distancia_restante > 120:
            return f"quedar a {distancia_restante:.0f} metros del {referencia}"
        
        # Construir mensaje: "quedar a X metros del {referencia} para {tipo}"
        tipo_siguiente = self._get_shot_type_from_distance(distancia_restante)
        return f"quedar a {distancia_restante:.0f} metros del {referencia} para {tipo_siguiente}"
    
    def _get_shot_type_from_distance(self, distancia: float) -> str:
        """
        Determina el tipo de golpe basado en la distancia al green.
        Nota: No devuelve "approach" si la distancia es mayor a 120m.
        """
        if distancia <= 20:
            return "chip o putt"
        elif distancia <= 50:
            return "approach corto"
        elif distancia <= 100:
            return "approach medio"
        elif distancia <= 120:
            return "approach largo"
        else:
            # Para distancias > 120m, no usar "approach"
            return ""  # Se manejará en _get_next_shot_description o se omitirá
    
    def _format_alternative_trajectory(self, trayectoria: Dict[str, Any], distance_to_target: Optional[float], tipo: str, is_on_green: bool = False) -> Optional[str]:
        """
        Formatea una trayectoria alternativa (conservadora o de riesgo) para el mensaje.
        """
        if not isinstance(trayectoria, dict):
            return None
        
        club_rec = trayectoria.get('club_recommendation', {})
        recommended_club = club_rec.get('recommended_club', 'un palo apropiado')
        swing_type = club_rec.get('swing_type', 'completo')
        target = trayectoria.get('target', 'flag')
        waypoint_desc = trayectoria.get('waypoint_description')
        distance_meters = trayectoria.get('distance_meters', 0)
        is_optimal_shot = trayectoria.get('is_optimal_shot', False)
        
        # Determinar tipo de swing
        if swing_type == 'completo':
            swing_text = "con swing completo"
        elif swing_type == '3/4':
            swing_text = "con swing de tres cuartos"
        elif swing_type == '1/2':
            swing_text = "con swing de medio"
        else:
            swing_text = "con swing completo"
        
        # Determinar objetivo del campo
        if target == 'flag':
            objetivo_campo = "el green"
        elif is_optimal_shot:
            # Para optimal_shots, usar el mismo formato que en la recomendación principal
            obstacles_alt = trayectoria.get('obstacles', [])
            objetivo_campo = self._format_optimal_shot_target(obstacles_alt)
        elif waypoint_desc:
            objetivo_campo = self._extract_field_target(waypoint_desc)
        else:
            objetivo_campo = "el punto estratégico"
        
        # Construir mensaje según el tipo
        distancia_reference = "inicio del green" if not is_on_green else "hoyo"
        
        if tipo == "conservadora":
            if distance_to_target is not None:
                distancia_despues = distance_to_target - distance_meters
                if distancia_despues > 0:
                    siguiente_golpe = self._get_next_shot_description(distancia_despues, target, waypoint_desc, is_on_green)
                    if siguiente_golpe:
                        return f"También tienes la opción más conservadora de usar {recommended_club} {swing_text} para hacer {distance_meters:.0f} metros {objetivo_campo}, que te permitirá {siguiente_golpe}"
            return f"También tienes la opción más conservadora de usar {recommended_club} {swing_text} para hacer {distance_meters:.0f} metros {objetivo_campo}"
        else:  # tipo == "riesgo"
            if distance_to_target is not None:
                distancia_despues = distance_to_target - distance_meters
                if distancia_despues > 0:
                    siguiente_golpe = self._get_next_shot_description(distancia_despues, target, waypoint_desc, is_on_green)
                    if siguiente_golpe:
                        return f"También tienes la opción de usar {recommended_club} {swing_text} para hacer {distance_meters:.0f} metros {objetivo_campo}, con mayor riesgo pero que te permitirá {siguiente_golpe}"
            return f"También tienes la opción de usar {recommended_club} {swing_text} para hacer {distance_meters:.0f} metros {objetivo_campo}, con mayor riesgo"
    
    def _handle_register_stroke(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para registrar un golpe.
        
        La posición GPS recibida (latitude, longitude) es:
        - La posición INICIAL del nuevo stroke que se va a crear (donde está la bola antes de golpear)
        - La posición FINAL del stroke anterior pendiente (donde terminó la bola del golpe anterior)
        
        Por lo tanto:
        1. Evalúa el stroke anterior usando esta posición como posición final
        2. Incrementa el contador de golpes
        3. Crea el nuevo stroke usando esta posición como posición inicial
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás. No puedo registrar tu golpe.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        hole_number = hole_info['hole_number']
        course_id = hole_info['course_id']
        
        # ANTES de incrementar, evaluar el stroke anterior si existe
        stroke_evaluation = None
        try:
            # Obtener número actual de golpes para validación
            current_strokes = self.match_service.match_repository.get_hole_strokes_for_player(
                match_id, user_id, hole_id
            )
            
            # Buscar stroke pendiente de evaluación
            pending_stroke = self.match_service.match_repository.get_last_unevaluated_stroke(
                match_id, user_id, hole_id
            )
            
            if pending_stroke:
                # Detectar si la posición está en el green
                is_on_green = self.golf_service.is_ball_on_green(latitude, longitude, hole_id)
                
                # Evaluar el stroke anterior usando la posición GPS actual como posición final
                stroke_evaluation = self.match_service.evaluate_stroke(
                    match_id=match_id,
                    user_id=user_id,
                    course_id=course_id,
                    hole_number=hole_number,
                    ball_end_latitude=latitude,  # Posición GPS actual = posición final del stroke anterior
                    ball_end_longitude=longitude,
                    is_on_green=is_on_green,
                    current_strokes=current_strokes
                )
                
                # Si se evaluó un golpe y tiene información del palo, actualizar estadísticas
                if stroke_evaluation and stroke_evaluation.get('club_used_id') and stroke_evaluation.get('evaluation_quality') is not None:
                    try:
                        player_profile = self.player_service.player_repository.get_player_profile_by_user_id(user_id)
                        if player_profile:
                            target_distance = stroke_evaluation.get('proposed_distance_meters')
                            if not target_distance:
                                target_distance = stroke_evaluation.get('ball_end_distance_meters', 0)
                            
                            actual_distance = stroke_evaluation.get('ball_end_distance_meters', 0)
                            quality_score = stroke_evaluation.get('evaluation_quality', 0)
                            
                            self.player_service.player_repository.update_club_statistics_after_stroke(
                                player_profile_id=player_profile['id'],
                                club_id=stroke_evaluation['club_used_id'],
                                actual_distance=actual_distance,
                                target_distance=target_distance,
                                quality_score=quality_score
                            )
                    except Exception as e:
                        print(f"Advertencia: No se pudo actualizar estadísticas del palo: {e}")
        except Exception as e:
            print(f"Advertencia: No se pudo evaluar el golpe anterior: {e}")
        
        # Incrementar golpes
        try:
            score = self.match_service.increment_hole_strokes(
                match_id=match_id,
                user_id=user_id,
                course_id=course_id,
                hole_number=hole_number,
                strokes=1
            )
            
            strokes = score['strokes']
            
            # Crear el nuevo stroke usando la posición GPS actual como posición inicial
            stroke_created = None
            try:
                stroke_created = self.match_service.create_stroke(
                    match_id=match_id,
                    user_id=user_id,
                    course_id=course_id,
                    hole_number=hole_number,
                    ball_start_latitude=latitude,  # Posición GPS actual = posición inicial del nuevo stroke
                    ball_start_longitude=longitude,
                    stroke_number=strokes,  # El golpe que acabamos de incrementar
                    club_used_id=None,  # No se proporciona en el query de voz
                    trajectory_type=None,
                    proposed_distance_meters=None,
                    proposed_club_id=None
                )
            except Exception as e:
                print(f"Advertencia: No se pudo crear el stroke: {e}")
            
            response_data = {
                'hole_number': hole_number,
                'strokes': strokes
            }
            
            # Incluir información de evaluación si se evaluó un stroke
            if stroke_evaluation:
                response_data['previous_stroke_evaluation'] = {
                    'stroke_id': stroke_evaluation.get('id'),
                    'evaluation_quality': stroke_evaluation.get('evaluation_quality'),
                    'evaluation_distance_error': stroke_evaluation.get('evaluation_distance_error'),
                    'ball_end_distance_meters': stroke_evaluation.get('ball_end_distance_meters')
                }
            
            # Incluir información del stroke creado
            if stroke_created:
                response_data['stroke_created'] = {
                    'stroke_id': stroke_created.get('id'),
                    'stroke_number': stroke_created.get('stroke_number')
                }
            
            return {
                'response': f"Golpe registrado. Llevas {strokes} golpe{'s' if strokes != 1 else ''} en el hoyo {hole_number}.",
                'data': response_data
            }
        except Exception as e:
            return {
                'response': f"No pude registrar tu golpe: {str(e)}",
                'data': {'error': str(e)}
            }
    
    def _handle_check_distance(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar distancia al hoyo.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        hole_number = hole_info['hole_number']
        
        # Calcular distancia
        distance_result = self.golf_service.calculate_distance_to_hole(
            latitude, longitude, hole_id
        )
        
        if not distance_result:
            return {
                'response': f"El hoyo {hole_number} no tiene una bandera definida.",
                'data': {'hole_number': hole_number}
            }
        
        distance_meters = distance_result['distance_meters']
        distance_yards = distance_result['distance_yards']
        
        return {
            'response': f"Estás a {distance_meters:.0f} metros ({distance_yards:.0f} yardas) de la bandera del hoyo {hole_number}.",
            'data': {
                'distance_meters': distance_meters,
                'distance_yards': distance_yards,
                'hole_number': hole_number
            }
        }
    
    def _handle_check_obstacles(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar obstáculos.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        hole_number = hole_info['hole_number']
        
        # Buscar obstáculos
        obstacles_result = self.golf_service.find_obstacles_between_ball_and_flag(
            latitude, longitude, hole_id
        )
        
        obstacles = obstacles_result.get('obstacles', [])
        obstacle_count = obstacles_result.get('obstacle_count', 0)
        
        if obstacle_count == 0:
            return {
                'response': f"No hay obstáculos entre tu posición y la bandera del hoyo {hole_number}.",
                'data': {
                    'obstacle_count': 0,
                    'hole_number': hole_number
                }
            }
        
        # Construir respuesta
        obstacle_names = []
        for obs in obstacles[:3]:  # Máximo 3 obstáculos en la respuesta
            obs_name = obs.get('name') or obs.get('type', 'obstáculo')
            obstacle_names.append(obs_name)
        
        if obstacle_count == 1:
            response = f"Hay 1 obstáculo en el camino: {obstacle_names[0]}."
        elif obstacle_count <= 3:
            response = f"Hay {obstacle_count} obstáculos en el camino: {', '.join(obstacle_names)}."
        else:
            response = f"Hay {obstacle_count} obstáculos en el camino, incluyendo: {', '.join(obstacle_names)} y otros."
        
        return {
            'response': response,
            'data': {
                'obstacle_count': obstacle_count,
                'obstacles': obstacles[:5],  # Máximo 5 en data
                'hole_number': hole_number
            }
        }
    
    def _handle_check_terrain(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar tipo de terreno.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        hole_number = hole_info['hole_number']
        
        # Determinar terreno
        terrain_result = self.golf_service.determine_terrain_type(
            latitude, longitude, hole_id
        )
        
        terrain_type = terrain_result.get('terrain_type')
        
        terrain_names = {
            'bunker': 'un bunker',
            'water': 'agua',
            'trees': 'entre árboles',
            'rough_heavy': 'rough pesado',
            'out_of_bounds': 'fuera de límites'
        }
        
        if terrain_type:
            terrain_name = terrain_names.get(terrain_type, terrain_type)
            response = f"Estás en {terrain_name} del hoyo {hole_number}."
        else:
            # Verificar si está en el green
            is_on_green = self.golf_service.is_ball_on_green(latitude, longitude, hole_id)
            if is_on_green:
                response = f"Estás en el green del hoyo {hole_number}."
            else:
                response = f"Estás en terreno normal (fairway) del hoyo {hole_number}."
        
        return {
            'response': response,
            'data': {
                'terrain_type': terrain_type,
                'is_on_green': terrain_type is None and self.golf_service.is_ball_on_green(
                    latitude, longitude, hole_id
                ),
                'hole_number': hole_number
            }
        }
    
    def _handle_complete_hole(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para completar el hoyo.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_number = hole_info['hole_number']
        
        # Completar hoyo
        try:
            result = self.match_service.complete_hole(
                match_id=match_id,
                user_id=user_id,
                course_id=course_id,
                hole_number=hole_number
            )
            
            hole_strokes = result['hole_strokes']
            total_strokes = result['total_strokes']
            ranking = result.get('ranking', {})
            position = ranking.get('position', 'N/A')
            
            response = f"Hoyo {hole_number} completado con {hole_strokes} golpe{'s' if hole_strokes != 1 else ''}. "
            response += f"Total en el partido: {total_strokes} golpes. "
            response += f"Tu posición actual: {position}."
            
            return {
                'response': response,
                'data': {
                    'hole_number': hole_number,
                    'hole_strokes': hole_strokes,
                    'total_strokes': total_strokes,
                    'ranking': ranking
                }
            }
        except Exception as e:
            return {
                'response': f"No pude completar el hoyo: {str(e)}",
                'data': {'error': str(e)}
            }
    
    def _handle_check_ranking(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar el ranking del partido.
        """
        try:
            leaderboard = self.match_service.get_match_leaderboard(match_id)
            
            if not leaderboard:
                return {
                    'response': "No hay jugadores en el partido.",
                    'data': {}
                }
            
            # Encontrar posición del usuario
            user_position = None
            for idx, player in enumerate(leaderboard, 1):
                if player['user_id'] == user_id:
                    user_position = idx
                    user_strokes = player['total_strokes']
                    break
            
            if user_position is None:
                return {
                    'response': "No encontré tu posición en el partido.",
                    'data': {}
                }
            
            # Construir respuesta
            total_players = len(leaderboard)
            response = f"Vas en la posición {user_position} de {total_players} con {user_strokes} golpes. "
            
            if user_position == 1:
                response += "¡Vas ganando!"
            elif user_position == total_players:
                response += "Todavía puedes remontar."
            else:
                # Mostrar diferencia con el primero
                leader_strokes = leaderboard[0]['total_strokes']
                difference = user_strokes - leader_strokes
                if difference > 0:
                    response += f"Vas {difference} golpe{'s' if difference != 1 else ''} por detrás del líder."
                else:
                    response += "Estás empatado con el líder."
            
            return {
                'response': response,
                'data': {
                    'position': user_position,
                    'total_strokes': user_strokes,
                    'total_players': total_players,
                    'leaderboard': leaderboard[:5]  # Top 5 en data
                }
            }
        except Exception as e:
            return {
                'response': f"No pude obtener el ranking: {str(e)}",
                'data': {'error': str(e)}
            }
    
    def _handle_check_hole_stats(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar estadísticas del hoyo actual.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_id = hole_info['id']
        hole_number = hole_info['hole_number']
        
        # Obtener golpes en el hoyo
        try:
            strokes = self.match_service.match_repository.get_hole_strokes_for_player(
                match_id, user_id, hole_id
            )
            
            par = hole_info.get('par', 'N/A')
            
            if strokes == 0:
                response = f"En el hoyo {hole_number} (par {par}) aún no has registrado golpes."
            else:
                response = f"En el hoyo {hole_number} (par {par}) llevas {strokes} golpe{'s' if strokes != 1 else ''}."
                
                # Comparar con par
                if isinstance(par, int):
                    if strokes < par:
                        response += f" Vas {par - strokes} por debajo del par. ¡Excelente!"
                    elif strokes == par:
                        response += " Estás al par."
                    else:
                        response += f" Vas {strokes - par} por encima del par."
            
            return {
                'response': response,
                'data': {
                    'hole_number': hole_number,
                    'par': par,
                    'strokes': strokes
                }
            }
        except Exception as e:
            return {
                'response': f"No pude obtener tus estadísticas del hoyo: {str(e)}",
                'data': {'error': str(e)}
            }
    
    def _handle_check_hole_info(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar información del hoyo.
        """
        # Obtener información del hoyo desde estado persistido o GPS
        hole_info = self._get_hole_info_from_state_or_gps(
            match_id, user_id, course_id, latitude, longitude
        )
        
        if not hole_info:
            return {
                'response': "No pude identificar en qué hoyo estás.",
                'data': {}
            }
        
        hole_number = hole_info.get('hole_number', 'N/A')
        par = hole_info.get('par', 'N/A')
        length = hole_info.get('length', 'N/A')
        course_name = hole_info.get('course_name', 'el campo')
        
        response = f"Estás en el hoyo {hole_number} de {course_name}. "
        response += f"Par {par}, longitud {length} metros."
        
        return {
            'response': response,
            'data': {
                'hole_info': hole_info
            }
        }
    
    def _handle_check_weather(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para consultar el clima.
        
        Nota: Este handler requiere acceso al servicio de clima.
        Por ahora, retorna un mensaje indicando que debe usar el endpoint de clima.
        """
        # Importar aquí para evitar dependencia circular
        try:
            from kdi_back.infrastructure.agents.weather_agent import get_weather_response
            
            # Construir query de clima basada en la ubicación
            weather_query = f"¿Qué tiempo hace en las coordenadas {latitude}, {longitude}?"
            if "viento" in query.lower() or "wind" in query.lower():
                weather_query += " ¿Hay viento?"
            elif "lluvia" in query.lower() or "rain" in query.lower():
                weather_query += " ¿Va a llover?"
            
            weather_response = get_weather_response(weather_query)
            
            return {
                'response': weather_response,
                'data': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'weather_query': weather_query
                }
            }
        except Exception as e:
            return {
                'response': f"No pude obtener información del clima: {str(e)}",
                'data': {
                    'error': str(e),
                    'note': 'Usar endpoint /weather para consultas de clima'
                }
            }
    
    def _handle_record_hole_score_direct(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para registrar el resultado de un hoyo directamente con número de golpes.
        
        Ejemplos:
        - "Completa el hoyo con 4 golpes" -> Registra 4 golpes en el hoyo actual
        - "Registra 5 golpes en este hoyo" -> Registra 5 golpes en el hoyo actual
        """
        # Extraer número de golpes del query
        extracted = self._extract_hole_and_strokes_from_query(query)
        strokes = extracted.get('strokes')
        hole_number = extracted.get('hole_number')
        
        # Si no se especificó el hoyo, usar el hoyo actual del estado
        if not hole_number:
            match_state = self.match_service.get_match_state(match_id, user_id)
            if not match_state:
                return {
                    'response': "No pude determinar en qué hoyo estás. Por favor, especifica el número de hoyo.",
                    'data': {}
                }
            hole_number = match_state['current_hole_number']
        
        # Validar que se especificaron golpes
        if not strokes:
            return {
                'response': f"No pude determinar cuántos golpes quieres registrar para el hoyo {hole_number}. Por favor, especifica el número de golpes.",
                'data': {'hole_number': hole_number}
            }
        
        # Validar que los golpes sean válidos
        if strokes <= 0:
            return {
                'response': f"El número de golpes debe ser mayor que cero. Especificaste {strokes} golpes.",
                'data': {'hole_number': hole_number, 'strokes': strokes}
            }
        
        # Registrar el score del hoyo
        try:
            score = self.match_service.record_hole_score(
                match_id=match_id,
                user_id=user_id,
                course_id=course_id,
                hole_number=hole_number,
                strokes=strokes
            )
            
            # Obtener información del hoyo para la respuesta
            hole_info = self.golf_service.get_hole_by_course_and_number(course_id, hole_number)
            par = hole_info.get('par', 'N/A') if hole_info else 'N/A'
            
            response = f"Hoyo {hole_number} registrado con {strokes} golpe{'s' if strokes != 1 else ''}."
            if isinstance(par, int):
                if strokes < par:
                    response += f" Excelente, estás {par - strokes} por debajo del par."
                elif strokes == par:
                    response += " Estás al par."
                else:
                    response += f" Vas {strokes - par} por encima del par."
            
            return {
                'response': response,
                'data': {
                    'hole_number': hole_number,
                    'strokes': strokes,
                    'par': par,
                    'score': score
                }
            }
        except Exception as e:
            return {
                'response': f"No pude registrar el resultado del hoyo {hole_number}: {str(e)}",
                'data': {'error': str(e), 'hole_number': hole_number, 'strokes': strokes}
            }
    
    def _handle_update_hole_score(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja peticiones para corregir el resultado de un hoyo específico.
        
        Ejemplos:
        - "Corrige el resultado del hoyo 2 con 3 golpes" -> Actualiza el hoyo 2 a 3 golpes
        - "Cambia el hoyo 5 a 4 golpes" -> Actualiza el hoyo 5 a 4 golpes
        """
        # Extraer número de hoyo y golpes del query
        extracted = self._extract_hole_and_strokes_from_query(query)
        hole_number = extracted.get('hole_number')
        strokes = extracted.get('strokes')
        
        # Validar que se especificó el hoyo
        if not hole_number:
            return {
                'response': "No pude determinar qué hoyo quieres corregir. Por favor, especifica el número de hoyo, por ejemplo: 'Corrige el resultado del hoyo 2 con 3 golpes'.",
                'data': {}
            }
        
        # Validar que se especificaron golpes
        if not strokes:
            return {
                'response': f"No pude determinar cuántos golpes quieres registrar para el hoyo {hole_number}. Por favor, especifica el número de golpes.",
                'data': {'hole_number': hole_number}
            }
        
        # Validar que los golpes sean válidos
        if strokes <= 0:
            return {
                'response': f"El número de golpes debe ser mayor que cero. Especificaste {strokes} golpes.",
                'data': {'hole_number': hole_number, 'strokes': strokes}
            }
        
        # Registrar/actualizar el score del hoyo
        try:
            score = self.match_service.record_hole_score(
                match_id=match_id,
                user_id=user_id,
                course_id=course_id,
                hole_number=hole_number,
                strokes=strokes
            )
            
            # Obtener información del hoyo para la respuesta
            hole_info = self.golf_service.get_hole_by_course_and_number(course_id, hole_number)
            par = hole_info.get('par', 'N/A') if hole_info else 'N/A'
            
            response = f"Resultado del hoyo {hole_number} actualizado a {strokes} golpe{'s' if strokes != 1 else ''}."
            if isinstance(par, int):
                if strokes < par:
                    response += f" Excelente, estás {par - strokes} por debajo del par."
                elif strokes == par:
                    response += " Estás al par."
                else:
                    response += f" Vas {strokes - par} por encima del par."
            
            return {
                'response': response,
                'data': {
                    'hole_number': hole_number,
                    'strokes': strokes,
                    'par': par,
                    'score': score
                }
            }
        except Exception as e:
            return {
                'response': f"No pude actualizar el resultado del hoyo {hole_number}: {str(e)}",
                'data': {'error': str(e), 'hole_number': hole_number, 'strokes': strokes}
            }
    
    def _handle_require_hole_confirmation(
        self,
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        """
        Maneja respuestas a solicitudes de confirmación de hoyos.
        
        Este handler se activa cuando el jugador responde a una solicitud de confirmación
        de hoyos sin completar. Extrae múltiples confirmaciones del query y las registra.
        
        El query debe contener confirmaciones en formato:
        - "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes"
        - "5: 4 golpes, 6: 5 golpes"
        - "Hoyo 5: 4, hoyo 6: 5"
        """
        # Extraer todas las confirmaciones del query
        confirmations = self._extract_multiple_hole_confirmations(query)
        
        if not confirmations:
            return {
                'response': "No pude entender las confirmaciones. Por favor, especifica cada hoyo y sus golpes, por ejemplo: 'Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes'.",
                'data': {}
            }
        
        # Registrar cada confirmación
        registered = []
        errors = []
        
        for conf in confirmations:
            hole_number = conf.get('hole_number')
            strokes = conf.get('strokes')
            
            if not hole_number or not strokes:
                errors.append(f"Confirmación incompleta: {conf}")
                continue
            
            try:
                score = self.match_service.record_hole_score(
                    match_id=match_id,
                    user_id=user_id,
                    course_id=course_id,
                    hole_number=hole_number,
                    strokes=strokes
                )
                registered.append({'hole': hole_number, 'strokes': strokes})
            except Exception as e:
                errors.append(f"Error registrando hoyo {hole_number}: {str(e)}")
        
        # Obtener el nuevo estado después de registrar (para sincronizar frontend)
        updated_state = None
        if len(errors) == 0 and registered:
            try:
                updated_state = self.match_service.get_match_state(match_id, user_id)
            except Exception as e:
                print(f"Advertencia: No se pudo obtener el estado actualizado: {e}")
        
        # Construir respuesta
        if not registered:
            response = f"No pude registrar ningún hoyo. Errores: {', '.join(errors)}"
        elif errors:
            holes_str = ', '.join([f"hoyo {r['hole']} con {r['strokes']} golpes" for r in registered])
            response = f"Registré {len(registered)} hoyos: {holes_str}. Hubo algunos errores: {', '.join(errors)}"
        else:
            if len(registered) == 1:
                r = registered[0]
                response = f"Perfecto. He registrado el hoyo {r['hole']} con {r['strokes']} golpes. Ahora puedes continuar con tu petición."
            else:
                holes_str = ', '.join([f"hoyo {r['hole']} con {r['strokes']} golpes" for r in registered[:-1]])
                last = registered[-1]
                response = f"Perfecto. He registrado: {holes_str} y hoyo {last['hole']} con {last['strokes']} golpes. Ahora puedes continuar con tu petición."
        
        # Preparar datos de respuesta
        response_data = {
            'registered': registered,
            'errors': errors,
            'all_registered': len(errors) == 0
        }
        
        # Si se registraron exitosamente, incluir el nuevo estado para sincronizar frontend
        if updated_state:
            response_data['updated_state'] = {
                'current_hole_number': updated_state.get('current_hole_number'),
                'current_hole_id': updated_state.get('current_hole_id'),
                'strokes_in_current_hole': updated_state.get('strokes_in_current_hole', 0),
                'course_id': updated_state.get('course_id')
            }
            # Determinar el hoyo objetivo (el último registrado o el nuevo current_hole)
            if registered:
                # El hoyo objetivo es el último hoyo registrado (que debería ser el más alto)
                max_hole = max(r['hole'] for r in registered)
                response_data['target_hole'] = max_hole
        
        return {
            'response': response,
            'data': response_data
        }

