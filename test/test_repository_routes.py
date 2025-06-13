from datetime import datetime, UTC
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import app
from infra.api_github import APIGithub
from entities import Repository

client = TestClient(app)

# Mock user para testes
TOKEN = ""
mock_user = APIGithub.get_user_info(token=TOKEN)

# Mock repository
mock_repository = Repository(
    id=123456,
    name="test-repo",
    full_name="testuser/test-repo",
    private=False,
    url="https://github.com/testuser/test-repo",
    owner_id=12345,
    created_at=datetime.now(UTC),
    agents=[],
    branches=[],
    webhooks=[]
)


class TestRepositoryRoutes:
    """Testes para as rotas de repositório"""

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    @patch('routes.repository.repository_routes.APIGithub.get_repository')
    async def test_get_repository_success(self, mock_get_repo, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa preta: GET /repositories/repo/{id} - sucesso"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_repo_orm = MagicMock()
        mock_repo_orm.id = 123456
        mock_repo_orm.branches = []
        mock_repo_orm.agents = []
        mock_repo_orm.webhooks = []

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_repo_orm

        # Mock da API do GitHub
        mock_get_repo.return_value = mock_repository

        response = client.get(
            "/repositories/repo/123456",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Repository retrieved successfully."
        assert data["repository"]["name"] == "test-repo"

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    def test_get_repository_not_found(self, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa preta: GET /repositories/repo/{id} - não encontrado"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        response = client.get(
            "/repositories/repo/999999",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 204

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    @patch('routes.repository.repository_routes.APIGithub.get_repositories_infos')
    async def test_list_available_repositories_success(self, mock_get_repos, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa branca: GET /repositories/available - sucesso"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock da API do GitHub
        mock_get_repos.return_value = [
            {"id": 123456, "name": "test-repo", "url": "https://github.com/testuser/test-repo"},
            {"id": 789012, "name": "another-repo", "url": "https://github.com/testuser/another-repo"}
        ]

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_repo_orm = MagicMock()
        mock_repo_orm.id = 123456
        mock_repo_orm.agents = []

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_repo_orm]

        response = client.get(
            "/repositories/available",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["repositories"]) >= 1
        assert data["message"] == "Repositories listed successfully."

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    @patch('routes.repository.repository_routes.APIGithub')
    async def test_create_repository_success(self, mock_api_github, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa branca: POST /repositories - sucesso"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock da API do GitHub
        mock_api_github.check_repository_exists = AsyncMock(return_value=True)
        mock_api_github.check_user_repo_access = AsyncMock(return_value=True)
        mock_api_github.create_webhooks = AsyncMock(return_value=[])

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        create_data = {
            "id": 123456,
            "branches": ["main", "develop"],
            "agents": [
                {
                    "name": "PR Agent",
                    "function": "pr_review",
                    "ai_model_id": 1,
                    "response_length": "medium"
                }
            ]
        }

        response = client.post(
            "/repositories/",
            json=create_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Repository created successfully."
        mock_session.commit.assert_called_once()

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    @patch('routes.repository.repository_routes.APIGithub')
    async def test_create_repository_no_agents(self, mock_api_github, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa preta: POST /repositories - sem agentes"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        create_data = {
            "id": 123456,
            "branches": ["main"],
            "agents": []
        }

        response = client.post(
            "/repositories/",
            json=create_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 400
        assert "At least one agent is required" in response.json()["detail"]

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    @patch('routes.repository.repository_routes.APIGithub.delete_webhook')
    async def test_delete_repository_success(self, mock_delete_webhook, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa preta: DELETE /repositories/{id} - sucesso"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_repo_orm = MagicMock()
        mock_repo_orm.id = 123456
        mock_repo_orm.deleted = False
        mock_repo_orm.webhooks = []

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_repo_orm

        response = client.delete(
            "/repositories/123456",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Repository deleted successfully."
        assert mock_repo_orm.deleted == True
        mock_session.commit.assert_called_once()

    @patch('routes.repository.repository_routes.get_current_active_user')
    @patch('routes.repository.repository_routes.oauth2_scheme')
    @patch('routes.repository.repository_routes.Database')
    def test_delete_repository_not_found(self, mock_db, mock_oauth, mock_get_user):
        """Teste de caixa preta: DELETE /repositories/{id} - não encontrado"""
        mock_get_user.return_value = mock_user
        mock_oauth.return_value = "fake-token"

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        response = client.delete(
            "/repositories/999999",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 404
        assert "Repository not found" in response.json()["detail"]
