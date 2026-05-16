# Reto06-cache.py
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Umbral configurable — aquí se cambia, no en la lógica
UMBRAL_SIMILITUD = 0.85 # Bajar a 0.70 para más hits, subir a 0.98 para solo exactos

# El caché en memoria — lista de dicts
# cada entry: {"embedding": vector, "pregunta": texto, "respuesta": texto}
cache = []

# System prompt de FinBot (mismo de los otros retos)
SYSTEM_PROMPT = """Eres FinBot, el asistente virtual oficial de FinBot, una empresa fintech
que opera en Colombia y Estados Unidos.

Personalidad y tono:
- Mantén siempre un tono formal, profesional y empático propio del sector financiero.
- Sé confiable, preciso y claro. Nunca uses lenguaje coloquial o informal.

Detección automática de idioma:
- Detecta el idioma de cada mensaje y responde SIEMPRE en ese mismo idioma.
- Si el usuario escribe en español, responde completamente en español formal.
- If the user writes in English, respond entirely in formal English.

Temas permitidos (SOLO responde sobre estos):
1. Finanzas personales: presupuesto, ahorro, inversión, crédito, deudas, planificación.
2. Mercados e inversiones: tasas de cambio, criptomonedas (Bitcoin, etc.), acciones, rendimientos.
3. Productos y servicios de FinBot: cuentas, tarjetas, préstamos, transferencias.
4. Soporte técnico: problemas con la app, transacciones, seguridad de la cuenta.

Restricción de dominio:
- Si el usuario pregunta algo que NO sea finanzas, productos FinBot o soporte,
  declina amablemente en el idioma activo.
"""

# =============================================================================
# Función 1 — Genera embedding de un texto
# =============================================================================
def obtener_embedding(texto: str) -> list:
    # Llama a client.embeddings.create()
    # model="text-embedding-3-small"
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=texto
    )
    # Retorna el vector como lista
    return response.data[0].embedding

# =============================================================================
# Función 2 — Similitud coseno entre dos vectores
# =============================================================================
def similitud_coseno(a, b) -> float:
    # Dos líneas con numpy
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# =============================================================================
# Función 3 — Busca en el caché
# =============================================================================
def buscar_en_cache(pregunta: str):
    # 1. Genera embedding de la pregunta
    embedding_pregunta = obtener_embedding(pregunta)

    mejor_similitud = -1
    mejor_respuesta = None
    mejor_pregunta = None

    # 2. Compara con cada entry del caché
    for entry in cache:
        sim = similitud_coseno(embedding_pregunta, entry["embedding"])
        if sim > mejor_similitud:
            mejor_similitud = sim
            mejor_respuesta = entry["respuesta"]
            mejor_pregunta = entry["pregunta"]

    # Debug: muestra la mejor coincidencia encontrada
    print(f"   🔍 Mejor match: '{mejor_pregunta}' (similitud: {mejor_similitud:.4f}, umbral: {UMBRAL_SIMILITUD})")

    # 3. Si similitud > UMBRAL_SIMILITUD retorna la respuesta
    if mejor_similitud >= UMBRAL_SIMILITUD:
        return mejor_respuesta, mejor_similitud

    # 4. Si no hay hit retorna None
    return None, mejor_similitud

# =============================================================================
# Función 4 — Guarda en el caché
# =============================================================================
def guardar_en_cache(pregunta: str, respuesta: str):
    # 1. Genera embedding de la pregunta
    embedding = obtener_embedding(pregunta)
    # 2. Agrega al caché
    cache.append({
        "embedding": embedding,
        "pregunta": pregunta,
        "respuesta": respuesta
    })

# =============================================================================
# Función 5 — Llama al LLM cuando no hay hit en caché
# =============================================================================
def llamar_llm(pregunta: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta}
        ],
        max_tokens=512,
    )
    return response.choices[0].message.content

# =============================================================================
# Función 6 — Pipeline completo: caché → LLM
# =============================================================================
def responder_con_cache(pregunta: str) -> tuple:
    """Solo busca en caché. Retorna (respuesta|None, desde_cache: bool)
    
    IMPORTANTE: esta función NO llama al LLM. El agente real (con tools)
    vive en /chat. El frontend llama /cache primero; si hay miss, llama /chat
    y luego guarda la respuesta via /cache/guardar.
    """
    respuesta_cache, similitud = buscar_en_cache(pregunta)
    if respuesta_cache:
        return respuesta_cache, True
    # Miss — retorna None para que el frontend llame al agente real
    return None, False

# =============================================================================
# Pre-poblar con 5 preguntas frecuentes de FinBot
# =============================================================================
def poblar_cache():
    preguntas_respuestas = [
        ("¿Cuál es el horario de atención de FinBot?",
         "Nuestro horario de atención es de lunes a viernes de 7:00 a.m. a 7:00 p.m. (hora Colombia). "
         "Los sábados atendemos de 8:00 a.m. a 1:00 p.m. Domingos y festivos no hay servicio presencial, "
         "pero la app y el chat están disponibles 24/7."),

        ("¿Cómo recupero mi contraseña?",
         "Para recuperar su contraseña, ingrese a la app FinBot o al sitio web y seleccione 'Olvidé mi contraseña'. "
         "Se enviará un código de verificación a su correo o celular registrado. Si persiste el problema, "
         "contacte a soporte al 01-800-FINBOT."),

        ("¿Cuánto demora una transferencia?",
         "Las transferencias entre cuentas FinBot son inmediatas. Transferencias a otros bancos nacionales "
         "demoran entre 5 y 30 minutos en días hábiles. Transferencias internacionales pueden tomar de 1 a 3 "
         "días hábiles dependiendo del banco destino."),

        ("¿Cuáles son las tarifas de FinBot?",
         "FinBot no cobra cuota de manejo en cuentas de ahorro. Las transferencias nacionales tienen un costo "
         "de $0 entre cuentas FinBot y $3,500 COP a otros bancos. Retiros en cajero aliado: $0 los primeros 3 "
         "del mes, $2,800 COP los siguientes."),

        ("¿Cómo contacto a soporte?",
         "Puede contactar a soporte FinBot por los siguientes canales: Chat en la app (24/7), "
         "línea telefónica 01-800-FINBOT (lunes a sábado), correo soporte@finbot.co, "
         "o en nuestras redes sociales @FinBotCo en Twitter e Instagram."),
    ]
    for pregunta, respuesta in preguntas_respuestas:
        guardar_en_cache(pregunta, respuesta)

# =============================================================================
# Prueba interactiva
# =============================================================================
if __name__ == "__main__":
    print("Poblando caché semántico con 5 preguntas frecuentes...")
    poblar_cache()
    print(f"✅ Caché listo ({len(cache)} entradas). Umbral: {UMBRAL_SIMILITUD}\n")

    while True:
        pregunta = input("Tu pregunta (o 'salir'): ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue

        print("-" * 50)
        respuesta, desde_cache = responder_con_cache(pregunta)

        if desde_cache:
            print("🟢 [CACHÉ] Respuesta desde caché semántico:")
        else:
            print("🔵 [LLM] Respuesta generada por el modelo:")

        print(respuesta)
        print("-" * 50 + "\n")