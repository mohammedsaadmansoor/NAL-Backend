from fastapi import APIRouter
from .views import router

user_profile_router = APIRouter()
user_profile_router.include_router(router, prefix="/profile", tags=["user profile"])
