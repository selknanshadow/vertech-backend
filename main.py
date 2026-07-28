from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import json
import re

app = FastAPI(title="Vertech TdF API", version="4.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE MOTOR IA
# ──────────────────────────────────────────────────────────
# Diseñado para ser INTERCAMBIABLE: en despliegue institucional
# CONAE puede apuntar AI_ENDPOINT a un modelo local (Ollama,
# vLLM, LM Studio) sin modificar la lógica de la aplicación.
# ══════════════════════════════════════════════════════════
AI_ENDPOINT = os.getenv("AI_ENDPOINT", "https://api.anthropic.com/v1/messages")
AI_MODEL    = os.getenv("AI_MODEL", "claude-sonnet-4-6")
AI_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODE     = os.getenv("AI_MODE", "cloud")  # "cloud" | "local"


# ══════════════════ MODELOS DE DATOS ══════════════════

class ImageRequest(BaseModel):
    imagen_base64: str
    media_type: str = "image/jpeg"
    tipo: str = "campo"
    lugar: str = ""
    fuente: str = "imagen satelital"

class MapaQARequest(BaseModel):
    imagen_base64: str
    media_type: str = "image/jpeg"
    tipo_evento: str = "general"      # incendio | inundacion | volcanico | nevada | general
    descripcion: str = ""              # descripción declarada del mapa
    organismo: str = "CONAE"

class ChatMessage(BaseModel):
    role: str      # "user" | "assistant"
    content: str

class MapaChatRequest(BaseModel):
    imagen_base64: str
    media_type: str = "image/jpeg"
    historial: List[ChatMessage] = []
    pregunta: str
    tipo_evento: str = "general"


# ══════════════════ PROMPTS DE ANÁLISIS SATELITAL ══════════════════

PROMPTS = {

"campo": """Sos un experto en teledetección agrícola, análisis de vegetación y monitoreo de cultivos satelital.
Analizá esta imagen satelital{lugar_str} — puede provenir de SAOCOM (SAR banda L), constelación SIASGE o Sentinel-2 — y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
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


# ══════════════════ PROMPT QA DE MAPAS DE EMERGENCIA ══════════════════

CONTEXTO_EVENTO = {
    "incendio":   "incendio forestal o de interfaz — se esperan capas de área quemada (burn scar), severidad, focos de calor, dirección de propagación y áreas de riesgo",
    "inundacion": "inundación — se esperan capas de lámina de agua, área anegada, comparación pre/post evento, infraestructura afectada y población expuesta",
    "volcanico":  "erupción volcánica — se esperan capas de dispersión de ceniza, radio de exclusión, flujos piroclásticos, rutas afectadas y centros poblados en riesgo",
    "nevada":     "nevada extrema — se esperan capas de cobertura nívea, espesor estimado, rutas cortadas, localidades aisladas y accesibilidad",
    "general":    "evento de emergencia general — se esperan capas temáticas del fenómeno, área afectada e infraestructura crítica",
}

SISTEMA_QA = """Sos un asistente experto en control de calidad cartográfica de la Unidad de Emergencias y Alertas Tempranas de CONAE (Comisión Nacional de Actividades Espaciales, Argentina).

Tu función es revisar mapas temáticos de emergencia ANTES de su entrega a organismos de decisión (Defensa Civil, Protección Civil, gobiernos provinciales, Ministerios).

CONTEXTO OPERATIVO CRÍTICO:
- Estos mapas se producen bajo presión de tiempo durante emergencias reales
- Un error u omisión puede afectar la toma de decisiones en una crisis
- Los técnicos necesitan observaciones concretas y accionables, no teoría
- NUNCA reemplazás el criterio técnico del operador: lo asistís

ESTÁNDARES CARTOGRÁFICOS QUE DEBÉS VERIFICAR:
1. ELEMENTOS OBLIGATORIOS: título descriptivo, escala (gráfica y/o numérica), flecha de norte, grilla de coordenadas, sistema de referencia (datum/proyección), fecha de la imagen, fecha de elaboración
2. LEYENDA: completa, con todos los símbolos usados en el mapa, sin símbolos huérfanos (en leyenda pero no en mapa) ni símbolos sin declarar (en mapa pero no en leyenda)
3. IDENTIDAD INSTITUCIONAL: logo CONAE, logo de organismo solicitante, créditos de fuente satelital (SAOCOM, Sentinel, Landsat), disclaimer de uso
4. REDACCIÓN: ortografía, gramática, tildes, coherencia terminológica, uso correcto de topónimos oficiales argentinos
5. COHERENCIA: el contenido visible del mapa debe corresponder con el título y la descripción declarada
6. LEGIBILIDAD: contraste suficiente, tamaño de tipografía, superposición de elementos, densidad de información
7. INFORMACIÓN CRÍTICA: metadatos de la imagen fuente, resolución espacial, nivel de procesamiento, limitaciones del producto

Sos directo, técnico y concreto. Priorizás lo que puede causar un error operativo real."""

PROMPT_QA_INICIAL = """Realizá el control de calidad de este mapa temático de emergencia.

CONTEXTO DEL EVENTO: {contexto_evento}
DESCRIPCIÓN DECLARADA POR EL TÉCNICO: {descripcion}
ORGANISMO EMISOR: {organismo}

Revisá el mapa contra los estándares cartográficos y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
{{
  "titulo_detectado": "título que aparece en el mapa, o 'No detectado' si falta",
  "tipo_producto": "clasificación del producto cartográfico observado",
  "score": {{
    "global": 85,
    "cartografico": 90,
    "institucional": 70,
    "redaccion": 95,
    "coherencia": 85
  }},
  "checklist": [
    {{"item": "Título descriptivo", "estado": "ok", "obs": "presente y descriptivo"}},
    {{"item": "Escala gráfica/numérica", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Flecha de norte", "estado": "falta", "obs": "no se detecta indicador de orientación"}},
    {{"item": "Grilla de coordenadas", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Sistema de referencia", "estado": "revisar", "obs": "observación breve"}},
    {{"item": "Leyenda completa", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Logo CONAE", "estado": "falta", "obs": "observación breve"}},
    {{"item": "Créditos fuente satelital", "estado": "revisar", "obs": "observación breve"}},
    {{"item": "Fecha imagen / elaboración", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Legibilidad general", "estado": "ok", "obs": "observación breve"}}
  ],
  "criticos": [
    {{"titulo": "título del error crítico", "desc": "descripción concreta del problema y su impacto operativo", "accion": "corrección específica sugerida"}}
  ],
  "advertencias": [
    {{"titulo": "título de la advertencia", "desc": "descripción del problema menor", "accion": "sugerencia de mejora"}}
  ],
  "correcciones_texto": [
    {{"encontrado": "texto tal como aparece en el mapa", "sugerido": "texto corregido", "motivo": "ortografía / gramática / terminología"}}
  ],
  "resumen": "3-4 oraciones con el veredicto general del control de calidad, qué está bien, qué debe corregirse antes de la entrega y si el mapa está apto para distribución.",
  "apto_entrega": "SI"
}}

REGLAS PARA LOS CAMPOS:
- "estado" solo puede ser: "ok", "falta" o "revisar"
- "score" son enteros de 0 a 100
- "apto_entrega" solo puede ser: "SI", "NO" o "CON_CORRECCIONES"
- Si no encontrás errores críticos, dejá "criticos" como array vacío []
- Si no encontrás errores de texto, dejá "correcciones_texto" como array vacío []

LÍMITES DE EXTENSIÓN (obligatorio para evitar respuestas cortadas):
- "checklist": exactamente 10 items, "obs" de máximo 12 palabras cada uno
- "criticos": máximo 4 items, "desc" de máximo 25 palabras
- "advertencias": máximo 4 items, "desc" de máximo 25 palabras
- "correcciones_texto": máximo 5 items
- "resumen": máximo 60 palabras
Priorizá siempre los hallazgos de mayor impacto operativo.
- Sé honesto: si la imagen no es un mapa temático, indicalo en "resumen" y poné score bajo"""


# ══════════════════ UTILIDADES ══════════════════

def _reparar_truncado(txt: str) -> str:
    """
    Repara un JSON cortado por límite de tokens.
    Descarta el último elemento incompleto y cierra las estructuras abiertas.
    """
    # Cortar en el último separador estructural completo
    for corte in ('},', '],', '",'):
        i = txt.rfind(corte)
        if i > 0:
            txt = txt[:i + 1]
            break
    else:
        i = max(txt.rfind('}'), txt.rfind(']'), txt.rfind('"'))
        if i > 0:
            txt = txt[:i + 1]

    txt = txt.rstrip().rstrip(',')

    # Contar delimitadores abiertos ignorando los que están dentro de strings
    pila, en_str, escape = [], False, False
    for ch in txt:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            en_str = not en_str
            continue
        if en_str:
            continue
        if ch in '{[':
            pila.append(ch)
        elif ch in '}]' and pila:
            pila.pop()

    if en_str:
        txt += '"'
    for ch in reversed(pila):
        txt += '}' if ch == '{' else ']'
    return txt


def limpiar_json(texto: str) -> str:
    """Extrae y normaliza el bloque JSON de la respuesta del modelo."""
    texto = texto.replace("```json", "").replace("```", "").strip()
    inicio = texto.find("{")
    if inicio >= 0:
        texto = texto[inicio:]
    fin = texto.rfind("}") + 1
    if fin > 0:
        texto = texto[:fin]
    texto = re.sub(r',\s*([}\]])', r'\1', texto)
    return texto


def parsear_respuesta(texto: str) -> dict:
    """
    Parsea la respuesta del modelo con tolerancia a truncamiento.
    Primero intenta el parseo normal; si falla, repara y reintenta.
    """
    limpio = limpiar_json(texto)
    try:
        return json.loads(limpio)
    except json.JSONDecodeError:
        pass

    # Reintento sobre el texto crudo desde la primera llave
    crudo = texto.replace("```json", "").replace("```", "").strip()
    i = crudo.find("{")
    if i >= 0:
        crudo = crudo[i:]
    reparado = _reparar_truncado(crudo)
    reparado = re.sub(r',\s*([}\]])', r'\1', reparado)
    datos = json.loads(reparado)
    datos["_respuesta_truncada"] = True
    return datos


def get_headers():
    return {
        "Content-Type": "application/json",
        "x-api-key": AI_API_KEY,
        "anthropic-version": "2023-06-01"
    }


async def llamar_ia(payload: dict) -> str:
    """
    Punto único de llamada al motor de IA.
    En despliegue local CONAE, esta función es el único lugar
    que debe adaptarse para apuntar a un modelo on-premise.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(AI_ENDPOINT, json=payload, headers=get_headers())
    if r.status_code != 200:
        raise HTTPException(502, f"Error motor IA: {r.text}")
    return r.json()["content"][0]["text"]


# ══════════════════ ENDPOINT: ANÁLISIS SATELITAL ══════════════════

@app.post("/analizar-imagen")
async def analizar_imagen(req: ImageRequest):
    media_type = req.media_type
    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"

    lugar_str     = f" de {req.lugar}" if req.lugar else ""
    lugar_default = f", o '{req.lugar}' si no se puede determinar visualmente" if req.lugar else ", o 'Zona no especificada' si no se puede determinar"

    template     = PROMPTS.get(req.tipo, PROMPTS["campo"])
    prompt_texto = template.format(lugar_str=lugar_str, lugar_default=lugar_default)

    texto = await llamar_ia({
        "model": AI_MODEL,
        "max_tokens": 3000,
        "system": "Sos el sistema de análisis satelital Vertech TdF, desarrollado en Tierra del Fuego, Argentina. Analizás imágenes de la constelación CONAE (SAOCOM 1A/1B, SABIA-Mar, SIASGE) y datos complementarios de ESA/Copernicus. Tu especialidad es la ZEE argentina, el Mar Argentino, la Patagonia y ecosistemas subantárticos. Respondés SIEMPRE en JSON puro válido, sin backticks, sin texto adicional y SIN comas finales.",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": req.imagen_base64}},
                {"type": "text", "text": prompt_texto}
            ]
        }]
    })

    try:
        return parsear_respuesta(texto)
    except Exception as e:
        raise HTTPException(502, f"Error JSON: {str(e)} | Texto: {texto[:300]}")


# ══════════════════ ENDPOINT: QA DE MAPAS DE EMERGENCIA ══════════════════

@app.post("/qa-mapa")
async def qa_mapa(req: MapaQARequest):
    """Control de calidad inicial de un mapa temático de emergencia."""
    media_type = req.media_type
    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"

    contexto = CONTEXTO_EVENTO.get(req.tipo_evento, CONTEXTO_EVENTO["general"])
    descripcion = req.descripcion.strip() or "El técnico no proporcionó descripción — evaluá la coherencia solo con el contenido visible del mapa."

    prompt = PROMPT_QA_INICIAL.format(
        contexto_evento=contexto,
        descripcion=descripcion,
        organismo=req.organismo or "CONAE"
    )

    texto = await llamar_ia({
        "model": AI_MODEL,
        "max_tokens": 4000,
        "system": SISTEMA_QA + "\n\nRespondés SIEMPRE en JSON puro válido, sin backticks, sin texto adicional y SIN comas finales en arrays u objetos.",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": req.imagen_base64}},
                {"type": "text", "text": prompt}
            ]
        }]
    })

    try:
        return parsear_respuesta(texto)
    except Exception as e:
        raise HTTPException(502, f"Error JSON: {str(e)} | Texto: {texto[:300]}")


# ══════════════════ ENDPOINT: CHAT ITERATIVO SOBRE EL MAPA ══════════════════

@app.post("/qa-chat")
async def qa_chat(req: MapaChatRequest):
    """
    Diálogo iterativo con el técnico sobre el mapa cargado.
    Mantiene el contexto de la imagen en toda la conversación.
    """
    media_type = req.media_type
    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        media_type = "image/jpeg"

    contexto = CONTEXTO_EVENTO.get(req.tipo_evento, CONTEXTO_EVENTO["general"])

    # Primer mensaje: imagen + contexto
    mensajes = [{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": req.imagen_base64}},
            {"type": "text", "text": f"Este es el mapa temático de emergencia bajo revisión. Contexto del evento: {contexto}. Voy a hacerte consultas sobre este mapa."}
        ]
    }, {
        "role": "assistant",
        "content": "Recibí el mapa. Estoy listo para responder tus consultas sobre el control de calidad cartográfica."
    }]

    # Agregar historial previo
    for m in req.historial:
        if m.role in ("user", "assistant") and m.content.strip():
            mensajes.append({"role": m.role, "content": m.content})

    # Pregunta actual
    mensajes.append({"role": "user", "content": req.pregunta})

    texto = await llamar_ia({
        "model": AI_MODEL,
        "max_tokens": 1200,
        "system": SISTEMA_QA + "\n\nEn este modo conversacional respondés en texto plano, claro y conciso. Sin JSON. Máximo 4-5 oraciones salvo que te pidan detalle. Si el técnico pregunta algo fuera del alcance del control de calidad cartográfica, redirigí amablemente al tema.",
        "messages": mensajes
    })

    return {"respuesta": texto.strip()}


# ══════════════════════════════════════════════════════════
# MÓDULO QA ESTRUCTURAL — CONFIGURACIONES MAPSTORE2 / GEOJSON
# ══════════════════════════════════════════════════════════

class MapaJSONRequest(BaseModel):
    contenido_json: str
    nombre_archivo: str = "map.json"
    tipo_evento: str = "general"
    descripcion: str = ""


def analizar_mapstore(cfg: dict) -> dict:
    """
    Validación determinística de una configuración MapStore2.
    No usa IA: son reglas cartográficas verificables.
    """
    mapa    = cfg.get("map", {})
    capas   = mapa.get("layers", []) or []
    grupos  = mapa.get("groups", []) or []
    centro  = mapa.get("center", {}) or {}

    def titulo_grupo(g):
        t = g.get("title")
        if isinstance(t, dict):
            return t.get("default") or t.get("es-AR") or "(sin título)"
        return t or "(sin título)"

    visibles     = [c for c in capas if c.get("visibility")]
    ids_grupos   = {g.get("id") for g in grupos}
    grupos_usados = {c.get("group") for c in capas if c.get("group")}

    sin_desc      = [c.get("title","(sin título)") for c in capas if not c.get("description")]
    sin_creditos  = [c.get("title","(sin título)") for c in capas if not c.get("credits")]
    sin_titulo    = [c.get("id","(sin id)") for c in capas if not c.get("title")]
    sin_grupo     = [c.get("title","(sin título)") for c in capas if not c.get("group")]
    grupo_roto    = [c.get("title","(sin título)") for c in capas
                     if c.get("group") and c["group"] not in ids_grupos and c["group"] != "background"]
    url_insegura  = [c.get("title","(sin título)") for c in capas
                     if str(c.get("url","")).startswith("http://")]
    grupos_vacios = [titulo_grupo(g) for g in grupos if g.get("id") not in grupos_usados]

    from collections import Counter
    dup = {k: v for k, v in Counter(
        c.get("title","(sin título)") for c in capas).items() if v > 1}

    urls = sorted({c.get("url") for c in capas if c.get("url")})
    externos = [u for u in urls
                if not any(d in u.lower() for d in ("conae.gov.ar", "conae.gob.ar", "ign.gob.ar", "ign.gov.ar"))]

    return {
        "formato": "MapStore2",
        "version_config": cfg.get("version"),
        "proyeccion": mapa.get("projection"),
        "crs_centro": centro.get("crs"),
        "zoom": mapa.get("zoom"),
        "unidades": mapa.get("units"),
        "total_capas": len(capas),
        "capas_visibles": len(visibles),
        "total_grupos": len(grupos),
        "servicios_wms": len(urls),
        "titulos_visibles": [c.get("title") for c in visibles][:15],
        "servicios_externos": externos,
        "hallazgos": {
            "sin_descripcion": sin_desc,
            "sin_creditos": sin_creditos,
            "sin_titulo": sin_titulo,
            "sin_grupo": sin_grupo,
            "grupo_inexistente": grupo_roto,
            "url_insegura": url_insegura,
            "grupos_vacios": grupos_vacios,
            "titulos_duplicados": dup,
        },
    }


def analizar_geojson(cfg: dict) -> dict:
    """Validación determinística de un GeoJSON estándar."""
    feats = cfg.get("features", []) or []
    props_todas, geoms = set(), {}
    sin_props, sin_geom = 0, 0

    for f in feats:
        p = f.get("properties") or {}
        g = f.get("geometry") or {}
        if not p:
            sin_props += 1
        else:
            props_todas.update(p.keys())
        if not g:
            sin_geom += 1
        else:
            t = g.get("type", "?")
            geoms[t] = geoms.get(t, 0) + 1

    # atributos faltantes por feature
    incompletos = 0
    for f in feats:
        p = f.get("properties") or {}
        if props_todas and any(p.get(k) in (None, "") for k in props_todas):
            incompletos += 1

    crs = cfg.get("crs", {}).get("properties", {}).get("name") if isinstance(cfg.get("crs"), dict) else None

    return {
        "formato": "GeoJSON",
        "tipo": cfg.get("type"),
        "crs_declarado": crs,
        "total_features": len(feats),
        "tipos_geometria": geoms,
        "atributos": sorted(props_todas),
        "hallazgos": {
            "features_sin_propiedades": sin_props,
            "features_sin_geometria": sin_geom,
            "features_con_atributos_vacios": incompletos,
        },
    }


PROMPT_QA_JSON = """Realizá el control de calidad de esta configuración cartográfica digital destinada a la gestión de emergencias.

ARCHIVO: {nombre}
CONTEXTO DEL EVENTO: {contexto}
DESCRIPCIÓN DECLARADA: {descripcion}

ANÁLISIS ESTRUCTURAL AUTOMÁTICO (validación determinística ya ejecutada):
{resumen}

Interpretá estos hallazgos desde la óptica del control de calidad cartográfica institucional de CONAE y respondé ÚNICAMENTE con JSON puro sin backticks ni comas finales:
{{
  "titulo_detectado": "descripción del producto cartográfico digital analizado",
  "tipo_producto": "clasificación técnica del archivo",
  "score": {{
    "global": 85,
    "cartografico": 90,
    "institucional": 70,
    "redaccion": 95,
    "coherencia": 85
  }},
  "checklist": [
    {{"item": "Sistema de referencia declarado", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Proyección coherente", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Capas con título", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Capas con descripción", "estado": "revisar", "obs": "observación breve"}},
    {{"item": "Créditos y atribución de fuente", "estado": "falta", "obs": "observación breve"}},
    {{"item": "Organización en grupos temáticos", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Integridad referencial capa-grupo", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Seguridad de servicios (HTTPS)", "estado": "ok", "obs": "observación breve"}},
    {{"item": "Dependencia de servicios externos", "estado": "revisar", "obs": "observación breve"}},
    {{"item": "Capas visibles al abrir el mapa", "estado": "ok", "obs": "observación breve"}}
  ],
  "criticos": [
    {{"titulo": "título del error crítico", "desc": "problema concreto e impacto operativo en una emergencia", "accion": "corrección específica"}}
  ],
  "advertencias": [
    {{"titulo": "título de la advertencia", "desc": "problema menor detectado", "accion": "sugerencia de mejora"}}
  ],
  "correcciones_texto": [
    {{"encontrado": "texto o nombre problemático", "sugerido": "versión corregida", "motivo": "nomenclatura / ortografía / terminología"}}
  ],
  "resumen": "3-4 oraciones con el veredicto del control de calidad estructural, qué debe corregirse antes de publicar y si la configuración es apta para uso operativo en emergencias.",
  "apto_entrega": "CON_CORRECCIONES"
}}

CRITERIOS DE EVALUACIÓN:
- "institucional" baja si hay muchas capas sin créditos ni atribución de fuente
- "cartografico" baja si falta CRS, hay integridad referencial rota o proyección inconsistente
- "coherencia" baja si hay grupos vacíos, títulos duplicados o capas huérfanas
- Los servicios externos son un riesgo de disponibilidad en emergencias: mencionalo
- Muchas capas visibles al inicio saturan la lectura del operador
- "estado" solo puede ser: "ok", "falta" o "revisar"
- "apto_entrega" solo puede ser: "SI", "NO" o "CON_CORRECCIONES"
- Si no hay hallazgos de una categoría, devolvé array vacío []

LÍMITES DE EXTENSIÓN (obligatorio para evitar respuestas cortadas):
- "checklist": exactamente 10 items, "obs" de máximo 12 palabras cada uno
- "criticos": máximo 4 items, "desc" de máximo 25 palabras
- "advertencias": máximo 4 items, "desc" de máximo 25 palabras
- "correcciones_texto": máximo 5 items
- "resumen": máximo 60 palabras
Priorizá siempre los hallazgos de mayor impacto operativo."""


@app.post("/qa-json")
async def qa_json(req: MapaJSONRequest):
    """Control de calidad de configuraciones cartográficas digitales (MapStore2 / GeoJSON)."""
    try:
        cfg = json.loads(req.contenido_json)
    except Exception as e:
        raise HTTPException(400, f"El archivo no es un JSON válido: {str(e)}")

    # Detección de formato y validación determinística
    if isinstance(cfg, dict) and "map" in cfg and isinstance(cfg.get("map"), dict):
        analisis = analizar_mapstore(cfg)
    elif isinstance(cfg, dict) and cfg.get("type") in ("FeatureCollection", "Feature"):
        analisis = analizar_geojson(cfg)
    else:
        raise HTTPException(400, "Formato no reconocido. Se admite configuración MapStore2 o GeoJSON estándar.")

    contexto = CONTEXTO_EVENTO.get(req.tipo_evento, CONTEXTO_EVENTO["general"])
    descripcion = req.descripcion.strip() or "El técnico no proporcionó descripción."

    # Resumen compacto para la IA (evita mandar el archivo completo)
    h = analisis["hallazgos"]
    resumen = json.dumps({
        **{k: v for k, v in analisis.items() if k != "hallazgos"},
        "hallazgos_conteo": {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in h.items()},
        "ejemplos_sin_creditos": (h.get("sin_creditos") or [])[:8],
        "ejemplos_grupos_vacios": (h.get("grupos_vacios") or [])[:8],
        "ejemplos_sin_descripcion": (h.get("sin_descripcion") or [])[:5],
    }, ensure_ascii=False, indent=2)

    prompt = PROMPT_QA_JSON.format(
        nombre=req.nombre_archivo,
        contexto=contexto,
        descripcion=descripcion,
        resumen=resumen
    )

    texto = await llamar_ia({
        "model": AI_MODEL,
        "max_tokens": 4000,
        "system": SISTEMA_QA + "\n\nEn este modo analizás configuraciones cartográficas digitales (no imágenes). Respondés SIEMPRE en JSON puro válido, sin backticks, sin texto adicional y SIN comas finales.",
        "messages": [{"role": "user", "content": prompt}]
    })

    try:
        resultado = parsear_respuesta(texto)
        resultado["_analisis_estructural"] = analisis
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Error JSON: {str(e)} | Texto: {texto[:300]}")


class ChatJSONRequest(BaseModel):
    resumen_estructural: str
    historial: List[ChatMessage] = []
    pregunta: str
    tipo_evento: str = "general"


@app.post("/qa-json-chat")
async def qa_json_chat(req: ChatJSONRequest):
    """Diálogo iterativo sobre una configuración cartográfica analizada."""
    contexto = CONTEXTO_EVENTO.get(req.tipo_evento, CONTEXTO_EVENTO["general"])

    mensajes = [
        {"role": "user", "content": f"Esta es la configuración cartográfica bajo revisión. Contexto del evento: {contexto}.\n\nANÁLISIS ESTRUCTURAL:\n{req.resumen_estructural}\n\nVoy a hacerte consultas sobre esta configuración."},
        {"role": "assistant", "content": "Recibí el análisis estructural de la configuración. Estoy listo para responder tus consultas sobre el control de calidad."}
    ]

    for m in req.historial:
        if m.role in ("user", "assistant") and m.content.strip():
            mensajes.append({"role": m.role, "content": m.content})

    mensajes.append({"role": "user", "content": req.pregunta})

    texto = await llamar_ia({
        "model": AI_MODEL,
        "max_tokens": 1200,
        "system": SISTEMA_QA + "\n\nEn este modo conversacional respondés en texto plano, claro y conciso. Sin JSON. Máximo 4-5 oraciones salvo que te pidan detalle.",
        "messages": mensajes
    })

    return {"respuesta": texto.strip()}


# ══════════════════ ENDPOINTS DE ESTADO ══════════════════

@app.get("/")
def root():
    return {
        "status": "ok",
        "app": "Vertech TdF API",
        "version": "4.2.0",
        "modulos": ["analisis-satelital", "qa-mapas-imagen", "qa-mapas-json"],
        "ai_mode": AI_MODE
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_key_configured": bool(AI_API_KEY),
        "ai_mode": AI_MODE,
        "ai_model": AI_MODEL
    }
