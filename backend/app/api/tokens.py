from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..models.user import User
from ..models.token_balance import TokenBalance, TokenTransaction
from ..services.auth_service import AuthService
from ..services.token_service import token_service
from ..schemas.tokens import (
    TokenBalanceResponse,
    TokenTransactionResponse,
    AddTokensRequest,
    AddTokensResponse
)

router = APIRouter()
auth_service = AuthService()


@router.get("/balance", response_model=TokenBalanceResponse)
async def get_token_balance(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение баланса токенов пользователя"""
    balance = token_service.get_user_balance(db, current_user.id)
    
    # Получаем статистику
    balance_obj = db.query(TokenBalance).filter(TokenBalance.user_id == current_user.id).first()
    
    return TokenBalanceResponse(
        balance=balance,
        total_earned=balance_obj.total_earned if balance_obj else 0,
        total_spent=balance_obj.total_spent if balance_obj else 0
    )


@router.get("/history", response_model=List[TokenTransactionResponse])
async def get_token_history(
    limit: int = 50,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение истории транзакций токенов"""
    transactions = token_service.get_transaction_history(db, current_user.id, limit)
    
    return [
        TokenTransactionResponse(
            id=t.id,
            amount=t.amount,
            transaction_type=t.transaction_type,
            description=t.description,
            chat_session_id=t.chat_session_id,
            chat_message_id=t.chat_message_id,
            created_at=t.created_at
        )
        for t in transactions
    ]


@router.post("/add", response_model=AddTokensResponse)
async def add_tokens(
    request: AddTokensRequest,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Пополнение баланса токенов (для админов или покупки)"""
    # В реальном приложении здесь была бы проверка прав или интеграция с платёжной системой
    success = token_service.add_tokens(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=request.transaction_type,
        description=request.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка пополнения баланса"
        )
    
    new_balance = token_service.get_user_balance(db, current_user.id)
    
    return AddTokensResponse(
        success=True,
        new_balance=new_balance,
        added_amount=request.amount
    )
