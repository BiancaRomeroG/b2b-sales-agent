"""Readers that turn a file into raw rows. Validation happens later, in ProductIn."""

import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, Any]]:
    """Expected header: sku,name,description,category,unit,price,stock. Extra columns go to
    attributes."""
    known = {"sku", "name", "description", "category", "unit", "price", "stock"}
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as f:
        for raw in csv.DictReader(f):
            row = {k: v for k, v in raw.items() if k in known and v not in (None, "")}
            extra = {k: v for k, v in raw.items() if k not in known and v not in (None, "")}
            if extra:
                row["attributes"] = extra
            rows.append(row)
    return rows


def read_pdf_markdown(path: Path) -> str:
    """PDF to Markdown with layout preserved (tables become pipe tables).
    Scanned PDFs without a text layer come back empty; that case is handled by the caller."""
    import pymupdf4llm  # heavy import, keep it lazy

    return pymupdf4llm.to_markdown(str(path))
