from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import json

app = FastAPI(title="Vertech TdF API", version="2.0.0")

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
    tipo: str = "mar"
    lugar: str = "zona no especificada"
    fecha: str = "no especificada"
    fuente: str = "imagen satelital"
    prompt_custom: str = ""

IA_PROMPTS = {
    "pesquero": "Analizá las condiciones oceánicas y generá un informe de 5 oraciones sobre la situación pesquera en español e inglés.",
    "termico": "Evaluá el estado térmico marino en 5 oraciones en español e inglés.",
    "productividad": "Analizá la productividad marina en 5 oraciones en español e inglés.",
    "economia": "Estimá el impacto económico oceanográfico en 5 oraciones en español e inglés.",
    "ch4riesgo": "Evaluá el riesgo de emisiones CH₄ en 5 oraciones en español e inglés.",
    "ch4fuente": "Identificá fuentes probables de CH₄ en 5 oraciones en español e inglés.",
    "ch4tendencia": "Analizá la tendencia de CH₄ en 5 oraciones en español e inglés.",
    "ch4accion": "Generá 4 acciones ante emisiones CH₄ en español e inglés.",
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
            json={"model":"claude-sonnet-4-6","max_tokens":800,"system":"Sos el sistema de análisis satelital Vertech TdF. Respondés en español e inglés.","messages":[{"role":"user","content":prompt}]},
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"}
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Error Claude: {r.text}")
    return {"texto": r.json()["content"][0]["text"]}

@app.post("/analizar-imagen")
async def analizar_imagen(req: ImageRequest):
    if req.prompt_custom:
        prompt_texto = req.prompt_custom
    else:
        prompts = {
            "mar": f"Analizás imagen satelital del mar de {req.lugar} ({req.fuente}, {req.fecha}). Respondé SOLO en JSON puro sin backticks: {{\"indicadores\":{{\"temperatura\":\"X°C\",\"temperatura_estado\":\"normal\",\"temperatura_ref\":\"referencia\",\"clorofila\":\"X mg/m³\",\"clorofila_estado\":\"alta\",\"clorofila_ref\":\"referencia\",\"turbidez\":\"X NTU\",\"turbidez_estado\":\"ok\",\"turbidez_ref\":\"referencia\",\"embarcaciones\":\"X\",\"embarcaciones_estado\":\"normal\",\"embarcaciones_ref\":\"referencia\",\"productividad\":\"Alta\",\"productividad_estado\":\"ok\",\"productividad_ref\":\"referencia\",\"nivel_alerta\":\"Verde\",\"nivel_alerta_estado\":\"ok\",\"nivel_alerta_ref\":\"sin anomalias\"}},\"diagnostico\":\"5 oraciones en español e inglés sobre {req.lugar}.\",\"alertas\":[{{\"titulo\":\"alerta\",\"descripcion\":\"descripción\",\"nivel\":\"verde\",\"icono\":\"ti-check\"}}],\"acciones\":[{{\"texto\":\"acción\",\"organismo\":\"organismo\"}}]}}",
            "campo": f"Analizás imagen satelital de campo de {req.lugar}. Respondé SOLO en JSON puro sin backticks: {{\"indices\":[{{\"label\":\"NDVI\",\"value\":\"0.XX\",\"sub\":\"estado\"}}],\"diagnostico\":\"5 oraciones sobre {req.lugar}.\",\"misiones\":[{{\"tarea\":\"tarea\",\"prioridad\":\"alta\",\"zona\":\"zona\"}}]}}",
            "metano": f"Analizás imagen satelital de CH₄ de {req.lugar}. Respondé SOLO en JSON puro sin backticks: {{\"indices\":[{{\"label\":\"CH₄\",\"value\":\"XXXX ppb\",\"sub\":\"estado\"}}],\"diagnostico\":\"5 oraciones sobre {req.lugar}.\",\"misiones\":[{{\"tarea\":\"tarea\",\"prioridad\":\"alta\",\"zona\":\"zona\"}}]}}"
        }
        prompt_texto = prompts.get(req.tipo, prompts["mar"])

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model":"claude-sonnet-4-6",
                "max_tokens":1200,
                "system":"Sos el sistema de análisis satelital Vertech TdF. Respondés SIEMPRE en JSON puro sin backticks.",
                "messages":[{"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":"image/png","data":req.imagen_base64}},
                    {"type":"text","text":prompt_texto}
                ]}]
            },
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"}
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Error Claude: {r.text}")
    texto = r.json()["content"][0]["text"]
    try:
        return json.loads(texto.replace("```json","").replace("```","").strip())
    except:
        raise HTTPException(502, f"Error JSON: {texto[:300]}")

@app.get("/")
def root():
    return {"status":"ok","app":"Vertech TdF API","version":"2.0.0"}

@app.get("/health")
def health():
    return {"status":"healthy"}
