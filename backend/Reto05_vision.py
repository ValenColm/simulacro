# Reto05-vision.py
import os
import base64
import mimetypes
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """Eres FinBot, el asistente virtual oficial de FinBot, una empresa fintech
que opera en Colombia y Estados Unidos.

Personalidad y tono:
- Mantén siempre un tono formal, profesional y empático propio del sector financiero.
- Sé confiable, preciso y claro. Nunca uses lenguaje coloquial o informal.

Detección automática de idioma:
- Detecta el idioma de cada mensaje y responde SIEMPRE en ese mismo idioma.
- Si el usuario escribe en español, responde completamente en español formal.
- If the user writes in English, respond entirely in formal English.
- If the user mixes Spanish and English in the same message (Spanglish),
  respond in the language that appears most in that message.

Temas permitidos (SOLO responde sobre estos):
1. Finanzas personales: presupuesto, ahorro, inversión, crédito, deudas, planificación.
2. Mercados e inversiones: tasas de cambio, criptomonedas (Bitcoin, etc.), acciones, rendimientos.
3. Productos y servicios de FinBot: cuentas, tarjetas, préstamos, transferencias.
4. Soporte técnico: problemas con la app, transacciones, seguridad de la cuenta.

Restricción de dominio:
- Si el usuario pregunta algo que NO sea finanzas, productos FinBot o soporte,
  declina amablemente en el idioma activo.
- Rechazo en español: "Lo siento, solo puedo ayudarte con temas financieros,
  productos FinBot o soporte técnico."
- Rejection in English: "I am sorry, I can only assist with financial topics."

Además, puedes analizar imágenes financieras: extractos bancarios, errores en apps de pago, comprobantes.
"""

# =============================================================================
# Función 1 — Convierte imagen a base64
# =============================================================================
def imagen_a_base64(ruta_imagen: str) -> str:
    # 1. Abre el archivo en modo binario
    with open(ruta_imagen, "rb") as f:
        # 2. Lee los bytes y conviértelos a base64
        bytes_imagen = f.read()
    # 3. Retorna el string base64
    return base64.b64encode(bytes_imagen).decode("utf-8")

# =============================================================================
# Función 2 — Analiza imagen + texto con GPT-4o
# =============================================================================
def analizar_imagen(mensaje_texto: str, ruta_imagen: str = None) -> str:
    # Si hay imagen, modo visión (multimodal)
    if ruta_imagen:
        # 1. Convierte la imagen a base64
        imagen_b64 = imagen_a_base64(ruta_imagen)

        # 2. Construye el mensaje con dos partes en content
        media_type = mimetypes.guess_type(ruta_imagen)[0] or "image/jpeg"
        user_content = [
            {"type": "text", "text": mensaje_texto},
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{imagen_b64}"}},
        ]
    else:
        # Sin imagen: solo texto (modo normal)
        user_content = mensaje_texto

    # 3. Llama al modelo
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        max_tokens=1024,
    )

    # 4. Retorna el texto de respuesta
    return response.choices[0].message.content

# =============================================================================
# Prueba
# =============================================================================
if __name__ == "__main__":
    import sys

    # Acepta ruta de imagen como argumento (opcional)
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        ruta = input("Ruta de la imagen (Enter para solo texto): ").strip()

    if ruta:
        print(f"\n📷 Imagen cargada: {ruta}")
    else:
        ruta = None
        print("\n💬 Modo solo texto (sin imagen)")

    print("-" * 50)

    while True:
        pregunta = input("Tu pregunta (o 'salir'): ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        respuesta = analizar_imagen(pregunta, ruta)
        print("-" * 50)
        print(respuesta)
        print("-" * 50 + "\n")