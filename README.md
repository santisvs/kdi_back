# Servicio Hola Mundo

Servicio básico en Python con Flask que expone un endpoint GET.

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución

Ejecutar el servicio:
```bash
python app.py
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

## Pruebas

Puedes probar el endpoint con curl:
```bash
curl http://localhost:5000/hola-mundo
```

