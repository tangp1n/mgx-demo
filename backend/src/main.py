"""FastAPI application entry point."""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.config import settings
from src.services.database import connect_to_mongo, close_mongo_connection, create_indexes, get_database
from src.utils.errors import AppError, http_exception_from_error
from src.utils.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    await connect_to_mongo()
    await create_indexes()
    logger.info("Database connected and indexes created")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("Database connection closed")


# Create FastAPI app
app = FastAPI(
    title="AI-Powered Conversational App Builder Platform",
    description="API for conversational app creation platform with AI code generation and container execution",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.
    Returns the status of the application and its dependencies.
    """
    health_status = {
        "status": "healthy",
        "service": "AI-Powered Conversational App Builder Platform",
        "version": "1.0.0",
        "checks": {}
    }

    # Check database connection
    try:
        db = get_database()
        await db.client.admin.command("ping")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection is active"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        logger.warning(f"Health check: Database connection failed - {e}")

    # Determine overall status
    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status


# Error handlers
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse as FastAPIJSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle FastAPI request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    """Application error handler."""
    logger.error(f"Application error: {exc.message}", exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=http_exception_from_error(exc).detail,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc) if settings.debug else "An internal server error occurred",
        },
    )


# Include API routers
from src.api import auth, applications, conversations

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(applications.router, prefix=settings.api_prefix)
app.include_router(conversations.router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys

    # Ensure we're using the correct event loop policy
    # This must be set before any async operations
    if sys.platform == "win32":
        # Windows-specific: use SelectorEventLoopPolicy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        # Unix: use default policy (usually SelectorEventLoop)
        # Ensure we're using the selector event loop for better async I/O
        try:
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        except AttributeError:
            # Python < 3.7 compatibility
            pass

    # Enable asyncio debug mode in development
    if settings.debug:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        # Enable debug mode for better error reporting
        import logging
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        loop="asyncio",  # Explicitly use asyncio event loop
        # Ensure proper async handling
        access_log=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

