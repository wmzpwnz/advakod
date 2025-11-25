"""
Сервис ML прогнозов и рекомендаций
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import json
import numpy as np
from dataclasses import dataclass

from ..models.analytics import MLPrediction
from ..models.user import User
from ..core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Результат ML прогноза"""
    prediction_type: str
    value: float
    confidence: float
    features: Dict[str, Any]
    explanation: str
    recommendations: List[str]


class MLService:
    """Сервис ML прогнозов и рекомендаций"""
    
    def __init__(self):
        self.prediction_models = self._initialize_prediction_models()
        self.recommendation_engines = self._initialize_recommendation_engines()
    
    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Инициализация моделей прогнозирования"""
        return {
            'ltv': self._predict_ltv,
            'churn': self._predict_churn,
            'conversion': self._predict_conversion,
            'engagement': self._predict_engagement,
            'revenue': self._predict_revenue
        }
    
    def _initialize_recommendation_engines(self) -> Dict[str, Any]:
        """Инициализация движков рекомендаций"""
        return {
            'user_optimization': self._recommend_user_optimization,
            'metric_optimization': self._recommend_metric_optimization,
            'feature_usage': self._recommend_feature_usage,
            'retention_improvement': self._recommend_retention_improvement
        }
    
    async def generate_prediction(self, db: Session, prediction_type: str, 
                                target_user_id: Optional[int] = None) -> PredictionResult:
        """Генерация ML прогноза"""
        try:
            if prediction_type not in self.prediction_models:
                raise ValueError(f"Unknown prediction type: {prediction_type}")
            
            # Получаем функцию прогнозирования
            predict_func = self.prediction_models[prediction_type]
            
            # Генерируем прогноз
            result = await predict_func(db, target_user_id)
            
            # Сохраняем прогноз в БД
            await self._save_prediction(db, result, target_user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating prediction {prediction_type}: {e}")
            raise
    
    async def get_predictions(self, db: Session, prediction_type: Optional[str] = None,
                            target_user_id: Optional[int] = None, limit: int = 100) -> List[MLPrediction]:
        """Получение сохраненных прогнозов"""
        try:
            query = db.query(MLPrediction)
            
            if prediction_type:
                query = query.filter(MLPrediction.prediction_type == prediction_type)
            
            if target_user_id:
                query = query.filter(MLPrediction.target_user_id == target_user_id)
            
            # Фильтруем неустаревшие прогнозы
            query = query.filter(
                or_(
                    MLPrediction.expires_at.is_(None),
                    MLPrediction.expires_at > datetime.utcnow()
                )
            )
            
            predictions = query.order_by(desc(MLPrediction.created_at)).limit(limit).all()
            return predictions
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting predictions: {e}")
            raise    

    async def generate_recommendations(self, db: Session, recommendation_type: str,
                                     context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Генерация рекомендаций"""
        try:
            if recommendation_type not in self.recommendation_engines:
                raise ValueError(f"Unknown recommendation type: {recommendation_type}")
            
            # Получаем функцию рекомендаций
            recommend_func = self.recommendation_engines[recommendation_type]
            
            # Генерируем рекомендации
            recommendations = await recommend_func(db, context or {})
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations {recommendation_type}: {e}")
            raise
    
    async def get_user_insights(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Получение инсайтов о пользователе"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Генерируем различные прогнозы для пользователя
            ltv_prediction = await self.generate_prediction(db, 'ltv', user_id)
            churn_prediction = await self.generate_prediction(db, 'churn', user_id)
            engagement_prediction = await self.generate_prediction(db, 'engagement', user_id)
            
            # Генерируем рекомендации
            user_recommendations = await self.generate_recommendations(
                db, 'user_optimization', {'user_id': user_id}
            )
            
            return {
                'user_id': user_id,
                'predictions': {
                    'ltv': {
                        'value': ltv_prediction.value,
                        'confidence': ltv_prediction.confidence,
                        'explanation': ltv_prediction.explanation
                    },
                    'churn_risk': {
                        'value': churn_prediction.value,
                        'confidence': churn_prediction.confidence,
                        'explanation': churn_prediction.explanation
                    },
                    'engagement_score': {
                        'value': engagement_prediction.value,
                        'confidence': engagement_prediction.confidence,
                        'explanation': engagement_prediction.explanation
                    }
                },
                'recommendations': user_recommendations,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user insights for {user_id}: {e}")
            raise
    
    async def get_business_insights(self, db: Session) -> Dict[str, Any]:
        """Получение бизнес-инсайтов"""
        try:
            # Генерируем прогнозы на уровне бизнеса
            revenue_prediction = await self.generate_prediction(db, 'revenue')
            
            # Генерируем рекомендации по оптимизации метрик
            metric_recommendations = await self.generate_recommendations(
                db, 'metric_optimization'
            )
            
            # Рекомендации по улучшению удержания
            retention_recommendations = await self.generate_recommendations(
                db, 'retention_improvement'
            )
            
            # Рекомендации по использованию функций
            feature_recommendations = await self.generate_recommendations(
                db, 'feature_usage'
            )
            
            return {
                'predictions': {
                    'revenue_forecast': {
                        'value': revenue_prediction.value,
                        'confidence': revenue_prediction.confidence,
                        'explanation': revenue_prediction.explanation
                    }
                },
                'recommendations': {
                    'metrics': metric_recommendations,
                    'retention': retention_recommendations,
                    'features': feature_recommendations
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting business insights: {e}")
            raise
    
    # Prediction Models Implementation
    async def _predict_ltv(self, db: Session, user_id: Optional[int] = None) -> PredictionResult:
        """Прогноз LTV пользователя"""
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                # Простая модель LTV на основе типа подписки и активности
                base_ltv = 0
                if user.subscription_type == 'premium':
                    base_ltv = 5000  # ₽
                elif user.subscription_type == 'basic':
                    base_ltv = 2000  # ₽
                else:
                    base_ltv = 500   # ₽
                
                # Корректируем на основе активности
                if user.is_active:
                    base_ltv *= 1.5
                
                # Корректируем на основе времени регистрации
                if user.created_at:
                    days_since_registration = (datetime.utcnow() - user.created_at).days
                    if days_since_registration > 365:
                        base_ltv *= 1.2  # Лояльные пользователи
                
                confidence = 0.75 if user.is_premium else 0.65
                
                return PredictionResult(
                    prediction_type='ltv',
                    value=base_ltv,
                    confidence=confidence,
                    features={
                        'subscription_type': user.subscription_type,
                        'is_active': user.is_active,
                        'days_since_registration': days_since_registration if user.created_at else 0
                    },
                    explanation=f"Прогноз LTV основан на типе подписки ({user.subscription_type}), активности пользователя и времени в системе",
                    recommendations=[
                        "Предложить upgrade подписки для увеличения LTV",
                        "Улучшить engagement для повышения удержания",
                        "Персонализировать предложения на основе поведения"
                    ]
                )
            else:
                # Средний LTV по всем пользователям
                total_users = db.query(User).count()
                premium_users = db.query(User).filter(User.is_premium == True).count()
                
                avg_ltv = (premium_users * 5000 + (total_users - premium_users) * 1000) / total_users if total_users > 0 else 0
                
                return PredictionResult(
                    prediction_type='ltv',
                    value=avg_ltv,
                    confidence=0.70,
                    features={'total_users': total_users, 'premium_users': premium_users},
                    explanation="Средний LTV рассчитан на основе распределения типов подписок",
                    recommendations=[
                        "Увеличить конверсию в премиум подписки",
                        "Улучшить onboarding новых пользователей",
                        "Развивать программы лояльности"
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error predicting LTV: {e}")
            raise
    
    async def _predict_churn(self, db: Session, user_id: Optional[int] = None) -> PredictionResult:
        """Прогноз риска оттока пользователя"""
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                churn_risk = 0.0
                
                # Факторы риска оттока
                if not user.is_active:
                    churn_risk += 0.4
                
                if user.created_at:
                    days_since_registration = (datetime.utcnow() - user.created_at).days
                    if days_since_registration < 7:
                        churn_risk += 0.3  # Новые пользователи в зоне риска
                
                if user.subscription_type == 'free':
                    churn_risk += 0.2
                
                # Ограничиваем риск от 0 до 1
                churn_risk = min(churn_risk, 1.0)
                
                confidence = 0.80
                
                risk_level = "Высокий" if churn_risk > 0.7 else "Средний" if churn_risk > 0.4 else "Низкий"
                
                return PredictionResult(
                    prediction_type='churn',
                    value=churn_risk,
                    confidence=confidence,
                    features={
                        'is_active': user.is_active,
                        'subscription_type': user.subscription_type,
                        'days_since_registration': days_since_registration if user.created_at else 0
                    },
                    explanation=f"Риск оттока: {risk_level} ({churn_risk:.1%}). Основан на активности, типе подписки и времени в системе",
                    recommendations=[
                        "Отправить персонализированное предложение" if churn_risk > 0.5 else "Продолжить мониторинг активности",
                        "Предложить помощь в использовании продукта",
                        "Провести опрос удовлетворенности"
                    ]
                )
            else:
                # Общий риск оттока
                total_users = db.query(User).count()
                inactive_users = db.query(User).filter(User.is_active == False).count()
                
                avg_churn_risk = inactive_users / total_users if total_users > 0 else 0
                
                return PredictionResult(
                    prediction_type='churn',
                    value=avg_churn_risk,
                    confidence=0.75,
                    features={'total_users': total_users, 'inactive_users': inactive_users},
                    explanation=f"Общий риск оттока составляет {avg_churn_risk:.1%}",
                    recommendations=[
                        "Улучшить onboarding процесс",
                        "Развивать программы удержания",
                        "Анализировать причины оттока"
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error predicting churn: {e}")
            raise   
 
    async def _predict_conversion(self, db: Session, user_id: Optional[int] = None) -> PredictionResult:
        """Прогноз конверсии пользователя"""
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                conversion_probability = 0.1  # Базовая вероятность
                
                # Факторы, влияющие на конверсию
                if user.is_active:
                    conversion_probability += 0.3
                
                if user.created_at:
                    days_since_registration = (datetime.utcnow() - user.created_at).days
                    if 7 <= days_since_registration <= 30:
                        conversion_probability += 0.2  # Оптимальное окно для конверсии
                
                if user.subscription_type == 'basic':
                    conversion_probability += 0.4  # Уже показал готовность платить
                
                conversion_probability = min(conversion_probability, 1.0)
                
                return PredictionResult(
                    prediction_type='conversion',
                    value=conversion_probability,
                    confidence=0.70,
                    features={
                        'is_active': user.is_active,
                        'subscription_type': user.subscription_type,
                        'days_since_registration': days_since_registration if user.created_at else 0
                    },
                    explanation=f"Вероятность конверсии в премиум: {conversion_probability:.1%}",
                    recommendations=[
                        "Показать преимущества премиум подписки",
                        "Предложить пробный период",
                        "Персонализировать предложения"
                    ]
                )
            else:
                # Общая конверсия
                total_users = db.query(User).count()
                premium_users = db.query(User).filter(User.is_premium == True).count()
                
                conversion_rate = premium_users / total_users if total_users > 0 else 0
                
                return PredictionResult(
                    prediction_type='conversion',
                    value=conversion_rate,
                    confidence=0.80,
                    features={'total_users': total_users, 'premium_users': premium_users},
                    explanation=f"Общая конверсия в премиум: {conversion_rate:.1%}",
                    recommendations=[
                        "Оптимизировать воронку конверсии",
                        "A/B тестировать ценовые предложения",
                        "Улучшить value proposition"
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error predicting conversion: {e}")
            raise
    
    async def _predict_engagement(self, db: Session, user_id: Optional[int] = None) -> PredictionResult:
        """Прогноз уровня вовлеченности пользователя"""
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                engagement_score = 0.5  # Базовый уровень
                
                # Факторы вовлеченности
                if user.is_active:
                    engagement_score += 0.3
                
                if user.is_premium:
                    engagement_score += 0.2
                
                # Время в системе
                if user.created_at:
                    days_since_registration = (datetime.utcnow() - user.created_at).days
                    if days_since_registration > 30:
                        engagement_score += 0.1
                
                engagement_score = min(engagement_score, 1.0)
                
                level = "Высокий" if engagement_score > 0.7 else "Средний" if engagement_score > 0.4 else "Низкий"
                
                return PredictionResult(
                    prediction_type='engagement',
                    value=engagement_score,
                    confidence=0.75,
                    features={
                        'is_active': user.is_active,
                        'is_premium': user.is_premium,
                        'days_since_registration': days_since_registration if user.created_at else 0
                    },
                    explanation=f"Уровень вовлеченности: {level} ({engagement_score:.1%})",
                    recommendations=[
                        "Предложить новые функции для изучения",
                        "Отправить образовательный контент",
                        "Пригласить к участию в сообществе"
                    ]
                )
            else:
                # Средний уровень вовлеченности
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                
                avg_engagement = active_users / total_users if total_users > 0 else 0
                
                return PredictionResult(
                    prediction_type='engagement',
                    value=avg_engagement,
                    confidence=0.70,
                    features={'total_users': total_users, 'active_users': active_users},
                    explanation=f"Средний уровень вовлеченности: {avg_engagement:.1%}",
                    recommendations=[
                        "Улучшить пользовательский опыт",
                        "Добавить геймификацию",
                        "Развивать сообщество пользователей"
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            raise
    
    async def _predict_revenue(self, db: Session, user_id: Optional[int] = None) -> PredictionResult:
        """Прогноз доходов"""
        try:
            # Прогноз доходов на следующий месяц
            total_users = db.query(User).count()
            premium_users = db.query(User).filter(User.is_premium == True).count()
            basic_users = db.query(User).filter(User.subscription_type == 'basic').count()
            
            # Примерные цены подписок
            premium_price = 1000  # ₽/месяц
            basic_price = 500     # ₽/месяц
            
            predicted_revenue = (premium_users * premium_price) + (basic_users * basic_price)
            
            # Учитываем рост/снижение
            growth_factor = 1.05  # 5% рост
            predicted_revenue *= growth_factor
            
            return PredictionResult(
                prediction_type='revenue',
                value=predicted_revenue,
                confidence=0.65,
                features={
                    'total_users': total_users,
                    'premium_users': premium_users,
                    'basic_users': basic_users,
                    'growth_factor': growth_factor
                },
                explanation=f"Прогноз доходов на следующий месяц: {predicted_revenue:,.0f} ₽",
                recommendations=[
                    "Увеличить конверсию в платные подписки",
                    "Оптимизировать ценовую стратегию",
                    "Развивать дополнительные источники дохода"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error predicting revenue: {e}")
            raise
    
    # Recommendation Engines Implementation
    async def _recommend_user_optimization(self, db: Session, context: Dict[str, Any]) -> List[str]:
        """Рекомендации по оптимизации пользователя"""
        try:
            user_id = context.get('user_id')
            if not user_id:
                return ["Не указан ID пользователя для рекомендаций"]
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return ["Пользователь не найден"]
            
            recommendations = []
            
            # Рекомендации на основе статуса пользователя
            if not user.is_active:
                recommendations.extend([
                    "Отправить welcome-back кампанию",
                    "Предложить персональную консультацию",
                    "Показать новые функции продукта"
                ])
            
            if user.subscription_type == 'free':
                recommendations.extend([
                    "Показать value proposition премиум подписки",
                    "Предложить бесплатный пробный период",
                    "Отправить кейсы успешного использования"
                ])
            
            if user.is_premium:
                recommendations.extend([
                    "Предложить дополнительные премиум функции",
                    "Пригласить к участию в beta-тестировании",
                    "Запросить отзыв о продукте"
                ])
            
            return recommendations[:5]  # Ограничиваем количество рекомендаций
            
        except Exception as e:
            logger.error(f"Error generating user optimization recommendations: {e}")
            return ["Ошибка генерации рекомендаций"]
    
    async def _recommend_metric_optimization(self, db: Session, context: Dict[str, Any]) -> List[str]:
        """Рекомендации по оптимизации метрик"""
        try:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            premium_users = db.query(User).filter(User.is_premium == True).count()
            
            recommendations = []
            
            # Анализируем ключевые метрики
            activation_rate = active_users / total_users if total_users > 0 else 0
            conversion_rate = premium_users / total_users if total_users > 0 else 0
            
            if activation_rate < 0.7:
                recommendations.append("Улучшить onboarding процесс для повышения активации пользователей")
            
            if conversion_rate < 0.1:
                recommendations.append("Оптимизировать воронку конверсии в платные подписки")
            
            if total_users < 1000:
                recommendations.append("Усилить маркетинговые активности для привлечения новых пользователей")
            
            recommendations.extend([
                "Внедрить A/B тестирование ключевых элементов интерфейса",
                "Настроить когортный анализ для отслеживания retention",
                "Создать систему NPS для измерения удовлетворенности"
            ])
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error generating metric optimization recommendations: {e}")
            return ["Ошибка генерации рекомендаций по метрикам"]
    
    async def _recommend_feature_usage(self, db: Session, context: Dict[str, Any]) -> List[str]:
        """Рекомендации по использованию функций"""
        try:
            recommendations = [
                "Создать интерактивные туры по новым функциям",
                "Добавить подсказки и tooltips в интерфейс",
                "Отправлять еженедельные дайджесты с полезными функциями",
                "Создать базу знаний с видео-инструкциями",
                "Внедрить прогрессивное раскрытие функций для новых пользователей"
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating feature usage recommendations: {e}")
            return ["Ошибка генерации рекомендаций по функциям"]
    
    async def _recommend_retention_improvement(self, db: Session, context: Dict[str, Any]) -> List[str]:
        """Рекомендации по улучшению удержания"""
        try:
            recommendations = [
                "Внедрить систему push-уведомлений для неактивных пользователей",
                "Создать программу лояльности с наградами за активность",
                "Персонализировать контент на основе поведения пользователя",
                "Добавить социальные функции для создания сообщества",
                "Проводить регулярные опросы для выявления проблем пользователей"
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating retention improvement recommendations: {e}")
            return ["Ошибка генерации рекомендаций по удержанию"]
    
    async def _save_prediction(self, db: Session, result: PredictionResult, target_user_id: Optional[int] = None):
        """Сохранение прогноза в БД"""
        try:
            # Устанавливаем срок действия прогноза
            expires_at = datetime.utcnow() + timedelta(days=7)  # Прогнозы действительны 7 дней
            
            prediction = MLPrediction(
                model_name="simple_heuristic_model",
                prediction_type=result.prediction_type,
                target_user_id=target_user_id,
                prediction_value=result.value,
                confidence_score=result.confidence,
                features=result.features,
                model_version="1.0",
                expires_at=expires_at
            )
            
            db.add(prediction)
            db.commit()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error saving prediction: {e}")
            # Не прерываем выполнение, если не удалось сохранить


# Глобальный экземпляр сервиса
ml_service = MLService()