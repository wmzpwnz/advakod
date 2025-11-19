"""
API для системы резервного копирования
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os
import shutil

from ..core.database import get_db
from ..core.security import get_current_user, get_current_admin_user
from ..models.user import User
from ..models.backup import BackupRecord, BackupSchedule, RestoreRecord, BackupIntegrityCheck
from ..models.backup import BackupStatus, BackupType, RestoreStatus
from ..schemas.backup import (
    BackupCreate, BackupRecordResponse, BackupScheduleCreate, BackupScheduleResponse,
    BackupScheduleUpdate, RestoreCreate, RestoreRecordResponse, BackupIntegrityCheckResponse,
    BackupStats, BackupSystemStatus, BackupListResponse, BackupPreview, BackupValidationResult
)
# from ..services.backup_service import backup_service  # Temporarily disabled - missing croniter

router = APIRouter(prefix="/backup", tags=["backup"])


async def require_permissions(user: User, required_permissions: List[str]):
    """Проверяет права доступа пользователя"""
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не аутентифицирован")
    
    # Проверяем, является ли пользователь администратором
    if not hasattr(user, 'is_admin') or not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен: требуются права администратора")
    
    # TODO: Реализовать детальную проверку прав доступа на основе RBAC
    # Пока что разрешаем доступ всем администраторам
    return True


@router.post("/create", response_model=dict)
async def create_backup(
    backup_data: BackupCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создает новую резервную копию"""
    # Проверяем права доступа
    await require_permissions(current_user, ["backup:create"])
    
    try:
        # Запускаем создание резервной копии в фоне
        result = await backup_service.create_backup_with_record(
            name=backup_data.name,
            components=backup_data.components,
            description=backup_data.description,
            tags=backup_data.tags,
            created_by=current_user.id,
            backup_type=BackupType.MANUAL,
            compression_enabled=backup_data.compression_enabled,
            encryption_enabled=backup_data.encryption_enabled,
            retention_days=backup_data.retention_days
        )
        
        return {
            "message": "Резервная копия создается",
            "backup_id": result["backup_id"],
            "status": "in_progress"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания резервной копии: {str(e)}")


@router.get("/list", response_model=BackupListResponse)
async def list_backups(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[BackupStatus] = None,
    backup_type: Optional[BackupType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает список резервных копий"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        query = db.query(BackupRecord)
        
        # Фильтрация
        if status:
            query = query.filter(BackupRecord.status == status)
        if backup_type:
            query = query.filter(BackupRecord.backup_type == backup_type)
        
        # Подсчет общего количества
        total = query.count()
        
        # Пагинация
        offset = (page - 1) * size
        backups = query.order_by(BackupRecord.created_at.desc()).offset(offset).limit(size).all()
        
        return BackupListResponse(
            backups=[BackupRecordResponse.from_orm(backup) for backup in backups],
            total=total,
            page=page,
            size=size,
            has_next=offset + size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка резервных копий: {str(e)}")


@router.get("/{backup_id}", response_model=BackupRecordResponse)
async def get_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает информацию о резервной копии"""
    await require_permissions(current_user, ["backup:read"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    return BackupRecordResponse.from_orm(backup)


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаляет резервную копию"""
    await require_permissions(current_user, ["backup:delete"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    try:
        # Удаляем файлы резервной копии
        if backup.backup_path and os.path.exists(backup.backup_path):
            if os.path.isdir(backup.backup_path):
                shutil.rmtree(backup.backup_path)
            else:
                os.remove(backup.backup_path)
        
        # Удаляем запись из БД
        db.delete(backup)
        db.commit()
        
        return {"message": "Резервная копия удалена"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления резервной копии: {str(e)}")


@router.post("/{backup_id}/restore", response_model=dict)
async def restore_backup(
    backup_id: int,
    restore_data: RestoreCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Восстанавливает данные из резервной копии"""
    await require_permissions(current_user, ["backup:restore"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Резервная копия не завершена или повреждена")
    
    try:
        # Создаем запись о восстановлении
        restore_record = RestoreRecord(
            backup_record_id=backup_id,
            name=restore_data.name,
            description=restore_data.description,
            components_to_restore=restore_data.components_to_restore,
            restore_options=restore_data.restore_options,
            created_by=current_user.id,
            status=RestoreStatus.PENDING
        )
        
        db.add(restore_record)
        db.commit()
        db.refresh(restore_record)
        
        # Запускаем восстановление в фоне
        background_tasks.add_task(
            backup_service.restore_backup_with_record,
            restore_record.id,
            backup.backup_path,
            restore_data.components_to_restore,
            restore_data.restore_options
        )
        
        return {
            "message": "Восстановление запущено",
            "restore_id": restore_record.id,
            "status": "in_progress"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка запуска восстановления: {str(e)}")


@router.get("/{backup_id}/integrity", response_model=List[BackupIntegrityCheckResponse])
async def get_backup_integrity_checks(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает результаты проверки целостности резервной копии"""
    await require_permissions(current_user, ["backup:read"])
    
    checks = db.query(BackupIntegrityCheck).filter(
        BackupIntegrityCheck.backup_record_id == backup_id
    ).order_by(BackupIntegrityCheck.checked_at.desc()).all()
    
    return [BackupIntegrityCheckResponse.from_orm(check) for check in checks]


@router.post("/{backup_id}/check-integrity")
async def check_backup_integrity(
    backup_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Запускает проверку целостности резервной копии"""
    await require_permissions(current_user, ["backup:check"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    # Запускаем проверку в фоне
    background_tasks.add_task(backup_service.check_backup_integrity, backup_id)
    
    return {"message": "Проверка целостности запущена"}


# Управление расписанием
@router.post("/schedules", response_model=dict)
async def create_backup_schedule(
    schedule_data: BackupScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создает расписание резервного копирования"""
    await require_permissions(current_user, ["backup:schedule"])
    
    try:
        schedule_id = await backup_service.create_backup_schedule(
            name=schedule_data.name,
            cron_expression=schedule_data.cron_expression,
            components=schedule_data.backup_components,
            created_by=current_user.id,
            description=schedule_data.description,
            timezone=schedule_data.timezone,
            retention_days=schedule_data.retention_days,
            compression_enabled=schedule_data.compression_enabled,
            encryption_enabled=schedule_data.encryption_enabled,
            notify_on_success=schedule_data.notify_on_success,
            notify_on_failure=schedule_data.notify_on_failure,
            notification_channels=schedule_data.notification_channels,
            notification_recipients=schedule_data.notification_recipients
        )
        
        return {
            "message": "Расписание создано",
            "schedule_id": schedule_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания расписания: {str(e)}")


@router.get("/schedules", response_model=List[BackupScheduleResponse])
async def list_backup_schedules(
    enabled_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает список расписаний резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    schedules = await backup_service.get_backup_schedules(enabled_only=enabled_only)
    return [BackupScheduleResponse.from_orm(schedule) for schedule in schedules]


@router.put("/schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def update_backup_schedule(
    schedule_id: int,
    schedule_data: BackupScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновляет расписание резервного копирования"""
    await require_permissions(current_user, ["backup:schedule"])
    
    schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    
    try:
        # Обновляем поля
        update_data = schedule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        # Обновляем время изменения
        schedule.updated_at = datetime.utcnow()
        
        # Пересчитываем следующий запуск если изменилось cron выражение
        if 'cron_expression' in update_data:
            from croniter import croniter
            cron = croniter(schedule.cron_expression, datetime.utcnow())
            schedule.next_run_at = cron.get_next(datetime)
        
        db.commit()
        db.refresh(schedule)
        
        return BackupScheduleResponse.from_orm(schedule)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления расписания: {str(e)}")


@router.delete("/schedules/{schedule_id}")
async def delete_backup_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаляет расписание резервного копирования"""
    await require_permissions(current_user, ["backup:schedule"])
    
    schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    
    try:
        db.delete(schedule)
        db.commit()
        return {"message": "Расписание удалено"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления расписания: {str(e)}")


# Статистика и мониторинг
@router.get("/stats", response_model=BackupStats)
async def get_backup_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает статистику резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        # Общая статистика
        total_backups = db.query(BackupRecord).count()
        successful_backups = db.query(BackupRecord).filter(BackupRecord.success == True).count()
        failed_backups = db.query(BackupRecord).filter(BackupRecord.success == False).count()
        
        # Размер резервных копий
        total_size_result = db.query(db.func.sum(BackupRecord.total_size)).filter(
            BackupRecord.success == True
        ).scalar()
        total_size = total_size_result or 0
        
        # Среднее время резервного копирования
        avg_time_result = db.query(db.func.avg(BackupRecord.duration_seconds)).filter(
            BackupRecord.success == True,
            BackupRecord.duration_seconds.isnot(None)
        ).scalar()
        average_backup_time = float(avg_time_result) if avg_time_result else None
        
        # Последняя успешная резервная копия
        last_backup = db.query(BackupRecord).filter(
            BackupRecord.success == True
        ).order_by(BackupRecord.completed_at.desc()).first()
        last_backup_date = last_backup.completed_at if last_backup else None
        
        # Следующая запланированная резервная копия
        next_schedule = db.query(BackupSchedule).filter(
            BackupSchedule.enabled == True,
            BackupSchedule.next_run_at.isnot(None)
        ).order_by(BackupSchedule.next_run_at.asc()).first()
        next_scheduled_backup = next_schedule.next_run_at if next_schedule else None
        
        # Активные расписания
        active_schedules = db.query(BackupSchedule).filter(BackupSchedule.enabled == True).count()
        
        return BackupStats(
            total_backups=total_backups,
            successful_backups=successful_backups,
            failed_backups=failed_backups,
            total_size=total_size,
            average_backup_time=average_backup_time,
            last_backup_date=last_backup_date,
            next_scheduled_backup=next_scheduled_backup,
            active_schedules=active_schedules
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@router.get("/status", response_model=BackupSystemStatus)
async def get_backup_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает статус системы резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        warnings = []
        recommendations = []
        
        # Проверяем доступность хранилища
        storage_available = os.path.exists(backup_service.backup_dir)
        if not storage_available:
            warnings.append("Директория резервных копий недоступна")
        
        # Проверяем последнюю успешную резервную копию
        last_successful = db.query(BackupRecord).filter(
            BackupRecord.success == True
        ).order_by(BackupRecord.completed_at.desc()).first()
        
        last_successful_backup = last_successful.completed_at if last_successful else None
        
        # Проверяем неудачные резервные копии за последние 24 часа
        yesterday = datetime.utcnow() - timedelta(days=1)
        failed_last_24h = db.query(BackupRecord).filter(
            BackupRecord.success == False,
            BackupRecord.created_at >= yesterday
        ).count()
        
        if failed_last_24h > 0:
            warnings.append(f"За последние 24 часа неудачных резервных копий: {failed_last_24h}")
        
        # Проверяем ожидающие резервные копии
        pending_backups = db.query(BackupRecord).filter(
            BackupRecord.status.in_([BackupStatus.PENDING, BackupStatus.IN_PROGRESS])
        ).count()
        
        # Рекомендации
        if not last_successful_backup or (datetime.utcnow() - last_successful_backup).days > 7:
            recommendations.append("Рекомендуется создать резервную копию")
        
        if db.query(BackupSchedule).filter(BackupSchedule.enabled == True).count() == 0:
            recommendations.append("Настройте автоматическое резервное копирование")
        
        # Определяем общий статус
        if not storage_available or failed_last_24h > 3:
            status = "error"
        elif warnings or failed_last_24h > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return BackupSystemStatus(
            status=status,
            backup_service_running=True,  # TODO: реальная проверка
            scheduler_running=True,  # TODO: реальная проверка
            storage_available=storage_available,
            last_successful_backup=last_successful_backup,
            pending_backups=pending_backups,
            failed_backups_last_24h=failed_last_24h,
            warnings=warnings,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса системы: {str(e)}")


# Дополнительные методы для восстановления
@router.get("/restores", response_model=List[RestoreRecordResponse])
async def list_restore_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает список записей о восстановлении"""
    await require_permissions(current_user, ["backup:read"])
    
    restores = db.query(RestoreRecord).order_by(RestoreRecord.created_at.desc()).all()
    return [RestoreRecordResponse.from_orm(restore) for restore in restores]


@router.get("/restores/{restore_id}", response_model=RestoreRecordResponse)
async def get_restore_record(
    restore_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает информацию о восстановлении"""
    await require_permissions(current_user, ["backup:read"])
    
    restore = db.query(RestoreRecord).filter(RestoreRecord.id == restore_id).first()
    if not restore:
        raise HTTPException(status_code=404, detail="Запись о восстановлении не найдена")
    
    return RestoreRecordResponse.from_orm(restore)


@router.get("/{backup_id}/preview", response_model=BackupPreview)
async def get_backup_preview(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает предварительный просмотр содержимого резервной копии"""
    await require_permissions(current_user, ["backup:read"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    try:
        preview = await backup_service.get_backup_preview(backup_id)
        return BackupPreview(**preview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения предварительного просмотра: {str(e)}")


@router.post("/{backup_id}/validate-restore", response_model=BackupValidationResult)
async def validate_backup_restore(
    backup_id: int,
    validation_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Валидирует возможность восстановления из резервной копии"""
    await require_permissions(current_user, ["backup:read"])
    
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    
    try:
        validation_result = await backup_service.validate_restore(
            backup_id, 
            validation_data.get('components_to_restore', []),
            validation_data.get('restore_options', {})
        )
        return BackupValidationResult(**validation_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка валидации: {str(e)}")


# Мониторинг и отчеты
@router.get("/monitoring/metrics", response_model=dict)
async def get_monitoring_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает метрики мониторинга системы резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        from ..services.backup_monitoring_service import backup_monitoring_service
        metrics = await backup_monitoring_service.get_system_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")


@router.get("/monitoring/health-report", response_model=dict)
async def get_health_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает подробный отчет о состоянии системы резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        from ..services.backup_monitoring_service import backup_monitoring_service
        report = await backup_monitoring_service.generate_health_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчета: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Запускает мониторинг системы резервного копирования"""
    await require_permissions(current_user, ["backup:admin"])
    
    try:
        from ..services.backup_monitoring_service import backup_monitoring_service
        
        if not backup_monitoring_service.is_monitoring:
            # Запускаем мониторинг в фоне
            import asyncio
            asyncio.create_task(backup_monitoring_service.start_monitoring())
            return {"message": "Мониторинг запущен"}
        else:
            return {"message": "Мониторинг уже запущен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска мониторинга: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Останавливает мониторинг системы резервного копирования"""
    await require_permissions(current_user, ["backup:admin"])
    
    try:
        from ..services.backup_monitoring_service import backup_monitoring_service
        await backup_monitoring_service.stop_monitoring()
        return {"message": "Мониторинг остановлен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки мониторинга: {str(e)}")


@router.get("/monitoring/alerts", response_model=List[dict])
async def get_current_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает текущие алерты системы резервного копирования"""
    await require_permissions(current_user, ["backup:read"])
    
    try:
        from ..services.backup_monitoring_service import backup_monitoring_service
        metrics = await backup_monitoring_service.get_system_metrics()
        alerts = await backup_monitoring_service._check_alert_conditions(metrics)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения алертов: {str(e)}")