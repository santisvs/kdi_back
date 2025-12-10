# Servicio Hola Mundo
Activar el entorno Python3
.venv\Scripts\activate
Desactivar el entorno 
deactivate

Servicio básico en Python 3 con Flask que expone endpoints para consultas del clima usando AWS Bedrock.

## Requisitos

- Python 3.8 o superior
- Credenciales de AWS configuradas en un archivo `.env`

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-east-1
```

## Ejecución

Ejecutar el servicio:
```bash
python app.py
```

O con Python 3 explícitamente:
```bash
python3 app.py
```

El servicio estará disponible en: `http://localhost:5000`

## Endpoints

### GET /hola-mundo
Responde con "adios mundo"

**Ejemplo de respuesta:**
```json
{
  "mensaje": "adios mundo"
}
```

### GET /health
Endpoint de salud para verificar que el servicio está corriendo

**Ejemplo de respuesta:**
```json
{
  "status": "ok"
}
```

### POST /weather
Endpoint para consultar información del clima usando el agente de Bedrock

**Ejemplo de petición:**
```bash
curl -X POST http://localhost:5000/weather \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué tiempo hace en Madrid?"}'
```

**Ejemplo de respuesta:**
```json
{
  "query": "¿Qué tiempo hace en Madrid?",
  "response": "La respuesta del agente de clima..."
}
```

### GET /weather
Endpoint para consultar información del clima usando parámetros de URL

**Ejemplo de petición:**
```bash
curl "http://localhost:5000/weather?query=¿Qué tiempo hace en Madrid?"
```

## Pruebas

Puedes probar los endpoints con curl:
```bash
# Endpoint básico
curl http://localhost:5000/hola-mundo

# Health check
curl http://localhost:5000/health

# Consulta del clima (POST)
curl -X POST http://localhost:5000/weather \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué tiempo hace en Madrid?"}'

# Consulta del clima (GET)
curl "http://localhost:5000/weather?query=¿Qué tiempo hace en Madrid?"
```

