# Flujo Completo: Recomendación → Golpeo → Evaluación → Estadísticas → Mejora del Perfil

Este documento explica el flujo completo de cómo el sistema maneja cuando un jugador:
1. Pide una recomendación
2. Golpea la bola (registra golpe)
3. Pide otra recomendación o indica otro golpeo
4. Se evalúa el golpe anterior
5. Se actualizan las estadísticas del jugador
6. **Se mejora el perfil del jugador para futuras recomendaciones**

## Resumen del Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. JUGADOR PIDE RECOMENDACIÓN                                   │
│    "Dame una recomendación"                                     │
│    → voice-command → intent: "recommend_shot"                   │
│    → Obtiene estadísticas del jugador (si existen)              │
│    → Calcula recomendación personalizada usando estadísticas   │
│    → Retorna recomendación con palo, distancia, etc.            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. JUGADOR GOLPEA LA BOLA                                       │
│    "He golpeado"                                                │
│    → voice-command → intent: "register_stroke"                  │
│    → ANTES de incrementar:                                      │
│      a) Evalúa stroke anterior (si existe)                      │
│      b) Actualiza estadísticas del palo usado                  │
│    → Incrementa contador de golpes                             │
│    → Crea nuevo stroke con posición GPS actual                 │
│    → Posición GPS = inicial del nuevo stroke                   │
│    → Posición GPS = final del stroke anterior                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CICLO DE APRENDIZAJE                                         │
│    Cada golpe evaluado mejora el perfil del jugador:           │
│    - Actualiza distancia promedio del palo                      │
│    - Actualiza precisión del palo                              │
│    - Mejora futuras recomendaciones                             │
└─────────────────────────────────────────────────────────────────┘
```

## Detalles del Flujo

### 1. Jugador Pide Recomendación

**Endpoint**: `POST /match/<match_id>/voice-command`

**Intención detectada**: `recommend_shot`

**Handler**: `_handle_recommend_shot()` en `voice_service.py`

**Proceso**:

1. **Obtiene información del hoyo** desde estado persistido o GPS
2. **Obtiene estadísticas del jugador** (si existen):
   ```python
   player_profile = player_service.player_repository.get_player_profile_by_user_id(user_id)
   if player_profile:
       player_club_statistics = player_service.player_repository.get_player_club_statistics(
           player_profile['id']
       )
   ```
   - Si el jugador tiene estadísticas, se usan para personalizar la recomendación
   - Si no tiene estadísticas, se usan valores por defecto

3. **Calcula trayectoria óptima** usando algoritmo evolutivo:
   - `bola_menos_10m_optimal_shot()`: Busca optimal_shots cercanos
   - `find_strategic_shot()`: Evalúa trayectorias estratégicas
   - `evaluacion_final()`: Selecciona la mejor trayectoria
   - **Usa `player_club_statistics` para**:
     * Determinar distancia máxima alcanzable del jugador
     * Calcular recomendación de palo personalizada
     * Evaluar riesgo basado en precisión del jugador

4. **Retorna recomendación** en lenguaje natural con:
   - Distancia al objetivo
   - Palo recomendado (personalizado según estadísticas)
   - Tipo de swing
   - Obstáculos
   - Nivel de riesgo

**Respuesta ejemplo**:
```
"Estás a 150 metros del hoyo. Te recomiendo utilizar hierro 7 con swing completo 
intentando alcanzar el green. Ten cuidado con el bunker a la izquierda."
```

**Nota importante**: En este punto NO se crea ningún registro de stroke. Solo se da la recomendación.

---

### 2. Jugador Golpea la Bola

**Endpoint**: `POST /match/<match_id>/voice-command`

**Intención detectada**: `register_stroke`

**Handler**: `_handle_register_stroke()` en `voice_service.py`

**Concepto clave**: 
Cuando el jugador dice "he golpeado", la posición GPS que envía el frontend es:
- La posición **INICIAL** del nuevo stroke que se va a crear (donde está la bola antes de golpear)
- La posición **FINAL** del stroke anterior pendiente (donde terminó la bola del golpe anterior)

**Proceso**:

1. **Obtiene información del hoyo** desde estado persistido o GPS

2. **ANTES de incrementar el contador**:
   ```python
   # Buscar stroke pendiente de evaluación
   pending_stroke = match_repository.get_last_unevaluated_stroke(match_id, user_id, hole_id)
   
   if pending_stroke:
       # Evaluar el stroke anterior usando posición GPS actual como posición final
       stroke_evaluation = match_service.evaluate_stroke(
           match_id=match_id,
           user_id=user_id,
           course_id=course_id,
           hole_number=hole_number,
           ball_end_latitude=latitude,  # Posición GPS actual = posición final del stroke anterior
           ball_end_longitude=longitude,
           current_strokes=current_strokes
       )
       
       # Si se evaluó y tiene palo usado, actualizar estadísticas
       if stroke_evaluation and stroke_evaluation.get('club_used_id'):
           player_service.player_repository.update_club_statistics_after_stroke(
               player_profile_id=player_profile['id'],
               club_id=stroke_evaluation['club_used_id'],
               actual_distance=actual_distance,
               target_distance=target_distance,
               quality_score=quality_score
           )
   ```

3. **Incrementa el contador de golpes**:
   ```python
   score = match_service.increment_hole_strokes(...)
   ```

4. **Crea el nuevo stroke** usando la posición GPS actual como posición inicial:
   ```python
   stroke_created = match_service.create_stroke(
       match_id=match_id,
       user_id=user_id,
       course_id=course_id,
       hole_number=hole_number,
       ball_start_latitude=latitude,  # Posición GPS actual = posición inicial del nuevo stroke
       ball_start_longitude=longitude,
       stroke_number=strokes,  # El golpe que acabamos de incrementar
       club_used_id=None,  # No se proporciona en el query de voz
       ...
   )
   ```

**Respuesta ejemplo**:
```
"Golpe registrado. Llevas 2 golpes en el hoyo 5."
```

**Ejemplo del flujo completo**:

**Escenario 1: Jugador registra primer golpe vía voz**
```
1. Frontend: POST /match/123/voice-command
   Body: {
     "course_id": 1,
     "latitude": 40.44445,  ← Posición GPS (inicial del stroke #1)
     "longitude": -3.87095,
     "query": "He golpeado"
   }
   
   → Sistema: Clasifica intención → "register_stroke"
   → Sistema: Llama a _handle_register_stroke()
   → Sistema ANTES de incrementar:
      a) Busca stroke pendiente → NO encuentra (es el primer golpe)
   → Sistema: increment_hole_strokes() → Contador: 1 golpe
   → Sistema: Crea stroke #1 con:
      - ball_start_latitude: 40.44445
      - ball_start_longitude: -3.87095
      - stroke_number: 1
      - evaluated: FALSE
   → Respuesta: "Golpe registrado. Llevas 1 golpe en el hoyo 5."

Estado actual:
- Contador de golpes: 1
- Strokes en base de datos: 1 (stroke #1 pendiente de evaluación)
```

**Escenario 2: Jugador registra segundo golpe vía voz (evalúa stroke #1 y crea stroke #2)**
```
1. Estado previo:
   - Contador: 1 golpe
   - Stroke #1 creado (pendiente de evaluación)
   - Posición GPS inicial stroke #1: (40.44445, -3.87095)

2. Frontend: POST /match/123/voice-command
   Body: {
     "course_id": 1,
     "latitude": 40.44450,  ← Posición GPS (final del stroke #1, inicial del stroke #2)
     "longitude": -3.87100,
     "query": "He golpeado otra vez"
   }
   
   → Sistema: Clasifica intención → "register_stroke"
   → Sistema: Llama a _handle_register_stroke()
   → Sistema ANTES de incrementar:
      a) Busca stroke pendiente → ENCUENTRA stroke #1
      b) Evalúa stroke #1 usando posición GPS actual como posición final:
         - ball_end_latitude: 40.44450
         - ball_end_longitude: -3.87100
         - Calcula distancia real: 50 metros
         - Calcula calidad: 95 (muy bueno)
         - Calcula errores de distancia y dirección
         - Marca stroke #1 como evaluado ✅
      c) Actualiza estadísticas del palo usado (si stroke #1 tenía club_used_id):
         - Actualiza average_distance_meters del palo
         - Actualiza average_error_meters del palo
         - Incrementa shots_recorded
         - Actualiza min/max_distance_meters
   → Sistema: increment_hole_strokes() → Contador: 2 golpes
   → Sistema: Crea stroke #2 con:
      - ball_start_latitude: 40.44450
      - ball_start_longitude: -3.87100
      - stroke_number: 2
      - evaluated: FALSE
   → Respuesta: "Golpe registrado. Llevas 2 golpes en el hoyo 5."

Estado actual:
- Contador de golpes: 2
- Strokes en base de datos: 
  * stroke #1: EVALUADO ✅ (estadísticas actualizadas si tenía palo)
  * stroke #2: Pendiente de evaluación
```

**Escenario 3: Jugador registra tercer golpe vía voz (evalúa stroke #2 y crea stroke #3)**
```
1. Estado previo:
   - Contador: 2 golpes
   - Stroke #1: Evaluado ✅
   - Stroke #2: Pendiente de evaluación
   - Posición GPS inicial stroke #2: (40.44450, -3.87100)

2. Frontend: POST /match/123/voice-command
   Body: {
     "course_id": 1,
     "latitude": 40.44455,  ← Posición GPS (final del stroke #2, inicial del stroke #3)
     "longitude": -3.87105,
     "query": "He golpeado otra vez"
   }
   
   → Sistema: Clasifica intención → "register_stroke"
   → Sistema: Llama a _handle_register_stroke()
   → Sistema ANTES de incrementar:
      a) Busca stroke pendiente → ENCUENTRA stroke #2
      b) Evalúa stroke #2 usando posición GPS actual como posición final:
         - ball_end_latitude: 40.44455
         - ball_end_longitude: -3.87105
         - Calcula distancia real: 45 metros
         - Calcula calidad: 90
         - Marca stroke #2 como evaluado ✅
      c) Actualiza estadísticas del palo usado (si stroke #2 tenía club_used_id)
   → Sistema: increment_hole_strokes() → Contador: 3 golpes
   → Sistema: Crea stroke #3 con:
      - ball_start_latitude: 40.44455
      - ball_start_longitude: -3.87105
      - stroke_number: 3
      - evaluated: FALSE
   → Respuesta: "Golpe registrado. Llevas 3 golpes en el hoyo 5."

Estado actual:
- Contador de golpes: 3
- Strokes en base de datos: 
  * stroke #1: EVALUADO ✅
  * stroke #2: EVALUADO ✅ (estadísticas actualizadas si tenía palo)
  * stroke #3: Pendiente de evaluación
```

**Escenario 4: Jugador pide recomendación después de golpear (evalúa stroke pendiente)**
```
1. Estado previo:
   - Contador: 1 golpe
   - Stroke #1 creado (pendiente de evaluación)
   - Posición GPS inicial stroke #1: (40.44445, -3.87095)

2. Jugador se mueve a nueva posición: (40.44450, -3.87100)

3. Frontend: POST /match/123/voice-command
   Body: {
     "course_id": 1,
     "latitude": 40.44450,  ← Posición GPS actual (donde está la bola ahora)
     "longitude": -3.87100,
     "query": "Dame una recomendación"
   }
   
   → Sistema: Clasifica intención → "recommend_shot"
   → Sistema: Llama a trajectory-options-evol
   → Sistema ANTES de calcular recomendación:
      a) Busca stroke no evaluado → ENCUENTRA stroke #1
      b) Evalúa stroke #1 usando nueva posición GPS como posición final:
         - ball_end_latitude: 40.44450
         - ball_end_longitude: -3.87100
         - Calcula distancia: ~50 metros
         - Calcula calidad del golpe
         - Marca stroke #1 como evaluado ✅
      c) Actualiza estadísticas del palo (si aplica)
   → Sistema: Obtiene estadísticas actualizadas del jugador
   → Sistema: Calcula nueva recomendación usando estadísticas actualizadas
   → Respuesta: Recomendación personalizada para la nueva posición

Estado actual:
- Contador: 1 golpe
- Strokes en base de datos: 1 (stroke #1 evaluado ✅)
- Estadísticas del jugador: Actualizadas (si stroke #1 tenía palo)
```

---

### 3. Evaluación del Golpe

### Método: `evaluate_stroke()` en `match_service.py`

**Parámetros**:
- `match_id`, `user_id`, `course_id`, `hole_number`
- `ball_end_latitude`, `ball_end_longitude`: Posición final de la bola (nueva posición GPS)
- `target_latitude`, `target_longitude`: Objetivo (opcional, se calcula si no se proporciona)
- `is_on_green`: Si la bola terminó en el green (opcional, se detecta si no se proporciona)
- `current_strokes`: Número actual de golpes en el hoyo (opcional, se obtiene si no se proporciona)

**Proceso**:

1. **Busca el último golpe no evaluado**:
   ```python
   stroke = self.match_repository.get_last_unevaluated_stroke(
       match_id, user_id, hole_id
   )
   ```

2. **VALIDA que el golpe tiene sentido**:
   Antes de evaluar, se ejecuta `_validate_stroke_makes_sense()` que verifica:
   
   a. **Validación de stroke_number**: 
      - Verifica que `stroke_number == current_strokes - 1`
      - Esto asegura que el stroke pendiente es realmente el anterior al golpe actual
      - Si no coincide, NO se evalúa (retorna None)
   
   b. **Validación de distancia alcanzable**:
      - Obtiene las estadísticas de todos los palos del jugador
      - Encuentra la **mayor distancia promedio** entre todas las estadísticas
      - Calcula el **máximo permitido**: `mayor_distancia_promedio * 1.3` (30% más)
      - Verifica que la distancia no exceda este máximo permitido
      - Si no hay estadísticas del jugador, usa valor conservador por defecto (350m)
      - Si la distancia excede el máximo permitido, puede ser un error de GPS y NO se evalúa
   
   c. **Validación de trayectoria recta**:
      - Si hay `proposed_distance_meters`, calcula la distancia esperada al objetivo
      - Verifica que la desviación lateral no sea excesiva (máximo 50m adicionales)
      - Si la desviación es más del doble de lo esperado, puede ser un error de GPS y NO se evalúa
   
   d. **Validación de mismo hoyo**:
      - Ya verificado por `hole_id` en la búsqueda del stroke
   
   Si alguna validación falla, el golpe NO se evalúa y se retorna `None` con un mensaje de advertencia.

3. **Detecta si la bola terminó en el green**

4. **Detecta si el golpe comenzó en el green**

5. **Si comenzó Y terminó en el green**: NO se evalúa (solo se marca como evaluado)

6. **Si NO es golpe en el green**:
   - Calcula distancia real alcanzada
   - Obtiene distancia objetivo (propuesta o distancia a bandera)
   - Calcula error de distancia: `abs(actual_distance - target_distance)`
   - Calcula calidad del golpe (0-100):
     ```python
     error_percentage = (distance_error / reference_distance) * 100
     quality_score = max(0, min(100, 100 - error_percentage))
     ```
   - Calcula error de dirección (distancia al objetivo final)

7. **Actualiza el stroke en la base de datos** con la evaluación

---

### 4. Actualización de Estadísticas del Palo

### Método: `update_club_statistics_after_stroke()` en `player_repository_sql.py`

**Cuándo se actualiza**:
- Después de evaluar un stroke que tiene `club_used_id`
- Solo si `evaluation_quality` no es None (no fue golpe en el green)

**Parámetros**:
- `player_profile_id`: ID del perfil del jugador
- `club_id`: ID del palo usado
- `actual_distance`: Distancia real alcanzada
- `target_distance`: Distancia objetivo (propuesta o calculada)
- `quality_score`: Calidad del golpe (0-100)

**Proceso**:

1. **Obtiene estadísticas actuales** del palo:
   - `average_distance_meters`: Distancia promedio alcanzada
   - `average_error_meters`: Error promedio
   - `shots_recorded`: Número de golpes registrados
   - `min_distance_meters`: Distancia mínima alcanzada
   - `max_distance_meters`: Distancia máxima alcanzada
   - `error_std_deviation`: Desviación estándar del error

2. **Si no existen estadísticas**: Crea estadísticas iniciales con los valores del primer golpe

3. **Si existen estadísticas**: Actualiza usando **media móvil ponderada**:
   ```python
   learning_rate = 0.3  # Factor de aprendizaje (30% peso al nuevo golpe)
   
   # Actualizar distancia promedio
   new_avg_distance = current_avg_distance * (1 - learning_rate) + actual_distance * learning_rate
   
   # Calcular error actual
   current_error = abs(actual_distance - target_distance)
   
   # Actualizar error promedio
   new_avg_error = current_avg_error * (1 - learning_rate) + current_error * learning_rate
   
   # Actualizar min/max distancia
   new_min = min(current_min, actual_distance)
   new_max = max(current_max, actual_distance)
   
   # Actualizar desviación estándar (simplificado: 50% del error promedio)
   new_std_dev = new_avg_error * 0.5
   
   # Incrementar contador de golpes
   new_shots_recorded = shots_recorded + 1
   ```

4. **Actualiza en la base de datos**:
   - Actualiza `player_club_statistics` con los nuevos valores
   - Actualiza `last_updated` timestamp

**Ejemplo de actualización**:

```
Estado inicial (Hierro 7):
- average_distance_meters: 120.0
- average_error_meters: 10.0
- shots_recorded: 5

Nuevo golpe:
- actual_distance: 125.0
- target_distance: 120.0
- quality_score: 95.0

Cálculo:
- learning_rate = 0.3
- new_avg_distance = 120.0 * 0.7 + 125.0 * 0.3 = 121.5
- current_error = |125.0 - 120.0| = 5.0
- new_avg_error = 10.0 * 0.7 + 5.0 * 0.3 = 8.5
- new_shots_recorded = 6

Estado final:
- average_distance_meters: 121.5
- average_error_meters: 8.5
- shots_recorded: 6
```

**Nota importante**: 
- Las estadísticas se actualizan **solo si**:
  - El stroke tiene `club_used_id` (se usó un palo)
  - El stroke tiene `evaluation_quality` no es None (no fue golpe en el green)
- Los golpes en el green NO se evalúan y NO actualizan estadísticas

---

### 5. Evaluación y Mejora del Perfil del Jugador

El sistema evalúa y mejora el perfil del jugador a través de los golpes realizados mediante un **ciclo de aprendizaje continuo**.

#### 5.1. Cómo se Evalúa el Perfil

**Datos que se recopilan**:
- **Distancia alcanzada con cada palo**: Se registra la distancia real de cada golpe
- **Precisión de cada palo**: Se calcula el error promedio (diferencia entre objetivo y real)
- **Consistencia**: Se calcula la desviación estándar del error
- **Rango de distancias**: Se registra la distancia mínima y máxima alcanzada con cada palo
- **Número de golpes**: Se cuenta cuántos golpes se han registrado con cada palo

**Métricas calculadas**:
```python
# Para cada palo del jugador:
{
    'golf_club_id': 7,  # Hierro 7
    'average_distance_meters': 121.5,  # Distancia promedio
    'min_distance_meters': 110.0,  # Distancia mínima
    'max_distance_meters': 135.0,  # Distancia máxima
    'average_error_meters': 8.5,  # Error promedio
    'error_std_deviation': 4.25,  # Desviación estándar del error
    'shots_recorded': 15  # Número de golpes registrados
}
```

#### 5.2. Cómo se Usan las Estadísticas para Mejorar Recomendaciones

**1. Distancia Máxima Alcanzable**:
```python
def _get_max_accessible_distance(player_club_statistics):
    # Busca la distancia máxima entre todas las estadísticas
    max_distance = 0.0
    for stat in player_club_statistics:
        distance = stat.get('max_distance_meters') or stat.get('average_distance_meters', 0)
        if distance > max_distance:
            max_distance = distance
    return max_distance
```
- **Uso**: Determina si el green es alcanzable desde la posición actual
- **Impacto**: Si el jugador puede alcanzar el green, se evalúa trayectoria directa. Si no, se buscan puntos estratégicos intermedios.

**2. Recomendación de Palo Personalizada**:
```python
def calculate_club_recommendation(distance_meters, player_club_statistics):
    # Busca el palo cuyo average_distance_meters más se acerque a distance_meters
    # Considera también el error promedio para elegir el palo más preciso
    best_club = None
    best_score = float('inf')
    
    for stat in player_club_statistics:
        avg_distance = stat.get('average_distance_meters', 0)
        avg_error = stat.get('average_error_meters', 0)
        
        # Score = diferencia de distancia + error promedio (peso)
        distance_diff = abs(avg_distance - distance_meters)
        score = distance_diff + (avg_error * 0.5)  # Penalizar palos menos precisos
        
        if score < best_score:
            best_score = score
            best_club = stat.get('golf_club_id')
    
    return best_club
```
- **Uso**: Selecciona el palo más adecuado según las estadísticas del jugador
- **Impacto**: Las recomendaciones se adaptan al rendimiento real del jugador, no a valores teóricos.

**3. Evaluación de Riesgo Personalizada**:
```python
def _calculate_risk_score_detailed(obstacles, distance_to_target, player_club_statistics):
    # Calcula riesgo basado en:
    # - Obstáculos en la trayectoria
    # - Precisión del jugador con el palo recomendado
    # - Distancia al objetivo
    
    # Si hay estadísticas del palo, ajustar riesgo según precisión del jugador
    if player_club_statistics:
        club_stat = find_club_stat(recommended_club, player_club_statistics)
        if club_stat:
            # Jugadores más precisos tienen menos riesgo
            precision_factor = 1.0 - (club_stat['average_error_meters'] / 100.0)
            risk = base_risk * precision_factor
    
    return risk
```
- **Uso**: Ajusta el nivel de riesgo según la precisión del jugador
- **Impacto**: Jugadores más precisos reciben recomendaciones más agresivas, jugadores menos precisos reciben recomendaciones más conservadoras.

#### 5.3. Ciclo de Aprendizaje

```
┌─────────────────────────────────────────────────────────────┐
│ INICIO: Jugador sin estadísticas                            │
│ → Sistema usa valores por defecto                           │
│ → Recomendaciones genéricas                                 │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ JUGADOR GOLPEA                                               │
│ → Se evalúa el golpe                                         │
│ → Se actualizan estadísticas del palo usado                 │
│ → Perfil del jugador mejora                                 │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ PRÓXIMA RECOMENDACIÓN                                        │
│ → Sistema obtiene estadísticas actualizadas                 │
│ → Calcula recomendación personalizada                      │
│ → Recomendación más precisa que la anterior                 │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ CICLO CONTINÚA                                               │
│ → Cada golpe mejora el perfil                               │
│ → Cada recomendación es más personalizada                   │
│ → El sistema aprende del jugador                            │
└─────────────────────────────────────────────────────────────┘
```

**Ejemplo de evolución del perfil**:

**Golpe 1** (Jugador sin estadísticas):
```
Recomendación: "Hierro 7, 120 metros" (valor por defecto)
Golpe real: 125 metros
→ Crea estadísticas iniciales:
   - average_distance_meters: 125.0
   - average_error_meters: 5.0
   - shots_recorded: 1
```

**Golpe 2** (Jugador con 1 golpe registrado):
```
Recomendación: "Hierro 7, 125 metros" (basada en estadísticas)
Golpe real: 120 metros
→ Actualiza estadísticas:
   - average_distance_meters: 123.5 (media móvil)
   - average_error_meters: 4.5
   - shots_recorded: 2
```

**Golpe 10** (Jugador con 9 golpes registrados):
```
Recomendación: "Hierro 7, 122 metros" (muy personalizada)
Golpe real: 121 metros
→ Actualiza estadísticas:
   - average_distance_meters: 122.1 (refinada con muchos golpes)
   - average_error_meters: 3.2 (más preciso)
   - shots_recorded: 10
```

**Golpe 50** (Jugador con 49 golpes registrados):
```
Recomendación: "Hierro 7, 122 metros" (altamente personalizada)
Golpe real: 122 metros
→ Estadísticas muy precisas:
   - average_distance_meters: 122.0 (estable)
   - average_error_meters: 2.5 (muy preciso)
   - shots_recorded: 50
```

#### 5.4. Ventajas del Sistema de Aprendizaje

1. **Personalización progresiva**: 
   - Las recomendaciones mejoran con cada golpe
   - Se adaptan al estilo y capacidad real del jugador

2. **Adaptación a cambios**:
   - Si el jugador mejora, las estadísticas se actualizan automáticamente
   - Si el jugador empeora, el sistema se adapta

3. **Precisión mejorada**:
   - Más golpes = estadísticas más precisas
   - Recomendaciones más confiables

4. **Aprendizaje por palo**:
   - Cada palo tiene sus propias estadísticas
   - El sistema aprende las fortalezas y debilidades del jugador con cada palo

---

### 6. Dos Formas de Registrar Golpes

#### Forma 1: Incrementar uno a uno (crea strokes pendientes)

**Cuándo se usa**: Cuando el jugador dice "he golpeado" (con o sin palo específico)

**Proceso**:
1. Evalúa el stroke anterior (si existe) usando la posición GPS actual como posición final
2. Incrementa el contador de golpes
3. Crea el nuevo stroke usando la posición GPS actual como posición inicial (pendiente de evaluación)

**Resultado**:
- Contador incrementado
- Stroke anterior evaluado (si existía)
- Nuevo stroke creado (pendiente de evaluación)
- Estadísticas actualizadas (si el stroke anterior tenía palo)

#### Forma 2: Setear el total (elimina strokes pendientes)

**Cuándo se usa**: Cuando el jugador dice "completa el hoyo con X golpes" o "corrige el resultado del hoyo Y con X golpes"

**Proceso**:
1. Setea el contador de golpes al valor total especificado
2. **Elimina todos los strokes pendientes** de ese hoyo (el hoyo está finalizado)
3. No se evalúan golpes individuales

**Resultado**:
- Contador seteado al valor total
- Todos los strokes pendientes eliminados
- No se actualizan estadísticas (no se evalúan golpes individuales)

**Razón**: Cuando se setea el total, el hoyo está finalizado y no se necesitan evaluar golpes individuales.

---

## Flujo Completo Ejemplo: Ciclo de Aprendizaje

### Escenario: Jugador nuevo (sin estadísticas) en el hoyo 5

**1. Jugador pide primera recomendación**:
```
Jugador: "Dame una recomendación"
→ Sistema: Obtiene estadísticas → NO encuentra (jugador nuevo)
→ Sistema: Usa valores por defecto (distancia máxima: 250m)
→ Sistema: "Estás a 150 metros del hoyo. Te recomiendo utilizar hierro 7..."
→ NO se crea stroke
```

**2. Jugador golpea (primer golpe)**:
```
Jugador: "He golpeado" (GPS: 40.44445, -3.87095)
→ Sistema: NO hay stroke anterior que evaluar
→ Sistema: increment_hole_strokes() → Contador: 1 golpe
→ Sistema: Crea stroke #1 (pendiente)
→ Estado: Contador = 1, Stroke #1 pendiente
```

**3. Jugador golpea segunda vez (evalúa stroke #1)**:
```
Jugador: "He golpeado otra vez" (GPS: 40.44450, -3.87100)
→ Sistema: Evalúa stroke #1:
   - Distancia real: 50 metros
   - Calidad: 95
   - PERO: stroke #1 NO tenía club_used_id
   - NO se actualizan estadísticas (no hay palo identificado)
→ Sistema: increment_hole_strokes() → Contador: 2 golpes
→ Sistema: Crea stroke #2 (pendiente)
→ Estado: Contador = 2, Stroke #1 evaluado ✅, Stroke #2 pendiente
```

**4. Jugador pide recomendación (evalúa stroke #2)**:
```
Jugador: "Dame una recomendación" (GPS: 40.44455, -3.87105)
→ Sistema: Evalúa stroke #2:
   - Distancia real: 45 metros
   - Calidad: 90
   - PERO: stroke #2 NO tenía club_used_id
   - NO se actualizan estadísticas
→ Sistema: Obtiene estadísticas → Sigue sin estadísticas
→ Sistema: Calcula recomendación con valores por defecto
→ Estado: Stroke #2 evaluado ✅, Sin estadísticas todavía
```

**5. Jugador pide recomendación y luego golpea con palo identificado**:
```
Jugador: "Dame una recomendación"
→ Sistema: "Te recomiendo utilizar hierro 7, 80 metros..."

Jugador: "He golpeado con hierro 7" (GPS: 40.44460, -3.87110)
→ Sistema: Evalúa stroke #3 (si existe):
   - Si stroke #3 tenía club_used_id = 7 (Hierro 7)
   - Actualiza estadísticas del Hierro 7:
     * average_distance_meters: 80.0 (primer golpe)
     * average_error_meters: 5.0
     * shots_recorded: 1
→ Sistema: increment_hole_strokes() → Contador: 4 golpes
→ Sistema: Crea stroke #4 con club_used_id = 7
→ Estado: Estadísticas del Hierro 7 creadas
```

**6. Próxima recomendación (con estadísticas)**:
```
Jugador: "Dame una recomendación" (GPS: 40.44465, -3.87115)
→ Sistema: Obtiene estadísticas → ENCUENTRA estadísticas del Hierro 7
→ Sistema: Usa estadísticas para calcular recomendación:
   - Distancia máxima: Basada en max_distance_meters del jugador
   - Recomendación de palo: Basada en average_distance_meters
   - Riesgo: Ajustado según average_error_meters
→ Sistema: "Te recomiendo utilizar hierro 7, 78 metros..." (personalizada)
→ Estado: Recomendación mejorada usando estadísticas
```

**7. Jugador golpea y el sistema aprende más**:
```
Jugador: "He golpeado" (GPS: 40.44470, -3.87120)
→ Sistema: Evalúa stroke #4:
   - Distancia real: 75 metros
   - Objetivo: 78 metros
   - Error: 3 metros
   - Calidad: 96
→ Sistema: Actualiza estadísticas del Hierro 7:
   - average_distance_meters: 80.0 * 0.7 + 75.0 * 0.3 = 78.5
   - average_error_meters: 5.0 * 0.7 + 3.0 * 0.3 = 4.4
   - shots_recorded: 2
→ Estado: Estadísticas mejoradas, próximas recomendaciones más precisas
```

---

## Puntos Clave

1. **El frontend SIEMPRE llama a `voice-command`**, nunca llama directamente a otros endpoints.

2. **Cuando el jugador dice "he golpeado"**, la posición GPS enviada es:
   - La posición **INICIAL** del nuevo stroke (donde está la bola antes de golpear)
   - La posición **FINAL** del stroke anterior pendiente (donde terminó la bola del golpe anterior)

3. **El sistema evalúa automáticamente el stroke anterior** cuando se crea un nuevo stroke, usando la posición GPS actual como posición final del stroke anterior.

4. **Las estadísticas se actualizan después de evaluar un stroke** que tiene `club_used_id`, usando media móvil ponderada (learning_rate = 0.3).

5. **El sistema aprende del jugador**:
   - Cada golpe evaluado mejora las estadísticas
   - Las estadísticas se usan para personalizar futuras recomendaciones
   - Más golpes = recomendaciones más precisas

6. **Cuando se setea el total de golpes de un hoyo**, se eliminan todos los strokes pendientes (el hoyo está finalizado).

7. **ANTES de evaluar, se validan las condiciones de sentido del golpe**:
   - Verifica que el `stroke_number` corresponde al golpe anterior
   - Verifica que la distancia es alcanzable
   - Verifica que la trayectoria es razonablemente recta
   - Si alguna validación falla, el golpe NO se evalúa

8. **Los golpes en el green NO se evalúan** y NO actualizan estadísticas.

9. **El sistema busca automáticamente golpes no evaluados** antes de procesar nuevas peticiones.

10. **La calidad del golpe se calcula basándose en el error de distancia** respecto a la distancia objetivo.

11. **Las estadísticas mejoran las recomendaciones**:
    - Distancia máxima alcanzable personalizada
    - Recomendación de palo basada en rendimiento real
    - Evaluación de riesgo ajustada según precisión del jugador

---

## Endpoints Relacionados

- `POST /match/<match_id>/voice-command`: Endpoint principal que enruta todas las peticiones
- `POST /match/<match_id>/increment-strokes`: Endpoint interno (no usado directamente por frontend)
- `POST /golf/trajectory-options-evol`: Endpoint para calcular recomendaciones (usado internamente)

---

## Tablas de Base de Datos Involucradas

1. **`match_hole_score`**: Almacena el número total de golpes por hoyo
2. **`match_stroke`**: Almacena cada golpe individual con posición inicial, evaluación, etc.
3. **`player_club_statistics`**: Almacena estadísticas de cada palo del jugador (perfil del jugador)
4. **`player_profile`**: Almacena el perfil general del jugador

---

## Notas de Implementación

- El flujo actual **requiere que el jugador proporcione la posición GPS** para crear y evaluar strokes.
- Las estadísticas se actualizan automáticamente cuando se evalúa un stroke con palo identificado.
- El sistema es **tolerante a errores**: si no se puede evaluar o actualizar estadísticas, no falla la petición principal.
- El sistema **aprende continuamente**: cada golpe mejora el perfil del jugador y las futuras recomendaciones.
- Las estadísticas se actualizan usando **media móvil ponderada** para dar más peso a los golpes recientes.
- El **learning_rate = 0.3** significa que cada nuevo golpe tiene un 30% de peso en la actualización de estadísticas.
