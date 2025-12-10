# -*- coding: utf-8 -*-
import config
from strands import Agent
from strands.models import BedrockModel

# Define a golf-focused system prompt
GOLF_SYSTEM_PROMPT = """Eres un asistente experto en golf que ayuda a los jugadores a elegir el palo correcto para cada situación.

Tu función es:
1. Analizar la posición GPS de la pelota en el campo de golf
2. Interpretar el texto en lenguaje natural que describe la situación del juego
3. Recomendar el palo de golf más apropiado para la situación
4. Indicar dónde intentar botar la bola (green, antegreen, o posición específica del campo)
5. Establecer el objetivo de distancia en metros

Consideraciones importantes:
- Distancia al hoyo
- Condiciones del terreno (hierba, arena, rough, etc.)
- Condiciones climáticas si se mencionan
- Obstáculos (bunkers, agua, árboles, etc.)
- Tipo de tiro necesario (aproximación, drive, putt, etc.)
- Estrategia de juego según la situación

Formato de respuesta OBLIGATORIO:
Debes responder SIEMPRE con una frase en español siguiendo EXACTAMENTE este formato:
"Te recomiendo utilizar [palo] intentando botar la bola en [green/antegreen/posición del campo], con el objetivo de hacer [X] metros"

Ejemplos de formato correcto:
- "Te recomiendo utilizar el hierro siete intentando botar la bola en green, con el objetivo de hacer 150 metros"
- "Te recomiendo utilizar el wedge intentando botar la bola en antegreen, con el objetivo de hacer 80 metros"
- "Te recomiendo utilizar el driver intentando botar la bola en el fairway, con el objetivo de hacer 250 metros"

Ejemplos de palos: hierro siete, hierro cinco, hierro nueve, driver, wedge, putter, etc.
Posiciones donde botar: green, antegreen, fairway, rough, o cualquier posición específica del campo que sea relevante.

Responde siempre en español de manera clara y concisa, siguiendo EXACTAMENTE el formato especificado.
"""

# Create a model for golf recommendations
model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",  # Modelo Nova Lite - NO requiere formulario
    temperature=0.3
)
print("📌 Usando modelo Amazon Nova Lite para golf")

# Create an agent for golf recommendations
golf_agent = Agent(
    model=model,
    system_prompt=GOLF_SYSTEM_PROMPT,
    tools=[],  # No necesitamos herramientas HTTP para este agente
)


def get_golf_recommendation(latitude: float, longitude: float, query: str) -> str:
    """
    Función para obtener una recomendación de palo de golf basada en GPS y consulta
    
    Args:
        latitude: Latitud GPS de la posición de la pelota
        longitude: Longitud GPS de la posición de la pelota
        query: Texto en lenguaje natural describiendo la situación
        
    Returns:
        La recomendación del agente de golf
    """
    # Construir el prompt con la información GPS y la consulta
    prompt = f"""Posición GPS de la pelota:
- Latitud: {latitude}
- Longitud: {longitude}

Situación descrita: {query}

Analiza la situación y proporciona una recomendación completa siguiendo EXACTAMENTE este formato:
"Te recomiendo utilizar [palo] intentando botar la bola en [green/antegreen/posición del campo], con el objetivo de hacer [X] metros"

Debes incluir:
1. El palo de golf recomendado
2. Dónde intentar botar la bola (green, antegreen, o posición específica del campo)
3. El objetivo de distancia en metros
"""
    
    return golf_agent(prompt)

