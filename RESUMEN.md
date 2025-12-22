## Resumen de la Lógica

### Caso 1: Distancia a optimal_shot

1. **Calcular distancia al punto inicial del optimal_shot (dist_start_os)**
   - Si dist_start_os ≤ 10:
     - Calcular riesgo de trayectoria desde la posicion de la bola al punto final del optimal_shot
     - Si riesgo > 75:
	- Descartar esta trayectoria y pasar al Caso 2
     - Si 30 < riesgo ≤ 75:
	- Ofrecer como óptima y pasar al Caso 2
     - Si riesgo ≤ 30: → Ofrecer como óptima + NO buscar conservadora

### Caso 2: Distancia al green ES alcanzable

1. **Calcular riesgo directo al green (flag)**
   - Si riesgo ≤ 75:
     - Si 30 < riesgo ≤ 75 y no existe ya una trayectoria optima: → Ofrecer como óptima + Buscar conservadora
     - Si 30 < riesgo ≤ 75 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima
     - Si riesgo ≤ 30 y no existe ya una trayectoria optima: → Ofrecer como óptima + NO buscar conservadora
     - Si riesgo ≤ 30 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima
   - Si riesgo > 75:
     - Buscar strategic_point más cercano al green
     - Iterar hasta encontrar uno con riesgo < 75
     - Si encuentra uno con 30 < riesgo ≤ 75: → Ofrecer como óptima + Buscar conservadora
     - Si encuentra uno con riesgo ≤ 30: → Ofrecer como óptima + NO buscar conservadora

### Caso 3: Distancia al green NO es alcanzable

1. **Buscar strategic_point más cercano al green**
   - Calcular riesgo de trayectoria al strategic_point
   - Si riesgo > 75:
     - Iterar sobre siguientes strategic_points hasta encontrar uno con riesgo < 75
     - Si 30 < riesgo ≤ 75 y no existe ya una trayectoria optima: → Ofrecer como óptima + Buscar conservadora
     - Si 30 < riesgo ≤ 75 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima
     - Si encuentra uno con riesgo ≤ 30 y no existe ya una trayectoria optima: → Ofrecer como óptima + NO buscar conservadora
     - Si encuentra uno con riesgo ≤ 30 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima
   - Si riesgo ≤ 75:
     - Si 30 < riesgo ≤ 75 y no existe ya una trayectoria optima: → Ofrecer como óptima + Buscar conservadora
     - Si 30 < riesgo ≤ 75 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima
     - Si riesgo ≤ 30 y no existe ya una trayectoria optima: → Ofrecer como óptima + NO buscar conservadora
     - Si riesgo ≤ 30 y si existe ya una trayectoria optima: → Pasar la optima existente a conservadora + Ofrecer como óptima