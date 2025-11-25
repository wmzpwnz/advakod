import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import secrets

logger = logging.getLogger(__name__)

class ReferralStatus(Enum):
    """Статусы реферала"""
    PENDING = "pending"  # Ожидает активации
    ACTIVE = "active"    # Активный
    COMPLETED = "completed"  # Завершен (привел клиента)
    EXPIRED = "expired"  # Истек
    CANCELLED = "cancelled"  # Отменен

class ReferralType(Enum):
    """Типы рефералов"""
    USER_REGISTRATION = "user_registration"  # Регистрация пользователя
    SUBSCRIPTION_PURCHASE = "subscription_purchase"  # Покупка подписки
    CORPORATE_SUBSCRIPTION = "corporate_subscription"  # Корпоративная подписка
    PAYMENT = "payment"  # Платеж

class CommissionType(Enum):
    """Типы комиссий"""
    PERCENTAGE = "percentage"  # Процент от суммы
    FIXED = "fixed"  # Фиксированная сумма
    BONUS = "bonus"  # Бонус за действие

@dataclass
class ReferralCode:
    """Реферальный код"""
    code: str
    user_id: int
    created_at: datetime
    expires_at: Optional[datetime]
    max_uses: int
    current_uses: int
    is_active: bool
    description: Optional[str] = None

@dataclass
class Referral:
    """Реферал"""
    id: str
    referrer_id: int  # Кто привел
    referred_id: int  # Кого привели
    referral_code: str
    referral_type: ReferralType
    status: ReferralStatus
    created_at: datetime
    completed_at: Optional[datetime]
    commission_amount: float
    commission_type: CommissionType
    metadata: Dict[str, Any]

@dataclass
class CommissionRule:
    """Правило комиссии"""
    referral_type: ReferralType
    commission_type: CommissionType
    value: float  # Процент или фиксированная сумма
    min_amount: Optional[float] = None  # Минимальная сумма для начисления
    max_amount: Optional[float] = None  # Максимальная сумма комиссии
    is_active: bool = True

@dataclass
class ReferralStats:
    """Статистика рефералов"""
    user_id: int
    total_referrals: int
    active_referrals: int
    completed_referrals: int
    total_commission: float
    pending_commission: float
    paid_commission: float

class ReferralManager:
    """Менеджер реферальной системы"""
    
    def __init__(self):
        self.referral_codes: Dict[str, ReferralCode] = {}
        self.referrals: Dict[str, Referral] = {}
        self.commission_rules = self._initialize_commission_rules()
        self.user_stats: Dict[int, ReferralStats] = {}
    
    def _initialize_commission_rules(self) -> Dict[ReferralType, CommissionRule]:
        """Инициализация правил комиссий"""
        return {
            ReferralType.USER_REGISTRATION: CommissionRule(
                referral_type=ReferralType.USER_REGISTRATION,
                commission_type=CommissionType.FIXED,
                value=100.0,  # 100 рублей за регистрацию
                is_active=True
            ),
            
            ReferralType.SUBSCRIPTION_PURCHASE: CommissionRule(
                referral_type=ReferralType.SUBSCRIPTION_PURCHASE,
                commission_type=CommissionType.PERCENTAGE,
                value=0.15,  # 15% от стоимости подписки
                min_amount=1000.0,  # Минимум 1000 рублей
                max_amount=5000.0,  # Максимум 5000 рублей комиссии
                is_active=True
            ),
            
            ReferralType.CORPORATE_SUBSCRIPTION: CommissionRule(
                referral_type=ReferralType.CORPORATE_SUBSCRIPTION,
                commission_type=CommissionType.PERCENTAGE,
                value=0.10,  # 10% от стоимости корпоративной подписки
                min_amount=5000.0,  # Минимум 5000 рублей
                max_amount=50000.0,  # Максимум 50000 рублей комиссии
                is_active=True
            ),
            
            ReferralType.PAYMENT: CommissionRule(
                referral_type=ReferralType.PAYMENT,
                commission_type=CommissionType.PERCENTAGE,
                value=0.05,  # 5% от суммы платежа
                min_amount=100.0,  # Минимум 100 рублей
                max_amount=1000.0,  # Максимум 1000 рублей комиссии
                is_active=True
            )
        }
    
    def generate_referral_code(
        self,
        user_id: int,
        expires_days: Optional[int] = None,
        max_uses: int = 100,
        description: Optional[str] = None
    ) -> ReferralCode:
        """Генерация реферального кода"""
        try:
            # Генерируем уникальный код
            timestamp = int(datetime.now().timestamp())
            random_part = secrets.token_hex(4)
            code = f"REF{timestamp}{random_part}".upper()
            
            # Проверяем уникальность
            while code in self.referral_codes:
                random_part = secrets.token_hex(4)
                code = f"REF{timestamp}{random_part}".upper()
            
            # Определяем дату истечения
            expires_at = None
            if expires_days:
                expires_at = datetime.now() + timedelta(days=expires_days)
            
            # Создаем код
            referral_code = ReferralCode(
                code=code,
                user_id=user_id,
                created_at=datetime.now(),
                expires_at=expires_at,
                max_uses=max_uses,
                current_uses=0,
                is_active=True,
                description=description
            )
            
            self.referral_codes[code] = referral_code
            
            logger.info(f"Generated referral code {code} for user {user_id}")
            return referral_code
            
        except Exception as e:
            logger.error(f"Referral code generation error: {str(e)}")
            raise
    
    def get_referral_code(self, code: str) -> Optional[ReferralCode]:
        """Получение реферального кода"""
        return self.referral_codes.get(code)
    
    def validate_referral_code(self, code: str) -> Tuple[bool, str]:
        """Валидация реферального кода"""
        referral_code = self.get_referral_code(code)
        
        if not referral_code:
            return False, "Код не найден"
        
        if not referral_code.is_active:
            return False, "Код неактивен"
        
        if referral_code.expires_at and datetime.now() > referral_code.expires_at:
            return False, "Код истек"
        
        if referral_code.current_uses >= referral_code.max_uses:
            return False, "Превышено максимальное количество использований"
        
        return True, "Код действителен"
    
    def create_referral(
        self,
        referrer_id: int,
        referred_id: int,
        referral_code: str,
        referral_type: ReferralType,
        amount: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Referral:
        """Создание реферала"""
        try:
            # Валидируем код
            is_valid, message = self.validate_referral_code(referral_code)
            if not is_valid:
                raise ValueError(f"Invalid referral code: {message}")
            
            # Проверяем, что пользователь не привел сам себя
            if referrer_id == referred_id:
                raise ValueError("User cannot refer themselves")
            
            # Проверяем, что пользователь еще не был приведен
            existing_referral = self._find_existing_referral(referred_id)
            if existing_referral:
                raise ValueError("User already has a referrer")
            
            # Рассчитываем комиссию
            commission_amount, commission_type = self._calculate_commission(
                referral_type, amount
            )
            
            # Создаем реферал
            referral_id = f"ref_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            referral = Referral(
                id=referral_id,
                referrer_id=referrer_id,
                referred_id=referred_id,
                referral_code=referral_code,
                referral_type=referral_type,
                status=ReferralStatus.PENDING,
                created_at=datetime.now(),
                completed_at=None,
                commission_amount=commission_amount,
                commission_type=commission_type,
                metadata=metadata or {}
            )
            
            self.referrals[referral_id] = referral
            
            # Увеличиваем счетчик использований кода
            code_obj = self.get_referral_code(referral_code)
            if code_obj:
                code_obj.current_uses += 1
            
            # Обновляем статистику
            self._update_user_stats(referrer_id)
            
            logger.info(f"Created referral {referral_id} from {referrer_id} to {referred_id}")
            return referral
            
        except Exception as e:
            logger.error(f"Referral creation error: {str(e)}")
            raise
    
    def complete_referral(
        self,
        referral_id: str,
        amount: Optional[float] = None
    ) -> bool:
        """Завершение реферала (начисление комиссии)"""
        try:
            referral = self.referrals.get(referral_id)
            if not referral:
                return False
            
            if referral.status != ReferralStatus.PENDING:
                return False
            
            # Пересчитываем комиссию если нужно
            if amount is not None:
                commission_amount, commission_type = self._calculate_commission(
                    referral.referral_type, amount
                )
                referral.commission_amount = commission_amount
                referral.commission_type = commission_type
            
            # Обновляем статус
            referral.status = ReferralStatus.COMPLETED
            referral.completed_at = datetime.now()
            
            # Обновляем статистику
            self._update_user_stats(referral.referrer_id)
            
            logger.info(f"Completed referral {referral_id}, commission: {referral.commission_amount}")
            return True
            
        except Exception as e:
            logger.error(f"Referral completion error: {str(e)}")
            return False
    
    def _find_existing_referral(self, user_id: int) -> Optional[Referral]:
        """Поиск существующего реферала для пользователя"""
        for referral in self.referrals.values():
            if referral.referred_id == user_id:
                return referral
        return None
    
    def _calculate_commission(
        self,
        referral_type: ReferralType,
        amount: Optional[float] = None
    ) -> Tuple[float, CommissionType]:
        """Расчет комиссии"""
        rule = self.commission_rules.get(referral_type)
        if not rule or not rule.is_active:
            return 0.0, CommissionType.FIXED
        
        if rule.commission_type == CommissionType.FIXED:
            return rule.value, CommissionType.FIXED
        
        elif rule.commission_type == CommissionType.PERCENTAGE:
            if amount is None:
                return 0.0, CommissionType.PERCENTAGE
            
            commission = amount * rule.value
            
            # Применяем ограничения
            if rule.min_amount and commission < rule.min_amount:
                return 0.0, CommissionType.PERCENTAGE
            
            if rule.max_amount and commission > rule.max_amount:
                commission = rule.max_amount
            
            return commission, CommissionType.PERCENTAGE
        
        return 0.0, CommissionType.FIXED
    
    def _update_user_stats(self, user_id: int):
        """Обновление статистики пользователя"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = ReferralStats(
                user_id=user_id,
                total_referrals=0,
                active_referrals=0,
                completed_referrals=0,
                total_commission=0.0,
                pending_commission=0.0,
                paid_commission=0.0
            )
        
        stats = self.user_stats[user_id]
        
        # Пересчитываем статистику
        user_referrals = [r for r in self.referrals.values() if r.referrer_id == user_id]
        
        stats.total_referrals = len(user_referrals)
        stats.active_referrals = len([r for r in user_referrals if r.status == ReferralStatus.ACTIVE])
        stats.completed_referrals = len([r for r in user_referrals if r.status == ReferralStatus.COMPLETED])
        stats.total_commission = sum(r.commission_amount for r in user_referrals if r.status == ReferralStatus.COMPLETED)
        stats.pending_commission = sum(r.commission_amount for r in user_referrals if r.status == ReferralStatus.PENDING)
    
    def get_user_referrals(
        self,
        user_id: int,
        status: Optional[ReferralStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Referral]:
        """Получение рефералов пользователя"""
        user_referrals = [r for r in self.referrals.values() if r.referrer_id == user_id]
        
        if status:
            user_referrals = [r for r in user_referrals if r.status == status]
        
        # Сортируем по дате создания
        user_referrals.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_referrals[offset:offset + limit]
    
    def get_user_referral_codes(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[ReferralCode]:
        """Получение реферальных кодов пользователя"""
        user_codes = [c for c in self.referral_codes.values() if c.user_id == user_id]
        
        if active_only:
            user_codes = [c for c in user_codes if c.is_active]
        
        return user_codes
    
    def get_user_stats(self, user_id: int) -> Optional[ReferralStats]:
        """Получение статистики пользователя"""
        return self.user_stats.get(user_id)
    
    def get_referral_by_referred_user(self, user_id: int) -> Optional[Referral]:
        """Получение реферала по приведенному пользователю"""
        return self._find_existing_referral(user_id)
    
    def deactivate_referral_code(self, code: str) -> bool:
        """Деактивация реферального кода"""
        referral_code = self.get_referral_code(code)
        if not referral_code:
            return False
        
        referral_code.is_active = False
        logger.info(f"Deactivated referral code {code}")
        return True
    
    def get_referral_stats(self) -> Dict[str, Any]:
        """Получение общей статистики рефералов"""
        total_referrals = len(self.referrals)
        active_referrals = len([r for r in self.referrals.values() if r.status == ReferralStatus.ACTIVE])
        completed_referrals = len([r for r in self.referrals.values() if r.status == ReferralStatus.COMPLETED])
        total_commission = sum(r.commission_amount for r in self.referrals.values() if r.status == ReferralStatus.COMPLETED)
        
        # Статистика по типам
        type_stats = {}
        for referral_type in ReferralType:
            type_referrals = [r for r in self.referrals.values() if r.referral_type == referral_type]
            type_stats[referral_type.value] = {
                "count": len(type_referrals),
                "completed": len([r for r in type_referrals if r.status == ReferralStatus.COMPLETED]),
                "total_commission": sum(r.commission_amount for r in type_referrals if r.status == ReferralStatus.COMPLETED)
            }
        
        return {
            "total_referrals": total_referrals,
            "active_referrals": active_referrals,
            "completed_referrals": completed_referrals,
            "completion_rate": completed_referrals / total_referrals if total_referrals > 0 else 0,
            "total_commission": total_commission,
            "type_stats": type_stats,
            "currency": "RUB"
        }
    
    def cleanup_expired_codes(self):
        """Очистка истекших кодов"""
        current_time = datetime.now()
        expired_codes = []
        
        for code, referral_code in self.referral_codes.items():
            if referral_code.expires_at and current_time > referral_code.expires_at:
                expired_codes.append(code)
        
        for code in expired_codes:
            self.referral_codes[code].is_active = False
        
        if expired_codes:
            logger.info(f"Deactivated {len(expired_codes)} expired referral codes")

# Глобальный экземпляр менеджера рефералов
referral_manager = ReferralManager()

def get_referral_manager() -> ReferralManager:
    """Получение экземпляра менеджера рефералов"""
    return referral_manager
