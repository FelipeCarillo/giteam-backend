from fastapi import APIRouter
from fastapi.responses import JSONResponse

from entities.entities import Agent
from models.models import Agent as AgentORM
from schemas.agent.agent_schemas import UpdateAgent

from infra.database import Database

agent_router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@agent_router.put(
    "/{agent_id}",
    name="Agents",
    description="List all agents",
)
async def update_agent(
        agent_id: int,
        agent: UpdateAgent,
):
    """Update an agent."""
    db = Database()
    session = db.get_session()

    try:
        agent_orm = session.query(AgentORM).filter(
            AgentORM.id == agent_id and
            AgentORM.created_by == agent.created_by
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
