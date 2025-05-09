import functools
import logging

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def handle_database_exceptions(func):
    """Decorator to handle database exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database error: {e}")

    return wrapper


def handle_github_api_exceptions(func):
    """Async decorator to handle GitHub API exceptions."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise GithubAPIError(f"GitHub API HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise GithubAPIError(f"Unexpected GitHub API error: {e}")

    return wrapper


def handle_exceptions(func):
    """Decorator to handle general exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as e:
            logger.error(f"HTTP exception: {e.detail}")
            raise e
        except DatabaseError:
            raise HTTPException(status_code=500, detail="Internal server error")
        except GithubAPIError:
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as e:
            logger.error(f"General error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return wrapper


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class GithubAPIError(Exception):
    """Custom exception for API-related errors."""
    pass
