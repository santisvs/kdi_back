# -*- coding: utf-8 -*-
"""Golf routes"""
from flask import Blueprint, jsonify, request
from kdi_back.infrastructure.agents.golf_agent import get_golf_recommendation
from kdi_back.infrastructure.agents.next_shot_agent import get_next_shot_recommendation
from kdi_back.api.dependencies import get_golf_service, get_player_service

golf_bp = Blueprint('golf', __name__)


def _get_hole_id_from_request(data, golf_service, latitude=None, longitude=None):
    """
    Helper function para obtener hole_id desde course_id/hole_number o identificarlo desde coordenadas.
    
    Args:
        data: Datos del request JSON
        golf_service: Instancia del servicio de golf
        latitude: Latitud (opcional, para identificación automática)
        longitude: Longitud (opcional, para identificación automática)
    
    Returns:
        Tupla (hole_id, hole_info, course_id, hole_number) o None si no se puede determinar
    """
    course_id = None
    hole_number = None
    hole_id = None
    hole_info = None
    
    # Intentar obtener course_id y hole_number del request
    if 'course_id' in data or 'hole_number' in data:
        if 'course_id' not in data or 'hole_number' not in data:
            return None, None, None, None  # Deben estar juntos
        try:
            course_id = int(data['course_id'])
            hole_number = int(data['hole_number'])
            hole_info = golf_service.get_hole_by_course_and_number(course_id, hole_number)
            if hole_info:
                hole_id = hole_info['id']
        except (ValueError, TypeError):
            return None, None, None, None
    
    # Si no se proporcionaron course_id/hole_number, intentar identificarlo desde coordenadas
    if hole_id is None and latitude is not None and longitude is not None:
        hole_info = golf_service.identify_hole_by_ball_position(latitude, longitude)
        if hole_info:
            hole_id = hole_info['id']
            course_id = hole_info['course_id']
            hole_number = hole_info['hole_number']
    
    return hole_id, hole_info, course_id, hole_number


@golf_bp.route('/golf', methods=['POST'])
def golf():
    """
    Endpoint para obtener recomendaciones de palo de golf basadas en GPS y situación
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - query: Texto en lenguaje natural describiendo la situación del juego (string)
    
    Ejemplo POST:
    {
        "latitude": 40.4168,
        "longitude": -3.7038,
        "query": "Estoy a 150 metros del hoyo, hay viento en contra y estoy en el rough"
    }
    
    Respuesta:
    {
        "recommendation": "Te recomiendo utilizar el hierro siete intentando botar la bola en green, con el objetivo de hacer 150 metros"
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron todos los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude', 'longitude' y 'query'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        if 'query' not in data:
            return jsonify({"error": "Se requiere el campo 'query' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        query = str(data['query']).strip()
        if not query:
            return jsonify({"error": "El campo 'query' no puede estar vacío"}), 400
        
        # Llamar al agente de golf
        recommendation = get_golf_recommendation(latitude, longitude, query)
        
        # Devolver solo la recomendación del agente
        return jsonify({
            "recommendation": str(recommendation)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al procesar la recomendación de golf",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/identify-hole', methods=['POST'])
def identify_hole():
    """
    Endpoint para identificar en qué hoyo se encuentra una bola según su posición GPS.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    
    Ejemplo POST:
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Respuesta (si se encuentra el hoyo):
    {
        "hole": {
            "id": 1,
            "course_id": 1,
            "hole_number": 1,
            "par": 4,
            "length": 367,
            "course_name": "Las Rejas Club de Golf"
        }
    }
    
    Respuesta (si no se encuentra):
    {
        "hole": null,
        "message": "No se encontró ningún hoyo en esa posición"
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron todos los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Usar el servicio de dominio para identificar el hoyo
        golf_service = get_golf_service()
        hole = golf_service.identify_hole_by_ball_position(latitude, longitude)
        
        if hole:
            return jsonify({
                "hole": hole
            }), 200
        else:
            return jsonify({
                "hole": None,
                "message": "No se encontró ningún hoyo en esa posición"
            }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al identificar el hoyo",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/terrain-type', methods=['POST'])
def terrain_type():
    """
    Endpoint para determinar el tipo de terreno donde se encuentra una bola según su posición GPS.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - course_id: ID del campo de golf (opcional, debe ir con hole_number)
    - hole_number: Número del hoyo (opcional, debe ir con course_id)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (con course_id y hole_number):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (sin course_id/hole_number - identifica automáticamente):
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Respuesta (si está en un obstáculo):
    {
        "terrain_type": "bunker",
        "hole_id": 1,
        "hole_info": {
            "id": 1,
            "hole_number": 1,
            "par": 4,
            "course_name": "Las Rejas Club de Golf"
        }
    }
    
    Respuesta (si está en terreno normal):
    {
        "terrain_type": null,
        "hole_id": 1,
        "message": "La bola está en terreno normal (fairway/green)"
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Validar course_id y hole_number si se proporcionan
        if 'course_id' in data or 'hole_number' in data:
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # Obtener hole_id desde course_id/hole_number o identificarlo desde coordenadas
        hole_id, hole_info, course_id, hole_number = _get_hole_id_from_request(
            data, golf_service, latitude, longitude
        )
        
        if hole_id is None:
            return jsonify({
                "error": "No se pudo identificar el hoyo. Proporciona 'course_id' y 'hole_number' o asegúrate de que las coordenadas estén dentro de un hoyo."
            }), 400
        
        # Usar el servicio de dominio para determinar el tipo de terreno
        result = golf_service.determine_terrain_type(latitude, longitude, hole_id)
        
        # Añadir mensaje descriptivo
        if result['terrain_type']:
            result['message'] = f"La bola está en terreno: {result['terrain_type']}"
        else:
            result['message'] = "La bola está en terreno normal (fairway/green)"
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al determinar el tipo de terreno",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/distance-to-hole', methods=['POST'])
def distance_to_hole():
    """
    Endpoint para calcular la distancia desde la posición de la bola hasta la bandera del hoyo.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - course_id: ID del campo de golf (opcional, debe ir con hole_number)
    - hole_number: Número del hoyo (opcional, debe ir con course_id)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (con course_id y hole_number):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (sin course_id/hole_number - identifica automáticamente):
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Respuesta:
    {
        "distance_meters": 150.25,
        "distance_yards": 164.42,
        "hole_id": 1,
        "hole_info": {
            "id": 1,
            "hole_number": 1,
            "par": 4,
            "course_name": "Las Rejas Club de Golf"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Validar course_id y hole_number si se proporcionan
        if 'course_id' in data or 'hole_number' in data:
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # Obtener hole_id desde course_id/hole_number o identificarlo desde coordenadas
        hole_id, hole_info, course_id, hole_number = _get_hole_id_from_request(
            data, golf_service, latitude, longitude
        )
        
        if hole_id is None:
            return jsonify({
                "error": "No se pudo identificar el hoyo. Proporciona 'course_id' y 'hole_number' o asegúrate de que las coordenadas estén dentro de un hoyo."
            }), 400
        
        # Usar el servicio de dominio para calcular la distancia
        result = golf_service.calculate_distance_to_hole(latitude, longitude, hole_id)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al calcular la distancia al hoyo",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/obstacles-between', methods=['POST'])
def obstacles_between():
    """
    Endpoint para encontrar los obstáculos que intersectan con la línea entre la bola y la bandera.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - course_id: ID del campo de golf (opcional, debe ir con hole_number)
    - hole_number: Número del hoyo (opcional, debe ir con course_id)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (con course_id y hole_number):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (sin course_id/hole_number - identifica automáticamente):
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Respuesta (con obstáculos encontrados):
    {
        "obstacles": [
            {
                "id": 1,
                "hole_id": 1,
                "type": "bunker",
                "name": "Bunker derecho 1_1",
                "shape_wkt": "POLYGON(...)"
            },
            {
                "id": 2,
                "hole_id": 1,
                "type": "water",
                "name": "Lago frontal",
                "shape_wkt": "POLYGON(...)"
            }
        ],
        "obstacle_count": 2,
        "hole_id": 1,
        "hole_info": {
            "id": 1,
            "hole_number": 1,
            "par": 4,
            "course_name": "Las Rejas Club de Golf"
        }
    }
    
    Respuesta (sin obstáculos):
    {
        "obstacles": [],
        "obstacle_count": 0,
        "hole_id": 1,
        "message": "No hay obstáculos entre la bola y la bandera"
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Validar course_id y hole_number si se proporcionan
        if 'course_id' in data or 'hole_number' in data:
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # Obtener hole_id desde course_id/hole_number o identificarlo desde coordenadas
        hole_id, hole_info, course_id, hole_number = _get_hole_id_from_request(
            data, golf_service, latitude, longitude
        )
        
        if hole_id is None:
            return jsonify({
                "error": "No se pudo identificar el hoyo. Proporciona 'course_id' y 'hole_number' o asegúrate de que las coordenadas estén dentro de un hoyo."
            }), 400
        
        # Usar el servicio de dominio para encontrar obstáculos
        result = golf_service.find_obstacles_between_ball_and_flag(latitude, longitude, hole_id)
        
        # Añadir mensaje descriptivo
        if result['obstacle_count'] == 0:
            result['message'] = "No hay obstáculos entre la bola y la bandera"
        else:
            result['message'] = f"Se encontraron {result['obstacle_count']} obstáculo(s) entre la bola y la bandera"
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al buscar obstáculos",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/nearest-optimal-shot', methods=['POST'])
def nearest_optimal_shot():
    """
    Endpoint para encontrar el golpe óptimo más cercano a la posición actual de la bola.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - course_id: ID del campo de golf (opcional, debe ir con hole_number)
    - hole_number: Número del hoyo (opcional, debe ir con course_id)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (con course_id y hole_number):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (sin course_id/hole_number - identifica automáticamente):
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Respuesta:
    {
        "optimal_shot": {
            "id": 1,
            "hole_id": 1,
            "description": "Salida con drive al centro de la calle para dejar la bola a la derecha del segundo bunker de la izquierda",
            "path_wkt": "LINESTRING(-3.868570058479186 40.44451991692553, -3.87094755026384 40.44445006655005)"
        },
        "distance_meters": 25.50,
        "distance_yards": 27.89,
        "hole_id": 1,
        "hole_info": {
            "id": 1,
            "hole_number": 1,
            "par": 4,
            "course_name": "Las Rejas Club de Golf"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Validar course_id y hole_number si se proporcionan
        if 'course_id' in data or 'hole_number' in data:
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # Obtener hole_id desde course_id/hole_number o identificarlo desde coordenadas
        hole_id, hole_info, course_id, hole_number = _get_hole_id_from_request(
            data, golf_service, latitude, longitude
        )
        
        if hole_id is None:
            return jsonify({
                "error": "No se pudo identificar el hoyo. Proporciona 'course_id' y 'hole_number' o asegúrate de que las coordenadas estén dentro de un hoyo."
            }), 400
        
        # Usar el servicio de dominio para encontrar el golpe óptimo más cercano
        result = golf_service.find_nearest_optimal_shot(latitude, longitude, hole_id)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al buscar el golpe óptimo más cercano",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/next-shot', methods=['POST'])
def next_shot():
    """
    Endpoint para obtener recomendación del siguiente golpe basándose en información detallada del campo.
    
    Este endpoint utiliza las funcionalidades de análisis del campo para obtener información completa
    y proporcionarla a un agente IA que recomienda el palo a utilizar.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float)
    - longitude: Longitud GPS de la posición de la pelota (float)
    - course_id: ID del campo de golf (opcional, debe ir con hole_number)
    - hole_number: Número del hoyo (opcional, debe ir con course_id)
    - user_id: ID del usuario/jugador (opcional, si se proporciona usa el perfil del jugador)
    - ball_situation_description: Descripción opcional de la situación de la bola y lo que ve el jugador (string)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (sin perfil de jugador):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (con perfil de jugador):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1,
        "user_id": 1
    }
    
    Ejemplo POST (con descripción de situación de la bola):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1,
        "user_id": 1,
        "ball_situation_description": "La bola está en una posición elevada, puedo ver el green claramente. Hay viento en contra moderado."
    }
    
    Respuesta:
    {
        "recommendation": "Te recomiendo utilizar el hierro siete intentando botar la bola en green, con el objetivo de hacer 150 metros, evitando el bunker que hay en el camino",
        "analysis": {
            "hole_info": {
                "id": 1,
                "hole_number": 1,
                "par": 4,
                "length": 367,
                "course_name": "Las Rejas Club de Golf"
            },
            "distance_meters": 150.25,
            "distance_yards": 164.42,
            "terrain_type": null,
            "obstacles_count": 1,
            "obstacles": [
                {
                    "id": 1,
                    "type": "bunker",
                    "name": "Bunker derecho 1_1"
                }
            ]
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # Validar course_id y hole_number si se proporcionan
        if 'course_id' in data or 'hole_number' in data:
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
        
        # user_id es opcional
        user_id = None
        if 'user_id' in data:
            try:
                user_id = int(data['user_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'user_id' debe ser un número entero válido"}), 400
        
        # ball_situation_description es opcional
        ball_situation_description = None
        if 'ball_situation_description' in data:
            ball_situation_description = str(data['ball_situation_description']).strip()
            if not ball_situation_description:
                ball_situation_description = None
        
        # Usar el servicio de dominio para obtener toda la información
        golf_service = get_golf_service()
        
        # 1. Obtener información del hoyo (por course_id/hole_number o identificando desde coordenadas)
        hole_id, hole_info, course_id, hole_number = _get_hole_id_from_request(
            data, golf_service, latitude, longitude
        )
        
        if hole_id is None or hole_info is None:
            return jsonify({
                "error": "No se pudo identificar el hoyo. Proporciona 'course_id' y 'hole_number' o asegúrate de que las coordenadas estén dentro de un hoyo."
            }), 404
        
        # 2. Obtener estadísticas del jugador si se proporcionó user_id (necesarias para evaluar trayectorias)
        player_club_statistics = None
        if user_id:
            try:
                player_service = get_player_service()
                player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
                
                if player_profile:
                    player_club_statistics = player_service.player_repository.get_player_club_statistics(
                        player_profile['id']
                    )
                    # Si no hay estadísticas, no pasa nada, el agente funcionará sin ellas
            except Exception as e:
                # Si hay error obteniendo el perfil, continuar sin él
                print(f"Advertencia: No se pudo obtener el perfil del jugador {user_id}: {e}")
        
        # 3. Verificar que el hoyo tenga bandera antes de evaluar trayectorias
        flag_check = golf_service.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        if flag_check is None:
            return jsonify({
                "error": f"El hoyo número {hole_number} del campo {course_id} no tiene una bandera (flag) definida en la base de datos",
                "details": "Para usar este endpoint, el hoyo debe tener un punto con type='flag' en la tabla hole_point.",
                "course_id": course_id,
                "hole_number": hole_number
            }), 400
        
        # 4. Determinar tipo de terreno
        terrain_result = golf_service.determine_terrain_type(latitude, longitude, hole_id)
        terrain_type = terrain_result['terrain_type']
        
        # 5. Calcular trayectorias usando la lógica evolutiva (misma que trajectory-options-evol)
        trayectorias_optimal = golf_service.bola_menos_10m_optimal_shot(
            latitude=latitude,
            longitude=longitude,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics
        )
        
        trayectorias_completas = golf_service.find_strategic_shot(
            latitude=latitude,
            longitude=longitude,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics,
            trayectorias_existentes=trayectorias_optimal
        )
        
        resultado_trayectorias = golf_service.evaluacion_final(trayectorias_completas)
        
        trayectoria_optima = resultado_trayectorias.get('trayectoria_optima')
        if not isinstance(trayectoria_optima, dict):
            return jsonify({
                "error": "No se pudo calcular una trayectoria óptima",
                "details": "El algoritmo evolutivo no generó trayectorias válidas para esta posición"
            }), 404
        
        # Extraer información para el agente a partir de la trayectoria óptima
        distance_meters = trayectoria_optima.get('distance_meters')
        distance_yards = trayectoria_optima.get('distance_yards')
        obstacles_for_agent = trayectoria_optima.get('obstacles', [])
        trajectory_description = trayectoria_optima.get('description', '')
        waypoint_description = trayectoria_optima.get('waypoint_description') if trayectoria_optima.get('target') != 'flag' else None
        
        # Preparar info de trayectorias para el agente (incluye alternativas)
        trajectory_info_for_agent = {
            'trayectoria_optima': trayectoria_optima,
            'trayectoria_riesgo': resultado_trayectorias.get('trayectoria_riesgo'),
            'trayectoria_conservadora': resultado_trayectorias.get('trayectoria_conservadora')
        }
        
        # 6. Llamar al agente con toda la información
        recommendation = get_next_shot_recommendation(
            hole_info=hole_info,
            distance_meters=distance_meters,
            distance_yards=distance_yards,
            terrain_type=terrain_type,
            obstacles=obstacles_for_agent,
            player_club_statistics=player_club_statistics,
            ball_situation_description=ball_situation_description,
            trajectory_info=trajectory_info_for_agent
        )
        
        # Preparar respuesta con análisis completo
        response = {
            "recommendation": str(recommendation),
            "analysis": {
                "hole_info": hole_info,
                "distance_meters": distance_meters,
                "distance_yards": distance_yards,
                "terrain_type": terrain_type,
                "obstacles_count": len(obstacles_for_agent),
                "obstacles": obstacles_for_agent,
                "user_id": user_id if user_id else None,
                "player_profile_used": user_id is not None and player_club_statistics is not None,
                "ball_situation_description": ball_situation_description if ball_situation_description else None,
                "trajectory_analysis": resultado_trayectorias
            }
        }
        
        # Agregar estadísticas del jugador si se usaron
        if player_club_statistics:
            response["analysis"]["player_club_statistics"] = [
                {
                    "club_name": stat.get('club_name'),
                    "average_distance_meters": stat.get('average_distance_meters'),
                    "average_error_meters": stat.get('average_error_meters')
                }
                for stat in player_club_statistics
            ]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al obtener recomendación del siguiente golpe",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/trajectory-options', methods=['POST'])
def trajectory_options():
    """
    Endpoint para obtener opciones de trayectorias calculadas con recomendaciones de palo.
    
    Este endpoint es técnico y NO usa el agente IA. Devuelve pura lógica de negocio:
    - Trayectoria directa vs conservadora
    - Palo recomendado para cada trayectoria
    - Metros a realizar
    - Análisis de riesgo
    
    Útil para desarrollo, testing y análisis de la lógica de selección.
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float) - REQUERIDO
    - longitude: Longitud GPS de la posición de la pelota (float) - REQUERIDO
    - course_id: ID del campo de golf (opcional, se identifica automáticamente desde las coordenadas si no se proporciona)
    - hole_number: Número del hoyo (1, 2, 3, etc.) (opcional, se identifica automáticamente desde las coordenadas si no se proporciona)
    - user_id: ID del usuario/jugador (opcional, si se proporciona usa el perfil del jugador)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST (sin course_id/hole_number - se identifica automáticamente):
    {
        "latitude": 40.44445,
        "longitude": -3.87095
    }
    
    Ejemplo POST (con course_id y hole_number explícitos):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1
    }
    
    Ejemplo POST (con perfil de jugador):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1,
        "user_id": 1
    }
    
    Respuesta:
    {
        "hole_info": {...},
        "ball_position": {
            "latitude": 40.44445,
            "longitude": -3.87095,
            "terrain_type": null
        },
        "trajectory_analysis": {
            "recommended": "conservative",
            "direct_trajectory": {
                "description": "Trayectoria directa a la bandera",
                "distance_meters": 150.5,
                "distance_yards": 164.6,
                "target": "flag",
                "obstacles": [...],
                "risk_level": {
                    "total": 55.75,
                    "obstacle_risk": {
                        "value": 53.75,
                        "breakdown": {
                            "base_risk": 50.0,
                            "obstacle_penalty": 0.0,
                            "precision_penalty": 3.75,
                            "coverage_penalty": 0.0
                        }
                    },
                    "terrain_club_risk": {
                        "value": 2.0
                    }
                },
                "club_recommendation": {
                    "recommended_club": "Hierro 7",
                    "club_avg_distance": 130.0,
                    "distance_to_target": 150.5,
                    "recommended_distance": 130.0,
                    "swing_type": "completo",
                    "source": "player_profile"
                }
            },
            "conservative_trajectory": {
                "description": "Trayectoria conservadora siguiendo golpes óptimos",
                "distance_meters": 88.2,
                "distance_yards": 96.5,
                "target": "waypoint",
                "waypoint_description": "Centro de la calle antes de la curva",
                "obstacles": [],
                "risk_level": {
                    "total": 0.0,
                    "obstacle_risk": {
                        "value": 0.0,
                        "breakdown": {
                            "base_risk": 0.0,
                            "obstacle_penalty": 0.0,
                            "precision_penalty": 0.0,
                            "coverage_penalty": 0.0
                        }
                    },
                    "terrain_club_risk": {
                        "value": 0.0
                    }
                },
                "club_recommendation": {
                    "recommended_club": "Gap Wedge",
                    "club_avg_distance": 90.0,
                    "distance_to_target": 88.2,
                    "recommended_distance": 88.2,
                    "swing_type": "completo",
                    "source": "player_profile"
                }
            }
        },
        "player_info": {
            "user_id": 1,
            "has_profile": true,
            "club_count": 14
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # course_id y hole_number son opcionales - deben proporcionarse juntos
        course_id = None
        hole_number = None
        if 'course_id' in data or 'hole_number' in data:
            # Si se proporciona uno, se debe proporcionar el otro
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
            try:
                course_id = int(data['course_id'])
                hole_number = int(data['hole_number'])
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben ser números enteros válidos"
                }), 400
        
        # user_id es opcional
        user_id = None
        if 'user_id' in data:
            try:
                user_id = int(data['user_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'user_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # 1. Obtener información del hoyo (por course_id/hole_number o identificando desde coordenadas)
        if course_id and hole_number:
            # Si se proporcionaron course_id y hole_number, usarlos directamente
            hole_info = golf_service.get_hole_by_course_and_number(course_id, hole_number)
            if not hole_info:
                return jsonify({
                    "error": f"No se encontró el hoyo número {hole_number} en el campo {course_id}"
                }), 404
            hole_id = hole_info['id']
        else:
            # Si no se proporcionaron, identificarlo desde las coordenadas
            hole_info = golf_service.identify_hole_by_ball_position(latitude, longitude)
            if not hole_info:
                return jsonify({
                    "error": "No se pudo identificar el hoyo desde las coordenadas proporcionadas. Por favor, proporciona los campos 'course_id' y 'hole_number'."
                }), 404
            hole_id = hole_info['id']
            course_id = hole_info['course_id']
            hole_number = hole_info['hole_number']
        
        # 2. Determinar tipo de terreno donde está la bola
        terrain_result = golf_service.determine_terrain_type(latitude, longitude, hole_id)
        terrain_type = terrain_result['terrain_type']
        
        # 3. Verificar que el hoyo tenga bandera antes de evaluar trayectorias
        # (esto es necesario para calcular la trayectoria directa)
        flag_check = golf_service.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        if flag_check is None:
            return jsonify({
                "error": f"El hoyo número {hole_number} del campo {course_id} no tiene una bandera (flag) definida en la base de datos",
                "details": "Para usar este endpoint, el hoyo debe tener un punto con type='flag' en la tabla hole_point. Agrega el hoyo al JSON de configuración con su bandera y vuelve a importar los datos.",
                "course_id": course_id,
                "hole_number": hole_number,
                "solution": "Ejecuta: python scripts/recreate_and_import_golf_data.py después de agregar el hoyo al JSON"
            }), 400
        
        # 4. Obtener estadísticas del jugador si se proporcionó user_id (necesarias para evaluar trayectorias)
        player_club_statistics = None
        player_info = {
            'user_id': user_id,
            'has_profile': False,
            'club_count': 0
        }
        
        if user_id:
            try:
                player_service = get_player_service()
                player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
                
                if player_profile:
                    player_club_statistics = player_service.player_repository.get_player_club_statistics(
                        player_profile['id']
                    )
                    if player_club_statistics:
                        player_info['has_profile'] = True
                        player_info['club_count'] = len(player_club_statistics)
            except Exception as e:
                # Si hay error obteniendo el perfil, continuar sin él
                print(f"Advertencia: No se pudo obtener el perfil del jugador {user_id}: {e}")
        
        # 5. Evaluar trayectorias (directa y conservadora) con estadísticas del jugador
        trajectories = golf_service.evaluate_shot_trajectories(latitude, longitude, hole_id, player_club_statistics)
        
        # 5. Calcular recomendación de palo para cada trayectoria
        
        # Trayectoria DIRECTA
        direct_traj = trajectories['direct_trajectory']
        club_recommendation_direct = golf_service.calculate_club_recommendation(
            distance_meters=direct_traj['distance_meters'],
            player_club_statistics=player_club_statistics
        )
        
        # El riesgo ya viene calculado en direct_traj['numeric_risk'] o direct_traj['risk_level']
        # Usar el que esté disponible
        risk_detailed_direct = direct_traj.get('numeric_risk') or direct_traj.get('risk_level')
        if risk_detailed_direct is None:
            # Si no viene calculado, calcularlo (fallback)
            risk_detailed_direct = golf_service._calculate_risk_score_detailed(
                obstacles=direct_traj['obstacles'],
                distance_to_target=direct_traj['distance_meters'],
                target_type=direct_traj.get('target', 'flag'),
                terrain_type=terrain_type,
                recommended_club=club_recommendation_direct.get('recommended_club'),
                player_club_statistics=player_club_statistics
            )
        
        direct_trajectory_result = {
            'description': direct_traj['description'],
            'distance_meters': direct_traj['distance_meters'],
            'distance_yards': direct_traj['distance_yards'],
            'target': direct_traj.get('target', 'flag'),
            'obstacles': direct_traj['obstacles'],
            'obstacle_count': direct_traj['obstacle_count'],
            'risk_level': risk_detailed_direct,
            'club_recommendation': club_recommendation_direct
        }
        
        # Agregar waypoint_description si existe
        if 'waypoint_description' in direct_traj:
            direct_trajectory_result['waypoint_description'] = direct_traj['waypoint_description']
        
        # Trayectoria CONSERVADORA (si existe)
        conservative_trajectory_result = None
        if trajectories['conservative_trajectory']:
            cons_traj = trajectories['conservative_trajectory']
            club_recommendation_cons = golf_service.calculate_club_recommendation(
                distance_meters=cons_traj['distance_meters'],
                player_club_statistics=player_club_statistics
            )
            
            # El riesgo ya viene calculado en cons_traj['numeric_risk'] o cons_traj['risk_level']
            risk_detailed_cons = cons_traj.get('numeric_risk') or cons_traj.get('risk_level')
            if risk_detailed_cons is None:
                # Si no viene calculado, calcularlo (fallback)
                risk_detailed_cons = golf_service._calculate_risk_score_detailed(
                    obstacles=cons_traj['obstacles'],
                    distance_to_target=cons_traj['distance_meters'],
                    target_type=cons_traj.get('target', 'waypoint'),
                    terrain_type=terrain_type,
                    recommended_club=club_recommendation_cons.get('recommended_club'),
                    player_club_statistics=player_club_statistics
                )
            
            conservative_trajectory_result = {
                'description': cons_traj['description'],
                'distance_meters': cons_traj['distance_meters'],
                'distance_yards': cons_traj['distance_yards'],
                'target': cons_traj.get('target', 'waypoint'),
                'obstacles': cons_traj['obstacles'],
                'obstacle_count': cons_traj['obstacle_count'],
                'risk_level': risk_detailed_cons,
                'club_recommendation': club_recommendation_cons
            }
            
            # Agregar waypoint_description si existe
            if 'waypoint_description' in cons_traj:
                conservative_trajectory_result['waypoint_description'] = cons_traj['waypoint_description']
        
        # 6. Preparar respuesta completa
        response = {
            'hole_info': hole_info,
            'ball_position': {
                'latitude': latitude,
                'longitude': longitude,
                'terrain_type': terrain_type
            },
            'trajectory_analysis': {
                'recommended': trajectories['recommended_trajectory'],
                'direct_trajectory': direct_trajectory_result,
                'conservative_trajectory': conservative_trajectory_result
            },
            'player_info': player_info
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al calcular opciones de trayectorias",
            "details": str(e)
        }), 500


@golf_bp.route('/golf/trajectory-options-evol', methods=['POST'])
def trajectory_options_evol():
    """
    Endpoint evolutivo para obtener opciones de trayectorias calculadas con recomendaciones de palo.
    
    Este endpoint usa un algoritmo evolutivo que:
    1. Busca optimal_shots a menos de 10m de la bola
    2. Busca trayectorias en strategic_points (incluyendo el green)
    3. Evalúa y ordena las trayectorias según su riesgo
    
    Recibe en el body JSON:
    - latitude: Latitud GPS de la posición de la pelota (float) - REQUERIDO
    - longitude: Longitud GPS de la posición de la pelota (float) - REQUERIDO
    - course_id: ID del campo de golf (opcional, se identifica automáticamente desde las coordenadas si no se proporciona)
    - hole_number: Número del hoyo (opcional, se identifica automáticamente desde las coordenadas si no se proporciona)
    - user_id: ID del usuario/jugador (opcional, si se proporciona usa el perfil del jugador)
    
    Nota: course_id y hole_number deben proporcionarse juntos. Si no se proporcionan, se identifican automáticamente desde las coordenadas.
    
    Ejemplo POST:
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "course_id": 1,
        "hole_number": 1,
        "user_id": 1
    }
    
    Respuesta:
    {
        "hole_info": {...},
        "ball_position": {
            "latitude": 40.44445,
            "longitude": -3.87095,
            "terrain_type": null
        },
        "trajectory_analysis": {
            "trayectoria_optima": {...},
            "trayectoria_riesgo": {...},  // Si hay 2 o 3 trayectorias
            "trayectoria_conservadora": {...}  // Si hay 3 trayectorias
        },
        "player_info": {
            "user_id": 1,
            "has_profile": true,
            "club_count": 14
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibieron los campos requeridos
        if not data:
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude' y 'longitude'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Los campos 'latitude' y 'longitude' deben ser números válidos"}), 400
        
        # course_id y hole_number son opcionales - deben proporcionarse juntos
        course_id = None
        hole_number = None
        if 'course_id' in data or 'hole_number' in data:
            # Si se proporciona uno, se debe proporcionar el otro
            if 'course_id' not in data or 'hole_number' not in data:
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben proporcionarse juntos"
                }), 400
            try:
                course_id = int(data['course_id'])
                hole_number = int(data['hole_number'])
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Los campos 'course_id' y 'hole_number' deben ser números enteros válidos"
                }), 400
        
        # user_id es opcional
        user_id = None
        if 'user_id' in data:
            try:
                user_id = int(data['user_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'user_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para obtener información
        golf_service = get_golf_service()
        
        # 1. Obtener información del hoyo (por course_id/hole_number o identificando desde coordenadas)
        if course_id and hole_number:
            # Si se proporcionaron course_id y hole_number, usarlos directamente
            hole_info = golf_service.get_hole_by_course_and_number(course_id, hole_number)
            if not hole_info:
                return jsonify({
                    "error": f"No se encontró el hoyo número {hole_number} en el campo {course_id}"
                }), 404
            hole_id = hole_info['id']
        else:
            # Si no se proporcionaron, identificarlo desde las coordenadas
            hole_info = golf_service.identify_hole_by_ball_position(latitude, longitude)
            if not hole_info:
                return jsonify({
                    "error": "No se pudo identificar el hoyo desde las coordenadas proporcionadas. Por favor, proporciona los campos 'course_id' y 'hole_number'."
                }), 404
            hole_id = hole_info['id']
            course_id = hole_info['course_id']
            hole_number = hole_info['hole_number']
        
        # 2. Determinar tipo de terreno donde está la bola
        terrain_result = golf_service.determine_terrain_type(latitude, longitude, hole_id)
        terrain_type = terrain_result['terrain_type']
        
        # 3. Verificar que el hoyo tenga bandera antes de evaluar trayectorias
        flag_check = golf_service.golf_repository.calculate_distance_to_hole(hole_id, latitude, longitude)
        if flag_check is None:
            return jsonify({
                "error": f"El hoyo número {hole_number} del campo {course_id} no tiene una bandera (flag) definida en la base de datos",
                "details": "Para usar este endpoint, el hoyo debe tener un punto con type='flag' en la tabla hole_point.",
                "course_id": course_id,
                "hole_number": hole_number
            }), 400
        
        # 4. Obtener estadísticas del jugador si se proporcionó user_id
        player_club_statistics = None
        player_info = {
            'user_id': user_id,
            'has_profile': False,
            'club_count': 0
        }
        
        if user_id:
            try:
                player_service = get_player_service()
                player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
                
                if player_profile:
                    player_club_statistics = player_service.player_repository.get_player_club_statistics(
                        player_profile['id']
                    )
                    if player_club_statistics:
                        player_info['has_profile'] = True
                        player_info['club_count'] = len(player_club_statistics)
            except Exception as e:
                # Si hay error obteniendo el perfil, continuar sin él
                print(f"Advertencia: No se pudo obtener el perfil del jugador {user_id}: {e}")
        
        # 5. Ejecutar algoritmo evolutivo
        # PASO 1: bola_menos_10m_optimal_shot
        trayectorias_optimal = golf_service.bola_menos_10m_optimal_shot(
            latitude=latitude,
            longitude=longitude,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics
        )
        
        # PASO 2: find_strategic_shot (pasa las trayectorias encontradas en el paso 1)
        trayectorias_completas = golf_service.find_strategic_shot(
            latitude=latitude,
            longitude=longitude,
            hole_id=hole_id,
            player_club_statistics=player_club_statistics,
            trayectorias_existentes=trayectorias_optimal
        )
        
        # PASO 3: evaluacion_final
        resultado_final = golf_service.evaluacion_final(trayectorias_completas)
        
        # 6. Preparar respuesta completa
        response = {
            'hole_info': hole_info,
            'ball_position': {
                'latitude': latitude,
                'longitude': longitude,
                'terrain_type': terrain_type
            },
            'trajectory_analysis': resultado_final,
            'player_info': player_info
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al calcular opciones de trayectorias evolutivas",
            "details": str(e)
        }), 500



