from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status

from entities.entities import Operation, User
from models.models import Operation as OperationORM

from infra.database import Database

from helpers.auth import get_current_active_user
from schemas.operation.schemas import ListOperationsResponse

operation_router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)

@operation_router.get("/", status_code=status.HTTP_200_OK, response_model=ListOperationsResponse)
async def get_operations(
    agent_id: int = None,
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
            return JSONResponse(status_code=204, content={"message": "No operations found."})

        operations = [Operation(**operation.__dict__) for operation in operations]

        return JSONResponse(status_code=200, content={"operations": operations})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()