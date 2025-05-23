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
        agent_id: Optional[int] = None,
        current_user: User = Depends(get_current_active_user),
):
    """List all operations, optionally filtered by agent_id."""
    db = Database()
    session = db.get_session()

    try:
        # Use joinedload para carregar as relações necessárias em uma única consulta
        query = session.query(OperationORM).options(
            joinedload(OperationORM.agent).joinedload(AgentORM.repository),
            joinedload(OperationORM.agent).joinedload(AgentORM.ai_model)
        )

        if agent_id:
            query = query.filter(OperationORM.agent_id == agent_id)

        operations_orm = query.all()

        # Converter objetos ORM para entidades Pydantic
        operations = []
        for operation_orm in operations_orm:
            operation_dict = {k: v for k, v in operation_orm.__dict__.items() if not k.startswith('_')}

            # Processar o agente e seus relacionamentos
            if operation_orm.agent:
                agent_orm = operation_orm.agent
                agent_dict = {k: v for k, v in agent_orm.__dict__.items() if not k.startswith('_')}

                # Processar o repositório
                if agent_orm.repository:
                    repo_orm = agent_orm.repository
                    # Garantir que todos os campos necessários do modelo Repository estejam presentes
                    repo_dict = {
                        "id": repo_orm.id,
                        "owner_id": repo_orm.user_id,  # Mapeamento de user_id para owner_id
                        "name": "default_name" if not hasattr(repo_orm, "name") else repo_orm.name,
                        "full_name": "default_full_name" if not hasattr(repo_orm, "full_name") else repo_orm.full_name,
                        "private": False if not hasattr(repo_orm, "private") else repo_orm.private,
                        "url": "default_url" if not hasattr(repo_orm, "url") else repo_orm.url,
                        "created_at": repo_orm.created_at,
                        "agents": [],
                        "branches": [],
                        "webhooks": []
                    }
                    repository = Repository(**repo_dict)
                else:
                    repository = None

                # Processar o modelo de IA
                if agent_orm.ai_model:
                    ai_model_orm = agent_orm.ai_model
                    ai_model_dict = {k: v for k, v in ai_model_orm.__dict__.items() if not k.startswith('_')}

                    # Ajustar o campo specialties se necessário
                    if hasattr(ai_model_orm, "specialties_us") and not hasattr(ai_model_orm, "specialties"):
                        ai_model_dict["specialties"] = ai_model_orm.specialties_us
                    elif not hasattr(ai_model_orm, "specialties"):
                        ai_model_dict["specialties"] = ""

                    ai_model = AIModel(**ai_model_dict)
                else:
                    ai_model = None

                # Criar o agente com seus relacionamentos
                agent_dict["repository"] = repository
                agent_dict["ai_model"] = ai_model
                agent = Agent(**agent_dict)

                # Adicionar o agente à operação
                operation_dict["agent"] = agent
            else:
                operation_dict["agent"] = None

            # Criar a operação e adicioná-la à lista
            operation = Operation(**operation_dict)
            operations.append(operation)

        return ListOperationsResponse(
            message="Operations retrieved successfully." if operations else "No operations found.",
            operations=operations
        )
    except Exception as error:
        raise error
    finally:
        db.close_session()