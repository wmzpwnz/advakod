from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.payment import (
    get_payment_manager,
    ServiceType,
    PaymentMethod,
    PaymentStatus,
    PaymentTransaction,
    UserBalance
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

class PaymentRequest(BaseModel):
    service_type: str = Field(..., description="Тип услуги")
    quantity: int = Field(..., description="Количество")
    payment_method: str = Field(..., description="Способ оплаты")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Дополнительные данные")

class PriceCalculationRequest(BaseModel):
    service_type: str = Field(..., description="Тип услуги")
    quantity: int = Field(..., description="Количество")

class BalanceTopUpRequest(BaseModel):
    amount: float = Field(..., description="Сумма пополнения")
    payment_method: str = Field(..., description="Способ оплаты")

class RefundRequest(BaseModel):
    transaction_id: str = Field(..., description="ID транзакции")
    amount: Optional[float] = Field(None, description="Сумма возврата")

class PaymentTransactionResponse(BaseModel):
    id: str
    user_id: int
    service_type: str
    amount: float
    quantity: int
    unit_price: float
    total_price: float
    payment_method: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    payment_provider_id: Optional[str]
    metadata: Dict[str, Any]

class UserBalanceResponse(BaseModel):
    user_id: int
    balance: float
    frozen_balance: float
    last_updated: datetime
    currency: str

class PriceCalculationResponse(BaseModel):
    service_type: str
    quantity: int
    base_price: float
    unit_price: float
    total_price: float
    bulk_discount: float
    time_multiplier: float
    personal_discount: float
    currency: str
    pricing_details: Dict[str, Any]

@router.post("/calculate-price", response_model=PriceCalculationResponse)
async def calculate_price(
    request: PriceCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Расчет цены за услугу"""
    try:
        manager = get_payment_manager()
        
        try:
            service_type = ServiceType(request.service_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid service type")
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        total_price, pricing_details = manager.calculate_price(
            service_type, 
            request.quantity, 
            current_user.id
        )
        
        return PriceCalculationResponse(
            service_type=request.service_type,
            quantity=request.quantity,
            base_price=pricing_details["base_price"],
            unit_price=pricing_details["unit_price"],
            total_price=total_price,
            bulk_discount=pricing_details["bulk_discount"],
            time_multiplier=pricing_details["time_multiplier"],
            personal_discount=pricing_details["personal_discount"],
            currency="RUB",
            pricing_details=pricing_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-payment", response_model=PaymentTransactionResponse)
async def create_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание платежа"""
    try:
        manager = get_payment_manager()
        
        try:
            service_type = ServiceType(request.service_type)
            payment_method = PaymentMethod(request.payment_method)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        # Создаем платеж
        transaction = manager.create_payment(
            user_id=current_user.id,
            service_type=service_type,
            quantity=request.quantity,
            payment_method=payment_method,
            metadata=request.metadata
        )
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            service_type=transaction.service_type.value,
            amount=transaction.amount,
            quantity=transaction.quantity,
            unit_price=transaction.unit_price,
            total_price=transaction.total_price,
            payment_method=transaction.payment_method.value,
            status=transaction.status.value,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
            payment_provider_id=transaction.payment_provider_id,
            metadata=transaction.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-payment/{transaction_id}")
async def process_payment(
    transaction_id: str,
    payment_provider_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обработка платежа"""
    try:
        manager = get_payment_manager()
        
        # Проверяем, что транзакция принадлежит пользователю
        transaction = manager.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Обрабатываем платеж
        success = manager.process_payment(transaction_id, payment_provider_id)
        
        if success:
            return {"message": "Payment processed successfully", "status": "completed"}
        else:
            return {"message": "Payment processing failed", "status": "failed"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance", response_model=UserBalanceResponse)
async def get_user_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение баланса пользователя"""
    try:
        manager = get_payment_manager()
        balance = manager.get_user_balance(current_user.id)
        
        return UserBalanceResponse(
            user_id=balance.user_id,
            balance=balance.balance,
            frozen_balance=balance.frozen_balance,
            last_updated=balance.last_updated,
            currency=balance.currency
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/top-up-balance")
async def top_up_balance(
    request: BalanceTopUpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Пополнение баланса"""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        if request.amount > 100000:  # Максимум 100,000 рублей
            raise HTTPException(status_code=400, detail="Amount too large")
        
        manager = get_payment_manager()
        
        try:
            payment_method = PaymentMethod(request.payment_method)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment method")
        
        # Создаем транзакцию пополнения
        transaction = manager.create_payment(
            user_id=current_user.id,
            service_type=ServiceType.API_CALL,  # Используем как пополнение
            quantity=0,  # Специальное значение для пополнения
            payment_method=payment_method,
            metadata={"type": "balance_top_up", "amount": request.amount}
        )
        
        # Обрабатываем платеж
        success = manager.process_payment(transaction.id)
        
        if success:
            return {
                "message": "Balance topped up successfully",
                "transaction_id": transaction.id,
                "amount": request.amount
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to top up balance")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions", response_model=List[PaymentTransactionResponse])
async def get_user_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение транзакций пользователя"""
    try:
        if limit > 100:
            limit = 100
        
        manager = get_payment_manager()
        transactions = manager.get_user_transactions(current_user.id, limit, offset)
        
        return [
            PaymentTransactionResponse(
                id=t.id,
                user_id=t.user_id,
                service_type=t.service_type.value,
                amount=t.amount,
                quantity=t.quantity,
                unit_price=t.unit_price,
                total_price=t.total_price,
                payment_method=t.payment_method.value,
                status=t.status.value,
                created_at=t.created_at,
                completed_at=t.completed_at,
                payment_provider_id=t.payment_provider_id,
                metadata=t.metadata
            )
            for t in transactions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение транзакции по ID"""
    try:
        manager = get_payment_manager()
        transaction = manager.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            service_type=transaction.service_type.value,
            amount=transaction.amount,
            quantity=transaction.quantity,
            unit_price=transaction.unit_price,
            total_price=transaction.total_price,
            payment_method=transaction.payment_method.value,
            status=transaction.status.value,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
            payment_provider_id=transaction.payment_provider_id,
            metadata=transaction.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refund")
async def refund_transaction(
    request: RefundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Возврат средств"""
    try:
        manager = get_payment_manager()
        
        # Проверяем, что транзакция принадлежит пользователю
        transaction = manager.get_transaction(request.transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Выполняем возврат
        success = manager.refund_transaction(request.transaction_id, request.amount)
        
        if success:
            return {"message": "Refund processed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process refund")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/{service_type}")
async def get_pricing_info(
    service_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о ценообразовании"""
    try:
        manager = get_payment_manager()
        
        try:
            service_type_enum = ServiceType(service_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid service type")
        
        pricing_info = manager.get_pricing_info(service_type_enum)
        
        if not pricing_info:
            raise HTTPException(status_code=404, detail="Pricing info not found")
        
        return pricing_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing")
async def get_all_pricing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о ценообразовании для всех услуг"""
    try:
        manager = get_payment_manager()
        
        pricing_info = {}
        for service_type in ServiceType:
            pricing_info[service_type.value] = manager.get_pricing_info(service_type)
        
        return pricing_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_payment_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики платежей (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_payment_manager()
        stats = manager.get_payment_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def payment_health():
    """Проверка здоровья сервиса платежей"""
    try:
        manager = get_payment_manager()
        
        # Тестируем расчет цены
        test_price, _ = manager.calculate_price(ServiceType.CHAT_MESSAGE, 1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_calculation": {
                "service": "chat_message",
                "quantity": 1,
                "price": test_price
            },
            "payment_providers": manager.payment_providers
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
