"""
Generation Timeout Manager - предотвращает зависания генерации ответов
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class GenerationTimeoutManager:
    """Менеджер таймаутов для генерации ответов"""
    
    def __init__(self, max_generation_time: int = 180):  # ИСПРАВЛЕНО: 3 минуты максимум для предотвращения зависаний
        self.max_generation_time = max_generation_time
        self.active_generations: Dict[str, float] = {}
        self.generation_history: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        
    async def generate_with_timeout(
        self, 
        request_id: str, 
        generation_func: Callable,
        timeout: Optional[int] = None
    ) -> Any:
        """Выполняет генерацию с принудительным таймаутом"""
        timeout = timeout or self.max_generation_time
        start_time = time.time()
        
        async with self._lock:
            self.active_generations[request_id] = start_time
        
        try:
            logger.info(
                f"Starting generation with timeout {timeout}s for request {request_id}"
            )
            
            # Принудительный таймаут на уровне asyncio
            result = await asyncio.wait_for(
                generation_func(), 
                timeout=timeout
            )
            
            generation_time = time.time() - start_time
            
            async with self._lock:
                self.active_generations.pop(request_id, None)
                self.generation_history[request_id] = {
                    "success": True,
                    "duration": generation_time,
                    "completed_at": datetime.now()
                }
            
            logger.info(
                f"Generation completed successfully for {request_id} "
                f"in {generation_time:.2f}s"
            )
            return result
            
        except asyncio.TimeoutError:
            generation_time = time.time() - start_time
            
            async with self._lock:
                self.active_generations.pop(request_id, None)
                self.generation_history[request_id] = {
                    "success": False,
                    "duration": generation_time,
                    "timeout": True,
                    "completed_at": datetime.now()
                }
            
            logger.error(
                f"Generation timeout for request {request_id} "
                f"after {generation_time:.2f}s (max: {timeout}s)"
            )
            
            # Поднимаем исключение с понятным сообщением
            raise TimeoutError(
                f"Генерация ответа превысила максимальное время ожидания ({timeout} секунд). "
                "Попробуйте сократить запрос или подождите уменьшения нагрузки на сервер."
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            
            async with self._lock:
                self.active_generations.pop(request_id, None)
                self.generation_history[request_id] = {
                    "success": False,
                    "duration": generation_time,
                    "error": str(e),
                    "completed_at": datetime.now()
                }
            
            logger.error(
                f"Generation error for request {request_id}: {e} "
                f"(after {generation_time:.2f}s)"
            )
            raise
        
        finally:
            # Очистка старых записей (старше 1 часа)
            await self._cleanup_old_history()
    
    def get_active_generations(self) -> Dict[str, float]:
        """Возвращает активные генерации с их длительностью"""
        async def _get():
            async with self._lock:
                current_time = time.time()
                return {
                    request_id: current_time - start_time
                    for request_id, start_time in self.active_generations.items()
                }
        # Синхронная обертка
        return asyncio.run(_get()) if not asyncio.get_event_loop().is_running() else self.active_generations.copy()
    
    def get_generation_stats(self) -> Dict:
        """Возвращает статистику генераций"""
        async def _get():
            async with self._lock:
                active_count = len(self.active_generations)
                
                # Статистика по истории
                total = len(self.generation_history)
                successful = sum(1 for h in self.generation_history.values() if h.get("success"))
                failed = total - successful
                timeouts = sum(1 for h in self.generation_history.values() if h.get("timeout"))
                
                avg_duration = 0.0
                if self.generation_history:
                    durations = [h.get("duration", 0) for h in self.generation_history.values() if h.get("success")]
                    avg_duration = sum(durations) / len(durations) if durations else 0.0
                
                return {
                    "active_generations": active_count,
                    "total_generations": total,
                    "successful": successful,
                    "failed": failed,
                    "timeouts": timeouts,
                    "average_duration": avg_duration,
                    "max_generation_time": self.max_generation_time
                }
        
        try:
            return asyncio.run(_get()) if not asyncio.get_event_loop().is_running() else {}
        except:
            return {}
    
    async def _cleanup_old_history(self):
        """Очищает старую историю генераций"""
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            to_remove = [
                request_id 
                for request_id, history in self.generation_history.items()
                if history.get("completed_at", datetime.min) < cutoff_time
            ]
            
            for request_id in to_remove:
                self.generation_history.pop(request_id, None)
            
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} old generation history entries")


# Глобальный экземпляр менеджера таймаутов
generation_timeout_manager = GenerationTimeoutManager()

