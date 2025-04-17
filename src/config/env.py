import os
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel


class Env(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL")

env = Env()