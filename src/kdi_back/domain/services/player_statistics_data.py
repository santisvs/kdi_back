# -*- coding: utf-8 -*-
"""
Datos de distancias estándar por género y nivel de habilidad.

Este módulo contiene las distancias promedio por palo según el género
y el nivel de habilidad del jugador.
"""
from typing import Dict

# Mapeo de nombres de palos de la tabla a nombres en la base de datos
CLUB_NAME_MAPPING = {
    'Driver': 'Driver',
    'Wood 3': 'Madera 3',
    'Wood 5': 'Madera 5',
    'Hybrid 3': 'Híbrido 3',
    'Hybrid 4': 'Híbrido 4',
    'Iron 4': 'Hierro 4',
    'Iron 5': 'Hierro 5',
    'Iron 6': 'Hierro 6',
    'Iron 7': 'Hierro 7',
    'Iron 8': 'Hierro 8',
    'Iron 9': 'Hierro 9',
    'PW': 'Pitching Wedge',
    'GW': 'Gap Wedge',
    'SW': 'Sand Wedge',
    'LW': 'Lob Wedge',
}

# Distancias por género y nivel de habilidad
DISTANCES_BY_GENDER_AND_LEVEL = {
    'male': {
        'beginner': {
            'Driver': 160,
            'Wood 3': 145,
            'Wood 5': 135,
            'Hybrid 3': 130,
            'Hybrid 4': 120,
            'Iron 4': 140,
            'Iron 5': 130,
            'Iron 6': 120,
            'Iron 7': 110,
            'Iron 8': 100,
            'Iron 9': 90,
            'PW': 80,
            'GW': 65,
            'SW': 50,
            'LW': 35,
        },
        'intermediate': {
            'Driver': 190,
            'Wood 3': 175,
            'Wood 5': 165,
            'Hybrid 3': 160,
            'Hybrid 4': 150,
            'Iron 4': 170,
            'Iron 5': 160,
            'Iron 6': 150,
            'Iron 7': 140,
            'Iron 8': 130,
            'Iron 9': 120,
            'PW': 110,
            'GW': 95,
            'SW': 80,
            'LW': 65,
        },
        'advanced': {
            'Driver': 230,
            'Wood 3': 215,
            'Wood 5': 200,
            'Hybrid 3': 195,
            'Hybrid 4': 185,
            'Iron 4': 200,
            'Iron 5': 190,
            'Iron 6': 180,
            'Iron 7': 170,
            'Iron 8': 160,
            'Iron 9': 145,
            'PW': 135,
            'GW': 115,
            'SW': 100,
            'LW': 85,
        },
        'professional': {
            'Driver': 270,
            'Wood 3': 250,
            'Wood 5': 235,
            'Hybrid 3': 230,
            'Hybrid 4': 215,
            'Iron 4': 225,
            'Iron 5': 215,
            'Iron 6': 205,
            'Iron 7': 195,
            'Iron 8': 185,
            'Iron 9': 170,
            'PW': 155,
            'GW': 135,
            'SW': 120,
            'LW': 105,
        },
    },
    'female': {
        'beginner': {
            'Driver': 130,
            'Wood 3': 120,
            'Wood 5': 110,
            'Hybrid 3': 105,
            'Hybrid 4': 95,
            'Iron 4': 110,
            'Iron 5': 100,
            'Iron 6': 95,
            'Iron 7': 85,
            'Iron 8': 75,
            'Iron 9': 65,
            'PW': 60,
            'GW': 50,
            'SW': 40,
            'LW': 30,
        },
        'intermediate': {
            'Driver': 160,
            'Wood 3': 150,
            'Wood 5': 140,
            'Hybrid 3': 135,
            'Hybrid 4': 125,
            'Iron 4': 140,
            'Iron 5': 130,
            'Iron 6': 120,
            'Iron 7': 110,
            'Iron 8': 100,
            'Iron 9': 90,
            'PW': 85,
            'GW': 75,
            'SW': 65,
            'LW': 55,
        },
        'advanced': {
            'Driver': 190,
            'Wood 3': 175,
            'Wood 5': 165,
            'Hybrid 3': 160,
            'Hybrid 4': 150,
            'Iron 4': 170,
            'Iron 5': 160,
            'Iron 6': 150,
            'Iron 7': 140,
            'Iron 8': 130,
            'Iron 9': 120,
            'PW': 110,
            'GW': 95,
            'SW': 85,
            'LW': 75,
        },
        'professional': {
            'Driver': 220,
            'Wood 3': 205,
            'Wood 5': 195,
            'Hybrid 3': 190,
            'Hybrid 4': 175,
            'Iron 4': 195,
            'Iron 5': 185,
            'Iron 6': 175,
            'Iron 7': 165,
            'Iron 8': 155,
            'Iron 9': 145,
            'PW': 130,
            'GW': 115,
            'SW': 105,
            'LW': 95,
        },
    },
}


def get_default_distances(gender: str, skill_level: str) -> Dict[str, float]:
    """
    Obtiene las distancias por defecto para un género y nivel de habilidad.
    
    Args:
        gender: Género del jugador (male, female)
        skill_level: Nivel de habilidad (beginner, intermediate, advanced, professional)
        
    Returns:
        Diccionario con nombre de palo (nombre en BD) como clave y distancia en metros como valor
        
    Raises:
        ValueError: Si el género o nivel no son válidos
    """
    gender = gender.lower()
    skill_level = skill_level.lower()
    
    if gender not in DISTANCES_BY_GENDER_AND_LEVEL:
        raise ValueError(f"Género inválido: {gender}. Debe ser 'male' o 'female'")
    
    if skill_level not in DISTANCES_BY_GENDER_AND_LEVEL[gender]:
        raise ValueError(f"Nivel de habilidad inválido: {skill_level}")
    
    # Obtener las distancias del diccionario
    distances_table = DISTANCES_BY_GENDER_AND_LEVEL[gender][skill_level]
    
    # Mapear los nombres de la tabla a los nombres en la base de datos
    distances_db = {}
    for table_name, db_name in CLUB_NAME_MAPPING.items():
        if table_name in distances_table:
            distances_db[db_name] = distances_table[table_name]
    
    return distances_db

