"""Main FastAPI application for Starluck Astro API."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os

from app.core.config import settings
from app.core.security import verify_host
from app.api.endpoints import router

LOG_DIR = "debug_outputs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "server.log"), encoding="utf-8"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("starluck")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional astrological chart calculation and rendering API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Host verification middleware
@app.middleware("http")
async def verify_host_middleware(request: Request, call_next):
    """Verify that requests come from allowed hosts."""
    try:
        verify_host(request)
    except Exception as e:
        logger.warning(f"Host verification failed: {e}")
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied from this host"}
        )
    
    response = await call_next(request)
    return response

app.include_router(router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Starluck Astro API",
        "version": settings.app_version,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug
    )
