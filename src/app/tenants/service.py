from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant


async def get_tenant_by_whatsapp(session: AsyncSession, whatsapp_number: str) -> Tenant | None:
    """The only way a request maps to a tenant: the destination number, which the user
    cannot forge. Never trust a tenant id coming from the message body."""
    return await session.scalar(select(Tenant).where(Tenant.whatsapp_number == whatsapp_number))


async def get_or_create_tenant(
    session: AsyncSession, *, name: str, whatsapp_number: str, currency: str = "BOB"
) -> Tenant:
    tenant = await get_tenant_by_whatsapp(session, whatsapp_number)
    if tenant is None:
        tenant = Tenant(name=name, whatsapp_number=whatsapp_number, currency=currency)
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
    return tenant
