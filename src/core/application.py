import toml
from fastapi import FastAPI
from src.settings import settings
from src.utils.logging import get_logger
from src.app.api.router import api_router
from src.core.lifetime import LifecycleManager
from src.middleware import ExceptionHandlerMiddleware
from src.middleware.exception import ExceptionResponseModel
# from src.app.api.analytics.utils import start_scheduler
# from src.app.api.analytics.analytics_wrapper import AnalyticsSDK


logger = get_logger(__name__)

def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This factory function constructs and configures the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    try:
        logger.info("Initializing FastAPI application")
        
        # Load version from pyproject.toml
        file_path = "pyproject.toml"
        with open(file_path, "r") as toml_file:
            data = toml.loads(toml_file.read())
        
        # Create FastAPI app with version from pyproject.toml
        app = FastAPI(
            title="NAL Platform Service",
            version=data["tool"]["poetry"]["version"],
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json",
        )



        # Register startup and shutdown events 
        LifecycleManager.register_startup_event(app)
        LifecycleManager.register_shutdown_event(app)

        # Add middleware
        app.add_middleware(ExceptionHandlerMiddleware)
        
        # Add request context middleware
        from src.middleware.request import set_request_context
        app.middleware("http")(set_request_context)

        # Include API router
        app.include_router(
            router=api_router,
            prefix="/api",
            responses={
                400: {
                    "model": ExceptionResponseModel,
                    "description": "Bad Request",
                },
                500: {
                    "model": ExceptionResponseModel,
                    "description": "Internal Server Error",
                },
            },
        )

        @app.on_event("startup")
        async def start_scheduler_event():
            # service_instance = AnalyticsSDK(credentials_dict=settings.goole_firestore_service_account_dict) 
            # start_scheduler(service_instance)
            
            # Run database migrations
            try:
                from src.db.migrate import run_migrations
                await run_migrations()
                logger.info("Database migrations completed successfully")
            except Exception as e:
                logger.error(f"Failed to run database migrations: {str(e)}")
                logger.warning("Application will continue without migrations. Please check database connection.")
                # Don't fail startup for migration errors in development
                if settings.environment == "production":
                    logger.error("Production environment requires successful migrations")
                    raise
        
            logger.info("FastAPI application initialized successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to initialize FastAPI application: {str(e)}")
        raise