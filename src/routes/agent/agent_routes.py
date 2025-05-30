from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from entities import User
from models import Agent as AgentORM
from schemas.agent.schemas import UpdateAgent
from helpers.auth import get_current_active_user

from infra.database import Database

agent_router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@agent_router.put(
    "/{agent_id}",
    name="Update Agent",
    description="Update a specific agent.",
)
async def update_agent(
        agent_id: int,
        agent: UpdateAgent,
        current_user: User = Depends(get_current_active_user),
        # nossa rota depende de chamar essa função que pega o usuário atual
):
    """Update an agent."""
    db = Database()
    session = db.get_session()

    try:
        agent_orm = session.query(AgentORM).filter(
            AgentORM.id == agent_id and
            AgentORM.created_by_id == current_user.id and
            AgentORM.deleted == False
        ).first()
        if not agent_orm:
            return JSONResponse(status_code=204, content={"message": "Agent not found."})

        # Update the agent
        for key, value in agent.model_dump().items():
            setattr(agent_orm, key, value)

        session.commit()

        return JSONResponse(status_code=200, content={"message": "Agent updated successfully."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()


@agent_router.delete(
    "/{agent_id}",
    name="Delete Agent",
    description="Delete a specific agent.",
)
async def delete_agent(
        agent_id: int,
        current_user: User = Depends(get_current_active_user),
):
    """Deletes an agent."""
    db = Database()
    session = db.get_session()

    try:
        agent_orm = session.query(AgentORM).filter(
            AgentORM.id == agent_id and
            AgentORM.created_by_id == current_user.id and
            AgentORM.deleted == False
        ).first()
        if not agent_orm:
            return JSONResponse(status_code=204, content={"message": "Agent not found."})

        # delete agent
        setattr(agent_orm, "deleted", True)

        session.commit()

        return JSONResponse(status_code=200, content={"message": "Agent updated successfully."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()

@agent_router.get(
    "/{agent_id}",
    name="Get Agents",
    description="Get all agents for the current user.",
)
async def get_agents(
        current_user: User = Depends(get_current_active_user),
):
    """Get all agents for the current user."""
    db = Database()
    session = db.get_session()

    try:
        agents_orm = session.query(AgentORM).filter(
            AgentORM.created_by_id == current_user.id and
            AgentORM.deleted == False
        ).all()

        return JSONResponse(status_code=200, content={"agents": [agent.__dict__ for agent in agents_orm]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Internal server error.", "error": str(e)})
    finally:
        db.close_session()