from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional conversation session ID")
    message: Optional[str] = Field(default=None, description="User message to send")
    messages: Optional[List[ChatMessage]] = Field(default=None, description="Optional full history if provided")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model creativity")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class DocumentUploadResponse(BaseModel):
    id: int
    title: str
    message: str


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
