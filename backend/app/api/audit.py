from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..services.auth_service import AuthService
from ..services.audit_service import AuditService
from ..models.audit_log import ActionType, SeverityLevel
from ..models.user import User
from ..schemas.audit import (
    AuditLogResponse,
    SecurityEventResponse,
    AuditStatisticsResponse,
    AuditLogFilter
)

router = APIRouter()
auth_service = AuthService()

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[ActionType] = None,
    severity: Optional[SeverityLevel] = None,
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение аудит логов"""
    
    # Проверяем права доступа
    if not current_user.is_premium and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аудит логов других пользователей"
        )
    
    audit_service = AuditService(db)
    
    # Если user_id не указан, показываем логи текущего пользователя
    target_user_id = user_id if user_id else current_user.id
    
    logs = audit_service.get_user_audit_logs(
        user_id=target_user_id,
        limit=limit,
        offset=offset,
        action_filter=action,
        severity_filter=severity
    )
    
    return logs

@router.get("/security-events", response_model=List[SecurityEventResponse])
async def get_security_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    threat_level: Optional[SeverityLevel] = None,
    status: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение событий безопасности"""
    
    # Только премиум пользователи могут просматривать события безопасности
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Просмотр событий безопасности доступен только премиум пользователям"
        )
    
    audit_service = AuditService(db)
    
    events = audit_service.get_security_events(
        limit=limit,
        offset=offset,
        threat_level_filter=threat_level,
        status_filter=status
    )
    
    return events

@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение статистики аудит логов"""
    
    # Проверяем права доступа
    if not current_user.is_premium and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра статистики других пользователей"
        )
    
    audit_service = AuditService(db)
    
    # Если user_id не указан, показываем статистику текущего пользователя
    target_user_id = user_id if user_id else current_user.id
    
    statistics = audit_service.get_audit_statistics(
        user_id=target_user_id,
        days=days
    )
    
    return statistics

@router.get("/export")
async def export_audit_logs(
    format: str = Query("json", pattern="^(json|csv)$"),
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Экспорт аудит логов"""
    
    # Проверяем права доступа
    if not current_user.is_premium and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Экспорт аудит логов доступен только премиум пользователям"
        )
    
    audit_service = AuditService(db)
    
    # Если user_id не указан, экспортируем логи текущего пользователя
    target_user_id = user_id if user_id else current_user.id
    
    logs = audit_service.get_user_audit_logs(
        user_id=target_user_id,
        limit=10000,  # Большой лимит для экспорта
        offset=0
    )
    
    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "user_id": target_user_id,
                "export_date": datetime.utcnow().isoformat(),
                "period_days": days,
                "total_logs": len(logs),
                "logs": [
                    {
                        "id": log.id,
                        "action": log.action.value,
                        "resource": log.resource,
                        "resource_id": log.resource_id,
                        "description": log.description,
                        "severity": log.severity.value,
                        "status": log.status,
                        "ip_address": log.ip_address,
                        "created_at": log.created_at.isoformat(),
                        "details": log.details
                    }
                    for log in logs
                ]
            }
        )
    
    elif format == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            "ID", "Action", "Resource", "Resource ID", "Description",
            "Severity", "Status", "IP Address", "Created At", "Details"
        ])
        
        # Данные
        for log in logs:
            writer.writerow([
                log.id,
                log.action.value,
                log.resource,
                log.resource_id,
                log.description,
                log.severity.value,
                log.status,
                log.ip_address,
                log.created_at.isoformat(),
                str(log.details) if log.details else ""
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{target_user_id}_{datetime.now().strftime('%Y%m%d')}.csv"}
        )

@router.post("/security-events/{event_id}/resolve")
async def resolve_security_event(
    event_id: int,
    resolution: str = Query(..., description="Resolution description"),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Разрешение события безопасности"""
    
    # Только премиум пользователи могут разрешать события безопасности
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Разрешение событий безопасности доступно только премиум пользователям"
        )
    
    from ..models.audit_log import SecurityEvent
    
    # Находим событие
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие безопасности не найдено"
        )
    
    # Обновляем статус
    event.status = "resolved"
    event.resolved_at = datetime.utcnow()
    event.resolved_by = current_user.id
    
    # Добавляем описание разрешения в детали
    if not event.details:
        event.details = {}
    event.details["resolution"] = resolution
    event.details["resolved_by"] = current_user.username
    
    db.commit()
    db.refresh(event)
    
    return {"message": "Событие безопасности успешно разрешено", "event_id": event_id}

@router.get("/dashboard")
async def get_audit_dashboard(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение данных для дашборда аудит логов"""
    
    audit_service = AuditService(db)
    
    # Статистика за последние 7 дней
    week_stats = audit_service.get_audit_statistics(
        user_id=current_user.id,
        days=7
    )
    
    # Статистика за последние 30 дней
    month_stats = audit_service.get_audit_statistics(
        user_id=current_user.id,
        days=30
    )
    
    # Последние события безопасности
    security_events = audit_service.get_security_events(
        limit=10,
        offset=0
    )
    
    # Последние аудит логи
    recent_logs = audit_service.get_user_audit_logs(
        user_id=current_user.id,
        limit=10,
        offset=0
    )
    
    return {
        "week_statistics": week_stats,
        "month_statistics": month_stats,
        "recent_security_events": security_events,
        "recent_audit_logs": recent_logs,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "is_premium": current_user.is_premium
        }
    }
