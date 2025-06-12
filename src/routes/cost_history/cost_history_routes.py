from datetime import datetime
from sqlalchemy.orm import joinedload
from fastapi import APIRouter, Depends, status

from entities import CostHistory, User
from models import CostHistory as CostHistoryORM, User as UserORM

from infra.database import Database

from helpers.errors import handle_exceptions
from helpers.auth import get_current_active_user
from schemas.cost_history.schemas import ListCostHistoryResponse

cost_history_router = APIRouter(
    prefix="/cost-history",
    tags=["Cost History"],
)


@handle_exceptions
@cost_history_router.get("/", status_code=status.HTTP_200_OK, response_model=ListCostHistoryResponse)
async def get_cost_history(
        current_user: User = Depends(get_current_active_user),
):
    """List cost history for the current user, optionally filtered by month."""
    db = Database()
    session = db.get_session()

    try:
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        month = f"{current_year}-{current_month:02d}"

        # Modificação: usar joinedload para carregar o usuário relacionado e suas configurações
        query = session.query(CostHistoryORM).filter(
            CostHistoryORM.user_id == current_user.id,
            CostHistoryORM.month == month,
        ).options(
            joinedload(CostHistoryORM.user).joinedload(UserORM.settings)
        )

        cost_history_orm = query.all()

        cost_history = []
        for record in cost_history_orm:
            cost_hist = CostHistory(**record.__dict__)

            if record.user:
                user_dict = record.user.__dict__.copy()

                if record.user.settings:
                    user_dict["settings"] = record.user.settings.__dict__

                cost_hist.user = User(**user_dict)

            cost_history.append(cost_hist)

        return ListCostHistoryResponse(
            message="Cost history retrieved successfully." if cost_history else "No cost history found.",
            cost_history=cost_history
        )
    except Exception as error:
        raise error
    finally:
        db.close_session()
