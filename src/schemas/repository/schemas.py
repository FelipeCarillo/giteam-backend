from typing import List

from entities import Repository
from helpers.enums import AgentFunction, AgentResponseLength
from schemas.http import ResponseModel


class ListRepositoryResponse(ResponseModel):
    repositories: List[Repository] = []


class CreateAgentRequest(ResponseModel):
    name: str
    function: AgentFunction
    ai_model_id: int
    response_length: AgentResponseLength = "medium"


class CreateRepositoryRequest(ResponseModel):
    id: int
    agents: List[CreateAgentRequest]
