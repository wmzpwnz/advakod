import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """Уровни подписки"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class FeatureType(Enum):
    """Типы функций"""
    CHAT_MESSAGES = "chat_messages"
    DOCUMENT_ANALYSIS = "document_analysis"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    EXPORT_REPORTS = "export_reports"
    PRIORITY_SUPPORT = "priority_support"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    WHITE_LABEL = "white_label"

@dataclass
class FeatureLimit:
    """Ограничение функции"""
    feature_type: FeatureType
    limit: int  # -1 означает безлимит
    period: str  # daily, monthly, yearly
    reset_date: Optional[datetime] = None

@dataclass
class SubscriptionPlan:
    """План подписки"""
    tier: SubscriptionTier
    name: str
    description: str
    price: float  # в рублях
    billing_period: str  # monthly, yearly
    features: Dict[FeatureType, FeatureLimit]
    max_users: int  # -1 означает безлимит
    trial_days: int
    is_active: bool = True

@dataclass
class UserSubscription:
    """Подписка пользователя"""
    user_id: int
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime
    is_active: bool
    auto_renew: bool
    trial_end_date: Optional[datetime] = None
    usage_stats: Dict[FeatureType, int] = None

class SubscriptionManager:
    """Менеджер подписок и ограничений"""
    
    def __init__(self):
        self.plans = self._initialize_plans()
        self.user_subscriptions: Dict[int, UserSubscription] = {}
        self.usage_tracking: Dict[int, Dict[FeatureType, Dict[str, int]]] = {}
    
    def _initialize_plans(self) -> Dict[SubscriptionTier, SubscriptionPlan]:
        """Инициализация планов подписки"""
        return {
            SubscriptionTier.FREE: SubscriptionPlan(
                tier=SubscriptionTier.FREE,
                name="Бесплатный",
                description="Базовые возможности для знакомства с сервисом",
                price=0.0,
                billing_period="monthly",
                features={
                    FeatureType.CHAT_MESSAGES: FeatureLimit(FeatureType.CHAT_MESSAGES, 10, "daily"),
                    FeatureType.DOCUMENT_ANALYSIS: FeatureLimit(FeatureType.DOCUMENT_ANALYSIS, 3, "daily"),
                    FeatureType.API_CALLS: FeatureLimit(FeatureType.API_CALLS, 100, "monthly"),
                    FeatureType.STORAGE: FeatureLimit(FeatureType.STORAGE, 100, "monthly"),  # MB
                    FeatureType.EXPORT_REPORTS: FeatureLimit(FeatureType.EXPORT_REPORTS, 0, "monthly"),
                    FeatureType.PRIORITY_SUPPORT: FeatureLimit(FeatureType.PRIORITY_SUPPORT, 0, "monthly"),
                    FeatureType.ADVANCED_ANALYTICS: FeatureLimit(FeatureType.ADVANCED_ANALYTICS, 0, "monthly"),
                    FeatureType.CUSTOM_INTEGRATIONS: FeatureLimit(FeatureType.CUSTOM_INTEGRATIONS, 0, "monthly"),
                    FeatureType.WHITE_LABEL: FeatureLimit(FeatureType.WHITE_LABEL, 0, "monthly")
                },
                max_users=1,
                trial_days=0
            ),
            
            SubscriptionTier.BASIC: SubscriptionPlan(
                tier=SubscriptionTier.BASIC,
                name="Базовый",
                description="Для индивидуальных юристов и малого бизнеса",
                price=2990.0,
                billing_period="monthly",
                features={
                    FeatureType.CHAT_MESSAGES: FeatureLimit(FeatureType.CHAT_MESSAGES, 100, "daily"),
                    FeatureType.DOCUMENT_ANALYSIS: FeatureLimit(FeatureType.DOCUMENT_ANALYSIS, 20, "daily"),
                    FeatureType.API_CALLS: FeatureLimit(FeatureType.API_CALLS, 1000, "monthly"),
                    FeatureType.STORAGE: FeatureLimit(FeatureType.STORAGE, 1000, "monthly"),  # MB
                    FeatureType.EXPORT_REPORTS: FeatureLimit(FeatureType.EXPORT_REPORTS, 50, "monthly"),
                    FeatureType.PRIORITY_SUPPORT: FeatureLimit(FeatureType.PRIORITY_SUPPORT, 1, "monthly"),
                    FeatureType.ADVANCED_ANALYTICS: FeatureLimit(FeatureType.ADVANCED_ANALYTICS, 0, "monthly"),
                    FeatureType.CUSTOM_INTEGRATIONS: FeatureLimit(FeatureType.CUSTOM_INTEGRATIONS, 0, "monthly"),
                    FeatureType.WHITE_LABEL: FeatureLimit(FeatureType.WHITE_LABEL, 0, "monthly")
                },
                max_users=1,
                trial_days=14
            ),
            
            SubscriptionTier.PREMIUM: SubscriptionPlan(
                tier=SubscriptionTier.PREMIUM,
                name="Премиум",
                description="Для юридических фирм и среднего бизнеса",
                price=7990.0,
                billing_period="monthly",
                features={
                    FeatureType.CHAT_MESSAGES: FeatureLimit(FeatureType.CHAT_MESSAGES, 500, "daily"),
                    FeatureType.DOCUMENT_ANALYSIS: FeatureLimit(FeatureType.DOCUMENT_ANALYSIS, 100, "daily"),
                    FeatureType.API_CALLS: FeatureLimit(FeatureType.API_CALLS, 10000, "monthly"),
                    FeatureType.STORAGE: FeatureLimit(FeatureType.STORAGE, 10000, "monthly"),  # MB
                    FeatureType.EXPORT_REPORTS: FeatureLimit(FeatureType.EXPORT_REPORTS, 200, "monthly"),
                    FeatureType.PRIORITY_SUPPORT: FeatureLimit(FeatureType.PRIORITY_SUPPORT, 1, "monthly"),
                    FeatureType.ADVANCED_ANALYTICS: FeatureLimit(FeatureType.ADVANCED_ANALYTICS, 1, "monthly"),
                    FeatureType.CUSTOM_INTEGRATIONS: FeatureLimit(FeatureType.CUSTOM_INTEGRATIONS, 2, "monthly"),
                    FeatureType.WHITE_LABEL: FeatureLimit(FeatureType.WHITE_LABEL, 0, "monthly")
                },
                max_users=5,
                trial_days=14
            ),
            
            SubscriptionTier.ENTERPRISE: SubscriptionPlan(
                tier=SubscriptionTier.ENTERPRISE,
                name="Корпоративный",
                description="Для крупных компаний и корпораций",
                price=19990.0,
                billing_period="monthly",
                features={
                    FeatureType.CHAT_MESSAGES: FeatureLimit(FeatureType.CHAT_MESSAGES, -1, "monthly"),  # безлимит
                    FeatureType.DOCUMENT_ANALYSIS: FeatureLimit(FeatureType.DOCUMENT_ANALYSIS, -1, "monthly"),
                    FeatureType.API_CALLS: FeatureLimit(FeatureType.API_CALLS, -1, "monthly"),
                    FeatureType.STORAGE: FeatureLimit(FeatureType.STORAGE, -1, "monthly"),
                    FeatureType.EXPORT_REPORTS: FeatureLimit(FeatureType.EXPORT_REPORTS, -1, "monthly"),
                    FeatureType.PRIORITY_SUPPORT: FeatureLimit(FeatureType.PRIORITY_SUPPORT, 1, "monthly"),
                    FeatureType.ADVANCED_ANALYTICS: FeatureLimit(FeatureType.ADVANCED_ANALYTICS, 1, "monthly"),
                    FeatureType.CUSTOM_INTEGRATIONS: FeatureLimit(FeatureType.CUSTOM_INTEGRATIONS, -1, "monthly"),
                    FeatureType.WHITE_LABEL: FeatureLimit(FeatureType.WHITE_LABEL, 1, "monthly")
                },
                max_users=-1,  # безлимит
                trial_days=30
            )
        }
    
    def get_plan(self, tier: SubscriptionTier) -> Optional[SubscriptionPlan]:
        """Получение плана по уровню"""
        return self.plans.get(tier)
    
    def get_all_plans(self) -> List[SubscriptionPlan]:
        """Получение всех планов"""
        return list(self.plans.values())
    
    def create_user_subscription(
        self, 
        user_id: int, 
        tier: SubscriptionTier,
        start_date: Optional[datetime] = None
    ) -> UserSubscription:
        """Создание подписки пользователя"""
        plan = self.get_plan(tier)
        if not plan:
            raise ValueError(f"Plan not found for tier: {tier}")
        
        start_date = start_date or datetime.now()
        end_date = start_date + timedelta(days=30)  # По умолчанию месяц
        
        # Определяем дату окончания триала
        trial_end_date = None
        if plan.trial_days > 0:
            trial_end_date = start_date + timedelta(days=plan.trial_days)
        
        subscription = UserSubscription(
            user_id=user_id,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=True,
            trial_end_date=trial_end_date,
            usage_stats={feature: 0 for feature in plan.features.keys()}
        )
        
        self.user_subscriptions[user_id] = subscription
        self.usage_tracking[user_id] = {
            feature: {"daily": 0, "monthly": 0, "yearly": 0}
            for feature in plan.features.keys()
        }
        
        logger.info(f"Created subscription for user {user_id}: {tier.value}")
        return subscription
    
    def get_user_subscription(self, user_id: int) -> Optional[UserSubscription]:
        """Получение подписки пользователя"""
        return self.user_subscriptions.get(user_id)
    
    def check_feature_access(self, user_id: int, feature_type: FeatureType) -> Tuple[bool, str]:
        """Проверка доступа к функции"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            # Создаем бесплатную подписку
            subscription = self.create_user_subscription(user_id, SubscriptionTier.FREE)
        
        # Проверяем активность подписки
        if not subscription.is_active:
            return False, "Подписка неактивна"
        
        # Проверяем срок действия
        if datetime.now() > subscription.end_date:
            return False, "Подписка истекла"
        
        # Проверяем триал
        if subscription.trial_end_date and datetime.now() > subscription.trial_end_date:
            if subscription.plan.tier == SubscriptionTier.FREE:
                return False, "Триал истек"
        
        # Получаем лимит функции
        feature_limit = subscription.plan.features.get(feature_type)
        if not feature_limit:
            return False, "Функция недоступна в вашем тарифе"
        
        # Проверяем лимит
        if feature_limit.limit == -1:  # безлимит
            return True, "Доступ разрешен"
        
        # Получаем текущее использование
        current_usage = self.get_feature_usage(user_id, feature_type, feature_limit.period)
        
        if current_usage >= feature_limit.limit:
            return False, f"Превышен лимит использования ({current_usage}/{feature_limit.limit})"
        
        return True, "Доступ разрешен"
    
    def increment_feature_usage(self, user_id: int, feature_type: FeatureType, amount: int = 1):
        """Увеличение счетчика использования функции"""
        if user_id not in self.usage_tracking:
            self.usage_tracking[user_id] = {}
        
        if feature_type not in self.usage_tracking[user_id]:
            self.usage_tracking[user_id][feature_type] = {"daily": 0, "monthly": 0, "yearly": 0}
        
        # Увеличиваем счетчики
        self.usage_tracking[user_id][feature_type]["daily"] += amount
        self.usage_tracking[user_id][feature_type]["monthly"] += amount
        self.usage_tracking[user_id][feature_type]["yearly"] += amount
        
        # Обновляем статистику в подписке
        subscription = self.get_user_subscription(user_id)
        if subscription and feature_type in subscription.usage_stats:
            subscription.usage_stats[feature_type] += amount
    
    def get_feature_usage(self, user_id: int, feature_type: FeatureType, period: str) -> int:
        """Получение текущего использования функции"""
        if user_id not in self.usage_tracking:
            return 0
        
        if feature_type not in self.usage_tracking[user_id]:
            return 0
        
        return self.usage_tracking[user_id][feature_type].get(period, 0)
    
    def get_usage_summary(self, user_id: int) -> Dict[str, Any]:
        """Получение сводки по использованию"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return {}
        
        usage_summary = {
            "subscription": {
                "tier": subscription.plan.tier.value,
                "name": subscription.plan.name,
                "end_date": subscription.end_date.isoformat(),
                "is_active": subscription.is_active,
                "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None
            },
            "features": {}
        }
        
        for feature_type, limit in subscription.plan.features.items():
            current_usage = self.get_feature_usage(user_id, feature_type, limit.period)
            
            usage_summary["features"][feature_type.value] = {
                "limit": limit.limit,
                "current_usage": current_usage,
                "period": limit.period,
                "remaining": limit.limit - current_usage if limit.limit != -1 else -1,
                "percentage": (current_usage / limit.limit * 100) if limit.limit > 0 else 0
            }
        
        return usage_summary
    
    def upgrade_subscription(self, user_id: int, new_tier: SubscriptionTier) -> bool:
        """Обновление подписки"""
        try:
            current_subscription = self.get_user_subscription(user_id)
            if not current_subscription:
                return False
            
            new_plan = self.get_plan(new_tier)
            if not new_plan:
                return False
            
            # Обновляем план
            current_subscription.plan = new_plan
            current_subscription.end_date = datetime.now() + timedelta(days=30)
            
            # Сбрасываем статистику использования
            current_subscription.usage_stats = {feature: 0 for feature in new_plan.features.keys()}
            
            logger.info(f"Upgraded subscription for user {user_id} to {new_tier.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upgrade subscription: {str(e)}")
            return False
    
    def cancel_subscription(self, user_id: int) -> bool:
        """Отмена подписки"""
        try:
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                return False
            
            subscription.is_active = False
            subscription.auto_renew = False
            
            logger.info(f"Cancelled subscription for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            return False
    
    def reset_daily_usage(self):
        """Сброс ежедневного использования (вызывается по расписанию)"""
        for user_id in self.usage_tracking:
            for feature_type in self.usage_tracking[user_id]:
                self.usage_tracking[user_id][feature_type]["daily"] = 0
    
    def reset_monthly_usage(self):
        """Сброс месячного использования (вызывается по расписанию)"""
        for user_id in self.usage_tracking:
            for feature_type in self.usage_tracking[user_id]:
                self.usage_tracking[user_id][feature_type]["monthly"] = 0
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Получение статистики подписок"""
        stats = {
            "total_users": len(self.user_subscriptions),
            "active_subscriptions": len([s for s in self.user_subscriptions.values() if s.is_active]),
            "tiers_distribution": {},
            "revenue": 0.0
        }
        
        for subscription in self.user_subscriptions.values():
            tier = subscription.plan.tier.value
            stats["tiers_distribution"][tier] = stats["tiers_distribution"].get(tier, 0) + 1
            
            if subscription.is_active:
                stats["revenue"] += subscription.plan.price
        
        return stats

# Глобальный экземпляр менеджера подписок
subscription_manager = SubscriptionManager()

def get_subscription_manager() -> SubscriptionManager:
    """Получение экземпляра менеджера подписок"""
    return subscription_manager
