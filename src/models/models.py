from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, MetaData


class Base(DeclarativeBase):
    metadata = MetaData(schema='giteam')


class User(Base):
    """Modelo de usuário que representa uma conta no sistema GiTeam."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    github_token = Column(String)
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamentos
    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cost_history = relationship("CostHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}')>"


class UserSettings(Base):
    """Configurações e preferências do usuário."""
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Notificações
    email_notifications = Column(Boolean, default=True)
    telegram_notifications = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100))  # ID do chat do Telegram

    # Limites de custo
    daily_limit = Column(Float, default=5.0)
    weekly_limit = Column(Float, default=25.0)
    monthly_limit = Column(Float, default=100.0)
    alert_threshold = Column(Integer, default=80)  # percentual

    # Ações ao atingir limites (notify_only ou disable_agents)
    daily_limit_action = Column(String(20), default='notify_only')
    weekly_limit_action = Column(String(20), default='notify_only')
    monthly_limit_action = Column(String(20), default='disable_agents')

    # Preferências
    language = Column(String(10), default='en-US')
    theme = Column(String(10), default='light')

    # Relacionamentos
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"


class Repository(Base):
    """Repositório GitHub conectado à plataforma."""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    github_id = Column(String(50), nullable=False)
    link = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamentos
    user = relationship("User", back_populates="repositories")
    agents = relationship("Agent", back_populates="repository", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="repository", cascade="all, delete-orphan")
    webhooks = relationship("RepositoryWebhook", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(name='{self.name}')>"


class Branch(Base):
    """Branch de um repositório Git."""
    __tablename__ = 'branches'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)

    # Relacionamentos
    repository = relationship("Repository", back_populates="branches")

    def __repr__(self):
        return f"<Branch(name='{self.name}')>"


class AIModel(Base):
    """Modelo de IA disponível para uso nos agentes."""
    __tablename__ = 'ai_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    prompt_token_cost = Column(Float, nullable=False)  # Custo por token de prompt (entrada)
    completion_token_cost = Column(Float, nullable=False)  # Custo por token de completion (saída)
    max_tokens = Column(Integer, nullable=False)
    specialties = Column(String(255))  # Lista separada por vírgulas
    active = Column(Boolean, default=True)

    # Relacionamentos
    agents = relationship("Agent", back_populates="ai_model")

    def __repr__(self):
        return f"<AIModel(name='{self.name}', provider='{self.provider}')>"


class Agent(Base):
    """Agente de IA que executa tarefas em um repositório."""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    function = Column(String(50), nullable=False)  # 'PR Review', 'Issue Resolution', 'Both'
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    ai_model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    active = Column(Boolean, default=True)
    response_length = Column(String(20), default='medium')  # 'concise', 'medium', 'detailed'
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)  # ID do usuário que criou o agente
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_by = Column(Integer, ForeignKey('users.id'))  # ID do usuário que atualizou o agente
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Relacionamentos
    user = relationship("User", back_populates="agents")
    repository = relationship("Repository", back_populates="agents")
    ai_model = relationship("AIModel", back_populates="agents")
    operations = relationship("Operation", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent(name='{self.name}', function='{self.function}')>"


class Operation(Base):
    """Operação executada por um agente."""
    __tablename__ = 'operations'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    action = Column(String(100), nullable=False)  # 'PR Review', 'Issue Resolution'
    details = Column(String(255))
    github_reference = Column(String(100))  # Número do PR ou Issue
    prompt_tokens = Column(Integer)  # Tokens de entrada (prompt)
    completion_tokens = Column(Integer)  # Tokens de saída (resposta)
    total_tokens = Column(Integer)  # Total de tokens usados
    cost = Column(Float, nullable=False)
    status = Column(String(20), default='completed')  # 'pending', 'completed', 'failed'
    execution_time = Column(Float)  # em segundos
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamentos
    agent = relationship("Agent", back_populates="operations")

    def __repr__(self):
        return f"<Operation(action='{self.action}', cost='{self.cost}')>"


class CostHistory(Base):
    """Histórico de custos por mês."""
    __tablename__ = 'cost_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    month = Column(String(7), nullable=False)  # Formato: '2025-04'
    pr_cost = Column(Float, default=0.0)
    issue_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    # Detalhamento opcional
    model_costs = Column(Text)  # String JSON com detalhamento por modelo
    repository_costs = Column(Text)  # String JSON com detalhamento por repositório

    # Relacionamento
    user = relationship("User", back_populates="cost_history")

    def __repr__(self):
        return f"<CostHistory(month='{self.month}', total_cost='{self.total_cost}')>"


class RepositoryWebhook(Base):
    """Configuração de webhooks para um repositório."""
    __tablename__ = 'repository_webhooks'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    webhook_id = Column(String(50), nullable=False)  # ID do webhook no GitHub
    webhook_url = Column(String(255), nullable=False)  # URL de callback
    webhook_secret = Column(String(100), nullable=False)  # Secret para validação
    events = Column(String(255), nullable=False)  # pull_request,issues,etc.
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamento
    repository = relationship("Repository", back_populates="webhooks")

    def __repr__(self):
        return f"<RepositoryWebhook(id={self.id}, events='{self.events}')>"
