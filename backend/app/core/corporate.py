import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)

class CorporateTier(Enum):
    """Корпоративные уровни"""
    SMALL_BUSINESS = "small_business"  # 10-50 сотрудников
    MEDIUM_BUSINESS = "medium_business"  # 50-200 сотрудников
    LARGE_ENTERPRISE = "large_enterprise"  # 200+ сотрудников
    CUSTOM_ENTERPRISE = "custom_enterprise"  # Индивидуальные условия

class CorporateFeature(Enum):
    """Корпоративные функции"""
    MULTI_USER_ACCESS = "multi_user_access"
    ROLE_BASED_ACCESS = "role_based_access"
    SSO_INTEGRATION = "sso_integration"
    API_ACCESS = "api_access"
    WHITE_LABEL = "white_label"
    DEDICATED_SUPPORT = "dedicated_support"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    ADVANCED_ANALYTICS = "advanced_analytics"
    DATA_EXPORT = "data_export"
    COMPLIANCE_REPORTS = "compliance_reports"
    SLA_GUARANTEE = "sla_guarantee"
    ON_PREMISE_DEPLOYMENT = "on_premise_deployment"

@dataclass
class CorporatePlan:
    """Корпоративный план"""
    tier: CorporateTier
    name: str
    description: str
    base_price: float  # Базовая цена в рублях
    price_per_user: float  # Цена за пользователя
    min_users: int
    max_users: int
    features: List[CorporateFeature]
    sla_uptime: float  # Гарантированное время работы (99.9%)
    support_level: str  # Уровень поддержки
    contract_duration: int  # Длительность контракта в месяцах
    setup_fee: float  # Стоимость настройки
    is_active: bool = True

@dataclass
class CorporateSubscription:
    """Корпоративная подписка"""
    id: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    plan: CorporatePlan
    user_count: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    contract_number: str
    billing_address: str
    legal_entity: str
    inn: str  # ИНН
    kpp: str  # КПП
    bank_details: Dict[str, str]
    admin_users: List[int]  # ID администраторов
    regular_users: List[int]  # ID обычных пользователей

@dataclass
class UserRole:
    """Роль пользователя в корпоративной подписке"""
    user_id: int
    subscription_id: str
    role: str  # admin, manager, user, viewer
    permissions: List[str]
    department: Optional[str]
    manager_id: Optional[int]

class CorporateManager:
    """Менеджер корпоративных подписок"""
    
    def __init__(self):
        self.corporate_plans = self._initialize_corporate_plans()
        self.corporate_subscriptions: Dict[str, CorporateSubscription] = {}
        self.user_roles: Dict[int, UserRole] = {}
        self.usage_tracking: Dict[str, Dict[str, int]] = {}
    
    def _initialize_corporate_plans(self) -> Dict[CorporateTier, CorporatePlan]:
        """Инициализация корпоративных планов"""
        return {
            CorporateTier.SMALL_BUSINESS: CorporatePlan(
                tier=CorporateTier.SMALL_BUSINESS,
                name="Малый бизнес",
                description="Для небольших юридических фирм и консультаций",
                base_price=15000.0,
                price_per_user=500.0,
                min_users=5,
                max_users=50,
                features=[
                    CorporateFeature.MULTI_USER_ACCESS,
                    CorporateFeature.ROLE_BASED_ACCESS,
                    CorporateFeature.API_ACCESS,
                    CorporateFeature.ADVANCED_ANALYTICS,
                    CorporateFeature.DATA_EXPORT
                ],
                sla_uptime=99.5,
                support_level="standard",
                contract_duration=12,
                setup_fee=5000.0
            ),
            
            CorporateTier.MEDIUM_BUSINESS: CorporatePlan(
                tier=CorporateTier.MEDIUM_BUSINESS,
                name="Средний бизнес",
                description="Для средних юридических фирм и корпораций",
                base_price=50000.0,
                price_per_user=400.0,
                min_users=10,
                max_users=200,
                features=[
                    CorporateFeature.MULTI_USER_ACCESS,
                    CorporateFeature.ROLE_BASED_ACCESS,
                    CorporateFeature.SSO_INTEGRATION,
                    CorporateFeature.API_ACCESS,
                    CorporateFeature.WHITE_LABEL,
                    CorporateFeature.DEDICATED_SUPPORT,
                    CorporateFeature.CUSTOM_INTEGRATIONS,
                    CorporateFeature.ADVANCED_ANALYTICS,
                    CorporateFeature.DATA_EXPORT,
                    CorporateFeature.COMPLIANCE_REPORTS
                ],
                sla_uptime=99.7,
                support_level="priority",
                contract_duration=24,
                setup_fee=15000.0
            ),
            
            CorporateTier.LARGE_ENTERPRISE: CorporatePlan(
                tier=CorporateTier.LARGE_ENTERPRISE,
                name="Крупное предприятие",
                description="Для крупных корпораций и холдингов",
                base_price=150000.0,
                price_per_user=300.0,
                min_users=50,
                max_users=1000,
                features=[
                    CorporateFeature.MULTI_USER_ACCESS,
                    CorporateFeature.ROLE_BASED_ACCESS,
                    CorporateFeature.SSO_INTEGRATION,
                    CorporateFeature.API_ACCESS,
                    CorporateFeature.WHITE_LABEL,
                    CorporateFeature.DEDICATED_SUPPORT,
                    CorporateFeature.CUSTOM_INTEGRATIONS,
                    CorporateFeature.ADVANCED_ANALYTICS,
                    CorporateFeature.DATA_EXPORT,
                    CorporateFeature.COMPLIANCE_REPORTS,
                    CorporateFeature.SLA_GUARANTEE
                ],
                sla_uptime=99.9,
                support_level="dedicated",
                contract_duration=36,
                setup_fee=50000.0
            ),
            
            CorporateTier.CUSTOM_ENTERPRISE: CorporatePlan(
                tier=CorporateTier.CUSTOM_ENTERPRISE,
                name="Индивидуальное решение",
                description="Персональные условия для крупных клиентов",
                base_price=0.0,  # Индивидуальная цена
                price_per_user=0.0,
                min_users=100,
                max_users=-1,  # Без ограничений
                features=[
                    CorporateFeature.MULTI_USER_ACCESS,
                    CorporateFeature.ROLE_BASED_ACCESS,
                    CorporateFeature.SSO_INTEGRATION,
                    CorporateFeature.API_ACCESS,
                    CorporateFeature.WHITE_LABEL,
                    CorporateFeature.DEDICATED_SUPPORT,
                    CorporateFeature.CUSTOM_INTEGRATIONS,
                    CorporateFeature.ADVANCED_ANALYTICS,
                    CorporateFeature.DATA_EXPORT,
                    CorporateFeature.COMPLIANCE_REPORTS,
                    CorporateFeature.SLA_GUARANTEE,
                    CorporateFeature.ON_PREMISE_DEPLOYMENT
                ],
                sla_uptime=99.99,
                support_level="dedicated",
                contract_duration=60,
                setup_fee=0.0  # Индивидуальная цена
            )
        }
    
    def get_corporate_plan(self, tier: CorporateTier) -> Optional[CorporatePlan]:
        """Получение корпоративного плана"""
        return self.corporate_plans.get(tier)
    
    def get_all_corporate_plans(self) -> List[CorporatePlan]:
        """Получение всех корпоративных планов"""
        return list(self.corporate_plans.values())
    
    def create_corporate_subscription(
        self,
        company_name: str,
        contact_person: str,
        email: str,
        phone: str,
        tier: CorporateTier,
        user_count: int,
        contract_duration: Optional[int] = None,
        custom_features: Optional[List[CorporateFeature]] = None
    ) -> CorporateSubscription:
        """Создание корпоративной подписки"""
        try:
            plan = self.get_corporate_plan(tier)
            if not plan:
                raise ValueError(f"Corporate plan not found for tier: {tier}")
            
            # Проверяем количество пользователей
            if user_count < plan.min_users:
                raise ValueError(f"Minimum users required: {plan.min_users}")
            
            if plan.max_users != -1 and user_count > plan.max_users:
                raise ValueError(f"Maximum users allowed: {plan.max_users}")
            
            # Создаем подписку
            subscription_id = f"corp_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            contract_number = f"CONTRACT-{subscription_id[:8].upper()}"
            
            start_date = datetime.now()
            duration = contract_duration or plan.contract_duration
            end_date = start_date + timedelta(days=duration * 30)
            
            # Создаем план с кастомными функциями
            if custom_features:
                plan.features.extend(custom_features)
            
            subscription = CorporateSubscription(
                id=subscription_id,
                company_name=company_name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                plan=plan,
                user_count=user_count,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                contract_number=contract_number,
                billing_address="",
                legal_entity="",
                inn="",
                kpp="",
                bank_details={},
                admin_users=[],
                regular_users=[]
            )
            
            self.corporate_subscriptions[subscription_id] = subscription
            self.usage_tracking[subscription_id] = {}
            
            logger.info(f"Created corporate subscription {subscription_id} for {company_name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Corporate subscription creation error: {str(e)}")
            raise
    
    def get_corporate_subscription(self, subscription_id: str) -> Optional[CorporateSubscription]:
        """Получение корпоративной подписки"""
        return self.corporate_subscriptions.get(subscription_id)
    
    def add_user_to_subscription(
        self,
        subscription_id: str,
        user_id: int,
        role: str = "user",
        department: Optional[str] = None,
        manager_id: Optional[int] = None
    ) -> bool:
        """Добавление пользователя в корпоративную подписку"""
        try:
            subscription = self.get_corporate_subscription(subscription_id)
            if not subscription:
                return False
            
            # Проверяем лимит пользователей
            total_users = len(subscription.admin_users) + len(subscription.regular_users)
            if total_users >= subscription.user_count:
                return False
            
            # Определяем права доступа
            permissions = self._get_role_permissions(role)
            
            # Создаем роль пользователя
            user_role = UserRole(
                user_id=user_id,
                subscription_id=subscription_id,
                role=role,
                permissions=permissions,
                department=department,
                manager_id=manager_id
            )
            
            self.user_roles[user_id] = user_role
            
            # Добавляем в соответствующий список
            if role == "admin":
                subscription.admin_users.append(user_id)
            else:
                subscription.regular_users.append(user_id)
            
            logger.info(f"Added user {user_id} to corporate subscription {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Add user to subscription error: {str(e)}")
            return False
    
    def remove_user_from_subscription(self, subscription_id: str, user_id: int) -> bool:
        """Удаление пользователя из корпоративной подписки"""
        try:
            subscription = self.get_corporate_subscription(subscription_id)
            if not subscription:
                return False
            
            # Удаляем роль пользователя
            if user_id in self.user_roles:
                del self.user_roles[user_id]
            
            # Удаляем из списков
            if user_id in subscription.admin_users:
                subscription.admin_users.remove(user_id)
            if user_id in subscription.regular_users:
                subscription.regular_users.remove(user_id)
            
            logger.info(f"Removed user {user_id} from corporate subscription {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Remove user from subscription error: {str(e)}")
            return False
    
    def get_user_subscription(self, user_id: int) -> Optional[CorporateSubscription]:
        """Получение корпоративной подписки пользователя"""
        user_role = self.user_roles.get(user_id)
        if not user_role:
            return None
        
        return self.get_corporate_subscription(user_role.subscription_id)
    
    def get_user_role(self, user_id: int) -> Optional[UserRole]:
        """Получение роли пользователя"""
        return self.user_roles.get(user_id)
    
    def check_user_permission(self, user_id: int, permission: str) -> bool:
        """Проверка прав пользователя"""
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        return permission in user_role.permissions
    
    def calculate_corporate_price(
        self,
        tier: CorporateTier,
        user_count: int,
        contract_duration: int,
        custom_features: Optional[List[CorporateFeature]] = None
    ) -> Dict[str, Any]:
        """Расчет стоимости корпоративной подписки"""
        try:
            plan = self.get_corporate_plan(tier)
            if not plan:
                raise ValueError(f"Corporate plan not found for tier: {tier}")
            
            # Базовая цена
            base_price = plan.base_price
            
            # Цена за пользователей
            user_price = plan.price_per_user * user_count
            
            # Скидка за длительный контракт
            contract_discount = 0.0
            if contract_duration >= 24:
                contract_discount = 0.1  # 10% скидка
            elif contract_duration >= 36:
                contract_discount = 0.15  # 15% скидка
            
            # Скидка за количество пользователей
            volume_discount = 0.0
            if user_count >= 100:
                volume_discount = 0.1
            elif user_count >= 500:
                volume_discount = 0.15
            
            # Стоимость кастомных функций
            custom_features_price = 0.0
            if custom_features:
                custom_features_price = len(custom_features) * 5000.0  # 5000 за функцию
            
            # Общая стоимость
            subtotal = base_price + user_price + custom_features_price
            total_discount = max(contract_discount, volume_discount)
            discounted_price = subtotal * (1 - total_discount)
            
            # НДС (20%)
            vat = discounted_price * 0.2
            total_price = discounted_price + vat
            
            return {
                "tier": tier.value,
                "user_count": user_count,
                "contract_duration": contract_duration,
                "base_price": base_price,
                "user_price": user_price,
                "custom_features_price": custom_features_price,
                "subtotal": subtotal,
                "contract_discount": contract_discount,
                "volume_discount": volume_discount,
                "total_discount": total_discount,
                "discounted_price": discounted_price,
                "vat": vat,
                "total_price": total_price,
                "setup_fee": plan.setup_fee,
                "currency": "RUB"
            }
            
        except Exception as e:
            logger.error(f"Corporate price calculation error: {str(e)}")
            raise
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """Получение прав для роли"""
        permissions_map = {
            "admin": [
                "manage_users", "manage_subscription", "view_analytics",
                "export_data", "manage_integrations", "view_billing"
            ],
            "manager": [
                "manage_users", "view_analytics", "export_data"
            ],
            "user": [
                "use_chat", "view_documents", "create_reports"
            ],
            "viewer": [
                "view_documents", "view_reports"
            ]
        }
        
        return permissions_map.get(role, [])
    
    def get_corporate_stats(self) -> Dict[str, Any]:
        """Получение статистики корпоративных подписок"""
        total_subscriptions = len(self.corporate_subscriptions)
        active_subscriptions = len([s for s in self.corporate_subscriptions.values() if s.is_active])
        
        # Статистика по уровням
        tier_stats = {}
        for tier in CorporateTier:
            tier_subscriptions = [s for s in self.corporate_subscriptions.values() if s.plan.tier == tier]
            tier_stats[tier.value] = {
                "count": len(tier_subscriptions),
                "active": len([s for s in tier_subscriptions if s.is_active]),
                "total_users": sum(s.user_count for s in tier_subscriptions)
            }
        
        # Общее количество пользователей
        total_users = sum(s.user_count for s in self.corporate_subscriptions.values() if s.is_active)
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "total_users": total_users,
            "tier_distribution": tier_stats,
            "average_users_per_subscription": total_users / active_subscriptions if active_subscriptions > 0 else 0
        }

# Глобальный экземпляр менеджера корпоративных подписок
corporate_manager = CorporateManager()

def get_corporate_manager() -> CorporateManager:
    """Получение экземпляра менеджера корпоративных подписок"""
    return corporate_manager
