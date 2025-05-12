import os

from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel


class Env(BaseModel):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Github OAuth
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/callback/github")
    GITHUB_SCOPE: str = os.getenv("GITHUB_SCOPE", "user,repo")

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")

    # API URL
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Agent Webhook
    AGENT_WEBHOOK_URL: str = os.getenv("AGENT_WEBHOOK_URL")


env = Env()
