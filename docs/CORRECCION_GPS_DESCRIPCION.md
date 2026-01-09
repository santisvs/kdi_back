# Corrección GPS Basada en Descripciones Textuales

## 📋 Resumen

Nueva característica que permite corregir posiciones GPS erróneas basándose en descripciones textuales del jugador sobre su posición en el terreno.

### Problema Resuelto

**Ejemplo real:**
- Jugador está jugando el hoyo 1 (segundo golpe)
- GPS coloca al jugador en el fairway del hoyo 2 (error GPS)
- Jugador dice: *"mi bola está entre los árboles"*
- Sistema corrige: Detecta que debería estar en el hoyo 1, busca el polígono de árboles más cercano en ese hoyo, y corrige la posición GPS

## 🏗️ Arquitectura

### Componentes Nuevos

1. **`TerrainDescriptionService`** (`terrain_description_service.py`)
   - Extrae tipo de terreno desde descripciones en lenguaje natural
   - Mapea términos en español e inglés a tipos de obstáculos
   - Retorna confianza de la detección

2. **Método `find_nearest_obstacle_by_type`** en `GolfRepository`
   - Busca obstáculos de un tipo específico cerca de una posición GPS
   - Retorna la posición corregida (centro del polígono)

3. **Método `_correct_position_by_terrain_description`** en `GPSValidationService`
   - Lógica de corrección GPS basada en descripción
   - Evalúa si hay discrepancia y si debe corregir
   - Integrado en la estrategia híbrida de validación

### Flujo de Corrección

```
┌─────────────────────────────────────┐
│  Petición con GPS + Query           │
│  GPS: lat/lon                       │
│  Query: "qué palo... entre árboles" │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  1. Extraer descripción de terreno  │
│     └─> "entre árboles" → trees    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Detectar hoyo por GPS           │
│     └─> Hoyo 2 (incorrecto)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Validar contexto                │
│     └─> Jugador debe estar en Hoyo 1│
│         ❌ Discrepancia detectada   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Buscar obstáculo más cercano    │
│     └─> Buscar "trees" en Hoyo 1   │
│         dentro de 100m del GPS      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Corregir posición GPS           │
│     └─> Lat/Lon corregida al centro│
│         del polígono de árboles     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  6. Continuar con validación normal │
│     └─> Usar posición corregida    │
└─────────────────────────────────────┘
```

## 📝 Tipos de Terreno Soportados

El servicio reconoce los siguientes tipos de terreno:

| Tipo | Términos en Español | Términos en Inglés |
|------|---------------------|-------------------|
| **trees** | árbol, árboles, entre árboles, bosque | tree, trees, between trees, wood |
| **bunker** | bunker, trampa de arena, arenera | bunker, sand trap, sand |
| **water** | agua, lago, río, estanque | water, lake, river, pond |
| **rough_heavy** | rough pesado, hierba alta | heavy rough, thick rough |
| **rough** | rough ligero, hierba | light rough, grass |
| **fairway** | fairway, calle | fairway, on the fairway |
| **green** | green, verde | green, putting green |
| **out_of_bounds** | fuera de límites, ob | out of bounds, ob |
| **tee** | tee, salida | tee, teeing ground |

## 🔧 Uso

### En VoiceService

```python
# En _handle_recommend_shot, extraer descripción del query
validation_result = self.gps_validation_service.validate_and_identify_hole(
    match_id=match_id,
    user_id=user_id,
    course_id=course_id,
    latitude=latitude,
    longitude=longitude,
    terrain_description=query  # Pasar el query completo
)

# Usar posición corregida si existe
if validation_result.get('corrected_position'):
    corrected = validation_result['corrected_position']
    latitude = corrected['latitude']
    longitude = corrected['longitude']
    
hole_info = validation_result['hole_info']
```

### Extracción Manual de Descripción

Si quieres extraer solo la parte de terreno del query:

```python
from kdi_back.domain.services.terrain_description_service import TerrainDescriptionService

terrain_service = TerrainDescriptionService()

# Extraer descripción de terreno
terrain_info = terrain_service.extract_terrain_from_description(
    "qué palo me recomiendas, mi bola está entre los árboles"
)

if terrain_info:
    terrain_type = terrain_info['terrain_type']  # 'trees'
    confidence = terrain_info['confidence']  # 0.7-1.0
```

## 📊 Ejemplos de Casos de Uso

### Caso 1: Error GPS con Corrección Exitosa

**Input:**
- GPS: (40.44669, -3.86608) → Detecta Hoyo 2
- Estado: Jugador en Hoyo 1, segundo golpe
- Query: "qué palo me recomiendas, estoy entre los árboles"

**Procesamiento:**
1. Detecta terreno: `trees` (confianza: 0.9)
2. Valida contexto: GPS dice Hoyo 2 pero esperado es Hoyo 1
3. Busca obstáculo: Encuentra polígono de árboles en Hoyo 1 a 25m del GPS
4. Corrige: Posición corregida al centro del polígono

**Output:**
```json
{
  "hole_info": {"id": 1, "hole_number": 1, ...},
  "corrected_position": {
    "latitude": 40.44675,
    "longitude": -3.86612
  },
  "validation_confidence": 0.95,
  "validation_reason": "GPS corregido según descripción: trees"
}
```

### Caso 2: Sin Corrección Necesaria

**Input:**
- GPS: (40.44669, -3.86608) → Detecta Hoyo 1 (correcto)
- Estado: Jugador en Hoyo 1, segundo golpe
- Query: "qué palo me recomiendas, estoy en el fairway"

**Procesamiento:**
1. Detecta terreno: `fairway` (confianza: 0.8)
2. Valida contexto: GPS detecta Hoyo 1 correcto, confianza alta (0.9)
3. Verifica terreno: GPS confirma fairway
4. No corrige: No hay discrepancia

**Output:**
```json
{
  "hole_info": {"id": 1, "hole_number": 1, ...},
  "corrected_position": null,
  "validation_confidence": 0.9,
  "validation_reason": "Hoyo correcto detectado (hoyo 1)"
}
```

### Caso 3: Descripción pero Sin Obstáculo Cercano

**Input:**
- GPS: (40.44669, -3.86608) → Detecta Hoyo 2 (incorrecto)
- Estado: Jugador en Hoyo 1, segundo golpe
- Query: "estoy en un bunker"

**Procesamiento:**
1. Detecta terreno: `bunker` (confianza: 0.9)
2. Valida contexto: GPS dice Hoyo 2 pero esperado es Hoyo 1
3. Busca obstáculo: No encuentra bunker en Hoyo 1 dentro de 100m
4. No corrige: No se puede corregir (no hay obstáculo cercano)
5. Usa estrategia alternativa: Identifica por distancia al Hoyo 1

**Output:**
```json
{
  "hole_info": {"id": 1, "hole_number": 1, ...},
  "corrected_position": null,
  "validation_confidence": 0.85,
  "validation_reason": "Identificado por distancia al hoyo esperado 1 (45.2m)"
}
```

## ⚙️ Configuración

### Radio de Búsqueda

El radio máximo para buscar obstáculos es configurable:

```python
# En _correct_position_by_terrain_description
max_search_distance = 100.0  # metros (ajustable)
```

### Confianza Mínima de Descripción

Solo se usa la descripción si la confianza es > 0.6:

```python
if terrain_info and terrain_info['confidence'] > 0.6:
    # Proceder con corrección
```

## 🎯 Ventajas

1. **Mayor Precisión**: Corrige errores GPS comunes usando conocimiento del usuario
2. **Mejor Experiencia**: El jugador no necesita precisar coordenadas manualmente
3. **Robustez**: Funciona incluso con GPS impreciso si la descripción es clara
4. **Validación Inteligente**: Solo corrige cuando hay discrepancia real

## ⚠️ Limitaciones

1. **Requiere Obstáculos Definidos**: Necesita polígonos de obstáculos en la base de datos
2. **Radio Limitado**: Solo busca dentro de 100m (ajustable)
3. **Tipos Soportados**: Solo corrige para tipos de terreno que existen como obstáculos en la BD
4. **Depende de Descripción**: Si la descripción es ambigua o incorrecta, puede no funcionar

## 🚀 Próximas Mejoras

1. **Aprendizaje de Patrones**: Usar ML para aprender qué descripciones corresponden a qué terrenos
2. **Múltiples Obstáculos**: Si hay varios obstáculos del mismo tipo, elegir el más probable
3. **Corrección Parcial**: Si no hay polígono exacto, ajustar posición en dirección del terreno descrito
4. **Validación Cruzada**: Combinar múltiples descripciones para mayor confianza

## 📚 Referencias

- Ver `ANALISIS_VALIDACION_GPS.md` para el análisis completo del sistema híbrido
- Ver `RESUMEN_VALIDACION_GPS.md` para resumen ejecutivo
- Ver código en `terrain_description_service.py` y `gps_validation_service.py`


