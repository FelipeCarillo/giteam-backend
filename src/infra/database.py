from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, text

from config.env import env
from helpers.errors import handle_database_exceptions


class Database:
    def __init__(self):
        self._engine = self._create_engine()
        self.session = self._init_session()

    @staticmethod
    @handle_database_exceptions
    def _create_engine():
        return create_engine(env.DATABASE_URL, poolclass=NullPool)

    @handle_database_exceptions
    def _init_session(self):
        return Session(self._engine)

    @handle_database_exceptions
    def get_session(self):
        """Get the current session."""
        return self.session

    @handle_database_exceptions
    def close_session(self):
        """Close the current session."""
        self.session.close()

    @handle_database_exceptions
    def create_all(self):
        """Create all tables in the database."""
        from models import Base
        session = self.get_session()
        session.execute(text("CREATE SCHEMA IF NOT EXISTS giteam"))
        session.commit()
        session.close()
        Base.metadata.create_all(self._engine)

    @handle_database_exceptions
    def drop_all(self):
        """Drop all tables in the database."""
        from models import Base
        Base.metadata.drop_all(self._engine)
