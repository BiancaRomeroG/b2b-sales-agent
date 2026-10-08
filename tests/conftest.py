import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, engine
from app.main import app
from app.models import Tenant
from app.tenants.service import get_or_create_tenant


def has_infra() -> bool:
    return os.getenv("INTEGRATION") == "1"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Apply all migrations once per test session. Integration tests depend on this."""
    if not has_infra():
        pytest.skip("set INTEGRATION=1 with docker compose up")
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def session(migrated_db: None) -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as s:
        yield s
    # pytest-asyncio gives each test its own event loop. Pooled asyncpg connections belong to
    # the loop that created them, so the pool is dropped here and rebuilt on the next test.
    await engine.dispose()


@pytest.fixture
async def tenant(session: AsyncSession) -> Tenant:
    return await get_or_create_tenant(
        session, name="Test Ferretería", whatsapp_number="whatsapp:+10000000001"
    )
