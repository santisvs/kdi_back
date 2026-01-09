# -*- coding: utf-8 -*-
"""
Helper para crear clientes de AWS (boto3) que funcionan tanto en local como en AWS.

En AWS Elastic Beanstalk:
- Usa automáticamente el IAM Role asignado a la instancia EC2
- No requiere credenciales explícitas

En entorno local:
- Usa las credenciales del archivo .env o configuración de AWS CLI
"""
import boto3
from typing import Optional
from kdi_back.infrastructure.config import settings


def get_bedrock_client(service_name: str = 'bedrock', region_name: Optional[str] = None):
    """
    Crea un cliente de boto3 para servicios de Bedrock.
    
    En AWS: Usa IAM Role automáticamente (no requiere credenciales)
    En local: Usa credenciales del .env o AWS CLI
    
    Args:
        service_name: Nombre del servicio (bedrock, bedrock-agent-runtime, etc.)
        region_name: Región de AWS (opcional, usa AWS_REGION de settings si no se proporciona)
    
    Returns:
        Cliente de boto3 configurado
    """
    region = region_name or settings.AWS_REGION
    
    # En AWS: No pasar credenciales, boto3 usará el IAM Role automáticamente
    if settings.IS_AWS_ENVIRONMENT:
        return boto3.client(
            service_name,
            region_name=region
        )
    
    # En local: Usar credenciales del .env si están disponibles
    # Si no hay credenciales en .env, boto3 intentará usar AWS CLI o variables de entorno
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        return boto3.client(
            service_name,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=region
        )
    
    # Si no hay credenciales explícitas, boto3 usará la cadena de credenciales por defecto
    # (AWS CLI, variables de entorno, IAM role si está en EC2, etc.)
    return boto3.client(
        service_name,
        region_name=region
    )


def get_bedrock_agent_runtime_client(region_name: Optional[str] = None):
    """
    Crea un cliente de boto3 para Bedrock Agent Runtime (Knowledge Base).
    
    Args:
        region_name: Región de AWS (opcional, usa AWS_KNOWLEDGE_BASE_REGION de settings si no se proporciona)
    
    Returns:
        Cliente de boto3 para bedrock-agent-runtime
    """
    region = region_name or getattr(settings, 'AWS_KNOWLEDGE_BASE_REGION', 'eu-south-2')
    return get_bedrock_client('bedrock-agent-runtime', region_name=region)

