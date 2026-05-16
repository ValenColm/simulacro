# FinBot — Simulacro de Automatización con IA

Asistente financiero multimodal construido con FastAPI + OpenAI. Implementa los 8 retos del simulacro RIWI de Automatización con IA (2026).

---

## Arquitectura

```
simulacro/
├── backend/
│   ├── main.py              # FastAPI — punto de entrada y endpoints
│   ├── Reto01_agent.py      # Agente bilingüe con memoria (Reto 01)
│   ├── Reto02_tools.py      # 3 Tools: interés compuesto, dólar, Bitcoin (Reto 02)
│   ├── Reto03_voice.py      # Pipeline de voz: Whisper STT + ElevenLabs TTS (Reto 03)
│   ├── Reto04_rag.py        # RAG sobre web de Bancolombia con FAISS (Reto 04)
│   ├── Reto05_vision.py     # Análisis de imágenes con GPT-4o Vision (Reto 05)
│   └── Reto06_cache.py      # Caché semántico con embeddings + similitud coseno (Reto 06)
├── frontend/
│   ├── index.html           # Estructura HTML del chat (Reto 07)
│   ├── styles.css           # Estilos — diseño dark fintech premium
│   └── app.js               # Lógica JS: routing, badges, audio, imagen
├── .env                     # Variables de entorno (no se sube al repo)
└── requirements.txt         # Dependencias Python
```

---

## Retos implementados

| # | Reto | Tecnologías | Badge en UI |
|---|------|-------------|-------------|
| 01 | Agente bilingüe con personalidad definida | GPT-4o-mini, system prompt, memoria de 7 mensajes | — |
| 02 | 3 Tools: interés compuesto, USD/COP, Bitcoin | Tool calling, CoinGecko API | ⚡ Tool |
| 03 | Pipeline de voz: STT + TTS | Whisper API, ElevenLabs TTS | — |
| 04 | RAG sobre web real (Bancolombia créditos) | WebBaseLoader, FAISS, RecursiveCharacterTextSplitter | 🔍 RAG |
| 05 | Visión: análisis de imágenes | GPT-4o Vision, base64, mimetypes dinámico | — |
| 06 | Caché semántico | text-embedding-ada-002, similitud coseno, numpy | ■ Caché |
| 07 | App web con indicadores visuales | HTML/CSS/JS vanilla, badges permanentes en historial | Todos |
| 08 | Reto integrador end-to-end | Secuencia completa de 8 pasos del PDF | — |

---

## Requisitos previos

- Python 3.10+
- Cuenta OpenAI con créditos (GPT-4o-mini, GPT-4o, Whisper, embeddings)
- Cuenta ElevenLabs (opcional — solo para síntesis de voz)

---

## Instalación

```powershell
# 1. Clonar o descomprimir el proyecto
cd simulacro

# 2. Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env   # o editar .env directamente
```

### `.env`

```env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...   # opcional
```

---

## Ejecutar

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

Abrir en el navegador: **http://127.0.0.1:8000**

La documentación interactiva de la API está en: **http://127.0.0.1:8000/docs**

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/chat` | Agente principal con tools. Retorna `respuesta`, `tool_used`, `tools[]` |
| `POST` | `/voice/transcribe` | Transcripción de audio con Whisper (multipart/form-data) |
| `POST` | `/voice/synthesize` | Síntesis de voz con ElevenLabs (retorna audio/mpeg) |
| `POST` | `/rag` | Consulta RAG sobre web indexada (Bancolombia créditos) |
| `POST` | `/vision` | Análisis de imagen con GPT-4o Vision (multipart/form-data) |
| `POST` | `/cache` | Búsqueda en caché semántico. Retorna `respuesta`, `desde_cache` |
| `POST` | `/cache/guardar` | Guarda pregunta+respuesta en el caché |

### Ejemplo — Probar el caché

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cache" -Method POST `
  -ContentType "application/json" `
  -Body '{"mensaje": "cual es el horario de atencion"}'
```

### Ejemplo — Preguntar al agente

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"mensaje": "a cuanto esta el dolar hoy"}'
```

---

## Flujo de prioridad del frontend

```
Pregunta del usuario
    │
    ├─ ¿Contiene keywords RAG? ──► /rag ──────────────────► 🔍 RAG
    │
    └─ ¿No es RAG?
           │
           ├─ ¿Hit en caché semántico? ──► respuesta caché ► ■ Caché
           │
           └─ ¿No hay hit?
                  │
                  └─ /chat (agente + tools) ──────────────► ⚡ Tool  o sin badge
                         │
                         └─ Guarda en caché para la próxima vez
```

---

## Secuencia de prueba — Reto 08

Ejecutar estos 8 pasos en la UI para validar el sistema completo:

| # | Acción | Módulo activo | Resultado esperado |
|---|--------|---------------|--------------------|
| 1 | `Hola, soy Daniela, analista financiera` | Reto 01 Memoria | Saluda y recuerda el nombre |
| 2 | `What is the current USD to COP rate?` | Reto 02 Tool | Badge ⚡ get_usd_rate, responde en inglés |
| 3 | `¿Cuál es el horario de atención?` | Reto 06 Caché | Badge ■ Caché, respuesta inmediata |
| 4 | Imagen de extracto + `¿cuánto gasté en restaurantes?` | Reto 05 Visión | Analiza imagen y responde |
| 5 | Modo Voz → graba `¿Cómo está el Bitcoin hoy?` | Reto 03 + 02 | Transcripción visible, badge ⚡ get_bitcoin_price |
| 6 | `Según la web de FinBot, ¿qué créditos ofrecen?` | Reto 04 RAG | Badge 🔍 RAG, info de Bancolombia |
| 7 | Modo Audio → `Summarize what we discussed today` | Reto 01 + 03 | Respuesta en inglés reproducida como audio |
| 8 | `¿Recuerdas cómo me llamo?` | Reto 01 Memoria | Responde "Daniela" |

---

## Decisiones técnicas

- **`text-embedding-ada-002`** en lugar de `text-embedding-3-small`: el modelo más nuevo generaba scores de similitud consistentemente bajos (~0.53) con el umbral recomendado de 0.90, haciendo el caché ineficaz.
- **Caché solo busca, nunca genera**: `responder_con_cache()` devuelve `None` en caso de miss; el frontend llama al agente real (con tools) y luego persiste la respuesta correcta en caché via `/cache/guardar`. Esto evita que el caché almacene respuestas del LLM sin tools.
- **Prioridad RAG > Caché > Chat**: las preguntas sobre la web de FinBot/Bancolombia saltan el caché para evitar falsos hits con el FAQ pre-poblado.
- **Umbral de similitud = 0.85**: configurable en `UMBRAL_SIMILITUD` en `Reto06_cache.py`. Bajar a 0.70 para más hits, subir a 0.98 para solo coincidencias exactas.
- **Detección de MIME type dinámica** en Reto 05: se usa `mimetypes.guess_type()` en lugar de hardcodear `image/jpeg`, soportando `.png`, `.webp` y otros formatos.
