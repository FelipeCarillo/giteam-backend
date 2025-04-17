from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine

from config.env import env
from models.models import AIModel


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


if __name__ == "__main__":
    db = Database()
    db.create_all()
    print("Database tables created successfully.")

    ai_models = [
        AIModel(
            name="GPT-3.5",
            provider="OpenAI",
            prompt_token_cost=0.0004,
            completion_token_cost=0.0004,
            max_tokens=4096,
            specialties="general, conversational",
        ),
        AIModel(
            name="GPT-4",
            provider="OpenAI",
            prompt_token_cost=0.03,
            completion_token_cost=0.06,
            max_tokens=8192,
            specialties="general, conversational, advanced",
        ),
        AIModel(
            name="Claude",
            provider="Anthropic",
            prompt_token_cost=0.0005,
            completion_token_cost=0.0005,
            max_tokens=4096,
            specialties="general, conversational",
        ),
        AIModel(
            name="Bard",
            provider="Google",
            prompt_token_cost=0.0003,
            completion_token_cost=0.0003,
            max_tokens=4096,
            specialties="general, conversational",
        ),
    ]

    db = Database()
    session = db.get_session()

    try:
        for model in ai_models:
            session.add(model)
        session.commit()
        print("AI models added successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error adding AI models: {e}")
    finally:
        db.close_session()
