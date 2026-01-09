# -*- coding: utf-8 -*-
"""Main Flask application"""
from flask import Flask, jsonify
from werkzeug.exceptions import BadRequest
from kdi_back.infrastructure.config import settings
from kdi_back.infrastructure.db.database import init_database, Database
from kdi_back.api.routes import health, weather, golf, player, match, auth, game

app = Flask(__name__)

# Handler global para errores de parsing JSON
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    """Maneja errores de parsing JSON y otros errores BadRequest."""
    error_description = str(e.description) if hasattr(e, 'description') else str(e)
    
    # Detectar errores de parsing JSON
    if "Failed to decode JSON" in error_description or "Expecting property name" in error_description:
        return jsonify({
            "error": "Error al parsear el JSON",
            "details": error_description,
            "suggestion": "Asegúrate de que el JSON esté bien formateado con todas las claves entre comillas dobles. Ejemplo: {\"course_id\": 6, \"name\": \"test\"}"
        }), 400
    
    return jsonify({
        "error": "Bad Request",
        "details": error_description
    }), 400

# Register blueprints
app.register_blueprint(health.health_bp)
app.register_blueprint(weather.weather_bp)
app.register_blueprint(golf.golf_bp)
app.register_blueprint(player.player_bp)
app.register_blueprint(match.match_bp)
app.register_blueprint(auth.auth_bp)
app.register_blueprint(game.game_bp)


def create_app():
    """Factory function to create and configure the Flask app"""
    # Inicializar la base de datos (no bloquea el inicio si falla)
    print("Inicializando conexión a PostgreSQL/PostGIS...")
    try:
        if init_database():
            print("✓ Base de datos inicializada correctamente")
        else:
            print("⚠ Advertencia: No se pudo inicializar la base de datos completamente")
            print("  La aplicación continuará, pero las operaciones de BD pueden fallar")
            print("  Verifica que las variables de entorno DB_* estén configuradas correctamente")
    except Exception as e:
        print(f"⚠ Error al inicializar la base de datos: {e}")
        print("  La aplicación continuará, pero las operaciones de BD pueden fallar")
        print("  Verifica que las variables de entorno DB_* estén configuradas correctamente")
    
    return app


if __name__ == '__main__':
    # Mostrar valores de configuración cargados
    print("=" * 50)
    print("Configuración AWS cargada:")
    print("=" * 50)
    print(f"AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID}")
    secret_key_display = '*' * len(settings.AWS_SECRET_ACCESS_KEY) if settings.AWS_SECRET_ACCESS_KEY else 'No configurado'
    print(f"AWS_SECRET_ACCESS_KEY: {secret_key_display}")
    print(f"AWS_REGION: {settings.AWS_REGION}")
    print("=" * 50)
    print("Configuración PostgreSQL:")
    print("=" * 50)
    print(f"DB_HOST: {settings.DB_HOST}")
    print(f"DB_PORT: {settings.DB_PORT}")
    print(f"DB_NAME: {settings.DB_NAME}")
    print(f"DB_USER: {settings.DB_USER}")
    db_password_display = '*' * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else 'No configurado'
    print(f"DB_PASSWORD: {db_password_display}")
    print("=" * 50)
    
    # Crear y configurar la app
    app = create_app()
    
    print("=" * 50)
    print("Iniciando servidor...")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Cerrar conexiones al finalizar
        Database.close_all_connections()

