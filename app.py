# -*- coding: utf-8 -*-
from flask import Flask, jsonify
import config

app = Flask(__name__)


@app.route('/hola-mundo', methods=['GET'])
def hola_mundo():
    """
    Endpoint GET que responde 'adios mundo'
    """
    return jsonify({"mensaje": "adios mundo"}), 200


@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint de salud para verificar que el servicio está corriendo
    """
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # Mostrar valores de configuración cargados
    print("=" * 50)
    print("Configuración AWS cargada:")
    print("=" * 50)
    print(f"AWS_ACCESS_KEY_ID: {config.AWS_ACCESS_KEY_ID}")
    print(f"AWS_SECRET_ACCESS_KEY: {'*' * len(config.AWS_SECRET_ACCESS_KEY) if config.AWS_SECRET_ACCESS_KEY else 'No configurado'}")
    print(f"AWS_REGION: {config.AWS_REGION}")
    print("=" * 50)
    print("Iniciando servidor...")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

