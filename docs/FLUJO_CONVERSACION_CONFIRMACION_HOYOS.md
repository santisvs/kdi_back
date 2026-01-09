# Flujo de Conversación para Confirmación de Hoyos

## Problema

Cuando un jugador tiene guardado en su estado que está jugando el hoyo X pero pide información o realiza una acción para el hoyo Y (donde Y > X), el sistema necesita:

1. Detectar la inconsistencia
2. Identificar los hoyos sin completar entre X e Y
3. Solicitar confirmación de los resultados de esos hoyos
4. Procesar las confirmaciones
5. Continuar con la petición original

## Implementación Actual

### 1. Detección de Inconsistencia

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py`

El sistema detecta inconsistencias en `process_voice_command()` antes de ejecutar cualquier handler:

```python
# Detectar si el query menciona un hoyo específico
mentioned_hole = self._extract_mentioned_hole_number(query)

# Si se menciona un hoyo específico y es diferente al actual, verificar consistencia
if mentioned_hole:
    match_state = self.match_service.get_match_state(match_id, user_id)
    if match_state:
        current_hole = match_state['current_hole_number']
        if mentioned_hole > current_hole:
            # Verificar si hay hoyos sin completar
            consistency = self._check_hole_consistency(
                match_id, user_id, course_id, mentioned_hole
            )
            
            if not consistency['is_consistent']:
                # Retornar respuesta especial pidiendo confirmación
                ...
```

### 2. Respuesta de Confirmación

Cuando se detectan hoyos sin completar, el sistema retorna una respuesta especial:

**Estructura de respuesta**:
```json
{
    "response": "Antes de continuar, necesito que confirmes el resultado de los hoyos 5, 6 y 7. ¿Cuántos golpes realizaste en cada uno de estos hoyos?",
    "intent": "require_hole_confirmation",
    "confidence": 1.0,
    "data": {
        "missing_holes": [5, 6, 7],
        "current_hole": 5,
        "target_hole": 8,
        "requires_confirmation": true
    }
}
```

**Mensajes según cantidad de hoyos**:
- **Un hoyo**: "Antes de continuar, necesito que confirmes el resultado del hoyo X. ¿Cuántos golpes realizaste en el hoyo X?"
- **Múltiples hoyos**: "Antes de continuar, necesito que confirmes el resultado de los hoyos X, Y y Z. ¿Cuántos golpes realizaste en cada uno de estos hoyos?"

## Flujo de Conversación Propuesto

### Opción 1: Confirmación Múltiple en una Respuesta (Implementación Actual)

**Ventajas**:
- Rápido: el jugador puede confirmar todos los hoyos de una vez
- Eficiente: menos interacciones

**Desventajas**:
- Puede ser confuso si hay muchos hoyos
- El jugador debe recordar todos los resultados

**Ejemplo**:
```
Jugador: "Dame una recomendación para el hoyo 8"
Sistema: "Antes de continuar, necesito que confirmes el resultado de los hoyos 5, 6 y 7. ¿Cuántos golpes realizaste en cada uno de estos hoyos?"
Jugador: "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes, hoyo 7 con 3 golpes"
Sistema: [Registra los scores] "Perfecto. Ahora, para el hoyo 8, te recomiendo..."
```

### Opción 2: Confirmación Secuencial (Mejora Futura)

**Ventajas**:
- Más natural: una pregunta a la vez
- Menos confuso para el jugador
- Permite validar cada respuesta antes de continuar

**Desventajas**:
- Más interacciones
- Requiere mantener estado de conversación

**Ejemplo**:
```
Jugador: "Dame una recomendación para el hoyo 8"
Sistema: "Antes de continuar, necesito que confirmes el resultado del hoyo 5. ¿Cuántos golpes realizaste en el hoyo 5?"
Jugador: "4 golpes"
Sistema: [Registra score] "Hoyo 5 registrado con 4 golpes. Ahora, ¿cuántos golpes realizaste en el hoyo 6?"
Jugador: "5 golpes"
Sistema: [Registra score] "Hoyo 6 registrado con 5 golpes. Finalmente, ¿cuántos golpes realizaste en el hoyo 7?"
Jugador: "3 golpes"
Sistema: [Registra score] "Hoyo 7 registrado con 3 golpes. Perfecto. Ahora, para el hoyo 8, te recomiendo..."
```

## Implementación de Confirmación Múltiple

### Procesamiento de Respuesta con Múltiples Hoyos

Cuando el jugador responde con múltiples confirmaciones, el sistema debe:

1. **Extraer cada confirmación** del query
2. **Validar** que se mencionaron todos los hoyos requeridos
3. **Registrar** cada score
4. **Continuar** con la petición original

**Handler propuesto**: `_handle_require_hole_confirmation()`

```python
def _handle_require_hole_confirmation(
    self,
    user_id: int,
    match_id: int,
    course_id: int,
    latitude: float,
    longitude: float,
    query: str
) -> Dict[str, Any]:
    """
    Maneja respuestas a solicitudes de confirmación de hoyos.
    
    El query debe contener confirmaciones en formato:
    - "Hoyo X con Y golpes"
    - "Hoyo X: Y golpes"
    - "X golpes en el hoyo Y"
    """
    # Obtener los hoyos que faltan del contexto anterior
    # (Esto requeriría mantener estado de conversación)
    
    # Extraer todas las confirmaciones del query
    confirmations = self._extract_multiple_hole_confirmations(query)
    
    # Validar que se confirmaron todos los hoyos requeridos
    # Registrar cada score
    # Retornar confirmación y continuar con petición original
```

### Problema: Estado de Conversación

**Desafío**: El sistema actual es stateless. No mantiene el contexto de la conversación anterior.

**Soluciones posibles**:

1. **Incluir contexto en la respuesta**:
   - El frontend puede almacenar temporalmente los hoyos que faltan
   - Cuando el jugador responde, el frontend puede incluir esta información en el siguiente request

2. **Usar sesión/conversación ID**:
   - Crear un ID de conversación para rastrear el contexto
   - Almacenar temporalmente el estado de la conversación

3. **Re-detectar en cada respuesta**:
   - En cada respuesta, verificar nuevamente si hay hoyos sin completar
   - Si el jugador menciona un hoyo, intentar registrar su score

## Recomendación: Implementación Híbrida

### Fase 1: Implementación Actual (Confirmación Múltiple)

**Cómo funciona**:
1. Sistema detecta inconsistencias y pide confirmación de todos los hoyos
2. Jugador responde con todas las confirmaciones en un solo mensaje
3. Sistema extrae todas las confirmaciones y las registra
4. Sistema continúa con la petición original

**Handler necesario**: `_handle_require_hole_confirmation()`

Este handler debe:
- Detectar que la intención es `require_hole_confirmation` (o detectar múltiples confirmaciones)
- Extraer todas las confirmaciones del query
- Registrar cada score
- Si se completaron todos los hoyos requeridos, continuar con la petición original (o informar al jugador que puede repetir su petición)

### Fase 2: Mejora Futura (Confirmación Secuencial)

Para implementar confirmación secuencial, se necesitaría:

1. **Sistema de estado de conversación**:
   - Almacenar temporalmente el contexto de la conversación
   - Mantener lista de hoyos pendientes de confirmación
   - Rastrear el estado actual de la conversación

2. **Handler mejorado**:
   - Detectar si es la primera pregunta o una respuesta
   - Si es primera pregunta, pedir confirmación del primer hoyo
   - Si es respuesta, validar, registrar, y preguntar por el siguiente
   - Si se completaron todos, continuar con petición original

## Ejemplo de Implementación: Confirmación Múltiple

### Handler `_handle_require_hole_confirmation()`

```python
def _handle_require_hole_confirmation(
    self,
    user_id: int,
    match_id: int,
    course_id: int,
    latitude: float,
    longitude: float,
    query: str
) -> Dict[str, Any]:
    """
    Maneja respuestas a solicitudes de confirmación de hoyos.
    
    El query debe contener confirmaciones en formato:
    - "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes"
    - "5: 4 golpes, 6: 5 golpes"
    """
    # Extraer todas las confirmaciones del query
    confirmations = self._extract_multiple_hole_confirmations(query)
    
    if not confirmations:
        return {
            'response': "No pude entender las confirmaciones. Por favor, especifica cada hoyo y sus golpes, por ejemplo: 'Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes'.",
            'data': {}
        }
    
    # Registrar cada confirmación
    registered = []
    errors = []
    
    for conf in confirmations:
        hole_number = conf.get('hole_number')
        strokes = conf.get('strokes')
        
        if not hole_number or not strokes:
            errors.append(f"Confirmación incompleta: {conf}")
            continue
        
        try:
            score = self.match_service.record_hole_score(
                match_id=match_id,
                user_id=user_id,
                course_id=course_id,
                hole_number=hole_number,
                strokes=strokes
            )
            registered.append({'hole': hole_number, 'strokes': strokes})
        except Exception as e:
            errors.append(f"Error registrando hoyo {hole_number}: {str(e)}")
    
    # Construir respuesta
    if errors:
        response = f"Registré {len(registered)} hoyos correctamente. Hubo errores: {', '.join(errors)}"
    else:
        holes_str = ', '.join([f"hoyo {r['hole']} con {r['strokes']} golpes" for r in registered])
        response = f"Perfecto. He registrado: {holes_str}. Ahora puedes continuar con tu petición original."
    
    return {
        'response': response,
        'data': {
            'registered': registered,
            'errors': errors
        }
    }
```

### Función Helper: `_extract_multiple_hole_confirmations()`

```python
def _extract_multiple_hole_confirmations(self, query: str) -> List[Dict[str, Any]]:
    """
    Extrae múltiples confirmaciones de hoyos del query.
    
    Busca patrones como:
    - "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes"
    - "5: 4 golpes, 6: 5 golpes"
    - "Hoyo 5: 4, hoyo 6: 5"
    """
    import re
    
    confirmations = []
    query_lower = query.lower()
    
    # Patrón 1: "Hoyo X con Y golpes" (múltiples, separados por comas)
    pattern1 = r'hoyo\s+(\d+)\s+(?:con|:)\s+(\d+)\s*golpes?'
    matches1 = re.finditer(pattern1, query_lower)
    for match in matches1:
        confirmations.append({
            'hole_number': int(match.group(1)),
            'strokes': int(match.group(2))
        })
    
    # Si no se encontraron, intentar otros patrones
    if not confirmations:
        # Patrón 2: "X: Y golpes" o "X: Y"
        pattern2 = r'(\d+)\s*:\s*(\d+)\s*(?:golpes?)?'
        matches2 = re.finditer(pattern2, query_lower)
        for match in matches2:
            # Validar que sean números razonables
            num1 = int(match.group(1))
            num2 = int(match.group(2))
            if 1 <= num1 <= 18 and 1 <= num2 <= 20:  # Asumir que num1 es hoyo, num2 es golpes
                confirmations.append({
                    'hole_number': num1,
                    'strokes': num2
                })
    
    return confirmations
```

## Flujo Completo de Ejemplo

### Escenario: Jugador en hoyo 5 pide recomendación para hoyo 8

```
1. Jugador: "Dame una recomendación para el hoyo 8"
   
2. Sistema detecta inconsistencia:
   - Estado actual: hoyo 5
   - Hoyo mencionado: 8
   - Hoyos sin completar: 5, 6, 7
   
3. Sistema responde:
   {
     "response": "Antes de continuar, necesito que confirmes el resultado de los hoyos 5, 6 y 7. ¿Cuántos golpes realizaste en cada uno de estos hoyos?",
     "intent": "require_hole_confirmation",
     "data": {
       "missing_holes": [5, 6, 7],
       "current_hole": 5,
       "target_hole": 8,
       "requires_confirmation": true
     }
   }

4. Frontend muestra el mensaje y espera respuesta

5. Jugador: "Hoyo 5 con 4 golpes, hoyo 6 con 5 golpes, hoyo 7 con 3 golpes"

6. Sistema procesa confirmaciones:
   - Clasifica intención: puede ser "require_hole_confirmation" o detectar múltiples confirmaciones
   - Extrae confirmaciones: [(5, 4), (6, 5), (7, 3)]
   - Registra cada score
   - Actualiza estado: ahora está en hoyo 8

7. Sistema responde:
   "Perfecto. He registrado: hoyo 5 con 4 golpes, hoyo 6 con 5 golpes, hoyo 7 con 3 golpes. 
    Ahora puedes repetir tu petición para el hoyo 8."

8. Jugador: "Dame una recomendación para el hoyo 8"

9. Sistema procesa normalmente (ya no hay inconsistencia):
   - Detecta hoyo 8 mencionado
   - Estado actual: hoyo 8
   - No hay inconsistencias
   - Ejecuta handler de recomendación
   - Retorna recomendación
```

## Mejora: Procesamiento Automático

**Opción mejorada**: Después de registrar las confirmaciones, el sistema podría automáticamente procesar la petición original si se almacena en el contexto.

**Requisitos**:
- Almacenar la petición original cuando se detecta inconsistencia
- Después de registrar confirmaciones, procesar automáticamente la petición original
- Retornar la respuesta de la petición original directamente

**Implementación**:
```python
# En process_voice_command(), cuando se detecta inconsistencia:
if not consistency['is_consistent']:
    return {
        'response': response,
        'intent': 'require_hole_confirmation',
        'data': {
            'missing_holes': missing_holes,
            'original_query': query,  # Guardar query original
            'original_intent': intent,  # Guardar intención original
            ...
        }
    }

# En _handle_require_hole_confirmation(), después de registrar:
if 'original_query' in data and 'original_intent' in data:
    # Procesar automáticamente la petición original
    original_handler = getattr(self, f'_handle_{data["original_intent"]}', None)
    if original_handler:
        result = original_handler(...)
        return {
            'response': f"Confirmaciones registradas. {result['response']}",
            'data': result.get('data', {})
        }
```

## Conclusión

La implementación actual usa **confirmación múltiple** que es más simple pero puede ser mejorada con:

1. **Mejor extracción de confirmaciones múltiples** del query
2. **Procesamiento automático** de la petición original después de confirmar
3. **Validación** de que se confirmaron todos los hoyos requeridos
4. **Mensajes más claros** guiando al jugador sobre cómo responder

Para una experiencia más natural, se recomienda implementar **confirmación secuencial** en el futuro, pero requiere un sistema de estado de conversación más complejo.

