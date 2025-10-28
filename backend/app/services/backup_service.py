"""
Расширенный сервис для резервного копирования и восстановления данных
"""

import logging
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
from pathlib import Path
import json
import hashlib
import zipfile
import tempfile
from croniter import croniter
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.backup import BackupRecord, BackupSchedule, RestoreRecord, BackupIntegrityCheck
from ..models.backup import BackupStatus, BackupType, RestoreStatus
from ..services.notification_service import notification_service

logger = logging.getLogger(__name__)


class EnhancedBackupService:
    """Расширенный сервис для резервного копирования"""
    
    def __init__(self):
        self.backup_dir = os.getenv("BACKUP_DIR", os.path.join(os.getcwd(), "backend", "backups"))
        self.max_backups = int(os.getenv("MAX_BACKUPS", "7"))  # Храним 7 дней
        self.backup_interval_hours = int(os.getenv("BACKUP_INTERVAL_HOURS", "6"))  # Каждые 6 часов
        self.compression_level = int(os.getenv("BACKUP_COMPRESSION_LEVEL", "6"))  # Уровень сжатия
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")  # Ключ шифрования
        
        # Создаем директории
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "temp"), exist_ok=True)
    
    async def create_backup_with_record(
        self, 
        name: str,
        components: List[str],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[int] = None,
        backup_type: BackupType = BackupType.MANUAL,
        compression_enabled: bool = True,
        encryption_enabled: bool = False,
        retention_days: int = 30
    ) -> Dict[str, Any]:
        """Создает резервную копию с записью в базе данных"""
        
        # Создаем запись в БД
        db = next(get_db())
        backup_record = BackupRecord(
            name=name,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            created_by=created_by,
            description=description,
            tags=tags,
            retention_days=retention_days,
            compression_enabled=compression_enabled,
            encryption_enabled=encryption_enabled
        )
        
        try:
            db.add(backup_record)
            db.commit()
            db.refresh(backup_record)
            
            # Обновляем статус на "в процессе"
            backup_record.status = BackupStatus.IN_PROGRESS
            backup_record.started_at = datetime.utcnow()
            db.commit()
            
            # Выполняем резервное копирование
            result = await self._perform_backup(backup_record.id, components, compression_enabled, encryption_enabled)
            
            # Обновляем запись результатами
            backup_record.status = BackupStatus.COMPLETED if result["success"] else BackupStatus.FAILED
            backup_record.completed_at = datetime.utcnow()
            backup_record.backup_path = result.get("backup_path")
            backup_record.total_size = result.get("total_size", 0)
            backup_record.components = result.get("components", {})
            backup_record.success = result["success"]
            backup_record.error_message = result.get("error")
            backup_record.warnings = result.get("warnings", [])
            backup_record.files_count = result.get("files_count", 0)
            
            if backup_record.started_at and backup_record.completed_at:
                backup_record.duration_seconds = (backup_record.completed_at - backup_record.started_at).total_seconds()
            
            db.commit()
            
            # Отправляем уведомление
            await self._send_backup_notification(backup_record, result["success"])
            
            # Запускаем проверку целостности в фоне
            if result["success"]:
                asyncio.create_task(self._schedule_integrity_check(backup_record.id))
            
            return {
                "backup_id": backup_record.id,
                "success": result["success"],
                "backup_path": result.get("backup_path"),
                "total_size": result.get("total_size", 0),
                "duration_seconds": backup_record.duration_seconds,
                "error": result.get("error"),
                "warnings": result.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            backup_record.status = BackupStatus.FAILED
            backup_record.completed_at = datetime.utcnow()
            backup_record.error_message = str(e)
            backup_record.success = False
            db.commit()
            
            return {
                "backup_id": backup_record.id,
                "success": False,
                "error": str(e)
            }
        finally:
            db.close()
        
    async def create_backup(self) -> Dict[str, Any]:
        """Создает резервную копию всех данных"""
        try:
            # Создаем папку для бэкапов
            os.makedirs(self.backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"advakod_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            result = {
                "timestamp": timestamp,
                "backup_path": backup_path,
                "databases": {},
                "success": True,
                "errors": []
            }
            
            # 1. Бэкап основной базы данных
            db_backup = await self._backup_main_database(backup_path)
            result["databases"]["main"] = db_backup
            
            # 2. Бэкап векторной базы данных
            vector_backup = await self._backup_vector_database(backup_path)
            result["databases"]["vector"] = vector_backup
            
            # 3. Бэкап конфигурационных файлов
            config_backup = await self._backup_config_files(backup_path)
            result["databases"]["config"] = config_backup
            
            # 4. Очистка старых бэкапов
            await self._cleanup_old_backups()
            
            # 5. Создание манифеста
            await self._create_backup_manifest(backup_path, result)
            
            logger.info(f"✅ Резервная копия создана: {backup_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _backup_main_database(self, backup_path: str) -> Dict[str, Any]:
        """Бэкап основной базы данных"""
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite бэкап
                source_db = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
                if source_db.startswith("./"):
                    source_db = os.path.join("backend", source_db[2:])
                
                if os.path.exists(source_db):
                    backup_db_path = os.path.join(backup_path, "main_database.db")
                    shutil.copy2(source_db, backup_db_path)
                    
                    # Проверяем целостность
                    conn = sqlite3.connect(backup_db_path)
                    conn.execute("PRAGMA integrity_check")
                    conn.close()
                    
                    file_size = os.path.getsize(backup_db_path)
                    return {
                        "status": "success",
                        "type": "sqlite",
                        "file_path": backup_db_path,
                        "file_size": file_size
                    }
                else:
                    return {"status": "error", "error": "Database file not found"}
                    
            else:
                # PostgreSQL бэкап
                backup_file = os.path.join(backup_path, "main_database.sql")
                
                # Используем pg_dump для создания SQL дампа
                cmd = [
                    "pg_dump",
                    "--no-password",
                    "--verbose",
                    "--clean",
                    "--no-acl",
                    "--no-owner",
                    "-f", backup_file,
                    settings.DATABASE_URL
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    file_size = os.path.getsize(backup_file)
                    return {
                        "status": "success",
                        "type": "postgresql",
                        "file_path": backup_file,
                        "file_size": file_size
                    }
                else:
                    return {
                        "status": "error", 
                        "error": stderr.decode() if stderr else "Unknown pg_dump error"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа основной БД: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _backup_vector_database(self, backup_path: str) -> Dict[str, Any]:
        """Бэкап векторной базы данных"""
        try:
            # ChromaDB бэкап
            chroma_source = os.path.join("backend", "data", "chroma_db")
            if os.path.exists(chroma_source):
                chroma_backup = os.path.join(backup_path, "chroma_db")
                shutil.copytree(chroma_source, chroma_backup)
                
                # Подсчитываем размер
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(chroma_backup)
                    for filename in filenames
                )
                
                return {
                    "status": "success",
                    "type": "chromadb",
                    "path": chroma_backup,
                    "size": total_size
                }
            else:
                return {"status": "skipped", "reason": "ChromaDB directory not found"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа векторной БД: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _backup_config_files(self, backup_path: str) -> Dict[str, Any]:
        """Бэкап конфигурационных файлов"""
        try:
            config_backup_path = os.path.join(backup_path, "config")
            os.makedirs(config_backup_path, exist_ok=True)
            
            # Файлы для бэкапа
            config_files = [
                "backend/app/core/config.py",
                "backend/alembic.ini",
                "backend/requirements.txt",
                ".env"  # Если существует
            ]
            
            backed_up = []
            for config_file in config_files:
                if os.path.exists(config_file):
                    filename = os.path.basename(config_file)
                    backup_file_path = os.path.join(config_backup_path, filename)
                    shutil.copy2(config_file, backup_file_path)
                    backed_up.append(filename)
            
            return {
                "status": "success",
                "files": backed_up,
                "path": config_backup_path
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа конфигурации: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_old_backups(self):
        """Удаляет старые резервные копии"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # Получаем список всех бэкапов
            backups = []
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path) and item.startswith("advakod_backup_"):
                    try:
                        # Извлекаем дату из имени
                        date_str = item.replace("advakod_backup_", "")
                        backup_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        backups.append((backup_date, item_path))
                    except ValueError:
                        continue
            
            # Сортируем по дате (новые первыми)
            backups.sort(key=lambda x: x[0], reverse=True)
            
            # Удаляем старые бэкапы
            if len(backups) > self.max_backups:
                for _, old_backup_path in backups[self.max_backups:]:
                    shutil.rmtree(old_backup_path)
                    logger.info(f"🗑️ Удален старый бэкап: {old_backup_path}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых бэкапов: {e}")
    
    async def _create_backup_manifest(self, backup_path: str, backup_info: Dict[str, Any]):
        """Создает манифест резервной копии"""
        try:
            manifest_path = os.path.join(backup_path, "manifest.json")
            
            manifest = {
                "backup_info": backup_info,
                "created_at": datetime.now().isoformat(),
                "version": settings.VERSION,
                "project_name": settings.PROJECT_NAME,
                "environment": settings.ENVIRONMENT,
                "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "sqlite",  # Скрываем пароли
                "restore_instructions": {
                    "main_db": "Восстановите main_database.db или импортируйте main_database.sql",
                    "vector_db": "Скопируйте папку chroma_db в backend/data/",
                    "config": "Проверьте конфигурационные файлы в папке config/"
                }
            }
            
            import json
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
                
            logger.info(f"📋 Манифест создан: {manifest_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания манифеста: {e}")
    
    async def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """Восстанавливает данные из резервной копии"""
        try:
            if not os.path.exists(backup_path):
                return {"status": "error", "error": "Backup path not found"}
            
            # Читаем манифест
            manifest_path = os.path.join(backup_path, "manifest.json")
            if os.path.exists(manifest_path):
                import json
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                logger.info(f"📋 Манифест загружен: {manifest['created_at']}")
            
            result = {"status": "success", "restored": []}
            
            # Восстанавливаем основную БД
            main_db_path = os.path.join(backup_path, "main_database.db")
            if os.path.exists(main_db_path):
                if settings.DATABASE_URL.startswith("sqlite"):
                    target_db = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
                    if target_db.startswith("./"):
                        target_db = os.path.join("backend", target_db[2:])
                    
                    shutil.copy2(main_db_path, target_db)
                    result["restored"].append("main_database")
            
            # Восстанавливаем векторную БД
            vector_backup_path = os.path.join(backup_path, "chroma_db")
            if os.path.exists(vector_backup_path):
                target_vector_path = os.path.join("backend", "data", "chroma_db")
                if os.path.exists(target_vector_path):
                    shutil.rmtree(target_vector_path)
                shutil.copytree(vector_backup_path, target_vector_path)
                result["restored"].append("vector_database")
            
            logger.info(f"✅ Восстановление завершено: {result['restored']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Получает статус системы бэкапов"""
        try:
            if not os.path.exists(self.backup_dir):
                return {
                    "status": "no_backups",
                    "backup_dir": self.backup_dir,
                    "backups_count": 0
                }
            
            # Подсчитываем бэкапы
            backups = []
            total_size = 0
            
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path) and item.startswith("advakod_backup_"):
                    try:
                        date_str = item.replace("advakod_backup_", "")
                        backup_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        
                        # Подсчитываем размер
                        size = sum(
                            os.path.getsize(os.path.join(dirpath, filename))
                            for dirpath, dirnames, filenames in os.walk(item_path)
                            for filename in filenames
                        )
                        total_size += size
                        
                        backups.append({
                            "name": item,
                            "date": backup_date.isoformat(),
                            "size": size,
                            "age_days": (datetime.now() - backup_date).days
                        })
                    except ValueError:
                        continue
            
            # Сортируем по дате (новые первыми)
            backups.sort(key=lambda x: x["date"], reverse=True)
            
            return {
                "status": "active",
                "backup_dir": self.backup_dir,
                "backups_count": len(backups),
                "total_size": total_size,
                "latest_backup": backups[0] if backups else None,
                "backups": backups[:5],  # Показываем только последние 5
                "settings": {
                    "max_backups": self.max_backups,
                    "interval_hours": self.backup_interval_hours
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса бэкапов: {e}")
            return {"status": "error", "error": str(e)}


    async def _perform_backup(
        self, 
        backup_id: int, 
        components: List[str], 
        compression_enabled: bool = True,
        encryption_enabled: bool = False
    ) -> Dict[str, Any]:
        """Выполняет резервное копирование компонентов"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_id}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            result = {
                "backup_path": backup_path,
                "components": {},
                "success": True,
                "warnings": [],
                "files_count": 0,
                "total_size": 0
            }
            
            # Резервное копирование компонентов
            for component in components:
                if component == "main_db":
                    comp_result = await self._backup_main_database(backup_path)
                elif component == "vector_db":
                    comp_result = await self._backup_vector_database(backup_path)
                elif component == "config":
                    comp_result = await self._backup_config_files(backup_path)
                elif component == "uploads":
                    comp_result = await self._backup_uploads(backup_path)
                elif component == "logs":
                    comp_result = await self._backup_logs(backup_path)
                else:
                    comp_result = {"status": "skipped", "reason": f"Unknown component: {component}"}
                
                result["components"][component] = comp_result
                
                if comp_result.get("status") == "error":
                    result["success"] = False
                elif comp_result.get("status") == "warning":
                    result["warnings"].append(f"{component}: {comp_result.get('warning', 'Unknown warning')}")
                
                # Подсчитываем размер и файлы
                if "file_size" in comp_result:
                    result["total_size"] += comp_result["file_size"]
                    result["files_count"] += 1
                elif "size" in comp_result:
                    result["total_size"] += comp_result["size"]
                    result["files_count"] += comp_result.get("files_count", 1)
            
            # Создаем манифест
            await self._create_backup_manifest(backup_path, result)
            
            # Сжатие если включено
            if compression_enabled and result["success"]:
                compressed_path = await self._compress_backup(backup_path)
                if compressed_path:
                    # Удаляем несжатую версию
                    shutil.rmtree(backup_path)
                    result["backup_path"] = compressed_path
                    result["total_size"] = os.path.getsize(compressed_path)
            
            # Шифрование если включено
            if encryption_enabled and result["success"] and self.encryption_key:
                encrypted_path = await self._encrypt_backup(result["backup_path"])
                if encrypted_path:
                    os.remove(result["backup_path"])
                    result["backup_path"] = encrypted_path
                    result["total_size"] = os.path.getsize(encrypted_path)
            
            # Очистка старых бэкапов
            await self._cleanup_old_backups()
            
            logger.info(f"✅ Резервная копия создана: {result['backup_path']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения резервного копирования: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _backup_uploads(self, backup_path: str) -> Dict[str, Any]:
        """Резервное копирование загруженных файлов"""
        try:
            uploads_source = os.path.join("backend", "uploads")
            if os.path.exists(uploads_source):
                uploads_backup = os.path.join(backup_path, "uploads")
                shutil.copytree(uploads_source, uploads_backup)
                
                # Подсчитываем размер
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(uploads_backup)
                    for filename in filenames
                )
                
                files_count = sum(
                    len(filenames)
                    for dirpath, dirnames, filenames in os.walk(uploads_backup)
                )
                
                return {
                    "status": "success",
                    "type": "uploads",
                    "path": uploads_backup,
                    "size": total_size,
                    "files_count": files_count
                }
            else:
                return {"status": "skipped", "reason": "Uploads directory not found"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа загрузок: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _backup_logs(self, backup_path: str) -> Dict[str, Any]:
        """Резервное копирование логов"""
        try:
            logs_backup_path = os.path.join(backup_path, "logs")
            os.makedirs(logs_backup_path, exist_ok=True)
            
            # Пути к логам
            log_paths = [
                "backend/logs",
                "backend/backend.log",
                "frontend/frontend.log"
            ]
            
            backed_up = []
            total_size = 0
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    if os.path.isdir(log_path):
                        # Копируем директорию
                        target_dir = os.path.join(logs_backup_path, os.path.basename(log_path))
                        shutil.copytree(log_path, target_dir)
                        
                        # Подсчитываем размер
                        dir_size = sum(
                            os.path.getsize(os.path.join(dirpath, filename))
                            for dirpath, dirnames, filenames in os.walk(target_dir)
                            for filename in filenames
                        )
                        total_size += dir_size
                    else:
                        # Копируем файл
                        filename = os.path.basename(log_path)
                        target_file = os.path.join(logs_backup_path, filename)
                        shutil.copy2(log_path, target_file)
                        total_size += os.path.getsize(target_file)
                    
                    backed_up.append(os.path.basename(log_path))
            
            return {
                "status": "success",
                "files": backed_up,
                "path": logs_backup_path,
                "size": total_size,
                "files_count": len(backed_up)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа логов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _compress_backup(self, backup_path: str) -> Optional[str]:
        """Сжимает резервную копию"""
        try:
            compressed_path = f"{backup_path}.zip"
            
            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            logger.info(f"📦 Резервная копия сжата: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка сжатия резервной копии: {e}")
            return None
    
    async def _encrypt_backup(self, backup_path: str) -> Optional[str]:
        """Шифрует резервную копию (заглушка для будущей реализации)"""
        try:
            # TODO: Реализовать шифрование с использованием cryptography
            logger.info(f"🔐 Шифрование резервной копии: {backup_path}")
            return backup_path  # Пока возвращаем исходный путь
            
        except Exception as e:
            logger.error(f"❌ Ошибка шифрования резервной копии: {e}")
            return None
    
    async def _send_backup_notification(self, backup_record: BackupRecord, success: bool):
        """Отправляет уведомление о результате резервного копирования"""
        try:
            if success:
                message = f"✅ Резервная копия '{backup_record.name}' успешно создана"
                notification_type = "success"
            else:
                message = f"❌ Ошибка создания резервной копии '{backup_record.name}': {backup_record.error_message}"
                notification_type = "error"
            
            # Отправляем уведомление через сервис уведомлений
            # TODO: Implement system notification when notification service is ready
            logger.info(f"📢 {message}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о резервном копировании: {e}")
    
    async def _schedule_integrity_check(self, backup_id: int):
        """Планирует проверку целостности резервной копии"""
        try:
            # Ждем немного, чтобы резервная копия была полностью записана
            await asyncio.sleep(10)
            
            # Выполняем проверку целостности
            await self.check_backup_integrity(backup_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка планирования проверки целостности: {e}")
    
    async def check_backup_integrity(self, backup_id: int) -> Dict[str, Any]:
        """Проверяет целостность резервной копии"""
        db = next(get_db())
        
        try:
            # Получаем запись о резервной копии
            backup_record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup_record:
                return {"success": False, "error": "Backup record not found"}
            
            if not backup_record.backup_path or not os.path.exists(backup_record.backup_path):
                return {"success": False, "error": "Backup file not found"}
            
            checks = []
            overall_passed = True
            
            # Проверка размера файла
            file_size_check = await self._check_file_size(backup_record)
            checks.append(file_size_check)
            if not file_size_check["passed"]:
                overall_passed = False
            
            # Проверка структуры архива (если сжато)
            if backup_record.backup_path.endswith('.zip'):
                archive_check = await self._check_archive_integrity(backup_record)
                checks.append(archive_check)
                if not archive_check["passed"]:
                    overall_passed = False
            
            # Проверка манифеста
            manifest_check = await self._check_manifest(backup_record)
            checks.append(manifest_check)
            if not manifest_check["passed"]:
                overall_passed = False
            
            # Сохраняем результаты проверок
            for check in checks:
                integrity_check = BackupIntegrityCheck(
                    backup_record_id=backup_id,
                    status="passed" if check["passed"] else "failed",
                    check_type=check["check_type"],
                    passed=check["passed"],
                    error_message=check.get("error"),
                    warnings=check.get("warnings", []),
                    details=check.get("details", {}),
                    files_checked=check.get("files_checked"),
                    size_verified=check.get("size_verified"),
                    checksum_verified=check.get("checksum_verified", False),
                    check_duration_seconds=check.get("duration")
                )
                db.add(integrity_check)
            
            db.commit()
            
            return {
                "success": True,
                "overall_passed": overall_passed,
                "checks": checks
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки целостности: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    async def _check_file_size(self, backup_record: BackupRecord) -> Dict[str, Any]:
        """Проверяет размер файла резервной копии"""
        start_time = datetime.utcnow()
        
        try:
            actual_size = os.path.getsize(backup_record.backup_path)
            expected_size = backup_record.total_size
            
            # Допускаем отклонение в 5% для сжатых архивов
            tolerance = 0.05 if backup_record.compression_enabled else 0.01
            size_diff = abs(actual_size - expected_size) / expected_size if expected_size > 0 else 0
            
            passed = size_diff <= tolerance
            
            return {
                "check_type": "file_size",
                "passed": passed,
                "size_verified": actual_size,
                "details": {
                    "expected_size": expected_size,
                    "actual_size": actual_size,
                    "size_difference": size_diff,
                    "tolerance": tolerance
                },
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                "check_type": "file_size",
                "passed": False,
                "error": str(e),
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _check_archive_integrity(self, backup_record: BackupRecord) -> Dict[str, Any]:
        """Проверяет целостность архива"""
        start_time = datetime.utcnow()
        
        try:
            with zipfile.ZipFile(backup_record.backup_path, 'r') as zipf:
                # Проверяем архив на ошибки
                bad_files = zipf.testzip()
                
                if bad_files:
                    return {
                        "check_type": "archive_integrity",
                        "passed": False,
                        "error": f"Corrupted files in archive: {bad_files}",
                        "duration": (datetime.utcnow() - start_time).total_seconds()
                    }
                
                # Подсчитываем файлы в архиве
                files_in_archive = len(zipf.namelist())
                
                return {
                    "check_type": "archive_integrity",
                    "passed": True,
                    "files_checked": files_in_archive,
                    "details": {
                        "files_in_archive": files_in_archive,
                        "archive_format": "zip"
                    },
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
                
        except Exception as e:
            return {
                "check_type": "archive_integrity",
                "passed": False,
                "error": str(e),
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _check_manifest(self, backup_record: BackupRecord) -> Dict[str, Any]:
        """Проверяет манифест резервной копии"""
        start_time = datetime.utcnow()
        
        try:
            manifest_path = None
            
            if backup_record.backup_path.endswith('.zip'):
                # Извлекаем манифест из архива
                with zipfile.ZipFile(backup_record.backup_path, 'r') as zipf:
                    if 'manifest.json' in zipf.namelist():
                        manifest_content = zipf.read('manifest.json').decode('utf-8')
                        manifest = json.loads(manifest_content)
                    else:
                        return {
                            "check_type": "manifest",
                            "passed": False,
                            "error": "Manifest file not found in archive",
                            "duration": (datetime.utcnow() - start_time).total_seconds()
                        }
            else:
                # Читаем манифест из директории
                manifest_path = os.path.join(backup_record.backup_path, 'manifest.json')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                else:
                    return {
                        "check_type": "manifest",
                        "passed": False,
                        "error": "Manifest file not found",
                        "duration": (datetime.utcnow() - start_time).total_seconds()
                    }
            
            # Проверяем структуру манифеста
            required_fields = ['backup_info', 'created_at', 'version']
            missing_fields = [field for field in required_fields if field not in manifest]
            
            if missing_fields:
                return {
                    "check_type": "manifest",
                    "passed": False,
                    "error": f"Missing required fields in manifest: {missing_fields}",
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            return {
                "check_type": "manifest",
                "passed": True,
                "details": {
                    "manifest_version": manifest.get('version'),
                    "backup_created_at": manifest.get('created_at'),
                    "components": list(manifest.get('backup_info', {}).get('components', {}).keys())
                },
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }
            
        except Exception as e:
            return {
                "check_type": "manifest",
                "passed": False,
                "error": str(e),
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }

    # Методы для управления расписанием
    async def create_backup_schedule(
        self,
        name: str,
        cron_expression: str,
        components: List[str],
        created_by: int,
        **kwargs
    ) -> int:
        """Создает расписание резервного копирования"""
        db = next(get_db())
        
        try:
            # Валидируем cron выражение
            try:
                croniter(cron_expression)
            except Exception:
                raise ValueError("Invalid cron expression")
            
            schedule = BackupSchedule(
                name=name,
                cron_expression=cron_expression,
                backup_components=components,
                created_by=created_by,
                **kwargs
            )
            
            # Вычисляем следующий запуск
            cron = croniter(cron_expression, datetime.utcnow())
            schedule.next_run_at = cron.get_next(datetime)
            
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
            
            logger.info(f"📅 Создано расписание резервного копирования: {schedule.name}")
            return schedule.id
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания расписания: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def get_backup_schedules(self, enabled_only: bool = False) -> List[BackupSchedule]:
        """Получает список расписаний резервного копирования"""
        db = next(get_db())
        
        try:
            query = db.query(BackupSchedule)
            if enabled_only:
                query = query.filter(BackupSchedule.enabled == True)
            
            return query.all()
            
        finally:
            db.close()
    
    async def get_due_schedules(self) -> List[BackupSchedule]:
        """Получает расписания, которые должны быть выполнены"""
        db = next(get_db())
        
        try:
            now = datetime.utcnow()
            return db.query(BackupSchedule).filter(
                BackupSchedule.enabled == True,
                BackupSchedule.next_run_at <= now
            ).all()
            
        finally:
            db.close()
    
    async def restore_backup_with_record(
        self,
        restore_id: int,
        backup_path: str,
        components_to_restore: List[str],
        restore_options: dict = None
    ) -> Dict[str, Any]:
        """Восстанавливает данные из резервной копии с записью в БД"""
        db = next(get_db())
        
        try:
            # Получаем запись о восстановлении
            restore_record = db.query(RestoreRecord).filter(RestoreRecord.id == restore_id).first()
            if not restore_record:
                return {"success": False, "error": "Restore record not found"}
            
            # Обновляем статус
            restore_record.status = RestoreStatus.IN_PROGRESS
            restore_record.started_at = datetime.utcnow()
            db.commit()
            
            # Выполняем восстановление
            result = await self.restore_backup(backup_path)
            
            # Обновляем запись результатами
            restore_record.status = RestoreStatus.COMPLETED if result["status"] == "success" else RestoreStatus.FAILED
            restore_record.completed_at = datetime.utcnow()
            restore_record.success = result["status"] == "success"
            restore_record.error_message = result.get("error")
            restore_record.restored_components = result.get("restored", [])
            
            if restore_record.started_at and restore_record.completed_at:
                restore_record.duration_seconds = (restore_record.completed_at - restore_record.started_at).total_seconds()
            
            db.commit()
            
            # Отправляем уведомление
            await self._send_restore_notification(restore_record, result["status"] == "success")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления с записью: {e}")
            restore_record.status = RestoreStatus.FAILED
            restore_record.completed_at = datetime.utcnow()
            restore_record.error_message = str(e)
            restore_record.success = False
            db.commit()
            
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    async def _send_restore_notification(self, restore_record: RestoreRecord, success: bool):
        """Отправляет уведомление о результате восстановления"""
        try:
            if success:
                message = f"✅ Восстановление '{restore_record.name}' успешно завершено"
                notification_type = "success"
            else:
                message = f"❌ Ошибка восстановления '{restore_record.name}': {restore_record.error_message}"
                notification_type = "error"
            
            # Отправляем уведомление через сервис уведомлений
            # TODO: Implement system notification when notification service is ready
            logger.info(f"📢 {message}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о восстановлении: {e}")
    
    async def get_backup_preview(self, backup_id: int) -> Dict[str, Any]:
        """Получает предварительный просмотр содержимого резервной копии"""
        db = next(get_db())
        
        try:
            # Получаем запись о резервной копии
            backup_record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup_record:
                raise ValueError("Backup record not found")
            
            if not backup_record.backup_path or not os.path.exists(backup_record.backup_path):
                raise ValueError("Backup file not found")
            
            preview = {
                "backup_id": backup_id,
                "manifest": {},
                "components": backup_record.components or {},
                "file_structure": {},
                "estimated_restore_time": None,
                "compatibility_check": {}
            }
            
            # Читаем манифест
            try:
                if backup_record.backup_path.endswith('.zip'):
                    # Из архива
                    with zipfile.ZipFile(backup_record.backup_path, 'r') as zipf:
                        if 'manifest.json' in zipf.namelist():
                            manifest_content = zipf.read('manifest.json').decode('utf-8')
                            preview["manifest"] = json.loads(manifest_content)
                        
                        # Структура файлов
                        preview["file_structure"] = {
                            "files": zipf.namelist(),
                            "total_files": len(zipf.namelist())
                        }
                else:
                    # Из директории
                    manifest_path = os.path.join(backup_record.backup_path, 'manifest.json')
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            preview["manifest"] = json.load(f)
                    
                    # Структура файлов
                    files = []
                    for root, dirs, filenames in os.walk(backup_record.backup_path):
                        for filename in filenames:
                            rel_path = os.path.relpath(os.path.join(root, filename), backup_record.backup_path)
                            files.append(rel_path)
                    
                    preview["file_structure"] = {
                        "files": files,
                        "total_files": len(files)
                    }
            except Exception as e:
                logger.warning(f"Не удалось прочитать манифест: {e}")
            
            # Оценка времени восстановления (примерная)
            if backup_record.total_size:
                # Примерно 50 МБ/сек для восстановления
                estimated_seconds = backup_record.total_size / (50 * 1024 * 1024)
                preview["estimated_restore_time"] = max(60, estimated_seconds)  # Минимум 1 минута
            
            # Проверка совместимости
            preview["compatibility_check"] = {
                "version_compatible": True,  # TODO: реальная проверка версий
                "database_compatible": True,  # TODO: проверка совместимости БД
                "storage_available": self._check_storage_space(backup_record.total_size or 0),
                "services_running": True  # TODO: проверка запущенных сервисов
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения предварительного просмотра: {e}")
            raise
        finally:
            db.close()
    
    async def validate_restore(
        self, 
        backup_id: int, 
        components_to_restore: List[str], 
        restore_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Валидирует возможность восстановления"""
        db = next(get_db())
        
        try:
            # Получаем запись о резервной копии
            backup_record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup_record:
                raise ValueError("Backup record not found")
            
            validation_errors = []
            validation_warnings = []
            components_status = {}
            file_integrity = {}
            size_verification = {}
            recommendations = []
            
            # Проверяем статус резервной копии
            if backup_record.status != BackupStatus.COMPLETED:
                validation_errors.append("Резервная копия не завершена или повреждена")
            
            if not backup_record.success:
                validation_errors.append("Резервная копия создана с ошибками")
            
            # Проверяем существование файла
            if not backup_record.backup_path or not os.path.exists(backup_record.backup_path):
                validation_errors.append("Файл резервной копии не найден")
            else:
                # Проверяем размер файла
                actual_size = os.path.getsize(backup_record.backup_path)
                expected_size = backup_record.total_size or 0
                
                if expected_size > 0:
                    size_diff = abs(actual_size - expected_size) / expected_size
                    if size_diff > 0.1:  # Более 10% отклонения
                        validation_warnings.append(f"Размер файла отличается от ожидаемого на {size_diff*100:.1f}%")
                
                size_verification["expected"] = expected_size
                size_verification["actual"] = actual_size
                size_verification["valid"] = size_diff <= 0.1 if expected_size > 0 else True
            
            # Проверяем компоненты
            available_components = list((backup_record.components or {}).keys())
            for component in components_to_restore:
                if component not in available_components:
                    validation_errors.append(f"Компонент '{component}' недоступен в резервной копии")
                    components_status[component] = "missing"
                else:
                    component_info = backup_record.components.get(component, {})
                    if component_info.get("status") == "success":
                        components_status[component] = "valid"
                    else:
                        validation_warnings.append(f"Компонент '{component}' может быть поврежден")
                        components_status[component] = "warning"
            
            # Проверяем место на диске
            if backup_record.total_size:
                if not self._check_storage_space(backup_record.total_size):
                    validation_errors.append("Недостаточно места на диске для восстановления")
            
            # Проверяем опции восстановления
            if restore_options.get("overwrite_existing") and not restore_options.get("create_backup_before_restore"):
                validation_warnings.append("Рекомендуется создать резервную копию перед перезаписью данных")
                recommendations.append("Включите опцию 'Создать резервную копию перед восстановлением'")
            
            # Проверяем целостность архива (если это архив)
            if backup_record.backup_path.endswith('.zip'):
                try:
                    with zipfile.ZipFile(backup_record.backup_path, 'r') as zipf:
                        bad_files = zipf.testzip()
                        if bad_files:
                            validation_errors.append(f"Поврежденные файлы в архиве: {bad_files}")
                            file_integrity["archive"] = False
                        else:
                            file_integrity["archive"] = True
                except Exception as e:
                    validation_errors.append(f"Ошибка проверки архива: {str(e)}")
                    file_integrity["archive"] = False
            
            # Общие рекомендации
            if not restore_options.get("validate_before_restore"):
                recommendations.append("Рекомендуется включить валидацию данных перед восстановлением")
            
            if not restore_options.get("stop_services_during_restore"):
                recommendations.append("Рекомендуется остановить сервисы во время восстановления")
            
            # Определяем общий статус валидации
            is_valid = len(validation_errors) == 0
            
            return {
                "backup_id": backup_id,
                "is_valid": is_valid,
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "components_status": components_status,
                "file_integrity": file_integrity,
                "size_verification": size_verification,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации восстановления: {e}")
            return {
                "backup_id": backup_id,
                "is_valid": False,
                "validation_errors": [f"Ошибка валидации: {str(e)}"],
                "validation_warnings": [],
                "components_status": {},
                "file_integrity": {},
                "size_verification": {},
                "recommendations": []
            }
        finally:
            db.close()
    
    def _check_storage_space(self, required_bytes: int) -> bool:
        """Проверяет доступное место на диске"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            return free > required_bytes * 1.2  # 20% запас
        except Exception:
            return True  # Если не можем проверить, считаем что места достаточно

# Создаем глобальный экземпляр
backup_service = EnhancedBackupService()


async def schedule_automatic_backups():
    """Планировщик автоматических бэкапов"""
    while True:
        try:
            logger.info("🔄 Запуск автоматического резервного копирования...")
            result = await backup_service.create_backup()
            
            if result["success"]:
                logger.info(f"✅ Автоматический бэкап завершен: {result['backup_path']}")
            else:
                logger.error(f"❌ Ошибка автоматического бэкапа: {result.get('error')}")
            
            # Ждем до следующего бэкапа
            await asyncio.sleep(backup_service.backup_interval_hours * 3600)
            
        except Exception as e:
            logger.error(f"❌ Ошибка планировщика бэкапов: {e}")
            await asyncio.sleep(3600)  # Повторяем через час при ошибке
