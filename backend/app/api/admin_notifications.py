"""
API endpoints для системы уведомлений админ-панели
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.permissions import require_admin_permission, get_current_admin_user
from ..models.user import User
from ..models.notification import AdminNotification
from ..services.admin_notification_service import admin_notification_service
from ..schemas.admin_notification import (
    AdminNotificationResponse,
    AdminNotificationCreate,
    SystemAlertCreate,
    NotificationStatsResponse
)

router = APIRouter()


@router.get("/notifications", response_model=List[AdminNotificationResponse])
async def get_admin_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(require_admin_permission("view_dashboard"))
):
    """Получение уведомлений текущего админа"""
    notifications = admin_notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    
    return [AdminNotificationResponse.from_orm(n) for n in notifications]


@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(require_admin_permission("view_dashboard"))
):
    """Получение статистики уведомлений"""
    unread_count = admin_notification_service.get_unread_count(current_user.id)
    total_notifications = admin_notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=1000  # Получаем большое количество для подсчета
    )
    
    return NotificationStatsResponse(
        unread_count=unread_count,
        total_count=len(total_notifications)
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(require_admin_permission("view_dashboard"))
):
    """Отметка уведомления как прочитанного"""
    success = await admin_notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"success": True, "message": "Notification marked as read"}


@router.post("/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(require_admin_permission("view_dashboard"))
):
    """Отметка всех уведомлений как прочитанных"""
    updated_count = await admin_notification_service.mark_all_as_read(
        user_id=current_user.id
    )
    
    return {
        "success": True,
        "message": f"Marked {updated_count} notifications as read",
        "count": updated_count
    }


@router.post("/notifications/create")
async def create_admin_notification(
    notification_data: AdminNotificationCreate,
    current_user: User = Depends(require_admin_permission("send_admin_notifications"))
):
    """Создание нового уведомления для админа"""
    try:
        notification = await admin_notification_service.create_notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            priority=notification_data.priority,
            channels=notification_data.channels
        )
        
        return {
            "success": True,
            "message": "Notification created successfully",
            "notification_id": notification.id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


@router.post("/notifications/system-alert")
async def create_system_alert(
    alert_data: SystemAlertCreate,
    current_user: User = Depends(require_admin_permission("send_admin_broadcasts"))
):
    """Создание системного алерта"""
    try:
        notifications = await admin_notification_service.create_system_alert(
            title=alert_data.title,
            message=alert_data.message,
            severity=alert_data.severity,
            data=alert_data.data,
            target_roles=alert_data.target_roles
        )
        
        return {
            "success": True,
            "message": "System alert created successfully",
            "recipients_count": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create system alert"
        )


@router.delete("/notifications/cleanup")
async def cleanup_old_notifications(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin_permission("manage_system"))
):
    """Очистка старых уведомлений"""
    try:
        deleted_count = await admin_notification_service.cleanup_old_notifications(days)
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old notifications",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup notifications"
        )


# WebSocket integration endpoints

@router.post("/notifications/test-websocket")
async def test_websocket_notification(
    current_user: User = Depends(require_admin_permission("send_admin_notifications"))
):
    """Тестовое уведомление через WebSocket"""
    try:
        notification = await admin_notification_service.create_notification(
            user_id=current_user.id,
            notification_type="test",
            title="Тестовое уведомление",
            message="Это тестовое уведомление для проверки WebSocket соединения",
            data={"test": True},
            priority="normal",
            channels=["websocket"]
        )
        
        return {
            "success": True,
            "message": "Test notification sent",
            "notification_id": notification.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.get("/notifications/delivery-stats")
async def get_delivery_stats(
    current_user: User = Depends(require_admin_permission("view_system_stats"))
):
    """Получение статистики доставки уведомлений"""
    # Здесь должна быть логика получения статистики доставки
    # Пока возвращаем заглушку
    return {
        "websocket_delivery_rate": 95.5,
        "email_delivery_rate": 87.2,
        "slack_delivery_rate": 92.1,
        "total_notifications_sent": 1234,
        "failed_deliveries": 45
    }