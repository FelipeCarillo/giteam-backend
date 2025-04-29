from enum import Enum


class AuthProvider(Enum):
    """
    Enum for the supported providers.
    """
    GITHUB = "github"


class AIModelProvider(Enum):
    """
    Enum for the supported AI model providers.
    """
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
