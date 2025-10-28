from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..models.user import User
from ..models.token_balance import TokenBalance, TokenTransaction

logger = logging.getLogger(__name__)


class TokenService:
    """Сервис для управления балансом токенов пользователей"""
    
    def __init__(self):
        pass
    
    def get_user_balance(self, db: Session, user_id: int) -> int:
        """Получение текущего баланса пользователя"""
        balance = db.query(TokenBalance).filter(TokenBalance.user_id == user_id).first()
        if not balance:
            # Создаем баланс для нового пользователя
            balance = TokenBalance(user_id=user_id, balance=1000)
            db.add(balance)
            db.commit()
            db.refresh(balance)
            logger.info(f"Создан новый баланс для пользователя {user_id}: 1000 токенов")
        return balance.balance
    
    def check_balance(self, db: Session, user_id: int, required_tokens: int) -> bool:
        """Проверка достаточности токенов"""
        current_balance = self.get_user_balance(db, user_id)
        return current_balance >= required_tokens
    
    def spend_tokens(
        self, 
        db: Session, 
        user_id: int, 
        amount: int, 
        transaction_type: str = "chat_message",
        description: str = None,
        chat_session_id: Optional[int] = None,
        chat_message_id: Optional[int] = None
    ) -> bool:
        """Списание токенов с баланса"""
        if not self.check_balance(db, user_id, amount):
            logger.warning(f"Недостаточно токенов у пользователя {user_id}: нужно {amount}")
            return False
        
        # Получаем баланс
        balance = db.query(TokenBalance).filter(TokenBalance.user_id == user_id).first()
        
        # Списываем токены
        balance.balance -= amount
        balance.total_spent += amount
        
        # Создаем транзакцию
        transaction = TokenTransaction(
            user_id=user_id,
            amount=-amount,  # Отрицательное значение для списания
            transaction_type=transaction_type,
            description=description or f"Списание {amount} токенов за {transaction_type}",
            chat_session_id=chat_session_id,
            chat_message_id=chat_message_id
        )
        
        db.add(transaction)
        db.commit()
        
        logger.info(f"Списано {amount} токенов у пользователя {user_id}. Остаток: {balance.balance}")
        return True
    
    def add_tokens(
        self, 
        db: Session, 
        user_id: int, 
        amount: int, 
        transaction_type: str = "bonus",
        description: str = None
    ) -> bool:
        """Пополнение баланса токенов"""
        # Получаем или создаем баланс
        balance = db.query(TokenBalance).filter(TokenBalance.user_id == user_id).first()
        if not balance:
            balance = TokenBalance(user_id=user_id, balance=0)
            db.add(balance)
        
        # Пополняем баланс
        balance.balance += amount
        balance.total_earned += amount
        
        # Создаем транзакцию
        transaction = TokenTransaction(
            user_id=user_id,
            amount=amount,  # Положительное значение для пополнения
            transaction_type=transaction_type,
            description=description or f"Пополнение на {amount} токенов ({transaction_type})"
        )
        
        db.add(transaction)
        db.commit()
        
        logger.info(f"Добавлено {amount} токенов пользователю {user_id}. Баланс: {balance.balance}")
        return True
    
    def get_transaction_history(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 50
    ) -> list:
        """Получение истории транзакций пользователя"""
        transactions = db.query(TokenTransaction)\
            .filter(TokenTransaction.user_id == user_id)\
            .order_by(TokenTransaction.created_at.desc())\
            .limit(limit)\
            .all()
        return transactions
    
    def calculate_message_cost(self, tokens_used: int) -> int:
        """Расчет стоимости сообщения в токенах"""
        # Базовая стоимость: 1 токен = 1 токен потрачен
        # Можно добавить коэффициенты для разных типов запросов
        return max(1, tokens_used)  # Минимум 1 токен за сообщение


# Глобальный экземпляр сервиса
token_service = TokenService()
