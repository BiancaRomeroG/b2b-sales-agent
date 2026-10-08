"""CLI: load a catalog into a tenant.

    uv run python -m app.ingest csv --tenant "Ferretería Central" \
        --whatsapp whatsapp:+14155238886 --file data/catalogo_ferreteria.csv
    uv run python -m app.ingest pdf --tenant "Ferretería Central" \
        --whatsapp whatsapp:+14155238886 --file data/catalogo_ferreteria.pdf
"""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from app.db import SessionLocal
from app.ingest.extract import extract_products
from app.ingest.loaders import read_csv, read_pdf_markdown
from app.ingest.schemas import IngestReport
from app.ingest.service import upsert_products, validate_rows
from app.tenants.service import get_or_create_tenant

cli = typer.Typer(no_args_is_help=True)

TenantOpt = Annotated[str, typer.Option(help="Tenant name; created if missing")]
WhatsappOpt = Annotated[str, typer.Option(help="Tenant WhatsApp number, e.g. whatsapp:+591...")]
FileOpt = Annotated[Path, typer.Option(exists=True, dir_okay=False, readable=True)]


def _print(report: IngestReport) -> None:
    typer.echo(
        f"tenant={report.tenant} received={report.received} "
        f"upserted={report.inserted_or_updated} rejected={len(report.rejected)}"
    )
    for r in report.rejected:
        typer.echo(f"  - {r}")


@cli.command()
def csv(tenant: TenantOpt, whatsapp: WhatsappOpt, file: FileOpt) -> None:
    async def run() -> IngestReport:
        async with SessionLocal() as session:
            t = await get_or_create_tenant(session, name=tenant, whatsapp_number=whatsapp)
            valid, rejected = validate_rows(read_csv(file))
            return await upsert_products(session, t, valid, rejected)

    _print(asyncio.run(run()))


@cli.command()
def pdf(tenant: TenantOpt, whatsapp: WhatsappOpt, file: FileOpt) -> None:
    async def run() -> IngestReport:
        text = read_pdf_markdown(file)
        if not text.strip():
            raise typer.BadParameter("PDF has no text layer; OCR is not wired yet")
        async with SessionLocal() as session:
            t = await get_or_create_tenant(session, name=tenant, whatsapp_number=whatsapp)
            valid, rejected = await extract_products(text)
            return await upsert_products(session, t, valid, rejected)

    _print(asyncio.run(run()))


if __name__ == "__main__":
    cli()
