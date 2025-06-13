from fastapi import APIRouter, Depends, status

from entities import User, Agent
from models import Agent as AgentORM
from models import Operation as OperationORM

from infra.database import Database
from infra.api_github import APIGithub

from helpers.errors import handle_exceptions
from helpers.auth import get_current_active_user, oauth2_scheme
from schemas.operations.schemas import ListOperationsResponse, OperationDetails

operation_router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@handle_exceptions
@operation_router.get("/", status_code=status.HTTP_200_OK, response_model=ListOperationsResponse)
async def get_operations(
        token: str = Depends(oauth2_scheme),
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

        api_github = APIGithub()

        operations = []
        for operation_orm in operations_orm:
            agent = Agent(**operation_orm.agent.__dict__)
            repository = await api_github.get_repository(token, repo_id=operation_orm.repository_id)
            operation = OperationDetails(
                id=operation_orm.id,
                agent=agent,
                repository=repository,
                action=operation_orm.action,
                details=operation_orm.details,
                created_at=operation_orm.created_at.isoformat(),
                updated_at=operation_orm.updated_at.isoformat() if operation_orm.updated_at else None
            )
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
