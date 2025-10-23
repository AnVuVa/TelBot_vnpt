from typing import Optional, Dict, Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-oss 20B"
    # customer_data: Optional[Dict[str, Any]] = None

class State(BaseModel):
    history: Optional[list] = []