"""
Сервис пользовательских метрик и KPI
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError
import json
import re

from ..models.analytics import CustomMetric, MetricAlert
from ..models.user import User
from ..schemas.analytics import (
    CustomMetricCreate, CustomMetricUpdate, 
    MetricAlertCreate, MetricAlertUpdate
)
from ..services.notification_service import notification_service
from ..core.database import get_db

logger = logging.getLogger(__name__)


class MetricsService:
    """Сервис пользовательских метрик"""
    
    def __init__(self):
        self.predefined_kpis = self._initialize_predefined_kpis()
        self.metric_functions = self._initialize_metric_functions()
    
    def _initialize_predefined_kpis(self) -> List[Dict[str, Any]]:
        """Инициализация предустановленных KPI"""
        return [
            {
                'name': 'Активные пользователи (DAU)',
                'description': 'Количество активных пользователей за день',
                'formula': 'COUNT(DISTINCT user_id) WHERE last_login >= CURRENT_DATE',
                'unit': 'пользователей',
                'format_type': 'number',
                'category': 'Пользователи',
                'tags': ['активность', 'пользователи', 'dau']
            },
            {
                'name': 'Активные пользователи (MAU)',
                'description': 'Количество активных пользователей за месяц',
                'formula': 'COUNT(DISTINCT user_id) WHERE last_login >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)',
                'unit': 'пользователей',
                'format_type': 'number',
                'category': 'Пользователи',
                'tags': ['активность', 'пользователи', 'mau']
            },
            {
                'name': 'Конверсия в премиум',
                'description': 'Процент пользователей с премиум подпиской',
                'formula': '(COUNT(*) WHERE is_premium = true) / COUNT(*) * 100',
                'unit': '%',
                'format_type': 'percentage',
                'category': 'Конверсия',
                'tags': ['конверсия', 'премиум', 'подписка']
            },
            {
                'name': 'Средний доход на пользователя (ARPU)',
                'description': 'Средний доход на активного пользователя',
                'formula': 'SUM(revenue) / COUNT(DISTINCT user_id)',
                'unit': '₽',
                'format_type': 'currency',
                'category': 'Доходы',
                'tags': ['доходы', 'arpu', 'монетизация']
            },
            {
                'name': 'Время удержания пользователей',
                'description': 'Среднее время от регистрации до последней активности',
                'formula': 'AVG(DATEDIFF(last_login, created_at))',
                'unit': 'дней',
                'format_type': 'number',
                'category': 'Удержание',
                'tags': ['удержание', 'активность', 'время']
            },
            {
                'name': 'Частота использования',
                'description': 'Среднее количество запросов на пользователя в день',
                'formula': 'COUNT(queries) / COUNT(DISTINCT user_id) / 30',
                'unit': 'запросов/день',
                'format_type': 'number',
                'category': 'Использование',
                'tags': ['использование', 'запросы', 'активность']
            }
        ]
    
    def _initialize_metric_functions(self) -> Dict[str, Any]:
        """Инициализация функций для вычисления метрик"""
        return {
            'user_count': self._calculate_user_count,
            'active_users': self._calculate_active_users,
            'premium_conversion': self._calculate_premium_conversion,
            'average_session_time': self._calculate_average_session_time,
            'query_frequency': self._calculate_query_frequency
        }
    
    # Custom Metrics CRUD
    async def create_custom_metric(self, db: Session, metric_data: CustomMetricCreate, user_id: int) -> CustomMetric:
        """Создание пользовательской метрики"""
        try:
            # Валидируем формулу
            if not self._validate_formula(metric_data.formula):
                raise ValueError("Invalid formula syntax")
            
            metric = CustomMetric(
                name=metric_data.name,
                description=metric_data.description,
                formula=metric_data.formula,
                unit=metric_data.unit,
                format_type=metric_data.format_type,
                user_id=user_id,
                is_public=metric_data.is_public,
                category=metric_data.category,
                tags=metric_data.tags or []
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            logger.info(f"Created custom metric {metric.id} for user {user_id}")
            return metric
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating custom metric: {e}")
            raise
    
    async def get_custom_metrics(self, db: Session, user_id: int, include_public: bool = True) -> List[CustomMetric]:
        """Получение пользовательских метрик"""
        try:
            query = db.query(CustomMetric)
            
            if include_public:
                query = query.filter(
                    or_(CustomMetric.user_id == user_id, CustomMetric.is_public == True)
                )
            else:
                query = query.filter(CustomMetric.user_id == user_id)
            
            metrics = query.order_by(desc(CustomMetric.created_at)).all()
            return metrics
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting custom metrics: {e}")
            raise
    
    async def get_custom_metric(self, db: Session, metric_id: int, user_id: int) -> Optional[CustomMetric]:
        """Получение пользовательской метрики по ID"""
        try:
            metric = db.query(CustomMetric).filter(
                CustomMetric.id == metric_id,
                or_(CustomMetric.user_id == user_id, CustomMetric.is_public == True)
            ).first()
            
            return metric
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting custom metric {metric_id}: {e}")
            raise
    
    async def update_custom_metric(self, db: Session, metric_id: int, metric_data: CustomMetricUpdate, user_id: int) -> Optional[CustomMetric]:
        """Обновление пользовательской метрики"""
        try:
            metric = db.query(CustomMetric).filter(
                CustomMetric.id == metric_id,
                CustomMetric.user_id == user_id
            ).first()
            
            if not metric:
                return None
            
            update_data = metric_data.dict(exclude_unset=True)
            
            # Валидируем формулу если она изменилась
            if 'formula' in update_data and not self._validate_formula(update_data['formula']):
                raise ValueError("Invalid formula syntax")
            
            for field, value in update_data.items():
                setattr(metric, field, value)
            
            metric.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(metric)
            
            logger.info(f"Updated custom metric {metric_id}")
            return metric
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating custom metric {metric_id}: {e}")
            raise
    
    async def delete_custom_metric(self, db: Session, metric_id: int, user_id: int) -> bool:
        """Удаление пользовательской метрики"""
        try:
            metric = db.query(CustomMetric).filter(
                CustomMetric.id == metric_id,
                CustomMetric.user_id == user_id
            ).first()
            
            if not metric:
                return False
            
            db.delete(metric)
            db.commit()
            
            logger.info(f"Deleted custom metric {metric_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting custom metric {metric_id}: {e}")
            raise
    
    async def calculate_metric_value(self, db: Session, metric: CustomMetric) -> Dict[str, Any]:
        """Вычисление значения метрики"""
        try:
            # Пытаемся выполнить формулу как SQL запрос
            if self._is_sql_formula(metric.formula):
                value = await self._execute_sql_formula(db, metric.formula)
            else:
                # Используем предустановленные функции
                value = await self._execute_function_formula(db, metric.formula)
            
            return {
                'value': value,
                'formatted_value': self._format_metric_value(value, metric.format_type, metric.unit),
                'unit': metric.unit,
                'format_type': metric.format_type,
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating metric {metric.id}: {e}")
            return {
                'value': None,
                'formatted_value': 'Ошибка вычисления',
                'error': str(e),
                'calculated_at': datetime.utcnow().isoformat()
            }
    
    # Metric Alerts CRUD
    async def create_metric_alert(self, db: Session, alert_data: MetricAlertCreate, user_id: int) -> MetricAlert:
        """Создание алерта метрики"""
        try:
            # Проверяем существование метрики
            metric = await self.get_custom_metric(db, alert_data.metric_id, user_id)
            if not metric:
                raise ValueError("Metric not found")
            
            alert = MetricAlert(
                metric_id=alert_data.metric_id,
                name=alert_data.name,
                condition=alert_data.condition,
                threshold=alert_data.threshold,
                is_active=alert_data.is_active,
                notification_channels=alert_data.notification_channels,
                user_id=user_id
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Created metric alert {alert.id} for metric {alert_data.metric_id}")
            return alert
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating metric alert: {e}")
            raise
    
    async def get_metric_alerts(self, db: Session, user_id: int, metric_id: Optional[int] = None) -> List[MetricAlert]:
        """Получение алертов метрик"""
        try:
            query = db.query(MetricAlert).filter(MetricAlert.user_id == user_id)
            
            if metric_id:
                query = query.filter(MetricAlert.metric_id == metric_id)
            
            alerts = query.order_by(desc(MetricAlert.created_at)).all()
            return alerts
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting metric alerts: {e}")
            raise
    
    async def update_metric_alert(self, db: Session, alert_id: int, alert_data: MetricAlertUpdate, user_id: int) -> Optional[MetricAlert]:
        """Обновление алерта метрики"""
        try:
            alert = db.query(MetricAlert).filter(
                MetricAlert.id == alert_id,
                MetricAlert.user_id == user_id
            ).first()
            
            if not alert:
                return None
            
            update_data = alert_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(alert, field, value)
            
            alert.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Updated metric alert {alert_id}")
            return alert
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating metric alert {alert_id}: {e}")
            raise
    
    async def delete_metric_alert(self, db: Session, alert_id: int, user_id: int) -> bool:
        """Удаление алерта метрики"""
        try:
            alert = db.query(MetricAlert).filter(
                MetricAlert.id == alert_id,
                MetricAlert.user_id == user_id
            ).first()
            
            if not alert:
                return False
            
            db.delete(alert)
            db.commit()
            
            logger.info(f"Deleted metric alert {alert_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting metric alert {alert_id}: {e}")
            raise
    
    async def check_metric_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Проверка алертов метрик"""
        try:
            # Получаем все активные алерты
            active_alerts = db.query(MetricAlert).filter(
                MetricAlert.is_active == True
            ).all()
            
            triggered_alerts = []
            
            for alert in active_alerts:
                try:
                    # Получаем метрику
                    metric = db.query(CustomMetric).filter(
                        CustomMetric.id == alert.metric_id
                    ).first()
                    
                    if not metric:
                        continue
                    
                    # Вычисляем значение метрики
                    metric_result = await self.calculate_metric_value(db, metric)
                    
                    if metric_result.get('value') is None:
                        continue
                    
                    # Проверяем условие алерта
                    if self._check_alert_condition(metric_result['value'], alert.condition, alert.threshold):
                        triggered_alerts.append({
                            'alert': alert,
                            'metric': metric,
                            'current_value': metric_result['value'],
                            'formatted_value': metric_result['formatted_value'],
                            'threshold': alert.threshold,
                            'condition': alert.condition
                        })
                        
                        # Обновляем время последнего срабатывания
                        alert.last_triggered = datetime.utcnow()
                        db.commit()
                        
                        # Отправляем уведомления
                        await self._send_alert_notifications(alert, metric, metric_result)
                        
                except Exception as e:
                    logger.error(f"Error checking alert {alert.id}: {e}")
                    continue
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Error checking metric alerts: {e}")
            return []
    
    # Helper methods
    def _validate_formula(self, formula: str) -> bool:
        """Валидация формулы метрики"""
        try:
            # Базовая валидация SQL формулы
            if not formula or not formula.strip():
                return False
            
            # Проверяем на опасные SQL команды
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            formula_upper = formula.upper()
            
            for keyword in dangerous_keywords:
                if keyword in formula_upper:
                    return False
            
            # Проверяем базовый синтаксис
            if not re.match(r'^[A-Za-z0-9\s\(\)\*\+\-\/\=\<\>\,\._]+$', formula):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating formula: {e}")
            return False
    
    def _is_sql_formula(self, formula: str) -> bool:
        """Проверка, является ли формула SQL запросом"""
        sql_keywords = ['SELECT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'FROM', 'WHERE']
        formula_upper = formula.upper()
        
        return any(keyword in formula_upper for keyword in sql_keywords)
    
    async def _execute_sql_formula(self, db: Session, formula: str) -> float:
        """Выполнение SQL формулы"""
        try:
            # Заменяем таблицы на реальные имена
            formula = formula.replace('users', 'users')
            formula = formula.replace('queries', 'chat_messages')  # Предполагаем, что запросы хранятся в chat_messages
            
            # Выполняем запрос
            result = db.execute(text(formula)).scalar()
            
            return float(result) if result is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error executing SQL formula: {e}")
            raise
    
    async def _execute_function_formula(self, db: Session, formula: str) -> float:
        """Выполнение функциональной формулы"""
        try:
            # Пытаемся найти соответствующую функцию
            if formula in self.metric_functions:
                return await self.metric_functions[formula](db)
            else:
                # Пытаемся выполнить как простое математическое выражение
                return eval(formula)
                
        except Exception as e:
            logger.error(f"Error executing function formula: {e}")
            raise
    
    def _format_metric_value(self, value: float, format_type: str, unit: str) -> str:
        """Форматирование значения метрики"""
        try:
            if value is None:
                return 'N/A'
            
            if format_type == 'percentage':
                return f"{value:.1f}%"
            elif format_type == 'currency':
                return f"{value:,.2f} {unit or '₽'}"
            elif format_type == 'time':
                # Предполагаем, что время в секундах
                if value < 60:
                    return f"{value:.0f} сек"
                elif value < 3600:
                    return f"{value/60:.1f} мин"
                else:
                    return f"{value/3600:.1f} ч"
            else:
                # number format
                if value >= 1000000:
                    return f"{value/1000000:.1f}M {unit or ''}"
                elif value >= 1000:
                    return f"{value/1000:.1f}K {unit or ''}"
                else:
                    return f"{value:,.0f} {unit or ''}"
                    
        except Exception as e:
            logger.error(f"Error formatting metric value: {e}")
            return str(value)
    
    def _check_alert_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Проверка условия алерта"""
        try:
            if condition == 'gt':
                return value > threshold
            elif condition == 'lt':
                return value < threshold
            elif condition == 'eq':
                return abs(value - threshold) < 0.01  # Учитываем погрешность для float
            elif condition == 'gte':
                return value >= threshold
            elif condition == 'lte':
                return value <= threshold
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error checking alert condition: {e}")
            return False
    
    async def _send_alert_notifications(self, alert: MetricAlert, metric: CustomMetric, metric_result: Dict[str, Any]):
        """Отправка уведомлений об алерте"""
        try:
            message = f"Алерт метрики: {metric.name}\n"
            message += f"Текущее значение: {metric_result['formatted_value']}\n"
            message += f"Условие: {alert.condition} {alert.threshold}\n"
            message += f"Время: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Отправляем уведомления по указанным каналам
            for channel in alert.notification_channels:
                if channel == 'email':
                    # Здесь должна быть интеграция с email сервисом
                    pass
                elif channel == 'push':
                    # Отправляем push уведомление
                    await notification_service.send_notification(
                        user_id=alert.user_id,
                        title=f"Алерт метрики: {metric.name}",
                        message=message,
                        notification_type="metric_alert"
                    )
                elif channel == 'slack':
                    # Здесь должна быть интеграция со Slack
                    pass
                elif channel == 'telegram':
                    # Здесь должна быть интеграция с Telegram
                    pass
                    
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    # Predefined metric calculation functions
    async def _calculate_user_count(self, db: Session) -> float:
        """Подсчет общего количества пользователей"""
        try:
            count = db.query(User).count()
            return float(count)
        except Exception as e:
            logger.error(f"Error calculating user count: {e}")
            return 0.0
    
    async def _calculate_active_users(self, db: Session) -> float:
        """Подсчет активных пользователей"""
        try:
            # Активные пользователи за последние 30 дней
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            count = db.query(User).filter(
                User.updated_at >= thirty_days_ago,
                User.is_active == True
            ).count()
            return float(count)
        except Exception as e:
            logger.error(f"Error calculating active users: {e}")
            return 0.0
    
    async def _calculate_premium_conversion(self, db: Session) -> float:
        """Подсчет конверсии в премиум"""
        try:
            total_users = db.query(User).count()
            premium_users = db.query(User).filter(User.is_premium == True).count()
            
            if total_users == 0:
                return 0.0
            
            return (premium_users / total_users) * 100
        except Exception as e:
            logger.error(f"Error calculating premium conversion: {e}")
            return 0.0
    
    async def _calculate_average_session_time(self, db: Session) -> float:
        """Подсчет среднего времени сессии (заглушка)"""
        # Здесь должна быть логика подсчета времени сессий
        return 15.5  # Минуты
    
    async def _calculate_query_frequency(self, db: Session) -> float:
        """Подсчет частоты запросов (заглушка)"""
        # Здесь должна быть логика подсчета частоты запросов
        return 3.2  # Запросов в день на пользователя
    
    def get_predefined_kpis(self) -> List[Dict[str, Any]]:
        """Получение предустановленных KPI"""
        return self.predefined_kpis


# Глобальный экземпляр сервиса
metrics_service = MetricsService()