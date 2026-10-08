from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProductIn(BaseModel):
    """One catalog row as it enters the system, from CSV or from an LLM reading a PDF.

    Validation is strict on purpose: an LLM can hallucinate prices and SKUs, and a CSV
    exported by a human can carry blanks. Nothing invalid reaches the database.
    """

    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    unit: str = Field(default="unidad", max_length=32)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sku", "name", "category", "unit", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return v.strip() if isinstance(v, str) else v

    @field_validator("sku")
    @classmethod
    def _upper_sku(cls, v: str) -> str:
        return v.upper()


class IngestReport(BaseModel):
    tenant: str
    received: int
    inserted_or_updated: int
    rejected: list[str] = Field(default_factory=list)
