from pydantic import BaseModel
from typing import List, Optional

from entities import Agent, Repository
from schemas.http import ResponseModel


class OperationDetails(BaseModel):
    """Response model for operation details."""
    id: int
    agent: Agent
    repository: Repository
    action: str
    details: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ListOperationsResponse(ResponseModel):
    """Response model for operations list endpoint."""
    operations: Optional[List[OperationDetails]] = None
