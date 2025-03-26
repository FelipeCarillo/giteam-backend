from datetime import datetime, UTC

from sqlalchemy.orm import DeclarativeBase, Relationship
from sqlalchemy import MetaData, UUID, Column, String, DateTime, Boolean, Enum, Integer, ForeignKey, ARRAY


class Base(DeclarativeBase):
    metadata = MetaData(schema=Env.DATABASE_SCHEMA)


class AgentResponsibilityCategories(Enum):
    __tablname__ = 'agent_responsibility_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    logo = Column(String, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID, nullable=False)
    updated_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(UTC))


class AgentResponsibilities(Base):
    __tablename__ = 'agent_responsibilities'

    id = Column(UUID, primary_key=True)
    agent_id = Column(UUID, ForeignKey(Agent.id), nullable=False)
    category_id = Column(Integer, ForeignKey(AgentResponsibilityCategories.id), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID, nullable=False)
    updated_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(UTC))


class AgentRepository(Base):
    __tablename__ = 'agent_repositories'

    id = Column(UUID, primary_key=True)
    agent_id = Column(UUID, ForeignKey(Agent.id), nullable=False)
    repository = Column(String, nullable=False)
    branches = Column(ARRAY(String), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID, nullable=False)
    updated_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(UTC))


class AgentCosts(Base):
    __tablename__ = 'agent_costs'

    id = Column(UUID, primary_key=True)
    agent_id = Column(UUID, ForeignKey(Agent.id), nullable=False)
    cost = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID, nullable=False)
    updated_by = Column(UUID, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
