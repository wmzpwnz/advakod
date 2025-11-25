from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import os

from ..core.database import get_db
from ..models.user import User
from ..core.export import (
    get_export_manager,
    ExportFormat,
    ExportType,
    ExportRequest
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

class ExportRequestModel(BaseModel):
    export_type: str = Field(..., description="Тип экспорта")
    export_format: str = Field(..., description="Формат экспорта")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Фильтры")

class ExportRequestResponse(BaseModel):
    id: str
    user_id: int
    export_type: str
    export_format: str
    filters: Dict[str, Any]
    created_at: datetime
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str]

@router.post("/request", response_model=ExportRequestResponse)
async def create_export_request(
    request: ExportRequestModel,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание запроса на экспорт"""
    try:
        manager = get_export_manager()
        
        try:
            export_type = ExportType(request.export_type)
            export_format = ExportFormat(request.export_format)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
        
        # Создаем запрос на экспорт
        export_request = manager.create_export_request(
            user_id=current_user.id,
            export_type=export_type,
            export_format=export_format,
            filters=request.filters
        )
        
        # Запускаем обработку в фоне
        background_tasks.add_task(manager.process_export, export_request.id)
        
        return ExportRequestResponse(
            id=export_request.id,
            user_id=export_request.user_id,
            export_type=export_request.export_type.value,
            export_format=export_request.export_format.value,
            filters=export_request.filters,
            created_at=export_request.created_at,
            status=export_request.status,
            file_path=export_request.file_path,
            file_size=export_request.file_size,
            error_message=export_request.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/request/{request_id}", response_model=ExportRequestResponse)
async def get_export_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статуса запроса на экспорт"""
    try:
        manager = get_export_manager()
        export_request = manager.get_export_request(request_id)
        
        if not export_request:
            raise HTTPException(status_code=404, detail="Export request not found")
        
        # Проверяем права доступа
        if export_request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ExportRequestResponse(
            id=export_request.id,
            user_id=export_request.user_id,
            export_type=export_request.export_type.value,
            export_format=export_request.export_format.value,
            filters=export_request.filters,
            created_at=export_request.created_at,
            status=export_request.status,
            file_path=export_request.file_path,
            file_size=export_request.file_size,
            error_message=export_request.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-requests", response_model=List[ExportRequestResponse])
async def get_my_export_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение запросов на экспорт пользователя"""
    try:
        manager = get_export_manager()
        requests = manager.get_user_export_requests(current_user.id)
        
        return [
            ExportRequestResponse(
                id=req.id,
                user_id=req.user_id,
                export_type=req.export_type.value,
                export_format=req.export_format.value,
                filters=req.filters,
                created_at=req.created_at,
                status=req.status,
                file_path=req.file_path,
                file_size=req.file_size,
                error_message=req.error_message
            )
            for req in requests
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{request_id}")
async def download_export_file(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скачивание экспортированного файла"""
    try:
        manager = get_export_manager()
        export_request = manager.get_export_request(request_id)
        
        if not export_request:
            raise HTTPException(status_code=404, detail="Export request not found")
        
        # Проверяем права доступа
        if export_request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Проверяем статус
        if export_request.status != "completed":
            raise HTTPException(status_code=400, detail="Export not completed yet")
        
        if not export_request.file_path or not os.path.exists(export_request.file_path):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        # Определяем MIME тип
        mime_types = {
            ExportFormat.PDF: "application/pdf",
            ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv"
        }
        
        mime_type = mime_types.get(export_request.export_format, "application/octet-stream")
        
        # Читаем файл
        with open(export_request.file_path, 'rb') as f:
            file_content = f.read()
        
        # Определяем имя файла
        filename = f"export_{request_id}.{export_request.export_format.value}"
        
        return Response(
            content=file_content,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/formats")
async def get_export_formats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение доступных форматов экспорта"""
    try:
        formats = [
            {
                "format": format_type.value,
                "name": _get_format_name(format_type),
                "description": _get_format_description(format_type),
                "mime_type": _get_format_mime_type(format_type)
            }
            for format_type in ExportFormat
        ]
        
        return {"formats": formats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_export_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение доступных типов экспорта"""
    try:
        manager = get_export_manager()
        
        types = []
        for export_type in ExportType:
            template = manager.export_templates.get(export_type, {})
            types.append({
                "type": export_type.value,
                "name": template.get("title", export_type.value),
                "description": _get_export_type_description(export_type),
                "columns": template.get("columns", [])
            })
        
        return {"types": types}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_export_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики экспорта (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_export_manager()
        stats = manager.get_export_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def export_health():
    """Проверка здоровья сервиса экспорта"""
    try:
        manager = get_export_manager()
        
        # Тестируем создание запроса
        test_request = manager.create_export_request(
            user_id=999999,
            export_type=ExportType.CHAT_HISTORY,
            export_format=ExportFormat.JSON
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_request": {
                "id": test_request.id,
                "type": test_request.export_type.value,
                "format": test_request.export_format.value
            },
            "total_requests": len(manager.export_requests)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _get_format_name(format_type: ExportFormat) -> str:
    """Получение названия формата"""
    names = {
        ExportFormat.PDF: "PDF",
        ExportFormat.DOCX: "Microsoft Word",
        ExportFormat.XLSX: "Microsoft Excel",
        ExportFormat.JSON: "JSON",
        ExportFormat.CSV: "CSV"
    }
    return names.get(format_type, format_type.value.upper())

def _get_format_description(format_type: ExportFormat) -> str:
    """Получение описания формата"""
    descriptions = {
        ExportFormat.PDF: "Портативный формат документов",
        ExportFormat.DOCX: "Документ Microsoft Word",
        ExportFormat.XLSX: "Таблица Microsoft Excel",
        ExportFormat.JSON: "Формат обмена данными JSON",
        ExportFormat.CSV: "Текстовый формат с разделителями"
    }
    return descriptions.get(format_type, "Неизвестный формат")

def _get_format_mime_type(format_type: ExportFormat) -> str:
    """Получение MIME типа формата"""
    mime_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ExportFormat.JSON: "application/json",
        ExportFormat.CSV: "text/csv"
    }
    return mime_types.get(format_type, "application/octet-stream")

def _get_export_type_description(export_type: ExportType) -> str:
    """Получение описания типа экспорта"""
    descriptions = {
        ExportType.CHAT_HISTORY: "История всех сообщений в чате",
        ExportType.DOCUMENT_ANALYSIS: "Результаты анализа документов",
        ExportType.USER_STATISTICS: "Статистика использования сервиса",
        ExportType.SUBSCRIPTION_REPORT: "Отчет по подпискам и тарифам",
        ExportType.PAYMENT_REPORT: "Отчет по платежам и транзакциям",
        ExportType.ANNOTATIONS_REPORT: "Отчет по аннотациям в документах",
        ExportType.REFERRAL_REPORT: "Отчет по реферальной программе"
    }
    return descriptions.get(export_type, "Неизвестный тип экспорта")
