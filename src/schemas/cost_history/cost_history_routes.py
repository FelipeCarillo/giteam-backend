from typing import List, Optional
from pydantic import BaseModel
from entities.entities import CostHistory

class ListCostHistoryResponse(BaseModel):
    """Response model for cost history list endpoint."""
    cost_history: Optional[List[CostHistory]] = None

class CostHistoryDetails(BaseModel):
    """Response model for cost history details."""
    id: int
    user_id: int
    month: str
    pr_cost: float
    issue_cost: float
    total_cost: float
    model_costs: Optional[str] = None
    repository_costs: Optional[str] = None
    
    class Config:
        from_attributes = True