# Análisis: Endpoint Gestor de Peticiones de Voz para Partidos

## Resumen Ejecutivo

**Estado:** ❌ **NO EXISTE** un endpoint unificado que gestione peticiones de voz durante un partido.

El sistema actual tiene endpoints específicos que cubren funcionalidades individuales, pero **falta un endpoint central** que:
1. Reciba token, course_id, match_id, GPS y query en lenguaje natural
2. Diferencie el tipo de petición del jugador
3. Enrute a la funcionalidad correspondiente
4. Retorne respuesta en lenguaje natural

---

## Situación Actual

### Endpoints Existentes (Parciales)

#### 1. `POST /golf` 
**Recibe:**
- ✅ `latitude`, `longitude` (GPS)
- ✅ `query` (lenguaje natural)
- ❌ NO recibe `token` (no requiere auth)
- ❌ NO recibe `course_id`
- ❌ NO recibe `match_id`

**Funcionalidad:** Recomendación básica de palo usando agente IA simple

**Problema:** No está integrado con el contexto del partido ni del jugador autenticado.

---

#### 2. `POST /golf/next-shot`
**Recibe:**
- ✅ `latitude`, `longitude` (GPS)
- ✅ `course_id` (opcional)
- ✅ `user_id` (opcional)
- ✅ `match_id` (opcional, solo contexto)
- ❌ NO recibe `query` en lenguaje natural
- ❌ NO recibe `token` (no requiere auth explícito)

**Funcionalidad:** Recomendación completa del siguiente golpe con análisis detallado

**Problema:** No procesa lenguaje natural para diferenciar intenciones. Siempre retorna recomendación de golpe.

---

#### 3. Endpoints de Match
**Ejemplos:**
- `POST /match/<match_id>/increment-strokes` - Registra golpe
- `POST /match/<match_id>/complete-hole` - Completa hoyo
- `GET /match/<match_id>/leaderboard` - Ver ranking

**Problema:** Son endpoints específicos que requieren saber exactamente qué acción realizar. No procesan lenguaje natural.

---

## Lo que FALTA

### Endpoint Unificado de Voz para Partidos

**Endpoint propuesto:** `POST /match/<match_id>/voice-command` o `POST /game/voice`

**Requisitos:**
1. ✅ Recibir token de autenticación (en header)
2. ✅ Recibir `course_id`
3. ✅ Recibir `match_id`
4. ✅ Recibir posición GPS (`latitude`, `longitude`)
5. ✅ Recibir `query` en lenguaje natural
6. ✅ Diferenciar tipo de petición (intent classification)
7. ✅ Enrutar a funcionalidad correspondiente
8. ✅ Retornar respuesta en lenguaje natural

---

## Tipos de Peticiones que Debe Manejar

### 1. Recomendación de Golpe
**Ejemplos de queries:**
- "¿Qué palo debo usar?"
- "¿Qué me recomiendas para este golpe?"
- "Necesito una recomendación"
- "¿Cómo debo jugar esta bola?"

**Acción:** Llamar a `POST /golf/next-shot` con los parámetros

---

### 2. Registrar Golpe
**Ejemplos de queries:**
- "He dado un golpe"
- "Registra mi golpe"
- "He golpeado la bola"
- "Incrementa mis golpes"

**Acción:** Llamar a `POST /match/<match_id>/increment-strokes`

---

### 3. Consultar Distancia
**Ejemplos de queries:**
- "¿A qué distancia estoy del hoyo?"
- "¿Cuántos metros hay hasta la bandera?"
- "Distancia al hoyo"

**Acción:** Llamar a `POST /golf/distance-to-hole`

---

### 4. Consultar Obstáculos
**Ejemplos de queries:**
- "¿Qué obstáculos hay en el camino?"
- "¿Hay bunkers o agua entre la bola y el hoyo?"
- "Muéstrame los obstáculos"

**Acción:** Llamar a `POST /golf/obstacles-between`

---

### 5. Consultar Tipo de Terreno
**Ejemplos de queries:**
- "¿En qué terreno estoy?"
- "¿Estoy en el bunker?"
- "¿Estoy en el green?"

**Acción:** Llamar a `POST /golf/terrain-type`

---

### 6. Completar Hoyo
**Ejemplos de queries:**
- "He completado el hoyo"
- "Terminé este hoyo"
- "Completa el hoyo"

**Acción:** Llamar a `POST /match/<match_id>/complete-hole`

---

### 7. Consultar Ranking
**Ejemplos de queries:**
- "¿Cómo voy en el partido?"
- "¿Cuál es mi posición?"
- "Muéstrame el ranking"
- "¿Quién va ganando?"

**Acción:** Llamar a `GET /match/<match_id>/leaderboard`

---

### 8. Consultar Estadísticas del Hoyo
**Ejemplos de queries:**
- "¿Cuántos golpes llevo en este hoyo?"
- "¿Cuál es mi puntuación en este hoyo?"
- "Muéstrame mis golpes"

**Acción:** Llamar a `GET /match/<match_id>/player/<user_id>/scores`

---

### 9. Consultar Información del Hoyo
**Ejemplos de queries:**
- "¿Qué hoyo es este?"
- "¿Cuál es el par de este hoyo?"
- "Información del hoyo"

**Acción:** Llamar a `POST /golf/identify-hole` o usar información ya obtenida

---

### 10. Consultar Clima
**Ejemplos de queries:**
- "¿Qué tiempo hace?"
- "¿Hay viento?"
- "Condiciones meteorológicas"

**Acción:** Llamar a `POST /weather` o `GET /weather`

---

## Arquitectura Propuesta

### Componentes Necesarios

#### 1. Clasificador de Intenciones (Intent Classifier)
**Función:** Analizar el query en lenguaje natural y determinar qué acción quiere realizar el jugador.

**Opciones de implementación:**

**Opción A: Agente IA con Bedrock**
- Usar Amazon Nova Lite para clasificar intenciones
- Prompt con ejemplos de cada tipo de petición
- Retornar tipo de intención + confianza

**Opción B: Reglas + Keywords**
- Análisis de keywords en el query
- Reglas simples basadas en palabras clave
- Más rápido pero menos flexible

**Opción C: Híbrido**
- Reglas para casos comunes (rápido)
- IA para casos ambiguos o complejos

**Recomendación:** Opción A (IA) para mayor flexibilidad y precisión.

---

#### 2. Router/Dispatcher
**Función:** Enrutar la petición clasificada al endpoint/función correspondiente.

**Lógica:**
```python
intent = classify_intent(query)
if intent == "recommend_shot":
    return call_next_shot_endpoint(...)
elif intent == "register_stroke":
    return call_increment_strokes(...)
elif intent == "check_distance":
    return call_distance_to_hole(...)
# etc.
```

---

#### 3. Generador de Respuestas en Lenguaje Natural
**Función:** Convertir las respuestas técnicas de los endpoints en lenguaje natural conversacional.

**Opciones:**
- Usar agente IA para formatear respuestas
- Templates con variables
- Combinación de ambas

---

## Diseño del Endpoint

### Estructura Propuesta

```python
POST /match/<match_id>/voice-command
# O alternativamente:
POST /game/voice-command

Headers:
  Authorization: Bearer <token>

Body:
{
  "course_id": 1,
  "latitude": 40.44445,
  "longitude": -3.87095,
  "query": "¿Qué palo debo usar?"
}
```

### Respuesta

```json
{
  "response": "Estás a 88 metros del hoyo, te recomiendo utilizar un Pitching Wedge con swing completo intentando hacer un flop shot para pasar los árboles por encima.",
  "intent": "recommend_shot",
  "confidence": 0.95,
  "data": {
    // Datos adicionales según el tipo de petición
    "distance_meters": 88.0,
    "recommended_club": "Pitching Wedge",
    // etc.
  }
}
```

---

## Implementación Propuesta

### Paso 1: Crear Agente Clasificador de Intenciones

**Archivo:** `src/kdi_back/infrastructure/agents/intent_classifier_agent.py`

```python
INTENT_CLASSIFIER_PROMPT = """
Eres un clasificador de intenciones para un asistente de voz de golf.
Analiza la petición del jugador y determina qué acción quiere realizar.

Tipos de intenciones:
1. recommend_shot - Pedir recomendación de palo/golpe
2. register_stroke - Registrar que ha dado un golpe
3. check_distance - Consultar distancia al hoyo
4. check_obstacles - Consultar obstáculos
5. check_terrain - Consultar tipo de terreno
6. complete_hole - Completar el hoyo actual
7. check_ranking - Consultar ranking del partido
8. check_hole_stats - Consultar estadísticas del hoyo
9. check_hole_info - Consultar información del hoyo
10. check_weather - Consultar clima

Responde SOLO con el nombre de la intención en formato JSON:
{"intent": "nombre_intencion", "confidence": 0.0-1.0}
"""

def classify_intent(query: str) -> Dict[str, Any]:
    # Usar agente IA para clasificar
    pass
```

---

### Paso 2: Crear Servicio de Voz

**Archivo:** `src/kdi_back/domain/services/voice_service.py`

```python
class VoiceService:
    def __init__(self, intent_classifier, golf_service, match_service, ...):
        self.intent_classifier = intent_classifier
        self.golf_service = golf_service
        self.match_service = match_service
        # etc.
    
    def process_voice_command(
        self, 
        user_id: int,
        match_id: int,
        course_id: int,
        latitude: float,
        longitude: float,
        query: str
    ) -> Dict[str, Any]:
        # 1. Clasificar intención
        intent_result = self.intent_classifier.classify_intent(query)
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        
        # 2. Enrutar según intención
        if intent == "recommend_shot":
            return self._handle_recommend_shot(...)
        elif intent == "register_stroke":
            return self._handle_register_stroke(...)
        # etc.
    
    def _handle_recommend_shot(self, ...):
        # Llamar a golf_service y formatear respuesta
        pass
    
    def _handle_register_stroke(self, ...):
        # Llamar a match_service y formatear respuesta
        pass
```

---

### Paso 3: Crear Endpoint

**Archivo:** `src/kdi_back/api/routes/game.py` (nuevo archivo)

```python
@game_bp.route('/match/<int:match_id>/voice-command', methods=['POST'])
@require_auth
def voice_command(match_id):
    """
    Endpoint principal para procesar comandos de voz durante un partido.
    
    Recibe:
    - course_id: ID del campo
    - latitude, longitude: Posición GPS
    - query: Petición en lenguaje natural
    
    Retorna:
    - response: Respuesta en lenguaje natural
    - intent: Tipo de intención detectada
    - data: Datos adicionales
    """
    # Validar que el usuario está en el partido
    # Procesar comando de voz
    # Retornar respuesta
```

---

## Flujo Completo

```
1. App móvil envía:
   POST /match/123/voice-command
   {
     "course_id": 1,
     "latitude": 40.44445,
     "longitude": -3.87095,
     "query": "¿Qué palo debo usar?"
   }

2. Backend:
   a. Valida token y que usuario está en partido
   b. Clasifica intención: "recommend_shot"
   c. Enruta a golf_service.get_next_shot_recommendation()
   d. Obtiene recomendación técnica
   e. Formatea respuesta en lenguaje natural
   f. Retorna respuesta conversacional

3. App móvil recibe:
   {
     "response": "Estás a 88 metros del hoyo, te recomiendo...",
     "intent": "recommend_shot",
     "confidence": 0.95
   }
```

---

## Ventajas de este Enfoque

1. ✅ **Un solo endpoint** para todas las peticiones de voz
2. ✅ **Flexibilidad** - El jugador puede expresarse de diferentes formas
3. ✅ **Extensible** - Fácil añadir nuevos tipos de peticiones
4. ✅ **Contexto completo** - Siempre tiene match_id, course_id, GPS
5. ✅ **Respuestas naturales** - Retorna texto conversacional

---

## Consideraciones Técnicas

### Validaciones Necesarias

1. **Usuario en partido:**
   - Verificar que el usuario autenticado está en el partido
   - Verificar que el partido está en progreso

2. **Coordenadas válidas:**
   - Validar que las coordenadas están dentro del campo
   - Validar que el hoyo identificado pertenece al campo del partido

3. **Contexto del partido:**
   - Verificar que el partido no está completado
   - Verificar que el jugador puede realizar la acción

---

### Manejo de Errores

**Casos a manejar:**
- Intención no reconocida → "No entendí tu petición, ¿puedes reformularla?"
- Acción no permitida → "No puedes realizar esa acción en este momento"
- Error técnico → "Hubo un problema procesando tu petición"

---

### Optimizaciones

1. **Cache de intenciones comunes:**
   - Cachear clasificaciones de queries similares
   - Reducir llamadas a IA

2. **Batch processing:**
   - Si se reciben múltiples queries, procesarlas en batch

3. **Contexto conversacional:**
   - Mantener contexto de la conversación (última petición, etc.)

---

## Plan de Implementación

### Fase 1: Clasificador de Intenciones (2-3 horas)
1. Crear agente clasificador
2. Definir tipos de intenciones
3. Crear prompt con ejemplos
4. Probar con queries de prueba

### Fase 2: Servicio de Voz (4-5 horas)
1. Crear VoiceService
2. Implementar handlers para cada intención
3. Integrar con servicios existentes
4. Formatear respuestas en lenguaje natural

### Fase 3: Endpoint (2-3 horas)
1. Crear endpoint `/match/<id>/voice-command`
2. Validaciones de seguridad
3. Manejo de errores
4. Documentación

### Fase 4: Testing (2-3 horas)
1. Tests unitarios del clasificador
2. Tests de integración del servicio
3. Tests E2E del endpoint
4. Pruebas con queries reales

**Tiempo total estimado: 10-14 horas**

---

## Alternativa: Endpoint Más Simple

Si se quiere una implementación más rápida, se puede crear un endpoint que:

1. **Siempre asuma** que la petición es "recomendación de golpe" (caso más común)
2. **Use el query** como `ball_situation_description` en `/golf/next-shot`
3. **Retorne** la recomendación directamente

**Endpoint:**
```python
POST /match/<match_id>/voice-command
{
  "course_id": 1,
  "latitude": 40.44445,
  "longitude": -3.87095,
  "query": "¿Qué palo debo usar? Hay viento en contra"
}

# Internamente llama a /golf/next-shot con:
# - ball_situation_description = query
# - match_id, course_id, user_id, GPS
```

**Ventaja:** Implementación rápida (2-3 horas)
**Desventaja:** No diferencia tipos de peticiones, solo recomendaciones

---

## Recomendación Final

**Implementar el endpoint completo con clasificador de intenciones** porque:

1. ✅ Permite múltiples tipos de peticiones (no solo recomendaciones)
2. ✅ Mejor experiencia de usuario (puede hacer cualquier pregunta)
3. ✅ Escalable para futuras funcionalidades
4. ✅ Tiempo de implementación razonable (10-14 horas)

El sistema ya tiene toda la infraestructura necesaria (agentes IA, servicios, endpoints), solo falta **orquestar** todo en un endpoint unificado.

---

## Conclusión

**NO existe actualmente** un endpoint que gestione peticiones de voz durante un partido. 

**Solución:** Crear `POST /match/<match_id>/voice-command` que:
- Reciba token, course_id, match_id, GPS y query
- Clasifique la intención usando IA
- Enrute a la funcionalidad correspondiente
- Retorne respuesta en lenguaje natural

**Tiempo estimado:** 10-14 horas de desarrollo.

