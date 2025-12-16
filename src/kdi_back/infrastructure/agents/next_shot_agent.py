# -*- coding: utf-8 -*-
"""
Agente especializado para recomendar el siguiente golpe basándose en información
detallada del campo de golf obtenida de la base de datos.
"""
from typing import Optional, List
from strands import Agent
from strands.models import BedrockModel
from kdi_back.infrastructure.agents.knowledge_base_helper import (
    query_knowledge_base,
    format_knowledge_base_results
)

# Define a next shot system prompt
NEXT_SHOT_SYSTEM_PROMPT = """Eres un asistente experto en golf que analiza información detallada del campo y recomienda el palo correcto y el tipo de golpe para el siguiente golpe.

Tu función es:
1. Analizar la información completa de la situación actual de la bola
2. Considerar la distancia exacta al hoyo
3. Evaluar el tipo de terreno donde está la bola
4. Analizar los obstáculos entre la bola y la bandera
5. Considerar la situación de la bola y lo que ve el jugador (si está disponible)
6. Usar la información de la base de conocimiento para recomendar el TIPO DE GOLPE específico (flop shot, pitch, chip, punch, etc.)
7. Recomendar el palo de golf MÁS CERCANO a la distancia objetivo
8. Indicar el tipo de swing (completo, 3/4, 1/2) según la distancia exacta necesaria
9. Recomendar la distancia objetivo correcta considerando la distancia al hoyo

Información que recibirás:
- Hoyo actual: número de hoyo, par, longitud del hoyo
- Distancia al hoyo: distancia exacta en metros y yardas hasta la bandera
- Tipo de terreno: terreno normal, bunker, water, trees, rough_heavy, out_of_bounds
- Obstáculos en el camino: lista de obstáculos que hay entre la bola y la bandera
- Situación de la bola y visión del jugador: descripción opcional de la posición de la bola y lo que observa el jugador
- Base de conocimiento: información relevante sobre técnicas de golf, estrategias y consejos

REGLAS CRÍTICAS para selección de palo y distancia:
1. SELECCIÓN DE PALO: Elige el palo cuya distancia promedio esté MÁS CERCA de la distancia al hoyo
   - Si la distancia al hoyo es 88m y tienes palos de 80m, 95m, 110m → elige 95m (Gap Wedge)
   - Busca el palo que minimice la diferencia con la distancia objetivo

2. DISTANCIA OBJETIVO RECOMENDADA:
   - Si la distancia promedio del palo < distancia al hoyo → recomienda la distancia promedio del palo
   - Si la distancia promedio del palo >= distancia al hoyo → recomienda como máximo la distancia al hoyo
   - Ejemplo: Hoyo a 88m, Gap Wedge 95m → recomendar "hacer 88 metros" (no 95)
   - Ejemplo: Hoyo a 120m, Gap Wedge 95m → recomendar "hacer 95 metros"

3. TIPO DE GOLPE (usar base de conocimiento):
   - Flop shot: para elevar rápidamente sobre obstáculos cercanos (árboles, bunkers)
   - Pitch: golpe elevado de distancia media
   - Chip: golpe bajo alrededor del green
   - Punch: golpe bajo para pasar bajo viento o ramas
   - Drive: golpe de salida con máxima distancia
   - Considera viento, obstáculos y lie de la bola

4. TIPO DE SWING:
   - Swing completo: cuando la distancia al hoyo = distancia promedio del palo
   - Swing 3/4: cuando necesitas menos distancia que el promedio del palo
   - Swing 1/2: cuando necesitas bastante menos distancia

Formato de respuesta OBLIGATORIO:
"Estás a [X] metros del hoyo, te recomiendo utilizar [palo] con [tipo de swing] intentando hacer un [tipo de golpe] para [estrategia específica]. [Consideraciones adicionales sobre obstáculos, viento, etc.]"

Ejemplos de formato correcto:
- "Estás a 88 metros del hoyo, te recomiendo utilizar un Pitching Wedge con swing completo intentando hacer un flop shot para pasar los árboles por encima y que no ruede la bola en el green. Además, con el viento en contra también te frenará la bola"
- "Estás a 150 metros del hoyo, te recomiendo utilizar un Hierro 7 con swing completo intentando hacer un approach directo al green. Ten en cuenta el bunker a la derecha"
- "Estás a 95 metros del hoyo, te recomiendo utilizar un Gap Wedge con swing completo para alcanzar el green. Considera el viento cruzado que puede desviar la bola"

Tipos de golpe comunes:
- Flop shot: elevado y con mucho spin, para pasar obstáculos y parar rápido
- Pitch: elevado de distancia media, aterriza suave
- Chip: bajo y rodado, alrededor del green
- Punch: bajo y penetrante, contra el viento o bajo ramas
- Draw/Fade: para sortear obstáculos laterales
- Bump and run: bajo y rodado hacia el green

OBLIGATORIO:
1. Menciona la distancia exacta al hoyo al inicio
2. Recomienda el palo cuya distancia promedio esté MÁS CERCA de la distancia al hoyo
3. Usa la distancia correcta (máximo la distancia al hoyo si el palo es más largo)
4. Especifica el TIPO DE GOLPE según la base de conocimiento y la situación
5. Menciona obstáculos y condiciones climáticas relevantes

Responde siempre en español de manera conversacional, clara y específica.
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
    player_club_statistics: Optional[List[dict]] = None,
    ball_situation_description: Optional[str] = None
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
        ball_situation_description: Descripción opcional de la situación de la bola y lo que ve el jugador
        
    Returns:
        La recomendación del agente en lenguaje natural
    """
    # Construir query para la Knowledge Base basada en la información disponible
    kb_query_parts = []
    
    # Query más específica para obtener información sobre tipos de golpe
    kb_query_parts.append(f"tipo de golpe técnica para {distance_meters:.0f} metros")
    
    if terrain_type:
        terrain_names = {
            'bunker': 'desde bunker',
            'water': 'cerca del agua',
            'trees': 'con árboles',
            'rough_heavy': 'desde rough pesado',
            'out_of_bounds': 'cerca de límites'
        }
        kb_query_parts.append(terrain_names.get(terrain_type, terrain_type))
    
    # Agregar información sobre obstáculos para obtener técnicas específicas
    if obstacles:
        obstacle_types = set([obs.get('type', '') for obs in obstacles if obs.get('type')])
        if 'trees' in obstacle_types:
            kb_query_parts.append("flop shot pasar árboles por encima")
        if 'bunker' in obstacle_types:
            kb_query_parts.append("evitar bunker estrategia")
        if 'water' in obstacle_types:
            kb_query_parts.append("evitar agua golpe seguro")
    
    # Información sobre situación de la bola para obtener técnicas específicas
    if ball_situation_description:
        # Agregar palabras clave relacionadas con tipos de golpe
        situation_lower = ball_situation_description.lower()
        if 'viento' in situation_lower:
            kb_query_parts.append("golpe con viento")
        if 'elevado' in situation_lower or 'arriba' in situation_lower:
            kb_query_parts.append("golpe desde posición elevada")
        if 'abajo' in situation_lower or 'bajo' in situation_lower:
            kb_query_parts.append("golpe desde posición baja")
        
        kb_query_parts.append(ball_situation_description[:100])  # Primeros 100 caracteres
    
    # Consultar Knowledge Base
    kb_query = " ".join(kb_query_parts)
    kb_results = query_knowledge_base(kb_query, max_results=5)
    kb_formatted = format_knowledge_base_results(kb_results)
    
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
    
    # Situación de la bola y lo que ve el jugador (si está disponible)
    if ball_situation_description:
        prompt_parts.append("\n=== SITUACIÓN DE LA BOLA Y VISIÓN DEL JUGADOR ===")
        prompt_parts.append(ball_situation_description)
        prompt_parts.append("Esta información describe la situación actual de la bola y lo que el jugador observa.")
        prompt_parts.append("Úsala para ajustar tu recomendación considerando el lie, las condiciones visuales y la perspectiva del jugador.")
    
    # Información de la Knowledge Base (si está disponible)
    if kb_formatted:
        prompt_parts.append(kb_formatted)
    
    # Información del perfil del jugador (si está disponible)
    if player_club_statistics:
        prompt_parts.append("\n=== PERFIL DEL JUGADOR - DISTANCIAS POR PALO ===")
        prompt_parts.append(f"⚠️ DISTANCIA AL HOYO: {distance_meters:.2f} metros")
        prompt_parts.append("\nDistancias promedio del jugador con cada palo:")
        
        # Ordenar palos por distancia promedio para facilitar el análisis
        sorted_stats = sorted(player_club_statistics, key=lambda x: x.get('average_distance_meters', 0), reverse=True)
        
        # Encontrar el palo más cercano a la distancia objetivo
        best_club = None
        min_diff = float('inf')
        
        for stat in sorted_stats:
            club_name = stat.get('club_name', 'Desconocido')
            avg_distance = stat.get('average_distance_meters', 0)
            avg_error = stat.get('average_error_meters', 0)
            shots = stat.get('shots_recorded', 0)
            
            # Calcular diferencia con la distancia objetivo
            diff = abs(avg_distance - distance_meters)
            
            if diff < min_diff:
                min_diff = diff
                best_club = club_name
            
            # Formatear el nombre del palo de manera más legible
            club_display = club_name
            if stat.get('club_number'):
                club_display = f"{club_name} ({stat['club_number']})"
            
            # Marcar el palo más adecuado
            closest_marker = " ⭐ PALO MÁS CERCANO A LA DISTANCIA OBJETIVO" if club_name == best_club else ""
            
            # Calcular distancia objetivo recomendada
            if avg_distance >= distance_meters:
                recommended_distance = distance_meters
                distance_note = f"→ Recomendar hacer {distance_meters:.0f}m (máximo la distancia al hoyo)"
            else:
                recommended_distance = avg_distance
                distance_note = f"→ Recomendar hacer {avg_distance:.0f}m (distancia promedio del palo)"
            
            prompt_parts.append(f"- {club_display}: {avg_distance:.0f} metros promedio (±{avg_error:.0f}m de error){closest_marker}")
            prompt_parts.append(f"  Diferencia con objetivo: {diff:.0f}m | {distance_note}")
        
        prompt_parts.append(f"\n⭐ PALO RECOMENDADO: {best_club}")
        prompt_parts.append(f"   (Es el que tiene la distancia más cercana a los {distance_meters:.0f}m que necesitas)")
        
        prompt_parts.append("\n🎯 INSTRUCCIONES CRÍTICAS PARA LA SELECCIÓN:")
        prompt_parts.append("1. DEBES elegir el palo marcado con ⭐ (el más cercano a la distancia objetivo)")
        prompt_parts.append("2. Si ese palo tiene más distancia que el hoyo → recomienda hacer como MÁXIMO la distancia al hoyo")
        prompt_parts.append("3. Si ese palo tiene menos distancia que el hoyo → recomienda hacer la distancia promedio del palo")
        
        prompt_parts.append("\n📋 EJEMPLO DETALLADO:")
        prompt_parts.append(f"   Distancia al hoyo: {distance_meters:.0f} metros")
        prompt_parts.append(f"   Palo recomendado: {best_club} (diferencia mínima: {min_diff:.0f}m)")
        
        # Buscar la distancia del mejor palo
        best_club_distance = 0
        for stat in sorted_stats:
            if stat.get('club_name') == best_club:
                best_club_distance = stat.get('average_distance_meters', 0)
                break
        
        if best_club_distance >= distance_meters:
            prompt_parts.append(f"   → Como el {best_club} ({best_club_distance:.0f}m) alcanza el hoyo, recomienda 'hacer {distance_meters:.0f} metros'")
        else:
            prompt_parts.append(f"   → Como el {best_club} ({best_club_distance:.0f}m) NO alcanza el hoyo, recomienda 'hacer {best_club_distance:.0f} metros'")
    
    # Instrucciones finales
    prompt_parts.append("\n=== 🎯 GENERA TU RECOMENDACIÓN FINAL ===")
    prompt_parts.append("Usa el formato conversacional y detallado especificado:")
    prompt_parts.append('"Estás a [X] metros del hoyo, te recomiendo utilizar [palo] con [swing] intentando hacer un [tipo de golpe] para [estrategia]. [Consideraciones]"')
    prompt_parts.append("\n✅ CHECKLIST OBLIGATORIO:")
    prompt_parts.append("1. ✓ Menciona la distancia exacta al hoyo al inicio")
    prompt_parts.append("2. ✓ Usa el palo marcado con ⭐ (el más cercano)")
    prompt_parts.append("3. ✓ Especifica el tipo de swing (completo, 3/4, 1/2)")
    prompt_parts.append("4. ✓ Indica el TIPO DE GOLPE (flop, pitch, chip, punch, etc.) según la base de conocimiento")
    prompt_parts.append("5. ✓ Usa la distancia correcta (máximo la distancia al hoyo si el palo alcanza)")
    prompt_parts.append("6. ✓ Explica la estrategia (pasar árboles, evitar bunker, etc.)")
    prompt_parts.append("7. ✓ Menciona condiciones: viento, obstáculos, lie de la bola")
    
    prompt = "\n".join(prompt_parts)
    
    return next_shot_agent(prompt)

