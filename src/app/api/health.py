from fastapi import APIRouter, Request
from sqlalchemy import text

from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Process is up. No dependencies checked."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    """Dependencies reachable: Postgres and Redis."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await request.app.state.redis.ping()
    return {"status": "ok", "postgres": "ok", "redis": "ok"}
