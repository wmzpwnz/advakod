"""
Сервис продвинутой аналитики и отчетности
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from ..models.analytics import (
    Dashboard, DashboardWidget, CustomMetric, MetricAlert,
    CohortAnalysis, UserSegment, MLPrediction, ReportTemplate, ReportExecution
)
from ..models.user import User
from ..schemas.analytics import (
    DashboardCreate, DashboardUpdate, DashboardWidgetCreate, DashboardWidgetUpdate,
    CustomMetricCreate, CustomMetricUpdate, MetricAlertCreate, MetricAlertUpdate,
    CohortAnalysisCreate, UserSegmentCreate, UserSegmentUpdate,
    DataSourceInfo, WidgetData
)
from ..core.database import get_db

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Сервис аналитики"""
    
    def __init__(self):
        self.data_sources = self._initialize_data_sources()
        self.widget_templates = self._initialize_widget_templates()
    
    def _initialize_data_sources(self) -> List[DataSourceInfo]:
        """Инициализация источников данных"""
        return [
            DataSourceInfo(
                id="users",
                name="Пользователи",
                description="Данные о пользователях системы",
                fields=[
                    {"name": "id", "type": "integer", "description": "ID пользователя"},
                    {"name": "email", "type": "string", "description": "Email пользователя"},
                    {"name": "created_at", "type": "datetime", "description": "Дата регистрации"},
                    {"name": "last_login", "type": "datetime", "description": "Последний вход"},
                    {"name": "is_active", "type": "boolean", "description": "Активен ли пользователь"},
                    {"name": "subscription_type", "type": "string", "description": "Тип подписки"},
                ]
            ),
            DataSourceInfo(
                id="queries",
                name="Запросы",
                description="Данные о запросах к ИИ",
                fields=[
                    {"name": "id", "type": "integer", "description": "ID запроса"},
                    {"name": "user_id", "type": "integer", "description": "ID пользователя"},
                    {"name": "query_text", "type": "string", "description": "Текст запроса"},
                    {"name": "response_time", "type": "float", "description": "Время ответа"},
                    {"name": "quality_score", "type": "float", "description": "Оценка качества"},
                    {"name": "legal_field", "type": "string", "description": "Отрасль права"},
                    {"name": "created_at", "type": "datetime", "description": "Время запроса"},
                ]
            ),
            DataSourceInfo(
                id="moderation",
                name="Модерация",
                description="Данные модерации ответов",
                fields=[
                    {"name": "id", "type": "integer", "description": "ID модерации"},
                    {"name": "message_id", "type": "integer", "description": "ID сообщения"},
                    {"name": "moderator_id", "type": "integer", "description": "ID модератора"},
                    {"name": "rating", "type": "integer", "description": "Оценка (1-10)"},
                    {"name": "comment", "type": "string", "description": "Комментарий"},
                    {"name": "created_at", "type": "datetime", "description": "Время модерации"},
                ]
            ),
            DataSourceInfo(
                id="system_metrics",
                name="Системные метрики",
                description="Метрики производительности системы",
                fields=[
                    {"name": "timestamp", "type": "datetime", "description": "Время измерения"},
                    {"name": "cpu_usage", "type": "float", "description": "Использование CPU"},
                    {"name": "memory_usage", "type": "float", "description": "Использование памяти"},
                    {"name": "response_time", "type": "float", "description": "Время ответа"},
                    {"name": "error_rate", "type": "float", "description": "Частота ошибок"},
                ]
            )
        ]
    
    def _initialize_widget_templates(self) -> List[Dict[str, Any]]:
        """Инициализация шаблонов виджетов"""
        return [
            {
                "id": "user_count",
                "name": "Количество пользователей",
                "type": "metric",
                "icon": "users",
                "config": {
                    "data_source": "users",
                    "aggregation": "count",
                    "time_range": "24h"
                }
            },
            {
                "id": "active_users",
                "name": "Активные пользователи",
                "type": "metric",
                "icon": "user-check",
                "config": {
                    "data_source": "users",
                    "aggregation": "count",
                    "filters": {"is_active": True},
                    "time_range": "24h"
                }
            },
            {
                "id": "queries_per_hour",
                "name": "Запросы в час",
                "type": "chart",
                "chart_type": "line",
                "icon": "trending-up",
                "config": {
                    "data_source": "queries",
                    "aggregation": "count",
                    "time_range": "24h",
                    "group_by": "hour"
                }
            },
            {
                "id": "response_time_trend",
                "name": "Тренд времени ответа",
                "type": "chart",
                "chart_type": "area",
                "icon": "clock",
                "config": {
                    "data_source": "queries",
                    "aggregation": "avg",
                    "field": "response_time",
                    "time_range": "24h",
                    "group_by": "hour"
                }
            },
            {
                "id": "quality_distribution",
                "name": "Распределение качества",
                "type": "chart",
                "chart_type": "pie",
                "icon": "pie-chart",
                "config": {
                    "data_source": "queries",
                    "field": "quality_score",
                    "time_range": "24h",
                    "buckets": ["0-0.3", "0.3-0.7", "0.7-1.0"]
                }
            },
            {
                "id": "legal_fields_table",
                "name": "Популярные отрасли права",
                "type": "table",
                "icon": "table",
                "config": {
                    "data_source": "queries",
                    "group_by": "legal_field",
                    "aggregation": "count",
                    "time_range": "7d",
                    "limit": 10
                }
            }
        ]
    
    # Dashboard CRUD operations
    async def create_dashboard(self, db: Session, dashboard_data: DashboardCreate, user_id: int) -> Dashboard:
        """Создание дашборда"""
        try:
            dashboard = Dashboard(
                name=dashboard_data.name,
                description=dashboard_data.description,
                user_id=user_id,
                layout=dashboard_data.layout or {},
                is_public=dashboard_data.is_public,
                is_default=dashboard_data.is_default
            )
            
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            
            logger.info(f"Created dashboard {dashboard.id} for user {user_id}")
            return dashboard
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating dashboard: {e}")
            raise
    
    async def get_dashboards(self, db: Session, user_id: int, include_public: bool = True) -> List[Dashboard]:
        """Получение дашбордов пользователя"""
        try:
            query = db.query(Dashboard)
            
            if include_public:
                query = query.filter(
                    or_(Dashboard.user_id == user_id, Dashboard.is_public == True)
                )
            else:
                query = query.filter(Dashboard.user_id == user_id)
            
            dashboards = query.order_by(desc(Dashboard.updated_at)).all()
            return dashboards
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting dashboards: {e}")
            raise
    
    async def get_dashboard(self, db: Session, dashboard_id: int, user_id: int) -> Optional[Dashboard]:
        """Получение дашборда по ID"""
        try:
            dashboard = db.query(Dashboard).filter(
                Dashboard.id == dashboard_id,
                or_(Dashboard.user_id == user_id, Dashboard.is_public == True)
            ).first()
            
            return dashboard
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting dashboard {dashboard_id}: {e}")
            raise
    
    async def update_dashboard(self, db: Session, dashboard_id: int, dashboard_data: DashboardUpdate, user_id: int) -> Optional[Dashboard]:
        """Обновление дашборда"""
        try:
            dashboard = db.query(Dashboard).filter(
                Dashboard.id == dashboard_id,
                Dashboard.user_id == user_id
            ).first()
            
            if not dashboard:
                return None
            
            update_data = dashboard_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(dashboard, field, value)
            
            dashboard.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(dashboard)
            
            logger.info(f"Updated dashboard {dashboard_id}")
            return dashboard
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating dashboard {dashboard_id}: {e}")
            raise
    
    async def delete_dashboard(self, db: Session, dashboard_id: int, user_id: int) -> bool:
        """Удаление дашборда"""
        try:
            dashboard = db.query(Dashboard).filter(
                Dashboard.id == dashboard_id,
                Dashboard.user_id == user_id
            ).first()
            
            if not dashboard:
                return False
            
            db.delete(dashboard)
            db.commit()
            
            logger.info(f"Deleted dashboard {dashboard_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
            raise
    
    # Widget CRUD operations
    async def create_widget(self, db: Session, widget_data: DashboardWidgetCreate, dashboard_id: int, user_id: int) -> Optional[DashboardWidget]:
        """Создание виджета"""
        try:
            # Проверяем права на дашборд
            dashboard = await self.get_dashboard(db, dashboard_id, user_id)
            if not dashboard or dashboard.user_id != user_id:
                return None
            
            widget = DashboardWidget(
                dashboard_id=dashboard_id,
                widget_type=widget_data.widget_type,
                title=widget_data.title,
                config=widget_data.config.dict(),
                position=widget_data.position.dict(),
                data_source=widget_data.data_source,
                refresh_interval=widget_data.refresh_interval
            )
            
            db.add(widget)
            db.commit()
            db.refresh(widget)
            
            logger.info(f"Created widget {widget.id} for dashboard {dashboard_id}")
            return widget
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating widget: {e}")
            raise
    
    async def update_widget(self, db: Session, widget_id: int, widget_data: DashboardWidgetUpdate, user_id: int) -> Optional[DashboardWidget]:
        """Обновление виджета"""
        try:
            widget = db.query(DashboardWidget).join(Dashboard).filter(
                DashboardWidget.id == widget_id,
                Dashboard.user_id == user_id
            ).first()
            
            if not widget:
                return None
            
            update_data = widget_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'config' and value:
                    setattr(widget, field, value.dict() if hasattr(value, 'dict') else value)
                elif field == 'position' and value:
                    setattr(widget, field, value.dict() if hasattr(value, 'dict') else value)
                else:
                    setattr(widget, field, value)
            
            widget.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(widget)
            
            logger.info(f"Updated widget {widget_id}")
            return widget
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating widget {widget_id}: {e}")
            raise
    
    async def delete_widget(self, db: Session, widget_id: int, user_id: int) -> bool:
        """Удаление виджета"""
        try:
            widget = db.query(DashboardWidget).join(Dashboard).filter(
                DashboardWidget.id == widget_id,
                Dashboard.user_id == user_id
            ).first()
            
            if not widget:
                return False
            
            db.delete(widget)
            db.commit()
            
            logger.info(f"Deleted widget {widget_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting widget {widget_id}: {e}")
            raise
    
    # Data retrieval for widgets
    async def get_widget_data(self, db: Session, widget: DashboardWidget) -> WidgetData:
        """Получение данных для виджета"""
        try:
            data_source = widget.data_source
            config = widget.config
            
            if data_source == "users":
                return await self._get_users_data(db, config)
            elif data_source == "queries":
                return await self._get_queries_data(db, config)
            elif data_source == "moderation":
                return await self._get_moderation_data(db, config)
            elif data_source == "system_metrics":
                return await self._get_system_metrics_data(db, config)
            else:
                return WidgetData(labels=[], datasets=[])
                
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return WidgetData(labels=[], datasets=[])
    
    async def _get_users_data(self, db: Session, config: Dict[str, Any]) -> WidgetData:
        """Получение данных пользователей"""
        try:
            time_range = config.get('time_range', '24h')
            aggregation = config.get('aggregation', 'count')
            filters = config.get('filters', {})
            group_by = config.get('group_by')
            
            # Базовый запрос
            query = db.query(User)
            
            # Применяем фильтры времени
            if time_range:
                start_time = self._parse_time_range(time_range)
                query = query.filter(User.created_at >= start_time)
            
            # Применяем дополнительные фильтры
            for field, value in filters.items():
                if hasattr(User, field):
                    query = query.filter(getattr(User, field) == value)
            
            if group_by == 'hour':
                # Группировка по часам
                results = query.all()
                hourly_data = {}
                for user in results:
                    hour = user.created_at.strftime('%H:00')
                    hourly_data[hour] = hourly_data.get(hour, 0) + 1
                
                return WidgetData(
                    labels=list(hourly_data.keys()),
                    datasets=[{
                        'label': 'Пользователи',
                        'data': list(hourly_data.values()),
                        'backgroundColor': 'rgba(59, 130, 246, 0.5)',
                        'borderColor': 'rgb(59, 130, 246)'
                    }]
                )
            else:
                # Простой подсчет
                count = query.count()
                return WidgetData(
                    labels=['Всего'],
                    datasets=[{
                        'label': 'Пользователи',
                        'data': [count],
                        'backgroundColor': 'rgba(59, 130, 246, 0.5)'
                    }]
                )
                
        except Exception as e:
            logger.error(f"Error getting users data: {e}")
            return WidgetData(labels=[], datasets=[])
    
    async def _get_queries_data(self, db: Session, config: Dict[str, Any]) -> WidgetData:
        """Получение данных запросов (заглушка)"""
        # Здесь должна быть логика получения данных из таблицы запросов
        # Пока возвращаем тестовые данные
        return WidgetData(
            labels=['00:00', '06:00', '12:00', '18:00'],
            datasets=[{
                'label': 'Запросы',
                'data': [45, 78, 123, 89],
                'backgroundColor': 'rgba(16, 185, 129, 0.5)',
                'borderColor': 'rgb(16, 185, 129)'
            }]
        )
    
    async def _get_moderation_data(self, db: Session, config: Dict[str, Any]) -> WidgetData:
        """Получение данных модерации (заглушка)"""
        return WidgetData(
            labels=['Отлично', 'Хорошо', 'Удовлетворительно', 'Плохо'],
            datasets=[{
                'label': 'Оценки',
                'data': [65, 25, 8, 2],
                'backgroundColor': [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        )
    
    async def _get_system_metrics_data(self, db: Session, config: Dict[str, Any]) -> WidgetData:
        """Получение системных метрик (заглушка)"""
        return WidgetData(
            labels=['CPU', 'Memory', 'Disk', 'Network'],
            datasets=[{
                'label': 'Использование (%)',
                'data': [45, 67, 23, 34],
                'backgroundColor': 'rgba(139, 92, 246, 0.5)',
                'borderColor': 'rgb(139, 92, 246)'
            }]
        )
    
    def _parse_time_range(self, time_range: str) -> datetime:
        """Парсинг временного диапазона"""
        now = datetime.utcnow()
        
        if time_range == '1h':
            return now - timedelta(hours=1)
        elif time_range == '24h':
            return now - timedelta(hours=24)
        elif time_range == '7d':
            return now - timedelta(days=7)
        elif time_range == '30d':
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)
    
    def get_data_sources(self) -> List[DataSourceInfo]:
        """Получение списка источников данных"""
        return self.data_sources
    
    def get_widget_templates(self) -> List[Dict[str, Any]]:
        """Получение шаблонов виджетов"""
        return self.widget_templates


# Глобальный экземпляр сервиса
analytics_service = AnalyticsService()