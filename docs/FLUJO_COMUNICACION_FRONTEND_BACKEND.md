# Flujo de Comunicación Frontend-Backend

## Resumen Ejecutivo

Actualmente existe **inconsistencia** en cómo el frontend se comunica con el backend:

1. **Flujo Principal (CORRECTO)**: El frontend llama a `/match/<match_id>/voice-command` que actúa como router unificado
2. **Flujo Secundario (LEGACY, NO USADO)**: Existe código que llama directamente a endpoints específicos, pero **NO se está usando actualmente**

## Flujo Actual (Implementado)

### 1. Usuario Habla → Frontend Procesa

**Archivo**: `kdi_front/lib/services/golf_voice_assistant_service.dart`

```dart
// Línea 71: processCommand() - Método principal
Future<void> processCommand(String transcript) async {
  // ...
  // Llamar siempre al endpoint unificado de voz
  final response = await GolfMatchService.processVoiceCommand(
    matchId: context.matchId,
    courseId: context.courseId,
    query: query,
  );
  // ...
}
```

**Flujo**:
1. Usuario habla → Transcripción de voz
2. `GolfVoiceAssistantService.processCommand()` recibe el texto
3. **SIEMPRE** llama a `GolfMatchService.processVoiceCommand()`
4. Este método llama a `/match/<match_id>/voice-command`

### 2. Backend Recibe → Clasifica → Enruta

**Archivo**: `kdi_back/src/kdi_back/api/routes/game.py`

```python
# Línea 10: Endpoint principal
@game_bp.route('/match/<int:match_id>/voice-command', methods=['POST'])
def voice_command(match_id):
    # ...
    result = voice_service.process_voice_command(
        user_id=user_id,
        match_id=match_id,
        course_id=course_id,
        latitude=latitude,
        longitude=longitude,
        query=query
    )
    # ...
```

**Archivo**: `kdi_back/src/kdi_back/domain/services/voice_service.py`

```python
# Línea 42: Procesa el comando
def process_voice_command(...):
    # 1. Clasificar intención con IA
    intent_result = classify_intent(query)
    intent = intent_result['intent']
    
    # 2. Enrutar según intención
    handler_method = getattr(self, f'_handle_{intent}', None)
    
    # 3. Ejecutar handler
    result = handler_method(...)
    
    return {
        'response': result['response'],
        'intent': intent,
        'confidence': confidence,
        'data': result.get('data', {})
    }
```

### 3. Handlers Internos del Backend

El backend tiene handlers internos que ejecutan la lógica:

| Intención | Handler | Funcionalidad Interna |
|-----------|---------|----------------------|
| `recommend_shot` | `_handle_recommend_shot()` | Usa `trajectory-options-evol` internamente |
| `register_stroke` | `_handle_register_stroke()` | Llama a `match_service.increment_hole_strokes()` |
| `check_distance` | `_handle_check_distance()` | Calcula distancia usando `golf_service` |
| `complete_hole` | `_handle_complete_hole()` | Llama a `match_service.complete_hole()` |
| `check_ranking` | `_handle_check_ranking()` | Llama a `match_service.get_match_leaderboard()` |

**IMPORTANTE**: Todos estos handlers son **internos al backend**. El frontend **NO** los llama directamente.

## Flujo Legacy (NO USADO)

### Código que Existe pero NO se Ejecuta

**Archivo**: `kdi_front/lib/services/golf_voice_assistant_service.dart`

```dart
// Línea 146: _processGameFlowCommand() - NO SE USA
Future<void> _processGameFlowCommand(VoiceCommand command) async {
  // ...
  await _handlePlayingHoleCommand(command);
}

// Línea 171: _handlePlayingHoleCommand() - NO SE USA
Future<void> _handlePlayingHoleCommand(VoiceCommand command) async {
  switch (command.gameFlowType!) {
    case GameFlowCommandType.recommendation:
      // ❌ LLAMA DIRECTAMENTE A ENDPOINT ESPECÍFICO
      response = await GolfMatchService.getNextShotRecommendation(...);
      break;
    
    case GameFlowCommandType.shotConfirmation:
      // ❌ LLAMA DIRECTAMENTE A ENDPOINT ESPECÍFICO
      response = await GolfMatchService.incrementStrokes(...);
      break;
    
    case GameFlowCommandType.completeHole:
      // ❌ LLAMA DIRECTAMENTE A ENDPOINT ESPECÍFICO
      response = await GolfMatchService.completeHole(...);
      break;
  }
}
```

**¿Por qué existe este código?**

Este código parece ser de una implementación anterior donde:
1. El frontend clasificaba los comandos localmente con `VoiceCommandProcessor`
2. El frontend llamaba a `_processGameFlowCommand()` o `_processContextCommand()`
3. Luego llamaba directamente a endpoints específicos según el tipo de comando

**¿Se está usando actualmente?**

**NO**. Los métodos `_processGameFlowCommand()` y `_handlePlayingHoleCommand()` **NO se llaman** desde `processCommand()`. 

**Verificación**:
- `processCommand()` (línea 71) **siempre** llama directamente a `GolfMatchService.processVoiceCommand()`
- **NO** llama a `_processGameFlowCommand()` ni a `_processContextCommand()`
- El `VoiceCommandProcessor` existe pero **NO se usa** en el flujo actual

El flujo actual es:
```
processCommand() 
  → GolfMatchService.processVoiceCommand() 
    → /match/<match_id>/voice-command
      → Backend clasifica con IA (classify_intent)
        → Backend enruta internamente (_handle_{intent})
```

**Nota**: El `VoiceCommandProcessor` en el frontend parece ser código legacy que no se está usando. El backend hace toda la clasificación de intenciones con IA.

## Endpoints que el Frontend Llama Directamente

### Endpoints Llamados desde el Frontend

1. **`/match/<match_id>/voice-command`** ✅ (Principal)
   - **Cuándo**: Siempre que el usuario habla
   - **Archivo**: `golf_match_service.dart:906`
   - **Uso**: CORRECTO - Es el router unificado

2. **`/match/<match_id>/state/<user_id>`** ✅ (Nuevo)
   - **Cuándo**: Para sincronizar estado del partido
   - **Archivo**: `golf_match_service.dart:862`
   - **Uso**: CORRECTO - Para obtener estado persistido

3. **`/match/<match_id>/leaderboard`** ⚠️ (Contexto)
   - **Cuándo**: Cuando se pide clasificación
   - **Archivo**: `golf_match_service.dart:697`
   - **Uso**: Se llama desde `ContextCommandHandler`, no desde el flujo principal de voz

4. **`/match/<match_id>/score`** ⚠️ (Contexto)
   - **Cuándo**: Para actualizar puntuación manualmente
   - **Archivo**: `golf_match_service.dart:810`
   - **Uso**: Se llama desde `ContextCommandHandler`, no desde el flujo principal de voz

### Endpoints que NO se Llaman Directamente

Los siguientes endpoints **NO** se llaman directamente desde el frontend durante el flujo de voz:

- ❌ `/golf/next-shot` - **NO se usa** (reemplazado por `voice-command`)
- ❌ `/golf/trajectory-options` - **NO se usa** desde el frontend
- ❌ `/golf/trajectory-options-evol` - **NO se usa** directamente (se usa internamente en el backend)
- ❌ `/match/<match_id>/increment-strokes` - **NO se usa** directamente (se usa internamente en el backend)
- ❌ `/match/<match_id>/complete-hole` - **NO se usa** directamente (se usa internamente en el backend)

## Diagrama de Flujo Actual

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO HABLA                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: GolfVoiceAssistantService.processCommand()       │
│  - Recibe transcripción                                     │
│  - Valida texto                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: GolfMatchService.processVoiceCommand()           │
│  - Construye request                                        │
│  - Envía a: POST /match/<match_id>/voice-command           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: /match/<match_id>/voice-command                    │
│  - Valida autenticación                                     │
│  - Extrae user_id del token                                │
│  - Llama a VoiceService.process_voice_command()             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: VoiceService.process_voice_command()              │
│  1. Clasifica intención con IA (classify_intent)            │
│  2. Obtiene handler: _handle_{intent}                        │
│  3. Ejecuta handler                                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ recommend_shot│ │register_stroke│ │complete_hole  │
│               │ │               │ │               │
│ Usa internamente│ │ Usa internamente│ │ Usa internamente│
│ trajectory-   │ │ match_service │ │ match_service │
│ options-evol  │ │ .increment_   │ │ .complete_    │
│               │ │ hole_strokes()│ │ hole()        │
└───────────────┘ └───────────────┘ └───────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: Retorna respuesta                                 │
│  {                                                           │
│    "response": "Te recomiendo usar...",                     │
│    "intent": "recommend_shot",                              │
│    "confidence": 0.95,                                      │
│    "data": {...}                                            │
│  }                                                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Recibe respuesta                                 │
│  - Reproduce audio (TTS)                                    │
│  - Muestra respuesta                                        │
└─────────────────────────────────────────────────────────────┘
```

## Problema Identificado

### ¿Por qué hay código que llama directamente a otros endpoints?

El código en `_handlePlayingHoleCommand()` es **legacy** de una implementación anterior donde:

1. El frontend clasificaba comandos localmente con `VoiceCommandProcessor`
2. El frontend llamaba directamente a endpoints según el tipo de comando
3. **NO** se usaba un router unificado en el backend

### ¿Por qué NO se está usando?

Porque el flujo actual **siempre** llama a `processCommand()` que **siempre** llama a `/match/<match_id>/voice-command`. El método `_handlePlayingHoleCommand()` **nunca se ejecuta** en el flujo actual.

### ¿Debería eliminarse?

**SÍ**, pero con precaución:

1. **Verificar** que ningún otro código lo esté usando
2. **Eliminar** el código legacy si no se usa
3. **Mantener** solo el flujo unificado a través de `voice-command`

## Recomendaciones

### 1. Limpiar Código Legacy

Eliminar o comentar el código en `_handlePlayingHoleCommand()` ya que no se está usando:

```dart
// TODO: Este método no se usa. El flujo actual siempre llama a
// processCommand() que usa /match/<match_id>/voice-command
// Considerar eliminar este código legacy
Future<void> _handlePlayingHoleCommand(VoiceCommand command) async {
  // ... código no usado ...
}
```

### 2. Verificar Endpoints de Contexto

Los endpoints `/match/<match_id>/leaderboard` y `/match/<match_id>/score` se llaman desde `ContextCommandHandler`. Esto está **bien** porque:

- Son comandos de contexto (no del flujo principal de juego)
- Se procesan de forma diferente
- No interrumpen el flujo principal

**Recomendación**: Considerar si estos también deberían pasar por `voice-command` para mantener consistencia.

### 3. Documentar Flujo Unificado

Asegurar que todos los desarrolladores entiendan que:
- **SIEMPRE** se debe usar `/match/<match_id>/voice-command` para comandos de voz
- El backend clasifica y enruta internamente
- **NO** se deben llamar endpoints específicos directamente desde el frontend

## Conclusión

El flujo actual es **correcto**: el frontend siempre llama a `/match/<match_id>/voice-command` que actúa como router unificado. El código que llama directamente a otros endpoints es **legacy** y **no se está usando**. Se recomienda limpiarlo para evitar confusión.

