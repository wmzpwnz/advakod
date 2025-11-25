from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.database import get_db
from ..models.user import User
from ..core.corporate import (
    get_corporate_manager,
    CorporateTier,
    CorporateFeature,
    CorporatePlan,
    CorporateSubscription,
    UserRole
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

class CorporateSubscriptionRequest(BaseModel):
    company_name: str = Field(..., description="Название компании")
    contact_person: str = Field(..., description="Контактное лицо")
    email: str = Field(..., description="Email")
    phone: str = Field(..., description="Телефон")
    tier: str = Field(..., description="Уровень подписки")
    user_count: int = Field(..., description="Количество пользователей")
    contract_duration: Optional[int] = Field(None, description="Длительность контракта в месяцах")
    custom_features: Optional[List[str]] = Field(None, description="Дополнительные функции")

class CorporatePriceRequest(BaseModel):
    tier: str = Field(..., description="Уровень подписки")
    user_count: int = Field(..., description="Количество пользователей")
    contract_duration: int = Field(..., description="Длительность контракта в месяцах")
    custom_features: Optional[List[str]] = Field(None, description="Дополнительные функции")

class AddUserRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    role: str = Field(default="user", description="Роль пользователя")
    department: Optional[str] = Field(None, description="Отдел")
    manager_id: Optional[int] = Field(None, description="ID менеджера")

class CorporatePlanResponse(BaseModel):
    tier: str
    name: str
    description: str
    base_price: float
    price_per_user: float
    min_users: int
    max_users: int
    features: List[str]
    sla_uptime: float
    support_level: str
    contract_duration: int
    setup_fee: float
    is_active: bool

class CorporateSubscriptionResponse(BaseModel):
    id: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    plan: CorporatePlanResponse
    user_count: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    contract_number: str
    billing_address: str
    legal_entity: str
    inn: str
    kpp: str
    bank_details: Dict[str, str]
    admin_users: List[int]
    regular_users: List[int]

class UserRoleResponse(BaseModel):
    user_id: int
    subscription_id: str
    role: str
    permissions: List[str]
    department: Optional[str]
    manager_id: Optional[int]

@router.get("/plans", response_model=List[CorporatePlanResponse])
async def get_corporate_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение всех корпоративных планов"""
    try:
        manager = get_corporate_manager()
        plans = manager.get_all_corporate_plans()
        
        return [
            CorporatePlanResponse(
                tier=plan.tier.value,
                name=plan.name,
                description=plan.description,
                base_price=plan.base_price,
                price_per_user=plan.price_per_user,
                min_users=plan.min_users,
                max_users=plan.max_users,
                features=[feature.value for feature in plan.features],
                sla_uptime=plan.sla_uptime,
                support_level=plan.support_level,
                contract_duration=plan.contract_duration,
                setup_fee=plan.setup_fee,
                is_active=plan.is_active
            )
            for plan in plans
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{tier}", response_model=CorporatePlanResponse)
async def get_corporate_plan(
    tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение конкретного корпоративного плана"""
    try:
        manager = get_corporate_manager()
        
        try:
            corporate_tier = CorporateTier(tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid corporate tier")
        
        plan = manager.get_corporate_plan(corporate_tier)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return CorporatePlanResponse(
            tier=plan.tier.value,
            name=plan.name,
            description=plan.description,
            base_price=plan.base_price,
            price_per_user=plan.price_per_user,
            min_users=plan.min_users,
            max_users=plan.max_users,
            features=[feature.value for feature in plan.features],
            sla_uptime=plan.sla_uptime,
            support_level=plan.support_level,
            contract_duration=plan.contract_duration,
            setup_fee=plan.setup_fee,
            is_active=plan.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-price")
async def calculate_corporate_price(
    request: CorporatePriceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Расчет стоимости корпоративной подписки"""
    try:
        manager = get_corporate_manager()
        
        try:
            tier = CorporateTier(request.tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid corporate tier")
        
        if request.user_count <= 0:
            raise HTTPException(status_code=400, detail="User count must be positive")
        
        if request.contract_duration <= 0:
            raise HTTPException(status_code=400, detail="Contract duration must be positive")
        
        # Преобразуем кастомные функции
        custom_features = None
        if request.custom_features:
            try:
                custom_features = [CorporateFeature(feature) for feature in request.custom_features]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid feature: {str(e)}")
        
        price_info = manager.calculate_corporate_price(
            tier=tier,
            user_count=request.user_count,
            contract_duration=request.contract_duration,
            custom_features=custom_features
        )
        
        return price_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe", response_model=CorporateSubscriptionResponse)
async def create_corporate_subscription(
    request: CorporateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание корпоративной подписки"""
    try:
        manager = get_corporate_manager()
        
        try:
            tier = CorporateTier(request.tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid corporate tier")
        
        if request.user_count <= 0:
            raise HTTPException(status_code=400, detail="User count must be positive")
        
        # Преобразуем кастомные функции
        custom_features = None
        if request.custom_features:
            try:
                custom_features = [CorporateFeature(feature) for feature in request.custom_features]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid feature: {str(e)}")
        
        # Создаем подписку
        subscription = manager.create_corporate_subscription(
            company_name=request.company_name,
            contact_person=request.contact_person,
            email=request.email,
            phone=request.phone,
            tier=tier,
            user_count=request.user_count,
            contract_duration=request.contract_duration,
            custom_features=custom_features
        )
        
        return CorporateSubscriptionResponse(
            id=subscription.id,
            company_name=subscription.company_name,
            contact_person=subscription.contact_person,
            email=subscription.email,
            phone=subscription.phone,
            plan=CorporatePlanResponse(
                tier=subscription.plan.tier.value,
                name=subscription.plan.name,
                description=subscription.plan.description,
                base_price=subscription.plan.base_price,
                price_per_user=subscription.plan.price_per_user,
                min_users=subscription.plan.min_users,
                max_users=subscription.plan.max_users,
                features=[feature.value for feature in subscription.plan.features],
                sla_uptime=subscription.plan.sla_uptime,
                support_level=subscription.plan.support_level,
                contract_duration=subscription.plan.contract_duration,
                setup_fee=subscription.plan.setup_fee,
                is_active=subscription.plan.is_active
            ),
            user_count=subscription.user_count,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_active=subscription.is_active,
            contract_number=subscription.contract_number,
            billing_address=subscription.billing_address,
            legal_entity=subscription.legal_entity,
            inn=subscription.inn,
            kpp=subscription.kpp,
            bank_details=subscription.bank_details,
            admin_users=subscription.admin_users,
            regular_users=subscription.regular_users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-subscription", response_model=CorporateSubscriptionResponse)
async def get_my_corporate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение корпоративной подписки пользователя"""
    try:
        manager = get_corporate_manager()
        subscription = manager.get_user_subscription(current_user.id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No corporate subscription found")
        
        return CorporateSubscriptionResponse(
            id=subscription.id,
            company_name=subscription.company_name,
            contact_person=subscription.contact_person,
            email=subscription.email,
            phone=subscription.phone,
            plan=CorporatePlanResponse(
                tier=subscription.plan.tier.value,
                name=subscription.plan.name,
                description=subscription.plan.description,
                base_price=subscription.plan.base_price,
                price_per_user=subscription.plan.price_per_user,
                min_users=subscription.plan.min_users,
                max_users=subscription.plan.max_users,
                features=[feature.value for feature in subscription.plan.features],
                sla_uptime=subscription.plan.sla_uptime,
                support_level=subscription.plan.support_level,
                contract_duration=subscription.plan.contract_duration,
                setup_fee=subscription.plan.setup_fee,
                is_active=subscription.plan.is_active
            ),
            user_count=subscription.user_count,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_active=subscription.is_active,
            contract_number=subscription.contract_number,
            billing_address=subscription.billing_address,
            legal_entity=subscription.legal_entity,
            inn=subscription.inn,
            kpp=subscription.kpp,
            bank_details=subscription.bank_details,
            admin_users=subscription.admin_users,
            regular_users=subscription.regular_users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-role", response_model=UserRoleResponse)
async def get_my_corporate_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение роли пользователя в корпоративной подписке"""
    try:
        manager = get_corporate_manager()
        user_role = manager.get_user_role(current_user.id)
        
        if not user_role:
            raise HTTPException(status_code=404, detail="No corporate role found")
        
        return UserRoleResponse(
            user_id=user_role.user_id,
            subscription_id=user_role.subscription_id,
            role=user_role.role,
            permissions=user_role.permissions,
            department=user_role.department,
            manager_id=user_role.manager_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-user")
async def add_user_to_subscription(
    request: AddUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление пользователя в корпоративную подписку"""
    try:
        manager = get_corporate_manager()
        
        # Проверяем права пользователя
        if not manager.check_user_permission(current_user.id, "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Получаем подписку пользователя
        subscription = manager.get_user_subscription(current_user.id)
        if not subscription:
            raise HTTPException(status_code=404, detail="No corporate subscription found")
        
        # Добавляем пользователя
        success = manager.add_user_to_subscription(
            subscription_id=subscription.id,
            user_id=request.user_id,
            role=request.role,
            department=request.department,
            manager_id=request.manager_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add user to subscription")
        
        return {"message": "User added to subscription successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove-user/{user_id}")
async def remove_user_from_subscription(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление пользователя из корпоративной подписки"""
    try:
        manager = get_corporate_manager()
        
        # Проверяем права пользователя
        if not manager.check_user_permission(current_user.id, "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Получаем подписку пользователя
        subscription = manager.get_user_subscription(current_user.id)
        if not subscription:
            raise HTTPException(status_code=404, detail="No corporate subscription found")
        
        # Удаляем пользователя
        success = manager.remove_user_from_subscription(subscription.id, user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove user from subscription")
        
        return {"message": "User removed from subscription successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-permission/{permission}")
async def check_user_permission(
    permission: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Проверка прав пользователя"""
    try:
        manager = get_corporate_manager()
        has_permission = manager.check_user_permission(current_user.id, permission)
        
        return {
            "user_id": current_user.id,
            "permission": permission,
            "has_permission": has_permission
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_corporate_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики корпоративных подписок (только для админов)"""
    try:
        # Проверяем права администратора
        if not current_user.is_premium:  # В реальном приложении нужна проверка на админа
            raise HTTPException(status_code=403, detail="Admin access required")
        
        manager = get_corporate_manager()
        stats = manager.get_corporate_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def corporate_health():
    """Проверка здоровья сервиса корпоративных подписок"""
    try:
        manager = get_corporate_manager()
        
        # Тестируем расчет цены
        price_info = manager.calculate_corporate_price(
            CorporateTier.SMALL_BUSINESS, 10, 12
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_calculation": {
                "tier": "small_business",
                "user_count": 10,
                "contract_duration": 12,
                "total_price": price_info["total_price"]
            },
            "plans_count": len(manager.get_all_corporate_plans())
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
