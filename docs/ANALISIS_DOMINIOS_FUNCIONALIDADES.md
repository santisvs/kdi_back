# Análisis de Dominios y Funcionalidades - KDI Backend

## Resumen Ejecutivo

Este documento analiza los tres dominios principales del sistema (Jugadores, Campos de Golf y Partidos), sus relaciones, funcionalidades actuales y áreas que requieren corrección o completado.

---

## 1. Relaciones entre Dominios

### Diagrama de Relaciones

```
┌─────────────────┐
│   JUGADORES     │
│  (user)         │
└────────┬────────┘
         │ 1:1
         │
         ▼
┌─────────────────┐
│ PLAYER_PROFILE  │
│  (perfil)       │
└────────┬────────┘
         │ 1:N
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ PLAYER_CLUB_    │──────▶│  GOLF_CLUB      │
│ STATISTICS      │  N:1  │  (catálogo)     │
└─────────────────┘      └─────────────────┘

┌─────────────────┐
│  CAMPOS GOLF    │
│ (golf_course)   │
└────────┬────────┘
         │ 1:N
         │
         ▼
┌─────────────────┐
│     HOYO        │
│    (hole)       │
└────────┬────────┘
         │ 1:N
         │
         ├──▶ OBSTACLES (obstacle)
         ├──▶ HOLE_POINTS (hole_point)
         ├──▶ OPTIMAL_SHOTS (optimal_shot)
         └──▶ STRATEGIC_POINTS (strategic_point)

┌─────────────────┐
│    PARTIDOS     │
│    (match)      │
└────────┬────────┘
         │ 1:N (course_id)
         │
         │ 1:N
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  MATCH_PLAYER   │──────▶│   JUGADORES     │
│  (relación)     │  N:1  │    (user)       │
└────────┬────────┘      └─────────────────┘
         │ 1:N
         │
         ├──▶ MATCH_HOLE_SCORE (puntuación por hoyo)
         └──▶ MATCH_STROKE (golpes individuales)
                  │
                  │ N:1
                  │
                  ▼
         ┌─────────────────┐
         │     HOYO        │
         │    (hole)       │
         └─────────────────┘
```

### Relaciones Detalladas

#### 1.1 Jugadores ↔ Campos de Golf
**Relación:** INDIRECTA a través de Partidos
- Los jugadores NO tienen relación directa con campos de golf
- Se relacionan a través de los partidos que juegan
- Un jugador puede jugar en múltiples campos (a través de diferentes partidos)
- Un campo puede tener múltiples jugadores (a través de diferentes partidos)

#### 1.2 Jugadores ↔ Partidos
**Relación:** MUCHOS A MUCHOS (N:N) a través de `match_player`
- Un jugador puede participar en múltiples partidos
- Un partido puede tener múltiples jugadores
- Cada relación `match_player` incluye:
  - `starting_hole_number`: Hoyo donde empieza el jugador
  - `total_strokes`: Total de golpes acumulados (se actualiza automáticamente)

#### 1.3 Partidos ↔ Campos de Golf
**Relación:** MUCHOS A UNO (N:1)
- Un partido pertenece a UN campo de golf (`match.course_id`)
- Un campo de golf puede tener múltiples partidos
- El campo define qué hoyos están disponibles para el partido

#### 1.4 Partidos ↔ Hoyos
**Relación:** INDIRECTA a través de `match_hole_score` y `match_stroke`
- Los partidos se relacionan con hoyos a través de:
  - `match_hole_score`: Puntuación de cada jugador en cada hoyo
  - `match_stroke`: Golpes individuales registrados en cada hoyo
- Un partido puede tener puntuaciones/golpes en múltiples hoyos
- Un hoyo puede aparecer en múltiples partidos

#### 1.5 Jugadores ↔ Estadísticas de Palos
**Relación:** UNO A MUCHOS (1:N)
- Un jugador tiene múltiples estadísticas (una por palo)
- Cada estadística pertenece a un palo del catálogo (`golf_club`)
- Las estadísticas se actualizan automáticamente después de evaluar golpes

---

## 2. Funcionalidades por Dominio

### 2.1 Dominio: JUGADORES

#### Funcionalidades Implementadas ✅

**Gestión de Usuarios:**
- ✅ Crear usuario con perfil de jugador (`POST /player`)
- ✅ Obtener perfil del jugador autenticado (`GET /player/profile`)
- ✅ Validación de datos (email, username, handicap, etc.)
- ✅ Inicialización automática de estadísticas por palo (si se proporciona género y nivel)

**Estadísticas de Palos:**
- ✅ Obtener estadísticas de palos del jugador (`GET /player/club-statistics`)
- ✅ Actualización automática de estadísticas después de evaluar golpes
- ✅ Cálculo de media móvil ponderada para:
  - Distancia promedio
  - Error promedio
  - Desviación estándar

**Autenticación:**
- ✅ Registro/Login tradicional
- ✅ OAuth Google
- ✅ OAuth Instagram
- ✅ Recuperación de contraseña

#### Funcionalidades Faltantes o Incompletas ❌

**Gestión de Perfil:**
- ❌ Actualizar perfil de jugador (handicap, años jugando, etc.)
- ❌ Eliminar perfil de jugador
- ❌ Historial de partidos del jugador (aunque existe endpoint, falta integración completa)

**Estadísticas Avanzadas:**
- ❌ Estadísticas agregadas del jugador:
  - Promedio de golpes por hoyo
  - Mejor hoyo
  - Peor hoyo
  - Evolución del handicap
- ❌ Gráficos de progreso
- ❌ Comparación con otros jugadores

**Gestión de Palos:**
- ❌ Añadir/eliminar palos personalizados
- ❌ Editar distancias manualmente
- ❌ Configurar set de palos favoritos

---

### 2.2 Dominio: CAMPOS DE GOLF

#### Funcionalidades Implementadas ✅

**Gestión de Campos:**
- ✅ Obtener todos los campos (`GET /golf/courses`)
- ✅ Identificar hoyo por GPS (`POST /golf/identify-hole`)
- ✅ Obtener hoyo por ID o por course_id + hole_number

**Análisis Geoespacial:**
- ✅ Calcular distancia a bandera (`POST /golf/distance-to-hole`)
- ✅ Detectar tipo de terreno (`POST /golf/terrain-type`)
- ✅ Encontrar obstáculos en trayectoria (`POST /golf/obstacles-between`)
- ✅ Verificar si bola está en green (`is_ball_on_green`)
- ✅ Calcular distancia entre dos puntos GPS

**Puntos Estratégicos:**
- ✅ Obtener puntos estratégicos de un hoyo
- ✅ Encontrar golpe óptimo más cercano (`POST /golf/nearest-optimal-shot`)
- ✅ Obtener todos los optimal_shots de un hoyo

**Recomendaciones:**
- ✅ Recomendación completa del siguiente golpe (`POST /golf/next-shot`)
- ✅ Opciones de trayectorias con análisis de riesgo (`POST /golf/trajectory-options`)
- ✅ Trayectorias con algoritmo evolutivo (`POST /golf/trajectory-options-evol`)
- ✅ Recomendación de palo basada en distancia y estadísticas del jugador

#### Funcionalidades Faltantes o Incompletas ❌

**Gestión de Campos:**
- ❌ Crear/editar/eliminar campos de golf
- ❌ Importar campos desde archivos JSON (existe script pero no endpoint)
- ❌ Validación de datos de campos (polígonos, puntos, etc.)
- ❌ Gestión de múltiples layouts/tees por campo

**Gestión de Hoyos:**
- ❌ Crear/editar/eliminar hoyos
- ❌ Gestión de obstáculos (CRUD)
- ❌ Gestión de optimal_shots (CRUD)
- ❌ Gestión de strategic_points (CRUD)
- ❌ Gestión de hole_points (tee, flag, etc.)

**Análisis Avanzado:**
- ❌ Análisis de dificultad del hoyo
- ❌ Estadísticas de juego por hoyo (promedio de golpes, etc.)
- ❌ Comparación de campos

---

### 2.3 Dominio: PARTIDOS

#### Funcionalidades Implementadas ✅

**Gestión de Partidos:**
- ✅ Crear partido (`POST /match`)
- ✅ Añadir jugador a partido (`POST /match/<id>/player`)
- ✅ Obtener detalles del partido (`GET /match/<id>`)
- ✅ Obtener partidos por campo (`GET /match/course/<id>`)
- ✅ Obtener partidos por jugador (`GET /match/player/<id>`)
- ✅ Completar partido (`POST /match/<id>/complete`)

**Registro de Golpes:**
- ✅ Registrar puntuación en hoyo (`POST /match/<id>/score`)
- ✅ Incrementar golpes (`POST /match/<id>/increment-strokes`)
- ✅ Crear registro de golpe individual (`create_stroke`)
- ✅ Evaluar golpe automáticamente (`evaluate_stroke`)
- ✅ Evaluar golpes en green (`evaluate_green_strokes`)

**Leaderboard:**
- ✅ Obtener leaderboard del partido (`GET /match/<id>/leaderboard`)
- ✅ Ranking automático por total de golpes
- ✅ Actualización automática de total_strokes

**Estadísticas de Partido:**
- ✅ Obtener puntuaciones de un jugador (`GET /match/<id>/player/<id>/scores`)
- ✅ Completar hoyo y obtener estadísticas (`POST /match/<id>/complete-hole`)
- ✅ Calcular ranking de jugador

#### Funcionalidades Faltantes o Incompletas ❌

**Gestión de Partidos:**
- ❌ Editar partido (nombre, estado)
- ❌ Cancelar partido (existe estado pero no endpoint específico)
- ❌ Eliminar jugador de partido
- ❌ Reanudar partido cancelado
- ❌ Validación: verificar que todos los jugadores completaron todos los hoyos antes de completar

**Registro de Golpes:**
- ❌ Editar/corregir golpe registrado
- ❌ Eliminar golpe
- ❌ Deshacer último golpe
- ❌ Validación: verificar que el jugador está en el partido antes de registrar golpes
- ❌ Validación: verificar que el hoyo existe en el campo del partido

**Estadísticas Avanzadas:**
- ❌ Estadísticas por hoyo en el partido:
  - Promedio de golpes por hoyo
  - Mejor/peor hoyo del partido
  - Comparación entre jugadores por hoyo
- ❌ Historial de cambios en leaderboard
- ❌ Análisis de rendimiento durante el partido

**Evaluación de Golpes:**
- ❌ Re-evaluar golpe (si cambia la posición final)
- ❌ Evaluación manual (sobrescribir evaluación automática)
- ❌ Historial de evaluaciones

---

## 3. Problemas y Áreas de Mejora

### 3.1 Problemas de Integridad

**Validaciones Faltantes:**
1. ❌ No se valida que un jugador esté en un partido antes de registrar golpes
2. ❌ No se valida que el hoyo pertenezca al campo del partido
3. ❌ No se verifica que todos los jugadores completaron todos los hoyos antes de completar partido
4. ❌ No se valida que un jugador no esté duplicado en un partido

**Consistencia de Datos:**
1. ⚠️ `total_strokes` se actualiza automáticamente, pero no hay verificación de consistencia
2. ⚠️ No hay validación de que `starting_hole_number` sea válido para el campo
3. ⚠️ No se valida que `hole_number` en `match_hole_score` corresponda al campo del partido

### 3.2 Funcionalidades Incompletas

**Gestión de Partidos:**
1. ❌ Falta endpoint para cancelar partido explícitamente
2. ❌ Falta endpoint para eliminar jugador de partido
3. ❌ Falta validación de finalización (todos los hoyos completados)

**Gestión de Campos:**
1. ❌ No hay CRUD completo para campos, hoyos, obstáculos
2. ❌ No hay endpoint para importar campos (solo script)
3. ❌ No hay validación de geometrías PostGIS

**Gestión de Jugadores:**
1. ❌ No hay actualización de perfil
2. ❌ No hay eliminación de perfil
3. ❌ Estadísticas agregadas limitadas

### 3.3 Optimizaciones Necesarias

**Consultas:**
1. ⚠️ Algunas consultas podrían optimizarse con índices adicionales
2. ⚠️ Falta caché para datos estáticos (campos, hoyos)
3. ⚠️ Consultas geoespaciales podrían beneficiarse de índices GIST adicionales

**Rendimiento:**
1. ⚠️ Actualización de `total_strokes` podría ser más eficiente
2. ⚠️ Cálculo de leaderboard podría optimizarse para partidos grandes

---

## 4. Priorización de Tareas

### Alta Prioridad 🔴

1. **Validaciones de Integridad:**
   - Validar jugador en partido antes de registrar golpes
   - Validar que hoyo pertenece al campo del partido
   - Validar finalización de partido (todos los hoyos completados)

2. **Gestión Básica de Partidos:**
   - Endpoint para cancelar partido
   - Endpoint para eliminar jugador de partido
   - Endpoint para editar partido

3. **Gestión de Perfil de Jugador:**
   - Endpoint para actualizar perfil
   - Endpoint para eliminar perfil

### Media Prioridad 🟡

1. **CRUD de Campos:**
   - Endpoints para crear/editar/eliminar campos
   - Endpoints para gestionar hoyos, obstáculos, optimal_shots

2. **Corrección de Golpes:**
   - Endpoint para editar/corregir golpe
   - Endpoint para deshacer último golpe

3. **Estadísticas Avanzadas:**
   - Estadísticas agregadas por jugador
   - Estadísticas por hoyo en partido

### Baja Prioridad 🟢

1. **Optimizaciones:**
   - Índices adicionales
   - Caché de datos estáticos

2. **Funcionalidades Avanzadas:**
   - Gráficos de progreso
   - Comparación entre jugadores
   - Análisis de dificultad de hoyos

---

## 5. Resumen de Estado Actual

### ✅ Funcionalidades Completas y Funcionales

- Sistema de autenticación completo
- Creación y gestión básica de partidos
- Registro de golpes con evaluación automática
- Sistema de recomendaciones de golpes (muy completo)
- Análisis geoespacial completo
- Leaderboard automático
- Estadísticas de palos con actualización automática

### ⚠️ Funcionalidades Parciales

- Gestión de partidos (falta cancelar, eliminar jugador)
- Gestión de campos (solo lectura, falta CRUD)
- Gestión de perfil (solo creación, falta actualización)
- Validaciones de integridad (algunas faltan)

### ❌ Funcionalidades Faltantes

- CRUD completo de campos y hoyos
- Actualización/eliminación de perfil
- Corrección de golpes
- Estadísticas avanzadas
- Validaciones de finalización de partido

---

## 6. Recomendaciones

### Inmediatas

1. **Implementar validaciones críticas** antes de continuar con nuevas funcionalidades
2. **Completar CRUD básico** de partidos (cancelar, eliminar jugador)
3. **Añadir actualización de perfil** de jugador

### Corto Plazo

1. **CRUD de campos** para permitir gestión completa
2. **Corrección de golpes** para mejorar experiencia de usuario
3. **Validación de finalización** de partidos

### Largo Plazo

1. **Estadísticas avanzadas** para análisis de rendimiento
2. **Optimizaciones** de rendimiento
3. **Funcionalidades sociales** (comparación, rankings globales)

---

## Conclusión

El sistema tiene una **base sólida** con funcionalidades core implementadas y funcionando. Las principales áreas de mejora son:

1. **Completar validaciones** de integridad
2. **Añadir operaciones CRUD** faltantes
3. **Mejorar gestión** de partidos y jugadores
4. **Implementar correcciones** de datos (editar golpes, etc.)

El sistema está **listo para continuar** con estas mejoras sin necesidad de refactorización mayor.

