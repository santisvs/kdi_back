# -*- coding: utf-8 -*-
"""Golf routes"""
from flask import Blueprint, jsonify, request
from kdi_back.infrastructure.agents.golf_agent import get_golf_recommendation
from kdi_back.infrastructure.agents.next_shot_agent import get_next_shot_recommendation
from kdi_back.api.dependencies import get_golf_service, get_player_service

golf_bp = Blueprint('golf', __name__)


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
    - hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
    
    Ejemplo POST (con hole_id):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1
    }
    
    Ejemplo POST (sin hole_id - identifica automáticamente):
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
        
        # hole_id es opcional
        hole_id = None
        if 'hole_id' in data:
            try:
                hole_id = int(data['hole_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'hole_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para determinar el tipo de terreno
        golf_service = get_golf_service()
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
    - hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
    
    Ejemplo POST (con hole_id):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1
    }
    
    Ejemplo POST (sin hole_id - identifica automáticamente):
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
        
        # hole_id es opcional
        hole_id = None
        if 'hole_id' in data:
            try:
                hole_id = int(data['hole_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'hole_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para calcular la distancia
        golf_service = get_golf_service()
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
    - hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
    
    Ejemplo POST (con hole_id):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1
    }
    
    Ejemplo POST (sin hole_id - identifica automáticamente):
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
        
        # hole_id es opcional
        hole_id = None
        if 'hole_id' in data:
            try:
                hole_id = int(data['hole_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'hole_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para encontrar obstáculos
        golf_service = get_golf_service()
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
    - hole_id: ID del hoyo (opcional, se identifica automáticamente si no se proporciona)
    
    Ejemplo POST (con hole_id):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1
    }
    
    Ejemplo POST (sin hole_id - identifica automáticamente):
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
        
        # hole_id es opcional
        hole_id = None
        if 'hole_id' in data:
            try:
                hole_id = int(data['hole_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'hole_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para encontrar el golpe óptimo más cercano
        golf_service = get_golf_service()
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
    - hole_id: ID del hoyo (requerido)
    - user_id: ID del usuario/jugador (opcional, si se proporciona usa el perfil del jugador)
    
    Ejemplo POST (sin perfil de jugador):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1
    }
    
    Ejemplo POST (con perfil de jugador):
    {
        "latitude": 40.44445,
        "longitude": -3.87095,
        "hole_id": 1,
        "user_id": 1
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
            return jsonify({"error": "Se requiere un body JSON con los campos 'latitude', 'longitude' y 'hole_id'"}), 400
        
        if 'latitude' not in data:
            return jsonify({"error": "Se requiere el campo 'latitude' en el body JSON"}), 400
        
        if 'longitude' not in data:
            return jsonify({"error": "Se requiere el campo 'longitude' en el body JSON"}), 400
        
        if 'hole_id' not in data:
            return jsonify({"error": "Se requiere el campo 'hole_id' en el body JSON"}), 400
        
        # Obtener y validar los valores
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            hole_id = int(data['hole_id'])
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Los campos 'latitude', 'longitude' y 'hole_id' deben ser números válidos"}), 400
        
        # user_id es opcional
        user_id = None
        if 'user_id' in data:
            try:
                user_id = int(data['user_id'])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'user_id' debe ser un número entero válido"}), 400
        
        # Usar el servicio de dominio para obtener toda la información
        golf_service = get_golf_service()
        
        # 1. Obtener información del hoyo por ID (verificar que existe)
        hole_info = golf_service.get_hole_by_id(hole_id)
        if not hole_info:
            return jsonify({
                "error": f"El hoyo {hole_id} no existe"
            }), 404
        
        # 2. Calcular distancia al hoyo
        distance_result = golf_service.calculate_distance_to_hole(latitude, longitude, hole_id)
        distance_meters = distance_result['distance_meters']
        distance_yards = distance_result['distance_yards']
        
        # 3. Determinar tipo de terreno
        terrain_result = golf_service.determine_terrain_type(latitude, longitude, hole_id)
        terrain_type = terrain_result['terrain_type']
        
        # 4. Encontrar obstáculos entre la bola y la bandera
        obstacles_result = golf_service.find_obstacles_between_ball_and_flag(latitude, longitude, hole_id)
        obstacles = obstacles_result['obstacles']
        
        # Preparar información de obstáculos para el agente (solo lo necesario)
        obstacles_for_agent = []
        for obs in obstacles:
            obstacles_for_agent.append({
                'id': obs.get('id'),
                'type': obs.get('type'),
                'name': obs.get('name')
            })
        
        # 5. Obtener estadísticas del jugador si se proporcionó user_id
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
        
        # 6. Llamar al agente con toda la información
        recommendation = get_next_shot_recommendation(
            hole_info=hole_info,
            distance_meters=distance_meters,
            distance_yards=distance_yards,
            terrain_type=terrain_type,
            obstacles=obstacles_for_agent,
            player_club_statistics=player_club_statistics
        )
        
        # Preparar respuesta con análisis completo
        response = {
            "recommendation": str(recommendation),
            "analysis": {
                "hole_info": hole_info,
                "distance_meters": distance_meters,
                "distance_yards": distance_yards,
                "terrain_type": terrain_type,
                "obstacles_count": len(obstacles),
                "obstacles": obstacles_for_agent,
                "user_id": user_id if user_id else None,
                "player_profile_used": user_id is not None and player_club_statistics is not None
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


