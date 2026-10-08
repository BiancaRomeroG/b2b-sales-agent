from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings
from app.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.redis = redis.from_url(settings.redis_url)
    yield
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(title="B2B Sales Agent", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
