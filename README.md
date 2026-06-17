# Vertech TdF — Backend API

Backend Python/FastAPI que conecta Copernicus/Sentinel con Claude Vision.

## Deploy en Render.com

1. Crear nuevo repositorio GitHub: `vertech-backend`
2. Subir estos archivos
3. Entrar a [render.com](https://render.com) → New → Web Service
4. Conectar el repositorio
5. Configurar variables de entorno:

| Variable | Valor |
|----------|-------|
| `COPERNICUS_USER` | Tu email de Copernicus |
| `COPERNICUS_PASSWORD` | Tu contraseña de Copernicus |
| `ANTHROPIC_API_KEY` | Tu API key de Anthropic |

6. Deploy → obtenés una URL tipo `https://vertech-tdf-api.onrender.com`

## Endpoints

### POST /analizar
Descarga imagen satelital real y la analiza con IA.

```json
{
  "lat": -54.8,
  "lon": -68.3,
  "tipo": "campo",
  "fecha": "2025-06-01",
  "zoom": 0.5
}
```

Tipos disponibles: `campo` | `mar` | `metano`

### GET /health
Health check del servicio.

## Flujo interno

1. Autentica con Copernicus Data Space
2. Busca la imagen más reciente disponible para la zona
3. Descarga el preview de la imagen
4. Envía la imagen a Claude Vision con el prompt correspondiente
5. Devuelve índices, diagnóstico y misiones en JSON
