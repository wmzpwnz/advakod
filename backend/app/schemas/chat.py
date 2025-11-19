from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageBase(BaseModel):
    content: str
    role: str  # user, assistant, system


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    chat_mode: Optional[str] = 'basic'  # 'basic' или 'expert'


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    chat_mode: str = 'basic'  # Режим чата: 'basic' или 'expert'
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[ChatMessage] = []
    # Дополнительные поля для UI
    last_message_preview: Optional[str] = None
    last_message_time: Optional[datetime] = None
    has_messages: Optional[bool] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    set_chat_mode: Optional[str] = None  # Для изменения режима сессии ('basic' или 'expert')
    
    @field_validator('message')
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Проверка, что сообщение не пустое"""
        if not v or not v.strip():
            raise ValueError('Сообщение не может быть пустым')
        return v.strip()


class ChatResponse(BaseModel):
    message: str
    session_id: int
    message_id: int
    sources: Optional[List[Dict[str, str]]] = None
    processing_time: Optional[float] = None


class DocumentAnalysisRequest(BaseModel):
    filename: str
    file_type: str
    content: str


class DocumentAnalysisResponse(BaseModel):
    analysis_id: int
    analysis_result: str
    risks_found: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[str] = None
    processing_time: Optional[float] = None
