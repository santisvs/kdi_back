# -*- coding: utf-8 -*-
"""
Helper para consultar AWS Bedrock Knowledge Base
"""
from typing import Optional, List, Dict
from kdi_back.infrastructure.config import settings
from kdi_back.infrastructure.config.aws_client import get_bedrock_agent_runtime_client


def query_knowledge_base(
    query: str,
    knowledge_base_id: Optional[str] = None,
    max_results: int = 5
) -> List[Dict]:
    """
    Consulta la AWS Bedrock Knowledge Base para obtener información relevante.
    
    Args:
        query: Texto de consulta para buscar en la base de conocimiento
        knowledge_base_id: ID de la Knowledge Base (opcional, se toma de settings si no se proporciona)
        max_results: Número máximo de resultados a retornar (default: 5)
        
    Returns:
        Lista de diccionarios con información relevante de la Knowledge Base.
        Cada diccionario contiene 'content' (texto) y 'score' (relevancia).
        Si hay error o no hay Knowledge Base configurada, retorna lista vacía.
    """
    # Obtener el ID de la Knowledge Base desde settings o parámetro
    kb_id = knowledge_base_id or getattr(settings, 'AWS_KNOWLEDGE_BASE_ID', None)
    
    if not kb_id:
        print("⚠️ Advertencia: No hay Knowledge Base ID configurado. Saltando consulta a Knowledge Base.")
        return []
    
    # Obtener la región de la Knowledge Base (por defecto eu-south-2)
    kb_region = getattr(settings, 'AWS_KNOWLEDGE_BASE_REGION', 'eu-south-2')
    
    try:
        # Crear cliente de Bedrock Agent Runtime en la región de la Knowledge Base
        # IMPORTANTE: La Knowledge Base se encuentra en la región eu-south-2
        # Esta función detecta automáticamente si está en AWS (usa IAM Role) o local (usa credenciales)
        bedrock_agent = get_bedrock_agent_runtime_client(region_name=kb_region)
        
        # Realizar la consulta usando retrieve
        response = bedrock_agent.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )
        
        # Extraer los resultados
        # La estructura de respuesta puede variar según la versión de la API
        results = []
        if 'retrievalResults' in response:
            for result in response['retrievalResults']:
                # Intentar diferentes estructuras posibles de la respuesta
                content = None
                score = result.get('score', 0.0)
                
                # Estructura 1: content.text
                if 'content' in result and isinstance(result['content'], dict):
                    content = result['content'].get('text', '')
                # Estructura 2: location.S3Location
                elif 'location' in result and 's3Location' in result['location']:
                    # Si es una referencia a S3, no podemos leer el contenido directamente aquí
                    # En este caso, podríamos necesitar descargar el archivo, pero por ahora lo omitimos
                    continue
                # Estructura 3: content directamente como string
                elif 'content' in result and isinstance(result['content'], str):
                    content = result['content']
                
                if content:
                    results.append({
                        'content': content,
                        'score': score
                    })
        
        print(f"✅ Consulta a Knowledge Base exitosa en región {kb_region}: {len(results)} resultados encontrados")
        return results
        
    except Exception as e:
        print(f"⚠️ Error al consultar Knowledge Base en región {kb_region}: {e}")
        # En caso de error, retornar lista vacía para no interrumpir el flujo
        return []


def format_knowledge_base_results(results: List[Dict]) -> str:
    """
    Formatea los resultados de la Knowledge Base para incluirlos en el prompt.
    
    Args:
        results: Lista de resultados de la Knowledge Base
        
    Returns:
        String formateado con la información de la Knowledge Base
    """
    if not results:
        return ""
    
    formatted_parts = ["\n=== INFORMACIÓN DE LA BASE DE CONOCIMIENTO ==="]
    formatted_parts.append("La siguiente información proviene de la base de conocimiento de golf:")
    formatted_parts.append("")
    
    for i, result in enumerate(results, 1):
        content = result.get('content', '')
        score = result.get('score', 0.0)
        
        if content:
            formatted_parts.append(f"[Conocimiento {i} - Relevancia: {score:.2f}]")
            formatted_parts.append(content)
            formatted_parts.append("")
    
    formatted_parts.append("IMPORTANTE: Usa esta información de la base de conocimiento para")
    formatted_parts.append("enriquecer tu recomendación, especialmente sobre:")
    formatted_parts.append("- Técnicas de golpe según la distancia")
    formatted_parts.append("- Estrategias para diferentes tipos de obstáculos")
    formatted_parts.append("- Consejos según la experiencia del jugador")
    formatted_parts.append("- Técnicas específicas según la situación de la bola")
    formatted_parts.append("")
    
    return "\n".join(formatted_parts)

