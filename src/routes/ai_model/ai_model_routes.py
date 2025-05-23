from typing import Literal
from fastapi import APIRouter, HTTPException, Depends, status

from entities import AIModel, User
from models import AIModel as AIModelORM
from helpers.errors import handle_exceptions

from infra.database import Database

from helpers.enums import AIModelProvider
from helpers.auth import get_current_active_user

from schemas.ai_model import ListAIModelsResponse, ListAIModelsProvidersResponse

ai_model_router = APIRouter(
    prefix="/ai-models",
    tags=["AI Model"],
)


@handle_exceptions
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
            raise HTTPException(status_code=204, detail="No AI models found")

        ai_models = [
            AIModel(
                **model.__dict__,
                specialties=model.specialties_br if language == "br" else model.specialties_us,
            ) for model in ai_models]

        return ListAIModelsResponse(message="AI models retrieved successfully.", ai_models=ai_models)
    except Exception as e:
        raise e
    finally:
        db.close_session()


@ai_model_router.get(
    "/providers",
    name="Get AI model providers",
    status_code=status.HTTP_200_OK,
    response_model=ListAIModelsProvidersResponse,
)
async def get_ai_model_providers(
        _: User = Depends(get_current_active_user),
):
    """List all AI model providers."""

    try:
        providers = [provider.value for provider in AIModelProvider]
        return ListAIModelsProvidersResponse(
            message="AI model providers retrieved successfully.",
            providers=providers,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
