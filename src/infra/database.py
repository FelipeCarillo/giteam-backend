from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine

from config.env import env


class Database:
    def __init__(self):
        self._engine = create_engine(env.DATABASE_URL, poolclass=NullPool)
        self.session = Session(self._engine)

    def get_session(self):
        """Get the current session."""
        return self.session

    def close_session(self):
        """Close the current session."""
        self.session.close()

    def create_all(self):
        """Create all tables in the database."""
        from models.models import Base
        Base.metadata.create_all(self._engine)

    def drop_all(self):
        """Drop all tables in the database."""
        from models.models import Base
        Base.metadata.drop_all(self._engine)


if __name__ == "__main__":
    db = Database()
    db.drop_all()
    db.create_all()
    print("Database tables created successfully.")
