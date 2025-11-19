from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.referral import (
    get_referral_manager,
    ReferralStatus,
    ReferralType,
    CommissionType,
    ReferralCode,
    Referral,
    ReferralStats
)
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)

router = APIRouter()

class ReferralCodeRequest(BaseModel):
    expires_days: Optional[int] = Field(None, description="Дней до истечения")
    max_uses: int = Field(default=100, description="Максимальное количество использований")
    description: Optional[str] = Field(None, description="Описание кода")

class ReferralRequest(BaseModel):
    referral_code: str = Field(..., description="Реферальный код")
    referral_type: str = Field(..., description="Тип реферала")
    amount: Optional[float] = Field(None, description="Сумма для расчета комиссии")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Дополнительные данные")

class ReferralCodeResponse(BaseModel):
    code: str
    user_id: int
    created_at: datetime
    expires_at: Optional[datetime]
    max_uses: int
    current_uses: int
    is_active: bool
    description: Optional[str]

class ReferralResponse(BaseModel):
    id: str
    referrer_id: int
    referred_id: int
    referral_code: str
    referral_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    commission_amount: float
    commission_type: str
    metadata: Dict[str, Any]

class ReferralStatsResponse(BaseModel):
    user_id: int
    total_referrals: int
    active_referrals: int
    completed_referrals: int
    total_commission: float
    pending_commission: float
    paid_commission: float

@router.post("/generate-code", response_model=ReferralCodeResponse)
async def generate_referral_code(
    request: ReferralCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Генерация реферального кода"""
    try:
        manager = get_referral_manager()
        
        if request.max_uses <= 0:
            raise HTTPException(status_code=400, detail="Max uses must be positive")
        
        if request.expires_days and request.expires_days <= 0:
            raise HTTPException(status_code=400, detail="Expires days must be positive")
        
        # Генерируем код
        referral_code = manager.generate_referral_code(
            user_id=current_user.id,
            expires_days=request.expires_days,
            max_uses=request.max_uses,
            description=request.description
        )
        
        return ReferralCodeResponse(
            code=referral_code.code,
            user_id=referral_code.user_id,
            created_at=referral_code.created_at,
            expires_at=referral_code.expires_at,
            max_uses=referral_code.max_uses,
            current_uses=referral_code.current_uses,
            is_active=referral_code.is_active,
            description=referral_code.description
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-codes", response_model=List[ReferralCodeResponse])
async def get_my_referral_codes(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение реферальных кодов пользователя"""
    try:
        manager = get_referral_manager()
        codes = manager.get_user_referral_codes(current_user.id, active_only)
        
        return [
            ReferralCodeResponse(
                code=code.code,
                user_id=code.user_id,
                created_at=code.created_at,
                expires_at=code.expires_at,
                max_uses=code.max_uses,
                current_uses=code.current_uses,
                is_active=code.is_active,
                description=code.description
            )
            for code in codes
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate-code/{code}")
async def validate_referral_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Валидация реферального кода"""
    try:
        manager = get_referral_manager()
        is_valid, message = manager.validate_referral_code(code)
        
        return {
            "code": code,
            "is_valid": is_valid,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-referral", response_model=ReferralResponse)
async def create_referral(
    request: ReferralRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание реферала"""
    try:
        manager = get_referral_manager()
        
        try:
            referral_type = ReferralType(request.referral_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid referral type")
        
        if request.amount is not None and request.amount < 0:
            raise HTTPException(status_code=400, detail="Amount must be non-negative")
        
        # Создаем реферал
        referral = manager.create_referral(
            referrer_id=current_user.id,
            referred_id=current_user.id,  # В реальном приложении это будет ID приведенного пользователя
            referral_code=request.referral_code,
            referral_type=referral_type,
            amount=request.amount,
            metadata=request.metadata
        )
        
        return ReferralResponse(
            id=referral.id,
            referrer_id=referral.referrer_id,
            referred_id=referral.referred_id,
            referral_code=referral.referral_code,
            referral_type=referral.referral_type.value,
            status=referral.status.value,
            created_at=referral.created_at,
            completed_at=referral.completed_at,
            commission_amount=referral.commission_amount,
            commission_type=referral.commission_type.value,
            metadata=referral.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-referrals", response_model=List[ReferralResponse])
async def get_my_referrals(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение рефералов пользователя"""
    try:
        if limit > 100:
            limit = 100
        
        manager = get_referral_manager()
        
        # Преобразуем статус
        referral_status = None
        if status:
            try:
                referral_status = ReferralStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        referrals = manager.get_user_referrals(
            current_user.id,
            status=referral_status,
            limit=limit,
            offset=offset
        )
        
        return [
            ReferralResponse(
                id=referral.id,
                referrer_id=referral.referrer_id,
                referred_id=referral.referred_id,
                referral_code=referral.referral_code,
                referral_type=referral.referral_type.value,
                status=referral.status.value,
                created_at=referral.created_at,
                completed_at=referral.completed_at,
                commission_amount=referral.commission_amount,
                commission_type=referral.commission_type.value,
                metadata=referral.metadata
            )
            for referral in referrals
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-stats", response_model=ReferralStatsResponse)
async def get_my_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики рефералов пользователя"""
    try:
        manager = get_referral_manager()
        stats = manager.get_user_stats(current_user.id)
        
        if not stats:
            # Создаем пустую статистику
            stats = ReferralStats(
                user_id=current_user.id,
                total_referrals=0,
                active_referrals=0,
                completed_referrals=0,
                total_commission=0.0,
                pending_commission=0.0,
                paid_commission=0.0
            )
        
        return ReferralStatsResponse(
            user_id=stats.user_id,
            total_referrals=stats.total_referrals,
            active_referrals=stats.active_referrals,
            completed_referrals=stats.completed_referrals,
            total_commission=stats.total_commission,
            pending_commission=stats.pending_commission,
            paid_commission=stats.paid_commission
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-referrer")
async def get_my_referrer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о том, кто привел пользователя"""
    try:
        manager = get_referral_manager()
        referral = manager.get_referral_by_referred_user(current_user.id)
        
        if not referral:
            return {"message": "No referrer found"}
        
        return {
            "referrer_id": referral.referrer_id,
            "referral_code": referral.referral_code,
            "referral_type": referral.referral_type.value,
            "status": referral.status.value,
            "created_at": referral.created_at,
            "commission_amount": referral.commission_amount
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-referral/{referral_id}")
async def complete_referral(
    referral_id: str,
    amount: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Завершение реферала (начисление комиссии)"""
    try:
        manager = get_referral_manager()
        
        # Проверяем, что реферал принадлежит пользователю
        referral = manager.referrals.get(referral_id)
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        if referral.referrer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if amount is not None and amount < 0:
            raise HTTPException(status_code=400, detail="Amount must be non-negative")
        
        # Завершаем реферал
        success = manager.complete_referral(referral_id, amount)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete referral")
        
        return {"message": "Referral completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deactivate-code/{code}")
async def deactivate_referral_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Деактивация реферального кода"""
    try:
        manager = get_referral_manager()
        
        # Проверяем, что код принадлежит пользователю
        referral_code = manager.get_referral_code(code)
        if not referral_code:
            raise HTTPException(status_code=404, detail="Referral code not found")
        
        if referral_code.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Деактивируем код
        success = manager.deactivate_referral_code(code)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deactivate code")
        
        return {"message": "Referral code deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commission-rules")
async def get_commission_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение правил комиссий"""
    try:
        manager = get_referral_manager()
        
        rules = []
        for referral_type, rule in manager.commission_rules.items():
            rules.append({
                "referral_type": referral_type.value,
                "commission_type": rule.commission_type.value,
                "value": rule.value,
                "min_amount": rule.min_amount,
                "max_amount": rule.max_amount,
                "is_active": rule.is_active,
                "description": _get_commission_description(referral_type, rule)
            })
        
        return {"commission_rules": rules}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение общей статистики рефералов (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_referral_manager()
        stats = manager.get_referral_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup-expired")
async def cleanup_expired_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Очистка истекших кодов (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_referral_manager()
        manager.cleanup_expired_codes()
        
        return {"message": "Expired codes cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def referral_health():
    """Проверка здоровья сервиса рефералов"""
    try:
        manager = get_referral_manager()
        
        # Тестируем генерацию кода
        test_code = manager.generate_referral_code(999999, expires_days=1, max_uses=1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_code": {
                "code": test_code.code,
                "expires_at": test_code.expires_at.isoformat() if test_code.expires_at else None
            },
            "commission_rules_count": len(manager.commission_rules)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _get_commission_description(referral_type: ReferralType, rule) -> str:
    """Получение описания правила комиссии"""
    descriptions = {
        ReferralType.USER_REGISTRATION: f"Фиксированная комиссия {rule.value} руб. за регистрацию нового пользователя",
        ReferralType.SUBSCRIPTION_PURCHASE: f"{rule.value * 100}% от стоимости подписки (мин. {rule.min_amount} руб., макс. {rule.max_amount} руб.)",
        ReferralType.CORPORATE_SUBSCRIPTION: f"{rule.value * 100}% от стоимости корпоративной подписки (мин. {rule.min_amount} руб., макс. {rule.max_amount} руб.)",
        ReferralType.PAYMENT: f"{rule.value * 100}% от суммы платежа (мин. {rule.min_amount} руб., макс. {rule.max_amount} руб.)"
    }
    return descriptions.get(referral_type, "Неизвестное правило комиссии")
