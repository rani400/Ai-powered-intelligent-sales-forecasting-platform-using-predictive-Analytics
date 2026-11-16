
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.routers import leads, intelligence, outreach, scoring, crm


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database migrations separately before startup.
    yield


def create_app():
    settings = get_settings()

    # Disable default Swagger UI to create our own.
    app = FastAPI(
        title=settings.app_name,
        version="1.1.0",
        description="",
        docs_url=None,
        lifespan=lifespan
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            x.strip() for x in settings.cors_origins.split(",")
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"]
    )

    # Modules 1–5
    app.include_router(leads.router)
    app.include_router(intelligence.router)
    app.include_router(outreach.router)
    app.include_router(scoring.router)
    app.include_router(crm.router)

    # Health endpoint
    @app.get("/health", tags=["System"])
    def health():
        return {
            "status": "ok",
            "application": settings.app_name,
            "active_modules": 5,
            "integrations": ["crm"]
        }

    # Custom Swagger UI
    @app.get("/docs", include_in_schema=False)
    def custom_swagger():
        html = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="SalesGenie AI - API Documentation"
        ).body.decode("utf-8")

        # Hide the OpenAPI JSON link in the Swagger UI
        html = html.replace(
            "</head>",
            """
            <style>
                .swagger-ui .info .url {
                    display: none !important;
                }

                .swagger-ui .info a[href$="/openapi.json"] {
                    display: none !important;
                }
            </style>
            </head>
            """
        )

        return HTMLResponse(content=html)

    return app


app = create_app()
