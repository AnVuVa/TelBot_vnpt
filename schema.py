from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DifyChatRequest(BaseModel):
    query: str
    user: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    response_mode: str = "blocking"
    conversation_id: Optional[str] = None
