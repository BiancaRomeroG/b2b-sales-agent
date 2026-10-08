"""Integration: real Postgres with pgvector, real local embedding model."""

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.loaders import read_csv
from app.ingest.service import upsert_products, validate_rows
from app.models import EMBEDDING_DIM, Product, Tenant

pytestmark = pytest.mark.integration


async def test_ingest_csv_is_idempotent_and_embeds(session: AsyncSession, tenant: Tenant) -> None:
    valid, rejected = validate_rows(read_csv(Path("data/catalogo_ferreteria.csv")))
    assert rejected == []

    first = await upsert_products(session, tenant, valid, rejected)
    second = await upsert_products(session, tenant, valid, rejected)  # same file again
    assert first.inserted_or_updated == second.inserted_or_updated == 42

    count = await session.scalar(
        select(func.count()).select_from(Product).where(Product.tenant_id == tenant.id)
    )
    assert count == 42  # upsert, not duplicates

    p = await session.scalar(
        select(Product).where(Product.tenant_id == tenant.id, Product.sku == "TRN-38-GALV")
    )
    assert p is not None
    assert p.embedding is not None and len(p.embedding) == EMBEDDING_DIM
    assert p.attributes == {"marca": "Fixa"}


async def test_search_text_is_generated_by_postgres(session: AsyncSession, tenant: Tenant) -> None:
    hit = await session.scalar(
        select(Product.sku).where(
            Product.tenant_id == tenant.id,
            Product.search_text.op("@@")(func.plainto_tsquery("spanish", "tornillo galvanizado")),
        )
    )
    assert hit is not None and hit.startswith("TRN-")
