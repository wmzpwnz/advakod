"""
WebSocket API endpoints для real-time чата
"""
import json
import logging
import time
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.websocket_service import websocket_service

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()

# Rate limiting для WebSocket подключений
class WebSocketRateLimiter:
    def __init__(self, max_connections_per_ip: int = 3, window_seconds: int = 60):
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
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {current_connections} connections")
            return False
        
        self.connections[client_ip] += 1
        return True
    
    def disconnect(self, client_ip: str):
        if client_ip in self.connections:
            self.connections[client_ip] = max(0, self.connections[client_ip] - 1)

# Глобальный rate limiter - увеличиваем лимит для localhost
websocket_limiter = WebSocketRateLimiter(max_connections_per_ip=10, window_seconds=60)


async def get_current_user_from_token(token: str, db: Session) -> User:
    """Получение пользователя из JWT токена для WebSocket"""
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
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


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
    """Общая логика обработки WebSocket соединения"""
    logger.info("WebSocket connection started")
    
    # Проверяем rate limiting (отключаем для localhost)
    client_ip = websocket.client.host
    if client_ip != "127.0.0.1" and not websocket_limiter.check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        await websocket.close(code=1008, reason="Too many connections")
        return
    
    # Проверяем инициализацию сервиса
    if not hasattr(websocket_service, 'manager'):
        logger.error("WebSocket service not properly initialized!")
        await websocket.close(code=1011, reason="Service error")
        return
    
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="No token provided")
        return
    
    db = SessionLocal()
    user = None
    try:
        # Получаем пользователя из токена
        user = await get_current_user_from_token(token, db)
        
        # Подключаемся к WebSocket
        await websocket.accept()
        logger.info("WebSocket accepted")
        
        # РЕГИСТРИРУЕМ соединение в менеджере
        await websocket_service.manager.connect(websocket, user.id, session_id)
        logger.info(f"WebSocket registered for user {user.id}")
        
        # Основной цикл обработки сообщений
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    logger.info(f"Received WebSocket message from user {user.id}: {data}")
                    
                    # Передаём сообщение в сервис для обработки
                    await websocket_service.handle_message(user.id, session_id, data)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user.id}")
                    break
                except Exception as e:
                    logger.error(f"Error processing WebSocket message from user {user.id}: {e}")
                    # Отправляем ошибку клиенту вместо разрыва соединения
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Произошла ошибка при обработке сообщения. Попробуйте еще раз.",
                            "error_code": "processing_error"
                        }))
                    except:
                        pass
                    break
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(f"Error in WebSocket loop for user {user.id}: {e}")
            # Отправляем ошибку клиенту
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Произошла критическая ошибка. Соединение будет закрыто.",
                    "error_code": "critical_error"
                }))
            except:
                pass
            
    except HTTPException as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {e.detail}")
    except WebSocketDisconnect:
        # Обработка нормального отключения
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Отключаем через менеджер (только если соединение было установлено)
        if user and 'websocket' in locals():
            await websocket_service.manager.disconnect(websocket, user.id, session_id)
        # Очищаем rate limiter при отключении (только для внешних IP)
        if client_ip != "127.0.0.1":
            websocket_limiter.disconnect(client_ip)
        db.close()


@router.get("/stats")
async def get_websocket_stats():
    """Получение статистики WebSocket соединений"""
    return websocket_service.manager.get_connection_count()
