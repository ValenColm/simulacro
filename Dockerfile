# ── Imagen base ──────────────────────────────────────────────────────────────
# Usamos Python 3.12 slim (versión ligera sin herramientas de desarrollo)
# "slim" reduce el tamaño de la imagen final significativamente
FROM python:3.12-slim

# ── Directorio de trabajo dentro del contenedor ───────────────────────────────
# Todo lo que hagamos después ocurre dentro de /app
WORKDIR /app

# ── Instalar dependencias primero (capa cacheada) ─────────────────────────────
# Copiamos requirements.txt ANTES del código fuente.
# Docker cachea las capas: si el código cambia pero requirements.txt no,
# no reinstala las librerías (más rápido al rebuild)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copiar el código fuente del backend ───────────────────────────────────────
# Copiamos solo la carpeta backend al directorio de trabajo
COPY backend/ .

# ── Puerto que expone el contenedor ───────────────────────────────────────────
# EXPOSE es documentación: le dice a Docker qué puerto usa la app
# No abre el puerto por sí solo, eso lo hace el docker-compose con "ports:"
EXPOSE 8000

# ── Comando de arranque ───────────────────────────────────────────────────────
# uvicorn es el servidor ASGI que corre FastAPI
# --host 0.0.0.0 → acepta conexiones desde fuera del contenedor
# --port 8000    → el puerto donde escucha
# --reload solo para desarrollo, quitar en producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]