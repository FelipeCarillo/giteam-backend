import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status

from infra.database import Database
from infra.api_github import APIGithub

from entities import Repository, User, Agent, RepositoryWebhook

from models import (Repository as RepositoryORM, Agent as AgentORM, RepositoryWebhook as RepositoryWebhookORM,
                    Branch as BranchORM)

from helpers.enums import AgentFunction
from helpers.errors import handle_exceptions
from helpers.auth import get_current_active_user, oauth2_scheme

from schemas.http import ResponseModel
from schemas.repository import ListRepositoryResponse, CreateRepositoryRequest, CreateAgentRequest, \
    ListRepositoryAvailableResponse, AvailableRepositoryResponse, RepositoryResponse

repositories_router = APIRouter(
    prefix="/repositories",
    tags=["Reporitories"],
)


@handle_exceptions
@repositories_router.get(
    "/repo/{repository_id}",
    name="Get Repository",
    description="Get a repository by ID.",
    status_code=status.HTTP_200_OK,
    response_model=RepositoryResponse,
)
async def get_repository(
        repository_id: int,
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user),
):
    """Get a repository by ID."""
    db = Database()
    session = db.get_session()

    try:
        repository_orm = session.query(RepositoryORM).filter(
            RepositoryORM.id == repository_id,
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).first()

        if not repository_orm:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Repository not found."
            )

        repository = await APIGithub.get_repository(
            token,
            repo_id=repository_orm.id,
            branches_name=[branch.name for branch in repository_orm.branches],
        )
        repository.agents = [
            Agent(**agent.__dict__, repository=None, operations=[])
            for agent in repository_orm.agents
        ]
        repository.webhooks = [
            RepositoryWebhook(**webhook.__dict__, repository=None)
            for webhook in repository_orm.webhooks
        ]

        return RepositoryResponse(message="Repository retrieved successfully.", repository=repository)
    except Exception as error:
        raise error
    finally:
        db.close_session()


@handle_exceptions
@repositories_router.get(
    "/",
    name="List Repositories",
    description="List all repositories.",
    status_code=status.HTTP_200_OK,
    response_model=ListRepositoryResponse,
)
async def list_repositories(
        token: str = Depends(oauth2_scheme),
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
            return []

        repositories = []
        for repo in repositories_orm:
            repository = await APIGithub.get_repository(
                token,
                repo_id=repo.id,
                branches_name=[branch.name for branch in repo.branches],
            )
            repository.created_at = repo.created_at
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
    except Exception as error:
        raise error
    finally:
        db.close_session()


@handle_exceptions
@repositories_router.get(
    "/available",
    name="List Available Repositories",
    description="List all available repositories.",
    status_code=status.HTTP_200_OK,
    response_model=ListRepositoryAvailableResponse,
)
async def list_available_repositories(
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user),
):
    """List all available repositories."""
    db = Database()
    session = db.get_session()

    try:

        repositories_github = await APIGithub.get_repositories_infos(token)
        if not repositories_github:
            return ListRepositoryAvailableResponse(
                message="No repositories found.",
                repositories=[]
            )

        repositories_orm = session.query(RepositoryORM).filter(
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).all()

        repositories = []
        for repo in repositories_github:
            repo_orm = next((r for r in repositories_orm if r.id == repo["id"]), None)
            if repo_orm and (len(repo_orm.agents) == 2 or repo_orm.agents[0].function == AgentFunction.BOTH):
                continue
            repositories.append(
                AvailableRepositoryResponse(
                    id=repo['id'],
                    name=repo['name'],
                    url=repo['url'],
                )
            )

        return ListRepositoryAvailableResponse(
            message="Repositories listed successfully.",
            repositories=repositories
        )
    except Exception as error:
        raise error
    finally:
        db.close_session()


@handle_exceptions
@repositories_router.post(
    "/",
    name="Create Repository",
    description="Create a new repository.",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseModel
)
async def create_repository(
        body: CreateRepositoryRequest,
        token: str = Depends(oauth2_scheme),
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Repository not found on GitHub."
            )

        user_has_access = await APIGithub.check_user_repo_access(
            token,
            repo_id=body.id,
            user_id=current_user.provider_id
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
                ai_model_id=agent.ai_model_id,
                created_by_id=current_user.id,
                updated_by_id=current_user.id,
            )
            for agent in body.agents
        ]

        branches = [
            BranchORM(name=branch, repository_id=body.id, created_by_id=current_user.id)
            for branch in body.branches
        ]

        repository = RepositoryORM(
            id=body.id,
            user_id=current_user.id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            agents=agents,
            branches=branches,
        )

        for agent in agents:
            webhooks += await APIGithub.create_webhooks(
                token,
                repo_id=repository.id,
                agent_function=agent.function
            )
        for webhook in webhooks:
            webhook_orm = RepositoryWebhookORM(
                id=webhook.id,
                repository_id=repository.id
            )
            repository.webhooks.append(webhook_orm)

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


@handle_exceptions
@repositories_router.delete(
    "/{repository_id}",
    name="Delete Repository",
    description="Delete a repository.",
    status_code=status.HTTP_200_OK,
    response_model=ResponseModel
)
async def delete_repository(
        repository_id: int,
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user),
):
    """Delete a repository."""
    db = Database()
    session = db.get_session()

    try:
        repository_orm = session.query(RepositoryORM).filter(
            RepositoryORM.id == repository_id,
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).first()

        if not repository_orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found."
            )

        for webhook in repository_orm.webhooks:
            await APIGithub.delete_webhook(
                token,
                repo_id=repository_orm.id,
                webhook_id=webhook.id
            )

        repository_orm.deleted = True
        session.commit()

        logging.info(f"Repository {repository_id} deleted from the database.")

        return ResponseModel(message="Repository deleted successfully.")
    except Exception as error:
        raise error
    finally:
        db.close_session()


@handle_exceptions
@repositories_router.post(
    "/{repository_id}/agents",
    name="Add Agent to Repository",
    description="Add an agent to a repository.",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseModel
)
async def add_agent_to_repository(
        repository_id: int,
        body: CreateAgentRequest,
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user),
):
    """Add an agent to a repository."""
    db = Database()
    session = db.get_session()

    try:
        repository_orm = session.query(RepositoryORM).filter(
            RepositoryORM.id == repository_id,
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).first()

        if not repository_orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found."
            )

        agent_exists = session.query(AgentORM).filter(
            AgentORM.name == body.name,
            AgentORM.repository_id == repository_id
        ).first()
        if agent_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent already exists in this repository."
            )

        if body.function == AgentFunction.BOTH and len(repository_orm.agents) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent function 'BOTH' cannot be used with other functions."
            )
        functions = [agent.function for agent in repository_orm.agents]
        if body.function in functions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent function must be unique."
            )

        agent = AgentORM(
            name=body.name,
            function=body.function,
            response_length=body.response_length,
            ai_model_id=body.ai_model_id,
            repository_id=repository_orm.id
        )

        webhooks = await APIGithub.create_webhooks(
            token,
            repo_id=repository_orm.id,
            agent_function=body.function
        )

        for webhook in webhooks:
            webhook_orm = RepositoryWebhookORM(
                id=webhook.id,
                url=webhook.url,
                events=webhook.events,
                active=webhook.active,
                agent_id=agent.id
            )
            repository_orm.webhooks.append(webhook_orm)

        repository_orm.agents.append(agent)
        session.commit()

        return ResponseModel(message="Agent added successfully.")
    except Exception as error:
        raise error
    finally:
        db.close_session()


@handle_exceptions
@repositories_router.patch(
    "/{repository_id}",
    name="Activate/Deactivate Repository",
    description="Activate or deactivate a repository.",
    status_code=status.HTTP_200_OK,
    response_model=ResponseModel
)
async def activate_deactivate_repository(
        repository_id: int,
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user),
):
    """Activate or deactivate a repository."""
    db = Database()
    session = db.get_session()

    try:
        repository_orm = session.query(RepositoryORM).filter(
            RepositoryORM.id == repository_id,
            RepositoryORM.created_by_id == current_user.id,
            RepositoryORM.deleted == False
        ).first()

        if not repository_orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found."
            )

        repository_orm.active = not repository_orm.active
        session.commit()

        for webhook in repository_orm.webhooks:
            await APIGithub.change_status_webhook(
                token,
                repo_full_name=repository_orm.full_name,
                webhook_id=webhook.id,
            )

        if repository_orm.active:
            logging.info(f"Repository {repository_orm.id} activated.")
        else:
            logging.info(f"Repository {repository_orm.id} deactivated.")

        return ResponseModel(message="Repository status changed successfully.")
    finally:
        db.close_session()
