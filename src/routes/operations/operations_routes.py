from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

from entities import Operation, User
from models import Operation as OperationORM

from infra.database import Database

from helpers.auth import get_current_active_user
from schemas.operations.schemas import ListOperationsResponse

operation_router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


@operation_router.get("/", status_code=status.HTTP_200_OK, response_model=ListOperationsResponse)
async def get_operations(
        agent_id: Optional[int] = None,
        _: User = Depends(get_current_active_user),
):
    """List all operations, optionally filtered by agent_id."""
    db = Database()
    session = db.get_session()

    try:
        query = session.query(OperationORM)
        if agent_id:
            query = query.filter(OperationORM.agent_id == agent_id)

        operations = query.all()
        if not operations:
            # Retorna um objeto vazio em vez de uma resposta JSON
            return ListOperationsResponse(operations=[])

        # Converte explicitamente para dicionários básicos antes de passar para o modelo Pydantic
        operation_dicts = []
        for op in operations:
            op_dict = {
                "id": op.id,
                "agent_id": op.agent_id,
                "action": op.action,
                "details": op.details,
                "github_reference": op.github_reference,
                "prompt_tokens": op.prompt_tokens,
                "completion_tokens": op.completion_tokens,
                "total_tokens": op.total_tokens,
                "cost": op.cost,
                "status": op.status,
                "execution_time": op.execution_time,
                "created_at": op.created_at
            }
            operation_dicts.append(op_dict)

        # Cria instâncias Pydantic usando os dicionários
        pydantic_operations = [Operation.model_validate(op_dict) for op_dict in operation_dicts]

        # Retorna o objeto de resposta diretamente em vez de JSONResponse
        return ListOperationsResponse(operations=pydantic_operations)

    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()