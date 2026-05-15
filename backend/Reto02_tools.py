# RETO 2: Herramientas (Tools) para el agente FinBot
import requests

# =============================================================================
# Tool 1 — Calcula interés compuesto
# =============================================================================
def calculate_interest(principal: float, rate: float, years: int):
    monto_final = principal * (1 + rate / 100) ** years

    # Los intereses generados son la diferencia entre el monto final
    # y el capital original que pusimos al inicio
    intereses = monto_final - principal

    # round(valor, 2) → redondea a 2 decimales para mostrar pesos/dólares
    return {
        "principal": round(principal, 2),       # Capital inicial
        "tasa_anual": rate,                     # Tasa en porcentaje
        "años": years,                          # Años de inversión
        "monto_final": round(monto_final, 2),   # Total al final
        "intereses_generados": round(intereses, 2)  # Ganancia pura
    }

# =============================================================================
# Tool 2 — Tipo de cambio USD/COP
# =============================================================================
def get_usd_rate():
    try:
        # Construimos la URL del endpoint público de tasa de cambio.
        # 'latest/USD' → trae todas las tasas con el dólar como base
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=5)

        data = response.json()

        # Extraemos solo la tasa USD→COP del dict de todas las tasas.
        # data["rates"] es un dict como {"COP": 4150.5, "EUR": 0.92, ...}
        tasa_cop = data["rates"]["COP"]

        return {
            "moneda_base": "USD",
            "moneda_destino": "COP",
            "tasa": round(tasa_cop, 2),   # Pesos colombianos por 1 dólar
            "fuente": "open.er-api.com"
        }

    except Exception as e:
      # Si la API falla (sin internet, timeout, etc.), retornamos
        # un valor hardcodeado de referencia en lugar de romper el agente.
        # El agente puede seguir respondiendo aunque la API no esté disponible.
        return {
            "moneda_base": "USD",
            "moneda_destino": "COP",
            "tasa": 4150.0,  # Valor de referencia aproximado
            "fuente": "valor_referencia (API no disponible)",
            "error": str(e)
        }

# =============================================================================
# Tool 3 — Precio de Bitcoin en USD via CoinGecko
# =============================================================================
def get_bitcoin_price():
    try: 
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        # Hacemos la petición GET con timeout de seguridad
        response = requests.get(url, timeout=5)

        # La respuesta tiene esta estructura:
        # {"bitcoin": {"usd": 67000}}
        # Navegamos el dict con ["bitcoin"]["usd"] para extraer el número
        data = response.json()
        precio = data["bitcoin"]["usd"]

        return {
            "activo": "Bitcoin (BTC)",
            "precio_usd": precio,
            "fuente": "CoinGecko"
        }

    except Exception as e:
        # Si CoinGecko no responde, retornamos un error claro sin romper el flujo
        return {
            "activo": "Bitcoin (BTC)",
            "precio_usd": None,
            "fuente": "CoinGecko",
            "error": f"No se pudo obtener el precio: {str(e)}"
        }


# =============================================================================
# TOOLS SCHEMA — Le dice a OpenAI qué funciones existen y cómo usarlas
# =============================================================================
tools_schema = [
    # ── Tool 1: Interés compuesto ──────────────────────────────────────────
    {
        # "type": "function" → le dice a OpenAI que esto es una función Python
        # (en el futuro OpenAI podría soportar otros tipos como "retrieval")
        "type": "function",
        "function": {
            # "name" → debe coincidir EXACTAMENTE con el nombre de la función Python
            # OpenAI pone este string en tool_call.function.name para que sepas cuál llamar
            "name": "calculate_interest",

            # "description" → el agente LEE esto para decidir cuándo usar la tool.
            # Sé específico: menciona qué calcula, con qué fórmula y cuándo aplica.
            "description": (
                "Calcula el monto final e intereses generados usando la fórmula de "
                "interés compuesto: monto = principal * (1 + rate/100) ** years. "
                "Úsala cuando el usuario pregunte cuánto crecerá una inversión, "
                "cuánto rinde un ahorro, o quiera proyectar capital a futuro."
            ),

            # "parameters" → describe los argumentos que acepta la función
            # Sigue el estándar JSON Schema (type: object con properties)
            "parameters": {
                "type": "object",  # siempre "object" como contenedor de parámetros

                # "properties" → un dict donde cada clave es un parámetro de la función
                "properties": {
                    "principal": {
                        # "type" → tipo de dato JSON: "number", "string", "integer", "boolean"
                        "type": "number",
                        # "description" → explica el parámetro para que el modelo
                        # lo mapee correctamente desde el lenguaje natural del usuario
                        "description": "Capital inicial a invertir en pesos o dólares"
                    },
                    "rate": {
                        "type": "number",
                        "description": "Tasa de interés anual en porcentaje (ej: 8 para 8%)"
                    },
                    "years": {
                        "type": "integer",  # integer = número entero sin decimales
                        "description": "Número de años de la inversión"
                    }
                },

                # "required" → lista de parámetros que DEBEN estar presentes.
                # Si el usuario no los menciona, el modelo pedirá la información.
                "required": ["principal", "rate", "years"]
            }
        }
    },

    # ── Tool 2: Tipo de cambio USD/COP ────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_usd_rate",
            "description": (
                "Consulta el tipo de cambio actual del dólar americano (USD) a "
                "pesos colombianos (COP) usando una API en tiempo real. "
                "Úsala cuando el usuario pregunte por la tasa de cambio, el valor "
                "del dólar hoy, o quiera convertir USD a COP."
            ),
            # Sin parámetros: la función no recibe argumentos
            "parameters": {
                "type": "object",
                "properties": {},   # dict vacío → no hay parámetros
                "required": []      # lista vacía → nada es obligatorio
            }
        }
    },

    # ── Tool 3: Precio de Bitcoin ─────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_bitcoin_price",
            "description": (
                "Obtiene el precio actual de Bitcoin (BTC) en dólares americanos (USD) "
                "usando la API pública de CoinGecko. "
                "Úsala cuando el usuario pregunte por el precio del bitcoin, "
                "su valor actual, o quiera saber cómo está el mercado crypto hoy."
            ),
            # Sin parámetros
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# =============================================================================
# Prueba rápida en terminal (solo se ejecuta con: python Reto02-tools.py)
# =============================================================================
if __name__ == "__main__":
    print("=== Tool 1: Interés Compuesto ===")
    print(calculate_interest(principal=1_000_000, rate=8, years=5))

    print("\n=== Tool 2: Tipo de cambio USD/COP ===")
    print(get_usd_rate())

    print("\n=== Tool 3: Precio Bitcoin ===")
    print(get_bitcoin_price())

    print("\n=== tools_schema cargado ===")
    print(f"Total tools registradas: {len(tools_schema)}")
    for t in tools_schema:
        print(f"  • {t['function']['name']}")
