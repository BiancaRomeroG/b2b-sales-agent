"""Upsert validated products for one tenant, with embeddings computed in batch."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.schemas import IngestReport, ProductIn
from app.models import Product, Tenant
from app.search.embeddings import get_embedder, product_embed_text


def validate_rows(rows: list[dict[str, Any]]) -> tuple[list[ProductIn], list[str]]:
    valid: list[ProductIn] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for i, row in enumerate(rows):
        try:
            p = ProductIn.model_validate(row)
        except ValidationError as e:
            err = e.errors()[0]
            rejected.append(f"row {i} ({row.get('sku', '?')}): {err['loc'][0]}: {err['msg']}")
            continue
        if p.sku in seen:
            rejected.append(f"row {i} ({p.sku}): duplicate sku in file")
            continue
        seen.add(p.sku)
        valid.append(p)
    return valid, rejected


async def upsert_products(
    session: AsyncSession, tenant: Tenant, products: list[ProductIn], rejected: list[str]
) -> IngestReport:
    if not products:
        return IngestReport(
            tenant=tenant.name, received=len(rejected), inserted_or_updated=0, rejected=rejected
        )

    embedder = get_embedder()
    texts = [product_embed_text(p.name, p.description, p.category) for p in products]
    vectors = embedder.embed_passages(texts)

    values = [
        {**p.model_dump(), "tenant_id": tenant.id, "embedding": vec}
        for p, vec in zip(products, vectors, strict=True)
    ]
    stmt = insert(Product).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_products_tenant_sku",
        set_={
            col: getattr(stmt.excluded, col)
            for col in (
                "name",
                "description",
                "category",
                "unit",
                "price",
                "stock",
                "attributes",
                "embedding",
            )
        },
    )
    await session.execute(stmt)
    await session.commit()

    return IngestReport(
        tenant=tenant.name,
        received=len(products) + len(rejected),
        inserted_or_updated=len(products),
        rejected=rejected,
    )
