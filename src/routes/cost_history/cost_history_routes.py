from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlalchemy.orm import joinedload

from entities import CostHistory, User
from models import CostHistory as CostHistoryORM, User as UserORM, UserSettings as UserSettingsORM

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
        # Modificação: usar joinedload para carregar o usuário relacionado e suas configurações
        query = session.query(CostHistoryORM).filter(CostHistoryORM.user_id == current_user.id) \
            .options(joinedload(CostHistoryORM.user).joinedload(UserORM.settings))

        if month:
            query = query.filter(CostHistoryORM.month == month)

        cost_history_orm = query.all()

        # Cria a lista de históricos de custo com os usuários relacionados
        cost_history = []
        for record in cost_history_orm:
            # Converte o objeto ORM para o modelo Pydantic
            cost_hist = CostHistory(**record.__dict__)

            # Adiciona o usuário ao objeto CostHistory
            if record.user:
                user_dict = record.user.__dict__.copy()

                # Adiciona as configurações do usuário se existirem
                if record.user.settings:
                    user_dict["settings"] = record.user.settings.__dict__

                # Adiciona o URL do avatar que vem do GitHub (conforme feito em user_routes.py)
                # Note: Como não temos acesso direto ao avatar_url do GitHub aqui,
                # você pode precisar adicionar isso através de uma chamada separada ou armazená-lo no banco de dados
                cost_hist.user = User(**user_dict)

            cost_history.append(cost_hist)

        return ListCostHistoryResponse(
            message="Cost history retrieved successfully." if cost_history else "No cost history found.",
            cost_history=cost_history
        )
    except Exception as error:
        return error
    finally:
        db.close_session()