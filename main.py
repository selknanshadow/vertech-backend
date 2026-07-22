from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import json

app = FastAPI(title="Vertech TdF API", version="3.2.0")

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
Analizá esta imagen satelital{lugar_str} — puede provenir de SAOCOM (SAR banda L), constelación SIASGE o Sentinel-2 — con máximo detalle agronómico y respondé ÚNICAMENTE con JSON puro sin backticks:
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
    {{"zona": "Zona con mayor NDVI", "ndvi": "0.XX", "estado": "Óptimo/Saludable/Estrés/Crítico", "pct": 80}},
    {{"zona": "Zona con NDVI medio", "ndvi": "0.XX", "estado": "Óptimo/Saludable/Estrés/Crítico", "pct": 55}},
    {{"zona": "Zona con menor NDVI", "ndvi": "0.XX", "estado": "Óptimo/Saludable/Estrés/Crítico", "pct": 30}},
    {{"zona": "Área sin vegetación/barbecho", "ndvi": "0.XX", "estado": "Sin cobertura/Suelo desnudo", "pct": 10}}
  ],
  "alertas": [
    {{"tipo": "critical/warn/ok", "titulo": "Alerta de sequía / estrés hídrico / plagas / helada / inundación", "desc": "descripción concreta de lo detectado"}},
    {{"tipo": "critical/warn/ok", "titulo": "Estado de cultivos o zonas degradadas", "desc": "descripción concreta"}},
    {{"tipo": "warn/ok", "titulo": "Recomendación de riego o intervención", "desc": "acción sugerida basada en la imagen"}}
  ],
  "diagnostico": "4-5 oraciones técnicas sobre: estado general del campo, presencia o ausencia de sequía, nivel de estrés hídrico detectado, dimensión aproximada de los cultivos, zonas que requieren intervención urgente y tendencia general del área analizada.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "zona específica detectada", "tarea": "acción urgente de campo o monitoreo"}},
    {{"prioridad": "MEDIA", "zona": "zona específica detectada", "tarea": "acción de seguimiento o riego"}},
    {{"prioridad": "BAJA", "zona": "zona específica detectada", "tarea": "monitoreo preventivo"}}
  ]
}}""",

"mar": """Sos un experto en oceanografía, vigilancia marítima y economía azul con experiencia en detección de pesca ilegal e identificación de embarcaciones por imagen satelital.
Analizá esta imagen satelital marina{lugar_str} — puede provenir de SAOCOM 1A/1B (SAR banda L, CONAE), SABIA-Mar (oceanografía, CONAE) o constelación SIASGE — con máximo detalle y respondé ÚNICAMENTE con JSON puro sin backticks:
{{
  "zona": "nombre del cuerpo de agua o región marina detectada{lugar_default}",
  "metricas": [
    {{"label": "Embarcaciones totales", "value": "X", "sub": "detectadas en imagen SAOCOM/SAR", "color": "blue"}},
    {{"label": "Pesca ilegal sospechosa", "value": "X embarcaciones", "sub": "sin AIS o en zona restringida", "color": "red"}},
    {{"label": "Estado de mareas", "value": "Alta/Baja/Media", "sub": "estimación por patrón costero", "color": "blue"}},
    {{"label": "Temperatura sup. mar", "value": "X.X°C", "sub": "SST via SABIA-Mar / sensor térmico", "color": "blue"}},
    {{"label": "Productividad marina", "value": "Alta/Media/Baja", "sub": "clorofila-a via SABIA-Mar", "color": "green"}},
    {{"label": "Nivel de alerta", "value": "Verde/Amarillo/Rojo", "sub": "estado de vigilancia ZEE", "color": "amber"}}
  ],
  "zonas_ndvi": [
    {{"zona": "Zona de mayor actividad pesquera", "ndvi": "X embarcaciones", "estado": "Activa/Sospechosa/Normal", "pct": 85}},
    {{"zona": "Área de mareas altas", "ndvi": "Nivel X m", "estado": "Alta/Media/Baja", "pct": 65}},
    {{"zona": "Zona de productividad biológica", "ndvi": "Alta/Media", "estado": "Productiva/Normal/Baja", "pct": 50}},
    {{"zona": "Área costera / Puerto", "ndvi": "X embarcaciones", "estado": "Activo/Inactivo", "pct": 30}}
  ],
  "alertas": [
    {{"tipo": "critical/warn/ok", "titulo": "Pesca ilegal detectada / Embarcación sin transpondedor AIS", "desc": "descripción concreta de la embarcación o zona sospechosa detectada por SAOCOM"}},
    {{"tipo": "critical/warn/ok", "titulo": "Condición de marea / corriente extrema", "desc": "descripción del estado de mareas o corrientes detectadas"}},
    {{"tipo": "warn/ok", "titulo": "Estado general de la flota pesquera", "desc": "descripción de la actividad pesquera observada en la ZEE argentina"}}
  ],
  "diagnostico": "4-5 oraciones técnicas sobre: cantidad y tipo de embarcaciones detectadas via SAOCOM SAR, presencia de actividad pesquera ilegal o sospechosa en la ZEE argentina (embarcaciones sin AIS, en zonas restringidas o con patrones anómalos), estado de las mareas, condiciones oceanográficas (temperatura y clorofila via SABIA-Mar) y nivel de alerta recomendado para la Prefectura Naval y CONAE.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "zona sospechosa específica", "tarea": "intercepción o verificación coordinada con Prefectura Naval"}},
    {{"prioridad": "MEDIA", "zona": "área de monitoreo", "tarea": "patrullaje o seguimiento de flota con próxima pasada SAOCOM"}},
    {{"prioridad": "BAJA", "zona": "zona costera", "tarea": "monitoreo preventivo de mareas y accesos portuarios"}}
  ]
}}""",

"metano": """Sos un experto en monitoreo atmosférico de gases de efecto invernadero, especializado en detección de fugas de metano (CH₄) y generación de alertas ambientales.
Analizá esta imagen de columna atmosférica de CH₄{lugar_str} — puede provenir de TROPOMI/Sentinel-5P (ESA/Copernicus) o sensores equivalentes — con máximo detalle y respondé ÚNICAMENTE con JSON puro sin backticks:
{{
  "zona": "nombre del área o región con emisiones detectadas{lugar_default}",
  "metricas": [
    {{"label": "CH₄ promedio", "value": "X.XXX ppb", "sub": "concentración columna total", "color": "red"}},
    {{"label": "Pico de emisión", "value": "X.XXX ppb", "sub": "valor máximo detectado", "color": "red"}},
    {{"label": "Fugas detectadas", "value": "X focos", "sub": "puntos de emisión identificados", "color": "red"}},
    {{"label": "Anomalía sobre base", "value": "+X ppb", "sub": "desviación sobre línea base global (~1900 ppb)", "color": "amber"}},
    {{"label": "Área afectada", "value": "~X.XXX km²", "sub": "superficie con emisiones elevadas", "color": "amber"}},
    {{"label": "Nivel de alerta", "value": "CRÍTICO/ALTO/MEDIO/BAJO", "sub": "clasificación de riesgo IA", "color": "red"}}
  ],
  "zonas_ndvi": [
    {{"zona": "Foco principal de fuga", "ndvi": "X.XXX ppb", "estado": "FUGA ACTIVA / Crítico", "pct": 95}},
    {{"zona": "Pluma de dispersión", "ndvi": "X.XXX ppb", "estado": "Elevado / En dispersión", "pct": 70}},
    {{"zona": "Área secundaria afectada", "ndvi": "X.XXX ppb", "estado": "Moderado / En monitoreo", "pct": 45}},
    {{"zona": "Zona de línea base", "ndvi": "~1.900 ppb", "estado": "Normal / Sin anomalía", "pct": 15}}
  ],
  "alertas": [
    {{"tipo": "critical", "titulo": "FUGA DE METANO ACTIVA detectada", "desc": "descripción de la fuga: ubicación estimada, intensidad y posible fuente (gasoducto, pozo, relleno sanitario, ganadería, humedal)"}},
    {{"tipo": "critical/warn", "titulo": "Pluma de dispersión identificada", "desc": "dirección y extensión de la pluma, vientos estimados y zonas en riesgo de exposición"}},
    {{"tipo": "warn/ok", "titulo": "Fuentes probables de emisión", "desc": "identificación de posibles fuentes: industria energética, agricultura, ganadería, descomposición orgánica"}}
  ],
  "diagnostico": "4-5 oraciones técnicas sobre: nivel de concentración de CH₄ detectado y comparación con línea base global, identificación de focos activos de fuga y sus posibles fuentes (sector energético, ganadería, humedales, industria), extensión y dirección de la pluma de dispersión, nivel de riesgo ambiental y para la salud, y acciones urgentes recomendadas para organismos ambientales y operadores de infraestructura.",
  "misiones": [
    {{"prioridad": "ALTA", "zona": "foco de fuga detectado", "tarea": "inspección urgente in-situ y cierre de válvulas / aislamiento del área"}},
    {{"prioridad": "ALTA", "zona": "pluma de dispersión", "tarea": "alerta a poblaciones cercanas y autoridades ambientales"}},
    {{"prioridad": "MEDIA", "zona": "área secundaria", "tarea": "muestreo atmosférico y validación con sensores terrestres"}}
  ]
}}"""
}

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
                "system": "Sos el sistema de análisis satelital Vertech TdF, desarrollado en Tierra del Fuego, Argentina. Analizás imágenes de la constelación CONAE (SAOCOM 1A/1B, SABIA-Mar, SIASGE) y datos complementarios de ESA/Copernicus. Tu especialidad es la ZEE argentina, el Mar Argentino, la Patagonia y ecosistemas subantárticos. Respondés SIEMPRE en JSON puro sin backticks ni texto adicional.",
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
        limpio = texto.replace("```json", "").replace("```", "").strip()
        inicio = limpio.find("{")
        fin = limpio.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            limpio = limpio[inicio:fin]
        return json.loads(limpio)
    except Exception as e:
        raise HTTPException(502, f"Error JSON: {str(e)} | Texto: {texto[:300]}")

@app.get("/")
def root():
    return {"status": "ok", "app": "Vertech TdF API", "version": "3.2.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "api_key_configured": ANTHROPIC_API_KEY.startswith("sk-ant-")}
