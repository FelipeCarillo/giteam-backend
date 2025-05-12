from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from helpers.enums import AIModelProvider, AgentFunction, AgentResponseLength


class User(BaseModel):
    """Pydantic model corresponding to User SQLAlchemy model."""
    id: Optional[int] = None
    provider: str
    name: str
    username: str
    email: EmailStr
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    settings: Optional["UserSettings"] = None

    class Config:
        from_attributes = True


class UserSettings(BaseModel):
    """Pydantic model corresponding to UserSettings SQLAlchemy model."""
    id: Optional[int] = None
    user_id: int
    email_notifications: bool = True
    telegram_notifications: bool = False
    telegram_chat_id: Optional[str] = None
    daily_limit: float = 5.0
    weekly_limit: float = 25.0
    monthly_limit: float = 100.0
    alert_threshold: int = 80
    daily_limit_action: str = "notify_only"
    weekly_limit_action: str = "notify_only"
    monthly_limit_action: str = "disable_agents"

    class Config:
        from_attributes = True


class Repository(BaseModel):
    """Pydantic model corresponding to Repository SQLAlchemy model."""
    id: Optional[int] = None
    owner_id: int

    name: str
    full_name: str
    private: bool
    url: str

    created_at: Optional[datetime] = None

    agents: List["Agent"] = []
    branches: List["Branch"] = []
    webhooks: List["RepositoryWebhook"] = []

    class Config:
        from_attributes = True


class Branch(BaseModel):
    """Pydantic model corresponding to Branch SQLAlchemy model."""
    id: Optional[int] = None
    name: str
    repository_id: int

    # Relationships
    repository: Optional[Repository] = None
    agents: List["Agent"] = []

    class Config:
        from_attributes = True


class AIModel(BaseModel):
    """Pydantic model corresponding to AIModel SQLAlchemy model."""
    id: Optional[int] = None
    name: str
    provider: AIModelProvider
    prompt_token_cost: float
    completion_token_cost: float
    specialties: Optional[str] = None
    active: bool = True

    # Relationships
    agents: List["Agent"] = []

    class Config:
        from_attributes = True


class ProviderSecretKey(BaseModel):
    """Pydantic model corresponding to ProviderSecretKey SQLAlchemy model."""
    id: Optional[int] = None
    provider: AIModelProvider
    secret_key: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Agent(BaseModel):
    """Pydantic model corresponding to Agent SQLAlchemy model."""
    id: Optional[int] = None
    name: str
    function: AgentFunction
    repository_id: int
    ai_model_id: int
    response_length: AgentResponseLength
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships
    repository: Optional[Repository] = None
    ai_model: Optional[AIModel] = None
    operations: List["Operation"] = []

    class Config:
        from_attributes = True


class Operation(BaseModel):
    """Pydantic model corresponding to Operation SQLAlchemy model."""
    id: Optional[int] = None
    agent_id: int
    action: str
    details: Optional[str] = None
    github_reference: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: float
    status: str = "completed"
    execution_time: Optional[float] = None
    created_at: Optional[datetime] = None

    # Relationships
    agent: Optional[Agent] = None

    class Config:
        from_attributes = True


class CostHistory(BaseModel):
    """Pydantic model corresponding to CostHistory SQLAlchemy model."""
    id: Optional[int] = None
    user_id: int
    month: str
    pr_cost: float = 0.0
    issue_cost: float = 0.0
    total_cost: float = 0.0
    model_costs: Optional[str] = None
    repository_costs: Optional[str] = None

    # Relationships
    user: Optional[User] = None


    class Config:
        from_attributes = True


class RepositoryWebhook(BaseModel):
    """Pydantic model corresponding to RepositoryWebhook SQLAlchemy model."""
    id: int
    repository_id: int
    secret: Optional[str] = None
    events: str
    active: bool = True
    created_at: Optional[datetime] = None

    # Relationships
    repository: Optional[Repository] = None

    class Config:
        from_attributes = True
