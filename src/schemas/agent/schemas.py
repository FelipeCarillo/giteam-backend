from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from entities import Repository, AIModel, Operation # Added Operation import here

class UpdateAgent(BaseModel):
    """Pydantic model for updating an agent."""
    name: Optional[str] = None
    ai_model_id: Optional[int] = None
    active: Optional[bool] = None
    response_length: Optional[str] = None
    branches: Optional[List[int]] = None

class AgentResponse(BaseModel):
    """Pydantic model for the response when getting agent details."""
    id: int
    name: str
    function: str
    repository_id: int
    ai_model_id: int
    response_length: str
    active: bool
    created_at: datetime
    updated_at: datetime

    repository: Optional[Repository] = None
    ai_model: Optional[AIModel] = None
    operations: List[Operation] = []

    class Config:
        from_attributes = True

class GetAgentsResponse(BaseModel):
    """Pydantic model for the overall response when fetching multiple agents."""
    agents: List[AgentResponse]