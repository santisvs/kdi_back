# -*- coding: utf-8 -*-
"""Weather routes"""
from flask import Blueprint, jsonify, request
from kdi_back.infrastructure.agents.weather_agent import get_weather_response

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/weather', methods=['POST', 'GET'])
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

