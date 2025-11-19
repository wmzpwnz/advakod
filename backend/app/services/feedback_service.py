"""
Сервис для работы с обратной связью пользователей
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.feedback import ResponseFeedback, ModerationQueue
from ..models.chat import ChatMessage
from ..schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)


class FeedbackService:
    """Сервис для управления обратной связью"""
    
    async def submit_feedback(
        self,
        db: Session,
        user_id: int,
        feedback_data: FeedbackCreate
    ) -> ResponseFeedback:
        """Отправка feedback от пользователя"""
        try:
            # Проверяем, существует ли сообщение
            message = db.query(ChatMessage).filter(
                ChatMessage.id == feedback_data.message_id
            ).first()
            
            if not message:
                raise ValueError(f"Message {feedback_data.message_id} not found")
            
            # Проверяем, не оставлял ли пользователь уже feedback
            existing = db.query(ResponseFeedback).filter(
                and_(
                    ResponseFeedback.message_id == feedback_data.message_id,
                    ResponseFeedback.user_id == user_id
                )
            ).first()
            
            if existing:
                # Обновляем существующий feedback
                existing.rating = feedback_data.rating.value
                existing.reason = feedback_data.reason.value if feedback_data.reason else None
                existing.comment = feedback_data.comment
                db.commit()
                db.refresh(existing)
                
                logger.info(f"Updated feedback {existing.id} for message {feedback_data.message_id}")
                return existing
            
            # Создаем новый feedback
            feedback = ResponseFeedback(
                message_id=feedback_data.message_id,
                user_id=user_id,
                rating=feedback_data.rating.value,
                reason=feedback_data.reason.value if feedback_data.reason else None,
                comment=feedback_data.comment,
                feedback_metadata={}
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            # Если оценка негативная, добавляем в очередь модерации
            if feedback_data.rating.value == "negative":
                await self._add_to_moderation_queue(
                    db=db,
                    message_id=feedback_data.message_id,
                    priority="high",
                    reason="user_complaint"
                )
            
            logger.info(f"Created feedback {feedback.id} for message {feedback_data.message_id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            db.rollback()
            raise
    
    async def get_message_feedback(
        self,
        db: Session,
        message_id: int
    ) -> Optional[ResponseFeedback]:
        """Получение feedback для сообщения"""
        return db.query(ResponseFeedback).filter(
            ResponseFeedback.message_id == message_id
        ).first()
    
    async def get_user_feedback_history(
        self,
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[ResponseFeedback]:
        """История feedback пользователя"""
        return db.query(ResponseFeedback).filter(
            ResponseFeedback.user_id == user_id
        ).order_by(
            ResponseFeedback.created_at.desc()
        ).limit(limit).all()
    
    async def get_feedback_stats(
        self,
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Статистика по feedback"""
        query = db.query(ResponseFeedback)
        
        if date_from:
            query = query.filter(ResponseFeedback.created_at >= date_from)
        if date_to:
            query = query.filter(ResponseFeedback.created_at <= date_to)
        
        total = query.count()
        
        # Распределение по рейтингам
        rating_dist = db.query(
            ResponseFeedback.rating,
            func.count(ResponseFeedback.id).label('count')
        ).group_by(ResponseFeedback.rating).all()
        
        rating_distribution = {rating: count for rating, count in rating_dist}
        
        # Распределение по причинам
        reason_dist = db.query(
            ResponseFeedback.reason,
            func.count(ResponseFeedback.id).label('count')
        ).filter(
            ResponseFeedback.reason.isnot(None)
        ).group_by(ResponseFeedback.reason).all()
        
        reason_distribution = {reason: count for reason, count in reason_dist}
        
        # Процент положительных оценок
        positive_count = rating_distribution.get('positive', 0)
        positive_rate = (positive_count / total * 100) if total > 0 else 0
        
        return {
            "total_feedback": total,
            "rating_distribution": rating_distribution,
            "reason_distribution": reason_distribution,
            "positive_rate": round(positive_rate, 2),
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            }
        }
    
    async def _add_to_moderation_queue(
        self,
        db: Session,
        message_id: int,
        priority: str = "medium",
        reason: Optional[str] = None
    ):
        """Добавление сообщения в очередь модерации"""
        try:
            # Проверяем, нет ли уже в очереди
            existing = db.query(ModerationQueue).filter(
                ModerationQueue.message_id == message_id
            ).first()
            
            if existing:
                # Обновляем приоритет если новый выше
                if priority == "high" and existing.priority != "high":
                    existing.priority = priority
                    existing.reason = reason
                    db.commit()
                return
            
            # Добавляем в очередь
            queue_item = ModerationQueue(
                message_id=message_id,
                priority=priority,
                reason=reason,
                status="pending"
            )
            
            db.add(queue_item)
            db.commit()
            
            logger.info(f"Added message {message_id} to moderation queue with priority {priority}")
            
        except Exception as e:
            logger.error(f"Error adding to moderation queue: {e}")
            db.rollback()


# Глобальный экземпляр
feedback_service = FeedbackService()
