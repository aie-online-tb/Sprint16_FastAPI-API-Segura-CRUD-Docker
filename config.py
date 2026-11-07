"""
Valores de configuración leídos del entorno (.env / variables del sistema).

Regla: secretos y cosas que cambian por entorno → aquí, no hardcodeados en app.py.
En Docker / PaaS llegan con -e o el panel; no hace falta fichero .env dentro de la imagen.
"""

import os

from dotenv import load_dotenv

# Carga el fichero .env al arrancar (si existe). En contenedor suelen inyectar env vars
# sin fichero; load_dotenv no pisa variables ya definidas en el sistema.
load_dotenv()

# Secreto del servidor. El cliente debe enviar la misma en ?api_key=
# "or None" → string vacío "" también se trata como "no configurada"
API_KEY: str | None = os.getenv("API_KEY") or None

# Cupo bajo a propósito para que en la práctica se pueda forzar un 429 fácil
RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# Lista de orígenes (fronts) permitidos por CORS. En .env van separados por comas.
# El segundo argumento de getenv es el valor por defecto si no hay CORS_ORIGINS.
_cors_raw = os.getenv(
    "CORS_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:8501,http://localhost:3000",
)
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]
