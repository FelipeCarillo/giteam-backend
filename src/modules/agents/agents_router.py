from fastapi import APIRouter


agents_router = APIRouter(
    prefix="/agents",
    tags=["agents"]
)


