import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Статусы платежа"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    """Способы оплаты"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    YANDEX_MONEY = "yandex_money"
    QIWI = "qiwi"
    WEBMONEY = "webmoney"
    CRYPTO = "crypto"
    BALANCE = "balance"  # Оплата с баланса

class ServiceType(Enum):
    """Типы услуг"""
    CHAT_MESSAGE = "chat_message"
    DOCUMENT_ANALYSIS = "document_analysis"
    API_CALL = "api_call"
    EXPORT_REPORT = "export_report"
    PRIORITY_SUPPORT = "priority_support"
    CUSTOM_INTEGRATION = "custom_integration"

@dataclass
class PricingRule:
    """Правило ценообразования"""
    service_type: ServiceType
    base_price: float  # Базовая цена в рублях
    unit: str  # Единица измерения (message, document, call, etc.)
    bulk_discounts: List[Tuple[int, float]]  # Скидки за объем [(количество, процент_скидки)]
    time_multipliers: Dict[str, float]  # Множители по времени {"peak": 1.5, "off_peak": 0.8}

@dataclass
class PaymentTransaction:
    """Транзакция платежа"""
    id: str
    user_id: int
    service_type: ServiceType
    amount: float
    quantity: int
    unit_price: float
    total_price: float
    payment_method: PaymentMethod
    status: PaymentStatus
    created_at: datetime
    completed_at: Optional[datetime]
    payment_provider_id: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class UserBalance:
    """Баланс пользователя"""
    user_id: int
    balance: float
    frozen_balance: float  # Замороженные средства
    last_updated: datetime
    currency: str = "RUB"

class PaymentManager:
    """Менеджер платежей и ценообразования"""
    
    def __init__(self):
        self.pricing_rules = self._initialize_pricing_rules()
        self.user_balances: Dict[int, UserBalance] = {}
        self.transactions: Dict[str, PaymentTransaction] = {}
        self.payment_providers = {
            "yookassa": {"enabled": True, "fee_percent": 2.9},
            "stripe": {"enabled": True, "fee_percent": 2.9},
            "tinkoff": {"enabled": True, "fee_percent": 2.5}
        }
    
    def _initialize_pricing_rules(self) -> Dict[ServiceType, PricingRule]:
        """Инициализация правил ценообразования"""
        return {
            ServiceType.CHAT_MESSAGE: PricingRule(
                service_type=ServiceType.CHAT_MESSAGE,
                base_price=5.0,  # 5 рублей за сообщение
                unit="message",
                bulk_discounts=[(100, 0.1), (500, 0.2), (1000, 0.3)],  # 10%, 20%, 30% скидки
                time_multipliers={"peak": 1.2, "off_peak": 0.8, "night": 0.6}
            ),
            
            ServiceType.DOCUMENT_ANALYSIS: PricingRule(
                service_type=ServiceType.DOCUMENT_ANALYSIS,
                base_price=50.0,  # 50 рублей за документ
                unit="document",
                bulk_discounts=[(10, 0.15), (50, 0.25), (100, 0.35)],
                time_multipliers={"peak": 1.1, "off_peak": 0.9, "night": 0.7}
            ),
            
            ServiceType.API_CALL: PricingRule(
                service_type=ServiceType.API_CALL,
                base_price=1.0,  # 1 рубль за вызов
                unit="call",
                bulk_discounts=[(1000, 0.1), (10000, 0.2), (100000, 0.3)],
                time_multipliers={"peak": 1.0, "off_peak": 0.8, "night": 0.6}
            ),
            
            ServiceType.EXPORT_REPORT: PricingRule(
                service_type=ServiceType.EXPORT_REPORT,
                base_price=25.0,  # 25 рублей за отчет
                unit="report",
                bulk_discounts=[(10, 0.2), (50, 0.3), (100, 0.4)],
                time_multipliers={"peak": 1.0, "off_peak": 0.9, "night": 0.8}
            ),
            
            ServiceType.PRIORITY_SUPPORT: PricingRule(
                service_type=ServiceType.PRIORITY_SUPPORT,
                base_price=200.0,  # 200 рублей за час поддержки
                unit="hour",
                bulk_discounts=[(10, 0.1), (50, 0.2)],
                time_multipliers={"peak": 1.5, "off_peak": 1.0, "night": 0.8}
            ),
            
            ServiceType.CUSTOM_INTEGRATION: PricingRule(
                service_type=ServiceType.CUSTOM_INTEGRATION,
                base_price=5000.0,  # 5000 рублей за интеграцию
                unit="integration",
                bulk_discounts=[(3, 0.1), (10, 0.2)],
                time_multipliers={"peak": 1.0, "off_peak": 0.9, "night": 0.8}
            )
        }
    
    def calculate_price(
        self, 
        service_type: ServiceType, 
        quantity: int, 
        user_id: Optional[int] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Расчет цены за услугу"""
        try:
            pricing_rule = self.pricing_rules.get(service_type)
            if not pricing_rule:
                raise ValueError(f"Pricing rule not found for service: {service_type}")
            
            # Базовая цена
            base_price = pricing_rule.base_price
            
            # Применяем скидки за объем
            discount_percent = 0.0
            for threshold, discount in pricing_rule.bulk_discounts:
                if quantity >= threshold:
                    discount_percent = max(discount_percent, discount)
            
            # Применяем временные множители
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 18:
                time_multiplier = pricing_rule.time_multipliers.get("peak", 1.0)
            elif 22 <= current_hour or current_hour <= 6:
                time_multiplier = pricing_rule.time_multipliers.get("night", 1.0)
            else:
                time_multiplier = pricing_rule.time_multipliers.get("off_peak", 1.0)
            
            # Рассчитываем цену за единицу
            unit_price = base_price * (1 - discount_percent) * time_multiplier
            
            # Общая цена
            total_price = unit_price * quantity
            
            # Применяем персональные скидки пользователя
            personal_discount = self._get_personal_discount(user_id, service_type)
            if personal_discount > 0:
                total_price *= (1 - personal_discount)
                discount_percent += personal_discount
            
            pricing_details = {
                "base_price": base_price,
                "unit_price": unit_price,
                "quantity": quantity,
                "bulk_discount": discount_percent,
                "time_multiplier": time_multiplier,
                "personal_discount": personal_discount,
                "total_price": total_price,
                "currency": "RUB"
            }
            
            return total_price, pricing_details
            
        except Exception as e:
            logger.error(f"Price calculation error: {str(e)}")
            raise
    
    def _get_personal_discount(self, user_id: Optional[int], service_type: ServiceType) -> float:
        """Получение персональной скидки пользователя"""
        if not user_id:
            return 0.0
        
        # В реальном приложении здесь будет запрос к базе данных
        # для получения персональных скидок пользователя
        
        # Имитация персональных скидок
        personal_discounts = {
            1: 0.1,  # 10% скидка для VIP пользователей
            2: 0.05,  # 5% скидка для постоянных клиентов
        }
        
        return personal_discounts.get(user_id, 0.0)
    
    def create_payment(
        self,
        user_id: int,
        service_type: ServiceType,
        quantity: int,
        payment_method: PaymentMethod,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentTransaction:
        """Создание платежа"""
        try:
            # Рассчитываем цену
            total_price, pricing_details = self.calculate_price(service_type, quantity, user_id)
            
            # Создаем транзакцию
            transaction_id = f"pay_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            transaction = PaymentTransaction(
                id=transaction_id,
                user_id=user_id,
                service_type=service_type,
                amount=total_price,
                quantity=quantity,
                unit_price=pricing_details["unit_price"],
                total_price=total_price,
                payment_method=payment_method,
                status=PaymentStatus.PENDING,
                created_at=datetime.now(),
                completed_at=None,
                payment_provider_id=None,
                metadata={
                    "pricing_details": pricing_details,
                    **(metadata or {})
                }
            )
            
            self.transactions[transaction_id] = transaction
            
            logger.info(f"Created payment {transaction_id} for user {user_id}: {total_price} RUB")
            return transaction
            
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            raise
    
    def process_payment(
        self,
        transaction_id: str,
        payment_provider_id: Optional[str] = None
    ) -> bool:
        """Обработка платежа"""
        try:
            transaction = self.transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction not found: {transaction_id}")
            
            if transaction.status != PaymentStatus.PENDING:
                raise ValueError(f"Transaction already processed: {transaction.status}")
            
            # Обновляем статус
            transaction.status = PaymentStatus.PROCESSING
            transaction.payment_provider_id = payment_provider_id
            
            # Имитируем обработку платежа
            # В реальном приложении здесь будет интеграция с платежными системами
            
            if transaction.payment_method == PaymentMethod.BALANCE:
                # Оплата с баланса
                success = self._process_balance_payment(transaction)
            else:
                # Оплата через внешние системы
                success = self._process_external_payment(transaction)
            
            if success:
                transaction.status = PaymentStatus.COMPLETED
                transaction.completed_at = datetime.now()
                
                # Пополняем баланс пользователя (если это пополнение)
                if transaction.service_type == ServiceType.API_CALL and transaction.quantity == 0:
                    self._add_to_balance(transaction.user_id, transaction.amount)
                
                logger.info(f"Payment {transaction_id} completed successfully")
            else:
                transaction.status = PaymentStatus.FAILED
                logger.error(f"Payment {transaction_id} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return False
    
    def _process_balance_payment(self, transaction: PaymentTransaction) -> bool:
        """Обработка платежа с баланса"""
        try:
            user_balance = self.get_user_balance(transaction.user_id)
            
            if user_balance.balance < transaction.total_price:
                return False
            
            # Списываем с баланса
            user_balance.balance -= transaction.total_price
            user_balance.last_updated = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Balance payment error: {str(e)}")
            return False
    
    def _process_external_payment(self, transaction: PaymentTransaction) -> bool:
        """Обработка внешнего платежа"""
        # Имитация обработки через внешние платежные системы
        # В реальном приложении здесь будет интеграция с YooKassa, Stripe и т.д.
        
        import random
        return random.random() > 0.1  # 90% успешных платежей
    
    def get_user_balance(self, user_id: int) -> UserBalance:
        """Получение баланса пользователя"""
        if user_id not in self.user_balances:
            self.user_balances[user_id] = UserBalance(
                user_id=user_id,
                balance=0.0,
                frozen_balance=0.0,
                last_updated=datetime.now()
            )
        
        return self.user_balances[user_id]
    
    def _add_to_balance(self, user_id: int, amount: float):
        """Пополнение баланса"""
        user_balance = self.get_user_balance(user_id)
        user_balance.balance += amount
        user_balance.last_updated = datetime.now()
    
    def get_transaction(self, transaction_id: str) -> Optional[PaymentTransaction]:
        """Получение транзакции по ID"""
        return self.transactions.get(transaction_id)
    
    def get_user_transactions(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[PaymentTransaction]:
        """Получение транзакций пользователя"""
        user_transactions = [
            t for t in self.transactions.values()
            if t.user_id == user_id
        ]
        
        # Сортируем по дате создания (новые сначала)
        user_transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_transactions[offset:offset + limit]
    
    def refund_transaction(self, transaction_id: str, amount: Optional[float] = None) -> bool:
        """Возврат средств"""
        try:
            transaction = self.transactions.get(transaction_id)
            if not transaction:
                return False
            
            if transaction.status != PaymentStatus.COMPLETED:
                return False
            
            refund_amount = amount or transaction.total_price
            
            # Обновляем статус
            transaction.status = PaymentStatus.REFUNDED
            
            # Возвращаем средства на баланс
            if transaction.payment_method == PaymentMethod.BALANCE:
                self._add_to_balance(transaction.user_id, refund_amount)
            
            logger.info(f"Refunded {refund_amount} RUB for transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return False
    
    def get_pricing_info(self, service_type: ServiceType) -> Dict[str, Any]:
        """Получение информации о ценообразовании"""
        pricing_rule = self.pricing_rules.get(service_type)
        if not pricing_rule:
            return {}
        
        return {
            "service_type": service_type.value,
            "base_price": pricing_rule.base_price,
            "unit": pricing_rule.unit,
            "bulk_discounts": [
                {"threshold": threshold, "discount_percent": discount * 100}
                for threshold, discount in pricing_rule.bulk_discounts
            ],
            "time_multipliers": pricing_rule.time_multipliers,
            "currency": "RUB"
        }
    
    def get_payment_stats(self) -> Dict[str, Any]:
        """Получение статистики платежей"""
        total_transactions = len(self.transactions)
        completed_transactions = len([t for t in self.transactions.values() if t.status == PaymentStatus.COMPLETED])
        total_revenue = sum(t.total_price for t in self.transactions.values() if t.status == PaymentStatus.COMPLETED)
        
        # Статистика по типам услуг
        service_stats = {}
        for service_type in ServiceType:
            service_transactions = [t for t in self.transactions.values() if t.service_type == service_type]
            service_stats[service_type.value] = {
                "count": len(service_transactions),
                "revenue": sum(t.total_price for t in service_transactions if t.status == PaymentStatus.COMPLETED)
            }
        
        return {
            "total_transactions": total_transactions,
            "completed_transactions": completed_transactions,
            "success_rate": completed_transactions / total_transactions if total_transactions > 0 else 0,
            "total_revenue": total_revenue,
            "service_stats": service_stats,
            "currency": "RUB"
        }

# Глобальный экземпляр менеджера платежей
payment_manager = PaymentManager()

def get_payment_manager() -> PaymentManager:
    """Получение экземпляра менеджера платежей"""
    return payment_manager
