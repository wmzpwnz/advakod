"""
Pydantic схемы для шаблонов документов
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentTemplateBase(BaseModel):
    """Базовая схема шаблона"""
    name: str
    category: str
    description: Optional[str] = None
    template_file: str
    template_type: str = "html"  # "html" или "xlsx"
    required_fields: Optional[List[Dict[str, Any]]] = None
    optional_fields: Optional[List[Dict[str, Any]]] = None
    field_descriptions: Optional[Dict[str, str]] = None
    is_active: bool = True


class DocumentTemplateCreate(DocumentTemplateBase):
    """Схема для создания шаблона"""
    pass


class DocumentTemplateUpdate(BaseModel):
    """Схема для обновления шаблона"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    template_file: Optional[str] = None
    template_type: Optional[str] = None
    required_fields: Optional[List[Dict[str, Any]]] = None
    optional_fields: Optional[List[Dict[str, Any]]] = None
    field_descriptions: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class DocumentTemplateResponse(DocumentTemplateBase):
    """Схема ответа с шаблоном"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentTemplateListResponse(BaseModel):
    """Схема списка шаблонов"""
    templates: List[DocumentTemplateResponse]
    total: int

