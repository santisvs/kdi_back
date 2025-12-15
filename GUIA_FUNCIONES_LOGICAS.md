# Guía: Dónde Colocar Funciones Lógicas en la Nueva Estructura

## Arquitectura: Clean Architecture / Hexagonal

La estructura sigue principios de **Clean Architecture** donde el código se organiza en capas:

```
┌─────────────────────────────────────┐
│         API Layer                   │  ← Capa de entrada (HTTP)
│  (api/routes/, api/schemas/)        │
└──────────────┬──────────────────────┘
               │ usa
┌──────────────▼──────────────────────┐
│      Domain Layer                    │  ← Lógica de negocio pura
│  (domain/services/, domain/models/)  │
└──────────────┬──────────────────────┘
               │ depende de
┌──────────────▼──────────────────────┐
│   Domain Ports (Interfaces)          │  ← Contratos/Interfaces
│  (domain/ports/)                     │
└──────────────┬──────────────────────┘
               │ implementado por
┌──────────────▼──────────────────────┐
│   Infrastructure Layer               │  ← Implementaciones técnicas
│  (infrastructure/db/, infrastructure/│
│   agents/, infrastructure/config/)   │
└─────────────────────────────────────┘
```

## Dónde Va Cada Tipo de Función

### 1. **Funciones de Lógica de Negocio** → `domain/services/`

**Ejemplo**: "Identificar en qué hoyo está una bola"

**Ubicación**: `src/kdi_back/domain/services/golf_service.py`

**Características**:
- ✅ Contiene la **lógica de negocio pura**
- ✅ **No depende** de implementaciones técnicas (SQL, HTTP, etc.)
- ✅ Solo depende de **interfaces** (ports)
- ✅ Puede tener **validaciones de negocio**
- ✅ Es **testeable** sin necesidad de base de datos

**Ejemplo creado**:
```python
# domain/services/golf_service.py
class GolfService:
    def identify_hole_by_ball_position(self, latitude, longitude):
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitud inválida")
        
        # Delegar al repositorio (implementación técnica)
        return self.golf_repository.find_hole_by_position(latitude, longitude)
```

---

### 2. **Interfaces/Contratos** → `domain/ports/`

**Ejemplo**: "Cómo obtener un hoyo por posición"

**Ubicación**: `src/kdi_back/domain/ports/golf_repository.py`

**Características**:
- ✅ Define **qué operaciones** necesita el dominio
- ✅ **No define cómo** se implementan
- ✅ Usa **ABC (Abstract Base Classes)** de Python
- ✅ Permite cambiar implementaciones sin afectar el dominio

**Ejemplo creado**:
```python
# domain/ports/golf_repository.py
class GolfRepository(ABC):
    @abstractmethod
    def find_hole_by_position(self, latitude, longitude):
        """Encuentra el hoyo en el que se encuentra una bola"""
        pass
```

---

### 3. **Implementaciones Técnicas (SQL, PostGIS)** → `infrastructure/db/repositories/`

**Ejemplo**: "Consulta SQL para encontrar hoyo por posición"

**Ubicación**: `src/kdi_back/infrastructure/db/repositories/golf_repository_sql.py`

**Características**:
- ✅ Implementa las **interfaces** definidas en `domain/ports/`
- ✅ Contiene **consultas SQL/PostGIS**
- ✅ Maneja **conexiones a base de datos**
- ✅ Puede cambiar sin afectar el dominio

**Ejemplo creado**:
```python
# infrastructure/db/repositories/golf_repository_sql.py
class GolfRepositorySQL(GolfRepository):
    def find_hole_by_position(self, latitude, longitude):
        # Consulta PostGIS
        cur.execute("""
            SELECT h.*
            FROM hole h
            WHERE ST_Contains(
                h.fairway_polygon::geometry,
                ST_SetSRID(ST_Point(%s, %s), 4326)
            )
        """, (longitude, latitude))
        return cur.fetchone()
```

---

### 4. **Endpoints HTTP** → `api/routes/`

**Ejemplo**: "Endpoint POST /golf/identify-hole"

**Ubicación**: `src/kdi_back/api/routes/golf.py`

**Características**:
- ✅ Maneja **peticiones HTTP**
- ✅ **Valida** datos de entrada
- ✅ **Serializa** respuestas JSON
- ✅ Llama a **servicios del dominio**
- ✅ Maneja **errores HTTP**

**Ejemplo creado**:
```python
# api/routes/golf.py
@golf_bp.route('/golf/identify-hole', methods=['POST'])
def identify_hole():
    data = request.get_json()
    latitude = float(data['latitude'])
    longitude = float(data['longitude'])
    
    # Usar servicio de dominio
    golf_service = get_golf_service()
    hole = golf_service.identify_hole_by_ball_position(latitude, longitude)
    
    return jsonify({"hole": hole})
```

---

### 5. **Inicialización de Dependencias** → `api/dependencies.py`

**Ejemplo**: "Crear servicio con su repositorio"

**Ubicación**: `src/kdi_back/api/dependencies.py`

**Características**:
- ✅ **Factory functions** para crear servicios
- ✅ **Inyecta dependencias** (repositorio → servicio)
- ✅ Centraliza la **configuración** de dependencias

**Ejemplo creado**:
```python
# api/dependencies.py
def get_golf_service() -> GolfService:
    golf_repository = GolfRepositorySQL()
    return GolfService(golf_repository)
```

---

## Flujo Completo: Identificar Hoyo

```
1. Cliente HTTP
   ↓ POST /golf/identify-hole {lat, lon}
   
2. API Route (api/routes/golf.py)
   ↓ Valida datos HTTP
   ↓ Obtiene servicio (api/dependencies.py)
   
3. Domain Service (domain/services/golf_service.py)
   ↓ Valida lógica de negocio
   ↓ Llama a repositorio (interfaz)
   
4. Domain Port (domain/ports/golf_repository.py)
   ↓ Define contrato
   
5. Infrastructure Repository (infrastructure/db/repositories/golf_repository_sql.py)
   ↓ Ejecuta SQL/PostGIS
   ↓ Retorna datos
   
6. Domain Service
   ↓ Procesa resultado
   
7. API Route
   ↓ Serializa JSON
   
8. Cliente HTTP
   ← Respuesta JSON
```

## Reglas de Oro

### ✅ SÍ hacer:
- **Lógica de negocio** → `domain/services/`
- **Consultas SQL** → `infrastructure/db/repositories/`
- **Endpoints HTTP** → `api/routes/`
- **Validaciones de negocio** → `domain/services/`
- **Validaciones de formato HTTP** → `api/routes/`

### ❌ NO hacer:
- ❌ SQL en `domain/services/` (rompe la separación de capas)
- ❌ Lógica de negocio en `api/routes/` (debe estar en servicios)
- ❌ Lógica de negocio en `infrastructure/` (debe estar en domain)
- ❌ Dependencias directas entre capas (usar interfaces)

## Ejemplo: Nueva Función "Calcular Distancia al Hoyo"

Si quieres añadir una función para calcular la distancia de la bola al hoyo:

1. **Domain Port** (`domain/ports/golf_repository.py`):
   ```python
   @abstractmethod
   def get_hole_flag_position(self, hole_id: int) -> Optional[Dict]:
       """Obtiene la posición de la bandera de un hoyo"""
       pass
   ```

2. **Domain Service** (`domain/services/golf_service.py`):
   ```python
   def calculate_distance_to_hole(self, ball_lat, ball_lon, hole_id):
       """Calcula distancia de la bola al hoyo"""
       hole = self.golf_repository.get_hole_by_id(hole_id)
       flag = self.golf_repository.get_hole_flag_position(hole_id)
       # Lógica de cálculo...
   ```

3. **Infrastructure Repository** (`infrastructure/db/repositories/golf_repository_sql.py`):
   ```python
   def get_hole_flag_position(self, hole_id):
       cur.execute("""
           SELECT position
           FROM hole_point
           WHERE hole_id = %s AND type = 'flag'
       """, (hole_id,))
   ```

4. **API Route** (`api/routes/golf.py`):
   ```python
   @golf_bp.route('/golf/distance-to-hole', methods=['POST'])
   def distance_to_hole():
       # ...
   ```

## Resumen

| Tipo de Función | Ubicación | Ejemplo |
|----------------|-----------|---------|
| Lógica de negocio | `domain/services/` | `identify_hole_by_ball_position()` |
| Consultas SQL | `infrastructure/db/repositories/` | `find_hole_by_position()` |
| Endpoints HTTP | `api/routes/` | `@golf_bp.route('/golf/identify-hole')` |
| Interfaces | `domain/ports/` | `GolfRepository` |
| Inicialización | `api/dependencies.py` | `get_golf_service()` |

