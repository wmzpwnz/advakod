from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.subscription import (
    get_subscription_manager,
    SubscriptionTier,
    FeatureType,
    SubscriptionPlan,
    UserSubscription
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

class SubscriptionTierRequest(BaseModel):
    tier: str = Field(..., description="Уровень подписки")

class SubscriptionUpgradeRequest(BaseModel):
    new_tier: str = Field(..., description="Новый уровень подписки")
    payment_method: Optional[str] = Field(None, description="Способ оплаты")

class FeatureUsageRequest(BaseModel):
    feature_type: str = Field(..., description="Тип функции")
    amount: int = Field(default=1, description="Количество использования")

class SubscriptionPlanResponse(BaseModel):
    tier: str
    name: str
    description: str
    price: float
    billing_period: str
    features: Dict[str, Dict[str, Any]]
    max_users: int
    trial_days: int
    is_active: bool

class UserSubscriptionResponse(BaseModel):
    user_id: int
    plan: SubscriptionPlanResponse
    start_date: datetime
    end_date: datetime
    is_active: bool
    auto_renew: bool
    trial_end_date: Optional[datetime]
    usage_stats: Dict[str, int]

class UsageSummaryResponse(BaseModel):
    subscription: Dict[str, Any]
    features: Dict[str, Dict[str, Any]]

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение всех планов подписки"""
    try:
        manager = get_subscription_manager()
        plans = manager.get_all_plans()
        
        return [
            SubscriptionPlanResponse(
                tier=plan.tier.value,
                name=plan.name,
                description=plan.description,
                price=plan.price,
                billing_period=plan.billing_period,
                features={
                    feature.value: {
                        "limit": limit.limit,
                        "period": limit.period,
                        "description": _get_feature_description(feature)
                    }
                    for feature, limit in plan.features.items()
                },
                max_users=plan.max_users,
                trial_days=plan.trial_days,
                is_active=plan.is_active
            )
            for plan in plans
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{tier}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение конкретного плана подписки"""
    try:
        manager = get_subscription_manager()
        
        try:
            subscription_tier = SubscriptionTier(tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        plan = manager.get_plan(subscription_tier)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return SubscriptionPlanResponse(
            tier=plan.tier.value,
            name=plan.name,
            description=plan.description,
            price=plan.price,
            billing_period=plan.billing_period,
            features={
                feature.value: {
                    "limit": limit.limit,
                    "period": limit.period,
                    "description": _get_feature_description(feature)
                }
                for feature, limit in plan.features.items()
            },
            max_users=plan.max_users,
            trial_days=plan.trial_days,
            is_active=plan.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe", response_model=UserSubscriptionResponse)
async def create_subscription(
    request: SubscriptionTierRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание подписки"""
    try:
        manager = get_subscription_manager()
        
        try:
            subscription_tier = SubscriptionTier(request.tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        # Проверяем, есть ли уже подписка
        existing_subscription = manager.get_user_subscription(current_user.id)
        if existing_subscription and existing_subscription.is_active:
            raise HTTPException(status_code=400, detail="User already has an active subscription")
        
        # Создаем подписку
        subscription = manager.create_user_subscription(current_user.id, subscription_tier)
        
        return UserSubscriptionResponse(
            user_id=subscription.user_id,
            plan=SubscriptionPlanResponse(
                tier=subscription.plan.tier.value,
                name=subscription.plan.name,
                description=subscription.plan.description,
                price=subscription.plan.price,
                billing_period=subscription.plan.billing_period,
                features={
                    feature.value: {
                        "limit": limit.limit,
                        "period": limit.period,
                        "description": _get_feature_description(feature)
                    }
                    for feature, limit in subscription.plan.features.items()
                },
                max_users=subscription.plan.max_users,
                trial_days=subscription.plan.trial_days,
                is_active=subscription.plan.is_active
            ),
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_active=subscription.is_active,
            auto_renew=subscription.auto_renew,
            trial_end_date=subscription.trial_end_date,
            usage_stats=subscription.usage_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-subscription", response_model=UserSubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение текущей подписки пользователя"""
    try:
        manager = get_subscription_manager()
        subscription = manager.get_user_subscription(current_user.id)
        
        if not subscription:
            # Создаем бесплатную подписку
            subscription = manager.create_user_subscription(current_user.id, SubscriptionTier.FREE)
        
        return UserSubscriptionResponse(
            user_id=subscription.user_id,
            plan=SubscriptionPlanResponse(
                tier=subscription.plan.tier.value,
                name=subscription.plan.name,
                description=subscription.plan.description,
                price=subscription.plan.price,
                billing_period=subscription.plan.billing_period,
                features={
                    feature.value: {
                        "limit": limit.limit,
                        "period": limit.period,
                        "description": _get_feature_description(feature)
                    }
                    for feature, limit in subscription.plan.features.items()
                },
                max_users=subscription.plan.max_users,
                trial_days=subscription.plan.trial_days,
                is_active=subscription.plan.is_active
            ),
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_active=subscription.is_active,
            auto_renew=subscription.auto_renew,
            trial_end_date=subscription.trial_end_date,
            usage_stats=subscription.usage_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upgrade", response_model=UserSubscriptionResponse)
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление подписки"""
    try:
        manager = get_subscription_manager()
        
        try:
            new_tier = SubscriptionTier(request.new_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        # Проверяем, что новый тариф выше текущего
        current_subscription = manager.get_user_subscription(current_user.id)
        if not current_subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        current_tier_value = list(SubscriptionTier).index(current_subscription.plan.tier)
        new_tier_value = list(SubscriptionTier).index(new_tier)
        
        if new_tier_value <= current_tier_value:
            raise HTTPException(status_code=400, detail="New tier must be higher than current tier")
        
        # Обновляем подписку
        success = manager.upgrade_subscription(current_user.id, new_tier)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upgrade subscription")
        
        # Получаем обновленную подписку
        updated_subscription = manager.get_user_subscription(current_user.id)
        
        return UserSubscriptionResponse(
            user_id=updated_subscription.user_id,
            plan=SubscriptionPlanResponse(
                tier=updated_subscription.plan.tier.value,
                name=updated_subscription.plan.name,
                description=updated_subscription.plan.description,
                price=updated_subscription.plan.price,
                billing_period=updated_subscription.plan.billing_period,
                features={
                    feature.value: {
                        "limit": limit.limit,
                        "period": limit.period,
                        "description": _get_feature_description(feature)
                    }
                    for feature, limit in updated_subscription.plan.features.items()
                },
                max_users=updated_subscription.plan.max_users,
                trial_days=updated_subscription.plan.trial_days,
                is_active=updated_subscription.plan.is_active
            ),
            start_date=updated_subscription.start_date,
            end_date=updated_subscription.end_date,
            is_active=updated_subscription.is_active,
            auto_renew=updated_subscription.auto_renew,
            trial_end_date=updated_subscription.trial_end_date,
            usage_stats=updated_subscription.usage_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отмена подписки"""
    try:
        manager = get_subscription_manager()
        
        success = manager.cancel_subscription(current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel subscription")
        
        return {"message": "Subscription cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение сводки по использованию"""
    try:
        manager = get_subscription_manager()
        usage_summary = manager.get_usage_summary(current_user.id)
        
        return UsageSummaryResponse(**usage_summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-feature-access")
async def check_feature_access(
    request: FeatureUsageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Проверка доступа к функции"""
    try:
        manager = get_subscription_manager()
        
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feature type")
        
        has_access, message = manager.check_feature_access(current_user.id, feature_type)
        
        return {
            "feature_type": request.feature_type,
            "has_access": has_access,
            "message": message,
            "current_usage": manager.get_feature_usage(current_user.id, feature_type, "monthly"),
            "limit": manager.get_user_subscription(current_user.id).plan.features[feature_type].limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/use-feature")
async def use_feature(
    request: FeatureUsageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Использование функции"""
    try:
        manager = get_subscription_manager()
        
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feature type")
        
        # Проверяем доступ
        has_access, message = manager.check_feature_access(current_user.id, feature_type)
        if not has_access:
            raise HTTPException(status_code=403, detail=message)
        
        # Увеличиваем счетчик использования
        manager.increment_feature_usage(current_user.id, feature_type, request.amount)
        
        return {
            "message": "Feature used successfully",
            "feature_type": request.feature_type,
            "amount": request.amount,
            "remaining_usage": manager.get_usage_summary(current_user.id)["features"][request.feature_type]["remaining"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_subscription_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики подписок (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_subscription_manager()
        stats = manager.get_subscription_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_feature_description(feature_type: FeatureType) -> str:
    """Получение описания функции"""
    descriptions = {
        FeatureType.CHAT_MESSAGES: "Сообщения в чате с ИИ",
        FeatureType.DOCUMENT_ANALYSIS: "Анализ документов",
        FeatureType.API_CALLS: "API вызовы",
        FeatureType.STORAGE: "Хранилище файлов (МБ)",
        FeatureType.EXPORT_REPORTS: "Экспорт отчетов",
        FeatureType.PRIORITY_SUPPORT: "Приоритетная поддержка",
        FeatureType.ADVANCED_ANALYTICS: "Расширенная аналитика",
        FeatureType.CUSTOM_INTEGRATIONS: "Пользовательские интеграции",
        FeatureType.WHITE_LABEL: "Белый лейбл"
    }
    return descriptions.get(feature_type, "Неизвестная функция")
