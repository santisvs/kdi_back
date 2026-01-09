# -*- coding: utf-8 -*-
"""Match routes"""
from flask import Blueprint, jsonify, request, g
from kdi_back.api.dependencies import get_match_service
from kdi_back.api.middleware.auth_middleware import require_auth

match_bp = Blueprint('match', __name__)


def format_datetime(value):
    """Helper para formatear fechas a strings ISO."""
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


@match_bp.route('/match', methods=['POST'])
@require_auth
def create_match():
    """
    Endpoint para crear un nuevo partido.
    
    Recibe en el body JSON:
    - course_id: ID del campo de golf (requerido)
    - name: Nombre opcional del partido
    - player_ids: Lista opcional de IDs de jugadores a añadir
    - starting_holes: Diccionario opcional {user_id: starting_hole_number}
    
    Ejemplo POST:
    {
        "course_id": 1,
        "name": "Partido de fin de semana",
        "player_ids": [1, 2, 3],
        "starting_holes": {"1": 1, "2": 5, "3": 10}
    }
    
    NOTA: En JSON, las claves de los objetos deben estar entre comillas dobles.
    Por lo tanto, starting_holes debe usar claves como strings: {"1": 1, "2": 5}
    
    Respuesta exitosa (201):
    {
        "match": {
            "id": 1,
            "course_id": 1,
            "name": "Partido de fin de semana",
            "status": "in_progress",
            "started_at": "2024-01-15T10:30:00",
            "completed_at": null,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        },
        "players": [...]
    }
    """
    try:
        # Verificar Content-Type
        if request.content_type and 'application/json' not in request.content_type:
            return jsonify({
                "error": "Content-Type incorrecto",
                "details": f"Se espera 'application/json', se recibió: {request.content_type}"
            }), 400
        
        # Intentar obtener el JSON con mejor manejo de errores
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as e:
            return jsonify({
                "error": "Error al parsear el JSON",
                "details": f"El body JSON no es válido: {str(e)}"
            }), 400
        
        if not data:
            # Si get_json() retorna None, podría ser porque el body está vacío o mal formado
            if not request.data:
                return jsonify({"error": "Se requiere un body JSON"}), 400
            else:
                return jsonify({
                    "error": "Error al parsear el JSON",
                    "details": "El body no contiene un JSON válido. Asegúrate de que todas las claves estén entre comillas dobles."
                }), 400
        
        if 'course_id' not in data:
            return jsonify({"error": "Se requiere el campo 'course_id' en el body JSON"}), 400
        
        try:
            course_id = int(data['course_id'])
        except (ValueError, TypeError):
            return jsonify({"error": "El campo 'course_id' debe ser un número entero"}), 400
        
        name = data.get('name')
        player_ids = data.get('player_ids')
        starting_holes = data.get('starting_holes')
        
        # Validar player_ids
        if player_ids is not None:
            if not isinstance(player_ids, list):
                return jsonify({"error": "El campo 'player_ids' debe ser una lista"}), 400
            try:
                player_ids = [int(pid) for pid in player_ids]
            except (ValueError, TypeError):
                return jsonify({"error": "Todos los elementos de 'player_ids' deben ser números enteros"}), 400
        
        # Validar starting_holes
        if starting_holes is not None:
            if not isinstance(starting_holes, dict):
                return jsonify({"error": "El campo 'starting_holes' debe ser un diccionario"}), 400
            try:
                # Convertir claves y valores a enteros (las claves pueden venir como strings desde JSON)
                starting_holes = {int(k): int(v) for k, v in starting_holes.items()}
            except (ValueError, TypeError) as e:
                return jsonify({
                    "error": "Las claves y valores de 'starting_holes' deben ser números enteros",
                    "details": f"Error al convertir: {str(e)}. Recuerda que en JSON las claves deben estar entre comillas: {{\"2\": 1}}"
                }), 400
        
        # Obtener el usuario autenticado desde g (establecido por require_auth)
        current_user_id = g.current_user['id']
        
        # Añadir el usuario autenticado a la lista de jugadores si no está ya incluido
        if player_ids is None:
            player_ids = [current_user_id]
        elif current_user_id not in player_ids:
            player_ids = [current_user_id] + player_ids
        
        match_service = get_match_service()
        result = match_service.create_match(
            course_id=course_id,
            name=name,
            player_ids=player_ids,
            starting_holes=starting_holes
        )
        
        # Formatear respuesta
        match = result['match']
        response = {
            "match": {
                "id": match['id'],
                "course_id": match['course_id'],
                "name": match.get('name'),
                "status": match['status'],
                "started_at": format_datetime(match.get('started_at')),
                "completed_at": format_datetime(match.get('completed_at')),
                "created_at": format_datetime(match.get('created_at')),
                "updated_at": format_datetime(match.get('updated_at'))
            },
            "players": [
                {
                    "id": p['id'],
                    "match_id": p['match_id'],
                    "user_id": p['user_id'],
                    "starting_hole_number": p['starting_hole_number'],
                    "total_strokes": p['total_strokes'],
                    "created_at": format_datetime(p.get('created_at'))
                }
                for p in result['players']
            ]
        }
        
        return jsonify(response), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        # Capturar errores de parsing JSON de Flask
        error_msg = str(e)
        if "Failed to decode JSON" in error_msg or "Expecting property name" in error_msg:
            return jsonify({
                "error": "Error al parsear el JSON",
                "details": error_msg,
                "suggestion": "Asegúrate de que el JSON esté bien formateado con todas las claves entre comillas dobles"
            }), 400
        return jsonify({
            "error": "Error al crear el partido",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/player', methods=['POST'])
def add_player_to_match(match_id):
    """
    Endpoint para añadir un jugador a un partido existente.
    
    Recibe en el body JSON:
    - user_id: ID del usuario/jugador (requerido)
    - starting_hole_number: Número del hoyo donde empieza (opcional, default: 1)
    
    Ejemplo POST:
    {
        "user_id": 4,
        "starting_hole_number": 3
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        if 'user_id' not in data:
            return jsonify({"error": "Se requiere el campo 'user_id' en el body JSON"}), 400
        
        try:
            user_id = int(data['user_id'])
        except (ValueError, TypeError):
            return jsonify({"error": "El campo 'user_id' debe ser un número entero"}), 400
        
        starting_hole_number = data.get('starting_hole_number', 1)
        try:
            starting_hole_number = int(starting_hole_number)
        except (ValueError, TypeError):
            return jsonify({"error": "El campo 'starting_hole_number' debe ser un número entero"}), 400
        
        match_service = get_match_service()
        player = match_service.add_player_to_match(match_id, user_id, starting_hole_number)
        
        response = {
            "id": player['id'],
            "match_id": player['match_id'],
            "user_id": player['user_id'],
            "starting_hole_number": player['starting_hole_number'],
            "total_strokes": player['total_strokes'],
            "created_at": format_datetime(player.get('created_at'))
        }
        
        return jsonify(response), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al añadir el jugador al partido",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/score', methods=['POST'])
def record_hole_score(match_id):
    """
    Endpoint para registrar la puntuación de un jugador en un hoyo.
    
    Recibe en el body JSON:
    - user_id: ID del usuario/jugador (requerido)
    - course_id: ID del campo de golf (requerido)
    - hole_number: Número del hoyo (requerido)
    - strokes: Número de golpes (requerido)
    
    Ejemplo POST:
    {
        "user_id": 1,
        "course_id": 1,
        "hole_number": 5,
        "strokes": 4
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        required_fields = ['user_id', 'course_id', 'hole_number', 'strokes']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Se requiere el campo '{field}' en el body JSON"}), 400
        
        try:
            user_id = int(data['user_id'])
            course_id = int(data['course_id'])
            hole_number = int(data['hole_number'])
            strokes = int(data['strokes'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'user_id', 'course_id', 'hole_number' y 'strokes' deben ser números enteros"}), 400
        
        match_service = get_match_service()
        score = match_service.record_hole_score(match_id, user_id, course_id, hole_number, strokes)
        
        # Obtener información del hoyo para incluir course_id y hole_number en la respuesta
        from kdi_back.api.dependencies import get_golf_service
        golf_service = get_golf_service()
        hole_info = golf_service.get_hole_by_id(score['hole_id'])
        
        response = {
            "id": score['id'],
            "match_player_id": score['match_player_id'],
            "hole_id": score['hole_id'],
            "course_id": hole_info['course_id'] if hole_info else course_id,
            "hole_number": hole_info['hole_number'] if hole_info else hole_number,
            "strokes": score['strokes'],
            "completed_at": format_datetime(score.get('completed_at')),
            "created_at": format_datetime(score.get('created_at'))
        }
        
        return jsonify(response), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al registrar la puntuación",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/increment-strokes', methods=['POST'])
def increment_hole_strokes(match_id):
    """
    Endpoint para incrementar el número de golpes de un jugador en un hoyo.
    
    Este endpoint se llama cuando un jugador confirma que ha ejecutado un golpe.
    Incrementa en 1 (o en el número especificado) los golpes del jugador en el hoyo.
    
    Recibe en el body JSON:
    - user_id: ID del usuario/jugador (requerido)
    - course_id: ID del campo de golf (requerido)
    - hole_number: Número del hoyo (requerido)
    - strokes: Número de golpes a incrementar (opcional, default: 1)
    - ball_start_latitude: Latitud inicial de la bola (opcional, para evaluación)
    - ball_start_longitude: Longitud inicial de la bola (opcional, para evaluación)
    - club_used_id: ID del palo utilizado (opcional)
    - club_used_name: Nombre del palo utilizado (opcional, se busca si no se proporciona club_used_id)
    - trajectory_type: Trayectoria escogida - 'conservadora', 'riesgo' o 'optima' (opcional)
    - proposed_distance_meters: Distancia propuesta en metros (opcional)
    - proposed_club_id: ID del palo propuesto (opcional)
    - proposed_club_name: Nombre del palo propuesto (opcional)
    
    Ejemplo POST (incrementar en 1):
    {
        "user_id": 1,
        "course_id": 1,
        "hole_number": 5
    }
    
    Ejemplo POST (con información de golpe para evaluación):
    {
        "user_id": 1,
        "course_id": 1,
        "hole_number": 5,
        "ball_start_latitude": 40.44445,
        "ball_start_longitude": -3.87095,
        "club_used_name": "Hierro 7",
        "trajectory_type": "optima",
        "proposed_distance_meters": 150.5
    }
    
    Respuesta exitosa (200):
    {
        "id": 123,
        "match_player_id": 45,
        "hole_id": 5,
        "course_id": 1,
        "hole_number": 5,
        "strokes": 4,
        "strokes_incremented": 1,
        "completed_at": "2024-01-15T10:30:00",
        "created_at": "2024-01-15T10:30:00"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        required_fields = ['user_id', 'course_id', 'hole_number']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Se requiere el campo '{field}' en el body JSON"}), 400
        
        try:
            user_id = int(data['user_id'])
            course_id = int(data['course_id'])
            hole_number = int(data['hole_number'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'user_id', 'course_id' y 'hole_number' deben ser números enteros"}), 400
        
        # strokes es opcional, por defecto 1
        strokes = 1
        if 'strokes' in data:
            try:
                strokes = int(data['strokes'])
                if strokes <= 0:
                    return jsonify({"error": "El campo 'strokes' debe ser un número entero mayor que 0"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'strokes' debe ser un número entero válido"}), 400
        
        match_service = get_match_service()
        
        # ANTES de incrementar, evaluar el golpe anterior si existe y se proporciona la nueva posición
        stroke_evaluation = None
        if 'ball_start_latitude' in data and 'ball_start_longitude' in data:
            try:
                ball_start_lat = float(data['ball_start_latitude'])
                ball_start_lon = float(data['ball_start_longitude'])
                
                # Obtener información del hoyo
                from kdi_back.api.dependencies import get_golf_service
                golf_service = get_golf_service()
                hole_info = golf_service.get_hole_by_course_and_number(course_id, hole_number)
                if hole_info:
                    hole_id = hole_info['id']
                    
                    # Verificar si hay un golpe pendiente de evaluación
                    pending_stroke = match_service.match_repository.get_last_unevaluated_stroke(
                        match_id, user_id, hole_id
                    )
                    
                    if pending_stroke:
                        # Detectar si la nueva posición está en el green
                        is_on_green = golf_service.is_ball_on_green(ball_start_lat, ball_start_lon, hole_id)
                        
                        # Obtener número actual de golpes para validación
                        current_strokes = match_service.match_repository.get_hole_strokes_for_player(
                            match_id, user_id, hole_id
                        )
                        
                        # Evaluar el golpe anterior con la nueva posición como posición final
                        stroke_evaluation = match_service.evaluate_stroke(
                            match_id=match_id,
                            user_id=user_id,
                            course_id=course_id,
                            hole_number=hole_number,
                            ball_end_latitude=ball_start_lat,
                            ball_end_longitude=ball_start_lon,
                            is_on_green=is_on_green,
                            current_strokes=current_strokes
                        )
                        
                        # Si se evaluó un golpe y tiene información del palo, actualizar estadísticas
                        # NO actualizar si el golpe fue en el green (evaluation_quality es None)
                        if stroke_evaluation and stroke_evaluation.get('club_used_id') and stroke_evaluation.get('evaluation_quality') is not None:
                            try:
                                from kdi_back.api.dependencies import get_player_service
                                player_service = get_player_service()
                                player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
                                
                                if player_profile:
                                    # Obtener distancia objetivo
                                    target_distance = stroke_evaluation.get('proposed_distance_meters')
                                    if not target_distance:
                                        target_distance = stroke_evaluation.get('ball_end_distance_meters', 0)
                                    
                                    actual_distance = stroke_evaluation.get('ball_end_distance_meters', 0)
                                    quality_score = stroke_evaluation.get('evaluation_quality', 0)
                                    
                                    # Actualizar estadísticas del palo
                                    player_service.player_repository.update_club_statistics_after_stroke(
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
        
        score = match_service.increment_hole_strokes(match_id, user_id, course_id, hole_number, strokes)
        
        # Si se proporciona información de posición inicial, crear registro de stroke para evaluación
        stroke_created = None
        if 'ball_start_latitude' in data and 'ball_start_longitude' in data:
            try:
                ball_start_lat = float(data['ball_start_latitude'])
                ball_start_lon = float(data['ball_start_longitude'])
                
                # Obtener número de golpe actual en el hoyo
                from kdi_back.api.dependencies import get_golf_service
                golf_service = get_golf_service()
                hole_info = golf_service.get_hole_by_course_and_number(course_id, hole_number)
                if hole_info:
                    hole_id = hole_info['id']
                    current_strokes = match_service.match_repository.get_hole_strokes_for_player(
                        match_id, user_id, hole_id
                    )
                    stroke_number = current_strokes  # El golpe que acabamos de incrementar
                    
                    # Buscar palos por nombre si se proporciona
                    club_used_id = data.get('club_used_id')
                    if not club_used_id and 'club_used_name' in data:
                        from kdi_back.api.dependencies import get_player_service
                        player_service = get_player_service()
                        club = player_service.player_repository.get_golf_club_by_name(data['club_used_name'])
                        if club:
                            club_used_id = club['id']
                    
                    proposed_club_id = data.get('proposed_club_id')
                    if not proposed_club_id and 'proposed_club_name' in data:
                        from kdi_back.api.dependencies import get_player_service
                        player_service = get_player_service()
                        club = player_service.player_repository.get_golf_club_by_name(data['proposed_club_name'])
                        if club:
                            proposed_club_id = club['id']
                    
                    # Campos opcionales
                    trajectory_type = data.get('trajectory_type')
                    proposed_distance_meters = data.get('proposed_distance_meters')
                    if proposed_distance_meters:
                        try:
                            proposed_distance_meters = float(proposed_distance_meters)
                        except (ValueError, TypeError):
                            proposed_distance_meters = None
                    
                    # Crear el stroke
                    stroke_created = match_service.create_stroke(
                        match_id=match_id,
                        user_id=user_id,
                        course_id=course_id,
                        hole_number=hole_number,
                        ball_start_latitude=ball_start_lat,
                        ball_start_longitude=ball_start_lon,
                        stroke_number=stroke_number,
                        club_used_id=club_used_id,
                        trajectory_type=trajectory_type,
                        proposed_distance_meters=proposed_distance_meters,
                        proposed_club_id=proposed_club_id
                    )
            except (ValueError, TypeError) as e:
                # Si hay error creando el stroke, no fallar el incremento de golpes
                print(f"Advertencia: No se pudo crear el registro de stroke: {e}")
        
        # Obtener información del hoyo para incluir course_id y hole_number en la respuesta
        from kdi_back.api.dependencies import get_golf_service
        golf_service = get_golf_service()
        hole_info = golf_service.get_hole_by_id(score['hole_id'])
        
        response = {
            "id": score['id'],
            "match_player_id": score['match_player_id'],
            "hole_id": score['hole_id'],
            "course_id": hole_info['course_id'] if hole_info else course_id,
            "hole_number": hole_info['hole_number'] if hole_info else hole_number,
            "strokes": score['strokes'],
            "strokes_incremented": strokes,
            "completed_at": format_datetime(score.get('completed_at')),
            "created_at": format_datetime(score.get('created_at'))
        }
        
        # Agregar información del stroke si se creó
        if stroke_created:
            response["stroke"] = {
                "id": stroke_created['id'],
                "stroke_number": stroke_created['stroke_number'],
                "evaluated": stroke_created['evaluated']
            }
        
        # Agregar información de evaluación del golpe anterior si se evaluó
        if stroke_evaluation:
            response["previous_stroke_evaluation"] = {
                "stroke_id": stroke_evaluation.get('id'),
                "evaluation_quality": stroke_evaluation.get('evaluation_quality'),
                "evaluation_distance_error": stroke_evaluation.get('evaluation_distance_error'),
                "evaluation_direction_error": stroke_evaluation.get('evaluation_direction_error'),
                "ball_end_distance_meters": stroke_evaluation.get('ball_end_distance_meters')
            }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al incrementar los golpes",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/complete-hole', methods=['POST'])
def complete_hole(match_id):
    """
    Endpoint para marcar el final de un hoyo para un jugador.
    
    Este endpoint se llama cuando un jugador completa un hoyo y retorna
    estadísticas del hoyo y del partido.
    
    Recibe en el body JSON:
    - user_id: ID del usuario/jugador (requerido)
    - course_id: ID del campo de golf (requerido)
    - hole_number: Número del hoyo (requerido)
    
    Ejemplo POST:
    {
        "user_id": 1,
        "course_id": 1,
        "hole_number": 5
    }
    
    Respuesta exitosa (200):
    {
        "hole_strokes": 4,
        "total_strokes": 18,
        "ranking": {
            "position": 2,
            "total_strokes": 18,
            "holes_completed": 5,
            "user_id": 1,
            "username": "jugador1",
            "first_name": "Juan",
            "last_name": "Pérez"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        required_fields = ['user_id', 'course_id', 'hole_number']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Se requiere el campo '{field}' en el body JSON"}), 400
        
        try:
            user_id = int(data['user_id'])
            course_id = int(data['course_id'])
            hole_number = int(data['hole_number'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'user_id', 'course_id' y 'hole_number' deben ser números enteros"}), 400
        
        match_service = get_match_service()
        result = match_service.complete_hole(match_id, user_id, course_id, hole_number)
        
        response = {
            "hole_strokes": result['hole_strokes'],
            "total_strokes": result['total_strokes'],
            "ranking": result['ranking']
        }
        
        # Agregar evaluación del green si existe
        if 'green_evaluation' in result:
            response["green_evaluation"] = result['green_evaluation']
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al completar el hoyo",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    """
    Endpoint para obtener los detalles completos de un partido.
    
    Respuesta exitosa (200):
    {
        "match": {...},
        "players": [...],
        "leaderboard": [...]
    }
    """
    try:
        match_service = get_match_service()
        result = match_service.get_match_details(match_id)
        
        # Formatear respuesta
        response = {
            "match": {
                "id": result['match']['id'],
                "course_id": result['match']['course_id'],
                "name": result['match'].get('name'),
                "status": result['match']['status'],
                "started_at": format_datetime(result['match'].get('started_at')),
                "completed_at": format_datetime(result['match'].get('completed_at')),
                "created_at": format_datetime(result['match'].get('created_at')),
                "updated_at": format_datetime(result['match'].get('updated_at'))
            },
            "players": [
                {
                    "id": p['id'],
                    "match_id": p['match_id'],
                    "user_id": p['user_id'],
                    "starting_hole_number": p['starting_hole_number'],
                    "total_strokes": p['total_strokes'],
                    "username": p.get('username'),
                    "first_name": p.get('first_name'),
                    "last_name": p.get('last_name'),
                    "email": p.get('email'),
                    "created_at": format_datetime(p.get('created_at'))
                }
                for p in result['players']
            ],
            "leaderboard": [
                {
                    "id": l['id'],
                    "match_id": l['match_id'],
                    "user_id": l['user_id'],
                    "starting_hole_number": l['starting_hole_number'],
                    "total_strokes": l['total_strokes'],
                    "holes_completed": l.get('holes_completed', 0),
                    "username": l.get('username'),
                    "first_name": l.get('first_name'),
                    "last_name": l.get('last_name'),
                    "email": l.get('email')
                }
                for l in result['leaderboard']
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener los detalles del partido",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/complete', methods=['POST'])
def complete_match(match_id):
    """
    Endpoint para completar un partido y determinar el ganador.
    
    Respuesta exitosa (200):
    {
        "match": {...},
        "leaderboard": [...],
        "winner": {...}
    }
    """
    try:
        match_service = get_match_service()
        result = match_service.complete_match(match_id)
        
        # Formatear respuesta
        response = {
            "match": {
                "id": result['match']['id'],
                "course_id": result['match']['course_id'],
                "name": result['match'].get('name'),
                "status": result['match']['status'],
                "started_at": format_datetime(result['match'].get('started_at')),
                "completed_at": format_datetime(result['match'].get('completed_at')),
                "created_at": format_datetime(result['match'].get('created_at')),
                "updated_at": format_datetime(result['match'].get('updated_at'))
            },
            "leaderboard": [
                {
                    "id": l['id'],
                    "match_id": l['match_id'],
                    "user_id": l['user_id'],
                    "starting_hole_number": l['starting_hole_number'],
                    "total_strokes": l['total_strokes'],
                    "holes_completed": l.get('holes_completed', 0),
                    "username": l.get('username'),
                    "first_name": l.get('first_name'),
                    "last_name": l.get('last_name'),
                    "email": l.get('email')
                }
                for l in result['leaderboard']
            ],
            "winner": {
                "id": result['winner']['id'],
                "user_id": result['winner']['user_id'],
                "total_strokes": result['winner']['total_strokes'],
                "username": result['winner'].get('username'),
                "first_name": result['winner'].get('first_name'),
                "last_name": result['winner'].get('last_name')
            } if result['winner'] else None
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al completar el partido",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/leaderboard', methods=['GET'])
def get_match_leaderboard(match_id):
    """
    Endpoint para obtener el ranking de jugadores de un partido.
    """
    try:
        match_service = get_match_service()
        leaderboard = match_service.get_match_leaderboard(match_id)
        
        response = [
            {
                "id": l['id'],
                "match_id": l['match_id'],
                "user_id": l['user_id'],
                "starting_hole_number": l['starting_hole_number'],
                "total_strokes": l['total_strokes'],
                "holes_completed": l.get('holes_completed', 0),
                "username": l.get('username'),
                "first_name": l.get('first_name'),
                "last_name": l.get('last_name'),
                "email": l.get('email')
            }
            for l in leaderboard
        ]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener el leaderboard",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/player/<int:user_id>/scores', methods=['GET'])
def get_player_scores(match_id, user_id):
    """
    Endpoint para obtener todas las puntuaciones de un jugador en un partido.
    """
    try:
        match_service = get_match_service()
        scores = match_service.get_player_scores(match_id, user_id)
        
        response = [
            {
                "id": s['id'],
                "match_player_id": s['match_player_id'],
                "hole_id": s['hole_id'],
                "strokes": s['strokes'],
                "hole_number": s.get('hole_number'),
                "par": s.get('par'),
                "length": s.get('length'),
                "completed_at": format_datetime(s.get('completed_at')),
                "created_at": format_datetime(s.get('created_at'))
            }
            for s in scores
        ]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener las puntuaciones del jugador",
            "details": str(e)
        }), 500


@match_bp.route('/match/course/<int:course_id>', methods=['GET'])
def get_matches_by_course(course_id):
    """
    Endpoint para obtener todos los partidos de un campo de golf.
    
    Query parameters:
    - status: Filtro opcional por estado (in_progress, completed, cancelled)
    """
    try:
        status = request.args.get('status')
        
        match_service = get_match_service()
        matches = match_service.get_matches_by_course(course_id, status)
        
        response = [
            {
                "id": m['id'],
                "course_id": m['course_id'],
                "name": m.get('name'),
                "status": m['status'],
                "started_at": format_datetime(m.get('started_at')),
                "completed_at": format_datetime(m.get('completed_at')),
                "created_at": format_datetime(m.get('created_at')),
                "updated_at": format_datetime(m.get('updated_at'))
            }
            for m in matches
        ]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener los partidos del campo",
            "details": str(e)
        }), 500


@match_bp.route('/match/<int:match_id>/state/<int:user_id>', methods=['GET'])
@require_auth
def get_match_state(match_id, user_id):
    """
    Endpoint para obtener el estado actual del partido para un jugador.
    
    Retorna:
    - course_id: ID del campo
    - current_hole_number: Hoyo actual en el que está jugando
    - current_hole_id: ID del hoyo actual
    - strokes_in_current_hole: Número de golpes en el hoyo actual
    - completed_holes: Lista de hoyos completados con sus puntuaciones
    - total_strokes: Total de golpes en el partido
    
    Respuesta exitosa (200):
    {
        "course_id": 1,
        "current_hole_number": 3,
        "current_hole_id": 15,
        "strokes_in_current_hole": 2,
        "completed_holes": [
            {
                "hole_id": 13,
                "hole_number": 1,
                "par": 4,
                "strokes": 5,
                "completed_at": "2024-01-15T10:45:00"
            },
            {
                "hole_id": 14,
                "hole_number": 2,
                "par": 4,
                "strokes": 4,
                "completed_at": "2024-01-15T11:00:00"
            }
        ],
        "total_strokes": 11
    }
    """
    try:
        match_service = get_match_service()
        
        # Obtener el estado del partido
        match_state = match_service.get_match_state(match_id, user_id)
        
        if match_state is None:
            return jsonify({
                "error": "No se encontró el estado del partido",
                "details": f"No existe un partido con ID {match_id} o el usuario {user_id} no está en el partido"
            }), 404
        
        # Formatear fechas
        for hole in match_state.get('completed_holes', []):
            if 'completed_at' in hole:
                hole['completed_at'] = format_datetime(hole['completed_at'])
        
        return jsonify(match_state), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener el estado del partido",
            "details": str(e)
        }), 500


@match_bp.route('/match/player/<int:user_id>', methods=['GET'])
def get_matches_by_player(user_id):
    """
    Endpoint para obtener todos los partidos de un jugador.
    
    Query parameters:
    - status: Filtro opcional por estado (in_progress, completed, cancelled)
    """
    try:
        status = request.args.get('status')
        
        match_service = get_match_service()
        matches = match_service.get_matches_by_player(user_id, status)
        
        response = [
            {
                "id": m['id'],
                "course_id": m['course_id'],
                "name": m.get('name'),
                "status": m['status'],
                "started_at": format_datetime(m.get('started_at')),
                "completed_at": format_datetime(m.get('completed_at')),
                "created_at": format_datetime(m.get('created_at')),
                "updated_at": format_datetime(m.get('updated_at'))
            }
            for m in matches
        ]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener los partidos del jugador",
            "details": str(e)
        }), 500

