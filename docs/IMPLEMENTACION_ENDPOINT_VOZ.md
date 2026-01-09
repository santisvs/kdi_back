# Implementación: Endpoint Unificado de Voz para Partidos

## Resumen

Se ha implementado el endpoint unificado `/match/<match_id>/voice-command` que gestiona todas las peticiones de voz durante un partido de golf.

---

## Componentes Implementados

### 1. Agente Clasificador de Intenciones

**Archivo:** `src/kdi_back/infrastructure/agents/intent_classifier_agent.py`

**Funcionalidad:**
- Usa Amazon Nova Lite (Bedrock) para clasificar intenciones
- Analiza el query en lenguaje natural
- Retorna intención + nivel de confianza

**Intenciones soportadas:**
1. `recommend_shot` - Recomendación de palo/golpe
2. `register_stroke` - Registrar golpe
3. `check_distance` - Consultar distancia
4. `check_obstacles` - Consultar obstáculos
5. `check_terrain` - Consultar terreno
6. `complete_hole` - Completar hoyo
7. `check_ranking` - Consultar ranking
8. `check_hole_stats` - Estadísticas del hoyo
9. `check_hole_info` - Información del hoyo
10. `check_weather` - Consultar clima

---

### 2. Servicio de Voz

**Archivo:** `src/kdi_back/domain/services/voice_service.py`

**Funcionalidad:**
- Clasifica intenciones usando el agente
- Enruta a handlers específicos según la intención
- Formatea respuestas en lenguaje natural
- Valida que el usuario está en el partido

**Handlers implementados:**
- `_handle_recommend_shot()` - Usa `trajectory-options-evol`
- `_handle_register_stroke()` - Registra golpe
- `_handle_check_distance()` - Consulta distancia
- `_handle_check_obstacles()` - Consulta obstáculos
- `_handle_check_terrain()` - Consulta terreno
- `_handle_complete_hole()` - Completa hoyo
- `_handle_check_ranking()` - Consulta ranking
- `_handle_check_hole_stats()` - Estadísticas del hoyo
- `_handle_check_hole_info()` - Información del hoyo
- `_handle_check_weather()` - Consulta clima

---

### 3. Endpoint REST

**Archivo:** `src/kdi_back/api/routes/game.py`

**Endpoint:** `POST /match/<match_id>/voice-command`

**Características:**
- Requiere autenticación (token JWT)
- Valida que el usuario está en el partido
- Valida que el partido está en progreso
- Valida que el course_id coincide con el partido

---

## Integración con trajectory-options-evol

El handler `_handle_recommend_shot()` utiliza la misma lógica que el endpoint `/golf/trajectory-options-evol`:

1. **Identifica el hoyo** desde GPS
2. **Obtiene estadísticas del jugador** (si tiene perfil)
3. **Ejecuta algoritmo evolutivo:**
   - `bola_menos_10m_optimal_shot()` - Busca optimal_shots cercanos
   - `find_strategic_shot()` - Busca trayectorias en strategic_points
   - `evaluacion_final()` - Evalúa y ordena trayectorias
4. **Extrae información** de la trayectoria óptima
5. **Formatea respuesta** en lenguaje natural

---

## Ejemplo de Uso

### Petición

```bash
POST /match/123/voice-command
Authorization: Bearer <token>

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
  "response": "Estás a 88 metros del hoyo, te recomiendo utilizar Pitching Wedge con swing completo intentando alcanzar el green. Ten en cuenta: Bunker derecho.",
  "intent": "recommend_shot",
  "confidence": 0.95,
  "data": {
    "distance_meters": 88.0,
    "distance_yards": 96.24,
    "recommended_club": "Pitching Wedge",
    "swing_type": "completo",
    "target": "flag",
    "obstacles_count": 1,
    "risk_level": 15.5,
    "hole_info": {
      "id": 1,
      "hole_number": 1,
      "par": 4,
      "length": 367,
      "course_name": "Las Rejas Club de Golf"
    }
  }
}
```

---

## Ejemplos de Queries por Intención

### Recomendación de Golpe
- "¿Qué palo debo usar?"
- "¿Qué me recomiendas?"
- "Necesito una recomendación"
- "¿Cómo debo jugar esta bola?"

### Registrar Golpe
- "He dado un golpe"
- "Registra mi golpe"
- "He golpeado la bola"
- "Incrementa mis golpes"

### Consultar Distancia
- "¿A qué distancia estoy?"
- "¿Cuántos metros hay hasta la bandera?"
- "Distancia al hoyo"

### Consultar Obstáculos
- "¿Qué obstáculos hay?"
- "¿Hay bunkers o agua?"
- "Muéstrame los obstáculos"

### Consultar Terreno
- "¿En qué terreno estoy?"
- "¿Estoy en el bunker?"
- "¿Estoy en el green?"

### Completar Hoyo
- "He completado el hoyo"
- "Terminé este hoyo"
- "Completa el hoyo"

### Consultar Ranking
- "¿Cómo voy?"
- "¿Cuál es mi posición?"
- "Muéstrame el ranking"
- "¿Quién va ganando?"

### Estadísticas del Hoyo
- "¿Cuántos golpes llevo?"
- "¿Cuál es mi puntuación en este hoyo?"
- "Muéstrame mis golpes"

### Información del Hoyo
- "¿Qué hoyo es este?"
- "¿Cuál es el par?"
- "Información del hoyo"

### Consultar Clima
- "¿Qué tiempo hace?"
- "¿Hay viento?"
- "Condiciones meteorológicas"

---

## Validaciones Implementadas

1. ✅ **Usuario autenticado** - Requiere token JWT válido
2. ✅ **Usuario en partido** - Verifica que el usuario está en el partido
3. ✅ **Partido en progreso** - Solo permite acciones en partidos `in_progress`
4. ✅ **Course ID válido** - Verifica que el course_id coincide con el partido
5. ✅ **Coordenadas válidas** - Valida rango de latitud/longitud
6. ✅ **Query no vacío** - Valida que el query tiene contenido

---

## Manejo de Errores

- **Intención no reconocida:** Usa `recommend_shot` como fallback
- **Error en handler:** Retorna mensaje de error amigable
- **Hoyo no identificado:** Mensaje claro indicando el problema
- **Partido no válido:** Error descriptivo con detalles

---

## Arquitectura

```
Cliente (App móvil)
    ↓
POST /match/<id>/voice-command
    ↓
VoiceService.process_voice_command()
    ↓
IntentClassifierAgent.classify_intent()
    ↓
Router/Dispatcher
    ↓
Handler específico (_handle_*)
    ↓
Servicios de dominio (GolfService, MatchService, etc.)
    ↓
Respuesta en lenguaje natural
```

---

## Archivos Creados/Modificados

### Nuevos Archivos
1. `src/kdi_back/infrastructure/agents/intent_classifier_agent.py`
2. `src/kdi_back/domain/services/voice_service.py`
3. `src/kdi_back/api/routes/game.py`

### Archivos Modificados
1. `src/kdi_back/api/dependencies.py` - Añadido `get_voice_service()`
2. `src/kdi_back/api/main.py` - Registrado blueprint `game`
3. `ENDPOINTS.md` - Documentado nuevo endpoint

---

## Próximos Pasos (Opcionales)

1. **Mejorar clasificador:**
   - Añadir más ejemplos de entrenamiento
   - Ajustar temperatura del modelo
   - Cachear clasificaciones similares

2. **Contexto conversacional:**
   - Mantener contexto de la conversación
   - Recordar última petición
   - Referencias a peticiones anteriores

3. **Respuestas más naturales:**
   - Usar agente IA para formatear respuestas
   - Personalizar según estilo del jugador
   - Añadir variaciones en las respuestas

4. **Métricas:**
   - Logging de intenciones detectadas
   - Tasa de acierto del clasificador
   - Tiempo de respuesta

---

## Testing

### Ejemplos de Prueba

```bash
# Recomendación de golpe
curl -X POST http://localhost:5000/match/1/voice-command \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "latitude": 40.44445,
    "longitude": -3.87095,
    "query": "¿Qué palo debo usar?"
  }'

# Registrar golpe
curl -X POST http://localhost:5000/match/1/voice-command \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "latitude": 40.44445,
    "longitude": -3.87095,
    "query": "He dado un golpe"
  }'

# Consultar distancia
curl -X POST http://localhost:5000/match/1/voice-command \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "latitude": 40.44445,
    "longitude": -3.87095,
    "query": "¿A qué distancia estoy?"
  }'
```

---

## Conclusión

El endpoint unificado de voz está **completamente implementado** y listo para usar. Integra:

✅ Clasificación de intenciones con IA (Bedrock)
✅ Router/Dispatcher para enrutar peticiones
✅ Integración con `trajectory-options-evol` para recomendaciones
✅ Handlers para todos los tipos de peticiones
✅ Validaciones de seguridad
✅ Respuestas en lenguaje natural

El sistema está listo para recibir peticiones de voz desde la aplicación móvil.


