"""Render data/catalogo_ferreteria.csv as a PDF price list, to demo the PDF ingestion path.

uv run python scripts/make_sample_pdf.py
"""

import csv
from pathlib import Path

import pymupdf

SRC = Path("data/catalogo_ferreteria.csv")
DST = Path("data/catalogo_ferreteria.pdf")

LINE_H = 14
TOP = 60
BOTTOM = 790


def main() -> None:
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    doc = pymupdf.open()
    page = doc.new_page()
    y = TOP
    page.insert_text((40, 36), "Ferretería Central - Lista de precios 2026", fontsize=14)
    page.insert_text((40, y), "SKU | Producto | Categoría | Unidad | Precio Bs | Stock", fontsize=9)
    y += LINE_H
    for r in rows:
        if y > BOTTOM:
            page = doc.new_page()
            y = TOP
        line = (
            f"{r['sku']} | {r['name']} | {r['category']} | {r['unit']} | "
            f"{r['price']} | {r['stock']}"
        )
        page.insert_text((40, y), line, fontsize=8)
        y += LINE_H
        page.insert_text((60, y), r["description"][:110], fontsize=7)
        y += LINE_H
    doc.save(DST)
    print(f"wrote {DST} ({len(rows)} products, {doc.page_count} pages)")


if __name__ == "__main__":
    main()
