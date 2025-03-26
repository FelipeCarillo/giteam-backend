from fastapi import APIRouter


home_router = APIRouter(
    prefix="/home",
    tags=["home"]
)