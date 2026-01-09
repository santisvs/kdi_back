# -*- coding: utf-8 -*-
"""Game routes - Endpoints para comandos de voz durante partidos"""
from flask import Blueprint, jsonify, request, g
from kdi_back.api.dependencies import get_voice_service
from kdi_back.api.middleware.auth_middleware import require_auth

game_bp = Blueprint('game', __name__)


@game_bp.route('/match/<int:match_id>/voice-command', methods=['POST'])
@require_auth
def voice_command(match_id):
    """
    Endpoint principal para procesar comandos de voz durante un partido.
    
    Este endpoint actúa como gestor unificado de peticiones de voz:
    1. Recibe token (en header), course_id, match_id, GPS y query en lenguaje natural
    2. Clasifica la intención de la petición usando IA
    3. Enruta a la funcionalidad correspondiente
    4. Retorna respuesta en lenguaje natural
    
    Headers:
    - Authorization: Bearer <token> (requerido)
    
    Body JSON:
    - course_id: ID del campo de golf (requerido)
    - latitude: Latitud GPS de la posición de la pelota (requerido)
    - longitude: Longitud GPS de la posición de la pelota (requerido)
    - query: Petición en lenguaje natural (requerido)
    
    Ejemplo POST:
    {
        "course_id": 1,
        "latitude": 40.44445,
        "longitude": -3.87095,
        "query": "¿Qué palo debo usar?"
    }
    
    Respuesta exitosa (200):
    {
        "response": "Estás a 88 metros del hoyo, te recomiendo utilizar Pitching Wedge con swing completo intentando alcanzar el green. Ten en cuenta: Bunker derecho.",
        "intent": "recommend_shot",
        "confidence": 0.95,
        "data": {
            "distance_meters": 88.0,
            "distance_yards": 96.24,
            "recommended_club": "Pitching Wedge",
            "swing_type": "completo",
            "target": "flag",
            "obstacles_count": 1,
            "risk_level": 15.5,
            "hole_info": {...}
        }
    }
    
    Tipos de intenciones soportadas:
    - recommend_shot: Recomendación de palo/golpe
    - register_stroke: Registrar golpe
    - check_distance: Consultar distancia al hoyo
    - check_obstacles: Consultar obstáculos
    - check_terrain: Consultar tipo de terreno
    - complete_hole: Completar hoyo
    - check_ranking: Consultar ranking del partido
    - check_hole_stats: Consultar estadísticas del hoyo
    - check_hole_info: Consultar información del hoyo
    - check_weather: Consultar clima
    """
    try:
        # Obtener usuario autenticado
        user_id = g.current_user['id']
        
        # Validar body JSON
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        required_fields = ['course_id', 'latitude', 'longitude', 'query']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Se requiere el campo '{field}' en el body JSON"}), 400
        
        # Validar y obtener valores
        try:
            course_id = int(data['course_id'])
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({
                "error": "Los campos 'course_id' debe ser un entero y 'latitude'/'longitude' deben ser números válidos"
            }), 400
        
        query = str(data['query']).strip()
        if not query:
            return jsonify({"error": "El campo 'query' no puede estar vacío"}), 400
        
        # Obtener servicio de voz
        voice_service = get_voice_service()
        
        # Procesar comando de voz
        result = voice_service.process_voice_command(
            user_id=user_id,
            match_id=match_id,
            course_id=course_id,
            latitude=latitude,
            longitude=longitude,
            query=query
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al procesar el comando de voz",
            "details": str(e)
        }), 500



