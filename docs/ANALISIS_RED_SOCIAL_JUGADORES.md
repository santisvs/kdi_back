# Análisis de Funcionalidades de Red Social - Dominio Jugadores

## Resumen Ejecutivo

Este documento analiza las funcionalidades solicitadas para convertir el dominio de jugadores en una red social, identificando qué está implementado, qué falta y los pasos para implementarlo.

---

## 1. Funcionalidades SIN Autenticación

### 1.1 Crear un usuario jugador con estadísticas estándar según género y nivel

**Estado:** ✅ **IMPLEMENTADO PARCIALMENTE**

**Implementación Actual:**
- ✅ Endpoint: `POST /player` (requiere auth, pero podría modificarse)
- ✅ Endpoint: `POST /auth/register` (crea usuario sin perfil)
- ✅ Lógica de inicialización de estadísticas por género y nivel existe en `PlayerService.create_user_with_profile()`
- ✅ Función `get_default_distances(gender, skill_level)` en `player_statistics_data.py`

**Problemas:**
- ⚠️ `POST /player` requiere autenticación (`@require_auth`), pero el usuario aún no existe
- ⚠️ `POST /auth/register` crea usuario pero NO crea perfil automáticamente
- ⚠️ No hay endpoint unificado que cree usuario + perfil + estadísticas en un solo paso sin auth

**Lo que falta:**
- ❌ Endpoint público `POST /auth/register-with-profile` que:
  - Cree usuario
  - Cree perfil con género y nivel
  - Inicialice estadísticas automáticamente
  - Retorne token JWT

**Pasos para implementar:**

1. **Modificar `POST /auth/register` para aceptar perfil opcional:**
   ```python
   # En auth.py, modificar register() para aceptar:
   - gender (opcional)
   - skill_level (opcional)
   # Si se proporcionan, crear perfil automáticamente
   ```

2. **O crear nuevo endpoint `POST /auth/register-complete`:**
   - Combinar registro + creación de perfil
   - Inicializar estadísticas si se proporciona género y nivel
   - Retornar token JWT

3. **Modificar `AuthService.register_user()` para:**
   - Aceptar parámetros opcionales de perfil
   - Llamar a `PlayerService` después de crear usuario
   - Inicializar estadísticas automáticamente

**Archivos a modificar:**
- `src/kdi_back/api/routes/auth.py` - Añadir parámetros opcionales
- `src/kdi_back/domain/services/auth_service.py` - Integrar creación de perfil
- `src/kdi_back/api/dependencies.py` - Asegurar que PlayerService esté disponible

---

### 1.2 Logarse

**Estado:** ✅ **COMPLETAMENTE IMPLEMENTADO**

**Implementación Actual:**
- ✅ Endpoint: `POST /auth/login`
- ✅ Validación de credenciales
- ✅ Generación de token JWT
- ✅ Retorna usuario y token

**No requiere cambios.**

---

## 2. Funcionalidades CON Autenticación

### 2.1 Deslogarse

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint `POST /auth/logout`
- ❌ Invalidar token JWT en la base de datos
- ❌ Sistema de revocación de tokens

**Pasos para implementar:**

1. **Añadir método en `AuthRepository`:**
   ```python
   def revoke_token(self, token: str) -> None:
       """Marca un token como revocado"""
   ```

2. **Añadir método en `AuthService`:**
   ```python
   def logout_user(self, token: str) -> None:
       """Invalida el token del usuario"""
   ```

3. **Crear endpoint en `auth.py`:**
   ```python
   @auth_bp.route('/auth/logout', methods=['POST'])
   @require_auth
   def logout():
       token = request.headers.get('Authorization').replace('Bearer ', '')
       auth_service.logout_user(token)
       return jsonify({"message": "Sesión cerrada exitosamente"}), 200
   ```

4. **Modificar `auth_middleware.py` para verificar tokens revocados**

**Archivos a crear/modificar:**
- `src/kdi_back/domain/ports/auth_repository.py` - Añadir método
- `src/kdi_back/infrastructure/db/repositories/auth_repository_sql.py` - Implementar
- `src/kdi_back/domain/services/auth_service.py` - Añadir método
- `src/kdi_back/api/routes/auth.py` - Añadir endpoint
- `src/kdi_back/api/middleware/auth_middleware.py` - Verificar tokens revocados

**Tabla necesaria:**
- Ya existe `auth_tokens` con campo `revoked_at` (verificar si está implementado)

---

### 2.2 Ver información del jugador (datos personales)

**Estado:** ✅ **IMPLEMENTADO PARCIALMENTE**

**Implementación Actual:**
- ✅ Endpoint: `GET /player/profile` - Retorna perfil del jugador autenticado
- ⚠️ Solo retorna perfil, no datos personales del usuario

**Lo que falta:**
- ❌ Endpoint que retorne datos personales + perfil juntos
- ❌ Endpoint para ver datos personales de otros jugadores (público)

**Pasos para implementar:**

1. **Modificar `GET /player/profile` para incluir datos personales:**
   ```python
   # Incluir en la respuesta:
   - email
   - username
   - first_name
   - last_name
   - phone
   - date_of_birth
   - perfil completo
   ```

2. **O crear nuevo endpoint `GET /player/me`:**
   - Retornar usuario completo + perfil
   - Más claro semánticamente

**Archivos a modificar:**
- `src/kdi_back/api/routes/player.py` - Modificar o crear endpoint

---

### 2.3 Editar información del jugador (datos personales)

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint `PUT /player/me` o `PATCH /player/me`
- ❌ Método en `PlayerService` para actualizar usuario
- ❌ Método en `PlayerRepository` para actualizar usuario

**Pasos para implementar:**

1. **Añadir método en `PlayerRepository` (puerto):**
   ```python
   def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
       """Actualiza datos del usuario"""
   ```

2. **Añadir método en `PlayerService`:**
   ```python
   def update_user_info(self, user_id: int, **kwargs) -> Dict[str, Any]:
       """Actualiza información del usuario con validaciones"""
   ```

3. **Crear endpoint en `player.py`:**
   ```python
   @player_bp.route('/player/me', methods=['PUT'])
   @require_auth
   def update_my_info():
       # Actualizar campos permitidos
   ```

**Archivos a crear/modificar:**
- `src/kdi_back/domain/ports/player_repository.py` - Añadir método
- `src/kdi_back/infrastructure/db/repositories/player_repository_sql.py` - Implementar
- `src/kdi_back/domain/services/player_service.py` - Añadir método
- `src/kdi_back/api/routes/player.py` - Añadir endpoint

**Validaciones necesarias:**
- Email único (si se cambia)
- Username único (si se cambia)
- Formato de email válido
- Formato de fecha válido

---

### 2.4 Eliminar usuario

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Implementación Actual:**
- ✅ Script `delete_player.py` existe pero NO es un endpoint
- ✅ Lógica de eliminación implementada (cascada)

**Lo que falta:**
- ❌ Endpoint `DELETE /player/me`
- ❌ Integración con servicio de dominio
- ❌ Validaciones de seguridad (confirmación, etc.)

**Pasos para implementar:**

1. **Añadir método en `PlayerService`:**
   ```python
   def delete_user(self, user_id: int, confirmation: str) -> None:
       """Elimina usuario con confirmación"""
   ```

2. **Crear endpoint en `player.py`:**
   ```python
   @player_bp.route('/player/me', methods=['DELETE'])
   @require_auth
   def delete_my_account():
       # Requerir confirmación (password o token especial)
       # Eliminar usuario (cascada elimina perfil, estadísticas, etc.)
   ```

**Archivos a crear/modificar:**
- `src/kdi_back/domain/services/player_service.py` - Añadir método
- `src/kdi_back/api/routes/player.py` - Añadir endpoint
- Reutilizar lógica de `delete_player.py`

**Consideraciones:**
- Requerir confirmación (password o token)
- Opcional: soft delete (marcar como eliminado en lugar de borrar)
- Revocar todos los tokens del usuario

---

### 2.5 Ver perfil de jugador

#### 2.5.1 Historial de partidos

**Estado:** ✅ **IMPLEMENTADO PARCIALMENTE**

**Implementación Actual:**
- ✅ Endpoint: `GET /match/player/<user_id>` - Retorna partidos de un jugador
- ⚠️ Requiere conocer `user_id` del jugador
- ⚠️ No está integrado en el perfil del jugador

**Lo que falta:**
- ❌ Endpoint `GET /player/<user_id>/profile` que incluya historial
- ❌ Endpoint `GET /player/<user_id>/matches` más específico
- ❌ Filtros por estado (completed, in_progress)
- ❌ Paginación para muchos partidos

**Pasos para implementar:**

1. **Crear endpoint `GET /player/<user_id>/profile`:**
   ```python
   @player_bp.route('/player/<int:user_id>/profile', methods=['GET'])
   @require_auth
   def get_player_profile(user_id):
       # Retornar perfil + estadísticas + historial de partidos
   ```

2. **Mejorar `GET /match/player/<user_id>`:**
   - Añadir query params: `?status=completed&limit=10&offset=0`
   - Retornar más información (campos, fechas, resultados)

**Archivos a modificar:**
- `src/kdi_back/api/routes/player.py` - Añadir endpoint
- `src/kdi_back/api/routes/match.py` - Mejorar endpoint existente

---

#### 2.5.2 Estadísticas avanzadas (valores por cada palo)

**Estado:** ✅ **IMPLEMENTADO**

**Implementación Actual:**
- ✅ Endpoint: `GET /player/club-statistics` - Retorna estadísticas por palo
- ✅ Incluye: distancia promedio, error, desviación estándar, etc.

**Mejoras sugeridas:**
- ⚠️ Añadir estadísticas agregadas (total de golpes, mejor palo, etc.)
- ⚠️ Añadir gráficos de progreso (si se almacena historial)

**No requiere cambios críticos, solo mejoras opcionales.**

---

### 2.6 Editar perfil de jugador

#### 2.6.1 Añadir/Editar/Eliminar palos

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint para añadir palo a estadísticas del jugador
- ❌ Endpoint para editar estadísticas de un palo
- ❌ Endpoint para eliminar palo de estadísticas
- ❌ Validación de que el palo existe en el catálogo

**Pasos para implementar:**

1. **Añadir métodos en `PlayerRepository`:**
   ```python
   def add_club_to_player(self, player_profile_id: int, club_id: int, 
                          initial_distance: float) -> Dict[str, Any]:
       """Añade un palo a las estadísticas del jugador"""
   
   def update_club_statistics(self, player_profile_id: int, club_id: int,
                             **kwargs) -> Dict[str, Any]:
       """Actualiza estadísticas de un palo"""
   
   def remove_club_from_player(self, player_profile_id: int, club_id: int) -> None:
       """Elimina un palo de las estadísticas del jugador"""
   ```

2. **Añadir métodos en `PlayerService`:**
   ```python
   def add_club(self, user_id: int, club_id: int, initial_distance: float):
       """Añade palo con validaciones"""
   
   def update_club_stats(self, user_id: int, club_id: int, **kwargs):
       """Actualiza estadísticas con validaciones"""
   
   def remove_club(self, user_id: int, club_id: int):
       """Elimina palo con validaciones"""
   ```

3. **Crear endpoints en `player.py`:**
   ```python
   POST   /player/clubs              # Añadir palo
   PUT    /player/clubs/<club_id>   # Editar estadísticas
   DELETE /player/clubs/<club_id>   # Eliminar palo
   ```

**Archivos a crear/modificar:**
- `src/kdi_back/domain/ports/player_repository.py` - Añadir métodos
- `src/kdi_back/infrastructure/db/repositories/player_repository_sql.py` - Implementar
- `src/kdi_back/domain/services/player_service.py` - Añadir métodos
- `src/kdi_back/api/routes/player.py` - Añadir endpoints

**Validaciones necesarias:**
- Verificar que el palo existe en `golf_club`
- Verificar que el jugador no tiene ya ese palo (para añadir)
- Validar valores de distancia (positivos, razonables)

---

#### 2.6.2 Editar estadísticas avanzadas (por cada palo)

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Implementación Actual:**
- ✅ Las estadísticas se actualizan automáticamente después de cada golpe
- ❌ No hay endpoint para editar manualmente

**Lo que falta:**
- ❌ Endpoint para editar estadísticas manualmente
- ❌ Validación de que los valores son razonables

**Pasos para implementar:**

1. **Reutilizar método `update_club_statistics` del punto anterior**
2. **Crear endpoint:**
   ```python
   PUT /player/clubs/<club_id>/statistics
   Body: {
       "average_distance_meters": 150.5,
       "max_distance_meters": 180.0,
       "average_error_meters": 12.3
   }
   ```

**Archivos a modificar:**
- Mismos que en 2.6.1

---

### 2.7 Buscar jugadores

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint de búsqueda de jugadores
- ❌ Búsqueda por username, nombre, email
- ❌ Filtros (handicap, nivel, etc.)
- ❌ Paginación

**Pasos para implementar:**

1. **Añadir método en `PlayerRepository`:**
   ```python
   def search_players(self, query: str, limit: int = 20, offset: int = 0,
                     filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
       """Busca jugadores por query y filtros"""
   ```

2. **Añadir método en `PlayerService`:**
   ```python
   def search_players(self, query: str, **kwargs) -> List[Dict[str, Any]]:
       """Busca jugadores con validaciones"""
   ```

3. **Crear endpoint en `player.py`:**
   ```python
   GET /player/search?q=username&handicap_min=10&handicap_max=20&limit=20&offset=0
   ```

**Archivos a crear/modificar:**
- `src/kdi_back/domain/ports/player_repository.py` - Añadir método
- `src/kdi_back/infrastructure/db/repositories/player_repository_sql.py` - Implementar
- `src/kdi_back/domain/services/player_service.py` - Añadir método
- `src/kdi_back/api/routes/player.py` - Añadir endpoint

**Consideraciones:**
- Búsqueda por username (LIKE)
- Búsqueda por nombre (first_name, last_name)
- Filtros opcionales: handicap, skill_level, gender
- Paginación obligatoria
- No retornar información sensible (email completo, etc.)

---

### 2.8 Ver perfil de otros jugadores

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint `GET /player/<user_id>/profile` público
- ❌ Determinar qué información es pública vs privada
- ❌ Verificación de que el jugador existe

**Pasos para implementar:**

1. **Crear endpoint en `player.py`:**
   ```python
   @player_bp.route('/player/<int:user_id>/profile', methods=['GET'])
   @require_auth  # Requiere auth pero puede ver otros perfiles
   def get_player_profile(user_id):
       # Retornar perfil público del jugador
       # Incluir: username, nombre, handicap, estadísticas, partidos públicos
   ```

2. **Definir qué es público:**
   - ✅ Público: username, nombre, handicap, estadísticas agregadas, partidos completados
   - ❌ Privado: email, teléfono, fecha nacimiento exacta

**Archivos a crear/modificar:**
- `src/kdi_back/api/routes/player.py` - Añadir endpoint
- `src/kdi_back/domain/services/player_service.py` - Añadir método `get_public_profile()`

---

### 2.9 Comparar mis estadísticas con otro jugador

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Endpoint de comparación
- ❌ Lógica de comparación de estadísticas
- ❌ Formato de respuesta comparativa

**Pasos para implementar:**

1. **Añadir método en `PlayerService`:**
   ```python
   def compare_statistics(self, user_id_1: int, user_id_2: int) -> Dict[str, Any]:
       """Compara estadísticas de dos jugadores"""
   ```

2. **Crear endpoint en `player.py`:**
   ```python
   GET /player/compare?user_id=123
   # Compara jugador autenticado con user_id
   ```

3. **Lógica de comparación:**
   - Comparar distancias por palo
   - Comparar errores promedio
   - Comparar handicap
   - Comparar estadísticas de partidos (promedio de golpes, etc.)

**Archivos a crear/modificar:**
- `src/kdi_back/domain/services/player_service.py` - Añadir método
- `src/kdi_back/api/routes/player.py` - Añadir endpoint

**Formato de respuesta sugerido:**
```json
{
  "player_1": {...},
  "player_2": {...},
  "comparison": {
    "handicap_difference": 2.5,
    "average_distance_difference": 15.3,
    "better_clubs": [...],
    "worse_clubs": [...]
  }
}
```

---

### 2.10 Seguir a otros jugadores

**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que falta:**
- ❌ Tabla `user_follows` en base de datos
- ❌ Endpoints CRUD para seguir/dejar de seguir
- ❌ Endpoint para ver seguidos/seguidores
- ❌ Validaciones (no seguirse a sí mismo, etc.)

**Pasos para implementar:**

1. **Crear migración para tabla `user_follows`:**
   ```sql
   CREATE TABLE user_follows (
       id SERIAL PRIMARY KEY,
       follower_id INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
       following_id INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       UNIQUE(follower_id, following_id),
       CHECK(follower_id != following_id)
   );
   ```

2. **Crear repositorio `FollowRepository`:**
   ```python
   class FollowRepository(ABC):
       def follow_user(self, follower_id: int, following_id: int) -> Dict
       def unfollow_user(self, follower_id: int, following_id: int) -> None
       def get_followers(self, user_id: int) -> List[Dict]
       def get_following(self, user_id: int) -> List[Dict]
       def is_following(self, follower_id: int, following_id: int) -> bool
   ```

3. **Crear servicio `FollowService`:**
   ```python
   class FollowService:
       def follow_user(self, follower_id: int, following_id: int)
       def unfollow_user(self, follower_id: int, following_id: int)
       def get_followers(self, user_id: int)
       def get_following(self, user_id: int)
   ```

4. **Crear endpoints en `player.py`:**
   ```python
   POST   /player/<user_id>/follow      # Seguir jugador
   DELETE /player/<user_id>/follow      # Dejar de seguir
   GET    /player/<user_id>/followers   # Ver seguidores
   GET    /player/<user_id>/following   # Ver seguidos
   GET    /player/me/following           # Ver a quién sigo
   GET    /player/me/followers           # Ver quién me sigue
   ```

**Archivos a crear:**
- `src/kdi_back/infrastructure/db/migrations_follow.py` - Migración
- `src/kdi_back/domain/ports/follow_repository.py` - Puerto
- `src/kdi_back/infrastructure/db/repositories/follow_repository_sql.py` - Implementación
- `src/kdi_back/domain/services/follow_service.py` - Servicio
- `src/kdi_back/api/routes/player.py` - Endpoints (o crear `follow.py`)

**Validaciones necesarias:**
- No seguirse a sí mismo
- No seguir dos veces al mismo usuario
- Verificar que el usuario a seguir existe

---

## 3. Resumen de Estado

### ✅ Funcionalidades Implementadas (4/13)

1. ✅ Logarse
2. ✅ Ver perfil de jugador (parcial - solo propio)
3. ✅ Ver estadísticas avanzadas (valores por palo)
4. ✅ Historial de partidos (parcial - endpoint existe pero no integrado)

### ⚠️ Funcionalidades Parciales (2/13)

1. ⚠️ Crear usuario con estadísticas (existe pero requiere auth)
2. ⚠️ Ver información del jugador (solo perfil, no datos personales)

### ❌ Funcionalidades Faltantes (7/13)

1. ❌ Deslogarse
2. ❌ Editar información del jugador
3. ❌ Eliminar usuario (existe script pero no endpoint)
4. ❌ Añadir/Editar/Eliminar palos
5. ❌ Editar estadísticas avanzadas manualmente
6. ❌ Buscar jugadores
7. ❌ Ver perfil de otros jugadores
8. ❌ Comparar estadísticas
9. ❌ Seguir a otros jugadores

---

## 4. Plan de Implementación Recomendado

### Fase 1: Funcionalidades Básicas (Prioridad Alta)

1. **Modificar registro para incluir perfil automáticamente**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Ninguna

2. **Implementar deslogarse**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Verificar tabla auth_tokens

3. **Implementar editar información del jugador**
   - Tiempo estimado: 3-4 horas
   - Dependencias: Ninguna

4. **Implementar eliminar usuario**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Reutilizar delete_player.py

**Total Fase 1: 9-13 horas**

### Fase 2: Gestión de Perfil y Estadísticas (Prioridad Media)

5. **Implementar CRUD de palos**
   - Tiempo estimado: 4-5 horas
   - Dependencias: Ninguna

6. **Implementar edición manual de estadísticas**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Reutilizar métodos de CRUD de palos

7. **Mejorar ver perfil (incluir datos personales + historial)**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Ninguna

**Total Fase 2: 8-11 horas**

### Fase 3: Funcionalidades Sociales (Prioridad Media-Alta)

8. **Implementar búsqueda de jugadores**
   - Tiempo estimado: 3-4 horas
   - Dependencias: Ninguna

9. **Implementar ver perfil de otros jugadores**
   - Tiempo estimado: 2-3 horas
   - Dependencias: Ninguna

10. **Implementar comparar estadísticas**
    - Tiempo estimado: 3-4 horas
    - Dependencias: Ninguna

**Total Fase 3: 8-11 horas**

### Fase 4: Sistema de Seguimiento (Prioridad Media)

11. **Implementar seguir a otros jugadores**
    - Tiempo estimado: 6-8 horas
    - Dependencias: Crear migración, repositorio, servicio

**Total Fase 4: 6-8 horas**

### Tiempo Total Estimado: 31-43 horas

---

## 5. Consideraciones Adicionales

### Seguridad

- ✅ Autenticación JWT ya implementada
- ⚠️ Validar que usuarios solo puedan editar su propia información
- ⚠️ Validar que usuarios solo puedan ver información pública de otros
- ⚠️ Implementar rate limiting para búsquedas

### Base de Datos

- ✅ Estructura base lista
- ❌ Necesaria migración para `user_follows`
- ⚠️ Considerar índices para búsquedas (username, nombre)
- ⚠️ Considerar índices para relaciones de seguimiento

### Performance

- ⚠️ Paginación obligatoria en búsquedas
- ⚠️ Cachear perfiles públicos frecuentemente consultados
- ⚠️ Optimizar consultas de comparación

### Privacidad

- ⚠️ Definir qué información es pública vs privada
- ⚠️ Permitir configuración de privacidad (futuro)
- ⚠️ No exponer emails completos en búsquedas

---

## 6. Conclusión

El sistema tiene una **base sólida** con autenticación y gestión básica de perfiles. Para convertirlo en una red social completa, se necesitan principalmente:

1. **Completar CRUD básico** (editar, eliminar)
2. **Añadir funcionalidades sociales** (búsqueda, comparación, seguimiento)
3. **Mejorar gestión de estadísticas** (CRUD de palos)

La implementación es **factible** y no requiere refactorización mayor. El tiempo estimado es **31-43 horas** de desarrollo.

