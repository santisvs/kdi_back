# Listado de Endpoints - kdi_back

Este documento contiene el listado completo de endpoints expuestos por el servicio kdi_back y una breve explicación de cada uno.

## Índice
- [Health](#health)
- [Autenticación](#autenticación)
- [Jugadores](#jugadores)
- [Partidos](#partidos)
- [Golf](#golf)
- [Clima](#clima)

---

## Health

### GET `/hola-mundo`
Endpoint de prueba que responde con un mensaje simple. Útil para verificar que el servicio está funcionando.

**Respuesta:** `{"mensaje": "adios mundo"}`

---

### GET `/health`
Endpoint de salud para verificar que el servicio está corriendo correctamente.

**Respuesta:** `{"status": "ok"}`

---

## Autenticación

### POST `/auth/register`
Registra un nuevo usuario en el sistema. Crea una cuenta con email, username y contraseña, y retorna un token JWT.

**Campos requeridos:**
- `email`: Email del usuario (único)
- `username`: Nombre de usuario (único)
- `password`: Contraseña (mínimo 6 caracteres)

**Campos opcionales:**
- `first_name`: Nombre del usuario
- `last_name`: Apellido del usuario

**Respuesta:** Usuario creado y token JWT

---

### POST `/auth/login`
Inicia sesión con email y contraseña. Retorna información del usuario y un token JWT.

**Campos requeridos:**
- `email`: Email del usuario
- `password`: Contraseña

**Respuesta:** Información del usuario y token JWT

---

### POST `/auth/forgot-password`
Solicita la recuperación de contraseña. Genera un token de recuperación que se envía por email (en desarrollo se retorna en la respuesta).

**Campos requeridos:**
- `email`: Email del usuario

**Respuesta:** Mensaje de confirmación y token de recuperación (solo en desarrollo)

---

### POST `/auth/reset-password`
Restablece la contraseña usando un token de recuperación obtenido del endpoint anterior.

**Campos requeridos:**
- `token`: Token de recuperación de contraseña
- `new_password`: Nueva contraseña (mínimo 6 caracteres)

**Respuesta:** Mensaje de confirmación

---

### POST `/auth/oauth/google`
Autenticación/registro con Google OAuth. Si el usuario no existe, lo crea automáticamente. Si ya existe, lo autentica.

**Campos requeridos:**
- `oauth_id`: ID del usuario en Google
- `email`: Email del usuario

**Campos opcionales:**
- `username`: Nombre de usuario
- `first_name`: Nombre del usuario
- `last_name`: Apellido del usuario

**Respuesta:** Información del usuario y token JWT

---

### POST `/auth/oauth/instagram`
Autenticación/registro con Instagram OAuth. Si el usuario no existe, lo crea automáticamente. Si ya existe, lo autentica.

**Campos requeridos:**
- `oauth_id`: ID del usuario en Instagram
- `email`: Email del usuario

**Campos opcionales:**
- `username`: Nombre de usuario
- `first_name`: Nombre del usuario
- `last_name`: Apellido del usuario

**Respuesta:** Información del usuario y token JWT

---

## Jugadores

### POST `/player`
Crea un usuario con su perfil de jugador inicial. Requiere autenticación.

**Autenticación:** Requerida (token JWT)

**Campos requeridos:**
- `email`: Email del usuario (único)
- `username`: Nombre de usuario (único)

**Campos opcionales:**
- `first_name`: Nombre del usuario
- `last_name`: Apellido del usuario
- `phone`: Teléfono de contacto
- `date_of_birth`: Fecha de nacimiento (YYYY-MM-DD)
- `handicap`: Handicap del jugador (0-54)
- `gender`: Género (male, female) - requerido para inicializar estadísticas
- `preferred_hand`: Mano preferida (right, left, ambidextrous)
- `years_playing`: Años de experiencia jugando golf
- `skill_level`: Nivel de habilidad (beginner, intermediate, advanced, professional) - requerido para inicializar estadísticas
- `notes`: Notas adicionales sobre el jugador

**Respuesta:** Usuario y perfil de jugador creados

---

### GET `/player/profile`
Obtiene el perfil de jugador del usuario autenticado. Requiere autenticación.

**Autenticación:** Requerida (token JWT)

**Respuesta:** Perfil completo del jugador con handicap, estadísticas, etc.

---

### GET `/player/club-statistics`
Obtiene las estadísticas de palos del usuario autenticado. Incluye información sobre distancia promedio, error, etc. para cada palo. Requiere autenticación.

**Autenticación:** Requerida (token JWT)

**Respuesta:** Lista de estadísticas por palo (driver, hierros, wedges, etc.)

---

## Partidos

### POST `/match/<match_id>/voice-command`
Endpoint principal para procesar comandos de voz durante un partido. Actúa como gestor unificado que clasifica la intención de la petición y enruta a la funcionalidad correspondiente.

**Autenticación:** Requerida (token JWT)

**Campos requeridos:**
- `course_id`: ID del campo de golf
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota
- `query`: Petición en lenguaje natural

**Respuesta:** Respuesta en lenguaje natural con la intención detectada y datos adicionales

**Tipos de intenciones soportadas:**
- `recommend_shot`: Recomendación de palo/golpe (usa trajectory-options-evol)
- `register_stroke`: Registrar golpe
- `check_distance`: Consultar distancia al hoyo
- `check_obstacles`: Consultar obstáculos
- `check_terrain`: Consultar tipo de terreno
- `complete_hole`: Completar hoyo
- `check_ranking`: Consultar ranking del partido
- `check_hole_stats`: Consultar estadísticas del hoyo
- `check_hole_info`: Consultar información del hoyo
- `check_weather`: Consultar clima

---

### POST `/match`
Crea un nuevo partido en un campo de golf. El usuario autenticado se añade automáticamente como jugador. Requiere autenticación.

**Autenticación:** Requerida (token JWT)

**Campos requeridos:**
- `course_id`: ID del campo de golf

**Campos opcionales:**
- `name`: Nombre del partido
- `player_ids`: Lista de IDs de jugadores a añadir
- `starting_holes`: Diccionario {user_id: starting_hole_number} para definir desde qué hoyo empieza cada jugador

**Respuesta:** Partido creado con información de jugadores

---

### POST `/match/<match_id>/player`
Añade un jugador a un partido existente.

**Campos requeridos:**
- `user_id`: ID del usuario/jugador
- `starting_hole_number`: Número del hoyo donde empieza (opcional, default: 1)

**Respuesta:** Información del jugador añadido al partido

---

### POST `/match/<match_id>/score`
Registra la puntuación de un jugador en un hoyo específico.

**Campos requeridos:**
- `user_id`: ID del usuario/jugador
- `course_id`: ID del campo de golf
- `hole_number`: Número del hoyo
- `strokes`: Número de golpes

**Respuesta:** Puntuación registrada con información del hoyo

---

### POST `/match/<match_id>/increment-strokes`
Incrementa el número de golpes de un jugador en un hoyo. Se usa cuando un jugador confirma que ha ejecutado un golpe. Puede evaluar el golpe anterior si se proporciona la nueva posición de la bola.

**Campos requeridos:**
- `user_id`: ID del usuario/jugador
- `course_id`: ID del campo de golf
- `hole_number`: Número del hoyo

**Campos opcionales:**
- `strokes`: Número de golpes a incrementar (default: 1)
- `ball_start_latitude`: Latitud inicial de la bola (para evaluación)
- `ball_start_longitude`: Longitud inicial de la bola (para evaluación)
- `club_used_id`: ID del palo utilizado
- `club_used_name`: Nombre del palo utilizado
- `trajectory_type`: Trayectoria escogida (conservadora, riesgo, optima)
- `proposed_distance_meters`: Distancia propuesta en metros
- `proposed_club_id`: ID del palo propuesto
- ` `: Nombre del palo propuesto

**Respuesta:** Golpes incrementados y evaluación del golpe anterior (si aplica)

---

### POST `/match/<match_id>/complete-hole`
Marca el final de un hoyo para un jugador. Retorna estadísticas del hoyo y del partido.

**Campos requeridos:**
- `user_id`: ID del usuario/jugador
- `course_id`: ID del campo de golf
- `hole_number`: Número del hoyo

**Respuesta:** Golpes del hoyo, total de golpes y ranking actualizado

---

### GET `/match/<match_id>`
Obtiene los detalles completos de un partido, incluyendo información de jugadores y leaderboard.

**Respuesta:** Información completa del partido, jugadores y ranking

---

### POST `/match/<match_id>/complete`
Completa un partido y determina el ganador basándose en el total de golpes.

**Respuesta:** Partido completado con leaderboard final y ganador

---

### GET `/match/<match_id>/leaderboard`
Obtiene el ranking de jugadores de un partido ordenado por total de golpes.

**Respuesta:** Lista de jugadores ordenados por ranking

---

### GET `/match/<match_id>/player/<user_id>/scores`
Obtiene todas las puntuaciones de un jugador en un partido específico.

**Respuesta:** Lista de puntuaciones del jugador por hoyo

---

### GET `/match/course/<course_id>`
Obtiene todos los partidos de un campo de golf.

**Query parameters:**
- `status`: Filtro opcional por estado (in_progress, completed, cancelled)

**Respuesta:** Lista de partidos del campo

---

### GET `/match/player/<user_id>`
Obtiene todos los partidos de un jugador.

**Query parameters:**
- `status`: Filtro opcional por estado (in_progress, completed, cancelled)

**Respuesta:** Lista de partidos del jugador

---

## Golf

### GET `/golf/courses`
Obtiene todos los campos de golf disponibles en el sistema.

**Respuesta:** Lista de campos de golf con ID y nombre

---

### POST `/golf`
Obtiene recomendaciones de palo de golf basadas en GPS y situación del juego usando un agente de IA.

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota
- `query`: Texto en lenguaje natural describiendo la situación del juego

**Respuesta:** Recomendación de palo en texto natural

---

### POST `/golf/identify-hole`
Identifica en qué hoyo se encuentra una bola según su posición GPS.

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Respuesta:** Información del hoyo identificado o null si no se encuentra

---

### POST `/golf/terrain-type`
Determina el tipo de terreno donde se encuentra una bola según su posición GPS (fairway, green, bunker, water, etc.).

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)

**Respuesta:** Tipo de terreno (bunker, water, etc.) o null si está en terreno normal

---

### POST `/golf/distance-to-hole`
Calcula la distancia desde la posición de la bola hasta la bandera del hoyo.

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)

**Respuesta:** Distancia en metros y yardas hasta la bandera

---

### POST `/golf/obstacles-between`
Encuentra los obstáculos que intersectan con la línea entre la bola y la bandera (bunkers, agua, etc.).

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)

**Respuesta:** Lista de obstáculos encontrados entre la bola y la bandera

---

### POST `/golf/nearest-optimal-shot`
Encuentra el golpe óptimo más cercano a la posición actual de la bola (basado en optimal_shots almacenados).

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)

**Respuesta:** Golpe óptimo más cercano con descripción y distancia

---

### POST `/golf/next-shot`
Obtiene recomendación del siguiente golpe usando análisis completo del campo y un agente de IA. Incluye evaluación de trayectorias, obstáculos, distancia, etc.

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)
- `user_id`: ID del usuario/jugador (usa el perfil del jugador si se proporciona)
- `ball_situation_description`: Descripción de la situación de la bola
- `match_id`: ID del partido (solo para contexto, no registra golpes)

**Respuesta:** Recomendación de palo y análisis completo (distancia, obstáculos, trayectorias, etc.)

---

### POST `/golf/trajectory-options`
Obtiene opciones de trayectorias calculadas con recomendaciones de palo. Endpoint técnico que devuelve lógica de negocio (trayectoria directa vs conservadora, palo recomendado, análisis de riesgo).

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)
- `user_id`: ID del usuario/jugador (usa el perfil del jugador si se proporciona)

**Respuesta:** Análisis de trayectorias (directa y conservadora) con recomendaciones de palo y análisis de riesgo

---

### POST `/golf/trajectory-options-evol`
Obtiene opciones de trayectorias usando un algoritmo evolutivo que busca optimal_shots y strategic_points. Versión avanzada del endpoint anterior.

**Campos requeridos:**
- `latitude`: Latitud GPS de la posición de la pelota
- `longitude`: Longitud GPS de la posición de la pelota

**Campos opcionales:**
- `course_id`: ID del campo de golf (debe ir con hole_number)
- `hole_number`: Número del hoyo (debe ir con course_id)
- `user_id`: ID del usuario/jugador (usa el perfil del jugador si se proporciona)

**Respuesta:** Trayectorias calculadas con algoritmo evolutivo (óptima, riesgo, conservadora) con recomendaciones de palo

---

## Clima

### POST `/weather` o GET `/weather`
Consulta información del clima usando un agente de IA conectado a servicios meteorológicos.

**POST - Campos requeridos:**
- `query`: Consulta sobre el clima en lenguaje natural

**GET - Query parameters:**
- `query`: Consulta sobre el clima en lenguaje natural

**Ejemplos de consultas:**
- "¿Qué tiempo hace en Madrid?"
- "¿Habrá viento mañana en Barcelona?"
- "Temperatura actual en Sevilla"

**Respuesta:** Respuesta del agente sobre el clima

---

## Notas Generales

### Autenticación
- Los endpoints que requieren autenticación deben incluir el token JWT en el header `Authorization: Bearer <token>`
- El token se obtiene mediante los endpoints de autenticación (`/auth/login`, `/auth/register`, etc.)

### Formato de Respuestas
- Todas las respuestas están en formato JSON
- Los códigos de estado HTTP siguen el estándar REST:
  - `200`: Éxito
  - `201`: Creado exitosamente
  - `400`: Error de validación/Bad Request
  - `401`: No autenticado
  - `404`: No encontrado
  - `500`: Error del servidor

### Coordenadas GPS
- Los endpoints de golf que usan coordenadas aceptan `latitude` y `longitude` como números decimales
- Si no se proporcionan `course_id` y `hole_number`, el sistema intenta identificarlos automáticamente desde las coordenadas
- `course_id` y `hole_number` deben proporcionarse juntos si se usan

### Base URL
Por defecto, el servicio corre en `http://localhost:5000` (configurable en `main.py`)

