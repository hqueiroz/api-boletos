from fastapi import APIRouter

from api.v1.endpoints import boleto 

api_router = APIRouter()
api_router.include_router(boleto.router, prefix='/boleto', tags=['Boleto'])

