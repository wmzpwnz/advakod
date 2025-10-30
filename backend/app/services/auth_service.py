from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    def __init__(self):
        pass
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            # Используем bcrypt напрямую для избежания проблем с passlib
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        # Используем bcrypt напрямую
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по email или username"""
        # Сначала пробуем найти по email
        user = db.query(User).filter(User.email == email).first()
        
        # Если не найден по email, пробуем по username
        if not user:
            user = db.query(User).filter(User.username == email).first()
        
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None, is_admin: bool = False):
        """Создание JWT токена с разными сроками для админов и пользователей"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        elif is_admin:
            # Админские токены: увеличиваем срок жизни для стабильной работы админки
            expire = datetime.utcnow() + timedelta(hours=12)
            to_encode.update({"admin": True})
        else:
            # Обычные пользователи - 8 часов
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """Получение текущего пользователя по токену"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
                
            # Дополнительная проверка для админских токенов
            # Дополнительных проверок времени входа не делаем — опираемся на exp токена
                        
        except JWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        
        return user
    
    def get_current_active_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Получение активного пользователя.
        Важно: не используем Depends(get_current_user) напрямую, чтобы избежать
        проблемы FastAPI с unbound-методами (появление обязательного query-параметра 'self').
        """
        current_user = self.get_current_user(token=token, db=db)
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    def decode_token(self, token: str) -> dict:
        """Декодирование JWT токена"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

# Создаем глобальный экземпляр сервиса
auth_service = AuthService()
