from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import json
import re

app = FastAPI(title="Vertech TdF API", version="3.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class ImageRequest(BaseModel):
    imagen_base64: str
    media_type: str = "image/jpeg"
    tipo: str = "campo"
    lugar: str = ""
    fuente: str = "imagen satelital"

PROMPTS = {

"campo": """Sos un experto en teledetección agrícola, análisis de vegetación y monitoreo de cultivos satelital.
Analizá esta imagen satelital{lugar_str} — puede provenir de SAOCOM (SAR banda L), constelación SIASGE o Sentinel-2 — con máximo detalle agronómico y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
{{
  "zona": "nombre del área o región detectada visualmente{lugar_default}",
  "metricas": [
    {{"label": "NDVI promedio", "value": "0.XX", "sub": "salud vegetal general", "color": "green"}},
    {{"label": "Cobertura vegetal", "value": "XX%", "sub": "% superficie con vegetación", "color": "green"}},
    {{"label": "Estrés hídrico", "value": "Alto/Medio/Bajo", "sub": "déficit de agua estimado", "color": "amber"}},
    {{"label": "Sequía detectada", "value": "Sí/No/Parcial", "sub": "indicador de aridez", "color": "red"}},
    {{"label": "Superficie cultivo", "value": "~X.XXX ha", "sub": "área cultivada estimada", "color": "blue"}},
    {{"label": "Estado general", "value": "Óptimo/Regular/Crítico", "sub": "clasificación IA", "color": "green"}}
  ],
  "zonas_ndvi": [
    {{"zona": "Zona con mayor NDVI", "ndvi": "0.XX", "estado": "Óptimo", "pct": 80}},
    {{"zona": "Zona con NDVI medio", "ndvi": "0.XX", "estado": "Moderado", "pct": 55}},
    {{"zona": "Zona con menor NDVI", "ndvi": "0.XX", "estado": "Estrés", "pct": 30}},
    {{"zona": "Área sin vegetación", "ndvi": "0.XX", "estado": "Sin cobertura", "pct": 10}}
  ],
  "alertas": [
    {{"tipo": "warn", "titulo": "Alerta de sequía o estrés hídrico", "desc": "descripción concreta"}},
    {{"tipo": "critical", "titulo": "Zona degradada o crítica", "desc": "descripción concreta"}},
    {{"tipo": "ok", "titulo": "Recomendación de intervención", "desc": "acción sugerida"}}
  ],
  "diagnostico": "4-5 oraciones técnicas sobre estado del campo, sequía, estrés hídrico, dimensión de cultivos y zonas críticas.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "zona detectada", "tarea": "acción urgente"}},
    {{"prioridad": "MEDIA", "zona": "zona detectada", "tarea": "seguimiento"}},
    {{"prioridad": "BAJA", "zona": "zona detectada", "tarea": "monitoreo preventivo"}}
  ]
}}""",

"mar": """Sos un experto en oceanografía, vigilancia marítima y economía azul con experiencia en detección de pesca ilegal.
Analizá esta imagen satelital marina{lugar_str} — puede provenir de SAOCOM 1A/1B (SAR banda L, CONAE), SABIA-Mar (CONAE) o equivalente — y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
{{
  "zona": "nombre del cuerpo de agua o región marina detectada{lugar_default}",
  "metricas": [
    {{"label": "Embarcaciones totales", "value": "X", "sub": "detectadas vía SAOCOM SAR", "color": "blue"}},
    {{"label": "Pesca ilegal sospechosa", "value": "X embarcaciones", "sub": "sin AIS o en zona restringida", "color": "red"}},
    {{"label": "Estado de mareas", "value": "Alta/Baja/Media", "sub": "estimación por patrón costero", "color": "blue"}},
    {{"label": "Temperatura sup. mar", "value": "X.X°C", "sub": "SST vía SABIA-Mar", "color": "blue"}},
    {{"label": "Productividad marina", "value": "Alta/Media/Baja", "sub": "clorofila-a vía SABIA-Mar", "color": "green"}},
    {{"label": "Nivel de alerta", "value": "Verde/Amarillo/Rojo", "sub": "estado de vigilancia ZEE", "color": "amber"}}
  ],
  "zonas_ndvi": [
    {{"zona": "Zona de mayor actividad pesquera", "ndvi": "X embarcaciones", "estado": "Activa", "pct": 85}},
    {{"zona": "Área de mareas altas", "ndvi": "Nivel X m", "estado": "Alta", "pct": 65}},
    {{"zona": "Zona de productividad biológica", "ndvi": "Alta", "estado": "Productiva", "pct": 50}},
    {{"zona": "Área costera / Puerto", "ndvi": "X embarcaciones", "estado": "Activo", "pct": 30}}
  ],
  "alertas": [
    {{"tipo": "critical", "titulo": "Pesca ilegal detectada", "desc": "descripción de embarcación o zona sospechosa"}},
    {{"tipo": "warn", "titulo": "Condición de marea o corriente", "desc": "descripción del estado detectado"}},
    {{"tipo": "ok", "titulo": "Estado general de la flota", "desc": "descripción de actividad observada"}}
  ],
  "diagnostico": "4-5 oraciones técnicas sobre embarcaciones detectadas, actividad ilegal, mareas, condiciones oceanográficas y nivel de alerta para la ZEE argentina.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "zona sospechosa", "tarea": "intercepción coordinada con Prefectura Naval"}},
    {{"prioridad": "MEDIA", "zona": "área de monitoreo", "tarea": "patrullaje con próxima pasada SAOCOM"}},
    {{"prioridad": "BAJA", "zona": "zona costera", "tarea": "monitoreo preventivo de accesos portuarios"}}
  ]
}}""",

"metano": """Sos un experto en monitoreo atmosférico de gases de efecto invernadero especializado en detección de fugas de metano CH4.
Analizá esta imagen de columna atmosférica{lugar_str} — puede provenir de TROPOMI/Sentinel-5P — y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
{{
  "zona": "nombre del área o región con emisiones detectadas{lugar_default}",
  "metricas": [
    {{"label": "CH4 promedio", "value": "X.XXX ppb", "sub": "concentración columna total", "color": "red"}},
    {{"label": "Pico de emisión", "value": "X.XXX ppb", "sub": "valor máximo detectado", "color": "red"}},
    {{"label": "Fugas detectadas", "value": "X focos", "sub": "puntos de emisión identificados", "color": "red"}},
    {{"label": "Anomalía sobre base", "value": "+X ppb", "sub": "desviación sobre línea base 1900 ppb", "color": "amber"}},
    {{"label": "Área afectada", "value": "~X.XXX km2", "sub": "superficie con emisiones elevadas", "color": "amber"}},
    {{"label": "Nivel de alerta", "value": "CRÍTICO/ALTO/MEDIO/BAJO", "sub": "clasificación de riesgo IA", "color": "red"}}
  ],
  "zonas_ndvi": [
    {{"zona": "Foco principal de fuga", "ndvi": "X.XXX ppb", "estado": "FUGA ACTIVA", "pct": 95}},
    {{"zona": "Pluma de dispersión", "ndvi": "X.XXX ppb", "estado": "Elevado", "pct": 70}},
    {{"zona": "Área secundaria", "ndvi": "X.XXX ppb", "estado": "Moderado", "pct": 45}},
    {{"zona": "Zona de línea base", "ndvi": "1.900 ppb", "estado": "Normal", "pct": 15}}
  ],
  "alertas": [
    {{"tipo": "critical", "titulo": "FUGA DE METANO ACTIVA", "desc": "ubicación y fuente probable de la fuga"}},
    {{"tipo": "warn", "titulo": "Pluma de dispersión", "desc": "dirección y extensión de la pluma"}},
    {{"tipo": "warn", "titulo": "Fuentes probables", "desc": "industria energética, ganadería o humedales"}}
  ],
  "diagnostico": "4-5 oraciones sobre concentración CH4, focos de fuga, fuentes probables, pluma de dispersión y nivel de riesgo ambiental.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "foco de fuga", "tarea": "inspección urgente y aislamiento del área"}},
    {{"prioridad": "ALTA", "zona": "pluma de dispersión", "tarea": "alerta a autoridades ambientales"}},
    {{"prioridad": "MEDIA", "zona": "área secundaria", "tarea": "muestreo atmosférico y validación"}}
  ]
}}"""
}

def limpiar_json(texto: str) -> str:
    """Limpia el texto para obtener JSON válido."""
    # Quitar backticks
    texto = texto.replace("```json", "").replace("```", "").strip()
    # Extraer solo el bloque JSON
    inicio = texto.find("{")
    fin = texto.rfind("}") + 1
    if inicio >= 0 and fin > inicio:
        texto = texto[inicio:fin]
    # Quitar trailing commas antes de } o ]
    texto = re.sub(r',\s*([}\]])', r'\1', texto)
    return texto

def get_headers():
    return {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

@app.post("/analizar-imagen")
async def analizar_imagen(req: ImageRequest):
    media_type = req.media_type
    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"

    lugar_str     = f" de {req.lugar}" if req.lugar else ""
    lugar_default = f", o '{req.lugar}' si no se puede determinar visualmente" if req.lugar else ", o 'Zona no especificada' si no se puede determinar"

    template     = PROMPTS.get(req.tipo, PROMPTS["campo"])
    prompt_texto = template.format(lugar_str=lugar_str, lugar_default=lugar_default)

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1800,
                "system": "Sos el sistema de análisis satelital Vertech TdF, desarrollado en Tierra del Fuego, Argentina. Analizás imágenes de la constelación CONAE (SAOCOM 1A/1B, SABIA-Mar, SIASGE) y datos complementarios de ESA/Copernicus. Tu especialidad es la ZEE argentina, el Mar Argentino, la Patagonia y ecosistemas subantárticos. Respondés SIEMPRE en JSON puro válido, sin backticks, sin texto adicional y SIN comas finales en arrays u objetos.",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": req.imagen_base64}},
                        {"type": "text", "text": prompt_texto}
                    ]
                }]
            },
            headers=get_headers()
        )

    if r.status_code != 200:
        raise HTTPException(502, f"Error Claude: {r.text}")

    texto = r.json()["content"][0]["text"]
    try:
        limpio = limpiar_json(texto)
        return json.loads(limpio)
    except Exception as e:
        raise HTTPException(502, f"Error JSON: {str(e)} | Texto: {texto[:300]}")

@app.get("/")
def root():
    return {"status": "ok", "app": "Vertech TdF API", "version": "3.3.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "api_key_configured": ANTHROPIC_API_KEY.startswith("sk-ant-")}
