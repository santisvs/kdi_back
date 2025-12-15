# Diseño de Base de Datos: Perfil de Jugador de Golf

## Resumen

Este documento describe la estructura de base de datos diseñada para gestionar el perfil de jugadores de golf, incluyendo sus estadísticas de distancia y error por cada palo.

## Estructura de Tablas

### 1. Tabla `user` (Usuarios/Jugadores)

Almacena la información básica de los usuarios del sistema.

**Campos:**
- `id` (SERIAL PRIMARY KEY): Identificador único del usuario
- `email` (TEXT UNIQUE NOT NULL): Email del usuario (único)
- `username` (TEXT UNIQUE NOT NULL): Nombre de usuario (único)
- `first_name` (TEXT): Nombre del usuario
- `last_name` (TEXT): Apellido del usuario
- `phone` (TEXT): Teléfono de contacto
- `date_of_birth` (DATE): Fecha de nacimiento
- `created_at` (TIMESTAMP): Fecha de creación del registro
- `updated_at` (TIMESTAMP): Fecha de última actualización

**Índices:**
- `idx_user_email`: Búsqueda rápida por email
- `idx_user_username`: Búsqueda rápida por username

**Relaciones:**
- Un usuario puede tener un perfil de jugador (relación 1:1 con `player_profile`)

---

### 2. Tabla `player_profile` (Perfil de Jugador)

Almacena información específica del perfil de golf de un usuario.

**Campos:**
- `id` (SERIAL PRIMARY KEY): Identificador único del perfil
- `user_id` (INT UNIQUE NOT NULL): Referencia al usuario (FK a `user.id`)
- `handicap` (DECIMAL(5,2)): Handicap del jugador (ej: 12.5)
- `preferred_hand` (TEXT): Mano preferida del jugador
  - Valores permitidos: `'right'`, `'left'`, `'ambidextrous'`
- `years_playing` (INT): Años de experiencia jugando golf
- `skill_level` (TEXT): Nivel de habilidad del jugador
  - Valores permitidos: `'beginner'`, `'intermediate'`, `'advanced'`, `'professional'`
- `notes` (TEXT): Notas adicionales sobre el jugador
- `created_at` (TIMESTAMP): Fecha de creación del perfil
- `updated_at` (TIMESTAMP): Fecha de última actualización

**Índices:**
- `idx_player_profile_user_id`: Búsqueda rápida por usuario

**Relaciones:**
- Pertenece a un usuario (FK a `user.id`)
- Puede tener múltiples estadísticas de palos (relación 1:N con `player_club_statistics`)

---

### 3. Tabla `golf_club` (Catálogo de Palos de Golf)

Catálogo de palos de golf disponibles en el sistema.

**Campos:**
- `id` (SERIAL PRIMARY KEY): Identificador único del palo
- `name` (TEXT UNIQUE NOT NULL): Nombre del palo (ej: "Driver", "Hierro 7", "Wedge")
- `type` (TEXT NOT NULL): Tipo de palo
  - Valores permitidos: `'driver'`, `'wood'`, `'hybrid'`, `'iron'`, `'wedge'`, `'putter'`
- `number` (INT): Número del palo (para hierros, maderas, etc.)
  - Ejemplos: 3, 5, 7, 9 para hierros
  - NULL para palos sin número (driver, putter, algunos wedges)
- `description` (TEXT): Descripción del palo
- `created_at` (TIMESTAMP): Fecha de creación del registro

**Índices:**
- `idx_golf_club_name`: Búsqueda rápida por nombre
- `idx_golf_club_type`: Búsqueda rápida por tipo

**Relaciones:**
- Puede tener múltiples estadísticas de jugadores (relación 1:N con `player_club_statistics`)

**Datos Predefinidos:**
El sistema incluye un script de seed que inserta los palos más comunes:
- **Drivers**: Driver
- **Woods**: Madera 3, Madera 5
- **Hybrids**: Híbrido 3, Híbrido 4, Híbrido 5
- **Irons**: Hierro 3, 4, 5, 6, 7, 8, 9
- **Wedges**: Pitching Wedge, Sand Wedge, Gap Wedge, Lob Wedge
- **Putters**: Putter

---

### 4. Tabla `player_club_statistics` (Estadísticas por Palo)

Almacena las estadísticas de distancia y error para cada combinación de jugador y palo.

**Campos:**
- `id` (SERIAL PRIMARY KEY): Identificador único de la estadística
- `player_profile_id` (INT NOT NULL): Referencia al perfil del jugador (FK a `player_profile.id`)
- `golf_club_id` (INT NOT NULL): Referencia al palo (FK a `golf_club.id`)
- `average_distance_meters` (DECIMAL(8,2) NOT NULL): Distancia promedio en metros
- `min_distance_meters` (DECIMAL(8,2)): Distancia mínima registrada
- `max_distance_meters` (DECIMAL(8,2)): Distancia máxima registrada
- `average_error_meters` (DECIMAL(8,2) NOT NULL): Error promedio en metros
  - Representa la desviación promedio del objetivo
- `error_std_deviation` (DECIMAL(8,2)): Desviación estándar del error
  - Indica la consistencia del jugador con ese palo
- `shots_recorded` (INT DEFAULT 0): Número de golpes registrados para calcular estas estadísticas
- `last_updated` (TIMESTAMP): Fecha de última actualización de las estadísticas
- `created_at` (TIMESTAMP): Fecha de creación del registro

**Restricciones:**
- `UNIQUE(player_profile_id, golf_club_id)`: Un jugador solo puede tener una estadística por palo

**Índices:**
- `idx_player_club_stats_profile`: Búsqueda rápida por perfil de jugador
- `idx_player_club_stats_club`: Búsqueda rápida por palo
- `idx_player_club_stats_distance`: Búsqueda por distancia (útil para consultas de recomendación)

**Relaciones:**
- Pertenece a un perfil de jugador (FK a `player_profile.id`)
- Pertenece a un palo de golf (FK a `golf_club.id`)

---

## Diagrama de Relaciones

```
┌─────────────┐
│    user     │
│─────────────│
│ id (PK)     │
│ email       │
│ username    │
│ first_name  │
│ last_name   │
│ ...         │
└──────┬──────┘
       │ 1:1
       │
       ▼
┌─────────────────────┐
│  player_profile     │
│─────────────────────│
│ id (PK)             │
│ user_id (FK, UNIQUE)│
│ handicap            │
│ preferred_hand      │
│ skill_level         │
│ ...                 │
└──────┬──────────────┘
       │ 1:N
       │
       ▼
┌──────────────────────────────┐
│ player_club_statistics       │
│──────────────────────────────│
│ id (PK)                      │
│ player_profile_id (FK)        │
│ golf_club_id (FK)             │
│ average_distance_meters       │
│ average_error_meters          │
│ error_std_deviation           │
│ shots_recorded                │
│ ...                           │
│ UNIQUE(profile_id, club_id)   │
└──────┬─────────────────────────┘
       │ N:1
       │
       ▼
┌─────────────┐
│ golf_club   │
│─────────────│
│ id (PK)     │
│ name        │
│ type        │
│ number      │
│ ...         │
└─────────────┘
```

## Casos de Uso

### 1. Registrar un nuevo jugador
1. Crear registro en `user`
2. Crear registro en `player_profile` asociado al usuario
3. Opcionalmente, crear estadísticas iniciales en `player_club_statistics`

### 2. Registrar estadísticas de un golpe
1. Identificar el jugador (`user` → `player_profile`)
2. Identificar el palo usado (`golf_club`)
3. Actualizar o crear registro en `player_club_statistics`:
   - Recalcular `average_distance_meters`
   - Recalcular `average_error_meters`
   - Actualizar `min_distance_meters` y `max_distance_meters` si corresponde
   - Recalcular `error_std_deviation`
   - Incrementar `shots_recorded`

### 3. Obtener recomendación de palo basada en perfil
1. Consultar `player_club_statistics` del jugador
2. Filtrar palos que tengan distancia promedio cercana a la distancia objetivo
3. Considerar el `average_error_meters` para elegir el palo más preciso
4. Considerar `error_std_deviation` para evaluar consistencia

### 4. Consultar perfil completo de un jugador
```sql
SELECT 
    u.id,
    u.email,
    u.username,
    pp.handicap,
    pp.skill_level,
    gc.name AS club_name,
    pcs.average_distance_meters,
    pcs.average_error_meters,
    pcs.shots_recorded
FROM "user" u
INNER JOIN player_profile pp ON u.id = pp.user_id
LEFT JOIN player_club_statistics pcs ON pp.id = pcs.player_profile_id
LEFT JOIN golf_club gc ON pcs.golf_club_id = gc.id
WHERE u.id = ?
ORDER BY gc.type, gc.number;
```

## Ejemplos de Consultas Útiles

### Obtener estadísticas de un jugador por palo
```sql
SELECT 
    gc.name,
    gc.type,
    pcs.average_distance_meters,
    pcs.average_error_meters,
    pcs.shots_recorded
FROM player_club_statistics pcs
INNER JOIN golf_club gc ON pcs.golf_club_id = gc.id
WHERE pcs.player_profile_id = ?
ORDER BY pcs.average_distance_meters DESC;
```

### Encontrar el palo más preciso de un jugador
```sql
SELECT 
    gc.name,
    pcs.average_distance_meters,
    pcs.average_error_meters
FROM player_club_statistics pcs
INNER JOIN golf_club gc ON pcs.golf_club_id = gc.id
WHERE pcs.player_profile_id = ?
  AND pcs.shots_recorded >= 10  -- Mínimo de golpes para considerar estadística válida
ORDER BY pcs.average_error_meters ASC
LIMIT 1;
```

### Encontrar palos que alcancen una distancia objetivo
```sql
SELECT 
    gc.name,
    pcs.average_distance_meters,
    pcs.average_error_meters,
    ABS(pcs.average_distance_meters - ?) AS distance_diff
FROM player_club_statistics pcs
INNER JOIN golf_club gc ON pcs.golf_club_id = gc.id
WHERE pcs.player_profile_id = ?
  AND pcs.average_distance_meters BETWEEN ? - 20 AND ? + 20  -- Rango de ±20 metros
ORDER BY distance_diff ASC;
```

## Migraciones

### Crear todas las tablas
```bash
python -m kdi_back.infrastructure.db.migrations_player create_all
```

### Recrear todas las tablas (elimina y vuelve a crear)
```bash
python -m kdi_back.infrastructure.db.migrations_player recreate_all
```

### Insertar palos de golf comunes
```bash
python -m kdi_back.infrastructure.db.migrations_player seed_clubs
```

### Eliminar todas las tablas
```bash
python -m kdi_back.infrastructure.db.migrations_player drop_all
```

## Consideraciones de Diseño

### Ventajas de este diseño:
1. **Normalización**: Datos organizados en tablas separadas para evitar redundancia
2. **Flexibilidad**: Fácil agregar nuevos palos o campos sin afectar datos existentes
3. **Escalabilidad**: Permite múltiples estadísticas por jugador sin límites
4. **Integridad**: Claves foráneas y restricciones UNIQUE garantizan consistencia
5. **Rendimiento**: Índices optimizan consultas frecuentes

### Campos de error:
- `average_error_meters`: Error promedio del jugador con ese palo
- `error_std_deviation`: Desviación estándar del error (consistencia)
- Estos campos permiten evaluar tanto la precisión como la consistencia del jugador

### Extensibilidad futura:
El diseño permite fácilmente agregar:
- Estadísticas por condiciones (viento, lluvia, etc.)
- Estadísticas por tipo de terreno (fairway, rough, bunker, etc.)
- Historial de golpes individuales
- Comparativas entre jugadores
- Estadísticas temporales (mejora a lo largo del tiempo)

## Integración con el Sistema Actual

Esta estructura se integra con el sistema existente de golf:
- Las recomendaciones de palo pueden usar las estadísticas del jugador
- El agente `next_shot_agent` puede considerar el perfil del jugador
- Las distancias calculadas pueden compararse con las estadísticas del jugador

