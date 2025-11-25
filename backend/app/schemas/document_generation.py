"""
Pydantic схемы для генераций документов
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DocumentGenerationCreate(BaseModel):
    """Схема для создания генерации"""
    template_id: int
    input_data: Dict[str, Any]
    format: str = "pdf"  # "pdf" или "xlsx"
    generation_method: str = "catalog"  # "catalog" или "chat"
    chat_session_id: Optional[int] = None


class DocumentGenerationResponse(BaseModel):
    """Схема ответа с генерацией"""
    id: int
    user_id: int
    template_id: int
    template_name: Optional[str] = None
    generated_file: str
    file_format: str
    file_size: Optional[int] = None
    input_data: Dict[str, Any]
    generation_method: str
    chat_session_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentGenerationListResponse(BaseModel):
    """Схема списка генераций"""
    generations: List[DocumentGenerationResponse]
    total: int

