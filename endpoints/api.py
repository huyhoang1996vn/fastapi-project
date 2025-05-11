from fastapi import APIRouter
from .products import product_router
from .auth import auth_router

api_router = APIRouter()
api_router.include_router(product_router)
api_router.include_router(auth_router)
