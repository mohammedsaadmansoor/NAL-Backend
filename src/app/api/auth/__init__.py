from fastapi import APIRouter
from .views import router

auth_router = APIRouter()
auth_router.include_router(router, prefix="/auth", tags=["authentication"])
