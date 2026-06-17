"""
Vertech TdF — Backend de análisis satelital
Conecta Copernicus/Sentinel con Claude Vision
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import base64
import os
from datetime import datetime, timedelta

app = FastAPI(title="Vertech TdF API", version="1.0.0")

# ── CORS — permite llamadas desde GitHub Pages ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Variables de entorno (se configuran en Render) ──
COPERNICUS_USER     = os.getenv("COPERNICUS_USER", "")
COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")

# ── Modelos ──
class AnalysisRequest(BaseModel):
    lat: float          # latitud centro
    lon: float          # longitud centro
    tipo: str           # campo | mar | metano
    fecha: str = ""     # YYYY-MM-DD (vacío = hoy)
    zoom: float = 0.5   # grados de margen

class AnalysisResponse(BaseModel):
    imagen_base64: str
    indices: list
    diagnostico: str
    misiones: list
    fuente: str
    fecha_imagen: str


# ── 1. Token de Copernicus ──
async def get_copernicus_token():
    url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    data = {
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": COPERNICUS_USER,
        "password": COPERNICUS_PASSWORD,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        if r.status_code != 200:
            raise HTTPException(502, f"Error Copernicus auth: {r.text}")
        return r.json()["access_token"]


# ── 2. Buscar imagen disponible en Copernicus ──
async def buscar_imagen(lat, lon, zoom, tipo, fecha, token):
    # Bounding box
    bbox = f"{lon-zoom},{lat-zoom},{lon+zoom},{lat+zoom}"

    # Colección según tipo
    if tipo == "metano":
        coleccion = "SENTINEL-5P"
        producto  = "L2__CH4___"
    elif tipo == "mar":
        coleccion = "SENTINEL-3"
        producto  = "OL_2_WFR___"
    else:
        coleccion = "SENTINEL-2"
        producto  = "S2MSI2A"

    # Fecha de búsqueda
    if fecha:
        fecha_fin   = fecha
        fecha_ini   = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
    else:
        fecha_fin   = datetime.utcnow().strftime("%Y-%m-%d")
        fecha_ini   = (datetime.utcnow() - timedelta(days=15)).strftime("%Y-%m-%d")

    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": (
            f"Collection/Name eq '{coleccion}' and "
            f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{producto}') and "
            f"ContentDate/Start gt {fecha_ini}T00:00:00.000Z and "
            f"ContentDate/Start lt {fecha_fin}T23:59:59.000Z and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({lon-zoom} {lat-zoom},{lon+zoom} {lat-zoom},{lon+zoom} {lat+zoom},{lon-zoom} {lat+zoom},{lon-zoom} {lat-zoom}))')"
        ),
        "$orderby": "ContentDate/Start desc",
        "$top": "1",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(502, f"Error búsqueda Copernicus: {r.text}")
        data = r.json()

    if not data.get("value"):
        raise HTTPException(404, "No se encontraron imágenes para esa zona y fecha. Probá con otra fecha o ampliá el zoom.")

    producto_id   = data["value"][0]["Id"]
    nombre        = data["value"][0]["Name"]
    fecha_imagen  = data["value"][0]["ContentDate"]["Start"][:10]
    return producto_id, nombre, fecha_imagen


# ── 3. Descargar preview de la imagen ──
async def descargar_preview(producto_id, token):
    url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({producto_id})/Nodes/QUICKLOOK.JPG/$value"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode()

    # Fallback: thumbnail del catálogo
    url2 = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({producto_id})/Nodes/thumbnail/$value"
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(url2, headers=headers)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode()

    raise HTTPException(502, "No se pudo descargar la imagen preview.")


# ── 4. Analizar con Claude Vision ──
async def analizar_con_ia(imagen_b64, tipo, lat, lon):
    prompts = {
        "campo": f"""Analizás una imagen satelital Sentinel-2 de un campo en coordenadas {lat:.2f}°, {lon:.2f}°.
Respondé SOLO en JSON puro sin backticks:
{{"indices":[{{"label":"NDVI promedio","value":"0.XX","sub":"estado vegetal"}},{{"label":"Humedad suelo","value":"XX%","sub":"condición hídrica"}},{{"label":"Cobertura vegetal","value":"XX%","sub":"densidad"}},{{"label":"Zonas críticas","value":"X","sub":"requieren acción"}}],
"diagnostico":"5-6 oraciones técnicas sobre estado del campo, zonas de estrés, cobertura vegetal y recomendaciones agronómicas.",
"misiones":[{{"tarea":"descripción concisa","prioridad":"alta","zona":"zona específica"}},{{"tarea":"descripción","prioridad":"media","zona":"zona"}},{{"tarea":"descripción","prioridad":"baja","zona":"zona"}}]}}""",

        "mar": f"""Analizás una imagen satelital Sentinel-3 del mar en coordenadas {lat:.2f}°, {lon:.2f}°.
Respondé SOLO en JSON puro sin backticks:
{{"indices":[{{"label":"Temperatura sup.","value":"X.X°C","sub":"vs media"}},{{"label":"Clorofila-a","value":"X.X mg/m³","sub":"productividad"}},{{"label":"Turbidez","value":"XX NTU","sub":"claridad del agua"}},{{"label":"Alertas","value":"X","sub":"zonas de riesgo"}}],
"diagnostico":"5-6 oraciones sobre estado oceanográfico, productividad marina, corrientes y condiciones para actividad pesquera.",
"misiones":[{{"tarea":"acción de monitoreo","prioridad":"alta","zona":"sector"}},{{"tarea":"descripción","prioridad":"media","zona":"sector"}},{{"tarea":"descripción","prioridad":"baja","zona":"sector"}}]}}""",

        "metano": f"""Analizás una imagen satelital Sentinel-5P de concentración CH₄ en coordenadas {lat:.2f}°, {lon:.2f}°.
Respondé SOLO en JSON puro sin backticks:
{{"indices":[{{"label":"CH₄ promedio","value":"XXXX ppb","sub":"zona general"}},{{"label":"Pico detectado","value":"XXXX ppb","sub":"zona crítica"}},{{"label":"Anomalías","value":"X zonas","sub":"sobre umbral"}},{{"label":"Variación","value":"+X%","sub":"tendencia"}}],
"diagnostico":"5-6 oraciones sobre nivel de riesgo, fuentes probables de emisión, tendencia temporal y recomendaciones urgentes.",
"misiones":[{{"tarea":"acción urgente","prioridad":"alta","zona":"zona"}},{{"tarea":"descripción","prioridad":"media","zona":"zona"}},{{"tarea":"descripción","prioridad":"baja","zona":"zona"}}]}}""",
    }

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": "Sos el sistema de análisis satelital Vertech TdF. Analizás imágenes satelitales reales y respondés SIEMPRE en JSON puro sin texto adicional ni backticks.",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": imagen_b64}},
                {"type": "text", "text": prompts.get(tipo, prompts["campo"])}
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
        )
        if r.status_code != 200:
            raise HTTPException(502, f"Error Claude API: {r.text}")

    texto = r.json()["content"][0]["text"]
    import json
    try:
        return json.loads(texto.replace("```json", "").replace("```", "").strip())
    except Exception:
        raise HTTPException(502, "Error al parsear respuesta de IA.")


# ── ENDPOINT PRINCIPAL ──
@app.post("/analizar", response_model=AnalysisResponse)
async def analizar(req: AnalysisRequest):
    # 1. Auth Copernicus
    token = await get_copernicus_token()

    # 2. Buscar imagen
    producto_id, nombre, fecha_imagen = await buscar_imagen(
        req.lat, req.lon, req.zoom, req.tipo, req.fecha, token
    )

    # 3. Descargar preview
    imagen_b64 = await descargar_preview(producto_id, token)

    # 4. Analizar con IA
    resultado = await analizar_con_ia(imagen_b64, req.tipo, req.lat, req.lon)

    fuentes = {
        "campo":  "Sentinel-2 MSI · ESA Copernicus",
        "mar":    "Sentinel-3 OLCI · ESA Copernicus",
        "metano": "Sentinel-5P TROPOMI · ESA Copernicus",
    }

    return AnalysisResponse(
        imagen_base64=imagen_b64,
        indices=resultado.get("indices", []),
        diagnostico=resultado.get("diagnostico", ""),
        misiones=resultado.get("misiones", []),
        fuente=fuentes.get(req.tipo, "ESA Copernicus"),
        fecha_imagen=fecha_imagen,
    )


# ── Health check ──
@app.get("/")
def root():
    return {"status": "ok", "app": "Vertech TdF API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
