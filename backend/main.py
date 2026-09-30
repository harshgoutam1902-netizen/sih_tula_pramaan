"""
FastAPI application entry point for TulaPramaan 3-Stage Smart Form System.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from config import get_settings
from database import init_db
from models.rulepacks import load_rulepack, clear_rulepack_cache

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting TulaPramaan application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Pre-load default rulepack
    if settings.rulepack_cache_enabled:
        try:
            load_rulepack(settings.default_rulepack_version, settings.rulepack_dir)
            logger.info(f"Loaded rulepack: {settings.default_rulepack_version}")
        except Exception as e:
            logger.error(f"Failed to load rulepack: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TulaPramaan application...")
    
    # Clear caches
    if settings.rulepack_cache_enabled:
        clear_rulepack_cache()
        logger.info("Cleared rulepack cache")
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Assisted OIML R 76 Type Evaluation & Test Report Automation",
    docs_url=settings.docs_url if settings.docs_enabled else None,
    redoc_url=settings.redoc_url if settings.docs_enabled else None,
    lifespan=lifespan
)


# ========== Middleware ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ========== Exception Handlers ==========

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle missing rulepack files."""
    logger.error(f"FileNotFoundError: {exc}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"Resource not found: {str(exc)}"}
    )


# ========== Health Check Endpoints ==========

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


@app.get("/api/v1/status")
async def api_status():
    """Detailed API status."""
    return {
        "status": "operational",
        "version": settings.app_version,
        "environment": settings.app_env,
        "features": {
            "ocr_enabled": settings.feature_ocr_enabled,
            "live_mpe_feedback": settings.feature_live_mpe_feedback,
            "multi_range_support": settings.feature_multi_range_support,
            "batch_repetitive_tests": settings.feature_batch_repetitive_tests,
            "environment_auto_propagation": settings.feature_environment_auto_propagation,
        },
        "rulepack": {
            "default_version": settings.default_rulepack_version,
            "cache_enabled": settings.rulepack_cache_enabled,
        }
    }


# ========== Router Registration ==========
from routers import classification, test_plans, environment, instruments, rag, ml

app.include_router(
    classification.router,
    prefix="/api/v1/classification",
    tags=["Classification"]
)

app.include_router(
    test_plans.router,
    prefix="/api/v1/test-plans",
    tags=["Test Plans"]
)

app.include_router(
    environment.router,
    prefix="/api/v1/environment",
    tags=["Environment"]
)

app.include_router(
    instruments.router,
    prefix="/api/v1/instruments",
    tags=["Instrument Profiles"]
)

app.include_router(
    rag.router,
    prefix="/api/v1",
    tags=["RAG"]
)

app.include_router(
    ml.router,
    prefix="/api/v1",
    tags=["ML"]
)


# ========== Development Endpoints ==========

if settings.debug:
    @app.post("/dev/reload-rulepacks")
    async def reload_rulepacks():
        """Reload all rulepacks (development only)."""
        clear_rulepack_cache()
        try:
            load_rulepack(settings.default_rulepack_version, settings.rulepack_dir)
            return {"status": "success", "message": "Rulepacks reloaded"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )


# ========== Application Entry Point ==========

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
