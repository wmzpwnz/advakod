"""
Admin WebSocket API endpoints для real-time админ-панели
"""
import json
import logging
import time
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional

from ..services.websocket_auth_manager import websocket_auth_manager
from ..services.admin_websocket_service import admin_websocket_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting для Admin WebSocket подключений
class AdminWebSocketRateLimiter:
    def __init__(self, max_connections_per_ip: int = 5, window_seconds: int = 60):
        self.connections = defaultdict(int)
        self.max_connections = max_connections_per_ip
        self.window_seconds = window_seconds
        self.last_cleanup = time.time()
    
    def check_rate_limit(self, client_ip: str) -> bool:
        current_time = time.time()
        
        # Очистка старых записей каждую минуту
        if current_time - self.last_cleanup > self.window_seconds:
            self.connections.clear()
            self.last_cleanup = current_time
        
        current_connections = self.connections[client_ip]
        if current_connections >= self.max_connections:
            logger.warning(f"Admin WebSocket rate limit exceeded for IP {client_ip}: {current_connections} connections")
            return False
        
        self.connections[client_ip] += 1
        return True
    
    def disconnect(self, client_ip: str):
        if client_ip in self.connections:
            self.connections[client_ip] = max(0, self.connections[client_ip] - 1)

# Глобальный rate limiter для админов
admin_websocket_limiter = AdminWebSocketRateLimiter(max_connections_per_ip=10, window_seconds=60)


@router.websocket("/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    """Admin WebSocket endpoint для админ-панели"""
    await handle_admin_websocket_connection(websocket)


async def handle_admin_websocket_connection(websocket: WebSocket):
    """Обработка Admin WebSocket соединения"""
    logger.info("Admin WebSocket connection started")
    
    # Проверяем rate limiting
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"Admin client IP: {client_ip}")
    if client_ip and client_ip not in ["127.0.0.1", "nginx", "advakod_nginx"] and client_ip != "unknown":
        if not admin_websocket_limiter.check_rate_limit(client_ip):
            logger.warning(f"Admin WebSocket rate limit exceeded for IP {client_ip}")
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return
    
    # КРИТИЧНО: Аутентификация ДО accept() с требованием прав администратора
    user, db, auth_error = await websocket_auth_manager.authenticate_websocket(
        websocket, 
        require_admin=True
    )
    
    if auth_error:
        logger.warning(f"Admin WebSocket authentication failed: {auth_error}")
        error_code = websocket_auth_manager.get_error_code_for_reason(auth_error)
        await websocket_auth_manager.close_with_auth_error(websocket, auth_error, error_code)
        return
    
    # ТОЛЬКО ПОСЛЕ успешной аутентификации принимаем соединение
    try:
        await websocket.accept()
        logger.info(f"Admin WebSocket accepted for user {user.id} (email: {user.email})")
    except Exception as accept_error:
        logger.error(f"Failed to accept Admin WebSocket connection for user {user.id}: {accept_error}", exc_info=True)
        if db:
            db.close()
        return
    
    # Определяем роль пользователя
    user_role = "super_admin" if user.is_admin else "admin"
    
    # РЕГИСТРИРУЕМ соединение в админ менеджере
    try:
        await admin_websocket_service.connect_admin(websocket, user.id, user_role)
        logger.info(f"Admin WebSocket registered for user {user.id} with role {user_role}")
    except Exception as connect_error:
        logger.error(f"Failed to register Admin WebSocket connection for user {user.id}: {connect_error}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Registration failed")
        except:
            pass
        if db:
            db.close()
        return
    
    # Основной цикл обработки сообщений
    try:
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received Admin WebSocket message from user {user.id}: {data}")
                
                # Передаём сообщение в админ сервис для обработки
                await admin_websocket_service.handle_admin_message(user.id, user_role, data)
                
            except WebSocketDisconnect:
                logger.info(f"Admin WebSocket disconnected for user {user.id}")
                break
            except Exception as e:
                logger.error(f"Error processing Admin WebSocket message from user {user.id}: {e}", exc_info=True)
                # Отправляем ошибку клиенту НО НЕ разрываем соединение
                try:
                    error_response = {
                        "type": "error",
                        "payload": {
                            "message": "Произошла ошибка при обработке сообщения. Попробуйте еще раз.",
                            "error_code": "admin_message_processing_error"
                        },
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(error_response))
                except Exception as send_error:
                    logger.error(f"Failed to send error message to admin user {user.id}: {send_error}")
                    # Если не можем отправить ошибку, возможно соединение разорвано
                    break
                # НЕ делаем break - продолжаем работу
                continue
                
    except WebSocketDisconnect:
        logger.info(f"Admin WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"Error in Admin WebSocket loop for user {user.id}: {e}")
        # Отправляем ошибку клиенту
        try:
            error_response = {
                "type": "error",
                "payload": {
                    "message": "Произошла критическая ошибка. Соединение будет закрыто.",
                    "error_code": "admin_connection_error",
                    "reconnect_suggested": True
                },
                "timestamp": time.time()
            }
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
    finally:
        # Отключаем через админ менеджер
        if user:
            try:
                await admin_websocket_service.disconnect_admin(websocket, user.id)
            except Exception as e:
                logger.error(f"Error disconnecting admin user {user.id} from WebSocket: {e}")
        
        # Очищаем rate limiter при отключении (только для внешних IP)
        if client_ip and client_ip not in ["127.0.0.1", "nginx", "advakod_nginx"] and client_ip != "unknown":
            admin_websocket_limiter.disconnect(client_ip)
        
        if db:
            db.close()


@router.get("/admin/stats")
async def get_admin_websocket_stats():
    """Получение статистики Admin WebSocket соединений"""
    return admin_websocket_service.get_connection_stats()