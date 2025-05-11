from fastapi import APIRouter, Depends, status
from typing import Optional

from entities import CostHistory, User
from models import CostHistory as CostHistoryORM

from infra.database import Database

from helpers.auth import get_current_active_user
from helpers.errors import handle_exceptions
from schemas.cost_history.schemas import ListCostHistoryResponse

cost_history_router = APIRouter(
    prefix="/cost-history",
    tags=["Cost History"],
)


@handle_exceptions
@cost_history_router.get("/", status_code=status.HTTP_200_OK, response_model=ListCostHistoryResponse)
async def get_cost_history(
        month: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
):
    """List cost history for the current user, optionally filtered by month."""
    db = Database()
    session = db.get_session()

    try:
        query = session.query(CostHistoryORM).filter(CostHistoryORM.user_id == current_user.id)
        if month:
            query = query.filter(CostHistoryORM.month == month)

        cost_history_orm = query.all()
        cost_history = [CostHistory(**record.__dict__) for record in cost_history_orm]

        return ListCostHistoryResponse(
            message="Cost history retrieved successfully." if cost_history else "No cost history found.",
            cost_history=cost_history
        )
    except Exception as error:
        return error
    finally:
        db.close_session()