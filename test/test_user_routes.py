import pytest
from datetime import datetime, UTC
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from entities import User, UserSettings
from helpers.enums import AIModelProvider

client = TestClient(app)

# Mock user para testes
mock_user = User(
    id=1,
    provider="github",
    provider_id=12345,
    name="Test User",
    username="testuser",
    email="test@example.com",
    avatar_url="https://example.com/avatar.jpg",
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
    settings=UserSettings(
        id=1,
        user_id=1,
        email_notifications=True,
        telegram_notifications=False,
        daily_limit=5.0,
        weekly_limit=25.0,
        monthly_limit=100.0,
        alert_threshold=80
    )
)


class TestUserRoutes:
    """Testes para as rotas de usuário"""

    @patch('routes.user.user_routes.get_current_active_user')
    def test_get_user_success(self, mock_get_user):
        """Teste de caixa preta: GET /user - sucesso"""
        mock_get_user.return_value = mock_user

        response = client.get("/user/", headers={"Authorization": "Bearer fake-token"})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User information retrieved successfully."
        assert data["user"]["email"] == "test@example.com"

    def test_get_user_unauthorized(self):
        """Teste de caixa preta: GET /user - não autorizado"""
        response = client.get("/user/")
        assert response.status_code == 401

    @patch('routes.user.user_routes.get_current_active_user')
    @patch('routes.user.user_routes.Database')
    def test_delete_user_success(self, mock_db, mock_get_user):
        """Teste de caixa branca: DELETE /user - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_user_orm = MagicMock()
        mock_user_orm.deleted = False

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user_orm

        response = client.delete("/user/", headers={"Authorization": "Bearer fake-token"})

        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully."
        assert mock_user_orm.deleted == True
        mock_session.commit.assert_called_once()

    @patch('routes.user.user_routes.get_current_active_user')
    @patch('routes.user.user_routes.Database')
    def test_update_user_success(self, mock_db, mock_get_user):
        """Teste de caixa branca: PUT /user - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_user_orm = MagicMock()
        mock_settings_orm = MagicMock()

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_user_orm, mock_settings_orm
        ]

        update_data = {
            "user": {"name": "Updated Name"},
            "user_settings": {"daily_limit": 10.0}
        }

        response = client.put(
            "/user/",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "User updated successfully."
        mock_session.commit.assert_called_once()

    @patch('routes.user.user_routes.get_current_active_user')
    @patch('routes.user.user_routes.Database')
    def test_create_secret_key_success(self, mock_db, mock_get_user):
        """Teste de caixa preta: POST /user/provider/secret-key - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        secret_data = {
            "provider": "OPENAI",
            "secret_key": "sk-test123"
        }

        response = client.post(
            "/user/provider/secret-key",
            json=secret_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 201
        assert "Secret key created successfully" in response.json()["message"]

    @patch('routes.user.user_routes.get_current_active_user')
    @patch('routes.user.user_routes.Database')
    def test_create_secret_key_already_exists(self, mock_db, mock_get_user):
        """Teste de caixa preta: POST /user/provider/secret-key - chave já existe"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_existing_key = MagicMock()
        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_existing_key

        secret_data = {
            "provider": "OPENAI",
            "secret_key": "sk-test123"
        }

        response = client.post(
            "/user/provider/secret-key",
            json=secret_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch('routes.user.user_routes.get_current_active_user')
    @patch('routes.user.user_routes.Database')
    def test_get_secret_keys_success(self, mock_db, mock_get_user):
        """Teste de caixa preta: GET /user/provider/secret-key - sucesso"""
        mock_get_user.return_value = mock_user

        # Mock do banco de dados
        mock_session = MagicMock()
        mock_key = MagicMock()
        mock_key.__dict__ = {
            "provider": AIModelProvider.OPENAI,
            "secret_key": "sk-test123"
        }

        mock_db.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_key]

        response = client.get(
            "/user/provider/secret-key",
            headers={"Authorization": "Bearer "}
        )

        assert response.status_code == 200
        assert "Secret keys retrieved successfully" in response.json()["message"]
