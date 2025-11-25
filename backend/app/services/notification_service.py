from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging
from fastapi import HTTPException

from ..models.notification import AdminNotification, NotificationTemplate, NotificationHistory
from ..models.user import User
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationFilters,
    NotificationTemplateCreate, NotificationTemplateUpdate,
    SendNotificationRequest, NotificationCenterResponse,
    MarkAsReadRequest
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and notification system"""

    async def create_notification(
        self, 
        db: Session, 
        notification_data: NotificationCreate
    ) -> AdminNotification:
        """Create a new notification"""
        try:
            # Create notification
            db_notification = AdminNotification(
                user_id=notification_data.user_id,
                title=notification_data.title,
                message=notification_data.message,
                type=notification_data.type,
                priority=notification_data.priority,
                channels=notification_data.channels,
                data=notification_data.data
            )
            
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            
            logger.info(f"Created notification {db_notification.id} for user {notification_data.user_id}")
            return db_notification
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise HTTPException(status_code=500, detail="Failed to create notification")

    async def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[NotificationFilters] = None
    ) -> List[AdminNotification]:
        """Get notifications for a user with optional filters"""
        try:
            query = db.query(AdminNotification).filter(AdminNotification.user_id == user_id)
            
            # Apply filters
            if filters:
                if filters.type:
                    query = query.filter(AdminNotification.type == filters.type)
                if filters.priority:
                    query = query.filter(AdminNotification.priority == filters.priority)
                if filters.read is not None:
                    if filters.read:
                        query = query.filter(AdminNotification.read_at.isnot(None))
                    else:
                        query = query.filter(AdminNotification.read_at.is_(None))
                if filters.date_from:
                    query = query.filter(AdminNotification.created_at >= filters.date_from)
                if filters.date_to:
                    query = query.filter(AdminNotification.created_at <= filters.date_to)
            
            # Order by priority and creation date
            notifications = query.order_by(
                desc(AdminNotification.priority),
                desc(AdminNotification.created_at)
            ).offset(skip).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            raise HTTPException(status_code=500, detail="Failed to get notifications")

    async def get_notification(self, db: Session, notification_id: int, user_id: int) -> Optional[AdminNotification]:
        """Get a specific notification for a user"""
        try:
            notification = db.query(AdminNotification).filter(
                and_(
                    AdminNotification.id == notification_id,
                    AdminNotification.user_id == user_id
                )
            ).first()
            
            return notification
            
        except Exception as e:
            logger.error(f"Error getting notification: {e}")
            return None

    async def mark_as_read(
        self,
        db: Session,
        user_id: int,
        notification_ids: List[int]
    ) -> int:
        """Mark notifications as read"""
        try:
            updated_count = db.query(AdminNotification).filter(
                and_(
                    AdminNotification.id.in_(notification_ids),
                    AdminNotification.user_id == user_id,
                    AdminNotification.read_at.is_(None)
                )
            ).update({
                "read": True,
                "read_at": datetime.utcnow()
            }, synchronize_session=False)
            
            db.commit()
            
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking notifications as read: {e}")
            raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

    async def get_unread_count(self, db: Session, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        try:
            count = db.query(AdminNotification).filter(
                and_(
                    AdminNotification.user_id == user_id,
                    AdminNotification.read_at.is_(None)
                )
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0

    async def send_notification(
        self,
        db: Session,
        request: SendNotificationRequest
    ) -> List[AdminNotification]:
        """Send notification to multiple users"""
        notifications = []
        
        try:
            user_ids = request.user_ids or []
            
            for user_id in user_ids:
                notification_data = NotificationCreate(
                    user_id=user_id,
                    title=request.title,
                    message=request.message,
                    type=request.type,
                    priority=request.priority,
                    channels=request.channels,
                    data=request.data
                )
                
                notification = await self.create_notification(db, notification_data)
                notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            raise HTTPException(status_code=500, detail="Failed to send notifications")

    # Template operations
    async def create_template(
        self,
        db: Session,
        template_data: NotificationTemplateCreate
    ) -> NotificationTemplate:
        """Create a notification template"""
        try:
            db_template = NotificationTemplate(
                name=template_data.name,
                type=template_data.type,
                title_template=template_data.title_template,
                message_template=template_data.message_template,
                default_channels=template_data.default_channels,
                default_priority=template_data.default_priority
            )
            
            db.add(db_template)
            db.commit()
            db.refresh(db_template)
            
            logger.info(f"Created notification template {db_template.id}")
            return db_template
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification template: {e}")
            raise HTTPException(status_code=500, detail="Failed to create template")

    async def get_templates(self, db: Session) -> List[NotificationTemplate]:
        """Get all notification templates"""
        try:
            templates = db.query(NotificationTemplate).filter(
                NotificationTemplate.active == True
            ).order_by(NotificationTemplate.name).all()
            
            return templates
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []


# Global instance
notification_service = NotificationService()