"""
Contrato Item (API de negocio dada).

Pydantic valida el body: si price <= 0 o name vacío → FastAPI responde 422
sin que escribas un if manual en la ruta.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Item(BaseModel):
    """Un producto/ítem de la API de ejemplo (CRUD en memoria)."""

    id: int = Field(..., ge=1, description="Identificador único (>= 1)")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: float = Field(..., gt=0, description="Precio debe ser > 0")
    on_offer: bool = False
