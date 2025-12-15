# -*- coding: utf-8 -*-
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel

# Define a weather-focused system prompt
WEATHER_SYSTEM_PROMPT = """Eres un asistente del clima con capacidades HTTP. Puedes:

1. Realizar peticiones HTTP a APIs meteorológicas globales
2. Procesar y mostrar datos del pronóstico del tiempo
3. Proporcionar información meteorológica para cualquier ubicación del mundo

Al recuperar información del clima:
1. Primero obtén las coordenadas o información de la cuadrícula usando https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true
2. Luego usa la URL del pronóstico devuelta para obtener el pronóstico real

Al mostrar respuestas:
- Da formato a los datos meteorológicos de manera legible
- Destaca información importante como temperatura, precipitación y alertas
- Maneja los errores apropiadamente
- Convierte términos técnicos a un lenguaje comprensible
- Responde en español

Siempre explica las condiciones meteorológicas claramente y proporciona contexto para el pronóstico.
"""

# Create a model for European regions (Spain)
# IMPORTANTE: Los modelos de Anthropic requieren formulario de uso de caso en AWS
# El modelo que realmente funciona sin formulario es us.amazon.nova-lite-v1:0
# Pero este solo funciona en regiones US
# Por ahora, usamos us-east-1 con us.amazon.nova-lite-v1:0 que NO requiere formulario

model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",  # Modelo Nova Lite - NO requiere formulario
    temperature=0.3
)
print("📌 Usando modelo Amazon Nova Lite")

# Create an agent with HTTP capabilities
weather_agent = Agent(
    model=model,
    system_prompt=WEATHER_SYSTEM_PROMPT,
    tools=[http_request],  # Explicitly enable http_request tool
)


def get_weather_response(query: str) -> str:
    """
    Función para obtener una respuesta del agente de clima
    
    Args:
        query: La consulta sobre el clima
        
    Returns:
        La respuesta del agente de clima
    """
    return weather_agent(query)

