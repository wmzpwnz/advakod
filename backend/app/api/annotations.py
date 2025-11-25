from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.annotations import (
    get_annotation_manager,
    AnnotationType,
    AnnotationStatus,
    TextRange,
    Annotation,
    AnnotationReply
)
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)

router = APIRouter()

class TextRangeRequest(BaseModel):
    start_offset: int = Field(..., description="Начальная позиция в тексте")
    end_offset: int = Field(..., description="Конечная позиция в тексте")
    start_line: int = Field(..., description="Начальная строка")
    end_line: int = Field(..., description="Конечная строка")
    text: str = Field(..., description="Выделенный текст")

class AnnotationRequest(BaseModel):
    document_id: str = Field(..., description="ID документа")
    annotation_type: str = Field(..., description="Тип аннотации")
    text_range: TextRangeRequest = Field(..., description="Диапазон текста")
    content: str = Field(..., description="Содержимое аннотации")
    color: Optional[str] = Field(None, description="Цвет выделения")
    style: Optional[Dict[str, Any]] = Field(None, description="Стиль")
    tags: Optional[List[str]] = Field(None, description="Теги")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Метаданные")
    is_public: bool = Field(default=False, description="Публичная аннотация")

class AnnotationUpdateRequest(BaseModel):
    content: Optional[str] = Field(None, description="Содержимое аннотации")
    color: Optional[str] = Field(None, description="Цвет выделения")
    style: Optional[Dict[str, Any]] = Field(None, description="Стиль")
    tags: Optional[List[str]] = Field(None, description="Теги")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Метаданные")
    is_public: Optional[bool] = Field(None, description="Публичная аннотация")

class AnnotationReplyRequest(BaseModel):
    content: str = Field(..., description="Содержимое ответа")

class AnnotationSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    document_id: Optional[str] = Field(None, description="ID документа")
    annotation_type: Optional[str] = Field(None, description="Тип аннотации")
    tags: Optional[List[str]] = Field(None, description="Теги")

class TextRangeResponse(BaseModel):
    start_offset: int
    end_offset: int
    start_line: int
    end_line: int
    text: str

class AnnotationResponse(BaseModel):
    id: str
    document_id: str
    user_id: int
    annotation_type: str
    text_range: TextRangeResponse
    content: str
    color: Optional[str]
    style: Dict[str, Any]
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    status: str
    is_public: bool
    replies: List[str]

class AnnotationReplyResponse(BaseModel):
    id: str
    annotation_id: str
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    status: str

@router.post("/create", response_model=AnnotationResponse)
async def create_annotation(
    request: AnnotationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание аннотации"""
    try:
        manager = get_annotation_manager()
        
        try:
            annotation_type = AnnotationType(request.annotation_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid annotation type")
        
        # Создаем диапазон текста
        text_range = TextRange(
            start_offset=request.text_range.start_offset,
            end_offset=request.text_range.end_offset,
            start_line=request.text_range.start_line,
            end_line=request.text_range.end_line,
            text=request.text_range.text
        )
        
        # Создаем аннотацию
        annotation = manager.create_annotation(
            document_id=request.document_id,
            user_id=current_user.id,
            annotation_type=annotation_type,
            text_range=text_range,
            content=request.content,
            color=request.color,
            style=request.style,
            tags=request.tags,
            metadata=request.metadata,
            is_public=request.is_public
        )
        
        return AnnotationResponse(
            id=annotation.id,
            document_id=annotation.document_id,
            user_id=annotation.user_id,
            annotation_type=annotation.annotation_type.value,
            text_range=TextRangeResponse(
                start_offset=annotation.text_range.start_offset,
                end_offset=annotation.text_range.end_offset,
                start_line=annotation.text_range.start_line,
                end_line=annotation.text_range.end_line,
                text=annotation.text_range.text
            ),
            content=annotation.content,
            color=annotation.color,
            style=annotation.style,
            tags=annotation.tags,
            metadata=annotation.metadata,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            status=annotation.status.value,
            is_public=annotation.is_public,
            replies=annotation.replies
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение аннотации по ID"""
    try:
        manager = get_annotation_manager()
        annotation = manager.get_annotation(annotation_id)
        
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        # Проверяем права доступа
        if annotation.user_id != current_user.id and not annotation.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return AnnotationResponse(
            id=annotation.id,
            document_id=annotation.document_id,
            user_id=annotation.user_id,
            annotation_type=annotation.annotation_type.value,
            text_range=TextRangeResponse(
                start_offset=annotation.text_range.start_offset,
                end_offset=annotation.text_range.end_offset,
                start_line=annotation.text_range.start_line,
                end_line=annotation.text_range.end_line,
                text=annotation.text_range.text
            ),
            content=annotation.content,
            color=annotation.color,
            style=annotation.style,
            tags=annotation.tags,
            metadata=annotation.metadata,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            status=annotation.status.value,
            is_public=annotation.is_public,
            replies=annotation.replies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: str,
    request: AnnotationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление аннотации"""
    try:
        manager = get_annotation_manager()
        annotation = manager.get_annotation(annotation_id)
        
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        # Проверяем права доступа
        if annotation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Обновляем аннотацию
        success = manager.update_annotation(
            annotation_id=annotation_id,
            content=request.content,
            color=request.color,
            style=request.style,
            tags=request.tags,
            metadata=request.metadata,
            is_public=request.is_public
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update annotation")
        
        # Получаем обновленную аннотацию
        updated_annotation = manager.get_annotation(annotation_id)
        
        return AnnotationResponse(
            id=updated_annotation.id,
            document_id=updated_annotation.document_id,
            user_id=updated_annotation.user_id,
            annotation_type=updated_annotation.annotation_type.value,
            text_range=TextRangeResponse(
                start_offset=updated_annotation.text_range.start_offset,
                end_offset=updated_annotation.text_range.end_offset,
                start_line=updated_annotation.text_range.start_line,
                end_line=updated_annotation.text_range.end_line,
                text=updated_annotation.text_range.text
            ),
            content=updated_annotation.content,
            color=updated_annotation.color,
            style=updated_annotation.style,
            tags=updated_annotation.tags,
            metadata=updated_annotation.metadata,
            created_at=updated_annotation.created_at,
            updated_at=updated_annotation.updated_at,
            status=updated_annotation.status.value,
            is_public=updated_annotation.is_public,
            replies=updated_annotation.replies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление аннотации"""
    try:
        manager = get_annotation_manager()
        
        success = manager.delete_annotation(annotation_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Annotation not found or access denied")
        
        return {"message": "Annotation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}", response_model=List[AnnotationResponse])
async def get_document_annotations(
    document_id: str,
    annotation_type: Optional[str] = None,
    include_public: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение аннотаций документа"""
    try:
        manager = get_annotation_manager()
        
        # Преобразуем тип аннотации
        annotation_type_enum = None
        if annotation_type:
            try:
                annotation_type_enum = AnnotationType(annotation_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid annotation type")
        
        annotations = manager.get_document_annotations(
            document_id=document_id,
            user_id=current_user.id,
            annotation_type=annotation_type_enum,
            include_public=include_public
        )
        
        return [
            AnnotationResponse(
                id=annotation.id,
                document_id=annotation.document_id,
                user_id=annotation.user_id,
                annotation_type=annotation.annotation_type.value,
                text_range=TextRangeResponse(
                    start_offset=annotation.text_range.start_offset,
                    end_offset=annotation.text_range.end_offset,
                    start_line=annotation.text_range.start_line,
                    end_line=annotation.text_range.end_line,
                    text=annotation.text_range.text
                ),
                content=annotation.content,
                color=annotation.color,
                style=annotation.style,
                tags=annotation.tags,
                metadata=annotation.metadata,
                created_at=annotation.created_at,
                updated_at=annotation.updated_at,
                status=annotation.status.value,
                is_public=annotation.is_public,
                replies=annotation.replies
            )
            for annotation in annotations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-annotations", response_model=List[AnnotationResponse])
async def get_my_annotations(
    annotation_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение аннотаций пользователя"""
    try:
        if limit > 100:
            limit = 100
        
        manager = get_annotation_manager()
        
        # Преобразуем тип аннотации
        annotation_type_enum = None
        if annotation_type:
            try:
                annotation_type_enum = AnnotationType(annotation_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid annotation type")
        
        annotations = manager.get_user_annotations(
            user_id=current_user.id,
            annotation_type=annotation_type_enum,
            limit=limit,
            offset=offset
        )
        
        return [
            AnnotationResponse(
                id=annotation.id,
                document_id=annotation.document_id,
                user_id=annotation.user_id,
                annotation_type=annotation.annotation_type.value,
                text_range=TextRangeResponse(
                    start_offset=annotation.text_range.start_offset,
                    end_offset=annotation.text_range.end_offset,
                    start_line=annotation.text_range.start_line,
                    end_line=annotation.text_range.end_line,
                    text=annotation.text_range.text
                ),
                content=annotation.content,
                color=annotation.color,
                style=annotation.style,
                tags=annotation.tags,
                metadata=annotation.metadata,
                created_at=annotation.created_at,
                updated_at=annotation.updated_at,
                status=annotation.status.value,
                is_public=annotation.is_public,
                replies=annotation.replies
            )
            for annotation in annotations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=List[AnnotationResponse])
async def search_annotations(
    request: AnnotationSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Поиск аннотаций"""
    try:
        manager = get_annotation_manager()
        
        # Преобразуем тип аннотации
        annotation_type_enum = None
        if request.annotation_type:
            try:
                annotation_type_enum = AnnotationType(request.annotation_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid annotation type")
        
        annotations = manager.search_annotations(
            query=request.query,
            user_id=current_user.id,
            document_id=request.document_id,
            annotation_type=annotation_type_enum,
            tags=request.tags
        )
        
        return [
            AnnotationResponse(
                id=annotation.id,
                document_id=annotation.document_id,
                user_id=annotation.user_id,
                annotation_type=annotation.annotation_type.value,
                text_range=TextRangeResponse(
                    start_offset=annotation.text_range.start_offset,
                    end_offset=annotation.text_range.end_offset,
                    start_line=annotation.text_range.start_line,
                    end_line=annotation.text_range.end_line,
                    text=annotation.text_range.text
                ),
                content=annotation.content,
                color=annotation.color,
                style=annotation.style,
                tags=annotation.tags,
                metadata=annotation.metadata,
                created_at=annotation.created_at,
                updated_at=annotation.updated_at,
                status=annotation.status.value,
                is_public=annotation.is_public,
                replies=annotation.replies
            )
            for annotation in annotations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{annotation_id}/replies", response_model=AnnotationReplyResponse)
async def add_annotation_reply(
    annotation_id: str,
    request: AnnotationReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление ответа на аннотацию"""
    try:
        manager = get_annotation_manager()
        
        # Проверяем, что аннотация существует и доступна
        annotation = manager.get_annotation(annotation_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        if annotation.user_id != current_user.id and not annotation.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Добавляем ответ
        reply = manager.add_annotation_reply(
            annotation_id=annotation_id,
            user_id=current_user.id,
            content=request.content
        )
        
        return AnnotationReplyResponse(
            id=reply.id,
            annotation_id=reply.annotation_id,
            user_id=reply.user_id,
            content=reply.content,
            created_at=reply.created_at,
            updated_at=reply.updated_at,
            status=reply.status.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{annotation_id}/replies", response_model=List[AnnotationReplyResponse])
async def get_annotation_replies(
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение ответов на аннотацию"""
    try:
        manager = get_annotation_manager()
        
        # Проверяем, что аннотация существует и доступна
        annotation = manager.get_annotation(annotation_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        if annotation.user_id != current_user.id and not annotation.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Получаем ответы
        replies = manager.get_annotation_replies(annotation_id)
        
        return [
            AnnotationReplyResponse(
                id=reply.id,
                annotation_id=reply.annotation_id,
                user_id=reply.user_id,
                content=reply.content,
                created_at=reply.created_at,
                updated_at=reply.updated_at,
                status=reply.status.value
            )
            for reply in replies
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_annotation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики аннотаций"""
    try:
        manager = get_annotation_manager()
        stats = manager.get_annotation_stats(current_user.id)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def annotation_health():
    """Проверка здоровья сервиса аннотаций"""
    try:
        manager = get_annotation_manager()
        
        # Тестируем создание аннотации
        test_text_range = TextRange(
            start_offset=0,
            end_offset=10,
            start_line=1,
            end_line=1,
            text="Test text"
        )
        
        test_annotation = manager.create_annotation(
            document_id="test_doc",
            user_id=999999,
            annotation_type=AnnotationType.HIGHLIGHT,
            text_range=test_text_range,
            content="Test annotation"
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_annotation": {
                "id": test_annotation.id,
                "type": test_annotation.annotation_type.value
            },
            "total_annotations": len(manager.annotations)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
