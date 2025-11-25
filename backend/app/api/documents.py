"""
API endpoints для работы с шаблонами документов и генерацией
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..models.user import User
from ..models.document_template import DocumentTemplate, DocumentGeneration
from ..services.auth_service import AuthService
from ..services.document_generator_service import document_generator_service
from ..schemas.document_template import (
    DocumentTemplateResponse,
    DocumentTemplateListResponse
)
from ..schemas.document_generation import (
    DocumentGenerationCreate,
    DocumentGenerationResponse,
    DocumentGenerationListResponse
)

router = APIRouter(prefix="/documents", tags=["documents"])
auth_service = AuthService()


@router.get("/templates", response_model=DocumentTemplateListResponse)
async def get_templates(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить список шаблонов документов
    
    Args:
        category: Фильтр по категории (опционально)
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        current_user: Текущий пользователь
        db: Сессия БД
        
    Returns:
        Список шаблонов
    """
    try:
        query = db.query(DocumentTemplate).filter(DocumentTemplate.is_active == True)
        
        if category:
            query = query.filter(DocumentTemplate.category == category)
        
        total = query.count()
        templates = query.order_by(DocumentTemplate.name).offset(skip).limit(limit).all()
        
        return DocumentTemplateListResponse(
            templates=[DocumentTemplateResponse.model_validate(t) for t in templates],
            total=total
        )
    except Exception as e:
        logger.error(f"Ошибка получения списка шаблонов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения списка шаблонов"
        )


@router.get("/templates/{template_id}", response_model=DocumentTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить детали шаблона документа
    
    Args:
        template_id: ID шаблона
        current_user: Текущий пользователь
        db: Сессия БД
        
    Returns:
        Детали шаблона
    """
    try:
        template = db.query(DocumentTemplate).filter(
            DocumentTemplate.id == template_id,
            DocumentTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Шаблон не найден"
            )
        
        return DocumentTemplateResponse.model_validate(template)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения шаблона {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения шаблона"
        )


@router.post("/generate")
async def generate_document(
    generation_data: DocumentGenerationCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Сгенерировать документ из шаблона
    
    Args:
        generation_data: Данные для генерации
        current_user: Текущий пользователь
        db: Сессия БД
        
    Returns:
        Информация о сгенерированном документе
    """
    try:
        # Получаем шаблон
        template = db.query(DocumentTemplate).filter(
            DocumentTemplate.id == generation_data.template_id,
            DocumentTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Шаблон не найден"
            )
        
        # Валидация данных
        is_valid, errors = document_generator_service.validate_template_data(
            template.required_fields or [],
            generation_data.input_data
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )
        
        # Проверяем формат
        if generation_data.format not in ["pdf", "xlsx"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Формат должен быть 'pdf' или 'xlsx'"
            )
        
        # Проверяем совместимость формата с типом шаблона
        if template.template_type == "html" and generation_data.format != "pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HTML шаблоны поддерживают только формат PDF"
            )
        
        if template.template_type == "xlsx" and generation_data.format != "xlsx":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="XLSX шаблоны поддерживают только формат XLSX"
            )
        
        # Генерируем документ
        result = await document_generator_service.generate_document(
            template_id=template.id,
            template_file=template.template_file,
            template_type=template.template_type,
            data=generation_data.input_data,
            output_format=generation_data.format,
            user_id=current_user.id
        )
        
        # Сохраняем запись о генерации
        generation = DocumentGeneration(
            user_id=current_user.id,
            template_id=template.id,
            generated_file=result["file_path"],
            file_format=result["file_format"],
            file_size=result["file_size"],
            input_data=generation_data.input_data,
            generation_method=generation_data.generation_method,
            chat_session_id=generation_data.chat_session_id
        )
        
        db.add(generation)
        db.commit()
        db.refresh(generation)
        
        return DocumentGenerationResponse(
            id=generation.id,
            user_id=generation.user_id,
            template_id=generation.template_id,
            template_name=template.name,
            generated_file=generation.generated_file,
            file_format=generation.file_format,
            file_size=generation.file_size,
            input_data=generation.input_data,
            generation_method=generation.generation_method,
            chat_session_id=generation.chat_session_id,
            created_at=generation.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации документа: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации документа: {str(e)}"
        )


@router.get("/generations", response_model=DocumentGenerationListResponse)
async def get_user_generations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить историю сгенерированных документов пользователя
    
    Args:
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        current_user: Текущий пользователь
        db: Сессия БД
        
    Returns:
        Список генераций
    """
    try:
        query = db.query(DocumentGeneration).filter(
            DocumentGeneration.user_id == current_user.id
        )
        
        total = query.count()
        generations = query.order_by(DocumentGeneration.created_at.desc()).offset(skip).limit(limit).all()
        
        # Добавляем названия шаблонов
        result = []
        for gen in generations:
            template = db.query(DocumentTemplate).filter(DocumentTemplate.id == gen.template_id).first()
            result.append(DocumentGenerationResponse(
                id=gen.id,
                user_id=gen.user_id,
                template_id=gen.template_id,
                template_name=template.name if template else None,
                generated_file=gen.generated_file,
                file_format=gen.file_format,
                file_size=gen.file_size,
                input_data=gen.input_data,
                generation_method=gen.generation_method,
                chat_session_id=gen.chat_session_id,
                created_at=gen.created_at
            ))
        
        return DocumentGenerationListResponse(
            generations=result,
            total=total
        )
    except Exception as e:
        logger.error(f"Ошибка получения истории генераций: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории генераций"
        )


@router.get("/generations/{generation_id}/download")
async def download_document(
    generation_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Скачать сгенерированный документ
    
    Args:
        generation_id: ID генерации
        current_user: Текущий пользователь
        db: Сессия БД
        
    Returns:
        Файл для скачивания
    """
    try:
        generation = db.query(DocumentGeneration).filter(
            DocumentGeneration.id == generation_id,
            DocumentGeneration.user_id == current_user.id
        ).first()
        
        if not generation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )
        
        file_path = generation.generated_file
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден на сервере"
            )
        
        # Определяем MIME тип
        mime_type = "application/pdf" if generation.file_format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Получаем имя файла
        template = db.query(DocumentTemplate).filter(DocumentTemplate.id == generation.template_id).first()
        filename = f"{template.name if template else 'document'}_{generation.id}.{generation.file_format}"
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка скачивания документа {generation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка скачивания документа"
        )

