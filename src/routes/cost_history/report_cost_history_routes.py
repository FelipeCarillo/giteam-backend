from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func, desc
from typing import List, Dict, Any
import json

from entities.entities import User
from models.models import CostHistory as CostHistoryORM, Repository as RepositoryORM, Operation as OperationORM, Agent as AgentORM, AIModel as AIModelORM

from infra.database import Database

from helpers.auth import get_current_active_user
from schemas.cost_history.schemas import CostHistoryReport

report_cost_history_router = APIRouter(
    prefix="/reports/cost-history",
    tags=["Cost Reports"],
)

@report_cost_history_router.get("/", status_code=status.HTTP_200_OK, response_model=CostHistoryReport)
async def get_cost_history_report(
    start_month: str = None,
    end_month: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed cost report for the current user, optionally filtered by month range."""
    db = Database()
    session = db.get_session()

    try:
        # Base query for cost history
        query = session.query(CostHistoryORM).filter(CostHistoryORM.user_id == current_user.id)
        
        # Apply date range filters if provided
        if start_month:
            query = query.filter(CostHistoryORM.month >= start_month)
        if end_month:
            query = query.filter(CostHistoryORM.month <= end_month)
        
        # Order by month
        query = query.order_by(CostHistoryORM.month)
        
        # Get cost history records
        cost_history = query.all()
        
        if not cost_history:
            return JSONResponse(status_code=204, content={"message": "No cost history found in the specified range."})

        # Calculate summary data
        total_pr_cost = sum(record.pr_cost for record in cost_history)
        total_issue_cost = sum(record.issue_cost for record in cost_history)
        total_cost = sum(record.total_cost for record in cost_history)
        
        # Get model usage breakdown
        model_costs: Dict[str, float] = {}
        for record in cost_history:
            if record.model_costs:
                model_costs_data = json.loads(record.model_costs)
                for model_name, cost in model_costs_data.items():
                    model_costs[model_name] = model_costs.get(model_name, 0) + cost
        
        # Get repository usage breakdown
        repository_costs: Dict[str, float] = {}
        for record in cost_history:
            if record.repository_costs:
                repo_costs_data = json.loads(record.repository_costs)
                for repo_name, cost in repo_costs_data.items():
                    repository_costs[repo_name] = repository_costs.get(repo_name, 0) + cost
        
        # Prepare monthly breakdown
        monthly_breakdown = [
            {
                "month": record.month,
                "pr_cost": record.pr_cost,
                "issue_cost": record.issue_cost,
                "total_cost": record.total_cost,
                "model_costs": json.loads(record.model_costs) if record.model_costs else {},
                "repository_costs": json.loads(record.repository_costs) if record.repository_costs else {}
            }
            for record in cost_history
        ]
        
        # Compile report data
        report = {
            "summary": {
                "total_pr_cost": total_pr_cost,
                "total_issue_cost": total_issue_cost,
                "total_cost": total_cost,
                "date_range": {
                    "start_month": cost_history[0].month if cost_history else None,
                    "end_month": cost_history[-1].month if cost_history else None
                }
            },
            "model_breakdown": model_costs,
            "repository_breakdown": repository_costs,
            "monthly_breakdown": monthly_breakdown
        }
        
        return JSONResponse(status_code=200, content=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()