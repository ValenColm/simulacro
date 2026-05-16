# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel
import tempfile
import os

# Importa las funciones de cada reto
from Reto01_agent import chat
from Reto03_voice import transcribir_audio, sintetizar_voz
from Reto04_rag import construir_base_vectorial, responder_rag
from Reto05_vision import analizar_imagen
from Reto06_cache import responder_con_cache, poblar_cache, cache

app = FastAPI()

# CORS — permite que el frontend llame al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Al arrancar: inicializa RAG y caché
# =============================================================================
vectorstore = None

@app.on_event("startup")
async def startup():
    global vectorstore
    # 1. Construye la base vectorial del RAG
    print("Construyendo base vectorial RAG...")
    vectorstore = construir_base_vectorial()
    print("✅ Base vectorial lista.")

    # 2. Pobla el caché semántico
    print("Poblando caché semántico...")
    poblar_cache()
    print(f"✅ Caché listo ({len(cache)} entradas).")

# =============================================================================
# Modelos de request
# =============================================================================
class MensajeRequest(BaseModel):
    mensaje: str

# =============================================================================
# Endpoints
# =============================================================================

# Reto 01 + 02 — chat con agente y tools
@app.post("/chat")
async def endpoint_chat(request: MensajeRequest):
    respuesta, tool_used, tools = chat(request.mensaje)
    return {"respuesta": respuesta, "tool_used": tool_used, "tools": tools}

# Reto 03 — transcribir audio
@app.post("/voice/transcribe")
async def endpoint_transcribir(audio: UploadFile = File(...)):
    # Guarda el audio en archivo temporal
    suffix = os.path.splitext(audio.filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contenido = await audio.read()
        tmp.write(contenido)
        tmp_path = tmp.name

    try:
        # Transcribe con Whisper
        texto = transcribir_audio(tmp_path)
        return {"texto": texto}
    finally:
        os.unlink(tmp_path)

# Reto 03 — sintetizar voz (TTS)
@app.post("/voice/synthesize")
async def endpoint_sintetizar(request: MensajeRequest):
    audio_bytes = sintetizar_voz(request.mensaje)
    return Response(content=audio_bytes, media_type="audio/mpeg")

# Reto 04 — RAG
@app.post("/rag")
async def endpoint_rag(request: MensajeRequest):
    # Llama a responder_rag() con el vectorstore global
    respuesta = responder_rag(request.mensaje, vectorstore)
    return {"respuesta": respuesta}

# Reto 05 — visión
@app.post("/vision")
async def endpoint_vision(
    mensaje: str = Form(""),
    imagen: UploadFile = File(None)
):
    ruta_tmp = None
    try:
        if imagen and imagen.filename:
            # Si hay imagen guárdala temporal y llama a analizar_imagen()
            suffix = os.path.splitext(imagen.filename)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                contenido = await imagen.read()
                tmp.write(contenido)
                ruta_tmp = tmp.name
            respuesta = analizar_imagen(mensaje or "Analiza esta imagen", ruta_tmp)
        else:
            # Si no hay imagen llama a analizar_imagen() solo con texto
            respuesta = analizar_imagen(mensaje)
        return {"respuesta": respuesta}
    except Exception as e:
        return {"respuesta": f"⚠️ Error interno: {str(e)}"}
    finally:
        if ruta_tmp and os.path.exists(ruta_tmp):
            os.unlink(ruta_tmp)

# Reto 06 — caché semántico: solo búsqueda
@app.post("/cache")
async def endpoint_cache(request: MensajeRequest):
    respuesta, desde_cache = responder_con_cache(request.mensaje)
    return {"respuesta": respuesta, "desde_cache": desde_cache}

# Guarda una respuesta en el caché (llamado por el frontend tras recibir respuesta del agente real)
class GuardarCacheRequest(BaseModel):
    pregunta: str
    respuesta: str

@app.post("/cache/guardar")
async def endpoint_guardar_cache(request: GuardarCacheRequest):
    guardar_en_cache(request.pregunta, request.respuesta)
    return {"ok": True, "total": len(cache)}

# Sirve el frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")