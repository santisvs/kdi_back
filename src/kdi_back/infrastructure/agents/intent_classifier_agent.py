# -*- coding: utf-8 -*-
"""
Agente especializado para clasificar intenciones de peticiones de voz durante un partido de golf.

Este agente analiza el query en lenguaje natural y determina qué acción quiere realizar el jugador.
"""
from typing import Dict, Any
from strands import Agent
from strands.models import BedrockModel
from kdi_back.infrastructure.config import settings
import json
import re

# Define intent classifier system prompt
INTENT_CLASSIFIER_SYSTEM_PROMPT = """Eres un clasificador de intenciones para un asistente de voz de golf.
Tu función es analizar la petición del jugador y determinar qué acción quiere realizar.

IMPORTANTE: Debes responder SOLO con un JSON válido en este formato exacto:
{"intent": "nombre_intencion", "confidence": 0.0-1.0}

Tipos de intenciones disponibles:

1. **recommend_shot** - Pedir recomendación de palo/golpe
   Ejemplos: "¿Qué palo debo usar?", "¿Qué me recomiendas?", "Necesito una recomendación", 
   "¿Cómo debo jugar esta bola?", "¿Qué palo uso?", "Recomiéndame un golpe"

2. **register_stroke** - Registrar que ha dado un golpe
   Ejemplos: "He dado un golpe", "Registra mi golpe", "He golpeado la bola", 
   "Incrementa mis golpes", "Añade un golpe", "He pegado"

3. **check_distance** - Consultar distancia al hoyo
   Ejemplos: "¿A qué distancia estoy?", "¿Cuántos metros hay hasta la bandera?", 
   "Distancia al hoyo", "¿Qué distancia hay?", "¿Cuánto falta?"

4. **check_obstacles** - Consultar obstáculos en el camino
   Ejemplos: "¿Qué obstáculos hay?", "¿Hay bunkers o agua?", "Muéstrame los obstáculos",
   "¿Hay algo en el camino?", "Obstáculos"

5. **check_terrain** - Consultar tipo de terreno
   Ejemplos: "¿En qué terreno estoy?", "¿Estoy en el bunker?", "¿Estoy en el green?",
   "Tipo de terreno", "¿Dónde está la bola?"

6. **complete_hole** - Completar el hoyo actual
   Ejemplos: "He completado el hoyo", "Terminé este hoyo", "Completa el hoyo",
   "Finalizar hoyo", "He terminado"

7. **record_hole_score_direct** - Registrar resultado de un hoyo directamente con número de golpes
   Ejemplos: "Completa el hoyo con 4 golpes", "Registra 5 golpes en este hoyo",
   "Terminé con 3 golpes", "Guarda 6 golpes para este hoyo"

8. **update_hole_score** - Corregir el resultado de un hoyo específico
   Ejemplos: "Corrige el resultado del hoyo 2 con 3 golpes", "Cambia el hoyo 5 a 4 golpes",
   "Modifica el hoyo 3 con 5 golpes", "Actualiza el hoyo 1 a 2 golpes"

9. **check_ranking** - Consultar ranking del partido
   Ejemplos: "¿Cómo voy?", "¿Cuál es mi posición?", "Muéstrame el ranking",
   "¿Quién va ganando?", "Ranking", "¿Cómo estoy en el partido?"

10. **check_hole_stats** - Consultar estadísticas del hoyo actual
   Ejemplos: "¿Cuántos golpes llevo?", "¿Cuál es mi puntuación en este hoyo?",
   "Muéstrame mis golpes", "Golpes en este hoyo"

11. **check_hole_info** - Consultar información del hoyo
   Ejemplos: "¿Qué hoyo es este?", "¿Cuál es el par?", "Información del hoyo",
   "¿Qué par tiene este hoyo?"

12. **check_weather** - Consultar clima
    Ejemplos: "¿Qué tiempo hace?", "¿Hay viento?", "Condiciones meteorológicas",
    "¿Cómo está el clima?", "Tiempo"

Si la petición no encaja claramente en ninguna categoría o es ambigua, usa "recommend_shot" como fallback (es la acción más común).

Responde SIEMPRE con JSON válido, sin texto adicional antes o después.
"""

# Create a model for intent classification
model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",  # Modelo Nova Lite
    temperature=0.1  # Baja temperatura para respuestas más consistentes
)
print("📌 Usando modelo Amazon Nova Lite para clasificación de intenciones")

# Create an agent for intent classification
intent_classifier_agent = Agent(
    model=model,
    system_prompt=INTENT_CLASSIFIER_SYSTEM_PROMPT,
    tools=[],  # No necesitamos herramientas HTTP
)


def classify_intent(query: str) -> Dict[str, Any]:
    """
    Clasifica la intención de una petición en lenguaje natural.
    
    Args:
        query: Texto en lenguaje natural de la petición del jugador
        
    Returns:
        Diccionario con:
        - intent: Nombre de la intención detectada
        - confidence: Nivel de confianza (0.0-1.0)
        
    Raises:
        ValueError: Si no se puede clasificar la intención
    """
    if not query or not isinstance(query, str):
        raise ValueError("El query debe ser una cadena de texto no vacía")
    
    query = query.strip()
    if not query:
        raise ValueError("El query no puede estar vacío")
    
    # Construir el prompt
    prompt = f"""Analiza esta petición del jugador y determina su intención:

"{query}"

Responde SOLO con JSON válido en este formato:
{{"intent": "nombre_intencion", "confidence": 0.0-1.0}}
"""
    
    try:
        # Llamar al agente
        response = intent_classifier_agent(prompt)
        
        # Intentar extraer JSON de la respuesta
        # El agente puede retornar el JSON directamente o con texto adicional
        response_str = str(response).strip()
        
        # Buscar JSON en la respuesta (puede venir con texto adicional)
        json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', response_str)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Si no se encuentra, intentar parsear toda la respuesta
            json_str = response_str
        
        # Parsear JSON
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError:
            # Si falla, intentar limpiar la respuesta
            # Eliminar markdown code blocks si existen
            json_str = re.sub(r'```json\s*', '', json_str)
            json_str = re.sub(r'```\s*', '', json_str)
            json_str = json_str.strip()
            result = json.loads(json_str)
        
        # Validar estructura
        if 'intent' not in result:
            raise ValueError("La respuesta del agente no contiene 'intent'")
        
        intent = result['intent']
        confidence = result.get('confidence', 0.5)  # Default 0.5 si no viene
        
        # Validar que la intención es válida
        valid_intents = [
            'recommend_shot', 'register_stroke', 'check_distance', 'check_obstacles',
            'check_terrain', 'complete_hole', 'record_hole_score_direct', 'update_hole_score',
            'check_ranking', 'check_hole_stats', 'check_hole_info', 'check_weather'
        ]
        
        if intent not in valid_intents:
            # Si la intención no es válida, usar fallback
            print(f"Advertencia: Intención '{intent}' no es válida, usando 'recommend_shot' como fallback")
            intent = 'recommend_shot'
            confidence = 0.3
        
        # Asegurar que confidence está en rango válido
        confidence = max(0.0, min(1.0, float(confidence)))
        
        return {
            'intent': intent,
            'confidence': confidence
        }
        
    except Exception as e:
        # Si hay error, usar fallback
        print(f"Error al clasificar intención: {e}. Usando 'recommend_shot' como fallback")
        return {
            'intent': 'recommend_shot',
            'confidence': 0.3
        }



