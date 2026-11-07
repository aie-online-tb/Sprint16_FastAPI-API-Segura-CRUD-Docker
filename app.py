"""
API CRUD dada + capa de seguridad: API key (?api_key=), rate limit y CORS.

Público: /, /docs, /health
Protegido (?api_key=): /items*

La protección no está “dentro” de cada función CRUD: se declara con
dependencies=[Depends(require_api_key)] → FastAPI ejecuta auth/rate limit primero.
"""

import logging
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

import config
from schemas import Item
from security import require_api_key

# Logs a consola (uvicorn). security.py / rate_limit.py usan el mismo sistema.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API segura — CRUD",
    description=(
        "CRUD de ítems con api_key por query, rate limit y CORS. "
        "En /docs: Try it out → parámetro api_key."
    ),
)

# CORS: el navegador bloquea llamadas cross-origin salvo que la API lo permita.
# allow_origins sale del .env (cambia en local / staging / prod).
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# “Base de datos” en memoria (se pierde al reiniciar). Varios ítems → practicar skip/limit.
items_db: List[Item] = [
    Item(id=1, name="Laptop", description="Portátil para desarrollo", price=1200.99, on_offer=True),
    Item(id=2, name="Smartphone", description="Teléfono de gama media", price=899.99, on_offer=False),
    Item(id=3, name="Auriculares", description="Cancelación de ruido", price=199.99, on_offer=True),
    Item(id=4, name="Teclado", description="Mecánico RGB", price=89.90, on_offer=True),
    Item(id=5, name="Ratón", description="Inalámbrico ergonómico", price=49.50, on_offer=False),
    Item(id=6, name="Monitor", description="27 pulgadas 144Hz", price=279.00, on_offer=True),
    Item(id=7, name="Webcam", description="Full HD", price=59.99, on_offer=False),
    Item(id=8, name="Dock USB-C", description="HDMI + Ethernet", price=119.00, on_offer=True),
]


def _find_index(item_id: int) -> int:
    """Posición en la lista, o -1 si no existe (helper del CRUD)."""
    for i, item in enumerate(items_db):
        if item.id == item_id:
            return i
    return -1


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    """Público: pulso del servicio (sin API key). Útil para monitors / load balancers."""
    return {"status": "ok"}


# --- CRUD protegido ----------------------------------------------------------
# Depends(require_api_key) en cada ruta: sin clave válida no se ejecuta el body.


@app.get("/items", response_model=List[Item], dependencies=[Depends(require_api_key)])
def list_items(
    skip: int = Query(0, ge=0),           # cuántos ítems saltar
    limit: int = Query(10, ge=1, le=100),  # tamaño del trozo
    on_offer: Optional[bool] = Query(None),
):
    """Listado con paginación tipo offset: data[skip : skip+limit]."""
    data = items_db
    if on_offer is not None:
        data = [item for item in data if item.on_offer == on_offer]
    logger.info("GET /items count=%s", min(len(data) - skip, limit))
    return data[skip : skip + limit]


@app.get("/items/{item_id}", response_model=Item, dependencies=[Depends(require_api_key)])
def get_item(item_id: int = Path(..., ge=1)):
    idx = _find_index(item_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return items_db[idx]


@app.post(
    "/items",
    response_model=Item,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_item(item: Item):
    # 409 = conflicto de negocio (el id ya existe); distinto de 401 (auth)
    if _find_index(item.id) >= 0:
        raise HTTPException(status_code=409, detail="Ya existe un ítem con ese id")
    items_db.append(item)
    return item


@app.put("/items/{item_id}", response_model=Item, dependencies=[Depends(require_api_key)])
def update_item(item: Item, item_id: int = Path(..., ge=1)):
    idx = _find_index(item_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    if item.id != item_id:
        raise HTTPException(
            status_code=400,
            detail="El id del body debe coincidir con el de la URL",
        )
    items_db[idx] = item
    return item


@app.delete("/items/{item_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_item(item_id: int = Path(..., ge=1)):
    idx = _find_index(item_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    del items_db[idx]
    return None
