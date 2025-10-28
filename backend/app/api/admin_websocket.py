"""
Admin WebSocket API endpoints для real-time обновлений админ-панели
"""
import json
import logging
import time
import asyncio
from typing import Dict, Set, Optional, Any
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.admin_websocket_service import admin_websocket_service
from ..core.permissions import require_admin_permission

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()

# Rate limiting для Admin WebSocket подключений
class AdminWebSocketRateLimiter:
    def __init__(self, max_connections_per_user: int = 5, window_seconds: int = 60):
        self.connections = defaultdict(int)
        self.max_connections = max_connections_per_user
        self.window_seconds = window_seconds
        self.last_cleanup = time.time()
    
    def check_rate_limit(self, user_id: int) -> bool:
        current_time = time.time()
        
        # Очистка старых записей каждую минуту
        if current_time - self.last_cleanup > self.window_seconds:
            self.connections.clear()
            self.last_cleanup = current_time
        
        current_connections = self.connections[user_id]
        if current_connections >= self.max_connections:
            logger.warning(f"Admin WebSocket rate limit exceeded for user {user_id}: {current_connections} connections")
            return False
        
        self.connections[user_id] += 1
        return True
    
    def disconnect(self, user_id: int):
        if user_id in self.connections:
            self.connections[user_id] = max(0, self.connections[user_id] - 1)

# Глобальный rate limiter для админ WebSocket
admin_websocket_limiter = AdminWebSocketRateLimiter(max_connections_per_user=10, window_seconds=60)


async def get_admin_user_from_token(token: str, db: Session) -> User:
    """Получение админ пользователя из JWT токена для WebSocket"""
    try:
        payload = auth_service.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Проверяем права администратора
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or insufficient permissions"
        )


@router.websocket("/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    """Admin WebSocket endpoint для real-time обновлений"""
    logger.info("Admin WebSocket connection started")
    
    # Получаем параметры из query string
    token = websocket.query_params.get("token")
    user_id_param = websocket.query_params.get("user_id")
    
    if not token:
        await websocket.close(code=1008, reason="No token provided")
        return
    
    if not user_id_param:
        await websocket.close(code=1008, reason="No user_id provided")
        return
    
    try:
        user_id = int(user_id_param)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid user_id")
        return
    
    # Проверяем rate limiting
    if not admin_websocket_limiter.check_rate_limit(user_id):
        logger.warning(f"Admin WebSocket rate limit exceeded for user {user_id}")
        await websocket.close(code=1008, reason="Too many connections")
        return
    
    db = SessionLocal()
    user = None
    try:
        # Получаем и проверяем пользователя
        user = await get_admin_user_from_token(token, db)
        
        # Проверяем соответствие user_id
        if user.id != user_id:
            await websocket.close(code=1008, reason="User ID mismatch")
            return
        
        # Подключаемся к WebSocket
        await websocket.accept()
        logger.info(f"Admin WebSocket accepted for user {user.id}")
        
        # Регистрируем соединение в менеджере
        await admin_websocket_service.connect_admin(websocket, user.id, user.role)
        logger.info(f"Admin WebSocket registered for user {user.id} with role {user.role}")
        
        # Основной цикл обработки сообщений
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    logger.debug(f"Received admin WebSocket message from user {user.id}: {data}")
                    
                    # Передаём сообщение в сервис для обработки
                    await admin_websocket_service.handle_admin_message(user.id, user.role, data)
                    
                except WebSocketDisconnect:
                    logger.info(f"Admin WebSocket disconnected for user {user.id}")
                    break
                except Exception as e:
                    logger.error(f"Error processing admin WebSocket message from user {user.id}: {e}")
                    # Не прерываем соединение при ошибке обработки сообщения
                    continue
                    
        except WebSocketDisconnect:
            logger.info(f"Admin WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(f"Error in admin WebSocket loop for user {user.id}: {e}")
            
    except HTTPException as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {e.detail}")
    except WebSocketDisconnect:
        logger.info(f"Admin WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"Admin WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Отключаем через менеджер
        if user:
            await admin_websocket_service.disconnect_admin(websocket, user.id)
        
        # Очищаем rate limiter при отключении
        if user:
            admin_websocket_limiter.disconnect(user.id)
        
        db.close()


@router.get("/admin/stats")
async def get_admin_websocket_stats(
    current_user: User = Depends(require_admin_permission("view_system_stats"))
):
    """Получение статистики Admin WebSocket соединений"""
    return admin_websocket_service.get_connection_stats()


@router.post("/admin/broadcast")
async def broadcast_admin_message(
    message_type: str,
    payload: dict,
    target_roles: Optional[list] = None,
    current_user: User = Depends(require_admin_permission("send_admin_broadcasts"))
):
    """Отправка broadcast сообщения всем админам или определенным ролям"""
    await admin_websocket_service.broadcast_to_admins(
        message_type=message_type,
        payload=payload,
        target_roles=target_roles,
        sender_id=current_user.id
    )
    
    return {
        "success": True,
        "message": "Broadcast sent successfully",
        "recipients": admin_websocket_service.get_active_admin_count(target_roles)
    }


@router.post("/admin/notify")
async def send_admin_notification(
    user_id: int,
    notification_type: str,
    payload: dict,
    current_user: User = Depends(require_admin_permission("send_admin_notifications"))
):
    """Отправка уведомления конкретному админу"""
    success = await admin_websocket_service.send_to_admin(
        user_id=user_id,
        message_type=notification_type,
        payload=payload,
        sender_id=current_user.id
    )
    
    return {
        "success": success,
        "message": "Notification sent successfully" if success else "Admin not connected"
    }


# Импортируем SessionLocal здесь, чтобы избежать циклических импортов
from ..core.database import SessionLocal