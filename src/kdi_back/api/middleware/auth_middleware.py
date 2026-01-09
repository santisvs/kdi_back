# -*- coding: utf-8 -*-
"""
Middleware de autenticación para validar tokens JWT en las peticiones.
"""
from functools import wraps
from flask import request, jsonify, g
from kdi_back.api.dependencies import get_auth_service


def require_auth(f):
    """
    Decorador para requerir autenticación en un endpoint.
    
    Verifica que la petición incluya un token JWT válido en el header Authorization.
    
    Uso:
        @auth_bp.route('/protected')
        @require_auth
        def protected_endpoint():
            # g.current_user contiene el usuario autenticado
            user_id = g.current_user['id']
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                "error": "Token de autenticación requerido",
                "details": "Incluye el header 'Authorization: Bearer <token>'"
            }), 401
        
        # Extraer token (formato: "Bearer <token>")
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({
                    "error": "Formato de token inválido",
                    "details": "El header debe tener el formato 'Authorization: Bearer <token>'"
                }), 401
        except ValueError:
            return jsonify({
                "error": "Formato de token inválido",
                "details": "El header debe tener el formato 'Authorization: Bearer <token>'"
            }), 401
        
        # Verificar token
        auth_service = get_auth_service()
        user = auth_service.verify_token(token)
        
        if not user:
            return jsonify({
                "error": "Token inválido o expirado",
                "details": "El token proporcionado no es válido o ha expirado"
            }), 401
        
        # Guardar usuario en g para uso en la función
        g.current_user = user
        g.current_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function

