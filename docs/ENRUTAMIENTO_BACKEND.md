# Enrutamiento en el Backend - Voice Command

## Resumen Ejecutivo

El backend utiliza un sistema de enrutamiento basado en **clasificación de intenciones con IA** que analiza el query en lenguaje natural y enruta a handlers especializados.

## Flujo de Enrutamiento

```
POST /match/<match_id>/voice-command
  ↓
VoiceService.process_voice_command()
  ↓
classify_intent(query) [IA - Amazon Nova Lite]
  ↓
Obtener handler: _handle_{intent}
  ↓
Ejecutar handler especializado
  ↓
Retornar respuesta en lenguaje natural
```

## Clasificación de Intenciones

**Archivo**: `kdi_back/src/kdi_back/infrastructure/agents/intent_classifier_agent.py`

El sistema utiliza **Amazon Nova Lite** para clasificar intenciones. Las intenciones disponibles son:

| Intención | Descripción | Ejemplos de Query |
|-----------|-------------|-------------------|
| `recommend_shot` | Recomendación de palo/golpe | "¿Qué palo debo usar?", "¿Qué me recomiendas?", "Recomiéndame un golpe" |
| `register_stroke` | Registrar golpe | "He dado un golpe", "Registra mi golpe", "He golpeado la bola" |
| `check_distance` | Consultar distancia | "¿A qué distancia estoy?", "¿Cuántos metros hay hasta la bandera?" |
| `check_obstacles` | Consultar obstáculos | "¿Qué obstáculos hay?", "¿Hay bunkers o agua?" |
| `check_terrain` | Consultar terreno | "¿En qué terreno estoy?", "¿Estoy en el bunker?" |
| `complete_hole` | Completar hoyo | "He completado el hoyo", "Terminé este hoyo", "Finalizar hoyo" |
| `record_hole_score_direct` | Registrar resultado directamente | "Completa el hoyo con 4 golpes", "Registra 5 golpes en este hoyo" |
| `update_hole_score` | Corregir resultado de un hoyo | "Corrige el resultado del hoyo 2 con 3 golpes", "Cambia el hoyo 5 a 4 golpes" |
| `check_ranking` | Consultar ranking | "¿Cómo voy?", "¿Cuál es mi posición?", "¿Quién va ganando?" |
| `check_hole_stats` | Estadísticas del hoyo | "¿Cuántos golpes llevo?", "¿Cuál es mi puntuación en este hoyo?" |
| `check_hole_info` | Información del hoyo | "¿Qué hoyo es este?", "¿Cuál es el par?", "Información del hoyo" |
| `check_weather` | Consultar clima | "¿Qué tiempo hace?", "¿Hay viento?", "Condiciones meteorológicas" |
| `require_hole_confirmation` | Requiere confirmación de hoyos | Respuesta automática cuando hay hoyos sin completar |

**Fallback**: Si la intención no se puede clasificar o no es válida, se usa `recommend_shot` como fallback.

## Handlers Implementados

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py`

### 1. `_handle_recommend_shot()` ✅

**Intención**: `recommend_shot`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()`:
   - Prioriza estado persistido del partido (si hay `match_id` y `user_id`)
   - Fallback a identificación por GPS si no hay estado persistido
2. Obtiene estadísticas del jugador (si hay `user_id`)
4. Ejecuta algoritmo evolutivo:
   - `bola_menos_10m_optimal_shot()` - Busca optimal_shots cercanos
   - `find_strategic_shot()` - Busca strategic_points (incluyendo green)
   - `evaluacion_final()` - Evalúa y ordena trayectorias
5. Construye respuesta en lenguaje natural con:
   - Distancia al objetivo
   - Palo recomendado
   - Tipo de swing
   - Obstáculos
   - Nivel de riesgo

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `match_service.get_match_state()` - Obtener estado persistido
- `golf_service.get_hole_by_course_and_number()` - Obtener información del hoyo
- `golf_service.identify_hole_by_ball_position()` - Identificar hoyo desde GPS (fallback)
- `player_service.player_repository.get_player_profile_by_user_id()` - Perfil del jugador
- `golf_service.bola_menos_10m_optimal_shot()` - Algoritmo evolutivo
- `golf_service.find_strategic_shot()` - Puntos estratégicos
- `golf_service.evaluacion_final()` - Evaluación final

**Endpoint Interno**: Usa lógica de `/golf/trajectory-options-evol` internamente

---

### 2. `_handle_register_stroke()` ✅

**Intención**: `register_stroke`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Llama a `match_service.increment_hole_strokes()` para incrementar golpes
3. Retorna confirmación con número de golpes actual

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `match_service.increment_hole_strokes()` - Incrementar golpes

**Endpoint Interno**: Usa lógica de `/match/<match_id>/increment-strokes` internamente

---

### 3. `_handle_check_distance()` ✅

**Intención**: `check_distance`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Calcula distancia a la bandera usando `golf_service.calculate_distance_to_hole()`
3. Retorna distancia en metros y yardas

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `golf_service.calculate_distance_to_hole()` - Calcular distancia

---

### 4. `_handle_check_obstacles()` ✅

**Intención**: `check_obstacles`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Busca obstáculos entre la bola y la bandera usando `golf_service.find_obstacles_between_ball_and_flag()`
3. Retorna lista de obstáculos encontrados

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `golf_service.find_obstacles_between_ball_and_flag()` - Buscar obstáculos

---

### 5. `_handle_check_terrain()` ✅

**Intención**: `check_terrain`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Determina tipo de terreno usando `golf_service.determine_terrain_type()`
3. Verifica si está en el green usando `golf_service.is_ball_on_green()`
4. Retorna tipo de terreno (bunker, agua, rough, green, fairway, etc.)

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `golf_service.determine_terrain_type()` - Determinar terreno
- `golf_service.is_ball_on_green()` - Verificar si está en green

---

### 6. `_handle_complete_hole()` ✅

**Intención**: `complete_hole`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Llama a `match_service.complete_hole()` para completar el hoyo
3. Obtiene ranking actualizado
4. Retorna resumen con:
   - Golpes en el hoyo
   - Total de golpes en el partido
   - Posición en el ranking

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `match_service.complete_hole()` - Completar hoyo (actualiza estado persistido automáticamente)

**Endpoint Interno**: Usa lógica de `/match/<match_id>/score` internamente

**Nota**: Este handler actualiza automáticamente el `current_hole_number` en el estado persistido.

---

### 7. `_handle_record_hole_score_direct()` ✅

**Intención**: `record_hole_score_direct`

**Proceso**:
1. Extrae número de golpes del query usando `_extract_hole_and_strokes_from_query()`
2. Si no se especifica el hoyo, usa el hoyo actual del estado persistido
3. Valida que los golpes sean válidos (> 0)
4. Registra el score usando `match_service.record_hole_score()`
5. Retorna confirmación con comparación con el par

**Servicios Usados**:
- `_extract_hole_and_strokes_from_query()` - Extraer información del query
- `match_service.get_match_state()` - Obtener hoyo actual
- `match_service.record_hole_score()` - Registrar score
- `golf_service.get_hole_by_course_and_number()` - Obtener información del hoyo

**Ejemplos de uso**:
- "Completa el hoyo con 4 golpes" → Registra 4 golpes en el hoyo actual
- "Registra 5 golpes en este hoyo" → Registra 5 golpes en el hoyo actual

---

### 8. `_handle_update_hole_score()` ✅

**Intención**: `update_hole_score`

**Proceso**:
1. Extrae número de hoyo y golpes del query usando `_extract_hole_and_strokes_from_query()`
2. Valida que se especifique tanto el hoyo como los golpes
3. Valida que los golpes sean válidos (> 0)
4. Registra/actualiza el score usando `match_service.record_hole_score()`
5. Retorna confirmación con comparación con el par

**Servicios Usados**:
- `_extract_hole_and_strokes_from_query()` - Extraer información del query
- `match_service.record_hole_score()` - Registrar/actualizar score
- `golf_service.get_hole_by_course_and_number()` - Obtener información del hoyo

**Ejemplos de uso**:
- "Corrige el resultado del hoyo 2 con 3 golpes" → Actualiza hoyo 2 a 3 golpes
- "Cambia el hoyo 5 a 4 golpes" → Actualiza hoyo 5 a 4 golpes

**Nota**: Este handler permite corregir el resultado de cualquier hoyo, independientemente del hoyo actual.

---

### 9. `_handle_check_ranking()` ✅

**Intención**: `check_ranking`

**Proceso**:
1. Obtiene leaderboard del partido usando `match_service.get_match_leaderboard()`
2. Encuentra posición del usuario
3. Calcula diferencia con el líder
4. Retorna posición, total de golpes y diferencia con el líder

**Servicios Usados**:
- `match_service.get_match_leaderboard()` - Obtener clasificación

**Endpoint Interno**: Usa lógica de `/match/<match_id>/leaderboard` internamente

---

### 10. `_handle_check_hole_stats()` ✅

**Intención**: `check_hole_stats`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Obtiene golpes del jugador en el hoyo usando `match_service.match_repository.get_hole_strokes_for_player()`
3. Compara con el par del hoyo
4. Retorna estadísticas: golpes, par, diferencia con par

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS
- `match_service.match_repository.get_hole_strokes_for_player()` - Obtener golpes

---

### 11. `_handle_check_hole_info()` ✅

**Intención**: `check_hole_info`

**Proceso**:
1. Obtiene información del hoyo usando `_get_hole_info_from_state_or_gps()` (prioriza estado persistido)
2. Obtiene información del hoyo (número, par, longitud, nombre del campo)
3. Retorna información básica del hoyo

**Servicios Usados**:
- `_get_hole_info_from_state_or_gps()` - Helper que obtiene hoyo desde estado persistido o GPS

---

### 12. `_handle_check_weather()` ✅

**Intención**: `check_weather`

**Proceso**:
1. Importa `weather_agent.get_weather_response()`
2. Construye query de clima basada en coordenadas GPS
3. Obtiene información del clima
4. Retorna condiciones meteorológicas

**Servicios Usados**:
- `weather_agent.get_weather_response()` - Obtener clima

**Nota**: Requiere acceso al servicio de clima. Si falla, retorna mensaje de error.

---

## Validación de Consistencia de Hoyos

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py` (líneas 106-140)

Antes de ejecutar cualquier handler, el sistema valida la consistencia de hoyos:

1. **Detección de hoyo mencionado**: Extrae el número de hoyo del query si se menciona usando `_extract_mentioned_hole_number()`
2. **Verificación de consistencia**: Si el hoyo mencionado es mayor que el hoyo actual del estado:
   - Verifica si hay hoyos sin completar entre el actual y el mencionado usando `_check_hole_consistency()`
   - Si hay hoyos sin completar, retorna una respuesta especial pidiendo confirmación
3. **Respuesta de confirmación**: Si se detectan hoyos sin completar:
   - **Un hoyo**: "Antes de continuar, necesito que confirmes el resultado del hoyo X. ¿Cuántos golpes realizaste en el hoyo X?"
   - **Múltiples hoyos**: "Antes de continuar, necesito que confirmes el resultado de los hoyos X, Y y Z. ¿Cuántos golpes realizaste en cada uno de estos hoyos?"

**Intención especial**: `require_hole_confirmation`
- Se retorna cuando hay inconsistencias detectadas
- Incluye en `data`:
  - `missing_holes`: Lista de hoyos sin completar
  - `current_hole`: Hoyo actual del estado
  - `target_hole`: Hoyo objetivo mencionado
  - `requires_confirmation`: True

**Ejemplo de flujo**:
```
Estado: Jugador en hoyo 5
Query: "Dame una recomendación para el hoyo 8"
→ Detecta hoyo 8 mencionado
→ Verifica: hay hoyos 5, 6, 7 sin completar
→ Retorna: "Antes de continuar, necesito que confirmes el resultado de los hoyos 5, 6 y 7..."
```

## Mecanismo de Enrutamiento

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py` (líneas 101-170)

```python
# 1. Clasificar intención con IA
intent_result = classify_intent(query)
intent = intent_result['intent']
confidence = intent_result['confidence']

# 2. Obtener handler dinámicamente
handler_method = getattr(self, f'_handle_{intent}', None)

# 3. Si no hay handler, usar fallback
if not handler_method:
    intent = 'recommend_shot'
    handler_method = self._handle_recommend_shot

# 4. Ejecutar handler
result = handler_method(
    user_id=user_id,
    match_id=match_id,
    course_id=course_id,
    latitude=latitude,
    longitude=longitude,
    query=query
)

# 5. Retornar respuesta
return {
    'response': result['response'],
    'intent': intent,
    'confidence': confidence,
    'data': result.get('data', {})
}
```

## Servicios Utilizados

### GolfService
- `get_hole_by_course_and_number()` - Obtener información del hoyo
- `identify_hole_by_ball_position()` - Identificar hoyo desde GPS
- `calculate_distance_to_hole()` - Calcular distancia
- `find_obstacles_between_ball_and_flag()` - Buscar obstáculos
- `determine_terrain_type()` - Determinar terreno
- `is_ball_on_green()` - Verificar si está en green
- `bola_menos_10m_optimal_shot()` - Algoritmo evolutivo (paso 1)
- `find_strategic_shot()` - Algoritmo evolutivo (paso 2)
- `evaluacion_final()` - Algoritmo evolutivo (paso 3)

### MatchService
- `get_match_state()` - Obtener estado persistido del partido
- `increment_hole_strokes()` - Incrementar golpes
- `complete_hole()` - Completar hoyo (actualiza estado persistido)
- `get_match_leaderboard()` - Obtener clasificación
- `match_repository.get_hole_strokes_for_player()` - Obtener golpes del jugador

### PlayerService
- `player_repository.get_player_profile_by_user_id()` - Perfil del jugador
- `player_repository.get_player_club_statistics()` - Estadísticas de palos

## Uso del Estado Persistido

**Importante**: Todos los handlers que necesitan identificar el hoyo ahora usan el **estado persistido** cuando está disponible a través de la función helper `_get_hole_info_from_state_or_gps()`.

### Función Helper: `_get_hole_info_from_state_or_gps()`

Esta función centraliza la lógica de obtención del hoyo y:
1. **Prioriza el estado persistido**: Si hay `match_id` y `user_id`, obtiene `current_hole_number` del estado persistido
2. **Fallback a GPS**: Si no hay estado persistido disponible, identifica el hoyo desde coordenadas GPS
3. **Manejo de errores**: Si falla la obtención del estado, automáticamente usa GPS como respaldo

### Handlers que Usan Estado Persistido

Todos los siguientes handlers usan `_get_hole_info_from_state_or_gps()`:
- ✅ `_handle_recommend_shot()` - Usa estado persistido
- ✅ `_handle_register_stroke()` - Usa estado persistido
- ✅ `_handle_check_distance()` - Usa estado persistido
- ✅ `_handle_check_obstacles()` - Usa estado persistido
- ✅ `_handle_check_terrain()` - Usa estado persistido
- ✅ `_handle_complete_hole()` - Usa estado persistido (y actualiza estado)
- ✅ `_handle_check_hole_stats()` - Usa estado persistido
- ✅ `_handle_check_hole_info()` - Usa estado persistido

### Handlers que No Necesitan Identificar Hoyo

- `_handle_check_ranking()` - No identifica hoyos (usa solo `match_id`)
- `_handle_check_weather()` - No identifica hoyos (usa solo coordenadas GPS)

## Resumen de Enrutamiento

| Intención | Handler | Usa Estado Persistido | Servicios Principales |
|-----------|---------|----------------------|----------------------|
| `recommend_shot` | `_handle_recommend_shot()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, GolfService (algoritmo evolutivo), MatchService, PlayerService |
| `register_stroke` | `_handle_register_stroke()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, MatchService |
| `check_distance` | `_handle_check_distance()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, GolfService |
| `check_obstacles` | `_handle_check_obstacles()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, GolfService |
| `check_terrain` | `_handle_check_terrain()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, GolfService |
| `complete_hole` | `_handle_complete_hole()` | ✅ Sí (y actualiza estado) | `_get_hole_info_from_state_or_gps()`, MatchService |
| `record_hole_score_direct` | `_handle_record_hole_score_direct()` | ✅ Sí | `_extract_hole_and_strokes_from_query()`, MatchService |
| `update_hole_score` | `_handle_update_hole_score()` | ✅ Sí | `_extract_hole_and_strokes_from_query()`, MatchService |
| `check_ranking` | `_handle_check_ranking()` | N/A | MatchService |
| `check_hole_stats` | `_handle_check_hole_stats()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, MatchService |
| `check_hole_info` | `_handle_check_hole_info()` | ✅ Sí | `_get_hole_info_from_state_or_gps()`, GolfService |
| `check_weather` | `_handle_check_weather()` | N/A | WeatherAgent |
| `require_hole_confirmation` | (Respuesta automática) | N/A | Validación de consistencia |

## Implementación de la Función Helper

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py` (líneas 139-188)

```python
def _get_hole_info_from_state_or_gps(
    self,
    match_id: int,
    user_id: int,
    course_id: int,
    latitude: float,
    longitude: float
) -> Optional[Dict[str, Any]]:
    """
    Obtiene información del hoyo desde el estado persistido del partido o desde GPS.
    
    Prioriza el estado persistido si está disponible, usa GPS como fallback.
    """
    # Intentar obtener el estado persistido del partido
    if match_id and user_id:
        try:
            match_state = self.match_service.get_match_state(match_id, user_id)
            
            if match_state:
                # Usar el estado persistido del partido
                course_id = match_state['course_id']
                hole_number = match_state['current_hole_number']
                hole_id = match_state['current_hole_id']
                
                # Obtener información completa del hoyo
                hole_info = self.golf_service.get_hole_by_course_and_number(
                    course_id, hole_number
                )
                
                if hole_info:
                    return hole_info
        except Exception as e:
            print(f"Advertencia: No se pudo obtener el estado del partido, usando GPS: {e}")
    
    # Fallback: Identificar el hoyo desde coordenadas GPS
    try:
        hole_info = self.golf_service.identify_hole_by_ball_position(
            latitude, longitude
        )
        return hole_info
    except Exception as e:
        print(f"Advertencia: No se pudo identificar el hoyo desde GPS: {e}")
        return None
```

## Beneficios de la Implementación Actual

1. ✅ **Consistencia**: Todos los handlers usan el mismo método para obtener el hoyo
2. ✅ **Precisión**: Prioriza el estado persistido sobre la identificación por GPS
3. ✅ **Mantenibilidad**: Lógica centralizada en una función helper reutilizable
4. ✅ **Robustez**: Fallback automático a GPS si el estado persistido no está disponible
5. ✅ **Resuelve el problema original**: Elimina la identificación incorrecta del hoyo cuando el jugador está en el tee de un hoyo que está geográficamente cerca del green de otro hoyo

## Mejoras Futuras Recomendadas

1. **Caché de resultados**: Considerar caché para consultas frecuentes como distancia o obstáculos.

2. **Manejo de errores mejorado**: Agregar más validaciones y mensajes de error más descriptivos.

3. **Logging estructurado**: Mejorar el logging para facilitar el debugging y monitoreo.

