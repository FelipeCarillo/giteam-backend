from typing import List

from pydantic import BaseModel

from entities import Repository
from helpers.enums import AgentFunction, AgentResponseLength
from schemas.http import ResponseModel


class ListRepositoryResponse(ResponseModel):
    repositories: List[Repository] = []


class AvailableRepositoryResponse(BaseModel):
    id: int
    name: str
    url: str


class ListRepositoryAvailableResponse(ResponseModel):
    repositories: List[AvailableRepositoryResponse] = []


class CreateAgentRequest(BaseModel):
    name: str
    function: AgentFunction
    ai_model_id: int
    response_length: AgentResponseLength = "medium"


class CreateRepositoryRequest(BaseModel):
    id: int
    agents: List[CreateAgentRequest]
