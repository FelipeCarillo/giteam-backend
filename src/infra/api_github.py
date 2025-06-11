import httpx
from typing import List, Union, Dict
from pydantic import EmailStr

from config.env import env
from helpers.enums import AgentFunction
from helpers.errors import handle_github_api_exceptions
from entities import Repository, Branch, RepositoryWebhook


class APIGithub:
    @staticmethod
    @handle_github_api_exceptions
    async def get_access_token(code: str, redirect_uri: str) -> str:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": env.GITHUB_CLIENT_ID,
                    "client_secret": env.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()

            token_data = token_response.json()

            return token_data["access_token"]

    @staticmethod
    @handle_github_api_exceptions
    async def get_user_info(token: str) -> dict:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
            )
            user_response.raise_for_status()

            github_user = user_response.json()

            return github_user

    @staticmethod
    @handle_github_api_exceptions
    async def get_user_primary_email(token: str) -> EmailStr:
        async with httpx.AsyncClient() as client:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {token}"},
            )
            emails_response.raise_for_status()

            emails = emails_response.json()
            primary_email = next((email["email"] for email in emails if email["primary"]), None)

            return primary_email

    @staticmethod
    @handle_github_api_exceptions
    async def check_repository_exists(token: str, repo_id: int) -> bool:
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/repositories/{repo_id}",
                headers={"Authorization": f"token {token}"},
            )
            if repo_response.status_code == 200:
                return True
            return False

    @staticmethod
    @handle_github_api_exceptions
    async def check_user_repo_access(token: str, user_id: int, repo_id: int) -> bool:
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/repositories/{repo_id}/collaborators",
                headers={"Authorization": f"token {token}"},
            )
            if repo_response.status_code == 200:
                collaborators = repo_response.json()
                for collaborator in collaborators:
                    if collaborator["id"] == user_id:
                        return True
            return False

    @staticmethod
    @handle_github_api_exceptions
    async def get_repo_full_name(token: str, repo_id: int) -> str:
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/repositories/{repo_id}",
                headers={"Authorization": f"token {token}"},
            )
            repo_response.raise_for_status()

            repo_json = repo_response.json()
            return repo_json["full_name"]

    @staticmethod
    @handle_github_api_exceptions
    async def get_repository(token: str, repo_id: int, branches_name: List[str]) -> Repository:
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/repositories/{repo_id}",
                headers={"Authorization": f"token {token}"},
            )
            repo_response.raise_for_status()

            repo_json = repo_response.json()

            repository = Repository(
                id=repo_json["id"],
                name=repo_json["name"],
                full_name=repo_json["full_name"],
                private=repo_json["private"],
                url=repo_json["html_url"],
                owner_id=repo_json["owner"]["id"],
            )

            branches = [
                await APIGithub.get_branch(token, repo_json["full_name"], branch_id)
                for branch_id in branches_name
            ]
            repository.branches = [
                Branch(name=branch, repository_id=repo_json["id"]) for branch in branches
            ]
            repository.webhooks = await APIGithub.get_webhooks(token, repository.id)

            return repository

    @staticmethod
    @handle_github_api_exceptions
    async def get_repositories_infos(token: str) -> List[Dict[str, Union[str, int]]]:
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/user/repos?affiliation=owner",
                headers={"Authorization": f"Bearer {token}"},
            )
            repo_response.raise_for_status()

            repo_json = repo_response.json()

            repositories = [
                {
                    "id": repo["id"],
                    "name": repo["name"],
                    "url": repo["html_url"],
                }
                for repo in repo_json
            ]
            return repositories

    @staticmethod
    @handle_github_api_exceptions
    async def get_user_repositories(token: str) -> List[Repository]:
        async with httpx.AsyncClient() as client:
            repos_response = await client.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {token}"},
            )
            repos_response.raise_for_status()

            repositories = repos_response.json()

            for repo in repositories:
                branches = await APIGithub.get_branches(token, repo["full_name"])
                repo["branches"] = [
                    Branch(name=branch, repository_id=repo["id"]) for branch in branches
                ]
                repo["webhooks"] = await APIGithub.get_webhooks(token, repo["full_name"])

            return repositories

    @staticmethod
    @handle_github_api_exceptions
    async def get_branch(token: str, repo_full_name: str, branch_name: str) -> str:
        async with httpx.AsyncClient() as client:
            branch_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/branches/{branch_name}",
                headers={"Authorization": f"token {token}"},
            )
            branch_response.raise_for_status()

            branch_json = branch_response.json()

            return branch_json["name"]

    @staticmethod
    @handle_github_api_exceptions
    async def get_branches(token: str, repo_full_name: str) -> List[str]:
        async with httpx.AsyncClient() as client:
            branches_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/branches",
                headers={"Authorization": f"token {token}"},
            )
            branches_response.raise_for_status()

            branches = branches_response.json()
            branch_names = [branch["name"] for branch in branches]

            return branch_names

    @staticmethod
    @handle_github_api_exceptions
    async def create_webhooks(
            token: str,
            repo_id: int,
            agent_function: AgentFunction
    ) -> List[RepositoryWebhook]:
        async with httpx.AsyncClient() as client:
            def generate_secret():
                import secrets
                return secrets.token_hex(16)

            if agent_function == AgentFunction.PR_REVIEW:
                events = ["pull_request"]
            elif agent_function == AgentFunction.ISSUE_RESOLUTION:
                events = ["issues"]
            else:
                events = ["pull_request", "issues"]

            webhooks = []
            repo_full_name = await APIGithub.get_repo_full_name(token, repo_id)

            for event in events:
                secret = generate_secret()
                webhook_response = await client.post(
                    f"https://api.github.com/repos/{repo_full_name}/hooks",
                    headers={"Authorization": f"token {token}"},
                    json={
                        "config": {
                            "url": env.AGENT_WEBHOOK_URL,
                            "content_type": "json",
                            "secret": secret
                        },
                        "events": [event],
                        "active": True,
                    },
                )
                webhook_response.raise_for_status()
                webhook_json = webhook_response.json()
                webhooks.append(
                    RepositoryWebhook(
                        id=webhook_json["id"],
                        repository_id=repo_id,
                        secret=secret,
                    )
                )
            return webhooks

    @staticmethod
    @handle_github_api_exceptions
    async def get_webhook(token: str, repo_full_name: str, webhook_id: int) -> RepositoryWebhook:
        async with httpx.AsyncClient() as client:
            webhook_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/hooks/{webhook_id}",
                headers={"Authorization": f"token {token}"},
            )
            webhook_response.raise_for_status()

            webhook_json = webhook_response.json()

            return RepositoryWebhook(
                id=webhook_json["id"],
                repository_id=webhook_json["config"].get("repository_id"),
                secret=webhook_json["config"].get("secret"),
            )

    @staticmethod
    @handle_github_api_exceptions
    async def get_webhooks(token: str, repo_id: int, with_secrets: bool = False) -> List[RepositoryWebhook]:
        async with httpx.AsyncClient() as client:
            full_name = await APIGithub.get_repo_full_name(token, repo_id)
            webhooks_response = await client.get(
                f"https://api.github.com/repos/{full_name}/hooks",
                headers={"Authorization": f"token {token}"},
            )
            webhooks_response.raise_for_status()

            webhooks_json = webhooks_response.json()

            webhooks = [
                RepositoryWebhook(
                    id=webhook["id"],
                    repository_id=repo_id,
                    secret=webhook["config"].get("secret") if with_secrets else None,
                )
                for webhook in webhooks_json
            ]
            return webhooks

    @staticmethod
    @handle_github_api_exceptions
    async def change_status_webhook(
            token: str,
            repo_full_name: str,
            webhook_id: int
    ) -> None:
        async with httpx.AsyncClient() as client:
            webhook_response = await APIGithub.get_webhook(token, repo_full_name, webhook_id)
            active = not webhook_response.active

            webhook_response = await client.patch(
                f"https://api.github.com/repos/{repo_full_name}/hooks/{webhook_id}",
                headers={"Authorization": f"token {token}"},
                json={
                    "active": active,
                },
            )
            webhook_response.raise_for_status()

    @staticmethod
    @handle_github_api_exceptions
    async def delete_webhook(token: str, repo_full_name: str, webhook_id: int) -> None:
        async with httpx.AsyncClient() as client:
            webhook_response = await client.delete(
                f"https://api.github.com/repos/{repo_full_name}/hooks/{webhook_id}",
                headers={"Authorization": f"token {token}"},
            )
            webhook_response.raise_for_status()
            return webhook_response.json()

    @staticmethod
    @handle_github_api_exceptions
    async def delete_all_webhooks(token: str, repo_id) -> None:
        webhooks_response = await APIGithub.get_webhooks(token, repo_id)
        repo_full_name = await APIGithub.get_repo_full_name(token, repo_id)
        for webhook in webhooks_response:
            await APIGithub.delete_webhook(token, repo_full_name, webhook.id)
