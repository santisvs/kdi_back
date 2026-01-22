# Simulación de Algoritmo de Recomendación

## Situación Inicial

**Posición del jugador:**
- Distancia al hoyo (flag): **200 metros**
- Terreno: **tee** (punto de salida)
- Distancia máxima alcanzable del jugador: **220 metros** (con driver)

**Puntos Estratégicos Disponibles en el Hoyo:**

| Punto | Tipo | Distancia al Hoyo | Distancia desde Bola | Descripción |
|-------|------|-------------------|---------------------|-------------|
| H | flag | 200m | 200m | Hoyo (bandera) |
| A | strategic_point | 180m | ~180m | Antegreen (approach_zone) |
| B | strategic_point | 100m | ~100m | Mitad de calle (fairway_center_mid) |
| C | strategic_point | 20m | ~20m | Cerca del green (approach_zone) |
| D | strategic_point | 50m | ~50m | Mitad de calle (ya superado) |
| OS | optimal_shot | - | 50m | Optimal shot (endpoint a 150m del hoyo) |

---

## Paso 1: Filtrado de Puntos

**Criterio:** Solo incluir puntos con `distance_to_flag < 200m` (posición actual)

**Resultado del filtrado:**
- ✅ **H (200m)**: `200m < 200m` → ❌ **EXCLUIDO** (es igual, no menor)
- ✅ **A (180m)**: `180m < 200m` → ✅ **INCLUIDO**
- ✅ **B (100m)**: `100m < 200m` → ✅ **INCLUIDO**
- ✅ **C (20m)**: `20m < 200m` → ✅ **INCLUIDO**
- ✅ **D (50m)**: `50m < 200m` → ✅ **INCLUIDO** (aunque "superado", está más cerca del hoyo)
- ✅ **OS (optimal_shot)**: Se evalúa por separado si está a <10m del inicio

**Lista filtrada:** [A, B, C, D]

---

## Paso 2: Ordenamiento

**Criterio:** Ordenar por `distance_to_flag` ASC (más cercano al hoyo primero)

**Orden final:** [C (20m), D (50m), B (100m), A (180m)]

**Orden de evaluación completo:**
1. **H (hoyo)** - siempre primero
2. **C (20m)** - más cercano al hoyo
3. **D (50m)**
4. **B (100m)**
5. **A (180m)** - más lejano al hoyo

---

## Paso 3: Verificación de Optimal Shot

**Criterio:** Si hay optimal_shot a <10m del inicio, evaluarlo primero

**Resultado:**
- Optimal shot está a 50m del inicio → **NO se evalúa** (solo si está a <10m)

---

## Paso 4: Evaluación Paso a Paso

### 4.1 Evaluar Hoyo (H) - 200m

**Cálculos:**
- Distancia: 200m
- ¿Alcanzable? Sí (200m ≤ 220m)
- Obstáculos: Bunkers, rough, árboles
- Palo recomendado: Driver
- Terreno: tee → Driver en tee = riesgo bajo (2.0 puntos)
- Riesgo calculado: **85 puntos**

**Decisión:** ❌ **DESCARTADO**
- **Razón:** Riesgo ≥ 75 (muy alto). Trayectoria directa al green es demasiado arriesgada.

---

### 4.2 Evaluar Punto C - 20m del hoyo

**Cálculos:**
- Distancia desde bola: ~180m (200m - 20m)
- ¿Alcanzable? Sí (180m ≤ 220m)
- Obstáculos: Pocos (cerca del green, zona segura)
- Palo recomendado: Hierro 7
- Terreno: tee → Hierro en tee = riesgo bajo (0.0 puntos)
- Riesgo calculado: **25 puntos**

**Decisión:** ✅ **ACEPTADO COMO ÓPTIMA**
- **Razón:** Riesgo ≤ 30 (óptimo). Es una opción segura y cercana al green.
- **Acción:** Guardar como `direct_trajectory`
- **Flag:** `should_search_conservative = False` (ya tenemos óptima con riesgo bajo)

**Resultado parcial:**
- ✅ Óptima: Punto C (20m del hoyo, 180m desde bola, riesgo 25)
- ⏸️ Conservadora: No buscar (ya tenemos óptima con riesgo ≤ 30)

---

### 4.3 Evaluar Punto D - 50m del hoyo

**Cálculos:**
- Distancia desde bola: ~150m (200m - 50m)
- ¿Alcanzable? Sí (150m ≤ 220m)
- Obstáculos: Moderados
- Palo recomendado: Hierro 6
- Terreno: tee → Hierro en tee = riesgo bajo (0.0 puntos)
- Riesgo calculado: **35 puntos**

**Decisión:** ⏸️ **NO SE EVALÚA** (algoritmo se detiene)
- **Razón:** Ya tenemos una opción óptima (riesgo ≤ 30). El algoritmo no continúa evaluando si ya encontró una óptima con riesgo bajo.

---

### 4.4 Evaluar Punto B - 100m del hoyo

**Decisión:** ⏸️ **NO SE EVALÚA** (algoritmo se detiene)

---

### 4.5 Evaluar Punto A - 180m del hoyo

**Decisión:** ⏸️ **NO SE EVALÚA** (algoritmo se detiene)

---

## Resultado Final

### Recomendación Entregada:

```json
{
  "direct_trajectory": {
    "distance_meters": 180,
    "target": "waypoint",
    "waypoint_description": "Antegreen para chip a 12m de green",
    "risk_level": {
      "total": 25
    },
    "club_recommendation": {
      "recommended_club": "Hierro 7",
      "swing_type": "completo"
    }
  },
  "conservative_trajectory": null,
  "recommended_trajectory": "direct"
}
```

### Mensaje al Jugador:

> "Estás a 200 metros del hoyo. Te recomiendo utilizar el Hierro 7 con swing completo hacia el antegreen, con el objetivo de hacer 180 metros. Esta es una opción segura que te dejará cerca del green para el siguiente golpe."

---

## Caso Alternativo: Si C tuviera Riesgo Alto

**Supongamos que el Punto C tiene riesgo 80:**

### 4.2 Evaluar Punto C - 20m del hoyo

**Riesgo calculado: 80 puntos**

**Decisión:** ❌ **DESCARTADO**
- **Razón:** Riesgo > 75 (muy alto)

### 4.3 Evaluar Punto D - 50m del hoyo

**Riesgo calculado: 35 puntos**

**Decisión:** ✅ **ACEPTADO COMO ÓPTIMA**
- **Razón:** Riesgo entre 30-75 (aceptable). 
- **Acción:** Guardar como `direct_trajectory`
- **Flag:** `should_search_conservative = True` (buscar conservadora porque riesgo > 30)

### 4.4 Evaluar Punto B - 100m del hoyo

**Riesgo calculado: 28 puntos**

**Decisión:** ✅ **ACEPTADO COMO CONSERVADORA**
- **Razón:** Riesgo < 30 (óptimo). Mejor que la óptima actual.
- **Acción:** Intercambiar roles:
  - Nueva óptima: Punto B (riesgo 28)
  - Nueva conservadora: Punto D (riesgo 35)
- **Flag:** `should_search_conservative = False` (ya tenemos óptima con riesgo ≤ 30)

### Resultado Alternativo:

```json
{
  "direct_trajectory": {
    "target": "waypoint",
    "waypoint_description": "Centro calle a 100m de green",
    "risk_level": {"total": 28}
  },
  "conservative_trajectory": {
    "target": "waypoint",
    "waypoint_description": "Centro calle a 50m de green",
    "risk_level": {"total": 35}
  },
  "recommended_trajectory": "direct"
}
```

---

## Resumen de Criterios de Decisión

| Riesgo Total | Decisión | Acción |
|--------------|----------|--------|
| ≤ 30 | ✅ Óptima | Guardar como `direct_trajectory`, no buscar conservadora |
| 30 < riesgo ≤ 75 | ✅ Óptima | Guardar como `direct_trajectory`, buscar conservadora |
| > 75 | ❌ Descartado | Continuar evaluando siguiente punto |
| Si encontramos riesgo < 30 después | 🔄 Intercambiar | Nueva óptima = mejor opción, anterior = conservadora |

---

## Notas Importantes

1. **El hoyo siempre se evalúa primero**, independientemente de su distancia
2. **Los strategic_points se ordenan desde más cercano a más lejano al hoyo**
3. **Solo se incluyen puntos entre la posición actual y el hoyo**
4. **El algoritmo se detiene cuando encuentra una opción óptima con riesgo ≤ 30**
5. **Si la óptima tiene riesgo 30-75, se busca una conservadora con riesgo < 30**
