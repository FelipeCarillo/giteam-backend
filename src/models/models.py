from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, MetaData, Enum

from helpers.enums import AuthProvider, AIModelProvider, AgentFunction, AgentResponseLength


class Base(DeclarativeBase):
    metadata = MetaData(schema='giteam')


class User(Base):
    """Modelo de usuário que representa uma conta no sistema GiTeam."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(Enum(AuthProvider), nullable=False)
    provider_id = Column(String, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    deleted = Column(Boolean, default=False)

    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserSettings(Base):
    """Configurações e preferências do usuário."""
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"


class Repository(Base):
    """Repositório GitHub conectado à plataforma."""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    created_by_id = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    deleted = Column(Boolean, default=False)

    # Relacionamentos adicionados
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    # Relacionamentos existentes
    agents = relationship("Agent", back_populates="repository")
    branches = relationship("Branch", back_populates="repository")
    webhooks = relationship("RepositoryWebhook", back_populates="repository")

    def __repr__(self):
        return f"<Repository(github_id='{self.github_id}', user_id='{self.user_id}')>"


class Branch(Base):
    """Branch de um repositório Git."""
    __tablename__ = 'branches'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    deleted = Column(Boolean, default=False)

    created_by = relationship("User", foreign_keys=[created_by_id])
    repository = relationship("Repository", back_populates="branches")

    def __repr__(self):
        return f"<Branch(name='{self.name}')>"


class AIModel(Base):
    """Modelo de IA disponível para uso nos agentes."""
    __tablename__ = 'ai_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    specialties_us = Column(String)
    specialties_br = Column(String)
    provider = Column(Enum(AIModelProvider), nullable=False)
    prompt_token_cost = Column(Float, nullable=False)
    completion_token_cost = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    def __repr__(self):
        return f"<AIModel(name='{self.name}', provider='{self.provider}')>"


class ProviderSecretKey(Base):
    """Chave secreta para autenticação com provedores de IA."""
    __tablename__ = 'ai_models_secret_key'

    id = Column(Integer, primary_key=True, autoincrement=True)

    provider = Column(Enum(AIModelProvider), nullable=False)
    secret_key = Column(String, nullable=False)

    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class Agent(Base):
    """Agente de IA que executa tarefas em um repositório."""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    function = Column(Enum(AgentFunction), nullable=False)  # 'PR Review', 'Issue Resolution', 'Both'
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    ai_model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    active = Column(Boolean, default=True)
    response_length = Column(Enum(AgentResponseLength), nullable=False)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    deleted = Column(Boolean, default=False)

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    repository = relationship("Repository", back_populates="agents", foreign_keys=[repository_id])
    ai_model = relationship("AIModel", foreign_keys=[ai_model_id])
    operations = relationship("Operation", back_populates="agent", cascade="all, delete-orphan")


class Operation(Base):
    """Operação executada por um agente."""
    __tablename__ = 'operations'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    action = Column(String(100), nullable=False)  # 'PR Review', 'Issue Resolution'
    # action = Column(String(100), nullable=False)
    details = Column(String(255))
    github_reference = Column(String(100))  # Número do PR ou Issue
    prompt_tokens = Column(Integer)  # Tokens de entrada (prompt)
    completion_tokens = Column(Integer)  # Tokens de saída (resposta)
    total_tokens = Column(Integer)  # Total de tokens usados
    cost = Column(Float, nullable=False)
    status = Column(String(20), default='completed')  # 'pending', 'completed', 'failed'
    execution_time = Column(Float)  # em segundos
    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamentos existentes
    agent = relationship("Agent", back_populates="operations", foreign_keys=[agent_id])

    def __repr__(self):
        return f"<Operation(action='{self.action}', cost='{self.cost}')>"


class CostHistory(Base):
    """Histórico de custos por mês."""
    __tablename__ = 'cost_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    month = Column(String(7), nullable=False)
    pr_cost = Column(Float, default=0.0)
    issue_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.now(UTC))

    # Relacionamento existente
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<CostHistory(month='{self.month}', total_cost='{self.total_cost}')>"


class RepositoryWebhook(Base):
    """Configuração de webhooks para um repositório."""
    __tablename__ = 'repository_webhooks'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    secret = Column(String(255))  # Adicionar este campo
    active = Column(Boolean, default=True)  # Adicionar este campo
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    repository = relationship("Repository", back_populates="webhooks", foreign_keys=[repository_id])

    def __repr__(self):
        return f"<RepositoryWebhook(id={self.id}, active={self.active})>"
