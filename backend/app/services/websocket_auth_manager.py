"""
WebSocket Authentication Manager
Централизованная аутентификация для WebSocket соединений
"""
import logging
import time
from typing import Optional, Tuple
from fastapi import WebSocket
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.user import User
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)


class WebSocketAuthManager:
    """Менеджер аутентификации для WebSocket соединений"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    async def authenticate_websocket(
        self, 
        websocket: WebSocket, 
        require_admin: bool = False
    ) -> Tuple[Optional[User], Optional[Session], Optional[str]]:
        """
        Аутентификация WebSocket соединения
        
        Args:
            websocket: WebSocket соединение
            require_admin: Требовать права администратора
            
        Returns:
            Tuple[User, Session, error_reason] - пользователь, сессия БД и причина ошибки
            Если аутентификация успешна, error_reason = None
        """
        db = None
        
        try:
            # Получаем токен из query параметров
            token = websocket.query_params.get("token")
            if not token:
                logger.warning("WebSocket connection attempt without token")
                return None, None, "Authentication required"
            
            # Создаем сессию БД
            db = SessionLocal()
            
            # Декодируем и валидируем токен
            try:
                payload = self.auth_service.decode_token(token)
            except Exception as e:
                logger.warning(f"WebSocket auth: Invalid token - {e}")
                if db:
                    db.close()
                return None, None, "Invalid token"
            
            # Получаем email из токена
            email = payload.get("sub")
            if not email:
                logger.warning("WebSocket auth: Token missing email")
                if db:
                    db.close()
                return None, None, "Invalid token format"
            
            # Проверяем срок действия токена
            exp = payload.get("exp")
            if exp and time.time() > exp:
                logger.warning(f"WebSocket auth: Expired token for {email}")
                if db:
                    db.close()
                return None, None, "Token expired"
            
            # Получаем пользователя из БД
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"WebSocket auth: User not found for email: {email}")
                if db:
                    db.close()
                return None, None, "User not found"
            
            # Проверяем активность пользователя
            if not user.is_active:
                logger.warning(f"WebSocket auth: Inactive user {user.id}")
                if db:
                    db.close()
                return None, None, "Account inactive"
            
            # Проверяем права администратора если требуется
            if require_admin and not user.is_admin:
                logger.warning(f"WebSocket auth: User {user.id} is not admin")
                if db:
                    db.close()
                return None, None, "Admin access required"
            
            # Дополнительная проверка для админских токенов
            if require_admin and payload.get("admin", False):
                admin_login_time = payload.get("admin_login_time")
                if admin_login_time:
                    from datetime import datetime, timedelta
                    try:
                        login_time = datetime.fromisoformat(admin_login_time)
                        if datetime.utcnow() - login_time > timedelta(minutes=30):
                            logger.warning(f"WebSocket auth: Admin session expired for {user.id}")
                            if db:
                                db.close()
                            return None, None, "Admin session expired"
                    except ValueError:
                        logger.warning(f"WebSocket auth: Invalid admin login time format")
            
            logger.info(f"WebSocket authentication successful for user {user.id} ({user.email})")
            return user, db, None
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            if db:
                db.close()
            return None, None, "Authentication error"
    
    async def close_with_auth_error(
        self, 
        websocket: WebSocket, 
        error_reason: str, 
        code: int = 1008
    ):
        """
        Закрытие WebSocket соединения с ошибкой аутентификации
        
        Args:
            websocket: WebSocket соединение
            error_reason: Причина ошибки
            code: Код закрытия WebSocket
        """
        try:
            await websocket.close(code=code, reason=error_reason)
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")
    
    def get_error_code_for_reason(self, error_reason: str) -> int:
        """
        Получение кода ошибки WebSocket по причине
        
        Args:
            error_reason: Причина ошибки
            
        Returns:
            Код ошибки WebSocket
        """
        error_codes = {
            "Authentication required": 1008,
            "Invalid token": 1008,
            "Invalid token format": 1008,
            "Token expired": 1008,
            "User not found": 1008,
            "Account inactive": 1008,
            "Admin access required": 1003,  # Unsupported data
            "Admin session expired": 1008,
            "Authentication error": 1011,  # Internal error
        }
        return error_codes.get(error_reason, 1011)


# Глобальный экземпляр менеджера аутентификации
websocket_auth_manager = WebSocketAuthManager()