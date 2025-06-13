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

    # QUEUE_URL
    QUEUE_URL: str = os.getenv("QUEUE_URL")

    # Agent Webhook
    AGENT_WEBHOOK_URL: str = os.getenv("AGENT_WEBHOOK_URL")


env = Env()
