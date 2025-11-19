from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TokenBalanceResponse(BaseModel):
    """Ответ с балансом токенов"""
    balance: int = Field(..., description="Текущий баланс токенов")
    total_earned: int = Field(..., description="Всего заработано токенов")
    total_spent: int = Field(..., description="Всего потрачено токенов")
    
    class Config:
        from_attributes = True


class TokenTransactionResponse(BaseModel):
    """Ответ с информацией о транзакции токенов"""
    id: int
    amount: int = Field(..., description="Количество токенов (+ пополнение, - списание)")
    transaction_type: str = Field(..., description="Тип транзакции")
    description: Optional[str] = Field(None, description="Описание транзакции")
    chat_session_id: Optional[int] = Field(None, description="ID сессии чата")
    chat_message_id: Optional[int] = Field(None, description="ID сообщения")
    created_at: datetime = Field(..., description="Дата и время транзакции")
    
    class Config:
        from_attributes = True


class AddTokensRequest(BaseModel):
    """Запрос на пополнение токенов"""
    amount: int = Field(..., gt=0, description="Количество токенов для пополнения")
    transaction_type: str = Field(default="purchase", description="Тип транзакции")
    description: Optional[str] = Field(None, description="Описание пополнения")


class AddTokensResponse(BaseModel):
    """Ответ на пополнение токенов"""
    success: bool = Field(..., description="Успешность операции")
    new_balance: int = Field(..., description="Новый баланс после пополнения")
    added_amount: int = Field(..., description="Количество добавленных токенов")


class TokenCostInfo(BaseModel):
    """Информация о стоимости операции в токенах"""
    estimated_cost: int = Field(..., description="Примерная стоимость в токенах")
    user_balance: int = Field(..., description="Текущий баланс пользователя")
    sufficient: bool = Field(..., description="Достаточно ли токенов")
