from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importamos la función chat y el historial desde Reto01
# Así reutilizamos toda la lógica ya construida sin duplicar código
from Reto01_agent import chat, historial

# Creamos la aplicación FastAPI
# FastAPI genera automáticamente documentación en /docs (Swagger UI)
app = FastAPI(
    title="FinBot API",
    description="Agente conversacional bilingüe de finanzas personales",
    version="1.0.0"
)

# CORS: permite que el frontend (HTML/JS) se comunique con este backend
# origins=["*"] acepta peticiones desde cualquier origen (útil en desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo Pydantic: define y valida el cuerpo del request JSON
# FastAPI lo usa para parsear automáticamente el JSON que llega
class MensajeRequest(BaseModel):
    mensaje: str  # El texto que envía el usuario

class MensajeResponse(BaseModel):
    respuesta: str  # La respuesta del agente

# Endpoint raíz — útil para verificar que el servidor está vivo
@app.get("/")
def root():
    return {"status": "ok", "agente": "FinBot"}

# Endpoint principal del chat
# POST /chat recibe un JSON {"mensaje": "..."} y retorna {"respuesta": "..."}
@app.post("/chat", response_model=MensajeResponse)
def chat_endpoint(body: MensajeRequest):
    # Llama a la función chat del Reto01 con el mensaje del usuario
    respuesta = chat(body.mensaje)
    return MensajeResponse(respuesta=respuesta)

# Endpoint para limpiar el historial de la sesión actual
@app.delete("/historial")
def limpiar_historial():
    historial.clear()
    return {"status": "historial limpiado"}
