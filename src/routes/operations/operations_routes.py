from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlalchemy.orm import joinedload

from entities import Operation, User, Agent, Repository, AIModel
from models import Operation as OperationORM
from models import Agent as AgentORM
from models import Repository as RepositoryORM
from models import AIModel as AIModelORM

from infra.database import Database

from helpers.auth import get_current_active_user
from helpers.errors import handle_exceptions
from schemas.operations.schemas import ListOperationsResponse

operation_router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@handle_exceptions
@operation_router.get("/", status_code=status.HTTP_200_OK, response_model=ListOperationsResponse)
async def get_operations(
        current_user: User = Depends(get_current_active_user),
):
    """List all operations, optionally filtered by agent_id."""
    db = Database()
    session = db.get_session()

    try:

        operations_orm = session.query(OperationORM).filter(
            OperationORM.agent.has(AgentORM.created_by_id == current_user.id),
        ).all()

        if not operations_orm:
            return ListOperationsResponse(
                message="No operations found.",
                operations=[]
            )

        operations = []
        for operation_orm in operations_orm:
            operation = Operation(**operation_orm.__dict__)

            if operation_orm.agent:
                agent_dict = operation_orm.agent.__dict__.copy()
                agent_dict["created_by"] = User(**operation_orm.agent.created_by.__dict__)
                agent_dict["repository"] = Repository(**operation_orm.agent.repository.__dict__)
                agent_dict["ai_model"] = AIModel(**operation_orm.agent.ai_model.__dict__)
                operation.agent = Agent(**agent_dict)

            operations.append(operation)

        operations.sort(key=lambda x: x.created_at, reverse=True)

        return ListOperationsResponse(
            message="Operations retrieved successfully." if operations else "No operations found.",
            operations=operations
        )
    except Exception as error:
        raise error
    finally:
        db.close_session()
