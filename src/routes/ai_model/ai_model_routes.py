from typing import Literal
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status

from entities import AIModel, User
from models import AIModel as AIModelORM

from infra.database import Database

from helpers.auth import get_current_active_user
from schemas.ai_model import ListAIModelsResponse

ai_model_router = APIRouter(
    prefix="/ai-models",
    tags=["AI Model"],
)


@ai_model_router.get("/", status_code=status.HTTP_200_OK, response_model=ListAIModelsResponse)
async def get_ai_models(
        language: Literal['br', 'us'] = "us",
        _: User = Depends(get_current_active_user),
):
    """List all AI models."""
    db = Database()
    session = db.get_session()

    try:
        ai_models = session.query(AIModelORM).all()
        if not ai_models:
            return JSONResponse(status_code=204, content=ListAIModelsResponse(message="No AI models found."))

        ai_models = [
            AIModel(
                **model.__dict__,
                specialties=model.specialties_br if language == "br" else model.specialties_us,
            ) for model in ai_models]

        return JSONResponse(status_code=200, content={"ai_models": ai_models})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()
