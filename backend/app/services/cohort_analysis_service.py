"""
Сервис когортного анализа пользователей
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, extract
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict
import pandas as pd
import numpy as np

from ..models.analytics import CohortAnalysis, UserSegment
from ..models.user import User
from ..schemas.analytics import CohortAnalysisCreate, UserSegmentCreate, UserSegmentUpdate
from ..core.database import get_db

logger = logging.getLogger(__name__)


class CohortAnalysisService:
    """Сервис когортного анализа"""
    
    def __init__(self):
        self.cohort_types = {
            'registration': 'Регистрация',
            'first_purchase': 'Первая покупка',
            'first_query': 'Первый запрос',
            'subscription': 'Подписка'
        }
        
        self.period_types = {
            'daily': 'Ежедневно',
            'weekly': 'Еженедельно',
            'monthly': 'Ежемесячно'
        }
    
    async def create_cohort_analysis(self, db: Session, cohort_data: CohortAnalysisCreate, user_id: int) -> CohortAnalysis:
        """Создание когортного анализа"""
        try:
            # Вычисляем данные когорт
            cohort_results = await self._calculate_cohort_data(
                db, 
                cohort_data.cohort_type,
                cohort_data.period_type,
                cohort_data.start_date,
                cohort_data.end_date
            )
            
            cohort_analysis = CohortAnalysis(
                name=cohort_data.name,
                cohort_type=cohort_data.cohort_type,
                period_type=cohort_data.period_type,
                start_date=cohort_data.start_date,
                end_date=cohort_data.end_date,
                data=cohort_results,
                user_id=user_id
            )
            
            db.add(cohort_analysis)
            db.commit()
            db.refresh(cohort_analysis)
            
            logger.info(f"Created cohort analysis {cohort_analysis.id} for user {user_id}")
            return cohort_analysis
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating cohort analysis: {e}")
            raise
    
    async def get_cohort_analyses(self, db: Session, user_id: int) -> List[CohortAnalysis]:
        """Получение списка когортных анализов пользователя"""
        try:
            analyses = db.query(CohortAnalysis).filter(
                CohortAnalysis.user_id == user_id
            ).order_by(desc(CohortAnalysis.created_at)).all()
            
            return analyses
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting cohort analyses: {e}")
            raise
    
    async def get_cohort_analysis(self, db: Session, analysis_id: int, user_id: int) -> Optional[CohortAnalysis]:
        """Получение когортного анализа по ID"""
        try:
            analysis = db.query(CohortAnalysis).filter(
                CohortAnalysis.id == analysis_id,
                CohortAnalysis.user_id == user_id
            ).first()
            
            return analysis
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting cohort analysis {analysis_id}: {e}")
            raise
    
    async def update_cohort_analysis(self, db: Session, analysis_id: int, user_id: int) -> Optional[CohortAnalysis]:
        """Обновление данных когортного анализа"""
        try:
            analysis = await self.get_cohort_analysis(db, analysis_id, user_id)
            if not analysis:
                return None
            
            # Пересчитываем данные когорт
            cohort_results = await self._calculate_cohort_data(
                db,
                analysis.cohort_type,
                analysis.period_type,
                analysis.start_date,
                analysis.end_date
            )
            
            analysis.data = cohort_results
            analysis.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(analysis)
            
            logger.info(f"Updated cohort analysis {analysis_id}")
            return analysis
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating cohort analysis {analysis_id}: {e}")
            raise
    
    async def delete_cohort_analysis(self, db: Session, analysis_id: int, user_id: int) -> bool:
        """Удаление когортного анализа"""
        try:
            analysis = await self.get_cohort_analysis(db, analysis_id, user_id)
            if not analysis:
                return False
            
            db.delete(analysis)
            db.commit()
            
            logger.info(f"Deleted cohort analysis {analysis_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting cohort analysis {analysis_id}: {e}")
            raise
    
    async def _calculate_cohort_data(self, db: Session, cohort_type: str, period_type: str, 
                                   start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Вычисление данных когорт"""
        try:
            if cohort_type == 'registration':
                return await self._calculate_registration_cohorts(db, period_type, start_date, end_date)
            elif cohort_type == 'first_query':
                return await self._calculate_query_cohorts(db, period_type, start_date, end_date)
            elif cohort_type == 'subscription':
                return await self._calculate_subscription_cohorts(db, period_type, start_date, end_date)
            else:
                # Базовый анализ регистрации
                return await self._calculate_registration_cohorts(db, period_type, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error calculating cohort data: {e}")
            raise
    
    async def _calculate_registration_cohorts(self, db: Session, period_type: str, 
                                            start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Вычисление когорт по регистрации"""
        try:
            # Получаем всех пользователей в указанном диапазоне
            users_query = db.query(User).filter(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                )
            )
            
            users = users_query.all()
            
            if not users:
                return {
                    'cohorts': [],
                    'periods': [],
                    'retention_matrix': [],
                    'summary': {
                        'total_users': 0,
                        'total_cohorts': 0,
                        'avg_retention': 0
                    }
                }
            
            # Группируем пользователей по когортам
            cohorts = self._group_users_by_period(users, period_type, 'created_at')
            
            # Вычисляем retention для каждой когорты
            retention_data = await self._calculate_retention_matrix(db, cohorts, period_type)
            
            return {
                'cohorts': list(cohorts.keys()),
                'periods': retention_data['periods'],
                'retention_matrix': retention_data['matrix'],
                'cohort_sizes': retention_data['sizes'],
                'summary': {
                    'total_users': len(users),
                    'total_cohorts': len(cohorts),
                    'avg_retention': retention_data['avg_retention']
                },
                'cohort_type': 'registration',
                'period_type': period_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating registration cohorts: {e}")
            raise
    
    async def _calculate_query_cohorts(self, db: Session, period_type: str, 
                                     start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Вычисление когорт по первому запросу (заглушка)"""
        # Здесь должна быть логика анализа первых запросов пользователей
        # Пока возвращаем тестовые данные
        return {
            'cohorts': ['2024-01', '2024-02', '2024-03'],
            'periods': ['Period 0', 'Period 1', 'Period 2', 'Period 3'],
            'retention_matrix': [
                [100, 85, 70, 60],  # Когорта 2024-01
                [100, 80, 65, 55],  # Когорта 2024-02
                [100, 90, 75, 0]    # Когорта 2024-03 (неполные данные)
            ],
            'cohort_sizes': [150, 200, 180],
            'summary': {
                'total_users': 530,
                'total_cohorts': 3,
                'avg_retention': 68.5
            },
            'cohort_type': 'first_query',
            'period_type': period_type
        }
    
    async def _calculate_subscription_cohorts(self, db: Session, period_type: str, 
                                            start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Вычисление когорт по подпискам (заглушка)"""
        # Здесь должна быть логика анализа подписок
        # Пока возвращаем тестовые данные
        return {
            'cohorts': ['2024-01', '2024-02', '2024-03'],
            'periods': ['Period 0', 'Period 1', 'Period 2', 'Period 3'],
            'retention_matrix': [
                [100, 95, 85, 80],  # Когорта 2024-01
                [100, 90, 80, 75],  # Когорта 2024-02
                [100, 92, 88, 0]    # Когорта 2024-03 (неполные данные)
            ],
            'cohort_sizes': [50, 75, 60],
            'summary': {
                'total_users': 185,
                'total_cohorts': 3,
                'avg_retention': 83.2
            },
            'cohort_type': 'subscription',
            'period_type': period_type
        }
    
    def _group_users_by_period(self, users: List[User], period_type: str, date_field: str) -> Dict[str, List[User]]:
        """Группировка пользователей по периодам"""
        cohorts = defaultdict(list)
        
        for user in users:
            date_value = getattr(user, date_field)
            if not date_value:
                continue
            
            if period_type == 'daily':
                period_key = date_value.strftime('%Y-%m-%d')
            elif period_type == 'weekly':
                # Начало недели (понедельник)
                start_of_week = date_value - timedelta(days=date_value.weekday())
                period_key = start_of_week.strftime('%Y-W%U')
            elif period_type == 'monthly':
                period_key = date_value.strftime('%Y-%m')
            else:
                period_key = date_value.strftime('%Y-%m')
            
            cohorts[period_key].append(user)
        
        return dict(cohorts)
    
    async def _calculate_retention_matrix(self, db: Session, cohorts: Dict[str, List[User]], 
                                        period_type: str) -> Dict[str, Any]:
        """Вычисление матрицы retention"""
        try:
            # Определяем количество периодов для анализа
            max_periods = 12 if period_type == 'monthly' else 8
            
            periods = [f"Period {i}" for i in range(max_periods)]
            matrix = []
            sizes = []
            
            for cohort_name, cohort_users in cohorts.items():
                cohort_size = len(cohort_users)
                sizes.append(cohort_size)
                
                retention_row = []
                
                for period_idx in range(max_periods):
                    if period_idx == 0:
                        # Первый период всегда 100%
                        retention_row.append(100.0)
                    else:
                        # Для упрощения используем убывающую функцию
                        # В реальной реализации здесь должен быть запрос к БД
                        # для подсчета активных пользователей в каждом периоде
                        retention_rate = max(0, 100 - (period_idx * 15) + np.random.normal(0, 5))
                        retention_row.append(round(retention_rate, 1))
                
                matrix.append(retention_row)
            
            # Вычисляем средний retention
            if matrix:
                avg_retention = np.mean([row[1] if len(row) > 1 else 0 for row in matrix])
            else:
                avg_retention = 0
            
            return {
                'periods': periods,
                'matrix': matrix,
                'sizes': sizes,
                'avg_retention': round(avg_retention, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating retention matrix: {e}")
            raise
    
    # User Segmentation Methods
    async def create_user_segment(self, db: Session, segment_data: UserSegmentCreate, user_id: int) -> UserSegment:
        """Создание сегмента пользователей"""
        try:
            # Вычисляем количество пользователей в сегменте
            user_count = await self._calculate_segment_size(db, segment_data.criteria)
            
            segment = UserSegment(
                name=segment_data.name,
                description=segment_data.description,
                criteria=segment_data.criteria,
                user_count=user_count,
                is_dynamic=segment_data.is_dynamic,
                user_id=user_id
            )
            
            db.add(segment)
            db.commit()
            db.refresh(segment)
            
            logger.info(f"Created user segment {segment.id} with {user_count} users")
            return segment
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating user segment: {e}")
            raise
    
    async def get_user_segments(self, db: Session, user_id: int) -> List[UserSegment]:
        """Получение сегментов пользователей"""
        try:
            segments = db.query(UserSegment).filter(
                UserSegment.user_id == user_id
            ).order_by(desc(UserSegment.created_at)).all()
            
            return segments
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user segments: {e}")
            raise
    
    async def update_user_segment(self, db: Session, segment_id: int, segment_data: UserSegmentUpdate, user_id: int) -> Optional[UserSegment]:
        """Обновление сегмента пользователей"""
        try:
            segment = db.query(UserSegment).filter(
                UserSegment.id == segment_id,
                UserSegment.user_id == user_id
            ).first()
            
            if not segment:
                return None
            
            update_data = segment_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(segment, field, value)
            
            # Пересчитываем размер сегмента если изменились критерии
            if 'criteria' in update_data:
                segment.user_count = await self._calculate_segment_size(db, segment.criteria)
            
            segment.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(segment)
            
            logger.info(f"Updated user segment {segment_id}")
            return segment
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating user segment {segment_id}: {e}")
            raise
    
    async def delete_user_segment(self, db: Session, segment_id: int, user_id: int) -> bool:
        """Удаление сегмента пользователей"""
        try:
            segment = db.query(UserSegment).filter(
                UserSegment.id == segment_id,
                UserSegment.user_id == user_id
            ).first()
            
            if not segment:
                return False
            
            db.delete(segment)
            db.commit()
            
            logger.info(f"Deleted user segment {segment_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting user segment {segment_id}: {e}")
            raise
    
    async def get_segment_users(self, db: Session, segment_id: int, user_id: int, 
                              limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Получение пользователей сегмента"""
        try:
            segment = db.query(UserSegment).filter(
                UserSegment.id == segment_id,
                UserSegment.user_id == user_id
            ).first()
            
            if not segment:
                return {'users': [], 'total': 0}
            
            # Применяем критерии сегментации
            query = db.query(User)
            query = self._apply_segment_criteria(query, segment.criteria)
            
            total = query.count()
            users = query.offset(offset).limit(limit).all()
            
            return {
                'users': [
                    {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'created_at': user.created_at,
                        'is_active': user.is_active,
                        'is_premium': user.is_premium,
                        'subscription_type': user.subscription_type
                    }
                    for user in users
                ],
                'total': total,
                'segment_name': segment.name
            }
            
        except Exception as e:
            logger.error(f"Error getting segment users: {e}")
            raise
    
    async def _calculate_segment_size(self, db: Session, criteria: List[Dict[str, Any]]) -> int:
        """Вычисление размера сегмента"""
        try:
            query = db.query(User)
            query = self._apply_segment_criteria(query, criteria)
            return query.count()
            
        except Exception as e:
            logger.error(f"Error calculating segment size: {e}")
            return 0
    
    def _apply_segment_criteria(self, query, criteria: List[Dict[str, Any]]):
        """Применение критериев сегментации к запросу"""
        try:
            for criterion in criteria:
                field = criterion.get('field')
                operator = criterion.get('operator')
                value = criterion.get('value')
                
                if not all([field, operator]) or not hasattr(User, field):
                    continue
                
                column = getattr(User, field)
                
                if operator == 'eq':
                    query = query.filter(column == value)
                elif operator == 'ne':
                    query = query.filter(column != value)
                elif operator == 'gt':
                    query = query.filter(column > value)
                elif operator == 'lt':
                    query = query.filter(column < value)
                elif operator == 'gte':
                    query = query.filter(column >= value)
                elif operator == 'lte':
                    query = query.filter(column <= value)
                elif operator == 'in' and isinstance(value, list):
                    query = query.filter(column.in_(value))
                elif operator == 'not_in' and isinstance(value, list):
                    query = query.filter(~column.in_(value))
                elif operator == 'contains' and isinstance(value, str):
                    query = query.filter(column.contains(value))
            
            return query
            
        except Exception as e:
            logger.error(f"Error applying segment criteria: {e}")
            return query
    
    def get_available_cohort_types(self) -> Dict[str, str]:
        """Получение доступных типов когорт"""
        return self.cohort_types
    
    def get_available_period_types(self) -> Dict[str, str]:
        """Получение доступных типов периодов"""
        return self.period_types


# Глобальный экземпляр сервиса
cohort_analysis_service = CohortAnalysisService()