import os
from openai import OpenAI
from dotenv import load_dotenv

# load_dotenv() carga el .env con OPENAI_API_KEY y ELEVENLABS_API_KEY
load_dotenv()

# Cliente de OpenAI — el mismo que en agent.py, lo usamos para Whisper (STT)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =============================================================================
# Función 1 — Transcribir audio a texto con Whisper
# =============================================================================

def transcribir_audio(ruta_archivo: str) -> str:
    # 1. Abre el archivo de audio en modo lectura binaria ("rb")
    # "rb" = read binary: los archivos de audio son binarios, no texto
    with open(ruta_archivo, "rb") as archivo_audio:

        # 2. Llama a client.audio.transcriptions.create()
        # Es el mismo cliente OpenAI que usamos en agent.py
        # pero por la rama audio → transcriptions en vez de chat → completions
        resultado = client.audio.transcriptions.create(
            model="whisper-1",       # modelo de transcripción de OpenAI
            file=archivo_audio,      # el archivo abierto en binario         
        )

    # 3. Retorna el texto transcrito
    # resultado.text contiene el string con todo lo que dijo el audio
    return resultado.text


# =============================================================================
# Función 2 — Sintetizar texto a audio con ElevenLabs
# =============================================================================
# Recibe: texto string
# Retorna: bytes del audio generado (listos para guardar como .mp3)

def sintetizar_voz(texto: str) -> bytes:
    # 1. Importamos ElevenLabs y creamos el cliente con su API key
    # Lo importamos aquí (no arriba) para no romper el archivo si ElevenLabs
    # no está instalado y alguien solo quiere usar transcribir_audio()
    from elevenlabs import ElevenLabs

    # Creamos el cliente con la API key de ElevenLabs del .env
    cliente_eleven = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    # 2. Llama a text_to_speech.convert()
    generador_audio = cliente_eleven.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George — Warm, Captivating Storyteller (lo más cercano a Morgan Freeman)
        model_id="eleven_multilingual_v2",  # soporta español nativo
        text=texto
    )

    # 3. El resultado es un GENERADOR (produce chunks de bytes uno a uno)
    # b"".join(...) concatena todos los chunks en un solo objeto bytes
    # Equivale a "pegar" todos los pedacitos del audio en un solo bloque
    audio_bytes = b"".join(generador_audio)

    # 4. Retorna los bytes completos del audio
    return audio_bytes


# =============================================================================
# Prueba en terminal
# =============================================================================
if __name__ == "__main__":
    import sys

    # ── Prueba síntesis (TTS) ─────────────────────────────────────────────
    print("Generando audio con ElevenLabs...")
    texto_prueba = "Hola, soy FinBot, su asistente financiero virtual. ¿En qué puedo ayudarle hoy?"
    audio = sintetizar_voz(texto_prueba)

    # Guardamos el audio en un archivo .mp3 para escucharlo
    # "wb" = write binary: escribimos bytes, no texto
    with open("output.mp3", "wb") as f:
        f.write(audio)
    print("✅ Audio guardado en output.mp3")

    # ── Prueba transcripción (STT) ────────────────────────────────────────
    # Usamos el output.mp3 que acabamos de generar como audio de prueba
    print("\nTranscribiendo output.mp3 con Whisper...")
    texto_transcrito = transcribir_audio("output.mp3")
    print(f"✅ Transcripción: {texto_transcrito}")
