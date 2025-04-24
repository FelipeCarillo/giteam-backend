from typing import List

from entities.entities import AIModel
from schemas.http.schemas import ResponseModel


class ListAIModelsResponse(ResponseModel):
    ai_models: List[AIModel] = []
