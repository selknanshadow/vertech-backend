"""
Vertech TdF — Backend unificado
Soporta MAREA (economía azul) y futuros módulos
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Vertech TdF API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
COPERNICUS_USER     = os.getenv("COPERNICUS_USER", "")
COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")

# ── Modelos ──
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

# ── Prompts de texto por módulo ──
IA_PROMPTS = {
    "pesquero": "Analizá las condiciones oceánicas de la zona indicada y generá un informe ejecutivo de 5 oraciones sobre la situación pesquera: productividad biológica, temperatura superficial, corrientes y recomendaciones operativas. Respondé en español e inglés alternando.",
    "termico": "Evaluá el estado térmico de la zona marina en 5 oraciones. ¿Qué implica para el ecosistema marino, la distribución de especies y la actividad pesquera? Respondé en español e inglés.",
    "productividad": "Analizá la productividad marina de la zona en 5 oraciones: biomasa fitoplanctónica, condiciones para la pesca y tendencias estacionales. Respondé en español e inglés.",
    "economia": "Estimá el impacto económico de las condiciones oceanográficas actuales en 5 oraciones. Incluí implicancias para la industria pesquera y la economía azul regional. Respondé en español e inglés.",
    "ch4riesgo": "Evaluá el nivel de riesgo de emisiones de CH₄ en la zona analizada en 5 oraciones. Clasificá el riesgo e identificá áreas críticas. Respondé en español e inglés.",
    "ch4fuente": "Identificá las fuentes más probables de emisión de CH₄ en la zona en 5 oraciones. Considerá sector energético, ganadería, humedales e industria. Respondé en español e inglés.",
    "ch4tendencia": "Analizá la tendencia de CH₄ en la zona en 5 oraciones y proyectá los próximos 7 días. Respondé en español e inglés.",
    "ch4accion": "Generá 4 acciones numeradas, concretas y operativas ante las emisiones de CH₄ detectadas. Para autoridades ambientales y sector energético. Respondé en español e inglés.",
}

# ── Llamada a Claude ──
async def llamar_claude(messages: list, system: str, max_tokens: int = 1200) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            }
        )
        if r.status_code != 200:
            raise HTTPException(502, f"Error Claude API: {r.text}")
        return r.json()["content"][0]["text"]

# ── ENDPOINT: análisis de texto ──
@app.post("/analizar-texto")
async def analizar_texto(req: TextRequest):
    prompt_base = IA_PROMPTS.get(req.prompt_key, "")
    if not prompt_base:
        raise HTTPException(400, f"Prompt '{req.prompt_key}' no encontrado.")
    
    prompt_final = prompt_base
    if req.contexto:
        prompt_final = f"Contexto de la zona: {req.contexto}\n\n{prompt_base}"

    texto = await llamar_claude(
        messages=[{"role": "user", "content": prompt_final}],
        system="Sos el sistema de análisis satelital Vertech TdF. Respondés en español e inglés de forma técnica, concisa y orientada a la acción para organismos estatales."
    )
    return {"texto": texto}

# ── ENDPOINT: análisis de imagen ──
@app.post("/analizar-imagen")
async def analizar_imagen(req: ImageRequest):
    import json as json_lib

    # Si viene prompt personalizado (MAREA), úsalo directamente
    if req.prompt_custom:
        prompt_texto = req.prompt_custom
    else:
        # Prompts genéricos por tipo
        prompts = {
            "mar": f"""Analizás una imagen satelital del mar/océano de: {req.lugar} ({req.fuente}, {req.fecha}).
Respondé SOLO en JSON puro sin backticks:
{{"indicadores":{{"temperatura":"X.X°C","temperatura_estado":"normal|elevada|baja","temperatura_ref":"explicación breve es/en","clorofila":"X.X mg/m³","clorofila_estado":"alta|media|baja","clorofila_ref":"explicación breve","turbidez":"X NTU","turbidez_estado":"ok|moderada|elevada","turbidez_ref":"explicación breve","embarcaciones":"X","embarcaciones_estado":"normal|elevado|sospechoso","embarcaciones_ref":"explicación breve","productividad":"Alta|Media|Baja","productividad_estado":"ok|warn|danger","productividad_ref":"explicación breve","nivel_alerta":"Verde|Amarillo|Rojo","nivel_alerta_estado":"ok|warn|danger","nivel_alerta_ref":"resumen del riesgo"}},"diagnostico":"5-7 oraciones en español e inglés alternando con diagnóstico oceanográfico completo de {req.lugar}.","alertas":[{{"titulo":"alerta en español / English","descripcion":"descripción clara","nivel":"rojo|amarillo|verde","icono":"ti-alert-triangle|ti-thermometer|ti-ship|ti-fish"}}],"acciones":[{{"texto":"acción concreta para organismo estatal en español / English","organismo":"nombre del organismo"}}]}}""",

            "campo": f"""Analizás una imagen satelital de campo/vegetación de: {req.lugar} ({req.fuente}, {req.fecha}).
Respondé SOLO en JSON puro sin backticks:
{{"indices":[{{"label":"NDVI promedio","value":"0.XX","sub":"estado vegetal"}},{{"label":"Humedad estimada","value":"XX%","sub":"condición hídrica"}},{{"label":"Cobertura vegetal","value":"XX%","sub":"densidad"}},{{"label":"Zonas críticas","value":"X","sub":"requieren acción"}}],"diagnostico":"5-6 oraciones en español e inglés sobre el estado del campo en {req.lugar}.","misiones":[{{"tarea":"descripción","prioridad":"alta","zona":"zona"}},{{"tarea":"descripción","prioridad":"media","zona":"zona"}},{{"tarea":"descripción","prioridad":"baja","zona":"zona"}}]}}""",

            "metano": f"""Analizás una imagen satelital de CH₄ de: {req.lugar} ({req.fuente}, {req.fecha}).
Respondé SOLO en JSON puro sin backticks:
{{"indices":[{{"label":"CH₄ estimado","value":"XXXX ppb","sub":"zona general"}},{{"label":"Pico detectado","value":"XXXX ppb","sub":"zona crítica"}},{{"label":"Anomalías","value":"X zonas","sub":"sobre umbral"}},{{"label":"Riesgo","value":"Alto|Medio|Bajo","sub":"clasificación"}}],"diagnostico":"5-6 oraciones en español e inglés sobre emisiones en {req.lugar}.","misiones":[{{"tarea":"acción urgente","prioridad":"alta","zona":"zona"}},{{"tarea":"descripción","prioridad":"media","zona":"zona"}},{{"tarea":"descripción","prioridad":"baja","zona":"zona"}}]}}"""
        }
        prompt_texto = prompts.get(req.tipo, prompts["mar"])

    texto = await llamar_claude(
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": req.imagen_base64
                    }
                },
                {"type": "text", "text": prompt_texto}
            ]
        }],
        system="Sos el sistema de análisis satelital Vertech TdF. Analizás imágenes satelitales de cualquier zona del mundo y respondés SIEMPRE en JSON puro sin texto adicional ni backticks.",
        max_tokens=1500
    )

    try:
        return json_lib.loads(texto.replace("```json", "").replace("```", "").strip())
    except Exception:
        raise HTTPException(502, f"Error al parsear respuesta de IA: {texto[:200]}")

# ── Health check ──
@app.get("/")
def root():
    return {"status": "ok", "app": "Vertech TdF API", "version": "2.0.0", "modulos": ["MAREA - Economía Azul"]}

@app.get("/health")
def health():
    return {"status": "healthy"}
