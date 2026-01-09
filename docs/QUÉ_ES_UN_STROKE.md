# ¿Qué es un Stroke?

## Definición

Un **stroke** (golpe) es un registro individual y detallado de **un golpe específico** que un jugador realiza durante un partido de golf.

## Diferencia entre Stroke y Contador de Golpes

Es importante entender la diferencia:

### Contador de Golpes (`match_hole_score`)
- **Qué es**: Un número que cuenta cuántos golpes ha dado el jugador en un hoyo
- **Ejemplo**: "El jugador lleva 3 golpes en el hoyo 5"
- **Dónde se almacena**: Tabla `match_hole_score`
- **Información**: Solo el número total de golpes

### Stroke (`match_stroke`)
- **Qué es**: Un registro detallado de **un golpe individual** con toda su información
- **Ejemplo**: "El golpe #2 del hoyo 5, realizado con hierro 7, desde posición (40.44445, -3.87095)"
- **Dónde se almacena**: Tabla `match_stroke`
- **Información**: Posición inicial, palo usado, distancia propuesta, evaluación, etc.

## Analogía

Piensa en el contador de golpes como el **marcador del partido** (como el marcador de un partido de fútbol que solo muestra 2-1), mientras que un stroke es como un **replay detallado de una jugada específica** (con cámara lenta, ángulos, estadísticas, etc.).

## Información que Contiene un Stroke

Un stroke almacena:

### Información Inicial (cuando se crea)
- **`stroke_number`**: Número del golpe (1, 2, 3, etc.)
- **`ball_start_latitude`**: Latitud GPS donde estaba la bola antes del golpe
- **`ball_start_longitude`**: Longitud GPS donde estaba la bola antes del golpe
- **`club_used_id`**: ID del palo que se usó (opcional)
- **`proposed_club_id`**: ID del palo que se recomendó usar (opcional)
- **`proposed_distance_meters`**: Distancia que se intentó alcanzar (opcional)
- **`trajectory_type`**: Tipo de trayectoria (conservadora, riesgo, óptima) (opcional)
- **`evaluated`**: `FALSE` (pendiente de evaluación)

### Información de Evaluación (cuando se evalúa)
- **`ball_end_latitude`**: Latitud GPS donde terminó la bola después del golpe
- **`ball_end_longitude`**: Longitud GPS donde terminó la bola después del golpe
- **`ball_end_distance_meters`**: Distancia real alcanzada
- **`evaluation_quality`**: Calidad del golpe (0-100)
- **`evaluation_distance_error`**: Error de distancia (diferencia entre objetivo y real)
- **`evaluation_direction_error`**: Error de dirección (desviación del objetivo)
- **`evaluated`**: `TRUE` (ya evaluado)
- **`evaluated_at`**: Timestamp de cuándo se evaluó

## Ejemplo Práctico

### Escenario: Jugador en el hoyo 5

**Golpe 1**:
- Jugador está en el tee (posición GPS: 40.44445, -3.87095)
- Sistema recomienda: Driver, 200 metros
- Jugador golpea
- **Contador**: 1 golpe
- **Stroke #1 creado**:
  ```json
  {
    "stroke_number": 1,
    "ball_start_latitude": 40.44445,
    "ball_start_longitude": -3.87095,
    "proposed_club_id": 1,  // Driver
    "proposed_distance_meters": 200,
    "evaluated": false
  }
  ```

**Golpe 2** (jugador se mueve a nueva posición):
- Jugador está en nueva posición (40.44450, -3.87100)
- Sistema evalúa el stroke #1:
  ```json
  {
    "ball_end_latitude": 40.44450,
    "ball_end_longitude": -3.87100,
    "ball_end_distance_meters": 195,
    "evaluation_quality": 97.5,  // Muy bueno (solo 5m de error)
    "evaluation_distance_error": 5,
    "evaluated": true
  }
  ```
- Sistema recomienda: Hierro 7, 80 metros
- Jugador golpea
- **Contador**: 2 golpes
- **Stroke #2 creado**:
  ```json
  {
    "stroke_number": 2,
    "ball_start_latitude": 40.44450,
    "ball_start_longitude": -3.87100,
    "club_used_id": 7,  // Hierro 7
    "proposed_distance_meters": 80,
    "evaluated": false
  }
  ```

## ¿Para Qué Sirve un Stroke?

Los strokes se usan para:

1. **Evaluar el rendimiento del jugador**:
   - ¿Qué tan preciso fue el golpe?
   - ¿Alcanzó la distancia objetivo?
   - ¿Cuál fue la calidad del golpe?

2. **Actualizar estadísticas del palo**:
   - Distancia promedio alcanzada con cada palo
   - Precisión del jugador con cada palo
   - Mejora de las recomendaciones futuras

3. **Análisis del partido**:
   - Ver el historial completo de golpes
   - Identificar patrones de juego
   - Mejorar estrategia

4. **Validación de datos**:
   - Verificar que los golpes tienen sentido
   - Detectar errores de GPS
   - Asegurar consistencia de datos

## Ciclo de Vida de un Stroke

```
1. CREACIÓN
   └─ Cuando se llama a /increment-strokes con posición GPS inicial
   └─ Estado: evaluated = FALSE
   └─ Información: Posición inicial, palo, distancia propuesta

2. PENDIENTE DE EVALUACIÓN
   └─ Stroke existe pero aún no se sabe dónde terminó la bola
   └─ Estado: evaluated = FALSE

3. EVALUACIÓN
   └─ Cuando el jugador proporciona nueva posición GPS (siguiente golpe o recomendación)
   └─ Sistema calcula: distancia real, calidad, errores
   └─ Estado: evaluated = TRUE
   └─ Información: Posición final, evaluación completa

4. ACTUALIZACIÓN DE ESTADÍSTICAS
   └─ Si el stroke tiene palo usado y calidad evaluada
   └─ Se actualizan las estadísticas del palo del jugador
```

## Cuándo se Crea un Stroke

**IMPORTANTE**: Un stroke **NO se crea automáticamente** cuando el jugador dice "he golpeado".

### Se crea cuando:
- Se llama al endpoint `/match/<match_id>/increment-strokes` con:
  - `ball_start_latitude`
  - `ball_start_longitude`
  - (Opcionalmente) `club_used_id`, `proposed_distance_meters`, etc.

### NO se crea cuando:
- El jugador solo dice "he golpeado" vía voice-command
- Solo se incrementa el contador de golpes
- No hay información GPS de la posición inicial

## Ejemplo de Código

### Crear un Stroke

```python
# En /match/<match_id>/increment-strokes
stroke_created = match_service.create_stroke(
    match_id=match_id,
    user_id=user_id,
    course_id=course_id,
    hole_number=hole_number,
    ball_start_latitude=40.44445,  # Posición GPS inicial
    ball_start_longitude=-3.87095,
    stroke_number=1,  # Primer golpe
    club_used_id=1,  # Driver
    proposed_distance_meters=200
)
```

### Evaluar un Stroke

```python
# Cuando el jugador proporciona nueva posición GPS
stroke_evaluation = match_service.evaluate_stroke(
    match_id=match_id,
    user_id=user_id,
    course_id=course_id,
    hole_number=hole_number,
    ball_end_latitude=40.44450,  # Nueva posición GPS (donde terminó la bola)
    ball_end_longitude=-3.87100,
    current_strokes=2  # Para validar que es el stroke correcto
)
```

## Resumen

- **Stroke** = Registro detallado de un golpe individual
- **Contador** = Número total de golpes en un hoyo
- Un stroke contiene: posición inicial, palo, distancia propuesta, evaluación, etc.
- Se crea cuando se proporciona posición GPS inicial
- Se evalúa cuando se proporciona posición GPS final
- Se usa para: evaluar rendimiento, actualizar estadísticas, análisis

