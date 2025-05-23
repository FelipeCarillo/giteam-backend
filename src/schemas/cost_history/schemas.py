from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from entities.entities import CostHistory
from schemas.http import ResponseModel


class ListCostHistoryResponse(ResponseModel):
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


class DateRange(BaseModel):
    """Date range for cost history report."""
    start_month: Optional[str] = None
    end_month: Optional[str] = None


class CostSummary(BaseModel):
    """Summary of total costs in the cost history report."""
    total_pr_cost: float
    total_issue_cost: float
    total_cost: float
    date_range: DateRange


class MonthlyBreakdown(BaseModel):
    """Monthly breakdown of costs."""
    month: str
    pr_cost: float
    issue_cost: float
    total_cost: float
    model_costs: Dict[str, float] = {}
    repository_costs: Dict[str, float] = {}


class CostHistoryReport(BaseModel):
    """Comprehensive cost history report."""
    summary: CostSummary
    model_breakdown: Dict[str, float] = {}
    repository_breakdown: Dict[str, float] = {}
    monthly_breakdown: List[MonthlyBreakdown] = []