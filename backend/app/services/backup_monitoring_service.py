"""
Сервис мониторинга системы резервного копирования
"""

import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db, SessionLocal
try:
    from ..models.backup import BackupRecord, BackupSchedule, BackupIntegrityCheck, RestoreRecord
    from ..models.backup import BackupStatus, BackupType
    BACKUP_MODELS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Backup models not available - backup monitoring will be limited")
    BACKUP_MODELS_AVAILABLE = False

try:
    from ..services.notification_service import notification_service
    NOTIFICATION_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Notification service not available")
    NOTIFICATION_SERVICE_AVAILABLE = False

try:
    from ..services.backup_service import backup_service
    BACKUP_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Backup service not available")
    BACKUP_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)


class BackupMonitoringService:
    """Сервис мониторинга резервного копирования"""
    
    def __init__(self):
        self.monitoring_interval = 300  # 5 минут
        self.alert_thresholds = {
            'max_backup_age_hours': 24,  # Максимальный возраст последней резервной копии
            'max_failed_backups': 3,     # Максимальное количество неудачных резервных копий подряд
            'min_success_rate': 0.8,     # Минимальный процент успешных резервных копий
            'max_backup_duration_hours': 2,  # Максимальная длительность резервного копирования
            'min_integrity_check_age_days': 7,  # Максимальный возраст последней проверки целостности
        }
        self.is_monitoring = False
    
    async def start_monitoring(self):
        """Запускает мониторинг резервного копирования"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        logger.info("🔍 Запуск мониторинга системы резервного копирования")
        
        while self.is_monitoring:
            try:
                await self._perform_monitoring_check()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга резервного копирования: {e}")
                await asyncio.sleep(60)  # Короткая пауза при ошибке
    
    async def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.is_monitoring = False
        logger.info("⏹️ Остановка мониторинга системы резервного копирования")
    
    async def _perform_monitoring_check(self):
        """Выполняет проверку состояния системы резервного копирования"""
        try:
            # Получаем метрики системы
            metrics = await self.get_system_metrics()
            
            # Проверяем пороговые значения и отправляем алерты
            alerts = await self._check_alert_conditions(metrics)
            
            # Отправляем алерты
            for alert in alerts:
                await self._send_alert(alert)
            
            # Логируем состояние системы
            if alerts:
                logger.warning(f"⚠️ Обнаружено {len(alerts)} проблем в системе резервного копирования")
            else:
                logger.debug("✅ Система резервного копирования работает нормально")
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки мониторинга: {e}")
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Получает метрики системы резервного копирования"""
        if not BACKUP_MODELS_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "Backup models not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            with SessionLocal() as db:
                now = datetime.utcnow()
                
                # Основные метрики
                total_backups = db.query(BackupRecord).count()
                successful_backups = db.query(BackupRecord).filter(BackupRecord.success == True).count()
                failed_backups = db.query(BackupRecord).filter(BackupRecord.success == False).count()
            
            # Последняя успешная резервная копия
            last_successful_backup = db.query(BackupRecord).filter(
                BackupRecord.success == True
            ).order_by(BackupRecord.completed_at.desc()).first()
            
            # Резервные копии за последние 24 часа
            yesterday = now - timedelta(days=1)
            recent_backups = db.query(BackupRecord).filter(
                BackupRecord.created_at >= yesterday
            ).all()
            
            recent_successful = len([b for b in recent_backups if b.success])
            recent_failed = len([b for b in recent_backups if not b.success])
            
            # Активные расписания
            active_schedules = db.query(BackupSchedule).filter(
                BackupSchedule.enabled == True
            ).count()
            
            # Просроченные расписания
            overdue_schedules = db.query(BackupSchedule).filter(
                BackupSchedule.enabled == True,
                BackupSchedule.next_run_at < now
            ).count()
            
            # Средняя длительность резервного копирования
            avg_duration = db.query(func.avg(BackupRecord.duration_seconds)).filter(
                BackupRecord.success == True,
                BackupRecord.duration_seconds.isnot(None),
                BackupRecord.created_at >= now - timedelta(days=7)
            ).scalar()
            
            # Общий размер резервных копий
            total_size = db.query(func.sum(BackupRecord.total_size)).filter(
                BackupRecord.success == True
            ).scalar() or 0
            
            # Последние проверки целостности
            last_integrity_check = db.query(BackupIntegrityCheck).order_by(
                BackupIntegrityCheck.checked_at.desc()
            ).first()
            
            # Неудачные проверки целостности
            failed_integrity_checks = db.query(BackupIntegrityCheck).filter(
                BackupIntegrityCheck.passed == False,
                BackupIntegrityCheck.checked_at >= now - timedelta(days=7)
            ).count()
            
            # Операции восстановления
            total_restores = db.query(RestoreRecord).count()
            successful_restores = db.query(RestoreRecord).filter(
                RestoreRecord.success == True
            ).count()
            
            # Последние неудачные резервные копии подряд
            consecutive_failures = 0
            recent_backups_ordered = db.query(BackupRecord).order_by(
                BackupRecord.created_at.desc()
            ).limit(10).all()
            
            for backup in recent_backups_ordered:
                if not backup.success:
                    consecutive_failures += 1
                else:
                    break
            
            return {
                'timestamp': now.isoformat(),
                'total_backups': total_backups,
                'successful_backups': successful_backups,
                'failed_backups': failed_backups,
                'success_rate': successful_backups / total_backups if total_backups > 0 else 0,
                'last_successful_backup': last_successful_backup.completed_at if last_successful_backup else None,
                'last_successful_backup_age_hours': (
                    (now - last_successful_backup.completed_at).total_seconds() / 3600
                    if last_successful_backup and last_successful_backup.completed_at else None
                ),
                'recent_backups_24h': len(recent_backups),
                'recent_successful_24h': recent_successful,
                'recent_failed_24h': recent_failed,
                'active_schedules': active_schedules,
                'overdue_schedules': overdue_schedules,
                'average_duration_seconds': float(avg_duration) if avg_duration else None,
                'total_size_bytes': total_size,
                'last_integrity_check': last_integrity_check.checked_at if last_integrity_check else None,
                'last_integrity_check_age_days': (
                    (now - last_integrity_check.checked_at).days
                    if last_integrity_check else None
                ),
                'failed_integrity_checks_7d': failed_integrity_checks,
                'total_restores': total_restores,
                'successful_restores': successful_restores,
                'consecutive_failures': consecutive_failures,
                'storage_usage': await self._get_storage_usage(),
                'system_health': await self._assess_system_health()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting backup system metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "database_available": False
            }
    
    async def _check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Проверяет условия для отправки алертов"""
        alerts = []
        
        # Проверка возраста последней резервной копии
        if metrics['last_successful_backup_age_hours']:
            if metrics['last_successful_backup_age_hours'] > self.alert_thresholds['max_backup_age_hours']:
                alerts.append({
                    'type': 'backup_age',
                    'severity': 'high',
                    'title': 'Устаревшая резервная копия',
                    'message': f"Последняя успешная резервная копия создана {metrics['last_successful_backup_age_hours']:.1f} часов назад",
                    'threshold': self.alert_thresholds['max_backup_age_hours'],
                    'current_value': metrics['last_successful_backup_age_hours']
                })
        
        # Проверка количества неудачных резервных копий подряд
        if metrics['consecutive_failures'] >= self.alert_thresholds['max_failed_backups']:
            alerts.append({
                'type': 'consecutive_failures',
                'severity': 'high',
                'title': 'Множественные неудачи резервного копирования',
                'message': f"Последние {metrics['consecutive_failures']} резервных копий завершились неудачей",
                'threshold': self.alert_thresholds['max_failed_backups'],
                'current_value': metrics['consecutive_failures']
            })
        
        # Проверка общего процента успешности
        if metrics['success_rate'] < self.alert_thresholds['min_success_rate']:
            alerts.append({
                'type': 'low_success_rate',
                'severity': 'medium',
                'title': 'Низкий процент успешных резервных копий',
                'message': f"Процент успешных резервных копий: {metrics['success_rate']*100:.1f}%",
                'threshold': self.alert_thresholds['min_success_rate'] * 100,
                'current_value': metrics['success_rate'] * 100
            })
        
        # Проверка длительности резервного копирования
        if metrics['average_duration_seconds']:
            duration_hours = metrics['average_duration_seconds'] / 3600
            if duration_hours > self.alert_thresholds['max_backup_duration_hours']:
                alerts.append({
                    'type': 'long_backup_duration',
                    'severity': 'medium',
                    'title': 'Долгое время резервного копирования',
                    'message': f"Среднее время резервного копирования: {duration_hours:.1f} часов",
                    'threshold': self.alert_thresholds['max_backup_duration_hours'],
                    'current_value': duration_hours
                })
        
        # Проверка просроченных расписаний
        if metrics['overdue_schedules'] > 0:
            alerts.append({
                'type': 'overdue_schedules',
                'severity': 'medium',
                'title': 'Просроченные расписания резервного копирования',
                'message': f"Количество просроченных расписаний: {metrics['overdue_schedules']}",
                'threshold': 0,
                'current_value': metrics['overdue_schedules']
            })
        
        # Проверка возраста последней проверки целостности
        if metrics['last_integrity_check_age_days']:
            if metrics['last_integrity_check_age_days'] > self.alert_thresholds['min_integrity_check_age_days']:
                alerts.append({
                    'type': 'old_integrity_check',
                    'severity': 'low',
                    'title': 'Устаревшая проверка целостности',
                    'message': f"Последняя проверка целостности выполнена {metrics['last_integrity_check_age_days']} дней назад",
                    'threshold': self.alert_thresholds['min_integrity_check_age_days'],
                    'current_value': metrics['last_integrity_check_age_days']
                })
        
        # Проверка неудачных проверок целостности
        if metrics['failed_integrity_checks_7d'] > 0:
            alerts.append({
                'type': 'failed_integrity_checks',
                'severity': 'high',
                'title': 'Неудачные проверки целостности',
                'message': f"За последние 7 дней неудачных проверок целостности: {metrics['failed_integrity_checks_7d']}",
                'threshold': 0,
                'current_value': metrics['failed_integrity_checks_7d']
            })
        
        # Проверка использования хранилища
        storage_usage = metrics.get('storage_usage', {})
        if storage_usage.get('usage_percent', 0) > 90:
            alerts.append({
                'type': 'high_storage_usage',
                'severity': 'high',
                'title': 'Высокое использование хранилища',
                'message': f"Использование хранилища: {storage_usage['usage_percent']:.1f}%",
                'threshold': 90,
                'current_value': storage_usage['usage_percent']
            })
        
        return alerts
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Отправляет алерт через систему уведомлений"""
        try:
            if not NOTIFICATION_SERVICE_AVAILABLE:
                logger.warning(f"🚨 Алерт резервного копирования (notification service unavailable): {alert['title']} - {alert['message']}")
                return
            
            severity_colors = {
                'low': 'info',
                'medium': 'warning', 
                'high': 'error'
            }
            
            await notification_service.create_system_notification(
                title=f"🚨 {alert['title']}",
                message=alert['message'],
                notification_type=severity_colors.get(alert['severity'], 'warning'),
                metadata={
                    'alert_type': alert['type'],
                    'severity': alert['severity'],
                    'threshold': alert['threshold'],
                    'current_value': alert['current_value'],
                    'component': 'backup_system'
                }
            )
            
            logger.warning(f"🚨 Алерт резервного копирования: {alert['title']} - {alert['message']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки алерта: {e}")
    
    async def _get_storage_usage(self) -> Dict[str, Any]:
        """Получает информацию об использовании хранилища"""
        try:
            import shutil
            
            # Проверяем использование диска для директории резервных копий
            if not BACKUP_SERVICE_AVAILABLE:
                backup_dir = "/tmp/backups"  # Fallback directory
            else:
                backup_dir = backup_service.backup_dir
            
            if os.path.exists(backup_dir):
                total, used, free = shutil.disk_usage(backup_dir)
                
                # Размер директории резервных копий
                backup_dir_size = 0
                for dirpath, dirnames, filenames in os.walk(backup_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            backup_dir_size += os.path.getsize(filepath)
                        except (OSError, IOError):
                            continue
                
                return {
                    'total_bytes': total,
                    'used_bytes': used,
                    'free_bytes': free,
                    'backup_dir_size_bytes': backup_dir_size,
                    'usage_percent': (used / total) * 100,
                    'backup_usage_percent': (backup_dir_size / total) * 100 if total > 0 else 0
                }
            else:
                return {
                    'total_bytes': 0,
                    'used_bytes': 0,
                    'free_bytes': 0,
                    'backup_dir_size_bytes': 0,
                    'usage_percent': 0,
                    'backup_usage_percent': 0
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о хранилище: {e}")
            return {
                'total_bytes': 0,
                'used_bytes': 0,
                'free_bytes': 0,
                'backup_dir_size_bytes': 0,
                'usage_percent': 0,
                'backup_usage_percent': 0
            }
    
    async def _assess_system_health(self) -> Dict[str, Any]:
        """Оценивает общее состояние системы резервного копирования"""
        try:
            # Проверяем доступность директории резервных копий
            if BACKUP_SERVICE_AVAILABLE:
                backup_dir_accessible = os.path.exists(backup_service.backup_dir) and os.access(backup_service.backup_dir, os.W_OK)
                backup_dir = backup_service.backup_dir
            else:
                backup_dir_accessible = False
                backup_dir = "unavailable"
            
            # Проверяем наличие активных расписаний
            active_schedules_count = 0
            if BACKUP_MODELS_AVAILABLE:
                try:
                    with SessionLocal() as db:
                        active_schedules_count = db.query(BackupSchedule).filter(
                            BackupSchedule.enabled == True
                        ).count()
                except Exception as e:
                    logger.warning(f"⚠️ Could not check backup schedules: {e}")
                    active_schedules_count = 0
            
            # Определяем общее состояние
            issues = []
            if not backup_dir_accessible:
                issues.append("Директория резервных копий недоступна")
            
            if active_schedules_count == 0:
                issues.append("Нет активных расписаний резервного копирования")
            
            # Оценка состояния
            if len(issues) == 0:
                health_status = "healthy"
                health_score = 100
            elif len(issues) == 1:
                health_status = "warning"
                health_score = 70
            else:
                health_status = "critical"
                health_score = 30
            
            return {
                'status': health_status,
                'score': health_score,
                'issues': issues,
                'backup_dir_accessible': backup_dir_accessible,
                'active_schedules_count': active_schedules_count,
                'last_assessment': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка оценки состояния системы: {e}")
            return {
                'status': 'unknown',
                'score': 0,
                'issues': [f"Ошибка оценки: {str(e)}"],
                'backup_dir_accessible': False,
                'active_schedules_count': 0,
                'last_assessment': datetime.utcnow().isoformat()
            }
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """Генерирует подробный отчет о состоянии системы"""
        try:
            metrics = await self.get_system_metrics()
            alerts = await self._check_alert_conditions(metrics)
            
            # Рекомендации по улучшению
            recommendations = []
            
            if metrics['success_rate'] < 0.9:
                recommendations.append("Рассмотрите возможность улучшения надежности резервного копирования")
            
            if not metrics['last_integrity_check'] or metrics['last_integrity_check_age_days'] > 7:
                recommendations.append("Настройте регулярные проверки целостности резервных копий")
            
            if metrics['active_schedules'] == 0:
                recommendations.append("Настройте автоматическое резервное копирование по расписанию")
            
            if metrics.get('storage_usage', {}).get('usage_percent', 0) > 80:
                recommendations.append("Рассмотрите возможность очистки старых резервных копий или увеличения хранилища")
            
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'metrics': metrics,
                'alerts': alerts,
                'recommendations': recommendations,
                'summary': {
                    'total_issues': len(alerts),
                    'critical_issues': len([a for a in alerts if a['severity'] == 'high']),
                    'warning_issues': len([a for a in alerts if a['severity'] == 'medium']),
                    'info_issues': len([a for a in alerts if a['severity'] == 'low']),
                    'overall_health': metrics['system_health']['status'],
                    'health_score': metrics['system_health']['score']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета о состоянии: {e}")
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'error': str(e),
                'metrics': {},
                'alerts': [],
                'recommendations': [],
                'summary': {
                    'total_issues': 0,
                    'critical_issues': 0,
                    'warning_issues': 0,
                    'info_issues': 0,
                    'overall_health': 'unknown',
                    'health_score': 0
                }
            }


# Создаем глобальный экземпляр
backup_monitoring_service = BackupMonitoringService()