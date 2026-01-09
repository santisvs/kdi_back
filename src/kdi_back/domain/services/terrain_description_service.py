# -*- coding: utf-8 -*-
"""
Servicio para procesar descripciones textuales de terreno/obstáculos del jugador.

Extrae información sobre el tipo de terreno u obstáculo desde descripciones en lenguaje natural
como "mi bola está entre los árboles", "estoy en un bunker", "hay agua cerca", etc.
"""
from typing import Optional, Dict, Any, List
import re


class TerrainDescriptionService:
    """
    Servicio para extraer información de terreno desde descripciones textuales.
    
    Mapea descripciones en lenguaje natural a tipos de terreno conocidos:
    - trees, bunker, water, rough_heavy, fairway, green, etc.
    """
    
    # Mapeo de términos en español e inglés a tipos de terreno
    TERRAIN_KEYWORDS = {
        'trees': {
            'es': ['árbol', 'arbol', 'árboles', 'arboles', 'entre árboles', 'bajo árboles', 
                   'debajo de árboles', 'entre los árboles', 'en los árboles', 'arboleda',
                   'bosque', 'matorral', 'vegetación', 'fronda'],
            'en': ['tree', 'trees', 'between trees', 'under trees', 'in trees', 'wood', 'woods'],
            'type': 'trees'
        },
        'bunker': {
            'es': ['bunker', 'búnker', 'trampa de arena', 'arenera', 'arena', 'en la arena',
                   'bunker de arena', 'trampa'],
            'en': ['bunker', 'sand trap', 'sand', 'in the sand', 'sand pit'],
            'type': 'bunker'
        },
        'water': {
            'es': ['agua', 'lago', 'estanque', 'río', 'arroyo', 'en el agua', 'cerca del agua',
                   'lago', 'charco', 'humedal', 'pantano'],
            'en': ['water', 'lake', 'pond', 'river', 'stream', 'in the water', 'near water',
                   'wetland', 'swamp'],
            'type': 'water'
        },
        'rough_heavy': {
            'es': ['rough', 'rough pesado', 'hierba alta', 'hierba larga', 'pasto alto',
                   'vegetación densa', 'matorral espeso', 'zona de hierba'],
            'en': ['rough', 'heavy rough', 'thick rough', 'long grass', 'dense vegetation'],
            'type': 'rough_heavy'
        },
        'rough': {
            'es': ['rough ligero', 'hierba', 'pasto', 'hierba corta', 'fuera del fairway'],
            'en': ['light rough', 'grass', 'off fairway', 'first cut'],
            'type': 'rough'
        },
        'fairway': {
            'es': ['fairway', 'calle', 'en la calle', 'sobre el fairway', 'calle del campo'],
            'en': ['fairway', 'in the fairway', 'on the fairway'],
            'type': 'fairway'
        },
        'green': {
            'es': ['green', 'verde', 'en el green', 'sobre el green', 'putting green'],
            'en': ['green', 'on the green', 'putting green', 'green surface'],
            'type': 'green'
        },
        'out_of_bounds': {
            'es': ['fuera de límites', 'fuera del campo', 'ob', 'out of bounds', 'fuera'],
            'en': ['out of bounds', 'ob', 'out', 'outside the course'],
            'type': 'out_of_bounds'
        },
        'tee': {
            'es': ['tee', 'salida', 'en el tee', 'salida del hoyo', 'tee de salida'],
            'en': ['tee', 'teeing ground', 'tee box', 'on the tee'],
            'type': 'tee'
        }
    }
    
    def extract_terrain_from_description(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información de terreno desde una descripción textual.
        
        Args:
            description: Descripción en lenguaje natural del jugador
            
        Returns:
            Diccionario con:
            - terrain_type: Tipo de terreno detectado (trees, bunker, water, etc.)
            - confidence: Confianza de la detección (0.0-1.0)
            - matched_keywords: Palabras clave que coincidieron
            - original_description: Descripción original
            - None si no se detecta ningún terreno específico
        """
        if not description or not isinstance(description, str):
            return None
        
        description_lower = description.lower().strip()
        
        # Buscar coincidencias para cada tipo de terreno
        matches = []
        
        for terrain_key, terrain_info in self.TERRAIN_KEYWORDS.items():
            terrain_type = terrain_info['type']
            keywords = terrain_info.get('es', []) + terrain_info.get('en', [])
            
            # Buscar coincidencias
            matched_keywords = []
            for keyword in keywords:
                # Buscar palabra completa o como parte de frase
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, description_lower):
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Calcular confianza basada en número de coincidencias y longitud del término
                confidence = min(0.9, 0.5 + (len(matched_keywords) * 0.1))
                
                # Aumentar confianza si hay indicadores de posición explícitos
                position_indicators = ['está', 'estoy', 'está en', 'en', 'entre', 'sobre', 'bajo', 
                                     'is', 'in', 'between', 'on', 'under', 'near']
                if any(indicator in description_lower for indicator in position_indicators):
                    confidence = min(1.0, confidence + 0.2)
                
                matches.append({
                    'terrain_type': terrain_type,
                    'confidence': confidence,
                    'matched_keywords': matched_keywords,
                    'terrain_key': terrain_key
                })
        
        if not matches:
            return None
        
        # Retornar el match con mayor confianza
        best_match = max(matches, key=lambda x: x['confidence'])
        
        return {
            'terrain_type': best_match['terrain_type'],
            'confidence': best_match['confidence'],
            'matched_keywords': best_match['matched_keywords'],
            'original_description': description,
            'all_matches': matches  # Para debugging
        }
    
    def is_terrain_description(self, description: str) -> bool:
        """
        Verifica si una descripción parece contener información sobre terreno.
        
        Args:
            description: Texto a verificar
            
        Returns:
            True si parece contener información de terreno, False si no
        """
        result = self.extract_terrain_from_description(description)
        return result is not None and result['confidence'] > 0.5



