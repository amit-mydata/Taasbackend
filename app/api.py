from fastapi import APIRouter

from app.routes.analyzer import analyze_router

from app.routes.user import user_router

api_router = APIRouter()

# User router
api_router.include_router(user_router, prefix="/user", tags=["user"])

# Analyzer router
api_router.include_router(analyze_router, prefix= "/analyzer", tags=['analyzer'] )