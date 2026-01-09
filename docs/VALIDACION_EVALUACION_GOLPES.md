# Validación de Evaluación de Golpes

Este documento explica las validaciones que se realizan antes de evaluar un golpe, para asegurar que el golpe tiene sentido y no es un error de GPS o datos inconsistentes.

## Contexto

Cuando un jugador confirma un golpeo (auto-incrementa el contador de golpes), el sistema crea un registro de `match_stroke` con la posición inicial de la bola. Este stroke queda pendiente de evaluación hasta que el jugador:

1. Pide otra recomendación (proporciona nueva posición GPS)
2. Confirma otro golpeo (proporciona nueva posición GPS)

En ese momento, el sistema debe evaluar el stroke anterior usando la nueva posición GPS como posición final de la bola.

## Problema

**¿Cómo sabemos que el siguiente golpeo es realmente el siguiente?**

La respuesta es: **Si el jugador confirmó el golpeo (auto-incrementó el contador), entonces la posición GPS del siguiente golpeo es donde finalizó el golpeo anterior.**

Sin embargo, antes de evaluar, debemos validar que el golpe tiene sentido para evitar errores de GPS o datos inconsistentes.

## Validaciones Implementadas

### 1. Validación de stroke_number

**Propósito**: Asegurar que el stroke pendiente es realmente el anterior al golpe actual.

**Validación**:
```python
stroke_number == current_strokes - 1
```

**Ejemplo**:
- Estado actual: Hoyo 4, 3 golpes
- Stroke pendiente: stroke_number = 2
- Validación: 2 == 3 - 1 ✅ (válido)
- Si stroke_number = 1: 1 != 3 - 1 ❌ (no válido, no se evalúa)

**Razón**: Si el stroke_number no corresponde, puede ser que:
- El stroke es de un golpe anterior que ya fue evaluado
- Hay un problema de sincronización
- El contador de golpes no está actualizado

### 2. Validación de Distancia Alcanzable

**Propósito**: Verificar que la distancia alcanzada es razonable según las capacidades del jugador.

**Validación**:
- Obtiene las estadísticas de todos los palos del jugador
- Encuentra la **mayor distancia promedio** entre todas las estadísticas
- Calcula el **máximo permitido**: `mayor_distancia_promedio * 1.3` (30% más)
- Verifica que `actual_distance <= máximo_permitido`
- Si no hay estadísticas del jugador, usa valor conservador por defecto (350m)

**Ejemplo 1 - Jugador con estadísticas**:
- Estadísticas del jugador:
  - Driver: average_distance_meters = 220m
  - Hierro 5: average_distance_meters = 150m
  - Hierro 7: average_distance_meters = 120m
- Mayor distancia promedio: 220m
- Máximo permitido: 220m * 1.3 = 286m
- Distancia alcanzada: 300m
- Validación: 300m > 286m ❌ (no válido, no se evalúa)

**Ejemplo 2 - Jugador sin estadísticas**:
- No hay estadísticas del jugador
- Máximo permitido: 350m (valor conservador por defecto)
- Distancia alcanzada: 400m
- Validación: 400m > 350m ❌ (no válido, no se evalúa)

**Razón**: 
- La validación se adapta a las capacidades reales del jugador
- Un jugador profesional puede alcanzar distancias mayores que un principiante
- Si la distancia excede el 30% de la mayor distancia promedio del jugador, probablemente es un error de GPS
- Evita evaluar golpes con datos incorrectos

### 3. Validación de Trayectoria Recta

**Propósito**: Verificar que la trayectoria del golpe es razonablemente recta (no hay desviaciones extremas).

**Validación**:
- Si hay `proposed_distance_meters`, calcula la distancia esperada al objetivo después del golpe
- Verifica que la desviación lateral no sea excesiva (máximo 50m adicionales)
- Si la desviación es más del doble de lo esperado, puede ser un error de GPS

**Ejemplo**:
- Distancia inicial al objetivo: 150m
- Distancia propuesta: 100m
- Distancia esperada final: 50m
- Distancia real final: 120m
- Desviación: 120m - 50m = 70m > 50m ❌ (no válido si ratio > 2.0)

**Razón**:
- Un golpe de golf típico se acerca al objetivo
- Si la desviación es excesiva, puede ser un error de GPS
- Evita evaluar golpes con trayectorias imposibles

### 4. Validación de Mismo Hoyo

**Propósito**: Asegurar que el stroke es del mismo hoyo que el golpe actual.

**Validación**:
- Ya verificado por `hole_id` en la búsqueda del stroke
- `get_last_unevaluated_stroke()` filtra por `hole_id`

**Razón**:
- Un stroke de un hoyo diferente no debe evaluarse con la posición GPS de otro hoyo
- Evita evaluaciones incorrectas entre hoyos

## Flujo de Validación

```
1. Buscar stroke pendiente
   ↓
2. ¿Existe stroke pendiente?
   ├─ NO → No evaluar
   └─ SÍ → Continuar
   ↓
3. Validar stroke_number
   ├─ ¿stroke_number == current_strokes - 1?
   ├─ NO → No evaluar (retornar None)
   └─ SÍ → Continuar
   ↓
4. Calcular distancia real
   ↓
5. Validar distancia alcanzable
   ├─ Obtener estadísticas del jugador
   ├─ Calcular máximo permitido: mayor_distancia_promedio * 1.3
   ├─ ¿actual_distance <= máximo_permitido?
   ├─ NO → No evaluar (retornar None)
   └─ SÍ → Continuar
   ↓
6. Validar trayectoria recta (si hay proposed_distance)
   ├─ ¿desviación razonable?
   ├─ NO → No evaluar (retornar None)
   └─ SÍ → Continuar
   ↓
7. Evaluar golpe (calcular calidad, errores, etc.)
```

## Implementación

### Método: `_validate_stroke_makes_sense()`

**Ubicación**: `kdi_back/src/kdi_back/domain/services/match_service.py`

**Parámetros**:
- `stroke`: Diccionario con información del stroke pendiente
- `ball_end_latitude`, `ball_end_longitude`: Posición final de la bola
- `hole_id`: ID del hoyo
- `current_strokes`: Número actual de golpes en el hoyo
- `user_id`: ID del usuario (opcional, para validación de estadísticas)

**Retorna**:
```python
{
    'is_valid': bool,  # Si el golpe tiene sentido
    'validation_errors': List[str],  # Lista de errores de validación
    'actual_distance': float  # Distancia real calculada
}
```

### Uso en `evaluate_stroke()`

```python
# VALIDACIÓN: Verificar que el golpe tiene sentido antes de evaluarlo
validation = self._validate_stroke_makes_sense(
    stroke=stroke,
    ball_end_latitude=ball_end_latitude,
    ball_end_longitude=ball_end_longitude,
    hole_id=hole_id,
    current_strokes=current_strokes,
    user_id=user_id
)

# Si la validación falla, retornar None (no evaluar)
if not validation['is_valid']:
    print(f"⚠️ Golpe no evaluado - Errores de validación: {', '.join(validation['validation_errors'])}")
    return None

# Usar la distancia calculada en la validación
actual_distance = validation['actual_distance']
```

## Casos de Uso

### Caso 1: Golpe Válido

**Estado**: Hoyo 4, 2 golpes
**Stroke pendiente**: stroke_number = 1, distancia propuesta = 100m
**Nueva posición GPS**: 80m del objetivo
**Distancia alcanzada**: 95m

**Validaciones**:
1. ✅ stroke_number (1) == current_strokes (2) - 1
2. ✅ actual_distance (95m) <= máximo_permitido (calculado según estadísticas)
3. ✅ Trayectoria razonable (se acercó al objetivo)

**Resultado**: ✅ Golpe evaluado

### Caso 2: Error de GPS (Distancia Excesiva)

**Estado**: Hoyo 4, 2 golpes
**Stroke pendiente**: stroke_number = 1, club_used_id = 5 (Wedge)
**Nueva posición GPS**: 500m de distancia

**Validaciones**:
1. ✅ stroke_number (1) == current_strokes (2) - 1
2. ❌ actual_distance (500m) > máximo_permitido (calculado según estadísticas)

**Resultado**: ❌ Golpe NO evaluado (error de GPS detectado)

### Caso 3: Stroke Number Incorrecto

**Estado**: Hoyo 4, 3 golpes
**Stroke pendiente**: stroke_number = 1 (golpe antiguo)

**Validaciones**:
1. ❌ stroke_number (1) != current_strokes (3) - 1 (esperado: 2)

**Resultado**: ❌ Golpe NO evaluado (stroke no corresponde al golpe anterior)

### Caso 4: Trayectoria Imposible

**Estado**: Hoyo 4, 2 golpes
**Stroke pendiente**: stroke_number = 1, distancia propuesta = 100m
**Nueva posición GPS**: 200m del objetivo (más lejos que antes)

**Validaciones**:
1. ✅ stroke_number (1) == current_strokes (2) - 1
2. ✅ actual_distance (150m) <= máximo_permitido (calculado según estadísticas)
3. ❌ Trayectoria: la bola se alejó del objetivo (desviación excesiva)

**Resultado**: ❌ Golpe NO evaluado (trayectoria imposible)

## Beneficios

1. **Evita errores de GPS**: No evalúa golpes con posiciones GPS incorrectas
2. **Mantiene consistencia**: Solo evalúa golpes que corresponden al estado actual
3. **Mejora calidad de datos**: Las estadísticas se basan en golpes válidos
4. **Detecta problemas**: Identifica errores de sincronización o datos inconsistentes

## Notas de Implementación

- Las validaciones son **tolerantes a errores**: Si hay un error obteniendo estadísticas, se usa un valor conservador por defecto
- Los mensajes de error se registran en los logs para debugging
- Si un golpe no pasa las validaciones, simplemente no se evalúa (no falla la petición principal)
- En el futuro, se puede mejorar la validación de distancia usando estadísticas reales del jugador

