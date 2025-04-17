from fastapi import APIRouter
from fastapi.responses import JSONResponse

from entities.entities import AIModel
from models.models import AIModel as AIModelORM

from infra.database import Database

ai_model_router = APIRouter(
    prefix="/ai-models",
    tags=["AI Model"],
)


@ai_model_router.get("/", name="AI Models", description="List all AI models")
async def get_ai_models():
    """List all AI models."""
    db = Database()
    session = db.get_session()

    try:
        ai_models = session.query(AIModelORM).all()
        if not ai_models:
            return JSONResponse(status_code=204, content={"message": "No AI models found."})

        ai_models = [AIModel(**model.__dict__) for model in ai_models]

        return JSONResponse(status_code=200, content={"ai_models": [model.model_dump() for model in ai_models]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()
