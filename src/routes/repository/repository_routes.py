import logging
from typing import List

from starlette.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Depends, status

from helpers.enums import AgentFunction
from infra.database import Database
from infra.api_github import APIGithub

from entities import Repository, User, Agent, RepositoryWebhook
from models import Repository as RepositoryORM, Agent as AgentORM

from helpers.errors import handle_exceptions
from helpers.auth import get_current_active_user, get_auth_token
from schemas.http import ResponseModel
from schemas.repository import ListRepositoryResponse, CreateRepositoryRequest

repositories_router = APIRouter(
    prefix="/repositories",
    tags=["Reporitories"],
)


@repositories_router.get(
    "/",
    name="List Repositories",
    description="List all repositories.",
    status_code=status.HTTP_200_OK,
    response_model=List[Repository],
)
@handle_exceptions
async def list_repositories(
        token: str = Depends(get_auth_token),
        current_user: User = Depends(get_current_active_user),
):
    """List all repositories."""
    db = Database()
    session = db.get_session()

    try:
        repositories_orm = session.query(RepositoryORM).filter(
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).all()

        if not repositories_orm:
            return JSONResponse(status_code=204, content={"message": "No repositories found."})

        repositories = []
        for repo in repositories_orm:
            repository = await APIGithub.get_repository(
                token,
                repo_id=repo.id,
                branches_name=[branch.name for branch in repo.branches],
            )
            repository.agents = [
                Agent(**agent.__dict__, repository=None, operations=[])
                for agent in repo.agents
            ]
            repository.webhooks = [
                RepositoryWebhook(**webhook.__dict__, repository=None)
                for webhook in repo.webhooks
            ]
            repositories.append(repository)

        return ListRepositoryResponse(
            message="Repositories listed successfully.",
            repositories=repositories
        )
    finally:
        db.close_session()


@repositories_router.post(
    "/",
    name="Create Repository",
    description="Create a new repository.",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseModel
)
@handle_exceptions
async def create_repository(
        body: CreateRepositoryRequest,
        token: str = Depends(get_auth_token),
        current_user: User = Depends(get_current_active_user),
):
    """Create a new repository."""
    db = Database()
    session = db.get_session()
    webhooks = []

    try:
        if not body.agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one agent is required."
            )

        repository_exists = await APIGithub.check_repository_exists(
            token,
            repo_id=body.id
        )
        if not repository_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found on GitHub."
            )

        user_has_access = await APIGithub.check_user_repo_access(
            token,
            repo_id=body.id,
            user_id=current_user.id
        )
        if not user_has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this repository."
            )

        functions = [agent.function for agent in body.agents]
        if len(functions) != len(set(functions)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent functions must be unique."
            )
        if any(function == AgentFunction.BOTH for function in functions) and len(functions) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent function 'BOTH' cannot be used with other functions."
            )

        repository_exists = session.query(RepositoryORM).filter(
            RepositoryORM.id == body.id,
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).first()
        if repository_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Repository already exists."
            )

        agents = [
            AgentORM(
                name=agent.name,
                function=agent.function,
                response_length=agent.response_length,
                ai_model_id=agent.ai_model_id
            )
            for agent in body.agents
        ]

        repository = RepositoryORM(
            id=body.id,
            name=body.name,
            full_name=body.full_name,
            private=body.private,
            url=body.url,
            owner_id=current_user.id,
            agents=agents
        )

        for agent in agents:
            webhooks += await APIGithub.create_webhooks(
                token,
                repo_id=repository.id,
                agent_function=agent.function
            )
        repository.webhooks = webhooks

        session.add(repository)
        session.commit()
        session.refresh(repository)

        logging.info(f"Repository {repository.id} added to the database.")

        return ResponseModel(message="Repository created successfully.")
    except Exception as error:
        if webhooks:
            for webhook in webhooks:
                await APIGithub.delete_webhook(
                    token,
                    repo_id=body.id,
                    webhook_id=webhook.id
                )
        session.rollback()
        raise error
    finally:
        db.close_session()
