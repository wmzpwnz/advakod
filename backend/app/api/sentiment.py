from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..core.sentiment_analysis import (
    get_sentiment_analyzer,
    SentimentResult
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

class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., description="Текст для анализа тональности")
    use_ml: bool = Field(default=True, description="Использовать ML анализ")

class BatchSentimentRequest(BaseModel):
    texts: List[str] = Field(..., description="Список текстов для анализа")
    use_ml: bool = Field(default=True, description="Использовать ML анализ")

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    scores: Dict[str, float]
    emotions: Dict[str, float]
    keywords: List[str]
    timestamp: datetime

class SentimentStatsRequest(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Начальная дата")
    end_date: Optional[datetime] = Field(None, description="Конечная дата")
    category: Optional[str] = Field(None, description="Категория для фильтрации")

@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Анализ тональности текста"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Получаем анализатор
        analyzer = get_sentiment_analyzer()
        
        # Выполняем анализ
        if request.use_ml:
            result = await analyzer.analyze_with_ml(request.text)
        else:
            result = analyzer.russian_analyzer.analyze_sentiment(request.text)
        
        return SentimentResponse(
            text=result.text,
            sentiment=result.sentiment,
            confidence=result.confidence,
            scores=result.scores,
            emotions=result.emotions,
            keywords=result.keywords,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/batch", response_model=List[SentimentResponse])
async def analyze_sentiment_batch(
    request: BatchSentimentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Анализ тональности для списка текстов"""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="Texts list cannot be empty")
        
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="Too many texts (max 100)")
        
        # Получаем анализатор
        analyzer = get_sentiment_analyzer()
        
        # Выполняем анализ
        if request.use_ml:
            results = await analyzer.analyze_batch(request.texts)
        else:
            results = []
            for text in request.texts:
                result = analyzer.russian_analyzer.analyze_sentiment(text)
                results.append(result)
        
        return [
            SentimentResponse(
                text=result.text,
                sentiment=result.sentiment,
                confidence=result.confidence,
                scores=result.scores,
                emotions=result.emotions,
                keywords=result.keywords,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/chat-message")
async def analyze_chat_message_sentiment(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Анализ тональности сообщения чата"""
    try:
        # Получаем сообщение из базы данных
        from ..models.chat import ChatMessage
        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.user_id == current_user.id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Анализируем тональность
        analyzer = get_sentiment_analyzer()
        result = await analyzer.analyze_with_ml(message.content)
        
        # Сохраняем результат анализа в базе данных
        # (здесь можно добавить поле sentiment_analysis в модель ChatMessage)
        
        return {
            "message_id": message_id,
            "content": message.content,
            "sentiment_analysis": {
                "sentiment": result.sentiment,
                "confidence": result.confidence,
                "emotions": result.emotions,
                "keywords": result.keywords
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_sentiment_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики тональности"""
    try:
        # В реальном приложении здесь будет запрос к базе данных
        # для получения статистики анализа тональности
        
        # Имитация статистики
        stats = {
            "total_analyses": 1250,
            "positive_count": 450,
            "negative_count": 200,
            "neutral_count": 600,
            "average_confidence": 0.78,
            "emotion_distribution": {
                "joy": 0.25,
                "sadness": 0.15,
                "anger": 0.10,
                "fear": 0.08,
                "surprise": 0.12,
                "disgust": 0.05,
                "trust": 0.20,
                "anticipation": 0.05
            },
            "top_keywords": [
                {"word": "договор", "count": 120},
                {"word": "права", "count": 95},
                {"word": "обязанности", "count": 80},
                {"word": "закон", "count": 75},
                {"word": "суд", "count": 60}
            ],
            "sentiment_trend": [
                {"date": "2024-01-01", "positive": 0.4, "negative": 0.2, "neutral": 0.4},
                {"date": "2024-01-02", "positive": 0.45, "negative": 0.15, "neutral": 0.4},
                {"date": "2024-01-03", "positive": 0.5, "negative": 0.1, "neutral": 0.4}
            ]
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotions")
async def get_emotion_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка категорий эмоций"""
    try:
        emotions = [
            {
                "name": "joy",
                "display_name": "Радость",
                "description": "Положительные эмоции, счастье, восторг",
                "color": "#FFD700"
            },
            {
                "name": "sadness",
                "display_name": "Грусть",
                "description": "Негативные эмоции, печаль, тоска",
                "color": "#4169E1"
            },
            {
                "name": "anger",
                "display_name": "Гнев",
                "description": "Агрессивные эмоции, злость, ярость",
                "color": "#DC143C"
            },
            {
                "name": "fear",
                "display_name": "Страх",
                "description": "Тревожные эмоции, боязнь, беспокойство",
                "color": "#8B0000"
            },
            {
                "name": "surprise",
                "display_name": "Удивление",
                "description": "Неожиданные эмоции, изумление, шок",
                "color": "#FF8C00"
            },
            {
                "name": "disgust",
                "display_name": "Отвращение",
                "description": "Неприятные эмоции, омерзение, антипатия",
                "color": "#228B22"
            },
            {
                "name": "trust",
                "display_name": "Доверие",
                "description": "Положительные социальные эмоции, уверенность",
                "color": "#32CD32"
            },
            {
                "name": "anticipation",
                "display_name": "Ожидание",
                "description": "Эмоции предвкушения, надежда, планы",
                "color": "#9370DB"
            }
        ]
        
        return {"emotions": emotions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_sentiment_feedback(
    analysis_id: str,
    correct_sentiment: str,
    feedback_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отправка обратной связи по анализу тональности"""
    try:
        # В реальном приложении здесь будет сохранение обратной связи
        # для улучшения модели
        
        feedback_data = {
            "analysis_id": analysis_id,
            "user_id": current_user.id,
            "correct_sentiment": correct_sentiment,
            "feedback_notes": feedback_notes,
            "timestamp": datetime.now()
        }
        
        # Здесь можно добавить логику для:
        # 1. Сохранения обратной связи в базу данных
        # 2. Обновления модели на основе обратной связи
        # 3. Уведомления команды разработки о неточностях
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": f"fb_{int(datetime.now().timestamp())}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def sentiment_analysis_health():
    """Проверка здоровья сервиса анализа тональности"""
    try:
        analyzer = get_sentiment_analyzer()
        
        # Тестируем анализатор
        test_text = "Это тестовое сообщение для проверки работы анализатора тональности."
        result = analyzer.russian_analyzer.analyze_sentiment(test_text)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "test_result": {
                "sentiment": result.sentiment,
                "confidence": result.confidence
            },
            "services": {
                "rule_based_analyzer": "healthy",
                "ml_analyzer": "healthy" if analyzer.openai_api_key else "disabled"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
