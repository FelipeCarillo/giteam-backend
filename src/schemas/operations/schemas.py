# from typing import List, Optional
# from pydantic import BaseModel
# from entities.entities import Operation
#
# class ListOperationsResponse(BaseModel):
#     """Response model for operations list endpoint."""
#     operations: Optional[List[Operation]] = None
#
# class OperationDetails(BaseModel):
#     """Response model for operation details."""
#     id: int
#     agent_id: int
#     action: str
#     details: Optional[str] = None
#     github_reference: Optional[str] = None
#     prompt_tokens: Optional[int] = None
#     completion_tokens: Optional[int] = None
#     total_tokens: Optional[int] = None
#     cost: float
#     status: str
#     execution_time: Optional[float] = None
#     created_at: Optional[str] = None
#
#     class Config:
#         from_attributes = True

from typing import List, Optional
from pydantic import BaseModel

from entities import Operation
from schemas.http import ResponseModel


class ListOperationsResponse(ResponseModel):
    """Response model for operations list endpoint."""
    operations: Optional[List[Operation]] = None


class OperationDetails(BaseModel):
    """Response model for operation details."""
    id: int
    agent_id: int
    action: str
    details: Optional[str] = None
    github_reference: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: float
    status: str
    execution_time: Optional[float] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True