"""Unit tests: no database, no model download, no network."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.ingest.extract import TOOL_NAME, extract_products
from app.ingest.loaders import read_csv
from app.ingest.service import validate_rows
from app.search.embeddings import product_embed_text

CSV = Path("data/catalogo_ferreteria.csv")


def test_read_csv_puts_unknown_columns_in_attributes() -> None:
    rows = read_csv(CSV)
    assert len(rows) == 42
    assert rows[0]["sku"] == "TRN-38-GALV"
    assert rows[0]["attributes"] == {"marca": "Fixa"}


def test_validate_rows_rejects_bad_price_and_duplicate_sku() -> None:
    rows = [
        {"sku": "a-1", "name": "Bueno", "price": "10.50"},
        {"sku": "A-1", "name": "Duplicado", "price": "5"},
        {"sku": "B-2", "name": "Sin precio"},
        {"sku": "C-3", "name": "Precio cero", "price": "0"},
    ]
    valid, rejected = validate_rows(rows)
    assert [p.sku for p in valid] == ["A-1"]  # sku is upper-cased
    assert len(rejected) == 3
    assert "duplicate" in rejected[0]
    assert "price" in rejected[1]
    assert "price" in rejected[2]


def test_product_embed_text_excludes_sku_and_price() -> None:
    text = product_embed_text("Tornillo 3/8", "Galvanizado", "Tornillería")
    assert text == "Tornillo 3/8. Tornillería. Galvanizado"


async def test_extract_products_validates_llm_output() -> None:
    fake_response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                name=TOOL_NAME,
                input={
                    "productos": [
                        {"sku": "x-1", "name": "Cable", "price": 10},
                        {"sku": "", "name": "Sin sku", "price": 10},
                        {"sku": "x-3", "name": "Negativo", "price": -1},
                    ]
                },
            )
        ]
    )
    client = SimpleNamespace(messages=SimpleNamespace(create=AsyncMock(return_value=fake_response)))

    valid, rejected = await extract_products("texto del catálogo", client=client)  # type: ignore[arg-type]

    assert [p.sku for p in valid] == ["X-1"]
    assert len(rejected) == 2
    call = client.messages.create.await_args.kwargs
    assert call["tool_choice"] == {"type": "tool", "name": TOOL_NAME}
    assert call["tools"][0]["input_schema"]["properties"]["productos"]["type"] == "array"
