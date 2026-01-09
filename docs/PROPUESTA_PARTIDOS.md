# Propuesta de Implementación: Sistema de Partidos (Matches)

## Resumen

Se ha implementado un sistema completo para gestionar partidos de golf en la aplicación. Un partido permite que uno o varios jugadores compitan en el mismo campo de golf, jugando todos los hoyos del campo. El ganador es el jugador con menos golpes al finalizar.

## Estructura de Base de Datos

### Tabla `match`
Almacena la información principal de cada partido:
- `id`: Identificador único del partido
- `course_id`: Referencia al campo de golf donde se juega
- `name`: Nombre opcional del partido
- `status`: Estado del partido (`in_progress`, `completed`, `cancelled`)
- `started_at`: Fecha y hora de inicio
- `completed_at`: Fecha y hora de finalización (cuando se completa)
- `created_at`, `updated_at`: Timestamps de auditoría

### Tabla `match_player`
Relación muchos a muchos entre partidos y jugadores:
- `id`: Identificador único
- `match_id`: Referencia al partido
- `user_id`: Referencia al jugador
- `starting_hole_number`: Hoyo donde empieza el jugador (permite que empiecen en hoyos diferentes)
- `total_strokes`: Total de golpes acumulados (se actualiza automáticamente)
- `created_at`: Timestamp de creación
- **Constraint UNIQUE(match_id, user_id)**: Un jugador solo puede estar una vez en un partido

### Tabla `match_hole_score`
Registra la puntuación de cada jugador en cada hoyo:
- `id`: Identificador único
- `match_player_id`: Referencia a la relación match-player
- `hole_id`: Referencia al hoyo
- `strokes`: Número de golpes en el hoyo
- `completed_at`: Fecha y hora de finalización del hoyo
- `created_at`: Timestamp de creación
- **Constraint UNIQUE(match_player_id, hole_id)**: Un jugador solo puede tener una puntuación por hoyo

## Arquitectura

La implementación sigue el patrón de arquitectura limpia del proyecto:

### 1. Migraciones
**Archivo**: `src/kdi_back/infrastructure/db/migrations_match.py`

Funciones para crear y gestionar las tablas:
- `create_match_table()`: Crea la tabla `match`
- `create_match_player_table()`: Crea la tabla `match_player`
- `create_match_hole_score_table()`: Crea la tabla `match_hole_score`
- `create_all_match_tables()`: Crea todas las tablas en orden
- `drop_all_match_tables()`: Elimina todas las tablas

**Uso**:
```bash
python -m kdi_back.infrastructure.db.migrations_match create_all
python -m kdi_back.infrastructure.db.migrations_match recreate_all
python -m kdi_back.infrastructure.db.migrations_match drop_all
```

### 2. Puerto (Interfaz)
**Archivo**: `src/kdi_back/domain/ports/match_repository.py`

Define la interfaz `MatchRepository` con métodos para:
- Crear partidos
- Añadir jugadores a partidos
- Registrar puntuaciones por hoyo
- Obtener información de partidos, jugadores y leaderboards
- Completar partidos

### 3. Implementación del Repositorio
**Archivo**: `src/kdi_back/infrastructure/db/repositories/match_repository_sql.py`

Implementación SQL de `MatchRepository` usando PostgreSQL:
- `MatchRepositorySQL`: Implementa todas las operaciones de base de datos
- Actualiza automáticamente `total_strokes` cuando se registran golpes
- Calcula leaderboards ordenados por total de golpes

### 4. Servicio de Dominio
**Archivo**: `src/kdi_back/domain/services/match_service.py`

Contiene la lógica de negocio:
- `MatchService`: Valida reglas de negocio y orquesta las operaciones
- Validaciones: IDs positivos, estados válidos, etc.
- Previene operaciones en partidos completados o cancelados

### 5. Rutas API
**Archivo**: `src/kdi_back/api/routes/match.py`

Endpoints REST para gestionar partidos:

#### Crear partido
```
POST /match
Body: {
  "course_id": 1,
  "name": "Partido de fin de semana",
  "player_ids": [1, 2, 3],
  "starting_holes": {1: 1, 2: 5, 3: 10}
}
```

#### Añadir jugador a partido
```
POST /match/<match_id>/player
Body: {
  "user_id": 4,
  "starting_hole_number": 3
}
```

#### Registrar puntuación en hoyo
```
POST /match/<match_id>/score
Body: {
  "user_id": 1,
  "hole_id": 5,
  "strokes": 4
}
```

#### Obtener detalles del partido
```
GET /match/<match_id>
```

#### Completar partido
```
POST /match/<match_id>/complete
```

#### Obtener leaderboard
```
GET /match/<match_id>/leaderboard
```

#### Obtener puntuaciones de un jugador
```
GET /match/<match_id>/player/<user_id>/scores
```

#### Obtener partidos por campo
```
GET /match/course/<course_id>?status=in_progress
```

#### Obtener partidos por jugador
```
GET /match/player/<user_id>?status=completed
```

## Características Principales

### 1. Múltiples Jugadores
- Un partido puede tener 1 o más jugadores
- Cada jugador se añade individualmente al partido

### 2. Inicio Flexible
- Los jugadores pueden empezar en hoyos diferentes
- Se especifica en `starting_hole_number` al añadir el jugador

### 3. Registro de Golpes
- Se registra la puntuación por hoyo para cada jugador
- El sistema actualiza automáticamente el total de golpes

### 4. Leaderboard Automático
- Se calcula automáticamente ordenando por total de golpes (menor a mayor)
- El primer lugar es el ganador

### 5. Estados del Partido
- `in_progress`: Partido en curso
- `completed`: Partido finalizado (se calcula el ganador)
- `cancelled`: Partido cancelado

### 6. Validaciones de Negocio
- No se pueden añadir jugadores a partidos completados
- No se pueden registrar golpes en partidos completados o cancelados
- Un jugador solo puede estar una vez en un partido
- Un jugador solo puede tener una puntuación por hoyo

## Flujo de Uso Típico

1. **Crear partido**: Se crea un partido asociado a un campo de golf
2. **Añadir jugadores**: Se añaden uno o más jugadores (pueden empezar en hoyos diferentes)
3. **Registrar golpes**: A medida que los jugadores completan hoyos, se registran sus golpes
4. **Consultar progreso**: Se puede consultar el leaderboard en cualquier momento
5. **Completar partido**: Cuando todos los jugadores terminan, se completa el partido y se determina el ganador

## Ejemplo de Uso

```python
# 1. Crear partido con 3 jugadores
match_service.create_match(
    course_id=1,
    name="Partido de fin de semana",
    player_ids=[1, 2, 3],
    starting_holes={1: 1, 2: 5, 3: 10}  # Jugador 2 empieza en hoyo 5, jugador 3 en hoyo 10
)

# 2. Registrar golpes del jugador 1 en el hoyo 1
match_service.record_hole_score(match_id=1, user_id=1, hole_id=1, strokes=4)

# 3. Consultar leaderboard
leaderboard = match_service.get_match_leaderboard(match_id=1)

# 4. Completar partido cuando todos terminan
result = match_service.complete_match(match_id=1)
winner = result['winner']  # Jugador con menos golpes
```

## Próximos Pasos (Opcionales)

1. **Validación de hoyos completados**: Verificar que todos los jugadores hayan completado todos los hoyos antes de completar el partido
2. **Historial de partidos**: Endpoint para ver historial de partidos de un jugador
3. **Estadísticas**: Calcular estadísticas agregadas (promedio de golpes, mejor hoyo, etc.)
4. **Notificaciones**: Notificar cuando un jugador completa un hoyo o cuando cambia el leaderboard
5. **Modo de juego**: Añadir diferentes modos (stroke play, match play, etc.)

## Notas Técnicas

- Las tablas usan `ON DELETE CASCADE` para mantener la integridad referencial
- Los índices están optimizados para consultas frecuentes (por match_id, user_id, etc.)
- El total de golpes se actualiza automáticamente al registrar cada golpe
- El sistema permite actualizar puntuaciones (si un jugador registra mal un golpe)

