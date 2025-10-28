from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user, get_current_admin_user
from ..models.user import User
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationCenterResponse, NotificationFilters,
    SendNotificationRequest, MarkAsReadRequest,
    NotificationPriority, NotificationType
)
from ..services.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/notifications", response_model=NotificationCenterResponse)
async def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    try:
        filters = NotificationFilters(
            type=type,
            priority=priority,
            read=read
        )
        
        notifications = await notification_service.get_user_notifications(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        unread_count = await notification_service.get_unread_count(
            db=db,
            user_id=current_user.id
        )
        
        return NotificationCenterResponse(
            notifications=[NotificationResponse.from_orm(n) for n in notifications],
            unread_count=unread_count,
            total_count=len(notifications),
            has_more=len(notifications) == limit
        )
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


@router.post("/notifications/mark-read")
async def mark_notifications_as_read(
    request: MarkAsReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark multiple notifications as read"""
    try:
        updated_count = await notification_service.mark_as_read(
            db=db,
            user_id=current_user.id,
            notification_ids=request.notification_ids
        )
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")


@router.get("/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    try:
        count = await notification_service.get_unread_count(
            db=db,
            user_id=current_user.id
        )
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")


# Admin endpoints
@router.post("/admin/notifications/send", dependencies=[Depends(get_current_admin_user)])
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send notification to users (admin only)"""
    try:
        notifications = await notification_service.send_notification(
            db=db,
            request=request
        )
        
        return {
            "message": f"Sent {len(notifications)} notifications",
            "notification_ids": [n.id for n in notifications]
        }
        
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notifications")