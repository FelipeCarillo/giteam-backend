from typing import List

from entities.entities import AIModel
from schemas.http.schemas import ResponseModel


class ListAIModelsProvidersResponse(ResponseModel):
    providers: List[str] = []


class ListAIModelsResponse(ResponseModel):
    ai_models: List[AIModel] = []
