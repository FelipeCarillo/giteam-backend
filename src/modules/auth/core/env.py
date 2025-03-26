import os
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env"))


class AuthEnv(BaseModel):
    GITHUB_LOGIN_URL: str = os.getenv("AUTH_GITHUB_LOGIN_URL")
    GITHUB_CLIENT_ID: str = os.getenv("AUTH_GITHUB_CLIENT_ID")
    GITHUB_REDIRECT_URI: str = os.getenv("AUTH_GITHUB_REDIRECT_URI")
    GITHUB_CLIENT_SECRET: str = os.getenv("AUTH_GITHUB_CLIENT_SECRET")

AUTH_ENV = AuthEnv()
