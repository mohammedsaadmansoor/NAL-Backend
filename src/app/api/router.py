from fastapi.routing import APIRouter

from src.app.api import monitoring
from src.app.api.auth import auth_router
from src.app.api.user_profile import user_profile_router

api_router = APIRouter()
api_router.include_router(monitoring.router, tags=["health check"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(user_profile_router, tags=["user profile"])