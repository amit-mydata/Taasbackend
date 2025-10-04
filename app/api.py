from fastapi import APIRouter

from app.routes.analyzer import analyze_router


api_router = APIRouter()


api_router.include_router(analyze_router, prefix= "/analyzer", tags=['analyzer'] )