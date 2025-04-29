from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, text

from config.env import env
from helpers.errors import DatabaseError


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise DatabaseError(f"Error in {func.__name__}: {e}")

    return wrapper


class Database:
    def __init__(self):
        self._engine = self._create_engine()
        self.session = self._init_session()

    @staticmethod
    @handle_exceptions
    def _create_engine():
        return create_engine(env.DATABASE_URL, poolclass=NullPool)

    @handle_exceptions
    def _init_session(self):
        return Session(self._engine)

    @handle_exceptions
    def get_session(self):
        """Get the current session."""
        return self.session

    @handle_exceptions
    def close_session(self):
        """Close the current session."""
        self.session.close()

    @handle_exceptions
    def create_all(self):
        """Create all tables in the database."""
        from models.models import Base
        session = self.get_session()
        session.execute(text("CREATE SCHEMA IF NOT EXISTS giteams"))
        session.commit()
        session.close()
        Base.metadata.create_all(self._engine)

    @handle_exceptions
    def drop_all(self):
        """Drop all tables in the database."""
        from models.models import Base
        Base.metadata.drop_all(self._engine)
