"""
Сервис для модерации ответов ИИ
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from ..models.feedback import (
    ModerationReview, ModerationQueue, ModeratorStats,
    ProblemCategory, ResponseFeedback
)
from ..models.chat import ChatMessage, ChatSession
from ..models.user import User
from ..schemas.feedback import (
    ModerationReviewCreate, ModerationReviewUpdate,
    QueueFilters, MessageWithReview
)

logger = logging.getLogger(__name__)


class ModerationService:
    """Сервис для управления модерацией"""
    
    async def get_moderation_queue(
        self,
        db: Session,
        moderator_id: int,
        filters: Optional[QueueFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Получение очереди модерации с фильтрами"""
        try:
            query = db.query(ModerationQueue).join(
                ChatMessage, ModerationQueue.message_id == ChatMessage.id
            )
            
            # Применяем фильтры
            if filters:
                if filters.priority:
                    query = query.filter(ModerationQueue.priority == filters.priority.value)
                
                if filters.status:
                    query = query.filter(ModerationQueue.status == filters.status.value)
                
                if filters.assigned_to_me:
                    query = query.filter(ModerationQueue.assigned_to == moderator_id)
                
                if filters.date_from:
                    query = query.filter(ModerationQueue.created_at >= filters.date_from)
                
                if filters.date_to:
                    query = query.filter(ModerationQueue.created_at <= filters.date_to)
                
                if filters.min_confidence is not None:
                    query = query.filter(ModerationQueue.confidence_score >= filters.min_confidence)
                
                if filters.max_confidence is not None:
                    query = query.filter(ModerationQueue.confidence_score <= filters.max_confidence)
            
            # Сортировка: сначала high priority, потом по дате
            query = query.order_by(
                desc(ModerationQueue.priority == 'high'),
                desc(ModerationQueue.priority == 'medium'),
                ModerationQueue.created_at.asc()
            )
            
            # Подсчет total
            total = query.count()
            
            # Пагинация
            offset = (page - 1) * page_size
            queue_items = query.offset(offset).limit(page_size).all()
            
            # Формируем детальную информацию
            result = []
            for item in queue_items:
                message_data = await self._get_message_with_context(db, item.message_id)
                result.append({
                    "queue_item": item,
                    "message": message_data
                })
            
            return result, total
            
        except Exception as e:
            logger.error(f"Error getting moderation queue: {e}")
            raise
    
    async def _get_message_with_context(
        self,
        db: Session,
        message_id: int
    ) -> Dict[str, Any]:
        """Получение сообщения с полным контекстом"""
        # Получаем сообщение
        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()
        
        if not message:
            return None
        
        # Получаем сессию для контекста
        session = db.query(ChatSession).filter(
            ChatSession.id == message.session_id
        ).first()
        
        # Получаем предыдущее сообщение (вопрос пользователя)
        user_question = db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == message.session_id,
                ChatMessage.id < message.id,
                ChatMessage.role == 'user'
            )
        ).order_by(desc(ChatMessage.id)).first()
        
        # Получаем feedback пользователя
        user_feedback = db.query(ResponseFeedback).filter(
            ResponseFeedback.message_id == message_id
        ).first()
        
        # Получаем существующую оценку модератора
        existing_review = db.query(ModerationReview).filter(
            ModerationReview.message_id == message_id
        ).first()
        
        return {
            "message_id": message.id,
            "session_id": message.session_id,
            "user_question": user_question.content if user_question else "N/A",
            "ai_response": message.content,
            "created_at": message.created_at,
            "metadata": message.message_metadata,
            "user_feedback": user_feedback,
            "existing_review": existing_review
        }
    
    async def submit_review(
        self,
        db: Session,
        moderator_id: int,
        review_data: ModerationReviewCreate
    ) -> ModerationReview:
        """Отправка оценки модератора"""
        try:
            # Проверяем, существует ли сообщение
            message = db.query(ChatMessage).filter(
                ChatMessage.id == review_data.message_id
            ).first()
            
            if not message:
                raise ValueError(f"Message {review_data.message_id} not found")
            
            # Проверяем, не оценивал ли модератор уже это сообщение
            existing = db.query(ModerationReview).filter(
                and_(
                    ModerationReview.message_id == review_data.message_id,
                    ModerationReview.moderator_id == moderator_id
                )
            ).first()
            
            if existing:
                raise ValueError("You have already reviewed this message")
            
            # Получаем confidence score из метаданных
            confidence = None
            if message.message_metadata:
                confidence = message.message_metadata.get('confidence_score')
            
            # Создаем оценку
            review = ModerationReview(
                message_id=review_data.message_id,
                moderator_id=moderator_id,
                star_rating=review_data.star_rating,
                problem_categories=review_data.problem_categories,
                comment=review_data.comment,
                suggested_fix=review_data.suggested_fix,
                status="reviewed",
                priority=review_data.priority.value,
                original_confidence=confidence
            )
            
            db.add(review)
            db.commit()
            db.refresh(review)
            
            # Обновляем очередь модерации
            await self._update_queue_status(db, review_data.message_id, "completed")
            
            # Обновляем статистику модератора
            await self._update_moderator_stats(db, moderator_id, review)
            
            logger.info(f"Created review {review.id} by moderator {moderator_id}")
            return review
            
        except Exception as e:
            logger.error(f"Error submitting review: {e}")
            db.rollback()
            raise
    
    async def update_review(
        self,
        db: Session,
        review_id: int,
        moderator_id: int,
        update_data: ModerationReviewUpdate
    ) -> ModerationReview:
        """Обновление оценки модератора"""
        try:
            review = db.query(ModerationReview).filter(
                and_(
                    ModerationReview.id == review_id,
                    ModerationReview.moderator_id == moderator_id
                )
            ).first()
            
            if not review:
                raise ValueError("Review not found or access denied")
            
            # Обновляем поля
            if update_data.star_rating is not None:
                review.star_rating = update_data.star_rating
            
            if update_data.problem_categories is not None:
                review.problem_categories = update_data.problem_categories
            
            if update_data.comment is not None:
                review.comment = update_data.comment
            
            if update_data.suggested_fix is not None:
                review.suggested_fix = update_data.suggested_fix
            
            if update_data.status is not None:
                review.status = update_data.status.value
            
            if update_data.priority is not None:
                review.priority = update_data.priority.value
            
            review.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(review)
            
            logger.info(f"Updated review {review_id}")
            return review
            
        except Exception as e:
            logger.error(f"Error updating review: {e}")
            db.rollback()
            raise
    
    async def _update_queue_status(
        self,
        db: Session,
        message_id: int,
        status: str
    ):
        """Обновление статуса в очереди"""
        queue_item = db.query(ModerationQueue).filter(
            ModerationQueue.message_id == message_id
        ).first()
        
        if queue_item:
            queue_item.status = status
            if status == "completed":
                queue_item.completed_at = datetime.utcnow()
            db.commit()
    
    async def _update_moderator_stats(
        self,
        db: Session,
        moderator_id: int,
        review: ModerationReview
    ):
        """Обновление статистики модератора"""
        stats = db.query(ModeratorStats).filter(
            ModeratorStats.moderator_id == moderator_id
        ).first()
        
        if not stats:
            # Создаем новую статистику
            stats = ModeratorStats(
                moderator_id=moderator_id,
                total_reviews=0,
                points=0,
                badges=[],
                rank='novice',
                category_stats={}
            )
            db.add(stats)
        
        # Обновляем счетчики
        stats.total_reviews += 1
        
        # Начисляем баллы
        points = 10  # Базовые баллы за оценку
        if review.comment and len(review.comment) > 50:
            points += 10  # Бонус за детальный комментарий
        if review.suggested_fix:
            points += 30  # Бонус за предложенное исправление
        
        stats.points += points
        
        # Обновляем средний рейтинг
        if stats.average_rating is None:
            stats.average_rating = float(review.star_rating)
        else:
            stats.average_rating = (
                (stats.average_rating * (stats.total_reviews - 1) + review.star_rating) 
                / stats.total_reviews
            )
        
        # Обновляем статистику по категориям
        if not stats.category_stats:
            stats.category_stats = {}
        
        for category in review.problem_categories:
            stats.category_stats[category] = stats.category_stats.get(category, 0) + 1
        
        # Обновляем ранг
        stats.rank = self._calculate_rank(stats.total_reviews, stats.points)
        
        # Проверяем бейджи
        stats.badges = self._check_badges(stats)
        
        db.commit()
    
    def _calculate_rank(self, total_reviews: int, points: int) -> str:
        """Вычисление ранга модератора"""
        if total_reviews >= 1000 or points >= 10000:
            return 'legend'
        elif total_reviews >= 500 or points >= 5000:
            return 'master'
        elif total_reviews >= 100 or points >= 1000:
            return 'expert'
        else:
            return 'novice'
    
    def _check_badges(self, stats: ModeratorStats) -> List[str]:
        """Проверка и присвоение бейджей"""
        badges = stats.badges or []
        
        # Бейдж за количество оценок
        if stats.total_reviews >= 10 and 'first_10' not in badges:
            badges.append('first_10')
        if stats.total_reviews >= 100 and 'century' not in badges:
            badges.append('century')
        if stats.total_reviews >= 500 and 'veteran' not in badges:
            badges.append('veteran')
        
        # Бейдж за качество
        if stats.average_rating and stats.average_rating >= 8.0 and 'quality_expert' not in badges:
            badges.append('quality_expert')
        
        # Бейдж за детальность
        if stats.total_reviews >= 50:
            # Проверяем процент оценок с исправлениями
            reviews_with_fixes = db.query(ModerationReview).filter(
                and_(
                    ModerationReview.moderator_id == stats.moderator_id,
                    ModerationReview.suggested_fix.isnot(None)
                )
            ).count()
            
            if reviews_with_fixes / stats.total_reviews >= 0.5 and 'detail_oriented' not in badges:
                badges.append('detail_oriented')
        
        return badges
    
    async def get_moderator_stats(
        self,
        db: Session,
        moderator_id: int
    ) -> Optional[ModeratorStats]:
        """Получение статистики модератора"""
        return db.query(ModeratorStats).filter(
            ModeratorStats.moderator_id == moderator_id
        ).first()
    
    async def get_leaderboard(
        self,
        db: Session,
        period: str = 'all_time',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение рейтинга модераторов"""
        query = db.query(ModeratorStats).join(
            User, ModeratorStats.moderator_id == User.id
        )
        
        # Фильтр по периоду (если нужно)
        # TODO: добавить фильтрацию по периоду
        
        # Сортировка по баллам
        query = query.order_by(desc(ModeratorStats.points))
        
        stats = query.limit(limit).all()
        
        result = []
        for i, stat in enumerate(stats, 1):
            result.append({
                "rank": i,
                "moderator_id": stat.moderator_id,
                "moderator_name": stat.moderator.email,  # TODO: добавить имя
                "points": stat.points,
                "total_reviews": stat.total_reviews,
                "rank_title": stat.rank,
                "badges": stat.badges,
                "average_rating": stat.average_rating
            })
        
        return result
    
    async def get_problem_categories(
        self,
        db: Session,
        active_only: bool = True
    ) -> List[ProblemCategory]:
        """Получение списка категорий проблем"""
        query = db.query(ProblemCategory)
        
        if active_only:
            query = query.filter(ProblemCategory.is_active == True)
        
        return query.order_by(ProblemCategory.display_order).all()
    
    async def get_analytics(
        self,
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение аналитики модерации"""
        query = db.query(ModerationReview)
        
        if date_from:
            query = query.filter(ModerationReview.created_at >= date_from)
        if date_to:
            query = query.filter(ModerationReview.created_at <= date_to)
        
        total_reviews = query.count()
        
        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "top_problems": [],
                "reviews_by_date": [],
                "quality_trend": []
            }
        
        # Средний рейтинг
        avg_rating = db.query(func.avg(ModerationReview.star_rating)).filter(
            ModerationReview.created_at >= date_from if date_from else True,
            ModerationReview.created_at <= date_to if date_to else True
        ).scalar()
        
        # Распределение оценок
        rating_dist = db.query(
            ModerationReview.star_rating,
            func.count(ModerationReview.id).label('count')
        ).group_by(ModerationReview.star_rating).all()
        
        rating_distribution = {rating: count for rating, count in rating_dist}
        
        # Топ проблем (нужно распарсить JSON)
        # TODO: реализовать подсчет категорий из JSON
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "rating_distribution": rating_distribution,
            "top_problems": [],  # TODO
            "reviews_by_date": [],  # TODO
            "quality_trend": []  # TODO
        }


# Глобальный экземпляр
moderation_service = ModerationService()
