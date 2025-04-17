from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """Pydantic model corresponding to User SQLAlchemy model."""
    id: Optional[int] = None
    username: str
    email: EmailStr
    github_token: Optional[str] = None
    created_at: Optional[datetime] = None

    # Relationships - will be populated when needed
    repositories: List["Repository"] = []
    settings: Optional["UserSettings"] = None
    cost_history: List["CostHistory"] = []

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
    language: str = "en-US"
    theme: str = "light"

    # Relationships
    user: Optional[User] = None

    class Config:
        from_attributes = True


class Repository(BaseModel):
    """Pydantic model corresponding to Repository SQLAlchemy model."""
    id: Optional[int] = None
    name: str
    github_id: str
    link: str
    user_id: int
    created_at: Optional[datetime] = None

    # Relationships
    user: Optional[User] = None
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
    provider: str
    prompt_token_cost: float
    completion_token_cost: float
    max_tokens: int
    specialties: Optional[str] = None
    active: bool = True

    # Relationships
    agents: List["Agent"] = []

    class Config:
        from_attributes = True


class Agent(BaseModel):
    """Pydantic model corresponding to Agent SQLAlchemy model."""
    id: Optional[int] = None
    name: str
    function: str
    repository_id: int
    ai_model_id: int
    active: bool = True
    response_length: str = "medium"
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
    id: Optional[int] = None
    repository_id: int
    webhook_id: str
    webhook_url: str
    webhook_secret: str
    events: str
    active: bool = True
    created_at: Optional[datetime] = None

    # Relationships
    repository: Optional[Repository] = None

    class Config:
        from_attributes = True