import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import StructuredLoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi import Request
settings = get_settings()

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    description="Smart Task Manager — REST API backing a simplified Jira-style "
    "task tracker with n8n-driven automation and an agentic AI layer.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(StructuredLoggingMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "type": type(exc).__name__}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Basic liveness check — used by Docker healthchecks and n8n to confirm the API is up."""
    return {"status": "ok", "environment": settings.environment}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("%s starting up in %s mode", settings.app_name, settings.environment)


# Routers are registered here as each phase implements them, e.g.:
from app.routers import ai, auth, dashboard, task_extras, tasks, recurring
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(task_extras.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(recurring.router, prefix="/api/v1")
