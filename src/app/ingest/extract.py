"""Structured extraction of products from free text with Claude tool calling.

The model never returns prose here. It is forced to call one tool whose input_schema is the
JSON schema of our Pydantic model, so the output is validated before it touches the database.
"""

from typing import Any

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from app.config import get_settings
from app.ingest.schemas import ProductIn

TOOL_NAME = "registrar_productos"

_SYSTEM = (
    "Sos un asistente que convierte catálogos de productos en datos estructurados. "
    "Leé el texto y registrá cada producto con la tool. Reglas: un producto por fila de "
    "catálogo; el SKU es el código tal como aparece; el precio es un número sin símbolo de "
    "moneda; si un dato no aparece, omitilo, nunca lo inventes."
)


def _tool_schema() -> dict[str, Any]:
    item = ProductIn.model_json_schema()
    item.pop("title", None)
    return {
        "name": TOOL_NAME,
        "description": "Registra la lista completa de productos encontrados en el texto.",
        "input_schema": {
            "type": "object",
            "properties": {"productos": {"type": "array", "items": item}},
            "required": ["productos"],
        },
    }


async def extract_products(
    text: str, *, client: AsyncAnthropic | None = None
) -> tuple[list[ProductIn], list[str]]:
    """Return (valid products, rejection reasons). Never raises on bad rows."""
    settings = get_settings()
    client = client or AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=settings.llm_extract_model,
        max_tokens=8192,
        system=_SYSTEM,
        tools=[_tool_schema()],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": text}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    raw_items: list[dict[str, Any]] = tool_use.input.get("productos", [])

    valid: list[ProductIn] = []
    rejected: list[str] = []
    for i, item in enumerate(raw_items):
        try:
            valid.append(ProductIn.model_validate(item))
        except ValidationError as e:
            rejected.append(f"item {i} ({item.get('sku', '?')}): {e.errors()[0]['msg']}")
    return valid, rejected
