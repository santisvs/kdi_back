# -*- coding: utf-8 -*-
"""Main Flask application"""
from flask import Flask
from kdi_back.infrastructure.config import settings
from kdi_back.infrastructure.db.database import init_database, Database
from kdi_back.api.routes import health, weather, golf, player

app = Flask(__name__)

# Register blueprints
app.register_blueprint(health.health_bp)
app.register_blueprint(weather.weather_bp)
app.register_blueprint(golf.golf_bp)
app.register_blueprint(player.player_bp)


def create_app():
    """Factory function to create and configure the Flask app"""
    # Inicializar la base de datos
    print("Inicializando conexión a PostgreSQL/PostGIS...")
    init_database()
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

