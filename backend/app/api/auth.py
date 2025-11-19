from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin, Token, User as UserSchema
from ..services.auth_service import AuthService
from ..services.audit_service import log_user_login, log_user_logout, log_security_incident, get_audit_service
from ..core.validators import validate_email, validate_password, validate_username, validate_full_name
from ..models.audit_log import ActionType, SeverityLevel
from ..core.admin_security import admin_security

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()


@router.post("/register", response_model=UserSchema)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Валидируем входные данные
    validated_email = validate_email(user_data.email)
    validated_password = validate_password(user_data.password)
    validated_username = validate_username(user_data.username)
    validated_full_name = validate_full_name(user_data.full_name)
    
    # Проверяем, существует ли пользователь с таким email
    existing_user = db.query(User).filter(User.email == validated_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Проверяем, существует ли пользователь с таким username
    existing_username = db.query(User).filter(User.username == validated_username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Создаем нового пользователя
    hashed_password = auth_service.get_password_hash(validated_password)
    
    db_user = User(
        email=validated_email,
        username=validated_username,
        hashed_password=hashed_password,
        full_name=validated_full_name,
        company_name=user_data.company_name,
        legal_form=user_data.legal_form,
        inn=user_data.inn,
        ogrn=user_data.ogrn
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None):
    """Вход пользователя"""
    # form_data.username может содержать email
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Логируем неудачную попытку входа
        log_security_incident(
            db=db,
            event_type="failed_login",
            user_id=None,
            request=request,
            details={"username": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен с учетом админских прав
    if user.is_admin:
        # Админские токены - короткий срок жизни (30 минут)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, is_admin=True
        )
    else:
        # Обычные пользователи - стандартный срок (8 часов)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
    
    # Логируем успешный вход
    try:
        log_user_login(db=db, user=user, request=request, success=True)
    except Exception as e:
        # Если аудит логи не работают, не прерываем процесс входа
        logger.warning(f"Failed to log user login: {e}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-email", response_model=Token)
async def login_with_email(login_data: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя по email"""
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен с учетом админских прав
    if user.is_admin:
        # Админские токены - короткий срок жизни (30 минут)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, is_admin=True
        )
    else:
        # Обычные пользователи - стандартный срок (8 часов)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/admin-login", response_model=Token)
async def admin_login(
    login_data: UserLogin, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Специальный эндпоинт для входа администраторов с дополнительными проверками"""
    
    # Проверки безопасности для админки
    logger.info("🔒 Проверяем безопасность админки")
    
    # 1. Проверка IP whitelist отключена для всех админов
    # if settings.ENVIRONMENT == "production" and not admin_security.check_admin_ip_access(request):
    #     admin_security.record_failed_admin_login(request)
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Доступ к админке разрешен только с авторизованных IP адресов"
    #     )
    
    # 2. Проверка на brute force
    if not admin_security.check_admin_brute_force(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много неудачных попыток входа. Попробуйте позже."
        )
    
    # 3. Аутентификация
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        admin_security.record_failed_admin_login(request)
        log_security_incident(
            db=db,
            event_type="failed_admin_login",
            user_id=None,
            request=request,
            details={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3.5. Проверка 2FA для админов (обязательна)
    if user.two_factor_enabled:
        # Требуем 2FA токен в заголовке
        two_factor_token = request.headers.get("X-2FA-Token")
        if not two_factor_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется 2FA токен для входа администратора"
            )
        
        from ..services.two_factor_service import two_factor_service
        if not two_factor_service.verify_2fa(user, two_factor_token):
            admin_security.record_failed_admin_login(request)
            log_security_incident(
                db=db,
                event_type="failed_2fa_admin_login",
                user_id=user.id,
                request=request,
                details={"email": login_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный 2FA токен"
            )
    else:
        # Для админов 2FA обязательна - ВРЕМЕННО ОТКЛЮЧЕНО ДЛЯ СУПЕРАДМИНА
        # TODO: Включить обратно после настройки 2FA
        logger.warning("⚠️ Админ входит без 2FA - это временно разрешено для разработки")
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail="Для администраторов обязательна настройка 2FA"
        # )
    
    # 4. Проверка админских прав
    if not user.is_admin:
        admin_security.record_failed_admin_login(request)
        log_security_incident(
            db=db,
            event_type="non_admin_login_attempt",
            user_id=user.id,
            request=request,
            details={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только администраторам"
        )
    
    # 5. Проверка активности аккаунта
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт администратора деактивирован"
        )
    
    # 6. Создаем админский токен (30 минут)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, is_admin=True
    )
    
    # 7. Логируем успешный админский вход
    try:
        log_user_login(db=db, user=user, request=request, success=True)
        
        # Дополнительное логирование для админов
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=user.id,
            action=ActionType.ADMIN_LOGIN,
            resource="admin_panel",
            resource_id=None,
            description=f"Успешный вход администратора {user.email}",
            details=None,
            request=request,
            severity=SeverityLevel.HIGH,
            status="success",
            error_message=None,
            request_id=None,
            duration_ms=None
        )
        logger.info(f"✅ Админ {user.email} успешно вошел в систему")
    except Exception as e:
        logger.error(f"❌ Ошибка логирования админ входа: {e}")
        # Не прерываем процесс входа из-за ошибки логирования
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": 1800,  # 30 минут в секундах
        "admin": True
    }


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_update: dict,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление информации о текущем пользователе"""
    for field, value in user_update.items():
        if hasattr(current_user, field) and value is not None:
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
