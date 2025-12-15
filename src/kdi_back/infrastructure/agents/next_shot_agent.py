# -*- coding: utf-8 -*-
"""
Agente especializado para recomendar el siguiente golpe basándose en información
detallada del campo de golf obtenida de la base de datos.
"""
from typing import Optional, List
from strands import Agent
from strands.models import BedrockModel

# Define a next shot system prompt
NEXT_SHOT_SYSTEM_PROMPT = """Eres un asistente experto en golf que analiza información detallada del campo y recomienda el palo correcto para el siguiente golpe.

Tu función es:
1. Analizar la información completa de la situación actual de la bola
2. Considerar la distancia exacta al hoyo
3. Evaluar el tipo de terreno donde está la bola
4. Analizar los obstáculos entre la bola y la bandera
5. Recomendar el palo de golf más apropiado para la situación
6. Indicar dónde intentar botar la bola (green, antegreen, o posición específica del campo)
7. Establecer el objetivo de distancia en metros

Información que recibirás:
- Hoyo actual: número de hoyo, par, longitud del hoyo
- Distancia al hoyo: distancia exacta en metros y yardas hasta la bandera
- Tipo de terreno: terreno normal, bunker, water, trees, rough_heavy, out_of_bounds
- Obstáculos en el camino: lista de obstáculos que hay entre la bola y la bandera

Consideraciones importantes:
- Distancia exacta al hoyo (usa esta información precisa)
- Tipo de terreno actual (afecta el tipo de golpe)
- Obstáculos en el camino (debes evitarlos o tenerlos en cuenta)
- Par del hoyo (estrategia según el par)
- Longitud del hoyo (contexto general)

Formato de respuesta OBLIGATORIO:
Debes responder SIEMPRE con una frase en español siguiendo EXACTAMENTE este formato:
"Te recomiendo utilizar [palo] intentando botar la bola en [green/antegreen/posición del campo], con el objetivo de hacer [X] metros"

Ejemplos de formato correcto:
- "Te recomiendo utilizar el hierro siete intentando botar la bola en green, con el objetivo de hacer 150 metros"
- "Te recomiendo utilizar el wedge intentando botar la bola en antegreen, con el objetivo de hacer 80 metros"
- "Te recomiendo utilizar el driver intentando botar la bola en el fairway, con el objetivo de hacer 250 metros"
- "Te recomiendo utilizar el hierro nueve intentando botar la bola en green, con el objetivo de hacer 120 metros, evitando el bunker que hay en el camino"

Ejemplos de palos: hierro siete, hierro cinco, hierro nueve, driver, wedge, putter, etc.
Posiciones donde botar: green, antegreen, fairway, rough, o cualquier posición específica del campo que sea relevante.

Responde siempre en español de manera clara y concisa, siguiendo EXACTAMENTE el formato especificado.
Si hay obstáculos en el camino, menciónalos en tu recomendación.
"""

# Create a model for next shot recommendations
model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",  # Modelo Nova Lite - NO requiere formulario
    temperature=0.3
)
print("📌 Usando modelo Amazon Nova Lite para next_shot")

# Create an agent for next shot recommendations
next_shot_agent = Agent(
    model=model,
    system_prompt=NEXT_SHOT_SYSTEM_PROMPT,
    tools=[],  # No necesitamos herramientas HTTP para este agente
)


def get_next_shot_recommendation(
    hole_info: dict,
    distance_meters: float,
    distance_yards: float,
    terrain_type: Optional[str],
    obstacles: List[dict],
    player_club_statistics: Optional[List[dict]] = None
) -> str:
    """
    Función para obtener una recomendación de palo de golf basada en información detallada del campo.
    
    Args:
        hole_info: Información del hoyo (hole_number, par, length, course_name)
        distance_meters: Distancia en metros hasta la bandera
        distance_yards: Distancia en yardas hasta la bandera
        terrain_type: Tipo de terreno (bunker, water, trees, rough_heavy, out_of_bounds, o None si es normal)
        obstacles: Lista de obstáculos entre la bola y la bandera
        player_club_statistics: Lista opcional con estadísticas de palos del jugador
        
    Returns:
        La recomendación del agente en lenguaje natural
    """
    # Construir el prompt con toda la información disponible
    prompt_parts = []
    
    # Información del hoyo
    prompt_parts.append("=== INFORMACIÓN DEL HOYO ===")
    prompt_parts.append(f"Hoyo número: {hole_info.get('hole_number', 'N/A')}")
    prompt_parts.append(f"Par: {hole_info.get('par', 'N/A')}")
    prompt_parts.append(f"Longitud del hoyo: {hole_info.get('length', 'N/A')} metros")
    if 'course_name' in hole_info:
        prompt_parts.append(f"Campo: {hole_info['course_name']}")
    
    # Distancia al hoyo
    prompt_parts.append("\n=== DISTANCIA AL HOYO ===")
    prompt_parts.append(f"Distancia exacta: {distance_meters:.2f} metros ({distance_yards:.2f} yardas)")
    
    # Tipo de terreno
    prompt_parts.append("\n=== TIPO DE TERRENO ACTUAL ===")
    if terrain_type:
        terrain_names = {
            'bunker': 'Bunker de arena',
            'water': 'Agua',
            'trees': 'Árboles',
            'rough_heavy': 'Rough pesado',
            'out_of_bounds': 'Fuera de límites'
        }
        prompt_parts.append(f"La bola está en: {terrain_names.get(terrain_type, terrain_type)}")
    else:
        prompt_parts.append("La bola está en terreno normal (fairway o green)")
    
    # Obstáculos en el camino
    prompt_parts.append("\n=== OBSTÁCULOS ENTRE LA BOLA Y LA BANDERA ===")
    if obstacles:
        obstacle_names = {
            'bunker': 'Bunker',
            'water': 'Agua',
            'trees': 'Árboles',
            'rough_heavy': 'Rough pesado',
            'out_of_bounds': 'Fuera de límites'
        }
        for i, obstacle in enumerate(obstacles, 1):
            obs_type = obstacle.get('type', 'desconocido')
            obs_name = obstacle.get('name', 'Sin nombre')
            prompt_parts.append(f"{i}. {obstacle_names.get(obs_type, obs_type)}: {obs_name}")
    else:
        prompt_parts.append("No hay obstáculos entre la bola y la bandera")
    
    # Información del perfil del jugador (si está disponible)
    if player_club_statistics:
        prompt_parts.append("\n=== PERFIL DEL JUGADOR - DISTANCIAS POR PALO ===")
        prompt_parts.append("IMPORTANTE: Debes usar estas distancias específicas del jugador para recomendar el palo correcto.")
        prompt_parts.append("La distancia objetivo es exactamente la distancia al hoyo calculada arriba.")
        prompt_parts.append("\nDistancias promedio del jugador con cada palo:")
        
        for stat in player_club_statistics:
            club_name = stat.get('club_name', 'Desconocido')
            avg_distance = stat.get('average_distance_meters', 0)
            avg_error = stat.get('average_error_meters', 0)
            shots = stat.get('shots_recorded', 0)
            
            # Formatear el nombre del palo de manera más legible
            club_display = club_name
            if stat.get('club_number'):
                club_display = f"{club_name} ({stat['club_number']})"
            
            prompt_parts.append(f"- {club_display}: {avg_distance:.0f} metros promedio (±{avg_error:.0f}m de error, {shots} golpes registrados)")
        
        prompt_parts.append("\nINSTRUCCIONES ESPECIALES:")
        prompt_parts.append("1. Elige el palo cuya distancia promedio esté más cerca de la distancia objetivo al hoyo")
        prompt_parts.append("2. Considera el error promedio del jugador con ese palo")
        prompt_parts.append("3. Si hay múltiples palos con distancias similares, elige el más preciso (menor error)")
        prompt_parts.append("4. Usa el nombre exacto del palo que aparece en la lista arriba")
    
    # Instrucciones finales
    prompt_parts.append("\n=== ANÁLISIS Y RECOMENDACIÓN ===")
    prompt_parts.append("Analiza toda esta información y proporciona una recomendación completa siguiendo EXACTAMENTE este formato:")
    prompt_parts.append('"Te recomiendo utilizar [palo] intentando botar la bola en [green/antegreen/posición del campo], con el objetivo de hacer [X] metros"')
    prompt_parts.append("\nDebes incluir:")
    prompt_parts.append("1. El palo de golf recomendado")
    prompt_parts.append("2. Dónde intentar botar la bola (green, antegreen, o posición específica del campo)")
    prompt_parts.append("3. El objetivo de distancia en metros")
    if obstacles:
        prompt_parts.append("4. Menciona los obstáculos que hay que evitar")
    
    prompt = "\n".join(prompt_parts)
    
    return next_shot_agent(prompt)

