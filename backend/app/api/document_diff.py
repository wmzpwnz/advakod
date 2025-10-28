from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.document_diff import (
    get_document_diff_engine,
    ChangeType,
    TextChange,
    DocumentDiff
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

class DocumentComparisonRequest(BaseModel):
    old_content: str = Field(..., description="Старое содержимое документа")
    new_content: str = Field(..., description="Новое содержимое документа")
    old_version_id: str = Field(..., description="ID старой версии")
    new_version_id: str = Field(..., description="ID новой версии")

class TextChangeResponse(BaseModel):
    change_type: str
    old_text: str
    new_text: str
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    line_number: int

class DocumentDiffResponse(BaseModel):
    old_version_id: str
    new_version_id: str
    changes: List[TextChangeResponse]
    total_changes: int
    added_lines: int
    deleted_lines: int
    modified_lines: int
    similarity_score: float
    created_at: datetime

@router.post("/compare", response_model=DocumentDiffResponse)
async def compare_documents(
    request: DocumentComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Сравнение двух версий документа"""
    try:
        engine = get_document_diff_engine()
        
        # Сравниваем документы
        diff = engine.compare_documents(
            old_content=request.old_content,
            new_content=request.new_content,
            old_version_id=request.old_version_id,
            new_version_id=request.new_version_id
        )
        
        return DocumentDiffResponse(
            old_version_id=diff.old_version_id,
            new_version_id=diff.new_version_id,
            changes=[
                TextChangeResponse(
                    change_type=change.change_type.value,
                    old_text=change.old_text,
                    new_text=change.new_text,
                    old_start=change.old_start,
                    old_end=change.old_end,
                    new_start=change.new_start,
                    new_end=change.new_end,
                    line_number=change.line_number
                )
                for change in diff.changes
            ],
            total_changes=diff.total_changes,
            added_lines=diff.added_lines,
            deleted_lines=diff.deleted_lines,
            modified_lines=diff.modified_lines,
            similarity_score=diff.similarity_score,
            created_at=diff.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diff/{diff_id}", response_model=DocumentDiffResponse)
async def get_document_diff(
    diff_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение diff по ID"""
    try:
        engine = get_document_diff_engine()
        diff = engine.get_diff(diff_id)
        
        if not diff:
            raise HTTPException(status_code=404, detail="Diff not found")
        
        return DocumentDiffResponse(
            old_version_id=diff.old_version_id,
            new_version_id=diff.new_version_id,
            changes=[
                TextChangeResponse(
                    change_type=change.change_type.value,
                    old_text=change.old_text,
                    new_text=change.new_text,
                    old_start=change.old_start,
                    old_end=change.old_end,
                    new_start=change.new_start,
                    new_end=change.new_end,
                    line_number=change.line_number
                )
                for change in diff.changes
            ],
            total_changes=diff.total_changes,
            added_lines=diff.added_lines,
            deleted_lines=diff.deleted_lines,
            modified_lines=diff.modified_lines,
            similarity_score=diff.similarity_score,
            created_at=diff.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}", response_model=List[DocumentDiffResponse])
async def get_document_diffs(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение всех diff для документа"""
    try:
        engine = get_document_diff_engine()
        diffs = engine.get_document_diffs(document_id)
        
        return [
            DocumentDiffResponse(
                old_version_id=diff.old_version_id,
                new_version_id=diff.new_version_id,
                changes=[
                    TextChangeResponse(
                        change_type=change.change_type.value,
                        old_text=change.old_text,
                        new_text=change.new_text,
                        old_start=change.old_start,
                        old_end=change.old_end,
                        new_start=change.new_start,
                        new_end=change.new_end,
                        line_number=change.line_number
                    )
                    for change in diff.changes
                ],
                total_changes=diff.total_changes,
                added_lines=diff.added_lines,
                deleted_lines=diff.deleted_lines,
                modified_lines=diff.modified_lines,
                similarity_score=diff.similarity_score,
                created_at=diff.created_at
            )
            for diff in diffs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diff/{diff_id}/summary")
async def get_diff_summary(
    diff_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение сводки изменений"""
    try:
        engine = get_document_diff_engine()
        diff = engine.get_diff(diff_id)
        
        if not diff:
            raise HTTPException(status_code=404, detail="Diff not found")
        
        summary = engine.get_change_summary(diff)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diff/{diff_id}/changes/{change_type}")
async def get_changes_by_type(
    diff_id: str,
    change_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение изменений по типу"""
    try:
        engine = get_document_diff_engine()
        diff = engine.get_diff(diff_id)
        
        if not diff:
            raise HTTPException(status_code=404, detail="Diff not found")
        
        try:
            change_type_enum = ChangeType(change_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid change type")
        
        changes = engine.get_changes_by_type(diff, change_type_enum)
        
        return [
            TextChangeResponse(
                change_type=change.change_type.value,
                old_text=change.old_text,
                new_text=change.new_text,
                old_start=change.old_start,
                old_end=change.old_end,
                new_start=change.new_start,
                new_end=change.new_end,
                line_number=change.line_number
            )
            for change in changes
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diff/{diff_id}/line/{line_number}")
async def get_line_changes(
    diff_id: str,
    line_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение изменений для конкретной строки"""
    try:
        engine = get_document_diff_engine()
        diff = engine.get_diff(diff_id)
        
        if not diff:
            raise HTTPException(status_code=404, detail="Diff not found")
        
        changes = engine.get_line_changes(diff, line_number)
        
        return [
            TextChangeResponse(
                change_type=change.change_type.value,
                old_text=change.old_text,
                new_text=change.new_text,
                old_start=change.old_start,
                old_end=change.old_end,
                new_start=change.new_start,
                new_end=change.new_end,
                line_number=change.line_number
            )
            for change in changes
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_diff_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики diff"""
    try:
        engine = get_document_diff_engine()
        stats = engine.get_diff_stats()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def document_diff_health():
    """Проверка здоровья сервиса сравнения документов"""
    try:
        engine = get_document_diff_engine()
        
        # Тестируем сравнение
        test_diff = engine.compare_documents(
            old_content="Hello world",
            new_content="Hello beautiful world",
            old_version_id="test_v1",
            new_version_id="test_v2"
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_diff": {
                "total_changes": test_diff.total_changes,
                "similarity_score": test_diff.similarity_score
            },
            "total_diffs": len(engine.diffs)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
