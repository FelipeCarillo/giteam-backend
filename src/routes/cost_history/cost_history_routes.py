from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status

from entities.entities import CostHistory, User
from models.models import CostHistory as CostHistoryORM

from infra.database import Database

from helpers.auth import get_current_active_user
from schemas.cost_history.schemas import ListCostHistoryResponse

cost_history_router = APIRouter(
    prefix="/cost-history",
    tags=["Cost History"],
)

@cost_history_router.get("/", status_code=status.HTTP_200_OK, response_model=ListCostHistoryResponse)
async def get_cost_history(
    month: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """List cost history for the current user, optionally filtered by month."""
    db = Database()
    session = db.get_session()

    try:
        query = session.query(CostHistoryORM).filter(CostHistoryORM.user_id == current_user.id)
        if month:
            query = query.filter(CostHistoryORM.month == month)
        
        cost_history = query.all()
        if not cost_history:
            return JSONResponse(status_code=204, content={"message": "No cost history found."})

        cost_history = [CostHistory(**record.__dict__) for record in cost_history]

        return JSONResponse(status_code=200, content={"cost_history": cost_history})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()