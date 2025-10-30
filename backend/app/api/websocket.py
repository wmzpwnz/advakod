"""
WebSocket API endpoints для real-time чата
"""
import json
import asyncio
import logging
import time
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import SessionLocal
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.websocket_service import websocket_service
from ..services.websocket_auth_manager import websocket_auth_manager

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()

# Rate limiting для WebSocket подключений с улучшенной конфигурацией
class WebSocketRateLimiter:
    def __init__(self, max_connections_per_ip: int = None, window_seconds: int = None):
        from ..core.config import settings
        self.connections = defaultdict(int)
        self.max_connections = max_connections_per_ip or settings.WEBSOCKET_MAX_CONNECTIONS_PER_IP
        self.window_seconds = window_seconds or settings.WEBSOCKET_RATE_LIMIT_WINDOW
        self.last_cleanup = time.time()
    
    def check_rate_limit(self, client_ip: str) -> bool:
        current_time = time.time()
        
        # Очистка старых записей
        if current_time - self.last_cleanup > self.window_seconds:
            self.connections.clear()
            self.last_cleanup = current_time
        
        current_connections = self.connections[client_ip]
        if current_connections >= self.max_connections:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {current_connections}/{self.max_connections} connections")
            return False
        
        self.connections[client_ip] += 1
        return True
    
    def disconnect(self, client_ip: str):
        if client_ip in self.connections:
            self.connections[client_ip] = max(0, self.connections[client_ip] - 1)
    
    def get_stats(self) -> dict:
        """Получение статистики rate limiting"""
        return {
            "active_ips": len(self.connections),
            "total_connections": sum(self.connections.values()),
            "max_connections_per_ip": self.max_connections,
            "window_seconds": self.window_seconds,
            "connections_by_ip": dict(self.connections)
        }

# Глобальный rate limiter с настройками из конфигурации
websocket_limiter = WebSocketRateLimiter()


def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """Получение пользователя из JWT токена для WebSocket
    Возвращает None при ошибке (не поднимает HTTPException для WebSocket)
    """
    try:
        # Декодируем токен
        payload = auth_service.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            logger.warning("WebSocket auth: Invalid token - no email in payload")
            return None
        
        # Проверяем срок действия токена
        exp = payload.get("exp")
        if exp is None:
            logger.warning("WebSocket auth: Token has no expiration")
            return None
            
        import time
        if time.time() > exp:
            logger.warning("WebSocket auth: Token has expired")
            return None
        
        # Получаем пользователя из БД
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            logger.warning(f"WebSocket auth: User not found for email: {email}")
            return None
        
        # Проверяем активность пользователя
        if not user.is_active:
            logger.warning(f"WebSocket auth: User {email} is not active")
            return None
        
        return user
    except HTTPException as e:
        # HTTPException не работает в WebSocket - логируем и возвращаем None
        logger.warning(f"WebSocket auth: HTTPException raised - {e.detail}")
        return None
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        return None


@router.websocket("/session/{session_id}")
async def websocket_endpoint_with_session(
    websocket: WebSocket, 
    session_id: int
):
    """WebSocket endpoint с привязкой к сессии"""
    await handle_websocket_connection(websocket, session_id)


@router.websocket("/general")
async def websocket_endpoint_general(websocket: WebSocket):
    """Общий WebSocket endpoint без привязки к сессии"""
    await handle_websocket_connection(websocket)


async def handle_websocket_connection(websocket: WebSocket, session_id: int = None):
    """Общая логика обработки WebSocket соединения с улучшенной стабильностью"""
    from ..core.config import settings
    
    logger.info(f"WebSocket connection started for session_id={session_id}")
    
    # Проверяем rate limiting (отключаем для nginx и внутренних сервисов)
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"Client IP: {client_ip}")
    
    # Список доверенных IP адресов
    trusted_ips = ["127.0.0.1", "nginx", "advakod_nginx", "::1", "localhost"]
    
    if client_ip and client_ip not in trusted_ips and client_ip != "unknown":
        if not websocket_limiter.check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return
    
    # Проверяем инициализацию сервиса
    if not hasattr(websocket_service, 'manager'):
        logger.error("WebSocket service not properly initialized!")
        await websocket.close(code=1011, reason="Service not initialized")
        return
    
    # КРИТИЧНО: Аутентификация ДО accept() для предотвращения неавторизованных соединений
    user, db, auth_error = await websocket_auth_manager.authenticate_websocket(websocket)
    
    if auth_error:
        logger.warning(f"WebSocket authentication failed: {auth_error}")
        error_code = websocket_auth_manager.get_error_code_for_reason(auth_error)
        await websocket_auth_manager.close_with_auth_error(websocket, auth_error, error_code)
        return
    
    # ТОЛЬКО ПОСЛЕ успешной аутентификации принимаем соединение
    try:
        await websocket.accept()
        logger.info(f"WebSocket accepted for user {user.id} (email: {user.email}), session_id={session_id}")
    except Exception as accept_error:
        logger.error(f"Failed to accept WebSocket connection for user {user.id}: {accept_error}", exc_info=True)
        if db:
            db.close()
        return
    
    # РЕГИСТРИРУЕМ соединение в менеджере
    try:
        await websocket_service.manager.connect(websocket, user.id, session_id)
        logger.info(f"WebSocket registered for user {user.id}, session_id={session_id}")
    except Exception as connect_error:
        logger.error(f"Failed to register WebSocket connection for user {user.id}: {connect_error}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Registration failed")
        except:
            pass
        if db:
            db.close()
        return
    
    # Отправляем клиенту событие об успешном подключении и список доступных каналов
    try:
        available_channels = [
            "admin_dashboard",
            "user_activity",
            "system_alerts",
            "moderation_queue",
            "notifications",
            "real_time_metrics",
            "backup_status",
            "task_updates"
        ]
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "payload": {
                "user_id": user.id,
                "session_id": session_id,
                "available_channels": available_channels
            },
            "timestamp": time.time()
        }))
    except Exception as init_err:
        logger.error(f"Failed to send connection_established to user {user.id}: {init_err}")

    # Основной цикл обработки сообщений с улучшенной стабильностью
    try:
        while True:
            try:
                # Используем таймаут для receive_text чтобы избежать зависания
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WEBSOCKET_CONNECTION_TIMEOUT * 6  # 60 секунд таймаут
                )

                # Проверяем размер сообщения
                if len(data.encode('utf-8')) > settings.WEBSOCKET_MAX_MESSAGE_SIZE:
                    logger.warning(f"Message too large from user {user.id}: {len(data)} bytes")
                    error_response = {
                        "type": "error",
                        "message": "Сообщение слишком большое",
                        "error_code": "message_too_large",
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue

                logger.debug(f"Received WebSocket message from user {user.id}: {data[:100]}...")

                # Передаём сообщение в сервис для обработки
                await websocket_service.handle_message(user.id, session_id, data)

            except asyncio.TimeoutError:
                # Таймаут receive - это нормально, продолжаем
                logger.debug(f"WebSocket receive timeout for user {user.id} (normal)")
                continue
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from user {user.id}: {e}")
                try:
                    error_response = {
                        "type": "error",
                        "message": "Неверный формат сообщения",
                        "error_code": "invalid_json",
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(error_response))
                except:
                    break
                continue
            except Exception as e:
                logger.error(f"Error processing WebSocket message from user {user.id}: {e}", exc_info=True)
                # Отправляем ошибку клиенту НО НЕ разрываем соединение
                try:
                    error_response = {
                        "type": "error",
                        "message": "Произошла ошибка при обработке сообщения. Попробуйте еще раз.",
                        "error_code": "message_processing_error",
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(error_response))
                except Exception as send_error:
                    logger.error(f"Failed to send error message to user {user.id}: {send_error}")
                    # Если не можем отправить ошибку, возможно соединение разорвано
                    break
                # НЕ делаем break - продолжаем работу
                continue
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Отключаем через менеджер (только если соединение было установлено)
        if user:
            try:
                await websocket_service.manager.disconnect(websocket, user.id, session_id)
            except Exception as e:
                logger.error(f"Error disconnecting user {user.id} from WebSocket: {e}")
        # Очищаем rate limiter при отключении (только для внешних IP)
        if client_ip and client_ip not in ["127.0.0.1", "nginx", "advakod_nginx"] and client_ip != "unknown":
            websocket_limiter.disconnect(client_ip)
        if db:
            db.close()


@router.get("/stats")
async def get_websocket_stats():
    """Получение статистики WebSocket соединений"""
    return websocket_service.get_connection_count()

@router.get("/stats/detailed")
async def get_detailed_websocket_stats():
    """Получение детальной статистики WebSocket соединений"""
    return websocket_service.get_detailed_stats()

@router.get("/stats/rate-limit")
async def get_rate_limit_stats():
    """Получение статистики rate limiting для WebSocket"""
    return websocket_limiter.get_stats()

@router.post("/cleanup")
async def cleanup_stale_connections():
    """Принудительная очистка устаревших соединений (только для админов)"""
    try:
        await websocket_service.manager.cleanup_stale_connections()
        return {"message": "Stale connections cleaned up successfully"}
    except Exception as e:
        logger.error(f"Error cleaning up stale connections: {e}")
        return {"error": str(e)}
