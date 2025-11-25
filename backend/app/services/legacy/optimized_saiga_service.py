"""
Optimized Saiga Service - улучшенная версия сервиса для работы с языковой моделью Vistral
Основан на saiga_service.py с оптимизациями производительности
"""

import logging
import time
import threading
import asyncio
from typing import Optional, AsyncGenerator, Any, Dict
from queue import Queue
from ..core.config import settings

# Внешняя зависимость llama_cpp оставляем как есть
from llama_cpp import Llama

logger = logging.getLogger(__name__)


def _redact_for_logs(text: str, max_len: int = 120) -> str:
    """Обрезает и маскирует потенциально чувствительную информацию для логов."""
    if not text:
        return ""
    s = text.strip()
    if len(s) <= max_len:
        return s.replace("\n", " ")
    return (s[:max_len//2] + " ... " + s[-max_len//2:]).replace("\n", " ")


def _estimate_tokens(text: str) -> int:
    """Приблизительная оценка токенов: 1 токен ≈ 3-4 символа."""
    if not text:
        return 0
    return max(1, len(text) // 4)


class OptimizedSaigaService:
    """Оптимизированный сервис для работы с языковой моделью Vistral"""
    
    def __init__(self):
        self.model: Optional[Llama] = None
        self._model_loaded: bool = False
        self._load_lock = threading.Lock()
        self._async_semaphore: Optional[asyncio.Semaphore] = None
        
        # Настройки из конфигурации
        self._inference_timeout = getattr(settings, "VISTRAL_INFERENCE_TIMEOUT", 900)
        self._max_concurrency = getattr(settings, "VISTRAL_MAX_CONCURRENCY", 3)  # Увеличено до 3
        
        # Статистика производительности
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_response_time": 0.0,
            "queue_length": 0,
            "concurrent_requests": 0
        }
        
        # Очередь запросов для мониторинга
        self._request_queue = asyncio.Queue()
        self._active_requests = set()
        
    def _ensure_semaphore(self):
        """Инициализирует семафор для ограничения конкурентности"""
        if self._async_semaphore is None:
            try:
                loop = asyncio.get_running_loop()
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)
            except RuntimeError:
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)
    
    def _load_model(self):
        """Синхронная загрузка модели Vistral"""
        if self._model_loaded and self.model is not None:
            return

        with self._load_lock:
            if self._model_loaded and self.model is not None:
                return
            try:
                import os
                
                # Используем VISTRAL параметры вместо SAIGA
                model_path = getattr(settings, "VISTRAL_MODEL_PATH", settings.SAIGA_MODEL_PATH)
                n_ctx = getattr(settings, "VISTRAL_N_CTX", settings.SAIGA_N_CTX)
                n_threads = getattr(settings, "VISTRAL_N_THREADS", settings.SAIGA_N_THREADS)
                n_gpu_layers = getattr(settings, "VISTRAL_N_GPU_LAYERS", getattr(settings, "SAIGA_N_GPU_LAYERS", 0))
                
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Файл модели не найден: {model_path}")
                
                logger.info("Загружаем оптимизированную модель Vistral из %s", model_path)
                logger.info("Параметры: n_ctx=%s, n_threads=%s, max_concurrency=%s", n_ctx, n_threads, self._max_concurrency)

                self.model = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_threads=n_threads,
                    n_gpu_layers=n_gpu_layers,
                    logits_all=False,
                    use_mmap=True,
                    use_mlock=False,
                    verbose=False
                )
                self._model_loaded = True
                logger.info("✅ Оптимизированная модель Vistral успешно загружена")
                
            except Exception as e:
                logger.exception("❌ Ошибка загрузки оптимизированной модели Vistral: %s", e)
                raise

    async def initialize(self):
        """Асинхронная инициализация сервиса"""
        try:
            logger.info("🔄 Инициализация OptimizedSaigaService...")
            await self.ensure_model_loaded_async()
            logger.info("✅ OptimizedSaigaService инициализирован успешно")
        except Exception as e:
            logger.error("❌ Ошибка инициализации OptimizedSaigaService: %s", e)
            raise

    async def ensure_model_loaded_async(self) -> None:
        """Асинхронная загрузка модели"""
        if self._model_loaded and self.model is not None:
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

    def _compute_max_gen_tokens(self, prompt: str, requested_max: int) -> int:
        """Ограничиваем max_tokens в зависимости от n_ctx и длины prompt"""
        n_ctx = getattr(settings, "VISTRAL_N_CTX", getattr(settings, "SAIGA_N_CTX", 4096))
        prompt_tokens = _estimate_tokens(prompt)
        safety_margin = getattr(settings, "VISTRAL_TOKEN_MARGIN", getattr(settings, "SAIGA_TOKEN_MARGIN", 32))
        available = max(1, n_ctx - prompt_tokens - safety_margin)
        if requested_max > available:
            logger.debug("requested_max (%s) > available (%s) -> limiting to available", requested_max, available)
            return available
        return requested_max

    async def generate_legal_response(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8,
        request_id: Optional[str] = None
    ) -> str:
        """Генерация юридического ответа с оптимизациями"""
        start_time = time.time()
        request_id = request_id or f"req_{int(time.time() * 1000)}"
        
        # Подготовка
        self._ensure_semaphore()
        await self.ensure_model_loaded_async()
        
        # Добавляем в активные запросы
        self._active_requests.add(request_id)
        self._stats["concurrent_requests"] = len(self._active_requests)
        
        try:
            # Ограничение конкуренции
            assert self._async_semaphore is not None
            async with self._async_semaphore:
                # Проверяем max tokens
                allowed_max = self._compute_max_gen_tokens(prompt, max_tokens)

                if getattr(settings, "LOG_PROMPTS", False):
                    logger.info("Генерация ответа (optimized) prompt=%s... max_tokens=%s temp=%s", 
                              _redact_for_logs(prompt, 120), allowed_max, temperature)
                else:
                    logger.info("Генерация ответа (optimized) max_tokens=%s temp=%s", allowed_max, temperature)

                loop = asyncio.get_running_loop()

                def _blocking_call():
                    try:
                        result = self.model(
                            prompt,
                            max_tokens=allowed_max,
                            temperature=temperature,
                            top_p=top_p,
                            stop=getattr(settings, "VISTRAL_STOP_TOKENS", getattr(settings, "SAIGA_STOP_TOKENS", None)),
                            repeat_penalty=getattr(settings, "VISTRAL_REPEAT_PENALTY", getattr(settings, "SAIGA_REPEAT_PENALTY", 1.1)),
                        )
                        return result
                    except Exception as e:
                        logger.exception("Ошибка в blocking_call модели: %s", e)
                        raise

                try:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, _blocking_call), 
                        timeout=self._inference_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error("⏰ Inference timeout after %s seconds", self._inference_timeout)
                    raise RuntimeError(f"Inference timeout after {self._inference_timeout} seconds")

                try:
                    text = ""
                    if isinstance(result, dict) and "choices" in result and len(result["choices"]) > 0:
                        text = (result["choices"][0].get("text") or "").strip()
                    else:
                        text = str(result)
                    
                    response_time = time.time() - start_time
                    self._update_stats(True, response_time)
                    logger.info("✅ Оптимизированная генерация завершена (len=%s, time=%.2fs)", len(text), response_time)
                    return text
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    self._update_stats(False, response_time)
                    logger.exception("❌ Ошибка извлечения текста из результата модели: %s", e)
                    raise
                    
        finally:
            # Удаляем из активных запросов
            self._active_requests.discard(request_id)
            self._stats["concurrent_requests"] = len(self._active_requests)

    async def stream_response(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8
    ) -> AsyncGenerator[str, None]:
        """Асинхронный стриминг-генератор с оптимизациями"""
        await self.ensure_model_loaded_async()
        self._ensure_semaphore()

        allowed_max = self._compute_max_gen_tokens(prompt, max_tokens)
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()

        stop_tokens = getattr(settings, "VISTRAL_STOP_TOKENS", getattr(settings, "SAIGA_STOP_TOKENS", None))
        repeat_penalty = getattr(settings, "VISTRAL_REPEAT_PENALTY", getattr(settings, "SAIGA_REPEAT_PENALTY", 1.1))

        def worker():
            try:
                for chunk in self.model(
                    prompt,
                    max_tokens=allowed_max,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop_tokens,
                    repeat_penalty=repeat_penalty,
                    stream=True
                ):
                    if not chunk:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("text", "")
                    if delta:
                        loop.call_soon_threadsafe(q.put_nowait, delta)
                loop.call_soon_threadsafe(q.put_nowait, None)
            except Exception as e:
                logger.exception("Ошибка в streaming worker: %s", e)
                loop.call_soon_threadsafe(q.put_nowait, f"[ERROR] {str(e)}")
                loop.call_soon_threadsafe(q.put_nowait, None)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            token = await q.get()
            if token is None:
                break
            if isinstance(token, str) and token.startswith("[ERROR]"):
                raise RuntimeError(token)
            yield token

    def create_legal_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Создание промпта для юридических вопросов (совместимость с оригинальным API)"""
        # Используем тот же формат промпта, что и в оригинальном сервисе
        special_instructions = ""
        question_lower = (question or "").lower()
        
        if "ип" in question_lower or "индивидуальный предприниматель" in question_lower:
            special_instructions = "\n# Инструкция: см. справочные данные в базе (не хардкодить в коде)\n"
        
        prompt = f"""<s><system>
Ты - опытный юрист-консультант по российскому законодательству. Отвечай на русском языке максимально подробно, точно и профессионально.

КРИТИЧЕСКИ ВАЖНО - ТОЧНОСТЬ ИНФОРМАЦИИ:
- НИКОГДА не выдумывай законы, статьи, сроки или процедуры
- Если не знаешь точную информацию - честно скажи "уточните в компетентных органах"
- Всегда проверяй актуальность данных на 2024 год
- Используй только реально существующие законы РФ
- Указывай точные номера статей и названия законов
- Сроки должны быть реалистичными (дни, недели, месяцы, НЕ годы)
- НЕ упоминай внешние источники (consultant.ru, garant.ru и т.д.)
- НЕ добавляй ссылки на веб-сайты в ответ
- НЕ ПУТАЙ номера статей!
- Если статья не найдена в базе - скажи "статья не найдена в базе данных"

{special_instructions}

Правила ответа:
- Давай развернутые и детальные ответы (1000-2000 слов)
- Используй простой и понятный язык, как будто объясняешь другу
- Приводи конкретные статьи законов и кодексов с точными номерами
- Давай практические рекомендации и реальные примеры
- Структурируй ответ с четкими заголовками и подзаголовками
- Объясняй сложные правовые понятия простыми словами
- Включай информацию о точных сроках, штрафах, ответственности
- Давай пошаговые инструкции с конкретными действиями
- НЕ ПОВТОРЯЙСЯ - каждый пункт должен быть уникальным
- ЗАВЕРШАЙ ответ кратким резюме

Помни: лучше честно сказать "уточните в налоговой/суде/прокуратуре", чем дать неправильную информацию!
</system>
<user>
{question}
</user>
<bot>"""
        
        if context:
            context_section = f"\n\n=== ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ ===\n{context}\n=== КОНЕЦ КОНТЕКСТА ===\n\n"
            prompt = prompt.replace(f"<user>\n{question}", f"{context_section}<user>\n{question}")
        
        return prompt

    def is_model_loaded(self) -> bool:
        """Проверяет, загружена ли модель"""
        return self._model_loaded and self.model is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает расширенную статистику производительности"""
        stats = self._stats.copy()
        stats.update({
            "model_loaded": self.is_model_loaded(),
            "max_concurrency": self._max_concurrency,
            "inference_timeout": self._inference_timeout,
            "active_requests": len(self._active_requests)
        })
        return stats
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_response_time": 0.0,
            "queue_length": 0,
            "concurrent_requests": 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        return {
            "status": "healthy" if self.is_model_loaded() else "unhealthy",
            "model_loaded": self.is_model_loaded(),
            "active_requests": len(self._active_requests),
            "max_concurrency": self._max_concurrency,
            "stats": self.get_stats()
        }
    
    def _update_stats(self, success: bool, response_time: float):
        """Обновляет статистику производительности"""
        self._stats["total_requests"] += 1
        if success:
            self._stats["successful_requests"] += 1
        else:
            self._stats["failed_requests"] += 1
        
        self._stats["last_response_time"] = response_time
        
        if self._stats["successful_requests"] > 0:
            total_time = self._stats["average_response_time"] * (self._stats["successful_requests"] - 1)
            self._stats["average_response_time"] = (total_time + response_time) / self._stats["successful_requests"]


# Глобальный экземпляр сервиса
optimized_saiga_service = OptimizedSaigaService()