# -*- coding: utf-8 -*-
"""
Servicio de validación GPS contextual para validar posiciones GPS basándose en:
- Estado actual del partido (hoyo actual, golpes realizados)
- Secuencia lógica de hoyos
- Progresión esperada (acercamiento al hoyo)
- Validación de posición inicial (tee)

Este servicio implementa una estrategia híbrida:
1. Validación contextual (hoyo esperado basado en partido)
2. Validación por polígonos (fairway, green)
3. Validación por distancias (fallback si polígonos fallan)
4. Filtrado de posiciones imposibles
"""
from typing import Optional, Dict, Any, Tuple, List
from math import radians, sin, cos, atan2, sqrt
from kdi_back.domain.ports.match_repository import MatchRepository
from kdi_back.domain.ports.golf_repository import GolfRepository
from kdi_back.domain.services.terrain_description_service import TerrainDescriptionService


class GPSValidationService:
    """
    Servicio para validar posiciones GPS considerando el contexto del partido.
    
    Implementa validaciones para:
    - Secuencia correcta de hoyos
    - Posición inicial en tee para primer golpe
    - Progresión lógica (acercamiento al hoyo)
    - Filtrado de posiciones imposibles
    """
    
    # Radio de la Tierra en metros
    EARTH_RADIUS_METERS = 6371000
    
    def __init__(self, match_repository: MatchRepository, golf_repository: GolfRepository):
        """
        Inicializa el servicio con sus dependencias.
        
        Args:
            match_repository: Repositorio para acceder a datos del partido
            golf_repository: Repositorio para acceder a datos del campo de golf
        """
        self.match_repository = match_repository
        self.golf_repository = golf_repository
        self.terrain_description_service = TerrainDescriptionService()
    
    def validate_and_identify_hole(
        self,
        match_id: int,
        user_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        expected_hole_number: Optional[int] = None,
        terrain_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida una posición GPS y identifica el hoyo correcto considerando el contexto del partido.
        
        Estrategia:
        1. Obtener hoyo esperado según estado del partido
        2. Intentar identificar hoyo por polígonos (fairway, green)
        3. Validar que el hoyo detectado sea lógico según el contexto
        4. Si hay descripción de terreno y discrepancia, corregir posición GPS
        5. Si no es lógico, usar distancias para encontrar el hoyo más cercano esperado
        6. Validar progresión (acercamiento al hoyo)
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario
            course_id: ID del campo de golf
            latitude: Latitud GPS
            longitude: Longitud GPS
            expected_hole_number: Número de hoyo esperado (opcional, se calcula si no se proporciona)
            terrain_description: Descripción textual del terreno del jugador (opcional)
                                 Ej: "mi bola está entre los árboles", "estoy en un bunker"
            
        Returns:
            Diccionario con:
            - hole_info: Información del hoyo identificado
            - is_valid: Si la posición es válida
            - validation_confidence: Confianza de la validación (0.0-1.0)
            - validation_reason: Razón de la validación/invalidación
            - corrected_hole_number: Número de hoyo corregido si fue necesario
            - corrected_position: Posición GPS corregida si fue necesario (dict con lat/lon)
            - distance_to_hole: Distancia al hoyo en metros
        """
        # Obtener estado actual del partido
        match_state = self._get_match_state(match_id, user_id, course_id)
        
        # Calcular hoyo esperado si no se proporciona
        if expected_hole_number is None:
            expected_hole_number = match_state['expected_hole_number']
        
        expected_hole_id = match_state['expected_hole_id']
        strokes_in_current_hole = match_state['strokes_in_current_hole']
        is_first_stroke = strokes_in_current_hole == 0
        
        # ESTRATEGIA 1: Identificar hoyo por polígonos (fairway, green)
        detected_hole = self.golf_repository.find_hole_by_position(latitude, longitude)
        
        # ESTRATEGIA 2: Validar lógica contextual
        validation_result = self._validate_hole_context(
            detected_hole=detected_hole,
            expected_hole_number=expected_hole_number,
            expected_hole_id=expected_hole_id,
            course_id=course_id,
            latitude=latitude,
            longitude=longitude,
            is_first_stroke=is_first_stroke,
            strokes_in_current_hole=strokes_in_current_hole
        )
        
        # ESTRATEGIA 3: Corrección GPS basada en descripción textual del jugador
        corrected_position = None
        if terrain_description:
            terrain_info = self.terrain_description_service.extract_terrain_from_description(
                terrain_description
            )
            
            if terrain_info and terrain_info['confidence'] > 0.6:
                # Si hay una descripción de terreno válida y hay discrepancia, intentar corregir
                correction_result = self._correct_position_by_terrain_description(
                    hole_id=expected_hole_id,
                    expected_hole_number=expected_hole_number,
                    detected_hole=detected_hole,
                    terrain_type=terrain_info['terrain_type'],
                    gps_latitude=latitude,
                    gps_longitude=longitude,
                    validation_result=validation_result
                )
                
                if correction_result and correction_result['corrected']:
                    corrected_position = {
                        'latitude': correction_result['corrected_latitude'],
                        'longitude': correction_result['corrected_longitude']
                    }
                    # Actualizar posición para el resto de validaciones
                    latitude = correction_result['corrected_latitude']
                    longitude = correction_result['corrected_longitude']
                    validation_result['confidence'] = min(1.0, validation_result['confidence'] + 0.15)
                    validation_result['validation_reason'] += f" | GPS corregido según descripción: {terrain_info['terrain_type']}"
        
        # Si la detección por polígonos no es válida contextualmente, usar distancias
        if not validation_result['is_valid'] or validation_result['confidence'] < 0.7:
            # ESTRATEGIA 4: Identificar por distancia al hoyo esperado
            distance_result = self._identify_by_distance(
                course_id=course_id,
                expected_hole_number=expected_hole_number,
                latitude=latitude,
                longitude=longitude,
                is_first_stroke=is_first_stroke
            )
            
            if distance_result['is_valid'] and distance_result['confidence'] > validation_result['confidence']:
                validation_result = distance_result
                detected_hole = distance_result['hole_info']
        
        # Validar progresión si no es el primer golpe
        if not is_first_stroke and detected_hole:
            progression_validation = self._validate_progression(
                match_id=match_id,
                user_id=user_id,
                hole_id=detected_hole['id'],
                latitude=latitude,
                longitude=longitude
            )
            
            # Si la progresión no es válida, reducir confianza
            if not progression_validation['is_valid']:
                validation_result['confidence'] *= 0.5
                validation_result['validation_reason'] += f" | {progression_validation['reason']}"
        
        # Calcular distancia al hoyo
        distance_to_hole = None
        if detected_hole:
            distance_to_hole = self.golf_repository.calculate_distance_to_hole(
                detected_hole['id'], latitude, longitude
            )
        
        return {
            'hole_info': detected_hole,
            'is_valid': validation_result['is_valid'],
            'validation_confidence': validation_result['confidence'],
            'validation_reason': validation_result['validation_reason'],
            'corrected_hole_number': validation_result.get('corrected_hole_number'),
            'corrected_position': corrected_position,
            'distance_to_hole': distance_to_hole,
            'match_state': match_state
        }
    
    def _get_match_state(
        self,
        match_id: int,
        user_id: int,
        course_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene el estado actual del partido para el jugador.
        
        Returns:
            Diccionario con:
            - expected_hole_number: Hoyo que debería estar jugando
            - expected_hole_id: ID del hoyo esperado
            - strokes_in_current_hole: Golpes en el hoyo actual
            - completed_holes: Lista de hoyos completados
            - total_holes: Total de hoyos del campo
        """
        # Obtener información del partido
        match = self.match_repository.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No se encontró el partido {match_id}")
        
        # Obtener jugadores del partido
        match_players = self.match_repository.get_match_players(match_id)
        user_player = next((p for p in match_players if p['user_id'] == user_id), None)
        
        if not user_player:
            raise ValueError(f"El usuario {user_id} no está en el partido {match_id}")
        
        # Obtener hoyo de inicio del jugador
        starting_hole = user_player.get('starting_hole', 1)
        
        # Calcular hoyo esperado basándose en hoyos completados
        # TODO: Implementar lógica para obtener hoyos completados del jugador
        # Por ahora, asumimos que está en el hoyo de inicio
        expected_hole_number = starting_hole
        
        # Obtener ID del hoyo esperado
        expected_hole = self.golf_repository.get_hole_by_course_and_number(
            course_id, expected_hole_number
        )
        expected_hole_id = expected_hole['id'] if expected_hole else None
        
        # Obtener golpes en el hoyo actual
        strokes_in_current_hole = 0
        if expected_hole_id:
            strokes_in_current_hole = self.match_repository.get_hole_strokes_for_player(
                match_id, user_id, expected_hole_id
            )
        
        # TODO: Obtener total de hoyos del campo
        total_holes = 18  # Por defecto
        
        return {
            'expected_hole_number': expected_hole_number,
            'expected_hole_id': expected_hole_id,
            'strokes_in_current_hole': strokes_in_current_hole,
            'starting_hole': starting_hole,
            'total_holes': total_holes
        }
    
    def _validate_hole_context(
        self,
        detected_hole: Optional[Dict[str, Any]],
        expected_hole_number: int,
        expected_hole_id: Optional[int],
        course_id: int,
        latitude: float,
        longitude: float,
        is_first_stroke: bool,
        strokes_in_current_hole: int
    ) -> Dict[str, Any]:
        """
        Valida si el hoyo detectado por GPS tiene sentido según el contexto del partido.
        
        Args:
            detected_hole: Hoyo detectado por polígonos (puede ser None)
            expected_hole_number: Hoyo que debería estar jugando
            expected_hole_id: ID del hoyo esperado
            course_id: ID del campo
            latitude: Latitud GPS
            longitude: Longitud GPS
            is_first_stroke: Si es el primer golpe del hoyo
            strokes_in_current_hole: Golpes en el hoyo actual
            
        Returns:
            Diccionario con is_valid, confidence, validation_reason
        """
        if not detected_hole:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'validation_reason': 'No se detectó ningún hoyo por polígonos'
            }
        
        detected_hole_number = detected_hole.get('hole_number')
        detected_hole_id = detected_hole.get('id')
        detected_course_id = detected_hole.get('course_id')
        
        # Validar que el campo coincida
        if detected_course_id != course_id:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'validation_reason': f'Hoyo detectado pertenece a otro campo (course_id={detected_course_id})'
            }
        
        # Validar si es el hoyo esperado
        if detected_hole_number == expected_hole_number:
            confidence = 0.9
            reason = f'Hoyo correcto detectado (hoyo {detected_hole_number})'
            
            # Validación adicional para primer golpe: debe estar en tee
            if is_first_stroke:
                tee_validation = self._validate_tee_position(
                    hole_id=detected_hole_id,
                    latitude=latitude,
                    longitude=longitude
                )
                if tee_validation['is_near_tee']:
                    confidence = 1.0
                    reason += ' | Posición en tee válida para primer golpe'
                else:
                    confidence = 0.7
                    reason += ' | Primer golpe pero no en tee (puede ser error GPS)'
            
            return {
                'is_valid': True,
                'confidence': confidence,
                'validation_reason': reason
            }
        
        # Si no es el hoyo esperado, verificar si es un hoyo adyacente (posible error GPS)
        # Permitir hoyo anterior o siguiente si la distancia es razonable
        hole_difference = abs(detected_hole_number - expected_hole_number)
        
        # Si es un hoyo cercano (1-2 hoyos de diferencia), puede ser error GPS pero aceptable
        if hole_difference <= 2:
            confidence = 0.5
            reason = f'Hoyo adyacente detectado (hoyo {detected_hole_number}, esperado {expected_hole_number}) - Posible error GPS'
            
            # Verificar distancia al hoyo esperado para decidir si aceptar
            if expected_hole_id:
                distance_to_expected = self.golf_repository.calculate_distance_to_hole(
                    expected_hole_id, latitude, longitude
                )
                
                # Si está cerca del hoyo esperado (< 100m), probablemente es el correcto
                if distance_to_expected and distance_to_expected < 100:
                    return {
                        'is_valid': True,
                        'confidence': 0.8,
                        'validation_reason': f'GPS detecta hoyo {detected_hole_number} pero posición muy cerca del hoyo esperado {expected_hole_number}',
                        'corrected_hole_number': expected_hole_number
                    }
            
            return {
                'is_valid': True,
                'confidence': confidence,
                'validation_reason': reason
            }
        
        # Si es un hoyo muy lejano, probablemente es un error
        return {
            'is_valid': False,
            'confidence': 0.2,
            'validation_reason': f'Hoyo detectado ({detected_hole_number}) muy diferente al esperado ({expected_hole_number})'
        }
    
    def _validate_tee_position(
        self,
        hole_id: int,
        latitude: float,
        longitude: float,
        max_distance_meters: float = 15.0
    ) -> Dict[str, Any]:
        """
        Valida si la posición está cerca de un tee (para primer golpe).
        
        Args:
            hole_id: ID del hoyo
            latitude: Latitud GPS
            longitude: Longitud GPS
            max_distance_meters: Distancia máxima aceptable al tee (metros)
            
        Returns:
            Diccionario con is_near_tee, nearest_tee_type, distance
        """
        # Obtener todos los tees del hoyo
        # Usar el repositorio para obtener puntos de tipo tee
        # Por ahora, asumimos que existe un método para obtener puntos cercanos
        # TODO: Implementar método en repositorio para obtener punto más cercano de tipo tee
        
        # Validar usando find_terrain_type_by_position que ya verifica si está cerca del tee
        terrain_type = self.golf_repository.find_terrain_type_by_position(
            hole_id, latitude, longitude
        )
        
        is_near_tee = terrain_type == 'tee'
        
        return {
            'is_near_tee': is_near_tee,
            'terrain_type': terrain_type,
            'distance': 0.0  # TODO: Calcular distancia real al tee
        }
    
    def _identify_by_distance(
        self,
        course_id: int,
        expected_hole_number: int,
        latitude: float,
        longitude: float,
        is_first_stroke: bool,
        max_distance_meters: float = 500.0
    ) -> Dict[str, Any]:
        """
        Identifica el hoyo usando distancias geodésicas (enfoque Hole19).
        
        Busca el hoyo más cercano dentro de un radio razonable.
        Si es primer golpe, busca el tee más cercano del hoyo esperado.
        Si no es primer golpe, busca la bandera más cercana del hoyo esperado.
        
        Args:
            course_id: ID del campo
            expected_hole_number: Hoyo esperado
            latitude: Latitud GPS
            longitude: Longitud GPS
            is_first_stroke: Si es el primer golpe
            max_distance_meters: Distancia máxima aceptable
            
        Returns:
            Diccionario con is_valid, confidence, hole_info, validation_reason
        """
        # Obtener información del hoyo esperado
        expected_hole = self.golf_repository.get_hole_by_course_and_number(
            course_id, expected_hole_number
        )
        
        if not expected_hole:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'validation_reason': f'No se encontró el hoyo esperado {expected_hole_number}'
            }
        
        expected_hole_id = expected_hole['id']
        
        # Calcular distancia al hoyo esperado
        distance_to_expected = self.golf_repository.calculate_distance_to_hole(
            expected_hole_id, latitude, longitude
        )
        
        if distance_to_expected is None:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'validation_reason': 'El hoyo esperado no tiene bandera definida'
            }
        
        # Si la distancia es razonable, aceptar el hoyo esperado
        if distance_to_expected <= max_distance_meters:
            confidence = 0.85
            reason = f'Identificado por distancia al hoyo esperado {expected_hole_number} ({distance_to_expected:.1f}m)'
            
            # Si es primer golpe, verificar que esté cerca del tee
            if is_first_stroke:
                tee_validation = self._validate_tee_position(expected_hole_id, latitude, longitude)
                if tee_validation['is_near_tee']:
                    confidence = 0.95
                    reason += ' | Posición en tee válida'
                else:
                    confidence = 0.7
                    reason += ' | Primer golpe pero no en tee'
            
            return {
                'is_valid': True,
                'confidence': confidence,
                'hole_info': expected_hole,
                'validation_reason': reason
            }
        
        return {
            'is_valid': False,
            'confidence': 0.0,
            'validation_reason': f'Distancia al hoyo esperado demasiado grande ({distance_to_expected:.1f}m > {max_distance_meters}m)'
        }
    
    def _validate_progression(
        self,
        match_id: int,
        user_id: int,
        hole_id: int,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Valida que el jugador se esté acercando al hoyo (progresión lógica).
        
        Compara la posición actual con la posición anterior registrada para verificar
        que el jugador se esté acercando al hoyo, no alejándose.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario
            hole_id: ID del hoyo
            latitude: Latitud GPS actual
            longitude: Longitud GPS actual
            
        Returns:
            Diccionario con is_valid, reason
        """
        # TODO: Implementar obtención de posición anterior del jugador
        # Por ahora, siempre retornamos válido
        # En el futuro, podríamos guardar la última posición GPS y comparar
        
        return {
            'is_valid': True,
            'reason': 'Progresión validada (implementación futura)'
        }
    
    def _correct_position_by_terrain_description(
        self,
        hole_id: Optional[int],
        expected_hole_number: int,
        detected_hole: Optional[Dict[str, Any]],
        terrain_type: str,
        gps_latitude: float,
        gps_longitude: float,
        validation_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Corrige la posición GPS basándose en la descripción de terreno del jugador.
        
        Si hay una discrepancia (ej: GPS dice fairway pero jugador dice "entre árboles"),
        busca el obstáculo más cercano del tipo descrito en el hoyo esperado y corrige la posición.
        
        Args:
            hole_id: ID del hoyo esperado
            expected_hole_number: Número del hoyo esperado
            detected_hole: Hoyo detectado por GPS (puede ser None o diferente)
            terrain_type: Tipo de terreno descrito (trees, bunker, water, etc.)
            gps_latitude: Latitud GPS original
            gps_longitude: Longitud GPS original
            validation_result: Resultado de la validación contextual
            
        Returns:
            Diccionario con:
            - corrected: True si se corrigió la posición
            - corrected_latitude: Latitud corregida
            - corrected_longitude: Longitud corregida
            - distance_correction: Distancia de la corrección en metros
            None si no se puede o no es necesario corregir
        """
        if not hole_id:
            return None
        
        # Solo corregir si hay una discrepancia o si el hoyo detectado es diferente al esperado
        should_correct = False
        
        if not detected_hole:
            # No se detectó hoyo por GPS pero tenemos contexto - intentar corregir
            should_correct = True
        elif detected_hole.get('hole_number') != expected_hole_number:
            # Se detectó un hoyo diferente - corregir basándose en descripción
            should_correct = True
        elif validation_result.get('confidence', 1.0) < 0.8:
            # Baja confianza - verificar si la descripción ayuda
            should_correct = True
        
        if not should_correct:
            # Verificar si el terreno detectado por GPS coincide con la descripción
            # Si no coincide, corregir
            detected_terrain = None
            if detected_hole:
                detected_terrain = self.golf_repository.find_terrain_type_by_position(
                    detected_hole['id'], gps_latitude, gps_longitude
                )
            
            # Si el terreno detectado no coincide con la descripción, corregir
            if detected_terrain != terrain_type:
                should_correct = True
        
        if not should_correct:
            return None
        
        # Buscar el obstáculo más cercano del tipo descrito en el hoyo esperado
        # Radio máximo de búsqueda: 100 metros (ajustable)
        max_search_distance = 100.0
        
        nearest_obstacle = self.golf_repository.find_nearest_obstacle_by_type(
            hole_id=hole_id,
            obstacle_type=terrain_type,
            latitude=gps_latitude,
            longitude=gps_longitude,
            max_distance_meters=max_search_distance
        )
        
        if nearest_obstacle:
            corrected_lat = nearest_obstacle['corrected_latitude']
            corrected_lon = nearest_obstacle['corrected_longitude']
            
            # Calcular distancia de la corrección
            distance_correction = self.haversine_distance(
                gps_latitude, gps_longitude, corrected_lat, corrected_lon
            )
            
            return {
                'corrected': True,
                'corrected_latitude': corrected_lat,
                'corrected_longitude': corrected_lon,
                'distance_correction': distance_correction,
                'obstacle_info': {
                    'id': nearest_obstacle['id'],
                    'type': nearest_obstacle['type'],
                    'name': nearest_obstacle.get('name')
                }
            }
        
        return None
    
    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcula la distancia geodésica entre dos puntos usando la fórmula de Haversine.
        
        Args:
            lat1: Latitud del primer punto
            lon1: Longitud del primer punto
            lat2: Latitud del segundo punto
            lon2: Longitud del segundo punto
            
        Returns:
            Distancia en metros
        """
        # Convertir a radianes
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        
        # Fórmula de Haversine
        a = (
            sin(d_lat / 2) ** 2 +
            cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return GPSValidationService.EARTH_RADIUS_METERS * c

