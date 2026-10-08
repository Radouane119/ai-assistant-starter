from pydantic import BaseModel, Field
from typing import List


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation history or current prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model creativity")


class ChatResponse(BaseModel):
    reply: str
