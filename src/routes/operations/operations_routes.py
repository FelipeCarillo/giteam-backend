# from fastapi.responses import JSONResponse
# from fastapi import APIRouter, HTTPException, Depends, status
#
# from entities import Operation, User
# from models import Operation as OperationORM
#
# from infra.database import Database
#
# from helpers.auth import get_current_active_user
# from schemas.operations.schemas import ListOperationsResponse
#
# operation_router = APIRouter(
#     prefix="/operations",
#     tags=["Operations"],
# )
#
#
# @operation_router.get("/", status_code=status.HTTP_200_OK, response_model=ListOperationsResponse)
# async def get_operations(
#         agent_id: int = None,
#         _: User = Depends(get_current_active_user),
# ):
#     """List all operations, optionally filtered by agent_id."""
#     db = Database()
#     session = db.get_session()
#
#     try:
#         query = session.query(OperationORM)
#         if agent_id:
#             query = query.filter(OperationORM.agent_id == agent_id)
#
#         operations = query.all()
#         if not operations:
#             return JSONResponse(status_code=204, content={"message": "No operations found."})
#
#         operations = [Operation(**operation.__dict__) for operation in operations]
#
#         return JSONResponse(status_code=200, content={"operations": operations})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail={"message": "Internal server error.", "error": str(e)})
#     finally:
#         db.close_session()


from fastapi import APIRouter, Depends, status
from typing import Optional

from entities import Operation, User, Agent
from models import Operation as OperationORM

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
        query = session.query(OperationORM)
        if agent_id:
            query = query.filter(OperationORM.agent_id == agent_id)

        operations_orm = query.all()
        operations = [Operation(**operation.__dict__) for operation in operations_orm]

        return ListOperationsResponse(
            message="Operations retrieved successfully." if operations else "No operations found.",
            operations=operations
        )
    except Exception as error:
        return error
    finally:
        db.close_session()