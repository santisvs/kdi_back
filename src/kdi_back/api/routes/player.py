# -*- coding: utf-8 -*-
"""Player routes"""
from flask import Blueprint, jsonify, request, g
from kdi_back.api.dependencies import get_player_service
from kdi_back.api.middleware.auth_middleware import require_auth

player_bp = Blueprint('player', __name__)


@player_bp.route('/player', methods=['POST'])
@require_auth
def create_player():
    """
    Endpoint para crear un usuario con su perfil de jugador inicial.
    
    Recibe en el body JSON:
    - email: Email del usuario (requerido, único)
    - username: Nombre de usuario (requerido, único)
    - first_name: Nombre del usuario (opcional)
    - last_name: Apellido del usuario (opcional)
    - phone: Teléfono de contacto (opcional)
    - date_of_birth: Fecha de nacimiento en formato YYYY-MM-DD (opcional)
    - handicap: Handicap del jugador (opcional, 0-54)
    - gender: Género del jugador - male, female (opcional, requerido para inicializar estadísticas)
    - preferred_hand: Mano preferida - right, left, ambidextrous (opcional)
    - years_playing: Años de experiencia jugando golf (opcional)
    - skill_level: Nivel de habilidad - beginner, intermediate, advanced, professional (opcional, requerido para inicializar estadísticas)
    - notes: Notas adicionales sobre el jugador (opcional)
    
    Ejemplo POST:
    {
        "email": "jugador@example.com",
        "username": "jugador123",
        "first_name": "Juan",
        "last_name": "Pérez",
        "phone": "+34612345678",
        "date_of_birth": "1990-05-15",
        "handicap": 12.5,
        "gender": "male",
        "preferred_hand": "right",
        "years_playing": 5,
        "skill_level": "intermediate",
        "notes": "Jugador regular los fines de semana"
    }
    
    Respuesta exitosa (201):
    {
        "user": {
            "id": 1,
            "email": "jugador@example.com",
            "username": "jugador123",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "+34612345678",
            "date_of_birth": "1990-05-15",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        },
        "player_profile": {
            "id": 1,
            "user_id": 1,
            "handicap": 12.5,
            "preferred_hand": "right",
            "years_playing": 5,
            "skill_level": "intermediate",
            "notes": "Jugador regular los fines de semana",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar que se recibió un body JSON
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email' en el body JSON"}), 400
        
        if 'username' not in data:
            return jsonify({"error": "Se requiere el campo 'username' en el body JSON"}), 400
        
        # Obtener valores del body
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        date_of_birth = data.get('date_of_birth')
        handicap = data.get('handicap')
        gender = data.get('gender')
        preferred_hand = data.get('preferred_hand')
        years_playing = data.get('years_playing')
        skill_level = data.get('skill_level')
        notes = data.get('notes')
        
        # Convertir handicap a float si se proporciona
        if handicap is not None:
            try:
                handicap = float(handicap)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'handicap' debe ser un número"}), 400
        
        # Convertir years_playing a int si se proporciona
        if years_playing is not None:
            try:
                years_playing = int(years_playing)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'years_playing' debe ser un número entero"}), 400
        
        # Obtener el servicio de jugadores
        player_service = get_player_service()
        
        # Crear el usuario con su perfil
        result = player_service.create_user_with_profile(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth,
            handicap=handicap,
            gender=gender,
            preferred_hand=preferred_hand,
            years_playing=years_playing,
            skill_level=skill_level,
            notes=notes
        )
        
        # Convertir fechas a strings para JSON
        def format_datetime(value):
            if value is None:
                return None
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        # Formatear respuesta
        user = result['user']
        player_profile = result['player_profile']
        
        response = {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
                "phone": user.get('phone'),
                "date_of_birth": str(user.get('date_of_birth')) if user.get('date_of_birth') else None,
                "created_at": format_datetime(user.get('created_at')),
                "updated_at": format_datetime(user.get('updated_at'))
            },
            "player_profile": {
                "id": player_profile['id'],
                "user_id": player_profile['user_id'],
                "handicap": float(player_profile['handicap']) if player_profile.get('handicap') else None,
                "gender": player_profile.get('gender'),
                "preferred_hand": player_profile.get('preferred_hand'),
                "years_playing": player_profile.get('years_playing'),
                "skill_level": player_profile.get('skill_level'),
                "notes": player_profile.get('notes'),
                "created_at": format_datetime(player_profile.get('created_at')),
                "updated_at": format_datetime(player_profile.get('updated_at'))
            }
        }
        
        return jsonify(response), 201
        
    except ValueError as e:
        # Errores de validación de negocio
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al crear el usuario y perfil de jugador",
            "details": str(e)
        }), 500


@player_bp.route('/player/profile', methods=['GET'])
@require_auth
def get_player_profile():
    """
    Endpoint para obtener el perfil de jugador del usuario autenticado.
    
    Respuesta exitosa (200):
    {
        "player_profile": {
            "id": 1,
            "user_id": 1,
            "handicap": 12.5,
            "gender": "male",
            "preferred_hand": "right",
            "years_playing": 5,
            "skill_level": "intermediate",
            "notes": "Jugador regular los fines de semana",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        }
    }
    
    Respuesta si no existe perfil (404):
    {
        "error": "Perfil de jugador no encontrado"
    }
    """
    try:
        # Obtener el usuario autenticado desde g (establecido por require_auth)
        user_id = g.current_user['id']
        
        # Obtener el servicio de jugadores
        player_service = get_player_service()
        
        # Obtener el perfil de jugador
        player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
        
        if not player_profile:
            return jsonify({"error": "Perfil de jugador no encontrado"}), 404
        
        # Convertir fechas a strings para JSON
        def format_datetime(value):
            if value is None:
                return None
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        response = {
            "player_profile": {
                "id": player_profile['id'],
                "user_id": player_profile['user_id'],
                "handicap": float(player_profile['handicap']) if player_profile.get('handicap') else None,
                "gender": player_profile.get('gender'),
                "preferred_hand": player_profile.get('preferred_hand'),
                "years_playing": player_profile.get('years_playing'),
                "skill_level": player_profile.get('skill_level'),
                "notes": player_profile.get('notes'),
                "created_at": format_datetime(player_profile.get('created_at')),
                "updated_at": format_datetime(player_profile.get('updated_at'))
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener el perfil de jugador",
            "details": str(e)
        }), 500


@player_bp.route('/player/club-statistics', methods=['GET'])
@require_auth
def get_player_club_statistics():
    """
    Endpoint para obtener las estadísticas de palos del usuario autenticado.
    
    Respuesta exitosa (200):
    {
        "club_statistics": [
            {
                "id": 1,
                "player_profile_id": 1,
                "golf_club_id": 5,
                "club_name": "Driver",
                "club_type": "wood",
                "club_number": null,
                "average_distance_meters": 220.5,
                "min_distance_meters": 200.0,
                "max_distance_meters": 240.0,
                "average_error_meters": 15.2,
                "error_std_deviation": 5.5,
                "shots_recorded": 50
            },
            ...
        ]
    }
    
    Respuesta si no existe perfil o estadísticas (404):
    {
        "error": "Perfil de jugador no encontrado o sin estadísticas"
    }
    """
    try:
        # Obtener el usuario autenticado desde g (establecido por require_auth)
        user_id = g.current_user['id']
        
        # Obtener el servicio de jugadores
        player_service = get_player_service()
        
        # Obtener el perfil de jugador
        player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
        
        if not player_profile:
            return jsonify({"error": "Perfil de jugador no encontrado o sin estadísticas"}), 404
        
        # Obtener las estadísticas de palos
        club_statistics = player_service.player_repository.get_player_club_statistics(
            player_profile['id']
        )
        
        if not club_statistics:
            return jsonify({
                "error": "Perfil de jugador no encontrado o sin estadísticas",
                "club_statistics": []
            }), 404
        
        response = {
            "club_statistics": club_statistics
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener las estadísticas de palos",
            "details": str(e)
        }), 500


@player_bp.route('/player/user', methods=['PUT'])
@require_auth
def update_user_data():
    """
    Endpoint para actualizar los datos del usuario autenticado.
    
    Recibe en el body JSON (todos los campos son opcionales):
    - email: Nuevo email del usuario
    - username: Nuevo nombre de usuario
    - first_name: Nuevo nombre
    - last_name: Nuevo apellido
    - phone: Nuevo teléfono
    - date_of_birth: Nueva fecha de nacimiento (formato YYYY-MM-DD)
    
    Ejemplo PUT:
    {
        "first_name": "Juan",
        "last_name": "Pérez",
        "phone": "+34612345678"
    }
    
    Respuesta exitosa (200):
    {
        "user": {
            "id": 1,
            "email": "jugador@example.com",
            "username": "jugador123",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "+34612345678",
            "date_of_birth": "1990-05-15",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T11:00:00"
        }
    }
    """
    try:
        # Obtener el usuario autenticado desde g (establecido por require_auth)
        user_id = g.current_user['id']
        
        data = request.get_json()
        
        # Validar que se recibió un body JSON
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Obtener valores del body (todos opcionales)
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        date_of_birth = data.get('date_of_birth')
        
        # Obtener el servicio de jugadores
        player_service = get_player_service()
        
        # Actualizar los datos del usuario
        user = player_service.update_user_data(
            user_id=user_id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth
        )
        
        # Convertir fechas a strings para JSON
        def format_datetime(value):
            if value is None:
                return None
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        response = {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
                "phone": user.get('phone'),
                "date_of_birth": str(user.get('date_of_birth')) if user.get('date_of_birth') else None,
                "created_at": format_datetime(user.get('created_at')),
                "updated_at": format_datetime(user.get('updated_at'))
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # Errores de validación de negocio
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al actualizar los datos del usuario",
            "details": str(e)
        }), 500


@player_bp.route('/player/profile', methods=['PUT'])
@require_auth
def update_player_profile():
    """
    Endpoint para actualizar el perfil de jugador del usuario autenticado.
    
    Recibe en el body JSON (todos los campos son opcionales):
    - handicap: Handicap del jugador (0-54)
    - gender: Género del jugador - male, female
    - preferred_hand: Mano preferida - right, left, ambidextrous
    - years_playing: Años de experiencia jugando golf
    - skill_level: Nivel de habilidad - beginner, intermediate, advanced, professional
    - notes: Notas adicionales sobre el jugador
    
    Ejemplo PUT:
    {
        "handicap": 15.5,
        "skill_level": "intermediate",
        "years_playing": 6
    }
    
    Respuesta exitosa (200):
    {
        "player_profile": {
            "id": 1,
            "user_id": 1,
            "handicap": 15.5,
            "gender": "male",
            "preferred_hand": "right",
            "years_playing": 6,
            "skill_level": "intermediate",
            "notes": "Jugador regular los fines de semana",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T11:00:00"
        }
    }
    
    Respuesta si no existe perfil (404):
    {
        "error": "Perfil de jugador no encontrado"
    }
    """
    try:
        # Obtener el usuario autenticado desde g (establecido por require_auth)
        user_id = g.current_user['id']
        
        data = request.get_json()
        
        # Validar que se recibió un body JSON
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Obtener valores del body (todos opcionales)
        handicap = data.get('handicap')
        gender = data.get('gender')
        preferred_hand = data.get('preferred_hand')
        years_playing = data.get('years_playing')
        skill_level = data.get('skill_level')
        notes = data.get('notes')
        
        # Convertir handicap a float si se proporciona
        if handicap is not None:
            try:
                handicap = float(handicap)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'handicap' debe ser un número"}), 400
        
        # Convertir years_playing a int si se proporciona
        if years_playing is not None:
            try:
                years_playing = int(years_playing)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'years_playing' debe ser un número entero"}), 400
        
        # Obtener el servicio de jugadores
        player_service = get_player_service()
        
        # Actualizar el perfil de jugador
        player_profile = player_service.update_player_profile(
            user_id=user_id,
            handicap=handicap,
            gender=gender,
            preferred_hand=preferred_hand,
            years_playing=years_playing,
            skill_level=skill_level,
            notes=notes
        )
        
        # Convertir fechas a strings para JSON
        def format_datetime(value):
            if value is None:
                return None
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        response = {
            "player_profile": {
                "id": player_profile['id'],
                "user_id": player_profile['user_id'],
                "handicap": float(player_profile['handicap']) if player_profile.get('handicap') else None,
                "gender": player_profile.get('gender'),
                "preferred_hand": player_profile.get('preferred_hand'),
                "years_playing": player_profile.get('years_playing'),
                "skill_level": player_profile.get('skill_level'),
                "notes": player_profile.get('notes'),
                "created_at": format_datetime(player_profile.get('created_at')),
                "updated_at": format_datetime(player_profile.get('updated_at'))
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # Errores de validación de negocio
        error_message = str(e)
        if "no tiene un perfil" in error_message.lower():
            return jsonify({
                "error": "Perfil de jugador no encontrado",
                "details": error_message
            }), 404
        return jsonify({
            "error": "Error de validación",
            "details": error_message
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al actualizar el perfil de jugador",
            "details": str(e)
        }), 500


@player_bp.route('/player/clubs', methods=['POST'])
@require_auth
def create_player_club():
    """
    Endpoint para crear un nuevo palo personalizado para el usuario autenticado.
    
    Recibe en el body JSON:
    - club_name: Nombre del palo (requerido)
    - club_type: Tipo del palo - driver, wood, hybrid, iron, wedge, putter (opcional)
    - average_distance_meters: Distancia promedio en metros (opcional)
    - min_distance_meters: Distancia mínima en metros (opcional)
    - max_distance_meters: Distancia máxima en metros (opcional)
    - average_error_meters: Error promedio en metros (opcional)
    
    Ejemplo POST:
    {
        "club_name": "Hierro 7",
        "club_type": "iron",
        "average_distance_meters": 150.0,
        "min_distance_meters": 140.0,
        "max_distance_meters": 160.0,
        "average_error_meters": 10.0
    }
    
    Respuesta exitosa (201):
    {
        "club": {
            "id": 1,
            "player_profile_id": 1,
            "golf_club_id": 5,
            "club_name": "Hierro 7",
            "club_type": "iron",
            "average_distance_meters": 150.0,
            "min_distance_meters": 140.0,
            "max_distance_meters": 160.0,
            "average_error_meters": 10.0,
            "shots_recorded": 0
        }
    }
    """
    try:
        user_id = g.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        if 'club_name' not in data or not data['club_name']:
            return jsonify({"error": "Se requiere el campo 'club_name'"}), 400
        
        club_name = data.get('club_name')
        club_type = data.get('club_type')
        average_distance_meters = data.get('average_distance_meters')
        min_distance_meters = data.get('min_distance_meters')
        max_distance_meters = data.get('max_distance_meters')
        average_error_meters = data.get('average_error_meters')
        
        # Convertir a float si se proporcionan
        if average_distance_meters is not None:
            try:
                average_distance_meters = float(average_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'average_distance_meters' debe ser un número"}), 400
        
        if min_distance_meters is not None:
            try:
                min_distance_meters = float(min_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'min_distance_meters' debe ser un número"}), 400
        
        if max_distance_meters is not None:
            try:
                max_distance_meters = float(max_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'max_distance_meters' debe ser un número"}), 400
        
        if average_error_meters is not None:
            try:
                average_error_meters = float(average_error_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'average_error_meters' debe ser un número"}), 400
        
        player_service = get_player_service()
        
        club = player_service.create_player_club(
            user_id=user_id,
            club_name=club_name,
            club_type=club_type,
            average_distance_meters=average_distance_meters,
            min_distance_meters=min_distance_meters,
            max_distance_meters=max_distance_meters,
            average_error_meters=average_error_meters
        )
        
        response = {"club": club}
        return jsonify(response), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al crear el palo",
            "details": str(e)
        }), 500


@player_bp.route('/player/clubs', methods=['GET'])
@require_auth
def get_player_clubs():
    """
    Endpoint para obtener todos los palos del usuario autenticado.
    
    Respuesta exitosa (200):
    {
        "clubs": [
            {
                "id": 1,
                "player_profile_id": 1,
                "golf_club_id": 5,
                "club_name": "Hierro 7",
                "club_type": "iron",
                "average_distance_meters": 150.0,
                "min_distance_meters": 140.0,
                "max_distance_meters": 160.0,
                "average_error_meters": 10.0,
                "shots_recorded": 50
            },
            ...
        ]
    }
    """
    try:
        user_id = g.current_user['id']
        player_service = get_player_service()
        
        player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
        if not player_profile:
            return jsonify({"error": "Perfil de jugador no encontrado"}), 404
        
        clubs = player_service.player_repository.get_player_club_statistics(player_profile['id'])
        
        response = {"clubs": clubs}
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener los palos",
            "details": str(e)
        }), 500


@player_bp.route('/player/clubs/<int:club_id>', methods=['PUT'])
@require_auth
def update_player_club(club_id: int):
    """
    Endpoint para actualizar un palo del usuario autenticado.
    
    Recibe en el body JSON (todos los campos son opcionales):
    - club_name: Nuevo nombre del palo
    - club_type: Nuevo tipo del palo
    - average_distance_meters: Nueva distancia promedio
    - min_distance_meters: Nueva distancia mínima
    - max_distance_meters: Nueva distancia máxima
    - average_error_meters: Nuevo error promedio
    
    Respuesta exitosa (200):
    {
        "club": {
            "id": 1,
            "club_name": "Hierro 7",
            "average_distance_meters": 155.0,
            ...
        }
    }
    """
    try:
        user_id = g.current_user['id']
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        club_name = data.get('club_name')
        club_type = data.get('club_type')
        average_distance_meters = data.get('average_distance_meters')
        min_distance_meters = data.get('min_distance_meters')
        max_distance_meters = data.get('max_distance_meters')
        average_error_meters = data.get('average_error_meters')
        
        # Convertir a float si se proporcionan
        if average_distance_meters is not None:
            try:
                average_distance_meters = float(average_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'average_distance_meters' debe ser un número"}), 400
        
        if min_distance_meters is not None:
            try:
                min_distance_meters = float(min_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'min_distance_meters' debe ser un número"}), 400
        
        if max_distance_meters is not None:
            try:
                max_distance_meters = float(max_distance_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'max_distance_meters' debe ser un número"}), 400
        
        if average_error_meters is not None:
            try:
                average_error_meters = float(average_error_meters)
            except (ValueError, TypeError):
                return jsonify({"error": "El campo 'average_error_meters' debe ser un número"}), 400
        
        player_service = get_player_service()
        
        club = player_service.update_player_club(
            user_id=user_id,
            club_statistics_id=club_id,
            club_name=club_name,
            club_type=club_type,
            average_distance_meters=average_distance_meters,
            min_distance_meters=min_distance_meters,
            max_distance_meters=max_distance_meters,
            average_error_meters=average_error_meters
        )
        
        response = {"club": club}
        return jsonify(response), 200
        
    except ValueError as e:
        error_message = str(e)
        if "no se encontró" in error_message.lower():
            return jsonify({
                "error": "Palo no encontrado",
                "details": error_message
            }), 404
        return jsonify({
            "error": "Error de validación",
            "details": error_message
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al actualizar el palo",
            "details": str(e)
        }), 500


@player_bp.route('/player/clubs/<int:club_id>', methods=['DELETE'])
@require_auth
def delete_player_club(club_id: int):
    """
    Endpoint para eliminar un palo del usuario autenticado.
    
    Respuesta exitosa (200):
    {
        "message": "Palo eliminado correctamente"
    }
    """
    try:
        user_id = g.current_user['id']
        player_service = get_player_service()
        
        player_service.delete_player_club(user_id=user_id, club_statistics_id=club_id)
        
        return jsonify({"message": "Palo eliminado correctamente"}), 200
        
    except ValueError as e:
        error_message = str(e)
        if "no se encontró" in error_message.lower():
            return jsonify({
                "error": "Palo no encontrado",
                "details": error_message
            }), 404
        return jsonify({
            "error": "Error de validación",
            "details": error_message
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Error al eliminar el palo",
            "details": str(e)
        }), 500

