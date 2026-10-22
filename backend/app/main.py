"""SalesGenie AI - FastAPI application entry point.

Run from the project root:

    python -m uvicorn app.main:app --reload --app-dir backend

Interactive API documentation is available at ``/docs`` and the OpenAPI schema at ``/openapi.json``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.errors import register_exception_handlers
from app.routers import company_analysis, leads, outreach
from app.schemas.lead_schema import HealthResponse

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("salesgenie")

DESCRIPTION = """
SalesGenie AI - AI Sales Assistant & Lead Intelligence Platform.

**Milestone 1 - Lead Management & Intelligence Engine** is implemented:
lead CRUD, CSV import with validation and duplicate detection, and company insights with a
transparent qualification score.

**Milestone 2 (first slice) - AI Outreach Generation** is implemented:
prompt templates, provider-backed generation with a labelled mock fallback, and draft storage.

Conversation intelligence, CRM integration, the full analytics dashboard and the learned
conversion model are later stages and are not exposed by this API.
"""


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Log the effective configuration on startup and dispose of the engine on shutdown."""
    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Database engine: %s", engine.url.render_as_string(hide_password=True))
    logger.info("LLM provider configured: %s", settings.llm_configured)
    yield
    engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(leads.router, prefix=settings.api_prefix)
app.include_router(company_analysis.router, prefix=settings.api_prefix)
app.include_router(outreach.router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthResponse, tags=["system"], summary="Service health")
def health() -> HealthResponse:
    """Return the service health payload."""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )


@app.get("/", tags=["system"], summary="Service banner")
def root() -> JSONResponse:
    """Return a short banner pointing at the API documentation."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        },
    )


def create_app() -> FastAPI:
    """Return the configured application (used by the test suite)."""
    return app
