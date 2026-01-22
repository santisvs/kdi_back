# Simulación Real: Hoyo 1 - Las Rejas

## Información del Hoyo

- **Campo:** Las Rejas Club de Golf
- **Hoyo:** 1
- **Par:** 4
- **Longitud:** 367 metros
- **Tee utilizado:** Tee Amarillas

---

## RECOMENDACIÓN 1: Desde Tee Amarillas

### Situación Inicial

**Posición del jugador:**
- **Ubicación:** Tee Amarillas (Hoyo 1)
- **Coordenadas:** -3.868570058479186, 40.44451991692553
- **Distancia al hoyo (flag):** ~367 metros
- **Terreno:** tee (punto de salida)
- **Distancia máxima alcanzable:** 250 metros (con driver)

**Coordenadas del hoyo (flag):**
- -3.872632222716335, 40.44442363791038

### Puntos Estratégicos Disponibles (Hoyo 1)

| Punto | Tipo | Distancia al Hoyo | Descripción |
|-------|------|------------------|-------------|
| H | flag | 367m | Hoyo (bandera) |
| SP1 | fairway_center_far | 170m | Centro calle antes de bunkers a 170m de green |
| SP2 | fairway_center_mid | 100m | Centro calle a 100m de green |
| SP3 | layup_zone | 57m | Centro calle para approach corto a 57m de green |
| SP4 | approach_zone | 12m | Antegreen para chip a 12m de green |

**Optimal Shot 1:**
- Inicio: Tee (-3.868570058479186, 40.44451991692553)
- Fin: (-3.87094755026384, 40.44445006655005)
- Descripción: "Salida con drive al centro de la calle para dejar la bola a la derecha del segundo bunker de la izquierda"
- Distancia aproximada: ~217 metros

---

## Paso 1: Filtrado de Puntos

**Criterio:** Solo incluir puntos con `distance_to_flag < 367m` (posición actual)

**Resultado del filtrado:**
- ✅ **H (367m)**: `367m < 367m` → ❌ **EXCLUIDO** (es igual, no menor)
- ✅ **SP1 (170m)**: `170m < 367m` → ✅ **INCLUIDO**
- ✅ **SP2 (100m)**: `100m < 367m` → ✅ **INCLUIDO**
- ✅ **SP3 (57m)**: `57m < 367m` → ✅ **INCLUIDO**
- ✅ **SP4 (12m)**: `12m < 367m` → ✅ **INCLUIDO**

**Lista filtrada:** [SP1, SP2, SP3, SP4]

---

## Paso 2: Ordenamiento

**Criterio:** Ordenar por `distance_to_flag` ASC (más cercano al hoyo primero)

**Orden final:** [SP4 (12m), SP3 (57m), SP2 (100m), SP1 (170m)]

**Orden de evaluación completo:**
1. **H (hoyo)** - siempre primero
2. **SP4 (12m)** - más cercano al hoyo
3. **SP3 (57m)**
4. **SP2 (100m)**
5. **SP1 (170m)** - más lejano al hoyo

---

## Paso 3: Verificación de Optimal Shot

**Criterio:** Si hay optimal_shot a <10m del inicio, evaluarlo primero

**Resultado:**
- Optimal shot 1 inicia en el tee (0m de distancia) → ✅ **SE EVALÚA PRIMERO**

**Evaluación del Optimal Shot 1:**
- Distancia desde tee al endpoint: ~217 metros
- ¿Alcanzable? Sí (217m ≤ 250m)
- Obstáculos: Bunkers, rough, árboles (según descripción)
- Palo recomendado: Driver
- Terreno: tee → Driver en tee = riesgo bajo (2.0 puntos)
- Riesgo calculado estimado: **45 puntos**

**Decisión:** ✅ **ACEPTADO COMO ÓPTIMA**
- **Razón:** Riesgo entre 30-75 (aceptable). Es la trayectoria recomendada del diseño del hoyo.
- **Acción:** Guardar como `direct_trajectory`
- **Flag:** `should_search_conservative = True` (buscar conservadora porque riesgo > 30)

---

## Paso 4: Evaluación de Strategic Points (si es necesario)

Como ya tenemos una óptima con riesgo 30-75, buscamos una conservadora con riesgo < 30.

### 4.1 Evaluar Hoyo (H) - 367m

**Cálculos:**
- Distancia: 367m
- ¿Alcanzable? No (367m > 250m)
- **Decisión:** ❌ **NO EVALUADO** (no alcanzable)

---

### 4.2 Evaluar SP4 - 12m del hoyo (~355m desde tee)

**Cálculos:**
- Distancia desde tee: ~355m
- ¿Alcanzable? No (355m > 250m)
- **Decisión:** ❌ **NO EVALUADO** (no alcanzable)

---

### 4.3 Evaluar SP3 - 57m del hoyo (~310m desde tee)

**Cálculos:**
- Distancia desde tee: ~310m
- ¿Alcanzable? No (310m > 250m)
- **Decisión:** ❌ **NO EVALUADO** (no alcanzable)

---

### 4.4 Evaluar SP2 - 100m del hoyo (~267m desde tee)

**Cálculos:**
- Distancia desde tee: ~267m
- ¿Alcanzable? No (267m > 250m)
- **Decisión:** ❌ **NO EVALUADO** (no alcanzable)

---

### 4.5 Evaluar SP1 - 170m del hoyo (~197m desde tee)

**Cálculos:**
- Distancia desde tee: ~197m
- ¿Alcanzable? Sí (197m ≤ 250m)
- Obstáculos: Moderados (mitad de calle)
- Palo recomendado: Hierro 5 o Madera 3
- Terreno: tee → Hierro/Madera en tee = riesgo bajo (0.0-1.5 puntos)
- Riesgo calculado estimado: **28 puntos**

**Decisión:** ✅ **ACEPTADO COMO CONSERVADORA**
- **Razón:** Riesgo < 30 (óptimo). Mejor que la óptima actual.
- **Acción:** Intercambiar roles:
  - Nueva óptima: SP1 (riesgo 28)
  - Nueva conservadora: Optimal Shot 1 (riesgo 45)
- **Flag:** `should_search_conservative = False` (ya tenemos óptima con riesgo ≤ 30)

---

## Resultado Final - Recomendación 1

### Recomendación Entregada:

```json
{
  "direct_trajectory": {
    "distance_meters": 197,
    "target": "waypoint",
    "waypoint_description": "Centro calle antes de bunkers a 170m de green",
    "risk_level": {
      "total": 28
    },
    "club_recommendation": {
      "recommended_club": "Hierro 5",
      "swing_type": "completo"
    }
  },
  "conservative_trajectory": {
    "distance_meters": 217,
    "target": "waypoint",
    "waypoint_description": "Salida con drive al centro de la calle para dejar la bola a la derecha del segundo bunker de la izquierda",
    "risk_level": {
      "total": 45
    },
    "club_recommendation": {
      "recommended_club": "Driver",
      "swing_type": "completo"
    }
  },
  "recommended_trajectory": "direct"
}
```

### Mensaje al Jugador:

> "Estás a 367 metros del hoyo. Te recomiendo utilizar el Hierro 5 con swing completo hacia el centro de calle antes de bunkers, con el objetivo de hacer 197 metros. Esta es una opción segura que te dejará en buena posición. También tienes la opción de usar el Driver hacia el centro de la calle, dejando la bola a la derecha del segundo bunker de la izquierda, con un riesgo moderado."

---

## RECOMENDACIÓN 2: Desde Mitad de Calle (después de golpe de 150m)

### Situación Inicial

**Posición del jugador:**
- **Ubicación:** Mitad de calle (fairway)
- **Distancia al hoyo (flag):** ~217 metros (367m - 150m)
- **Terreno:** fairway (calle)
- **Distancia máxima alcanzable:** 220 metros (con driver o madera)

**Nota:** El jugador golpeó 150m desde el tee, quedando aproximadamente en la posición del optimal shot endpoint o cerca.

---

## Paso 1: Filtrado de Puntos

**Criterio:** Solo incluir strategic_points con `distance_to_flag < 217m` (posición actual)

**Nota importante:** El hoyo (flag) NO es un strategic_point, se evalúa siempre primero independientemente del filtrado.

**Resultado del filtrado:**
- ✅ **H (hoyo/flag)**: Se evalúa siempre primero (no está en la lista de strategic_points)
- ✅ **SP1 (170m)**: `170m < 217m` → ✅ **INCLUIDO**
- ✅ **SP2 (100m)**: `100m < 217m` → ✅ **INCLUIDO**
- ✅ **SP3 (57m)**: `57m < 217m` → ✅ **INCLUIDO**
- ✅ **SP4 (12m)**: `12m < 217m` → ✅ **INCLUIDO**

**Lista filtrada:** [SP1, SP2, SP3, SP4]

**Distancias desde la nueva posición (mitad de calle):**
- Hoyo (flag): **217m** (se evalúa siempre primero)
- SP1 (170m del hoyo): ~**47m** desde posición actual (217m - 170m)
- SP2 (100m del hoyo): ~**117m** desde posición actual (217m - 100m)
- SP3 (57m del hoyo): ~**160m** desde posición actual (217m - 57m)
- SP4 (12m del hoyo): ~**205m** desde posición actual (217m - 12m)

---

## Paso 2: Ordenamiento

**Criterio:** Ordenar por `distance_to_flag` ASC (más cercano al hoyo primero)

**Orden final:** [SP4 (12m), SP3 (57m), SP2 (100m), SP1 (170m)]

**Orden de evaluación completo:**
1. **H (hoyo)** - siempre primero
2. **SP4 (12m)** - más cercano al hoyo
3. **SP3 (57m)**
4. **SP2 (100m)**
5. **SP1 (170m)** - más lejano al hoyo

---

## Paso 3: Verificación de Optimal Shot

**Criterio:** Si hay optimal_shot a <10m del inicio, evaluarlo primero

**Resultado:**
- Optimal shot 2 inicia en (-3.87094755026384, 40.44445006655005)
- Si el jugador está cerca de esta posición (<10m) → ✅ **SE EVALÚA PRIMERO**

**Evaluación del Optimal Shot 2:**
- Distancia desde posición actual al endpoint: ~100 metros (aproximado)
- Descripción: "Segundo golpe para dejar la bola en green. Procurad botar la bola en antegreen y dejar rodar"
- Obstáculos: Bunkers cerca del green
- Palo recomendado: Hierro 7 o 8
- Terreno: fairway → Hierro en fairway = riesgo bajo (2.0 puntos)
- Riesgo calculado estimado: **32 puntos**

**Decisión:** ✅ **ACEPTADO COMO ÓPTIMA**
- **Razón:** Riesgo entre 30-75 (aceptable). Es la trayectoria recomendada del diseño del hoyo.
- **Acción:** Guardar como `direct_trajectory`
- **Flag:** `should_search_conservative = True` (buscar conservadora porque riesgo > 30)

---

## Paso 4: Evaluación Paso a Paso

### 4.1 Evaluar Hoyo (H) - 217m desde posición actual

**Cálculos:**
- Distancia desde posición actual: **217m** (calculada dinámicamente desde las coordenadas GPS)
- ¿Alcanzable? Sí (217m ≤ 220m, justo en el límite)
- Obstáculos: Bunkers, rough, árboles cerca del green
- Palo recomendado: Driver o Madera 3
- Terreno: fairway → Driver/Madera en fairway = riesgo alto (60-70 puntos)
- Riesgo calculado estimado: **82 puntos**

**Decisión:** ❌ **DESCARTADO**
- **Razón:** Riesgo ≥ 75 (muy alto). Trayectoria directa al green es demasiado arriesgada desde esta distancia.

---

### 4.2 Evaluar SP4 - 12m del hoyo (205m desde posición actual)

**Cálculos:**
- Distancia desde posición actual: **205m** (calculada dinámicamente: 217m - 12m = 205m)
- ¿Alcanzable? Sí (205m ≤ 220m)
- Obstáculos: Pocos (cerca del green, zona segura)
- Palo recomendado: Madera 3 o Hierro 4
- Terreno: fairway → Madera/Hierro en fairway = riesgo moderado (2.0-5.0 puntos)
- Riesgo calculado estimado: **38 puntos**

**Decisión:** ⏸️ **NO SE ACEPTA COMO ÓPTIMA** (ya tenemos optimal shot con riesgo 32)
- **Razón:** El optimal shot tiene mejor riesgo (32 < 38). Se mantiene como óptima.

---

### 4.3 Evaluar SP3 - 57m del hoyo (160m desde posición actual)

**Cálculos:**
- Distancia desde posición actual: **160m** (calculada dinámicamente: 217m - 57m = 160m)
- ¿Alcanzable? Sí (160m ≤ 220m)
- Obstáculos: Moderados (mitad de calle)
- Palo recomendado: Hierro 6
- Terreno: fairway → Hierro en fairway = riesgo bajo (2.0 puntos)
- Riesgo calculado estimado: **22 puntos**

**Decisión:** ✅ **ACEPTADO COMO CONSERVADORA**
- **Razón:** Riesgo < 30 (óptimo). Mejor que la óptima actual.
- **Acción:** Intercambiar roles:
  - Nueva óptima: SP3 (riesgo 22)
  - Nueva conservadora: Optimal Shot 2 (riesgo 32)
- **Flag:** `should_search_conservative = False` (ya tenemos óptima con riesgo ≤ 30)

---

### 4.4 Evaluar SP2 - 100m del hoyo (117m desde posición actual)

**Cálculos:**
- Distancia desde posición actual: **117m** (calculada dinámicamente: 217m - 100m = 117m)
- ¿Alcanzable? Sí (117m ≤ 220m)

**Decisión:** ⏸️ **NO SE EVALÚA** (algoritmo se detiene)
- **Razón:** Ya tenemos una opción óptima (riesgo ≤ 30). El algoritmo no continúa evaluando.

---

### 4.5 Evaluar SP1 - 170m del hoyo (47m desde posición actual)

**Cálculos:**
- Distancia desde posición actual: **47m** (calculada dinámicamente: 217m - 170m = 47m)
- ¿Alcanzable? Sí (47m ≤ 220m)

**Decisión:** ⏸️ **NO SE EVALÚA** (algoritmo se detiene)
- **Razón:** Ya tenemos una opción óptima (riesgo ≤ 30). El algoritmo no continúa evaluando.

---

## Resultado Final - Recomendación 2

### Recomendación Entregada:

```json
{
  "direct_trajectory": {
    "distance_meters": 160,
    "target": "waypoint",
    "waypoint_description": "Centro calle para approach corto a 57m de green",
    "risk_level": {
      "total": 22
    },
    "club_recommendation": {
      "recommended_club": "Hierro 6",
      "swing_type": "completo"
    }
  },
  "conservative_trajectory": {
    "distance_meters": 100,
    "target": "waypoint",
    "waypoint_description": "Segundo golpe para dejar la bola en green. Procurad botar la bola en antegreen y dejar rodar",
    "risk_level": {
      "total": 32
    },
    "club_recommendation": {
      "recommended_club": "Hierro 7",
      "swing_type": "completo"
    }
  },
  "recommended_trajectory": "direct"
}
```

### Mensaje al Jugador:

> "Estás a 217 metros del hoyo. Te recomiendo utilizar el Hierro 6 con swing completo hacia el centro de calle para approach corto, con el objetivo de hacer 160 metros. Esta es una opción segura que te dejará a 57 metros del green. También tienes la opción de usar el Hierro 7 hacia el antegreen, procurando botar la bola y dejar rodar, con un riesgo moderado."

---

## Resumen Comparativo

| Aspecto | Recomendación 1 (Tee) | Recomendación 2 (Mitad Calle) |
|---------|----------------------|-------------------------------|
| **Distancia al hoyo** | 367m | 217m |
| **Óptima** | SP1 (170m del hoyo) - 197m desde tee | SP3 (57m del hoyo) - 160m desde posición |
| **Riesgo óptima** | 28 puntos | 22 puntos |
| **Conservadora** | Optimal Shot 1 (217m) | Optimal Shot 2 (100m) |
| **Riesgo conservadora** | 45 puntos | 32 puntos |
| **Palo óptima** | Hierro 5 | Hierro 6 |
| **Estrategia** | Posicionamiento seguro en mitad de calle | Approach corto para dejar cerca del green |

---

## Observaciones

1. **Primera recomendación:** El sistema prioriza seguridad, recomendando un golpe intermedio (SP1) en lugar del optimal shot más arriesgado.

2. **Segunda recomendación:** Al estar más cerca del green, el sistema recomienda un approach corto (SP3) que deja la bola muy cerca del green para el siguiente golpe.

3. **Filtrado funciona correctamente:** En la segunda recomendación, todos los strategic_points están disponibles porque todos están más cerca del hoyo que la posición actual (217m). Las distancias desde la nueva posición se recalculan dinámicamente.

4. **El hoyo siempre se evalúa:** El hoyo (flag) se evalúa siempre primero, independientemente del filtrado, porque no es un strategic_point. En la segunda recomendación, el hoyo está a 217m y es alcanzable, pero tiene riesgo muy alto (82 puntos) por lo que se descarta.

4. **Orden de evaluación:** Siempre se evalúa primero el hoyo, luego los strategic points desde más cercano a más lejano al hoyo.
