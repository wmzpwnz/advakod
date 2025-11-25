"""
API endpoints для двухфакторной аутентификации
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.two_factor_service import two_factor_service

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]


class TwoFactorConfirmRequest(BaseModel):
    token: str


class TwoFactorVerifyRequest(BaseModel):
    token: str


class TwoFactorStatusResponse(BaseModel):
    enabled: bool
    has_secret: bool
    backup_codes_count: int


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Настройка 2FA для пользователя"""
    
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA уже включен для этого пользователя"
        )
    
    try:
        secret, qr_code, backup_codes = two_factor_service.setup_2fa(current_user, db)
        
        return TwoFactorSetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
        
    except Exception as e:
        logger.error(f"Error setting up 2FA for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при настройке 2FA"
        )


@router.post("/confirm")
async def confirm_2fa_setup(
    request: TwoFactorConfirmRequest,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Подтверждение настройки 2FA"""
    
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA уже включен для этого пользователя"
        )
    
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала настройте 2FA"
        )
    
    try:
        if two_factor_service.confirm_2fa_setup(current_user, request.token, db):
            return {
                "message": "2FA успешно включен",
                "enabled": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный токен"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming 2FA for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при подтверждении 2FA"
        )


@router.post("/verify")
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Проверка 2FA токена"""
    
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не включен для этого пользователя"
        )
    
    try:
        if two_factor_service.verify_2fa(current_user, request.token, db):
            return {
                "message": "Токен подтвержден",
                "verified": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный токен или резервный код"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при проверке 2FA"
        )


@router.post("/disable")
async def disable_2fa(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отключение 2FA"""
    
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не включен для этого пользователя"
        )
    
    try:
        two_factor_service.disable_2fa(current_user, db)
        
        return {
            "message": "2FA успешно отключен",
            "enabled": False
        }
        
    except Exception as e:
        logger.error(f"Error disabling 2FA for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отключении 2FA"
        )


@router.get("/status", response_model=TwoFactorStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение статуса 2FA"""
    
    try:
        status_info = two_factor_service.get_2fa_status(current_user)
        
        return TwoFactorStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Error getting 2FA status for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статуса 2FA"
        )


@router.post("/regenerate-backup-codes")
async def regenerate_backup_codes(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Регенерация резервных кодов"""
    
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не включен для этого пользователя"
        )
    
    try:
        backup_codes = two_factor_service.regenerate_backup_codes(current_user, db)
        
        return {
            "message": "Резервные коды регенерированы",
            "backup_codes": backup_codes
        }
        
    except Exception as e:
        logger.error(f"Error regenerating backup codes for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регенерации резервных кодов"
        )
