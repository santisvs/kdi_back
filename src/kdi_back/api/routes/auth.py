# -*- coding: utf-8 -*-
"""Auth routes"""
from flask import Blueprint, jsonify, request, g
from kdi_back.api.dependencies import get_auth_service
from kdi_back.api.middleware.auth_middleware import require_auth

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Endpoint para registrar un nuevo usuario.
    
    Recibe en el body JSON:
    - email: Email del usuario (requerido)
    - username: Nombre de usuario (requerido)
    - password: Contraseña (requerido, mínimo 6 caracteres)
    - first_name: Nombre del usuario (opcional)
    - last_name: Apellido del usuario (opcional)
    
    Ejemplo POST:
    {
        "email": "usuario@example.com",
        "username": "usuario123",
        "password": "contraseña123",
        "first_name": "Juan",
        "last_name": "Pérez"
    }
    
    Respuesta exitosa (201):
    {
        "user": {
            "id": 1,
            "email": "usuario@example.com",
            "username": "usuario123",
            "first_name": "Juan",
            "last_name": "Pérez"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email'"}), 400
        
        if 'username' not in data:
            return jsonify({"error": "Se requiere el campo 'username'"}), 400
        
        if 'password' not in data:
            return jsonify({"error": "Se requiere el campo 'password'"}), 400
        
        # Obtener valores
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Registrar usuario
        result = auth_service.register_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return jsonify(result), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al registrar el usuario",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Endpoint para iniciar sesión.
    
    Recibe en el body JSON:
    - email: Email del usuario (requerido)
    - password: Contraseña (requerido)
    
    Ejemplo POST:
    {
        "email": "usuario@example.com",
        "password": "contraseña123"
    }
    
    Respuesta exitosa (200):
    {
        "user": {
            "id": 1,
            "email": "usuario@example.com",
            "username": "usuario123",
            "first_name": "Juan",
            "last_name": "Pérez"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email'"}), 400
        
        if 'password' not in data:
            return jsonify({"error": "Se requiere el campo 'password'"}), 400
        
        # Obtener valores
        email = data.get('email')
        password = data.get('password')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Autenticar usuario
        result = auth_service.login_user(email=email, password=password)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de autenticación",
            "details": str(e)
        }), 401
        
    except Exception as e:
        return jsonify({
            "error": "Error al iniciar sesión",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Endpoint para solicitar recuperación de contraseña.
    
    Recibe en el body JSON:
    - email: Email del usuario (requerido)
    
    Ejemplo POST:
    {
        "email": "usuario@example.com"
    }
    
    Respuesta exitosa (200):
    {
        "message": "Si el email existe, se enviará un correo con instrucciones."
    }
    
    Nota: En producción, se enviaría un email con el token de recuperación.
    En desarrollo, el token se retorna en la respuesta (NO hacer esto en producción).
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email'"}), 400
        
        # Obtener valores
        email = data.get('email')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Solicitar reset de contraseña
        message = auth_service.request_password_reset(email)
        
        # En desarrollo, retornar el token (NO hacer esto en producción)
        # En producción, solo retornar el mensaje genérico
        return jsonify({
            "message": message,
            "note": "En producción, el token se enviaría por email. En desarrollo, se retorna aquí."
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al procesar la solicitud",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Endpoint para restablecer la contraseña usando un token de recuperación.
    
    Recibe en el body JSON:
    - token: Token de recuperación de contraseña (requerido)
    - new_password: Nueva contraseña (requerido, mínimo 6 caracteres)
    
    Ejemplo POST:
    {
        "token": "token_de_recuperacion",
        "new_password": "nueva_contraseña123"
    }
    
    Respuesta exitosa (200):
    {
        "message": "Contraseña restablecida exitosamente"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'token' not in data:
            return jsonify({"error": "Se requiere el campo 'token'"}), 400
        
        if 'new_password' not in data:
            return jsonify({"error": "Se requiere el campo 'new_password'"}), 400
        
        # Obtener valores
        token = data.get('token')
        new_password = data.get('new_password')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Restablecer contraseña
        auth_service.reset_password(token=token, new_password=new_password)
        
        return jsonify({
            "message": "Contraseña restablecida exitosamente"
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al restablecer la contraseña",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/oauth/google', methods=['POST'])
def oauth_google():
    """
    Endpoint para autenticación/registro con Google OAuth.
    
    Recibe en el body JSON:
    - oauth_id: ID del usuario en Google (requerido)
    - email: Email del usuario (requerido)
    - username: Nombre de usuario (opcional)
    - first_name: Nombre del usuario (opcional)
    - last_name: Apellido del usuario (opcional)
    
    Ejemplo POST:
    {
        "oauth_id": "123456789",
        "email": "usuario@gmail.com",
        "username": "usuario123",
        "first_name": "Juan",
        "last_name": "Pérez"
    }
    
    Respuesta exitosa (200 o 201):
    {
        "user": {
            "id": 1,
            "email": "usuario@gmail.com",
            "username": "usuario123",
            "first_name": "Juan",
            "last_name": "Pérez"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'oauth_id' not in data:
            return jsonify({"error": "Se requiere el campo 'oauth_id'"}), 400
        
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email'"}), 400
        
        # Obtener valores
        oauth_id = data.get('oauth_id')
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Registrar/autenticar usuario OAuth
        result = auth_service.register_oauth_user(
            provider='google',
            oauth_id=oauth_id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        # Determinar código de estado (201 si es nuevo, 200 si ya existía)
        status_code = 201  # Por defecto, asumimos que es nuevo
        
        return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al autenticar con Google",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/oauth/instagram', methods=['POST'])
def oauth_instagram():
    """
    Endpoint para autenticación/registro con Instagram OAuth.
    
    Recibe en el body JSON:
    - oauth_id: ID del usuario en Instagram (requerido)
    - email: Email del usuario (requerido)
    - username: Nombre de usuario (opcional)
    - first_name: Nombre del usuario (opcional)
    - last_name: Apellido del usuario (opcional)
    
    Ejemplo POST:
    {
        "oauth_id": "123456789",
        "email": "usuario@example.com",
        "username": "usuario123",
        "first_name": "Juan",
        "last_name": "Pérez"
    }
    
    Respuesta exitosa (200 o 201):
    {
        "user": {
            "id": 1,
            "email": "usuario@example.com",
            "username": "usuario123",
            "first_name": "Juan",
            "last_name": "Pérez"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400
        
        # Validar campos requeridos
        if 'oauth_id' not in data:
            return jsonify({"error": "Se requiere el campo 'oauth_id'"}), 400
        
        if 'email' not in data:
            return jsonify({"error": "Se requiere el campo 'email'"}), 400
        
        # Obtener valores
        oauth_id = data.get('oauth_id')
        email = data.get('email')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Registrar/autenticar usuario OAuth
        result = auth_service.register_oauth_user(
            provider='instagram',
            oauth_id=oauth_id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        # Determinar código de estado (201 si es nuevo, 200 si ya existía)
        status_code = 201  # Por defecto, asumimos que es nuevo
        
        return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al autenticar con Instagram",
            "details": str(e)
        }), 500


@auth_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Endpoint para cerrar sesión invalidando el token del usuario.
    
    Requiere autenticación (token JWT en el header Authorization).
    
    Header requerido:
    - Authorization: Bearer <token>
    
    Respuesta exitosa (200):
    {
        "message": "Sesión cerrada exitosamente"
    }
    """
    try:
        # Obtener el token del contexto (g.current_token se establece en require_auth)
        token = g.current_token
        
        # Obtener el servicio de autenticación
        auth_service = get_auth_service()
        
        # Cerrar sesión (revocar token)
        auth_service.logout_user(token)
        
        return jsonify({
            "message": "Sesión cerrada exitosamente"
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Error de validación",
            "details": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": "Error al cerrar sesión",
            "details": str(e)
        }), 500
