from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from infra.api_github import APIGithub
from helpers.enums import AgentFunction, AgentResponseLength

client = TestClient(app)

# Mock user para testes
TOKEN = ""
mock_user = APIGithub.get_user_info(TOKEN)


class TestAgentRoutes:
    """Testes para as rotas de agentes"""

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_update_agent_success(self, mock_db, mock_get_user):
        """Teste de caixa branca: PUT /agents/{id} - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_agent_orm = MagicMock()
        mock_agent_orm.id = 1
        mock_agent_orm.name = "Old Agent Name"
        mock_agent_orm.active = True

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_agent_orm

        update_data = {
            "name": "Updated Agent Name",
            "active": False,
            "response_length": "detailed"
        }

        response = client.put(
            "/agents/1",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Agent updated successfully."
        assert mock_agent_orm.name == "Updated Agent Name"
        assert mock_agent_orm.active == False
        mock_session.commit.assert_called_once()

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_update_agent_not_found(self, mock_db, mock_get_user):
        """Teste de caixa preta: PUT /agents/{id} - não encontrado"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        update_data = {"name": "Updated Agent Name"}

        response = client.put(
            "/agents/999",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 204

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_delete_agent_success(self, mock_db, mock_get_user):
        """Teste de caixa branca: DELETE /agents/{id} - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_agent_orm = MagicMock()
        mock_agent_orm.id = 1
        mock_agent_orm.deleted = False

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_agent_orm

        response = client.delete(
            "/agents/1",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Agent updated successfully."
        assert mock_agent_orm.deleted == True
        mock_session.commit.assert_called_once()

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_delete_agent_not_found(self, mock_db, mock_get_user):
        """Teste de caixa preta: DELETE /agents/{id} - não encontrado"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        response = client.delete(
            "/agents/999",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 204

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_get_agents_success(self, mock_db, mock_get_user):
        """Teste de caixa preta: GET /agents/{id} - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_agent1 = MagicMock()
        mock_agent1.__dict__ = {
            "id": 1,
            "name": "Agent 1",
            "function": AgentFunction.PR_REVIEW,
            "active": True
        }
        mock_agent2 = MagicMock()
        mock_agent2.__dict__ = {
            "id": 2,
            "name": "Agent 2",
            "function": AgentFunction.ISSUE_RESOLUTION,
            "active": False
        }

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_agent1, mock_agent2]

        response = client.get(
            "/agents/1",  # Note: a rota parece ter um bug, deveria ser apenas /agents
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 2

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_get_agents_empty(self, mock_db, mock_get_user):
        """Teste de caixa preta: GET /agents/{id} - lista vazia"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        response = client.get(
            "/agents/1",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 0

    def test_update_agent_unauthorized(self):
        """Teste de caixa preta: PUT /agents/{id} - não autorizado"""
        update_data = {"name": "Updated Agent Name"}

        response = client.put("/agents/1", json=update_data)
        assert response.status_code == 401

    def test_delete_agent_unauthorized(self):
        """Teste de caixa preta: DELETE /agents/{id} - não autorizado"""
        response = client.delete("/agents/1")
        assert response.status_code == 401

    @patch('routes.agent.agent_routes.get_current_active_user')
    @patch('routes.agent.agent_routes.Database')
    def test_update_agent_partial_update(self, mock_db, mock_get_user):
        """Teste de caixa branca: PUT /agents/{id} - atualização parcial"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_agent_orm = MagicMock()
        mock_agent_orm.id = 1
        mock_agent_orm.name = "Original Name"
        mock_agent_orm.active = True
        mock_agent_orm.response_length = AgentResponseLength.MEDIUM
        mock_agent_orm.ai_model_id = 1

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_agent_orm

        # Atualizar apenas o nome
        update_data = {"name": "New Name"}

        response = client.put(
            "/agents/1",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert mock_agent_orm.name == "New Name"
        assert mock_agent_orm.active == True  # Não deve ter mudado
        assert mock_agent_orm.ai_model_id == 1  # Não deve ter mudado
        mock_session.commit.assert_called_once()
