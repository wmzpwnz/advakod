"""
Сервис уведомлений для админ-панели
"""
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db, SessionLocal
from ..models.user import User
from ..models.notification import AdminNotification, NotificationTemplate, NotificationHistory
from .admin_websocket_service import admin_websocket_service

logger = logging.getLogger(__name__)


class AdminNotificationService:
    """Сервис для управления уведомлениями админ-панели"""
    
    def __init__(self):
        self.websocket_service = admin_websocket_service
        self.delivery_queue = None
        self._worker_started = False
    
    def _start_delivery_worker(self):
        """Запуск фонового процесса доставки уведомлений"""
        if self._worker_started:
            return
        
        try:
            if self.delivery_queue is None:
                self.delivery_queue = asyncio.Queue()
            asyncio.create_task(self._delivery_worker())
            self._worker_started = True
        except RuntimeError:
            # No event loop running, worker will be started later
            pass
    
    async def _delivery_worker(self):
        """Фоновый процесс доставки уведомлений"""
        while True:
            try:
                notification_data = await self.delivery_queue.get()
                await self._process_notification_delivery(notification_data)
                self.delivery_queue.task_done()
            except Exception as e:
                logger.error(f"Error in notification delivery worker: {e}")
                await asyncio.sleep(1)
    
    async def _process_notification_delivery(self, notification_data: dict):
        """Обработка доставки уведомления"""
        notification_id = notification_data.get('notification_id')
        channels = notification_data.get('channels', ['websocket'])
        
        db = SessionLocal()
        try:
            notification = db.query(AdminNotification).filter(
                AdminNotification.id == notification_id
            ).first()
            
            if not notification:
                logger.error(f"Notification {notification_id} not found")
                return
            
            # Доставляем через каждый канал
            for channel in channels:
                await self._deliver_via_channel(db, notification, channel)
                
        except Exception as e:
            logger.error(f"Error processing notification delivery: {e}")
        finally:
            db.close()
    
    async def _deliver_via_channel(self, db: Session, notification: AdminNotification, channel: str):
        """Доставка уведомления через конкретный канал"""
        history = NotificationHistory(
            notification_id=notification.id,
            channel=channel,
            status="pending"
        )
        db.add(history)
        db.commit()
        
        try:
            if channel == "websocket":
                success = await self._deliver_websocket(notification)
            elif channel == "email":
                success = await self._deliver_email(notification)
            elif channel == "slack":
                success = await self._deliver_slack(notification)
            elif channel == "telegram":
                success = await self._deliver_telegram(notification)
            else:
                logger.warning(f"Unknown delivery channel: {channel}")
                success = False
            
            # Обновляем статус доставки
            if success:
                history.status = "delivered"
                history.delivered_at = datetime.utcnow()
            else:
                history.status = "failed"
                history.failed_at = datetime.utcnow()
                history.error_message = "Delivery failed"
            
            db.commit()
            
        except Exception as e:
            history.status = "failed"
            history.failed_at = datetime.utcnow()
            history.error_message = str(e)
            db.commit()
            logger.error(f"Error delivering notification via {channel}: {e}")
    
    async def _deliver_websocket(self, notification: AdminNotification) -> bool:
        """Доставка через WebSocket"""
        try:
            notification_data = {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat(),
                "read": notification.read
            }
            
            success = await self.websocket_service.send_to_admin(
                user_id=notification.user_id,
                message_type="notification",
                payload=notification_data
            )
            
            return success
        except Exception as e:
            logger.error(f"WebSocket delivery error: {e}")
            return False
    
    async def _deliver_email(self, notification: AdminNotification) -> bool:
        """Доставка через email (заглушка)"""
        # Здесь должна быть интеграция с email сервисом
        logger.info(f"Email delivery for notification {notification.id} (not implemented)")
        return True
    
    async def _deliver_slack(self, notification: AdminNotification) -> bool:
        """Доставка через Slack (заглушка)"""
        # Здесь должна быть интеграция со Slack API
        logger.info(f"Slack delivery for notification {notification.id} (not implemented)")
        return True
    
    async def _deliver_telegram(self, notification: AdminNotification) -> bool:
        """Доставка через Telegram (заглушка)"""
        # Здесь должна быть интеграция с Telegram Bot API
        logger.info(f"Telegram delivery for notification {notification.id} (not implemented)")
        return True
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
        priority: str = "normal",
        channels: Optional[List[str]] = None
    ) -> AdminNotification:
        """Создание нового уведомления"""
        db = SessionLocal()
        try:
            # Проверяем, что пользователь является админом
            user = db.query(User).filter(User.id == user_id, User.is_admin == True).first()
            if not user:
                raise ValueError(f"User {user_id} is not an admin")
            
            # Создаем уведомление
            notification = AdminNotification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                data=data or {},
                priority=priority,
                channels=channels or ["websocket"]
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Добавляем в очередь доставки
            await self.delivery_queue.put({
                'notification_id': notification.id,
                'channels': notification.channels
            })
            
            logger.info(f"Created notification {notification.id} for user {user_id}")
            return notification
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise
        finally:
            db.close()
    
    async def create_system_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        data: Optional[dict] = None,
        target_roles: Optional[List[str]] = None
    ):
        """Создание системного алерта для админов"""
        db = SessionLocal()
        try:
            # Получаем список админов для уведомления
            query = db.query(User).filter(User.is_admin == True)
            
            if target_roles:
                # Фильтруем по ролям (если поле role существует)
                if hasattr(User, 'role'):
                    query = query.filter(User.role.in_(target_roles))
            
            admins = query.all()
            
            # Создаем уведомления для каждого админа
            notifications = []
            for admin in admins:
                notification = await self.create_notification(
                    user_id=admin.id,
                    notification_type="system_alert",
                    title=title,
                    message=message,
                    data={**(data or {}), "severity": severity},
                    priority="high" if severity in ["warning", "error", "critical"] else "normal",
                    channels=["websocket", "email"] if severity == "critical" else ["websocket"]
                )
                notifications.append(notification)
            
            # Также отправляем через WebSocket для real-time обновлений
            alert_data = {
                "title": title,
                "message": message,
                "severity": severity,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_service.send_system_alert(alert_data, severity)
            
            logger.info(f"Created system alert for {len(notifications)} admins")
            return notifications
            
        except Exception as e:
            logger.error(f"Error creating system alert: {e}")
            raise
        finally:
            db.close()
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Отметка уведомления как прочитанного"""
        db = SessionLocal()
        try:
            notification = db.query(AdminNotification).filter(
                AdminNotification.id == notification_id,
                AdminNotification.user_id == user_id
            ).first()
            
            if not notification:
                return False
            
            notification.read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            
            # Уведомляем через WebSocket
            await self.websocket_service.send_to_admin(
                user_id=user_id,
                message_type="notification_marked_read",
                payload={"notification_id": notification_id}
            )
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking notification as read: {e}")
            return False
        finally:
            db.close()
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Отметка всех уведомлений пользователя как прочитанных"""
        db = SessionLocal()
        try:
            updated_count = db.query(AdminNotification).filter(
                AdminNotification.user_id == user_id,
                AdminNotification.read == False
            ).update({
                "read": True,
                "read_at": datetime.utcnow()
            })
            
            db.commit()
            
            # Уведомляем через WebSocket
            await self.websocket_service.send_to_admin(
                user_id=user_id,
                message_type="all_notifications_marked_read",
                payload={"count": updated_count}
            )
            
            return updated_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            return 0
        finally:
            db.close()
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[AdminNotification]:
        """Получение уведомлений пользователя"""
        db = SessionLocal()
        try:
            query = db.query(AdminNotification).filter(
                AdminNotification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(AdminNotification.read == False)
            
            notifications = query.order_by(
                AdminNotification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return notifications
            
        finally:
            db.close()
    
    def get_unread_count(self, user_id: int) -> int:
        """Получение количества непрочитанных уведомлений"""
        db = SessionLocal()
        try:
            count = db.query(AdminNotification).filter(
                AdminNotification.user_id == user_id,
                AdminNotification.read == False
            ).count()
            
            return count
            
        finally:
            db.close()
    
    async def cleanup_old_notifications(self, days: int = 30):
        """Очистка старых уведомлений"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Удаляем прочитанные уведомления старше указанного периода
            deleted_count = db.query(AdminNotification).filter(
                AdminNotification.read == True,
                AdminNotification.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up old notifications: {e}")
            return 0
        finally:
            db.close()
    
    # Предустановленные типы уведомлений
    
    async def notify_user_registered(self, new_user: User):
        """Уведомление о регистрации нового пользователя"""
        await self.create_system_alert(
            title="Новый пользователь",
            message=f"Зарегистрировался новый пользователь: {new_user.email}",
            severity="info",
            data={"user_id": new_user.id, "email": new_user.email},
            target_roles=["super_admin", "admin"]
        )
    
    async def notify_backup_completed(self, backup_info: dict):
        """Уведомление о завершении резервного копирования"""
        await self.create_system_alert(
            title="Резервное копирование завершено",
            message=f"Создана резервная копия: {backup_info.get('filename', 'unknown')}",
            severity="info",
            data=backup_info,
            target_roles=["super_admin", "admin"]
        )
    
    async def notify_backup_failed(self, error_info: dict):
        """Уведомление о сбое резервного копирования"""
        await self.create_system_alert(
            title="Ошибка резервного копирования",
            message=f"Не удалось создать резервную копию: {error_info.get('error', 'unknown error')}",
            severity="error",
            data=error_info,
            target_roles=["super_admin", "admin"]
        )
    
    async def notify_system_error(self, error_info: dict):
        """Уведомление о системной ошибке"""
        await self.create_system_alert(
            title="Системная ошибка",
            message=f"Обнаружена системная ошибка: {error_info.get('message', 'unknown error')}",
            severity="error",
            data=error_info,
            target_roles=["super_admin", "admin"]
        )
    
    async def notify_high_load(self, load_info: dict):
        """Уведомление о высокой нагрузке"""
        await self.create_system_alert(
            title="Высокая нагрузка на систему",
            message=f"Обнаружена высокая нагрузка: CPU {load_info.get('cpu', 0)}%, Memory {load_info.get('memory', 0)}%",
            severity="warning",
            data=load_info,
            target_roles=["super_admin", "admin", "project_manager"]
        )


# Глобальный экземпляр сервиса
admin_notification_service = AdminNotificationService()