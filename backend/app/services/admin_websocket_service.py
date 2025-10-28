"""
Admin WebSocket сервис для real-time обновлений админ-панели
"""
import json
import logging
import time
import asyncio
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
from fastapi import WebSocket
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models.notification import AdminNotification

logger = logging.getLogger(__name__)


class AdminConnectionManager:
    """Менеджер WebSocket соединений для админ-панели"""
    
    def __init__(self):
        # Активные соединения по user_id
        self.active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
        # Роли пользователей для фильтрации
        self.user_roles: Dict[int, str] = {}
        # Подписки на каналы
        self.subscriptions: Dict[int, Set[str]] = defaultdict(set)
        # Статистика соединений
        self.connection_stats = {
            'total_connections': 0,
            'active_admins': 0,
            'connections_by_role': defaultdict(int),
            'last_activity': {}
        }
    
    async def connect(self, websocket: WebSocket, user_id: int, role: str):
        """Подключение админа к WebSocket"""
        self.active_connections[user_id].add(websocket)
        self.user_roles[user_id] = role
        
        # Обновляем статистику
        self.connection_stats['total_connections'] += 1
        self.connection_stats['active_admins'] = len(self.active_connections)
        self.connection_stats['connections_by_role'][role] += 1
        self.connection_stats['last_activity'][user_id] = time.time()
        
        logger.info(f"Admin user {user_id} with role {role} connected to WebSocket")
        
        # Отправляем приветственное сообщение
        await self.send_to_user(user_id, "connection_established", {
            "user_id": user_id,
            "role": role,
            "timestamp": time.time(),
            "available_channels": self._get_available_channels(role)
        })
    
    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Отключение конкретного WebSocket соединения"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id]
            if websocket in connections:
                connections.remove(websocket)
                self.connection_stats['total_connections'] -= 1
            
            # Удаляем пользователя, если у него больше нет соединений
            if not connections:
                del self.active_connections[user_id]
                if user_id in self.user_roles:
                    role = self.user_roles[user_id]
                    self.connection_stats['connections_by_role'][role] -= 1
                    del self.user_roles[user_id]
                if user_id in self.subscriptions:
                    del self.subscriptions[user_id]
                if user_id in self.connection_stats['last_activity']:
                    del self.connection_stats['last_activity'][user_id]
        
        self.connection_stats['active_admins'] = len(self.active_connections)
        logger.info(f"Admin user {user_id} disconnected from WebSocket")
    
    def _get_available_channels(self, role: str) -> List[str]:
        """Получение доступных каналов для роли"""
        base_channels = ["admin_dashboard", "notifications", "system_alerts"]
        
        role_channels = {
            "super_admin": ["all_channels", "user_management", "system_management", "security_events"],
            "admin": ["user_management", "moderation_queue", "analytics"],
            "moderator": ["moderation_queue", "user_reports"],
            "analyst": ["analytics", "user_activity", "performance_metrics"],
            "marketing_manager": ["marketing_analytics", "campaign_updates", "conversion_tracking"],
            "project_manager": ["project_updates", "task_management", "resource_tracking"]
        }
        
        return base_channels + role_channels.get(role, [])
    
    async def send_to_user(self, user_id: int, message_type: str, payload: dict, sender_id: Optional[int] = None):
        """Отправка сообщения конкретному админу"""
        if user_id not in self.active_connections:
            return False
        
        message = {
            "type": message_type,
            "payload": payload,
            "timestamp": time.time(),
            "sender_id": sender_id
        }
        
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(json.dumps(message))
                self.connection_stats['last_activity'][user_id] = time.time()
            except Exception as e:
                logger.error(f"Error sending message to admin {user_id}: {e}")
                disconnected.add(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            self.active_connections[user_id].discard(connection)
        
        # Удаляем пользователя, если у него больше нет соединений
        if user_id in self.active_connections and not self.active_connections[user_id]:
            del self.active_connections[user_id]
            if user_id in self.user_roles:
                del self.user_roles[user_id]
            if user_id in self.subscriptions:
                del self.subscriptions[user_id]
        
        return len(disconnected) == 0
    
    async def broadcast_to_role(self, role: str, message_type: str, payload: dict, sender_id: Optional[int] = None):
        """Отправка сообщения всем админам с определенной ролью"""
        target_users = [user_id for user_id, user_role in self.user_roles.items() if user_role == role]
        
        for user_id in target_users:
            await self.send_to_user(user_id, message_type, payload, sender_id)
    
    async def broadcast_to_all(self, message_type: str, payload: dict, sender_id: Optional[int] = None, exclude_roles: Optional[List[str]] = None):
        """Отправка сообщения всем подключенным админам"""
        exclude_roles = exclude_roles or []
        
        for user_id, role in self.user_roles.items():
            if role not in exclude_roles:
                await self.send_to_user(user_id, message_type, payload, sender_id)
    
    async def broadcast_to_channel(self, channel: str, message_type: str, payload: dict, sender_id: Optional[int] = None):
        """Отправка сообщения всем подписанным на канал"""
        subscribers = [user_id for user_id, channels in self.subscriptions.items() if channel in channels]
        
        for user_id in subscribers:
            await self.send_to_user(user_id, message_type, payload, sender_id)
    
    def subscribe_to_channel(self, user_id: int, channel: str) -> bool:
        """Подписка пользователя на канал"""
        if user_id not in self.user_roles:
            return False
        
        role = self.user_roles[user_id]
        available_channels = self._get_available_channels(role)
        
        if channel not in available_channels and channel != "all_channels":
            logger.warning(f"User {user_id} with role {role} tried to subscribe to unauthorized channel {channel}")
            return False
        
        self.subscriptions[user_id].add(channel)
        logger.info(f"User {user_id} subscribed to channel {channel}")
        return True
    
    def unsubscribe_from_channel(self, user_id: int, channel: str):
        """Отписка пользователя от канала"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(channel)
            logger.info(f"User {user_id} unsubscribed from channel {channel}")
    
    def get_connection_stats(self) -> dict:
        """Получение статистики соединений"""
        return {
            "total_connections": self.connection_stats['total_connections'],
            "active_admins": self.connection_stats['active_admins'],
            "connections_by_role": dict(self.connection_stats['connections_by_role']),
            "active_channels": len(set().union(*self.subscriptions.values())) if self.subscriptions else 0,
            "last_activity": {
                user_id: time.time() - last_time 
                for user_id, last_time in self.connection_stats['last_activity'].items()
            }
        }
    
    def get_active_admin_count(self, target_roles: Optional[List[str]] = None) -> int:
        """Получение количества активных админов (опционально по ролям)"""
        if not target_roles:
            return len(self.active_connections)
        
        return len([user_id for user_id, role in self.user_roles.items() if role in target_roles])


# Глобальный менеджер соединений
admin_connection_manager = AdminConnectionManager()


class AdminWebSocketService:
    """Сервис для работы с Admin WebSocket"""
    
    def __init__(self):
        self.manager = admin_connection_manager
        # Периодические задачи
        self._background_tasks = set()
        self._tasks_started = False
    
    def _start_background_tasks(self):
        """Запуск фоновых задач"""
        if self._tasks_started:
            return
        
        try:
            # Задача для отправки периодических обновлений
            task = asyncio.create_task(self._periodic_updates())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            self._tasks_started = True
        except RuntimeError:
            # No event loop running, tasks will be started later
            pass
    
    async def _periodic_updates(self):
        """Периодические обновления для админов"""
        while True:
            try:
                await asyncio.sleep(30)  # Каждые 30 секунд
                
                # Отправляем обновления дашборда
                await self._send_dashboard_updates()
                
                # Отправляем системные метрики
                await self._send_system_metrics()
                
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(60)  # Увеличиваем интервал при ошибке
    
    async def _send_dashboard_updates(self):
        """Отправка обновлений дашборда"""
        try:
            # Получаем актуальные данные дашборда
            dashboard_data = await self._get_dashboard_data()
            
            await self.manager.broadcast_to_channel(
                "admin_dashboard",
                "dashboard_update",
                dashboard_data
            )
        except Exception as e:
            logger.error(f"Error sending dashboard updates: {e}")
    
    async def _send_system_metrics(self):
        """Отправка системных метрик"""
        try:
            # Получаем системные метрики
            metrics_data = await self._get_system_metrics()
            
            await self.manager.broadcast_to_channel(
                "system_alerts",
                "real_time_metrics",
                metrics_data
            )
        except Exception as e:
            logger.error(f"Error sending system metrics: {e}")
    
    async def _get_dashboard_data(self) -> dict:
        """Получение данных дашборда"""
        # Здесь должна быть логика получения актуальных данных
        # Пока возвращаем заглушку
        return {
            "timestamp": time.time(),
            "active_users": 0,
            "total_sessions": 0,
            "system_load": 0.0,
            "memory_usage": 0.0
        }
    
    async def _get_system_metrics(self) -> dict:
        """Получение системных метрик"""
        # Здесь должна быть логика получения системных метрик
        # Пока возвращаем заглушку
        return {
            "timestamp": time.time(),
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "active_connections": len(self.manager.active_connections)
        }
    
    async def connect_admin(self, websocket: WebSocket, user_id: int, role: str):
        """Подключение админа к WebSocket"""
        await self.manager.connect(websocket, user_id, role)
    
    async def disconnect_admin(self, websocket: WebSocket, user_id: int):
        """Отключение админа от WebSocket"""
        await self.manager.disconnect(websocket, user_id)
    
    async def handle_admin_message(self, user_id: int, role: str, message: str):
        """Обработка сообщения от админа"""
        try:
            message_data = json.loads(message)
            await self._handle_admin_websocket_message(message_data, user_id, role)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from admin {user_id}: {message}, error: {e}")
            await self.manager.send_to_user(user_id, "error", {
                "message": "Invalid JSON format",
                "error": str(e)
            })
        except Exception as e:
            logger.error(f"Error handling admin message from user {user_id}: {e}")
            await self.manager.send_to_user(user_id, "error", {
                "message": "Error processing message",
                "error": str(e)
            })
    
    async def _handle_admin_websocket_message(self, message_data: dict, user_id: int, role: str):
        """Обработка сообщений от админ WebSocket клиента"""
        message_type = message_data.get("type")
        payload = message_data.get("payload", {})
        
        if message_type == "subscribe":
            # Подписка на канал
            channel = payload.get("channel")
            if channel:
                success = self.manager.subscribe_to_channel(user_id, channel)
                await self.manager.send_to_user(user_id, "subscription_result", {
                    "channel": channel,
                    "success": success,
                    "message": "Subscribed successfully" if success else "Subscription failed"
                })
        
        elif message_type == "unsubscribe":
            # Отписка от канала
            channel = payload.get("channel")
            if channel:
                self.manager.unsubscribe_from_channel(user_id, channel)
                await self.manager.send_to_user(user_id, "unsubscription_result", {
                    "channel": channel,
                    "success": True,
                    "message": "Unsubscribed successfully"
                })
        
        elif message_type == "heartbeat":
            # Heartbeat для поддержания соединения
            await self.manager.send_to_user(user_id, "heartbeat", {
                "timestamp": payload.get("timestamp", time.time())
            })
        
        elif message_type == "request_refresh":
            # Запрос обновления данных
            data_type = payload.get("data_type")
            await self._handle_refresh_request(user_id, data_type)
        
        elif message_type == "admin_action":
            # Административное действие
            action = payload.get("action")
            data = payload.get("data", {})
            await self._handle_admin_action(user_id, role, action, data)
        
        else:
            logger.warning(f"Unknown admin message type: {message_type} from user {user_id}")
    
    async def _handle_refresh_request(self, user_id: int, data_type: str):
        """Обработка запроса обновления данных"""
        try:
            if data_type == "dashboard":
                data = await self._get_dashboard_data()
                await self.manager.send_to_user(user_id, "dashboard_update", data)
            
            elif data_type == "system_metrics":
                data = await self._get_system_metrics()
                await self.manager.send_to_user(user_id, "real_time_metrics", data)
            
            elif data_type == "user_activity":
                data = await self._get_user_activity_data()
                await self.manager.send_to_user(user_id, "user_activity", data)
            
            else:
                await self.manager.send_to_user(user_id, "error", {
                    "message": f"Unknown data type: {data_type}"
                })
        
        except Exception as e:
            logger.error(f"Error handling refresh request for {data_type}: {e}")
            await self.manager.send_to_user(user_id, "error", {
                "message": f"Error refreshing {data_type}",
                "error": str(e)
            })
    
    async def _handle_admin_action(self, user_id: int, role: str, action: str, data: dict):
        """Обработка административных действий"""
        try:
            if action == "mark_notification_read":
                notification_id = data.get("notification_id")
                # Здесь должна быть логика отметки уведомления как прочитанного
                await self.manager.send_to_user(user_id, "notification_marked_read", {
                    "notification_id": notification_id
                })
            
            elif action == "submit_review":
                message_id = data.get("message_id")
                review = data.get("review")
                # Здесь должна быть логика отправки отзыва на модерацию
                await self.manager.send_to_user(user_id, "review_submitted", {
                    "message_id": message_id,
                    "status": "success"
                })
            
            else:
                logger.warning(f"Unknown admin action: {action} from user {user_id}")
        
        except Exception as e:
            logger.error(f"Error handling admin action {action}: {e}")
            await self.manager.send_to_user(user_id, "error", {
                "message": f"Error executing action {action}",
                "error": str(e)
            })
    
    async def _get_user_activity_data(self) -> dict:
        """Получение данных активности пользователей"""
        # Заглушка для данных активности пользователей
        return {
            "timestamp": time.time(),
            "online_users": 0,
            "recent_activity": []
        }
    
    # Публичные методы для отправки уведомлений
    
    async def send_to_admin(self, user_id: int, message_type: str, payload: dict, sender_id: Optional[int] = None) -> bool:
        """Отправка сообщения конкретному админу"""
        return await self.manager.send_to_user(user_id, message_type, payload, sender_id)
    
    async def broadcast_to_admins(self, message_type: str, payload: dict, target_roles: Optional[List[str]] = None, sender_id: Optional[int] = None):
        """Отправка broadcast сообщения админам"""
        if target_roles:
            for role in target_roles:
                await self.manager.broadcast_to_role(role, message_type, payload, sender_id)
        else:
            await self.manager.broadcast_to_all(message_type, payload, sender_id)
    
    async def send_dashboard_update(self, data: dict):
        """Отправка обновления дашборда"""
        await self.manager.broadcast_to_channel("admin_dashboard", "dashboard_update", data)
    
    async def send_user_activity_update(self, activity_data: dict):
        """Отправка обновления активности пользователей"""
        await self.manager.broadcast_to_channel("user_activity", "user_activity", activity_data)
    
    async def send_system_alert(self, alert_data: dict, severity: str = "info"):
        """Отправка системного алерта"""
        await self.manager.broadcast_to_channel("system_alerts", "system_alert", {
            **alert_data,
            "severity": severity,
            "timestamp": time.time()
        })
    
    async def send_moderation_queue_update(self, queue_data: dict):
        """Отправка обновления очереди модерации"""
        await self.manager.broadcast_to_channel("moderation_queue", "moderation_queue_update", queue_data)
    
    async def send_notification(self, user_id: int, notification_data: dict):
        """Отправка уведомления конкретному админу"""
        await self.manager.send_to_user(user_id, "notification", notification_data)
    
    async def send_backup_status_update(self, status_data: dict):
        """Отправка обновления статуса бэкапа"""
        await self.manager.broadcast_to_channel("backup_status", "backup_status", status_data)
    
    async def send_task_update(self, task_data: dict):
        """Отправка обновления задачи"""
        await self.manager.broadcast_to_channel("task_updates", "task_update", task_data)
    
    def get_connection_stats(self) -> dict:
        """Получение статистики соединений"""
        return self.manager.get_connection_stats()
    
    def get_active_admin_count(self, target_roles: Optional[List[str]] = None) -> int:
        """Получение количества активных админов"""
        return self.manager.get_active_admin_count(target_roles)


# Глобальный экземпляр сервиса
admin_websocket_service = AdminWebSocketService()