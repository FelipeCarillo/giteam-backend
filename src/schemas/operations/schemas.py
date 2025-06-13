from pydantic import BaseModel
from typing import List, Optional

from entities import Agent, Repository
from schemas.http import ResponseModel


class OperationDetails(BaseModel):
    """Response model for operation details."""
    id: int
    agent: Agent
    repository: Repository
    details: Optional[str] = None
    action: str
    status: str
    github_reference: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    execution_time: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True


class ListOperationsResponse(ResponseModel):
    """Response model for operations list endpoint."""
    operations: Optional[List[OperationDetails]] = None
