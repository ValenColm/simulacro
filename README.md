# FinBot — Agente Conversacional de IA para Fintech

Proyecto de automatización con IA construido durante el simulacro de evaluación. Implementa un agente conversacional bilingüe con herramientas de datos en tiempo real, síntesis y transcripción de voz, y una API HTTP lista para producción.

---

## 🗂️ Estructura del Proyecto

```
simulacro/
├── backend/
│   ├── Reto01_agent.py     # Agente bilingüe FinBot con memoria y tools
│   ├── Reto02_tools.py     # Herramientas: interés compuesto, USD/COP, Bitcoin
│   ├── Reto03-voice.py     # STT (Whisper) + TTS (ElevenLabs)
│   ├── Reto04-rag.py       # RAG — búsqueda semántica en documentos
│   ├── Reto05-vision.py    # Análisis de imágenes con GPT-4o Vision
│   ├── Reto06-cache.py     # Caché de respuestas
│   └── main.py             # API FastAPI — expone el agente como endpoint HTTP
├── frontend/
│   ├── index.html          # Interfaz de usuario
│   └── styles.css          # Estilos
├── Dockerfile              # Imagen Docker del backend
├── docker-compose.yml      # Orquesta backend + frontend nginx
├── requirements.txt        # Dependencias Python
├── .env.example            # Plantilla de variables de entorno (sin valores reales)
└── README.md
```

---

## ⚙️ Requisitos

- Python 3.12+
- Docker y Docker Compose
- Claves de API:
  - [OpenAI](https://platform.openai.com/api-keys) — para GPT-4o-mini y Whisper
  - [ElevenLabs](https://elevenlabs.io/) — para síntesis de voz (TTS)

---

## 🚀 Cómo levantarlo

### Opción 1 — Docker (recomendado)

```bash
# 1. Clona el repositorio
git clone https://github.com/TU_USUARIO/simulacro.git
cd simulacro

# 2. Crea tu archivo .env con las claves reales
cp .env.example .env
# Edita .env y pega tus API keys

# 3. Levanta los servicios
docker compose up --build
```

Servicios disponibles:
- **Backend API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

### Opción 2 — Local (sin Docker)

```bash
# 1. Crea y activa el entorno virtual
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Configura las variables de entorno
cp .env.example .env
# Edita .env con tus API keys

# 4. Levanta el servidor
uvicorn backend.main:app --reload --port 8000
```

---

## 🔑 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (nunca lo subas a GitHub):

```env
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
```

---

## 📡 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat` | Envía un mensaje al agente FinBot |
| DELETE | `/historial` | Limpia la memoria de la sesión |

### Ejemplo de uso

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿Cuánto vale el bitcoin hoy?"}'
```

```json
{
  "respuesta": "El precio del Bitcoin (BTC) hoy es de 79,230 USD, según CoinGecko..."
}
```

---

## 🧩 Retos implementados

### ✅ Reto 1 — Agente Bilingüe (`Reto01_agent.py`)
- Agente conversacional **FinBot** para la fintech del mismo nombre
- **Detección automática de idioma**: responde siempre en el idioma del usuario (ES/EN/Spanglish)
- **Memoria de sesión**: mantiene los últimos 7 turnos de conversación
- **Restricción de dominio**: solo responde sobre finanzas personales, mercados e inversiones, productos FinBot y soporte técnico
- **Recorte seguro del historial**: nunca parte secuencias `tool_call → tool_result` a la mitad

### ✅ Reto 2 — Tools (`Reto02_tools.py`)
Herramientas que el agente puede llamar automáticamente según el contexto:

| Función | Qué hace |
|---------|---------|
| `calculate_interest(principal, rate, years)` | Calcula interés compuesto con la fórmula `P*(1+r)^t` |
| `get_usd_rate()` | Tasa de cambio USD/COP en tiempo real (API open.er-api.com) |
| `get_bitcoin_price()` | Precio actual de BTC en USD (API CoinGecko, sin key) |

El agente usa `tools_schema` (JSON Schema estándar de OpenAI) para que el modelo decida cuándo llamar cada función. Cuando OpenAI pide una tool, el agente la ejecuta y hace una segunda llamada para generar la respuesta final en lenguaje natural.

### ✅ Reto 3 — Voz (`Reto03-voice.py`)
Pipeline completo de procesamiento de voz:

```
Audio (.mp3/.wav) → Whisper STT → texto → GPT → texto → ElevenLabs TTS → Audio
```

- **STT**: `client.audio.transcriptions.create(model="whisper-1")` — OpenAI Whisper
- **TTS**: `cliente_eleven.text_to_speech.convert(voice_id="JBFqnCBsd6RMkjVDRZzb")` — ElevenLabs (voz George)
- El resultado TTS es un generador de chunks: se concatena con `b"".join(generador)`

---

## 🐳 Docker

### `Dockerfile`
- Base: `python:3.12-slim` (imagen ligera)
- Copia `requirements.txt` primero para aprovechar el cache de capas Docker
- Servidor: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### `docker-compose.yml`
- **backend**: FastAPI en puerto 8000, variables desde `.env`, hot-reload via volumen
- **frontend**: nginx:alpine sirviendo archivos estáticos en puerto 3000

---

## 🛠️ Pruebas rápidas

### Agente en terminal (CLI)
```bash
.venv/bin/python backend/Reto01_agent.py
```

Casos de prueba sugeridos:
- `¿Cómo puedo ahorrar más?` → respuesta en español
- `How can I reduce my debt?` → respuesta en inglés
- `¿Cuánto vale el bitcoin hoy?` → activa tool `get_bitcoin_price()`
- `Si invierto 5M al 10% por 3 años, ¿cuánto tendré?` → activa `calculate_interest()`
- `¿Quién ganó el mundial?` → rechazo de dominio

### Tools
```bash
.venv/bin/python backend/Reto02_tools.py
```

### Voz
```bash
.venv/bin/python backend/Reto03-voice.py
# Genera output.mp3 y lo transcribe de vuelta con Whisper
```

---

## 📦 Tecnologías

| Tecnología | Uso |
|------------|-----|
| Python 3.12 | Lenguaje principal |
| OpenAI GPT-4o-mini | LLM del agente |
| OpenAI Whisper | Speech-to-Text |
| ElevenLabs | Text-to-Speech |
| FastAPI | API HTTP |
| Uvicorn | Servidor ASGI |
| Docker + Compose | Contenerización |
| nginx | Servidor frontend estático |
| requests | Llamadas a APIs externas (CoinGecko, exchangerate) |

---

## 🔒 Seguridad

- Las API keys **nunca** están en el código — siempre en `.env`
- `.env` está en `.gitignore` — nunca se sube a GitHub
- Usa `.env.example` como plantilla para nuevos entornos
