from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import json

app = FastAPI(title="Vertech TdF API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class TextRequest(BaseModel):
    prompt_key: str
    contexto: str = ""

class ImageRequest(BaseModel):
    imagen_base64: str
    media_type: str = "image/jpeg"   # ← ahora viene del frontend
    tipo: str = "mar"
    lugar: str = "zona no especificada"
    fecha: str = "no especificada"
    fuente: str = "imagen satelital"
    prompt_custom: str = ""

IA_PROMPTS = {
    "pesquero":    "Analizá las condiciones oceánicas y generá un informe de 5 oraciones sobre la situación pesquera en español.",
    "termico":     "Evaluá el estado térmico marino en 5 oraciones en español.",
    "productividad":"Analizá la productividad marina en 5 oraciones en español.",
    "economia":    "Estimá el impacto económico oceanográfico en 5 oraciones en español.",
    "ch4riesgo":   "Evaluá el riesgo de emisiones CH₄ en 5 oraciones en español.",
    "ch4fuente":   "Identificá fuentes probables de CH₄ en 5 oraciones en español.",
    "ch4tendencia":"Analizá la tendencia de CH₄ en 5 oraciones en español.",
    "ch4accion":   "Generá 4 acciones ante emisiones CH₄ en español.",
}

PROMPTS_IMAGEN = {
    "campo": """Sos un experto en teledetección agrícola de Patagonia austral.
Analizá esta imagen satelital de {lugar} ({fuente}, {fecha}).
Respondé SOLO con JSON puro sin backticks:
{{"indices":"NDVI estimado: X\\nCobertura vegetal: X%\\nHumedad estimada: X%\\nZonas críticas: X","diagnostico":"5-6 oraciones técnicas sobre estado del campo, estrés hídrico, distribución de cobertura y riesgos.","misiones":"[ALTA] Zona X — tarea específica\\n[MEDIA] Zona Y — tarea\\n[BAJA] Zona Z — tarea"}}""",

    "mar": """Sos un experto en oceanografía del Mar Argentino y Canal Beagle.
Analizá esta imagen satelital de {lugar} ({fuente}, {fecha}).
Respondé SOLO con JSON puro sin backticks:
{{"indices":"Temperatura superficial: X°C\\nProductividad marina: X\\nTurbidez: X NTU\\nEmbarcaciones detectadas: X","diagnostico":"5-6 oraciones técnicas sobre estado oceanográfico, productividad biológica y condiciones para pesca.","misiones":"[ALTA] Zona X — acción\\n[MEDIA] Zona Y — acción\\n[BAJA] Zona Z — acción"}}""",

    "metano": """Sos un experto en monitoreo atmosférico de CH₄ en la Cuenca Austral.
Analizá esta imagen TROPOMI de {lugar} ({fuente}, {fecha}).
Respondé SOLO con JSON puro sin backticks:
{{"indices":"Concentración CH₄: X ppb\\nZonas de emisión: X\\nAnomalías detectadas: X\\nNivel de riesgo: X","diagnostico":"5-6 oraciones técnicas sobre riesgo, fuentes probables, dispersión y tendencia.","misiones":"[ALTA] Zona X — acción urgente\\n[MEDIA] Zona Y — acción\\n[BAJA] Zona Z — acción"}}"""
}

def get_headers():
    return {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

@app.post("/analizar-texto")
async def analizar_texto(req: TextRequest):
    prompt = IA_PROMPTS.get(req.prompt_key, "")
    if not prompt:
        raise HTTPException(400, f"Prompt no encontrado: {req.prompt_key}")
    if req.contexto:
        prompt = f"Contexto: {req.contexto}\n\n{prompt}"

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 800,
                "system": "Sos el sistema de análisis satelital Vertech TdF. Respondés en español.",
                "messages": [{"role": "user", "content": prompt}]
            },
            headers=get_headers()
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Error Claude: {r.text}")
    return {"texto": r.json()["content"][0]["text"]}

@app.post("/analizar-imagen")
async def analizar_imagen(req: ImageRequest):
    # Determinar media_type válido
    media_type = req.media_type
    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"  # fallback seguro

    # Construir prompt
    if req.prompt_custom:
        prompt_texto = req.prompt_custom
    else:
        template = PROMPTS_IMAGEN.get(req.tipo, PROMPTS_IMAGEN["mar"])
        prompt_texto = template.format(
            lugar=req.lugar,
            fuente=req.fuente,
            fecha=req.fecha
        )

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1200,
                "system": "Sos el sistema de análisis satelital Vertech TdF. Respondés SIEMPRE en JSON puro sin backticks.",
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": req.imagen_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_texto
                        }
                    ]
                }]
            },
            headers=get_headers()
        )

    if r.status_code != 200:
        raise HTTPException(502, f"Error Claude: {r.text}")

    texto = r.json()["content"][0]["text"]
    try:
        return json.loads(texto.replace("```json", "").replace("```", "").strip())
    except Exception:
        raise HTTPException(502, f"Error JSON: {texto[:300]}")

@app.get("/")
def root():
    return {"status": "ok", "app": "Vertech TdF API", "version": "2.1.0"}

@app.get("/health")
def health():
    key_ok = ANTHROPIC_API_KEY.startswith("sk-ant-")
    return {
        "status": "healthy",
        "api_key_configured": key_ok
    }
