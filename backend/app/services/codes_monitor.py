"""
Сервис мониторинга системы кодексов
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from .codes_downloader import CodesDownloader
from .codes_rag_integration import CodesRAGIntegration

logger = logging.getLogger(__name__)

class CodesMonitor:
    def __init__(self, codes_dir: str = "downloaded_codexes"):
        self.codes_dir = Path(codes_dir)
        self.downloader = CodesDownloader(codes_dir)
        self.rag_integration = CodesRAGIntegration(codes_dir)
        
        # Директория для логов мониторинга
        self.logs_dir = Path("monitoring/logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def get_system_status(self) -> Dict:
        """Возвращает общий статус системы кодексов"""
        try:
            # Статус скачивания
            download_status = self.downloader.get_status()
            
            # Статус интеграции
            integration_status = self.rag_integration.get_integration_status()
            
            # Общий статус
            status = {
                'timestamp': datetime.now().isoformat(),
                'download': download_status,
                'integration': integration_status,
                'system_health': self._calculate_system_health(download_status, integration_status)
            }
            
            # Сохранение статуса
            self._save_status(status)
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'system_health': 'error'
            }

    def _calculate_system_health(self, download_status: Dict, integration_status: Dict) -> str:
        """Вычисляет общее состояние системы"""
        try:
            # Проверяем наличие файлов
            if download_status['total_files'] == 0:
                return 'no_files'
            
            # Проверяем интеграцию
            if integration_status['integrated_files'] == 0:
                return 'not_integrated'
            
            # Проверяем соотношение интегрированных файлов
            integration_ratio = integration_status['integrated_files'] / download_status['total_files']
            
            if integration_ratio >= 0.8:
                return 'healthy'
            elif integration_ratio >= 0.5:
                return 'warning'
            else:
                return 'critical'
                
        except Exception:
            return 'unknown'

    def _save_status(self, status: Dict):
        """Сохраняет статус в файл"""
        try:
            status_file = self.logs_dir / f"status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            
            # Очистка старых файлов статуса (оставляем последние 100)
            self._cleanup_old_status_files()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения статуса: {e}")

    def _cleanup_old_status_files(self, keep_count: int = 100):
        """Очищает старые файлы статуса"""
        try:
            status_files = sorted(self.logs_dir.glob("status_*.json"))
            
            if len(status_files) > keep_count:
                files_to_delete = status_files[:-keep_count]
                for file_path in files_to_delete:
                    file_path.unlink()
                    logger.debug(f"Удален старый файл статуса: {file_path.name}")
                    
        except Exception as e:
            logger.error(f"Ошибка очистки старых файлов статуса: {e}")

    def get_download_history(self, days: int = 7) -> List[Dict]:
        """Возвращает историю скачиваний за указанное количество дней"""
        try:
            history = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for status_file in self.logs_dir.glob("status_*.json"):
                try:
                    file_time = datetime.fromtimestamp(status_file.stat().st_mtime)
                    
                    if file_time >= cutoff_date:
                        with open(status_file, 'r', encoding='utf-8') as f:
                            status_data = json.load(f)
                        
                        history.append({
                            'timestamp': status_data.get('timestamp'),
                            'file_time': file_time.isoformat(),
                            'total_files': status_data.get('download', {}).get('total_files', 0),
                            'total_size': status_data.get('download', {}).get('total_size', 0),
                            'system_health': status_data.get('system_health', 'unknown')
                        })
                        
                except Exception as e:
                    logger.warning(f"Ошибка чтения файла статуса {status_file.name}: {e}")
            
            # Сортируем по времени
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Ошибка получения истории скачиваний: {e}")
            return []

    def get_integration_history(self, days: int = 7) -> List[Dict]:
        """Возвращает историю интеграций за указанное количество дней"""
        try:
            history = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Ищем файлы отчетов интеграции
            integration_dir = Path("rag_integration/metadata")
            if integration_dir.exists():
                for report_file in integration_dir.glob("integration_report_*.json"):
                    try:
                        file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                        
                        if file_time >= cutoff_date:
                            with open(report_file, 'r', encoding='utf-8') as f:
                                report_data = json.load(f)
                            
                            history.append({
                                'timestamp': report_data.get('timestamp'),
                                'file_time': file_time.isoformat(),
                                'total_files': report_data.get('total_files', 0),
                                'successful_files': report_data.get('successful_files', 0),
                                'total_chunks': report_data.get('total_chunks', 0)
                            })
                            
                    except Exception as e:
                        logger.warning(f"Ошибка чтения файла отчета {report_file.name}: {e}")
            
            # Сортируем по времени
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Ошибка получения истории интеграций: {e}")
            return []

    def check_system_alerts(self) -> List[Dict]:
        """Проверяет систему на наличие проблем и возвращает алерты"""
        alerts = []
        
        try:
            status = self.get_system_status()
            
            # Проверка наличия файлов
            if status['download']['total_files'] == 0:
                alerts.append({
                    'type': 'warning',
                    'message': 'Нет скачанных файлов кодексов',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Проверка интеграции
            integration_ratio = status['integration']['integrated_files'] / max(status['download']['total_files'], 1)
            if integration_ratio < 0.5:
                alerts.append({
                    'type': 'critical',
                    'message': f'Низкий уровень интеграции: {integration_ratio:.1%}',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Проверка размера файлов
            total_size_mb = status['download']['total_size'] / (1024 * 1024)
            if total_size_mb < 10:  # Менее 10 МБ
                alerts.append({
                    'type': 'warning',
                    'message': f'Маленький общий размер файлов: {total_size_mb:.1f} МБ',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            alerts.append({
                'type': 'error',
                'message': f'Ошибка проверки системы: {e}',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts


