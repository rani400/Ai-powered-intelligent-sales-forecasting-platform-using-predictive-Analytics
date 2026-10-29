"""SalesGenie AI API: ONLY milestone Modules 1–4."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import leads, intelligence, outreach, scoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Explicit, versioned migrations; run `alembic upgrade head` before server startup.
    yield


def create_app():
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version='1.0.0',
                  description='Four-module lead intelligence and predictive conversion DEMO. No emails are sent.',
                  lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(',')],
                       allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['*'])
    app.include_router(leads.router)
    app.include_router(intelligence.router)
    app.include_router(outreach.router)
    app.include_router(scoring.router)

    @app.get('/health', tags=['System'])
    def health():
        return {'status': 'ok', 'application': settings.app_name, 'active_modules': 4}
    return app


app = create_app()
