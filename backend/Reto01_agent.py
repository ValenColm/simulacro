import os
import json                  
from openai import OpenAI
from dotenv import load_dotenv
from Reto02_tools import calculate_interest, get_usd_rate, get_bitcoin_price, tools_schema

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. Define aquí el system prompt
SYSTEM_PROMPT = """
Eres FinBot, el asistente virtual oficial de FinBot, una empresa fintech
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
"""

# 2. Este array es la memoria de la conversación
historial = []

# Mapa de nombre → función real. Lo usamos para ejecutar la tool correcta
# cuando OpenAI nos dice qué función quiere llamar (por su nombre string)
DISPATCH = {
    "calculate_interest": calculate_interest,
    "get_usd_rate":       get_usd_rate,
    "get_bitcoin_price":  get_bitcoin_price,
}

def chat(mensaje_usuario):
    # 'global' es necesario porque reasignamos historial (lista) dentro de la función
    global historial

    # 3. Agrega el mensaje del usuario al historial
    # formato: {"role": "user", "content": mensaje_usuario}
    historial.append({"role": "user", "content": mensaje_usuario})

    # 5. Llama a la API con:
    #    - el system prompt SIEMPRE primero
    #    - luego el historial
    #    - tools: el schema que describe las 3 funciones disponibles
    #    - tool_choice="auto": OpenAI decide si necesita llamar una tool o no
    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + historial,
        tools=tools_schema,      # ← le decimos a OpenAI que tiene 3 tools disponibles
        tool_choice="auto",      # ← "auto" = OpenAI decide cuándo usarlas
        temperature=0.3,
        max_tokens=500
    )

    # Extraemos el mensaje completo (puede ser texto O una solicitud de tool)
    mensaje = respuesta.choices[0].message

    # 6. ¿OpenAI quiere ejecutar una tool?
    # Si 'tool_calls' existe, el modelo NO generó texto todavía —
    # está pidiendo que nosotros ejecutemos una función y le devolvamos el resultado
    if mensaje.tool_calls:

        # Guardamos el mensaje del asistente con la solicitud de tool en el historial
        # Esto es obligatorio: OpenAI necesita ver su propio mensaje antes del tool result
        historial.append(mensaje)

        # Iteramos por cada tool que OpenAI quiere llamar
        # (puede pedir varias al mismo tiempo en llamadas paralelas)
        for tool_call in mensaje.tool_calls:

            # Nombre de la función que OpenAI quiere ejecutar (string)
            nombre_funcion = tool_call.function.name

            # Los argumentos llegan como un string JSON, los convertimos a dict
            # Ejemplo: '{"principal": 1000000, "rate": 8, "years": 5}'
            argumentos = json.loads(tool_call.function.arguments)

            # Buscamos la función real en DISPATCH y la ejecutamos con **argumentos
            # **argumentos desempaqueta el dict: funcion(principal=..., rate=..., years=...)
            funcion_real = DISPATCH[nombre_funcion]
            resultado = funcion_real(**argumentos)

            # Enviamos el resultado de vuelta al historial con role "tool"
            # OpenAI necesita este mensaje para generar la respuesta final
            historial.append({
                "role": "tool",
                "tool_call_id": tool_call.id,    # ID que empareja solicitud y resultado
                "name": nombre_funcion,           # Nombre de la función (requerido por algunos modelos)
                "content": json.dumps(resultado)  # El resultado como string JSON
            })

        # Segunda llamada: ahora OpenAI genera la respuesta en lenguaje natural
        # con el resultado real de la tool que acabamos de ejecutar
        respuesta_final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + historial,
            temperature=0.3,
            max_tokens=500
        )
        texto_respuesta = respuesta_final.choices[0].message.content

    else:
        # 6b. Respuesta normal sin tool — extraemos el texto directamente
        texto_respuesta = mensaje.content

    # 7. Agrega la respuesta final al historial
    historial.append({"role": "assistant", "content": texto_respuesta})
    MAX = 7 * 2
    if len(historial) > MAX:
        historial = historial[-MAX:]  # recorte inicial
        # Si el primer mensaje no es "user", avanzamos hasta encontrar uno
        # Esto descarta cualquier fragmento huérfano de tool al inicio
        while historial and historial[0]["role"] != "user":
            historial.pop(0)

    # 8. Retorna la respuesta
    return texto_respuesta

# 9. Loop simple para probar en terminal
if __name__ == "__main__":
    print("FinBot listo. Escribe 'salir' para terminar.\n")
    while True:
        mensaje = input("Tú: ").strip()  # .strip() elimina espacios en blanco

        # Si el usuario presiona Enter sin escribir nada, pedimos que ingrese algo
        if not mensaje:
            continue

        if mensaje.lower() in ["salir", "exit"]:
            print("Hasta luego / Goodbye!")
            break
        respuesta = chat(mensaje)
        print(f"FinBot: {respuesta}\n")

