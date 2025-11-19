"""
CPU Monitoring and Load Management for Generation Requests
Предотвращает зависания из-за перегрузки CPU
"""
import psutil
import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CPULoadStatus:
    """Статус загрузки CPU"""
    current_cpu: float
    cpu_overloaded: bool
    can_process: bool
    wait_time: float = 0.0
    reason: Optional[str] = None


class CPULoadManager:
    """Менеджер загрузки CPU для контроля генерации"""
    
    def __init__(
        self,
        max_cpu_threshold: float = 80.0,  # Максимум 80% CPU
        critical_cpu_threshold: float = 90.0,  # Критично при 90%
        check_interval: float = 1.0,  # Проверка каждую секунду
        wait_interval: float = 2.0  # Ждать 2 секунды перед повтором
    ):
        self.max_cpu_threshold = max_cpu_threshold
        self.critical_cpu_threshold = critical_cpu_threshold
        self.check_interval = check_interval
        self.wait_interval = wait_interval
        self._last_check_time = {}
        
    def check_cpu_load(self, request_id: Optional[str] = None) -> CPULoadStatus:
        """Проверяет текущую загрузку CPU"""
        try:
            current_cpu = psutil.cpu_percent(interval=self.check_interval)
            
            cpu_overloaded = current_cpu >= self.critical_cpu_threshold
            can_process = current_cpu < self.max_cpu_threshold
            
            wait_time = 0.0
            reason = None
            
            if cpu_overloaded:
                reason = f"Critical CPU usage: {current_cpu:.1f}%"
                wait_time = self.wait_interval * 3  # Ждем дольше при критической нагрузке
            elif not can_process:
                reason = f"High CPU usage: {current_cpu:.1f}%"
                wait_time = self.wait_interval
            
            status = CPULoadStatus(
                current_cpu=current_cpu,
                cpu_overloaded=cpu_overloaded,
                can_process=can_process,
                wait_time=wait_time,
                reason=reason
            )
            
            if request_id:
                self._last_check_time[request_id] = datetime.now()
                
            return status
            
        except Exception as e:
            logger.error(f"Error checking CPU load: {e}")
            # В случае ошибки разрешаем обработку
            return CPULoadStatus(
                current_cpu=0.0,
                cpu_overloaded=False,
                can_process=True,
                reason=f"Error checking CPU: {e}"
            )
    
    async def wait_for_cpu_availability(
        self, 
        request_id: Optional[str] = None,
        max_wait_time: float = 10.0
    ) -> bool:
        """Ожидает доступности CPU для обработки"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            status = self.check_cpu_load(request_id)
            
            if status.can_process:
                return True
                
            logger.warning(
                f"CPU overload detected ({status.current_cpu:.1f}%), "
                f"waiting {status.wait_time:.1f}s..."
            )
            
            await asyncio.sleep(status.wait_time)
        
        logger.error(f"CPU unavailable after {max_wait_time}s wait")
        return False
    
    def limit_model_threads(self, default_threads: int) -> int:
        """Ограничивает количество потоков модели в зависимости от загрузки CPU"""
        try:
            cpu_count = psutil.cpu_count()
            current_cpu = psutil.cpu_percent(interval=0.5)
            
            # Если CPU загружен больше 70%, уменьшаем потоки
            if current_cpu > 70:
                optimal_threads = max(1, cpu_count // 2)  # Половина ядер
                return min(default_threads, optimal_threads)
            elif current_cpu > 50:
                optimal_threads = max(1, cpu_count * 2 // 3)  # 2/3 ядер
                return min(default_threads, optimal_threads)
            else:
                # Нормальная загрузка - используем все доступные потоки
                return default_threads
                
        except Exception as e:
            logger.error(f"Error limiting model threads: {e}")
            return default_threads
    
    def get_system_info(self) -> Dict:
        """Получает информацию о системе"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_percent": psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}


# Глобальный экземпляр менеджера CPU
cpu_load_manager = CPULoadManager()

