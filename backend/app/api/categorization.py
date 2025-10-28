from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..core.categorization import (
    get_question_categorizer,
    CategoryResult,
    CategoryDefinition
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

class CategorizationRequest(BaseModel):
    text: str = Field(..., description="Текст для категоризации")
    include_reasoning: bool = Field(default=True, description="Включить объяснение")

class BatchCategorizationRequest(BaseModel):
    texts: List[str] = Field(..., description="Список текстов для категоризации")
    include_reasoning: bool = Field(default=True, description="Включить объяснение")

class CategorizationResponse(BaseModel):
    text: str
    category: str
    category_display_name: str
    confidence: float
    subcategory: Optional[str]
    keywords: List[str]
    reasoning: Optional[str]
    timestamp: datetime

class CategoryInfoResponse(BaseModel):
    name: str
    display_name: str
    description: str
    keywords_count: int
    patterns_count: int
    subcategories_count: int
    priority: int
    subcategories: Dict[str, List[str]]

@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_text(
    request: CategorizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Категоризация текста"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Получаем классификатор
        categorizer = get_question_categorizer()
        
        # Выполняем категоризацию
        result = categorizer.categorize_question(request.text)
        
        # Получаем информацию о категории
        category_info = categorizer.get_category_info(result.category)
        
        return CategorizationResponse(
            text=result.text,
            category=result.category,
            category_display_name=category_info.display_name if category_info else result.category,
            confidence=result.confidence,
            subcategory=result.subcategory,
            keywords=result.keywords,
            reasoning=result.reasoning if request.include_reasoning else None,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categorize/batch", response_model=List[CategorizationResponse])
async def categorize_texts_batch(
    request: BatchCategorizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Категоризация списка текстов"""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="Texts list cannot be empty")
        
        if len(request.texts) > 50:
            raise HTTPException(status_code=400, detail="Too many texts (max 50)")
        
        # Получаем классификатор
        categorizer = get_question_categorizer()
        
        # Выполняем категоризацию для каждого текста
        results = []
        for text in request.texts:
            if text.strip():
                result = categorizer.categorize_question(text)
                category_info = categorizer.get_category_info(result.category)
                
                results.append(CategorizationResponse(
                    text=result.text,
                    category=result.category,
                    category_display_name=category_info.display_name if category_info else result.category,
                    confidence=result.confidence,
                    subcategory=result.subcategory,
                    keywords=result.keywords,
                    reasoning=result.reasoning if request.include_reasoning else None,
                    timestamp=result.timestamp
                ))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=List[CategoryInfoResponse])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка всех категорий"""
    try:
        categorizer = get_question_categorizer()
        categories = categorizer.get_all_categories()
        
        return [
            CategoryInfoResponse(
                name=cat.name,
                display_name=cat.display_name,
                description=cat.description,
                keywords_count=len(cat.keywords),
                patterns_count=len(cat.patterns),
                subcategories_count=len(cat.subcategories),
                priority=cat.priority,
                subcategories=cat.subcategories
            )
            for cat in categories
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{category_name}", response_model=CategoryInfoResponse)
async def get_category_info(
    category_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о конкретной категории"""
    try:
        categorizer = get_question_categorizer()
        category = categorizer.get_category_info(category_name)
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return CategoryInfoResponse(
            name=category.name,
            display_name=category.display_name,
            description=category.description,
            keywords_count=len(category.keywords),
            patterns_count=len(category.patterns),
            subcategories_count=len(category.subcategories),
            priority=category.priority,
            subcategories=category.subcategories
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{category_name}/keywords")
async def get_category_keywords(
    category_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение ключевых слов категории"""
    try:
        categorizer = get_question_categorizer()
        category = categorizer.get_category_info(category_name)
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return {
            "category": category_name,
            "keywords": category.keywords,
            "patterns": category.patterns,
            "subcategories": category.subcategories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categories/{category_name}/test")
async def test_category_classification(
    category_name: str,
    test_texts: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Тестирование классификации для конкретной категории"""
    try:
        categorizer = get_question_categorizer()
        category = categorizer.get_category_info(category_name)
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        if not test_texts:
            raise HTTPException(status_code=400, detail="Test texts cannot be empty")
        
        # Тестируем классификацию
        results = []
        correct_predictions = 0
        
        for text in test_texts:
            result = categorizer.categorize_question(text)
            is_correct = result.category == category_name
            if is_correct:
                correct_predictions += 1
            
            results.append({
                "text": text,
                "predicted_category": result.category,
                "confidence": result.confidence,
                "is_correct": is_correct,
                "keywords": result.keywords
            })
        
        accuracy = correct_predictions / len(test_texts) if test_texts else 0
        
        return {
            "category": category_name,
            "total_tests": len(test_texts),
            "correct_predictions": correct_predictions,
            "accuracy": accuracy,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_categorization_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики категоризации"""
    try:
        categorizer = get_question_categorizer()
        categories_info = categorizer.get_categories_with_stats()
        
        # В реальном приложении здесь будет запрос к базе данных
        # для получения статистики использования категорий
        
        # Имитация статистики
        stats = {
            "total_categories": len(categories_info),
            "total_classifications": 1250,
            "average_confidence": 0.82,
            "category_usage": {
                "трудовое_право": 250,
                "гражданское_право": 200,
                "налоговое_право": 180,
                "корпоративное_право": 150,
                "семейное_право": 120,
                "жилищное_право": 100,
                "уголовное_право": 80,
                "административное_право": 70,
                "общие_вопросы": 100
            },
            "accuracy_by_category": {
                "трудовое_право": 0.89,
                "гражданское_право": 0.85,
                "налоговое_право": 0.87,
                "корпоративное_право": 0.83,
                "семейное_право": 0.91,
                "жилищное_право": 0.86,
                "уголовное_право": 0.88,
                "административное_право": 0.84
            }
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_categorization_feedback(
    text: str,
    correct_category: str,
    predicted_category: str,
    feedback_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отправка обратной связи по категоризации"""
    try:
        # В реальном приложении здесь будет сохранение обратной связи
        # для улучшения классификатора
        
        feedback_data = {
            "text": text,
            "correct_category": correct_category,
            "predicted_category": predicted_category,
            "user_id": current_user.id,
            "feedback_notes": feedback_notes,
            "timestamp": datetime.now()
        }
        
        # Здесь можно добавить логику для:
        # 1. Сохранения обратной связи в базу данных
        # 2. Обновления классификатора на основе обратной связи
        # 3. Уведомления команды разработки о неточностях
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": f"cat_fb_{int(datetime.now().timestamp())}",
            "improvement_suggestions": _generate_improvement_suggestions(
                correct_category, predicted_category
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def categorization_health():
    """Проверка здоровья сервиса категоризации"""
    try:
        categorizer = get_question_categorizer()
        
        # Тестируем классификатор
        test_text = "Как оформить трудовой договор?"
        result = categorizer.categorize_question(test_text)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_result": {
                "text": test_text,
                "category": result.category,
                "confidence": result.confidence
            },
            "categories_count": len(categorizer.get_all_categories()),
            "classifier_version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _generate_improvement_suggestions(correct_category: str, predicted_category: str) -> List[str]:
    """Генерация предложений по улучшению"""
    suggestions = []
    
    if correct_category != predicted_category:
        suggestions.append(f"Классификатор ошибся: предсказал '{predicted_category}', а должно быть '{correct_category}'")
        
        # Специфические предложения
        if correct_category == "трудовое_право" and predicted_category == "гражданское_право":
            suggestions.append("Улучшить различение трудовых и гражданских договоров")
        elif correct_category == "налоговое_право" and predicted_category == "административное_право":
            suggestions.append("Уточнить классификацию налоговых и административных вопросов")
        elif correct_category == "семейное_право" and predicted_category == "гражданское_право":
            suggestions.append("Улучшить различение семейных и гражданских правоотношений")
    
    suggestions.append("Рассмотреть добавление новых ключевых слов")
    suggestions.append("Проверить актуальность паттернов классификации")
    
    return suggestions
