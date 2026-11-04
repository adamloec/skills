"""{{App}} API — FastAPI entrypoint.

Serves every route under ``/v1``, plus the ``/health`` and ``/readiness`` probes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from {{pkg}}.api.middleware.exception_handler import (
    app_exception_handler,
    unhandled_exception_handler,
)
from {{pkg}}.api.routes import router
from {{pkg}}.config import db
from {{pkg}}.lib.exceptions import {{App}}Exception
from {{pkg}}.lib.utils.logger import get_logger

logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the database engine, and close it on shutdown.

    No schema is created here. Alembic owns it, and the image entrypoint has already applied it
    by the time this process starts.
    """
    logger.info("Starting {{App}} API")
    await db.init()
    logger.info("{{App}} API started")
    try:
        yield
    finally:
        logger.info("Shutting down {{App}} API")
        await db.close()
        logger.info("{{App}} API stopped")


app = FastAPI(title="{{App}} API", version="0.1.0", lifespan=lifespan)

app.add_exception_handler({{App}}Exception, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(router)


@app.get("/health", status_code=204)
async def health() -> None:
    """Report liveness: the process is up."""


@app.get("/readiness", status_code=204)
async def readiness() -> None:
    """Report readiness: the database is reachable.

    Raises:
        HTTPException: 503 when the database cannot be queried.
    """
    try:
        async with db.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable") from None
