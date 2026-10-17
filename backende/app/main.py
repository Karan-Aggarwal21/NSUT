"""Cognivia FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.questionnaire_service import seed_default_questionnaire

logging.basicConfig(
    level=logging.INFO if not settings.APP_DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cognivia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    logger.info("Initializing Cognivia backend...")
    # In development/test mode, ensure tables exist if not running alembic
    if settings.APP_ENV != "testing":
        try:
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                seed_default_questionnaire(db)
                logger.info("Default questionnaire verified.")
            finally:
                db.close()
        except Exception as e:
            logger.warning("Could not auto-seed database on startup: %s", str(e))
    yield
    logger.info("Shutting down Cognivia backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-Based Cognitive Gaming and Memory Assistance Platform Backend for Elderly People. "
        "Engineered for high reliability, offline synchronisation, and sensitive data protection."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], summary="System health check")
def health_check():
    """Verify backend responsiveness and basic service health."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# Register v1 router
app.include_router(api_router)


# Global unhandled exception handler to avoid leaking internal tracebacks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
