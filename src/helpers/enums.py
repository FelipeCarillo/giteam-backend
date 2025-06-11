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


class AgentFunction(Enum):
    """
    Enum for the supported agent functions.
    """
    PR_REVIEW = "pr_review"
    ISSUE_RESOLUTION = "issue_resolution"
    BOTH = "both"


class AgentResponseLength(Enum):
    """
    Enum for the supported agent response lengths.
    """
    CONCISE = "concise"
    MEDIUM = "medium"
    DETAILED = "detailed"


class WebhookEventType(Enum):
    PULL_REQUEST = "pull_request"
    ISSUE = "issues"
