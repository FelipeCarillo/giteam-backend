from pydantic import BaseModel
from typing import Optional, List


class UpdateAgent(BaseModel):
    """Pydantic model for updating an agent."""
    name: Optional[str] = None
    ai_model_id: Optional[int] = None
    active: Optional[bool] = None
    response_length: Optional[str] = None
    branches: Optional[List[int]] = None
