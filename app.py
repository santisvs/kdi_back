# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
import config
from agent_weather import get_weather_response

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


@app.route('/weather', methods=['POST', 'GET'])
def weather():
    """
    Endpoint para consultar información del clima usando el agente de Bedrock
    
    Métodos soportados:
    - POST: Recibe la consulta en el body JSON con el campo 'query'
    - GET: Recibe la consulta como parámetro 'query' en la URL
    
    Ejemplo POST:
    {
        "query": "¿Qué tiempo hace en Madrid?"
    }
    
    Ejemplo GET:
    /weather?query=¿Qué tiempo hace en Madrid?
    """
    try:
        # Obtener la consulta según el método HTTP
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"error": "Se requiere el campo 'query' en el body JSON"}), 400
            query = data['query']
        else:  # GET
            query = request.args.get('query')
            if not query:
                return jsonify({"error": "Se requiere el parámetro 'query' en la URL"}), 400
        
        # Llamar al agente de clima
        response = get_weather_response(query)
        
        return jsonify({
            "query": query,
            "response": str(response)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error al procesar la consulta del clima",
            "details": str(e)
        }), 500


if __name__ == '__main__':
    # Mostrar valores de configuración cargados
    print("=" * 50)
    print("Configuración AWS cargada:")
    print("=" * 50)
    print(f"AWS_ACCESS_KEY_ID: {config.AWS_ACCESS_KEY_ID}")
    secret_key_display = '*' * len(config.AWS_SECRET_ACCESS_KEY) if config.AWS_SECRET_ACCESS_KEY else 'No configurado'
    print(f"AWS_SECRET_ACCESS_KEY: {secret_key_display}")
    print(f"AWS_REGION: {config.AWS_REGION}")
    print("=" * 50)
    print("Iniciando servidor...")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

