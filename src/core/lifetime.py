from fastapi import FastAPI
from httpx import AsyncClient
from src.utils.logging import get_logger

logger = get_logger(__name__)

class LifecycleManager:
    """Manages FastAPI application lifecycle events."""
    
    @staticmethod
    def register_startup_event(app: FastAPI) -> None:
        """
        Register startup event to initialize resources.

        Args:
            app: FastAPI application instance.
        """
        async def startup() -> None:
            try:
                logger.info("Initializing HTTPX AsyncClient on startup")
                app.state.httpx_client = AsyncClient()
                logger.debug("HTTPX AsyncClient initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize HTTPX AsyncClient: {str(e)}")
                raise

        app.add_event_handler("startup", startup)

    @staticmethod
    def register_shutdown_event(app: FastAPI) -> None:
        """
        Register shutdown event to clean up resources.

        Args:
            app: FastAPI application instance.
        """
        async def shutdown() -> None:
            try:
                logger.info("Closing HTTPX AsyncClient on shutdown")
                if hasattr(app.state, 'httpx_client') and app.state.httpx_client:
                    await app.state.httpx_client.aclose()
                    logger.debug("HTTPX AsyncClient closed successfully")
            except Exception as e:
                logger.error(f"Failed to close HTTPX AsyncClient: {str(e)}")
                # Suppress errors to ensure shutdown completes

        app.add_event_handler("shutdown", shutdown)