# Resumen de la Lógica de Negocio y Juego - KDI Backend

## Visión General

El backend de KDI es un servicio Flask en Python que proporciona un sistema completo de asistencia para jugar al golf, integrando análisis geoespacial (PostGIS), inteligencia artificial (AWS Bedrock) y gestión de partidos y jugadores.

---

## Arquitectura del Sistema

### Estructura por Capas (Arquitectura Hexagonal)

1. **Capa API** (`api/`): Endpoints REST, validación, serialización
2. **Capa de Dominio** (`domain/`): Lógica de negocio pura, sin dependencias técnicas
3. **Capa de Infraestructura** (`infrastructure/`): Implementaciones técnicas (DB, AWS, PostGIS)
4. **Agentes IA** (`infrastructure/agents/`): Orquestación de agentes de Bedrock

---

## Componentes Principales del Juego

### 1. Sistema de Campos de Golf

**Conceptos:**
- **Course (Campo)**: Un campo de golf completo con múltiples hoyos
- **Hole (Hoyo)**: Cada uno de los 18 hoyos de un campo
- **Obstacles (Obstáculos)**: Elementos del campo (agua, bunkers, árboles, rough, out of bounds)
- **Strategic Points (Puntos Estratégicos)**: Puntos intermedios recomendados para jugar
- **Optimal Shots (Golpes Óptimos)**: Trayectorias predefinidas ideales para un hoyo

**Funcionalidades:**
- Identificación automática de hoyos por GPS usando PostGIS
- Cálculo de distancias precisas (metros y yardas)
- Detección de tipo de terreno (fairway, green, bunker, rough, agua, etc.)
- Análisis de obstáculos en trayectorias
- Búsqueda de puntos estratégicos y golpes óptimos

---

### 2. Sistema de Recomendaciones de Golpes

#### Algoritmo de Evaluación de Trayectorias

El sistema implementa un algoritmo complejo que evalúa múltiples trayectorias posibles y calcula un **score de riesgo numérico (0-100)** para cada una.

**Componentes del Score de Riesgo:**

1. **Riesgo de Obstáculos:**
   - Riesgo base por tipo de obstáculo:
     - Agua: 50 puntos
     - Out of bounds: 45 puntos
     - Árboles: 25 puntos
     - Rough pesado: 20 puntos
     - Bunker: 15 puntos
   - Penalización por cantidad de obstáculos
   - Penalización por precisión del jugador (error promedio)
   - Penalización por densidad de obstáculos

2. **Riesgo Terreno-Palo:**
   - Penalización según combinación terreno/palo:
     - Driver en fairway: 70 puntos
     - Madera en rough: 70 puntos
     - Driver en bunker: 100 puntos (prácticamente prohibido)
     - Wedge en cualquier terreno: 0-3 puntos

3. **Riesgo Distancia-Objetivo:**
   - Penalización que aumenta con la distancia
   - Diferente para waypoints (objetivos intermedios) vs bandera
   - Waypoints: penalización menor (0-6 puntos)
   - Bandera: penalización mayor (0-20 puntos según distancia)

**Lógica de Decisión de Trayectorias:**

El algoritmo sigue esta secuencia:

**CASO 1: Verificar Optimal Shots**
- Si la bola está a ≤10m del inicio de un optimal_shot:
  - Calcular riesgo de trayectoria al endpoint del optimal_shot
  - Si riesgo > 75: Descartar y continuar
  - Si 30 < riesgo ≤ 75: Ofrecer como óptima + buscar conservadora
  - Si riesgo ≤ 30: Ofrecer como óptima + NO buscar conservadora (final)

**CASO 2: Distancia al Green Alcanzable**
- Si la distancia al green es alcanzable con el palo más largo:
  - Calcular riesgo directo al green
  - Si riesgo ≤ 75:
    - Si 30 < riesgo ≤ 75: Ofrecer como óptima + buscar conservadora
    - Si riesgo ≤ 30: Ofrecer como óptima + NO buscar conservadora
  - Si riesgo > 75: Buscar strategic_point más cercano al green con riesgo < 75

**CASO 3: Distancia al Green NO Alcanzable**
- Buscar strategic_point más cercano al green
- Iterar hasta encontrar uno con riesgo ≤ 75
- Aplicar misma lógica de clasificación según riesgo

**Trayectoria Conservadora:**
- Solo se busca si la óptima tiene riesgo entre 30-75
- Busca cualquier strategic_point con riesgo < 30
- Si encuentra uno mejor: intercambia roles (nuevo = óptima, anterior = conservadora)

**Sin Trayectorias Válidas:**
- Si ninguna trayectoria tiene riesgo ≤ 75:
  - Mensaje: "Juega un hierro rodado y busca la calle"

#### Recomendación de Palos

El sistema calcula el palo recomendado basándose en:

1. **Distancia Objetivo**: Distancia al objetivo (bandera o waypoint)
2. **Estadísticas del Jugador** (si disponibles):
   - Distancia promedio por palo
   - Error promedio
   - Distancia máxima
3. **Distancias Estándar** (si no hay perfil):
   - Driver: 230m
   - Hierro 7: 130m
   - Pitching Wedge: 100m
   - etc.

**Criterio de Selección:**
- Elige el palo cuya distancia promedio esté **más cerca** de la distancia objetivo
- Calcula tipo de swing (completo, 3/4, 1/2) según relación distancia objetivo/distancia palo

#### Agente IA de Recomendaciones

El sistema usa AWS Bedrock (Amazon Nova Lite) con un agente especializado que:

1. Analiza toda la información del campo (distancia, obstáculos, terreno, trayectorias)
2. Consulta una Knowledge Base de golf para técnicas específicas
3. Genera recomendaciones en lenguaje natural incluyendo:
   - Palo recomendado
   - Tipo de golpe (flop shot, pitch, chip, punch, etc.)
   - Tipo de swing (completo, 3/4, 1/2)
   - Estrategia específica
   - Consideraciones (viento, obstáculos, etc.)

---

### 3. Sistema de Partidos (Matches)

**Conceptos:**
- **Match (Partido)**: Una sesión de juego en un campo con uno o más jugadores
- **Match Player**: Relación entre partido y jugador
- **Hole Score**: Puntuación de un jugador en un hoyo específico
- **Stroke**: Golpe individual registrado con posición GPS

**Estados del Partido:**
- `in_progress`: Partido en curso
- `completed`: Partido finalizado
- `cancelled`: Partido cancelado

**Funcionalidades:**

1. **Creación de Partidos:**
   - Crear partido asociado a un campo
   - Añadir múltiples jugadores
   - Permitir que jugadores empiecen en hoyos diferentes

2. **Registro de Golpes:**
   - Incrementar golpes por hoyo
   - Registrar golpes individuales con:
     - Posición GPS inicial
     - Palo utilizado
     - Trayectoria escogida (conservadora, riesgo, óptima)
     - Palo propuesto por el sistema
     - Distancia propuesta

3. **Evaluación de Golpes:**
   - Evalúa automáticamente cada golpe cuando se registra la nueva posición
   - Calcula:
     - Calidad del golpe (0-100)
     - Error de distancia
     - Error de dirección
   - **Reglas especiales para green:**
     - 1 golpe en green: calidad 80 (bueno)
     - 2 golpes: calidad 60 (correcto)
     - 3 golpes: calidad 40 (malo)
     - 4+ golpes: calidad 20 - (strokes - 4) * 5 (muy malo)

4. **Leaderboard:**
   - Ranking automático por total de golpes
   - Actualización en tiempo real
   - Ganador: jugador con menos golpes

5. **Finalización:**
   - Marca partido como completado
   - Determina ganador automáticamente
   - Retorna estadísticas finales

---

### 4. Sistema de Jugadores

**Perfil de Jugador:**
- Información personal (nombre, email, teléfono, fecha nacimiento)
- Handicap (0-54)
- Género, mano preferida
- Años jugando, nivel de habilidad (beginner, intermediate, advanced, professional)

**Estadísticas por Palo:**
- Distancia promedio
- Distancia máxima
- Error promedio
- Tipo de palo (driver, wood, hybrid, iron, wedge)

**Inicialización Automática:**
- Al crear perfil con género y nivel, se inicializan estadísticas por palo con distancias por defecto según género y nivel

---

### 5. Sistema de Autenticación

**Métodos:**
- Registro/Login tradicional (email + contraseña)
- OAuth Google
- OAuth Instagram
- Recuperación de contraseña

**Tokens JWT:**
- Autenticación mediante tokens JWT
- Endpoints protegidos requieren token en header `Authorization: Bearer <token>`

---

## Flujo de Juego Típico

### 1. Preparación
- Usuario se autentica
- Crea o se une a un partido
- Selecciona campo de golf

### 2. Durante el Juego

**Para cada golpe:**

1. **Jugador está en posición GPS (lat, lon)**
   - Sistema identifica automáticamente el hoyo
   - Calcula distancia a la bandera
   - Detecta tipo de terreno
   - Identifica obstáculos

2. **Solicita Recomendación** (`POST /golf/next-shot`)
   - Sistema evalúa trayectorias (óptima, conservadora, riesgo)
   - Calcula scores de riesgo
   - Recomienda palo y estrategia
   - Agente IA genera recomendación en lenguaje natural

3. **Jugador Ejecuta Golpe**
   - Registra golpe con posición inicial (`POST /match/<id>/increment-strokes`)
   - Proporciona:
     - Palo utilizado
     - Trayectoria escogida
     - Palo propuesto por sistema

4. **Nueva Posición GPS**
   - Sistema evalúa automáticamente el golpe anterior
   - Calcula calidad, errores de distancia y dirección
   - Actualiza estadísticas del jugador

5. **Completa Hoyo**
   - Marca hoyo como completado
   - Retorna estadísticas del hoyo
   - Actualiza leaderboard

### 3. Finalización
- Cuando todos los jugadores completan todos los hoyos
- Marca partido como completado
- Determina ganador
- Retorna estadísticas finales

---

## Características Técnicas Destacadas

### Análisis Geoespacial (PostGIS)
- Identificación de hoyos por proximidad GPS
- Cálculo de distancias precisas (Haversine)
- Detección de intersecciones con obstáculos (líneas y polígonos)
- Verificación de posición en áreas (green, bunker, etc.)

### Inteligencia Artificial
- **Agente de Golf**: Recomendaciones contextualizadas
- **Agente de Clima**: Consultas meteorológicas
- **Knowledge Base**: Base de conocimiento sobre técnicas y estrategias de golf
- **Modelo**: Amazon Nova Lite (Bedrock)

### Personalización
- Recomendaciones basadas en estadísticas del jugador
- Distancias personalizadas por palo
- Consideración de precisión y error del jugador
- Adaptación según nivel de habilidad

---

## Endpoints Principales

### Golf
- `POST /golf/next-shot`: Recomendación completa del siguiente golpe
- `POST /golf/trajectory-options`: Opciones de trayectorias con análisis de riesgo
- `POST /golf/identify-hole`: Identificar hoyo por GPS
- `POST /golf/distance-to-hole`: Calcular distancia a bandera
- `POST /golf/obstacles-between`: Encontrar obstáculos en trayectoria
- `POST /golf/terrain-type`: Detectar tipo de terreno

### Partidos
- `POST /match`: Crear partido
- `POST /match/<id>/increment-strokes`: Registrar golpe
- `POST /match/<id>/complete-hole`: Completar hoyo
- `GET /match/<id>/leaderboard`: Ver ranking
- `POST /match/<id>/complete`: Finalizar partido

### Jugadores
- `POST /player`: Crear perfil de jugador
- `GET /player/profile`: Obtener perfil
- `GET /player/club-statistics`: Estadísticas por palo

### Autenticación
- `POST /auth/register`: Registro
- `POST /auth/login`: Login
- `POST /auth/oauth/google`: OAuth Google
- `POST /auth/oauth/instagram`: OAuth Instagram

---

## Consideraciones de Diseño

### Arquitectura Limpia
- Separación clara entre lógica de negocio y implementación técnica
- Servicios de dominio independientes de bases de datos
- Fácil testeo y mantenimiento

### Escalabilidad
- Uso de PostGIS para consultas geoespaciales eficientes
- Agentes IA asíncronos
- Base de datos relacional normalizada

### Extensibilidad
- Sistema de puntos estratégicos y golpes óptimos configurables
- Knowledge Base extensible
- Estadísticas de jugador personalizables

---

## Resumen Ejecutivo

El sistema KDI Backend es una plataforma completa de asistencia para golf que combina:

1. **Análisis Geoespacial Avanzado**: Identificación automática de posición, cálculo de distancias, detección de obstáculos
2. **Algoritmo de Trayectorias Inteligente**: Evaluación de múltiples opciones con scores de riesgo numéricos
3. **Recomendaciones Personalizadas**: Basadas en estadísticas del jugador y análisis del campo
4. **Inteligencia Artificial**: Agentes especializados que generan recomendaciones en lenguaje natural
5. **Gestión Completa de Partidos**: Registro de golpes, evaluación automática, leaderboards en tiempo real
6. **Sistema de Jugadores**: Perfiles, estadísticas, personalización

Todo esto integrado en una arquitectura limpia y escalable que permite a los jugadores recibir asistencia inteligente durante sus partidas de golf.

