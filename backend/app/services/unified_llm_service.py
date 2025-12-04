"""
Unified LLM Service - единый сервис для работы с языковыми моделями
Объединяет функциональность saiga_service.py, saiga_service_improved.py, optimized_saiga_service.py
"""

import logging
import time
import threading
import asyncio
import uuid
from typing import Optional, AsyncGenerator, Any, Dict, List
from queue import Queue
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ..core.config import settings

# Внешняя зависимость llama_cpp
from llama_cpp import Llama

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Приоритеты запросов"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class LLMRequest:
    """Структура запроса к LLM"""
    id: str
    prompt: str
    context: Optional[str]
    user_id: str
    timestamp: datetime
    priority: RequestPriority = RequestPriority.NORMAL
    stream: bool = True
    max_tokens: int = 1024
    temperature: float = 0.3
    top_p: float = 0.8


@dataclass
class LLMResponse:
    """Структура ответа от LLM"""
    request_id: str
    content: str
    processing_time: float
    tokens_generated: int
    queue_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class ServiceHealth:
    """Состояние здоровья сервиса"""
    status: str  # "healthy", "degraded", "unhealthy"
    last_check: datetime
    response_time: float
    error_rate: float
    memory_usage: float
    cpu_usage: float
    queue_length: int
    active_requests: int


@dataclass
class LLMMetrics:
    """Метрики производительности LLM"""
    requests_per_minute: float
    average_response_time: float
    p95_response_time: float
    error_rate: float
    queue_length: int
    concurrent_requests: int
    memory_usage_mb: float
    cpu_usage_percent: float
    total_requests: int
    successful_requests: int
    failed_requests: int


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


class UnifiedLLMService:
    """Единый сервис для работы с языковыми моделями Vistral"""
    
    def __init__(self):
        self.model: Optional[Llama] = None
        self._model_loaded: bool = False
        self._load_lock = threading.Lock()
        self._async_semaphore: Optional[asyncio.Semaphore] = None
        self._configured_n_batch = getattr(settings, "VISTRAL_N_BATCH", 512)
        self._current_n_batch: Optional[int] = None
        self._long_prompt_threshold = 1500
        self._long_prompt_n_batch = min(512, self._configured_n_batch)
        self._use_mlock = getattr(settings, "VISTRAL_USE_MLOCK", False)
        
        # Настройки из конфигурации
        self._inference_timeout = getattr(settings, "VISTRAL_INFERENCE_TIMEOUT", 900)
        self._max_concurrency = getattr(settings, "VISTRAL_MAX_CONCURRENCY", 3)
        self._queue_size = getattr(settings, "VISTRAL_QUEUE_SIZE", 50)
        
        # Очередь запросов с приоритизацией
        self._request_queue = asyncio.PriorityQueue(maxsize=self._queue_size)
        self._active_requests: Dict[str, LLMRequest] = {}
        self._request_history: List[LLMResponse] = []
        self._max_history = 1000
        
        # Статистика производительности
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "p95_response_time": 0.0,
            "last_response_time": 0.0,
            "queue_length": 0,
            "concurrent_requests": 0,
            "requests_per_minute": 0.0,
            "error_rate": 0.0,
            "memory_usage_mb": 0.0,
            "cpu_usage_percent": 0.0
        }
        
        # Время последнего обновления метрик
        self._last_metrics_update = time.time()
        self._response_times: List[float] = []
        
        # Флаг для graceful shutdown
        self._shutdown_requested = False
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
    def _ensure_semaphore(self):
        """Инициализирует семафор для ограничения конкурентности"""
        if self._async_semaphore is None:
            try:
                loop = asyncio.get_running_loop()
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)
            except RuntimeError:
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)
    
    def _load_model(self, force_n_batch: Optional[int] = None):
        """Синхронная загрузка модели Vistral с оптимизированными параметрами"""
        if self._model_loaded and self.model is not None:
            return

        with self._load_lock:
            if self._model_loaded and self.model is not None:
                return
            try:
                import os
                
                # Используем только VISTRAL параметры
                model_path = getattr(settings, "VISTRAL_MODEL_PATH", "")
                n_ctx = getattr(settings, "VISTRAL_N_CTX", 8192)
                n_threads = getattr(settings, "VISTRAL_N_THREADS", 10)
                # Используем переданный n_batch или дефолтный из настроек (512 для CPU)
                n_batch = force_n_batch or getattr(settings, "VISTRAL_N_BATCH", 512)
                n_gpu_layers = getattr(settings, "VISTRAL_N_GPU_LAYERS", 0)
                # use_mlock и f16_kv только если явно включены (по умолчанию False для CPU)
                use_mlock = getattr(settings, "VISTRAL_USE_MLOCK", False)
                use_f16_kv = use_mlock  # f16_kv только если use_mlock включен
                
                if not model_path or not os.path.exists(model_path):
                    raise FileNotFoundError(f"Файл модели не найден: {model_path}")
                
                logger.info("🚀 Загружаем унифицированную модель Vistral из %s", model_path)
                logger.info("📊 Параметры: n_ctx=%s, n_threads=%s, n_batch=%s, use_mlock=%s, max_concurrency=%s, queue_size=%s", 
                          n_ctx, n_threads, n_batch, use_mlock, self._max_concurrency, self._queue_size)

                self.model = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_threads=n_threads,
                    n_batch=n_batch,  # 512 оптимален для CPU, ускоряет первый токен
                    n_gpu_layers=n_gpu_layers,
                    logits_all=False,
                    use_mmap=True,
                    use_mlock=use_mlock,  # По умолчанию False для CPU
                    verbose=False,
                    f16_kv=use_f16_kv,  # Только если use_mlock включен
                )
                self._current_n_batch = n_batch
                self._model_loaded = True
                logger.info("✅ Унифицированная модель Vistral успешно загружена")
                
            except Exception as e:
                logger.exception("❌ Ошибка загрузки унифицированной модели Vistral: %s", e)
                raise

    def _reload_model_with_batch(self, target_batch: int):
        """Перезагружает модель с указанным n_batch"""
        logger.info("⚙️ Переключаем модель на n_batch=%s", target_batch)
        self._model_loaded = False
        self.model = None
        self._load_model(force_n_batch=target_batch)

    async def _ensure_batch_for_prompt(self, prompt_len: int):
        """Гарантирует использование безопасного n_batch для длинных промптов"""
        if prompt_len <= self._long_prompt_threshold:
            return
        desired_batch = self._long_prompt_n_batch
        if self._current_n_batch is not None and self._current_n_batch <= desired_batch:
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._reload_model_with_batch, desired_batch)

    async def initialize(self):
        """Асинхронная инициализация сервиса"""
        try:
            logger.info("🔄 Инициализация UnifiedLLMService...")
            
            # Загружаем модель
            await self.ensure_model_loaded_async()
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            logger.info("✅ UnifiedLLMService инициализирован успешно")
        except Exception as e:
            logger.error("❌ Ошибка инициализации UnifiedLLMService: %s", e)
            raise

    async def _start_background_tasks(self):
        """Запускает фоновые задачи"""
        # Задача для обработки очереди запросов
        queue_processor = asyncio.create_task(self._process_request_queue())
        self._background_tasks.append(queue_processor)
        
        # Задача для обновления метрик
        metrics_updater = asyncio.create_task(self._update_metrics_periodically())
        self._background_tasks.append(metrics_updater)
        
        logger.info("🔄 Фоновые задачи запущены")

    async def _process_request_queue(self):
        """Обрабатывает очередь запросов в фоновом режиме"""
        while not self._shutdown_requested:
            try:
                # Ждем запрос из очереди с таймаутом
                try:
                    priority, request = await asyncio.wait_for(
                        self._request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Обрабатываем запрос
                await self._process_single_request(request)
                
                # Отмечаем задачу как выполненную
                self._request_queue.task_done()
                
            except Exception as e:
                logger.error("❌ Ошибка в обработчике очереди: %s", e)
                await asyncio.sleep(1)

    async def _process_single_request(self, request: LLMRequest):
        """Обрабатывает один запрос"""
        start_time = time.time()
        
        try:
            # Добавляем в активные запросы
            self._active_requests[request.id] = request
            
            # Генерируем ответ
            if request.stream:
                # Для streaming запросов обрабатываем напрямую
                logger.info(f"🔄 Processing streaming request {request.id}")
                # Streaming обрабатывается в _stream_response_internal
                pass
            else:
                response_text = await self._generate_response_internal(
                    request.prompt,
                    request.max_tokens,
                    request.temperature,
                    request.top_p
                )
                
                # Создаем ответ
                processing_time = time.time() - start_time
                response = LLMResponse(
                    request_id=request.id,
                    content=response_text,
                    processing_time=processing_time,
                    tokens_generated=_estimate_tokens(response_text),
                    queue_time=start_time - request.timestamp.timestamp(),
                    success=True
                )
                
                # Сохраняем в историю
                self._add_to_history(response)
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_response = LLMResponse(
                request_id=request.id,
                content="",
                processing_time=processing_time,
                tokens_generated=0,
                queue_time=start_time - request.timestamp.timestamp(),
                success=False,
                error=str(e)
            )
            self._add_to_history(error_response)
            logger.error("❌ Ошибка обработки запроса %s: %s", request.id, e)
            
        finally:
            # Удаляем из активных запросов
            self._active_requests.pop(request.id, None)

    async def ensure_model_loaded_async(self) -> bool:
        """Асинхронно загружает модель и возвращает результат."""
        if self.is_model_loaded():
            return True
            
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._load_model)
            if not self.is_model_loaded():
                raise Exception("Модель не загрузилась после вызова _load_model")
            logger.info("✅ Модель успешно загружена через ensure_model_loaded_async")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            return False

    def _compute_max_gen_tokens(self, prompt: str, requested_max: int) -> int:
        """Ограничиваем max_tokens в зависимости от n_ctx и длины prompt"""
        n_ctx = getattr(settings, "VISTRAL_N_CTX", 8192)
        prompt_tokens = _estimate_tokens(prompt)
        safety_margin = getattr(settings, "VISTRAL_TOKEN_MARGIN", 32)
        available = max(1, n_ctx - prompt_tokens - safety_margin)
        if requested_max > available:
            logger.debug("requested_max (%s) > available (%s) -> limiting to available", 
                        requested_max, available)
            return available
        return requested_max

    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        stream: bool = True,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8,
        user_id: str = "anonymous",
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> AsyncGenerator[str, None]:
        """Основной метод для генерации ответов с поддержкой streaming"""
        
        # Создаем запрос
        # НЕ обрабатываем промпт повторно, если он уже обработан (из chat.py)
        # Проверяем, не содержит ли промпт уже инструкции юриста
        if "Ты опытный юрист-консультант" in prompt:
            # Промпт уже обработан, используем как есть
            processed_prompt = prompt
        else:
            # Промпт не обработан, обрабатываем
            processed_prompt = self._prepare_prompt(prompt, context)
        
        request = LLMRequest(
            id=str(uuid.uuid4()),
            prompt=processed_prompt,
            context=context,
            user_id=user_id,
            timestamp=datetime.now(),
            priority=priority,
            stream=stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        if stream:
            # Streaming режим
            async for chunk in self._stream_response_internal(request):
                yield chunk
        else:
            # Обычный режим
            response = await self._generate_response_internal(
                request.prompt, max_tokens, temperature, top_p
            )
            yield response

    async def _generate_response_internal(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8
    ) -> str:
        """Внутренний метод для генерации ответа"""
        start_time = time.time()
        
        # Подготовка
        self._ensure_semaphore()
        await self.ensure_model_loaded_async()
        await self._ensure_batch_for_prompt(len(prompt))
        
        # Ограничение конкуренции
        assert self._async_semaphore is not None
        async with self._async_semaphore:
            # Проверяем max tokens
            allowed_max = self._compute_max_gen_tokens(prompt, max_tokens)

            if getattr(settings, "LOG_PROMPTS", False):
                logger.info("🔄 Генерация ответа (unified) prompt=%s... max_tokens=%s temp=%s", 
                          _redact_for_logs(prompt, 120), allowed_max, temperature)
            else:
                logger.info("🔄 Генерация ответа (unified) max_tokens=%s temp=%s", allowed_max, temperature)

            loop = asyncio.get_running_loop()

            def _blocking_call():
                try:
                    # Сначала пробуем chat-completion, совместимо с instruct-моделями
                    try:
                        chat_res = self.model.create_chat_completion(
                            messages=[
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=allowed_max,
                            temperature=temperature,
                            top_p=top_p,
                            stop=getattr(settings, "VISTRAL_STOP_TOKENS", None),
                            repeat_penalty=getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1),
                        )
                        return {"_mode": "chat", **chat_res}
                    except Exception:
                        # Фоллбэк на текстовую генерацию
                        pass

                    result = self.model(
                        prompt,
                        max_tokens=allowed_max,
                        temperature=temperature,
                        top_p=top_p,
                        stop=getattr(settings, "VISTRAL_STOP_TOKENS", None),
                        repeat_penalty=getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1),
                    )
                    return {"_mode": "text", **(result if isinstance(result, dict) else {"raw": result})}
                except Exception as e:
                    logger.exception("❌ Ошибка в blocking_call модели: %s", e)
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
                    # Пытаемся извлечь из chat-completion, затем из text
                    text = (
                        result["choices"][0].get("message", {}).get("content")
                        or result["choices"][0].get("text")
                        or ""
                    )
                    text = (text or "").strip()
                else:
                    text = (str(result) or "").strip()
                # Fallback: если модель вернула пустую строку, делаем одну повторную попытку
                if not text:
                    logger.warning("⚠️ Пустой ответ модели. Выполняем повтор с повышенной temperature/top_p")
                    def _retry_call():
                        return self.model(
                            prompt,
                            max_tokens=max(32, min(allowed_max, 256)),
                            temperature=0.5,
                            top_p=0.9,
                            stop=getattr(settings, "VISTRAL_STOP_TOKENS", None),
                            repeat_penalty=getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1),
                        )
                    retry_result = await loop.run_in_executor(None, _retry_call)
                    if isinstance(retry_result, dict) and "choices" in retry_result and len(retry_result["choices"]) > 0:
                        text = (retry_result["choices"][0].get("text") or "").strip()
                    else:
                        text = (str(retry_result) or "").strip()
                    if not text:
                        text = "Извините, сейчас не удалось сформировать ответ. Попробуйте переформулировать вопрос или задать его короче."

                response_time = time.time() - start_time
                self._update_stats(True, response_time)
                logger.info("✅ Унифицированная генерация завершена (len=%s, time=%.2fs)", 
                          len(text), response_time)
                return text
                
            except Exception as e:
                response_time = time.time() - start_time
                self._update_stats(False, response_time)
                logger.exception("❌ Ошибка извлечения текста из результата модели: %s", e)
                raise

    async def _stream_response_internal(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Внутренний метод для streaming ответа"""
        try:
            # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся, что модель действительно загружена
            model_loaded = await self.ensure_model_loaded_async()
            if not model_loaded:
                error_msg = "[ERROR] Модель не загружена. Попробуйте через несколько секунд."
                logger.error("❌ Модель не загружена перед генерацией!")
                yield error_msg
                return
            
            # Дополнительная проверка: модель должна существовать
            if not self.model or not self.is_model_loaded():
                error_msg = "[ERROR] Модель недоступна. Система перезагружается."
                logger.error("❌ Модель недоступна: model=%s, loaded=%s", self.model is not None, self.is_model_loaded())
                yield error_msg
                return
            
            await self._ensure_batch_for_prompt(len(request.prompt))
            self._ensure_semaphore()

            allowed_max = self._compute_max_gen_tokens(request.prompt, request.max_tokens)
            # Ограничиваем max_tokens для баланса скорости и качества (максимум 4000)
            allowed_max = min(allowed_max, 4000)
            loop = asyncio.get_running_loop()
            q: asyncio.Queue = asyncio.Queue()
            stop_event = threading.Event()

            stop_tokens = getattr(settings, "VISTRAL_STOP_TOKENS", "")
            if stop_tokens == "":
                stop_tokens = None
            repeat_penalty = getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1)

            def worker():
                try:
                    # КРИТИЧЕСКАЯ ПРОВЕРКА перед генерацией
                    if not self.model:
                        logger.error("❌ Model is None in worker thread!")
                        loop.call_soon_threadsafe(q.put_nowait, "[ERROR] Модель не загружена. Попробуйте позже.")
                        return
                    
                    if not hasattr(self.model, 'create_chat_completion'):
                        logger.error("❌ Model has no create_chat_completion method!")
                        loop.call_soon_threadsafe(q.put_nowait, "[ERROR] Модель не поддерживает генерацию.")
                        return
                    
                    logger.info(f"🚀 Starting model generation with prompt: {request.prompt[:100]}...")
                    logger.info(f"📊 Model settings: max_tokens={allowed_max}, temperature={request.temperature}, top_p={request.top_p}")
                    logger.info(f"✅ Model check: model={self.model is not None}, type={type(self.model)}")
                    
                    chunk_count = 0
                    
                    # Используем оптимизированные настройки из стабильной версии GitHub
                    # Ограничиваем max_tokens для ускорения (как в стабильной версии)
                    optimized_max_tokens = min(allowed_max, 4000)  # Ограничение как в стабильной версии
                    
                    # Используем параметры из запроса БЕЗ ограничений
                    # Параметры уже настроены в CHAT_MODE_CONFIG для каждого режима (basic/expert)
                    # Не ограничиваем top_p, чтобы сохранить различия между режимами
                    generation_params = {
                        "max_tokens": optimized_max_tokens,
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "stream": True
                    }

                    acceleration_enabled = (not request.context or not request.context.strip()) and len(self._active_requests) <= 1
                    if acceleration_enabled:
                        fast_token_limit = min(1500, generation_params["max_tokens"])
                        generation_params["max_tokens"] = fast_token_limit
                        generation_params["top_p"] = max(0.5, generation_params["top_p"] - 0.15)
                        logger.info("⚡ Fast-start режим активирован: max_tokens=%s, top_p=%s", fast_token_limit, generation_params["top_p"])

                    # Добавляем только необходимые параметры
                    if stop_tokens:
                        generation_params["stop"] = stop_tokens
                    
                    logger.info(f"🔧 Using optimized generation params: {generation_params}")
                    
                    start_time = time.time()
                    first_token_time = [None]  # Используем список для изменения из вложенных функций
                    timeout_triggered = [False]  # Флаг таймаута
                    accumulated_text = ""  # Накопленный текст для двухфазной генерации
                    quick_response_sent = [False]  # Флаг отправки быстрого ответа
                    QUICK_RESPONSE_THRESHOLD = 256  # Порог для быстрого ответа (примерно 200-300 символов)
                    
                    # Используем create_chat_completion (как в стабильной версии на GitHub)
                    logger.info(f"🔧 Calling create_chat_completion with params: {generation_params}")
                    try:
                        stream_iter = self.model.create_chat_completion(
                            messages=[
                                {"role": "user", "content": request.prompt},
                            ],
                            stream=True,
                            **{k: v for k, v in generation_params.items() if k != "stream"}
                        )
                        logger.info(f"✅ create_chat_completion returned iterator: {stream_iter is not None}")
                    except Exception as e:
                        logger.error(f"❌ Error calling create_chat_completion: {e}", exc_info=True)
                        loop.call_soon_threadsafe(q.put_nowait, f"[ERROR] Ошибка запуска генерации: {str(e)}")
                        return
                    
                    # Реальный watchdog с использованием stop_event для остановки генерации
                    FIRST_TOKEN_TIMEOUT = 25  # Таймаут для первого токена (25 секунд)
                    
                    # Запускаем watchdog в отдельном потоке для проверки таймаута
                    def watchdog():
                        while not stop_event.is_set() and first_token_time[0] is None:
                            time.sleep(1.0)  # Проверяем каждую секунду
                            elapsed = time.time() - start_time
                            if elapsed > FIRST_TOKEN_TIMEOUT:
                                logger.error(f"❌ FIRST TOKEN TIMEOUT after {FIRST_TOKEN_TIMEOUT}s! Stopping generation...")
                                timeout_triggered[0] = True
                                stop_event.set()  # Устанавливаем флаг остановки
                                loop.call_soon_threadsafe(q.put_nowait, f"[TIMEOUT] Первый токен не был сгенерирован за {FIRST_TOKEN_TIMEOUT} секунд. Попробуйте сократить вопрос или историю.")
                                break
                    
                    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
                    watchdog_thread.start()
                    
                    logger.info("🔄 Starting iteration over stream_iter...")
                    logger.info(f"🔍 stream_iter type: {type(stream_iter)}, is iterable: {hasattr(stream_iter, '__iter__')}")
                    
                    iteration_started = False
                    for chunk in stream_iter:
                        if not iteration_started:
                            iteration_started = True
                            elapsed_iter = time.time() - start_time
                            logger.info(f"✅ First iteration started after {elapsed_iter:.2f}s - chunk type: {type(chunk)}")
                        # Проверяем флаг остановки перед обработкой каждого чанка
                        if stop_event.is_set():
                            logger.warning("🛑 Generation stopped by watchdog")
                            break
                        
                        elapsed = time.time() - start_time
                        chunk_count += 1
                        
                        # Логируем каждый чанк для диагностики (первые 10, затем каждые 50)
                        if chunk_count <= 10 or chunk_count % 50 == 0:
                            logger.info(f"🔍 Received chunk {chunk_count}: has_chunk={bool(chunk)}, elapsed={elapsed:.2f}s")
                        
                        # Дополнительная проверка - если прошло много времени без чанков
                        if chunk_count > 10 and elapsed > 120:  # 2 минуты
                            logger.warning(f"⚠️ Generation taking too long: {chunk_count} chunks in {elapsed:.2f}s")
                        
                        if not chunk:
                            if chunk_count <= 10:
                                logger.warning(f"⚠️ Chunk {chunk_count} is empty/None")
                            continue
                        
                        choices = chunk.get("choices") or []
                        if not choices:
                            if chunk_count <= 10:
                                logger.warning(f"⚠️ Chunk {chunk_count} has no choices: chunk={chunk}")
                            continue
                        
                        # Отслеживаем время первого токена для диагностики (после получения)
                        if chunk_count == 1 and first_token_time[0] is None:
                            first_token_time[0] = elapsed
                            logger.info(f"⚡ First token generated in {first_token_time[0]:.2f}s")
                            # НЕ останавливаем генерацию - только фиксируем время первого токена
                            # Watchdog сам остановится, когда увидит, что first_token_time[0] не None
                        
                        # Поддержка chat-стрима (delta.content) и text-стрима (text)
                        delta = (
                            choices[0].get("delta", {}).get("content")  # Chat completion
                            or choices[0].get("text", "")  # Fallback для прямого вызова
                        )
                        if delta:
                            # Отправляем токен только если не было таймаута
                            if not timeout_triggered[0]:
                                loop.call_soon_threadsafe(q.put_nowait, delta)
                                # Логируем только первые несколько чанков для диагностики
                                if chunk_count <= 3:
                                    logger.info(f"📤 Chunk {chunk_count} sent: {delta[:50]}...")
                                
                                # Двухфазная генерация: отслеживаем накопленный текст
                                accumulated_text += delta
                                # Примерно 1 токен ≈ 0.75 символа, поэтому 256 токенов ≈ 200 символов
                                # Отправляем маркер быстрого ответа после ~200 символов
                                if not quick_response_sent[0] and len(accumulated_text) >= 200:
                                    quick_response_sent[0] = True
                                    # Отправляем специальный маркер как отдельное событие (не часть текста)
                                    # Используем специальный префикс, который будет отфильтрован в chat.py
                                    loop.call_soon_threadsafe(q.put_nowait, "__QUICK_RESPONSE_READY__")
                                    logger.info(f"✅ Quick response ready after {len(accumulated_text)} characters ({chunk_count} chunks)")
                        else:
                            # Логируем пустые чанки для диагностики
                            if chunk_count <= 5:
                                logger.warning(f"⚠️ Chunk {chunk_count} has no delta: choices={choices[0] if choices else 'empty'}")
                        
                        # Проверка таймаута каждые 10 чанков для более быстрого обнаружения проблем
                        if chunk_count > 0 and chunk_count % 10 == 0:
                            if elapsed > self._inference_timeout:
                                logger.error(f"❌ MODEL GENERATION TIMEOUT after {self._inference_timeout}s! Force stopping...")
                                stop_event.set()
                                loop.call_soon_threadsafe(q.put_nowait, f"[TIMEOUT] Model generation exceeded {self._inference_timeout} seconds")
                                break
                    
                    # Логируем завершение цикла генерации
                    logger.info(f"✅ Stream iteration loop completed. Processed {chunk_count} chunks")
                    
                    elapsed_time = time.time() - start_time
                    first_token_str = f"{first_token_time[0]:.2f}s" if first_token_time[0] else "N/A"
                    logger.info(f"🏁 Model generation completed. Total chunks: {chunk_count}, Time: {elapsed_time:.2f}s, First token: {first_token_str}")
                    if chunk_count == 0:
                        logger.warning("⚠️ No chunks received from model!")
                    elif chunk_count == 1:
                        logger.warning("⚠️ Only 1 chunk received - generation may have stopped early")
                    loop.call_soon_threadsafe(q.put_nowait, None)
                except Exception as e:
                    logger.exception("❌ Ошибка в streaming worker: %s", e)
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
                
        except Exception as e:
            logger.error(f"❌ Critical error in streaming: {e}")
            # Отправляем ошибку клиенту
            yield f"[ERROR] Произошла ошибка генерации: {str(e)}"
            return

    def _prepare_prompt(self, question: str, context: Optional[str] = None, chat_mode: str = "basic") -> str:
        """Подготавливает промпт для юридических вопросов"""
        return self.create_legal_prompt(question, context, chat_mode)

    def create_legal_prompt(self, question: str, context: Optional[str] = None, chat_mode: str = "basic") -> str:
        """Создание промпта для юридических вопросов с поддержкой режимов (оптимизированная версия)"""
        # Упрощенный системный промпт: 1-2 предложения вместо длинных списков
        if chat_mode == "expert":
            system_prompt = "Ты опытный юрист-консультант по российскому законодательству. Отвечай профессионально со ссылками на нормы права."
        else:  # basic
            system_prompt = "Ты юрист-консультант по российскому законодательству. Объясняй просто и понятно."
        
        # Компактный формат истории без заголовков и разделителей
        history_part = ""
        if context and context.strip():
            # История уже приходит в формате "Пользователь: ... / Ассистент: ..."
            # Просто добавляем её без дополнительных блоков
            history_part = context.strip() + "\n\n"
        
        # Минималистичный промпт без лишних разделителей
        if history_part:
            prompt = f"{system_prompt}\n\n{history_part}Пользователь: {question}\n\nАссистент:"
        else:
            prompt = f"{system_prompt}\n\nПользователь: {question}\n\nАссистент:"
        
        return prompt

    async def get_queue_position(self, request_id: str) -> int:
        """Возвращает позицию запроса в очереди"""
        # Простая реализация - возвращаем размер очереди
        return self._request_queue.qsize()

    async def health_check(self) -> ServiceHealth:
        """Проверка здоровья сервиса"""
        current_time = datetime.now()
        
        # Определяем статус
        status = "healthy"
        if not self.is_model_loaded():
            status = "unhealthy"
        elif self._stats["error_rate"] > 0.1:  # Более 10% ошибок
            status = "degraded"
        elif len(self._active_requests) >= self._max_concurrency:
            status = "degraded"
        
        return ServiceHealth(
            status=status,
            last_check=current_time,
            response_time=self._stats["last_response_time"],
            error_rate=self._stats["error_rate"],
            memory_usage=self._stats["memory_usage_mb"],
            cpu_usage=self._stats["cpu_usage_percent"],
            queue_length=self._request_queue.qsize(),
            active_requests=len(self._active_requests)
        )

    def get_metrics(self) -> LLMMetrics:
        """Возвращает метрики производительности"""
        return LLMMetrics(
            requests_per_minute=self._stats["requests_per_minute"],
            average_response_time=self._stats["average_response_time"],
            p95_response_time=self._stats["p95_response_time"],
            error_rate=self._stats["error_rate"],
            queue_length=self._request_queue.qsize(),
            concurrent_requests=len(self._active_requests),
            memory_usage_mb=self._stats["memory_usage_mb"],
            cpu_usage_percent=self._stats["cpu_usage_percent"],
            total_requests=self._stats["total_requests"],
            successful_requests=self._stats["successful_requests"],
            failed_requests=self._stats["failed_requests"]
        )

    def is_model_loaded(self) -> bool:
        """Проверяет, загружена ли модель"""
        return self._model_loaded and self.model is not None

    # Совместимость с API: простой индикатор готовности
    def is_model_ready(self) -> bool:
        """Возвращает True, если модель загружена и готова к обслуживанию запросов."""
        return self.is_model_loaded()

    async def get_model_status(self) -> dict:
        """Краткий статус модели для проверок в API."""
        return {
            "model_loaded": self.is_model_loaded(),
            "active_requests": len(self._active_requests),
            "max_concurrency": self._max_concurrency,
        }

    async def _update_metrics_periodically(self):
        """Периодически обновляет метрики"""
        while not self._shutdown_requested:
            try:
                await self._update_metrics()
                await asyncio.sleep(30)  # Обновляем каждые 30 секунд
            except Exception as e:
                logger.error("❌ Ошибка обновления метрик: %s", e)
                await asyncio.sleep(30)

    async def _update_metrics(self):
        """Обновляет метрики производительности"""
        current_time = time.time()
        time_diff = current_time - self._last_metrics_update
        
        if time_diff > 0:
            # Обновляем requests per minute
            recent_requests = len([r for r in self._request_history 
                                 if current_time - r.processing_time < 60])
            self._stats["requests_per_minute"] = recent_requests
            
            # Обновляем error rate
            if self._stats["total_requests"] > 0:
                self._stats["error_rate"] = self._stats["failed_requests"] / self._stats["total_requests"]
            
            # Обновляем P95 response time
            if self._response_times:
                sorted_times = sorted(self._response_times)
                p95_index = int(len(sorted_times) * 0.95)
                self._stats["p95_response_time"] = sorted_times[p95_index] if p95_index < len(sorted_times) else 0
            
            # Обновляем системные метрики (заглушка)
            try:
                import psutil
                process = psutil.Process()
                self._stats["memory_usage_mb"] = process.memory_info().rss / 1024 / 1024
                self._stats["cpu_usage_percent"] = process.cpu_percent()
            except ImportError:
                pass
        
        self._last_metrics_update = current_time

    def _add_to_history(self, response: LLMResponse):
        """Добавляет ответ в историю"""
        self._request_history.append(response)
        
        # Ограничиваем размер истории
        if len(self._request_history) > self._max_history:
            self._request_history = self._request_history[-self._max_history:]
        
        # Обновляем список времен ответов
        self._response_times.append(response.processing_time)
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]

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

    async def graceful_shutdown(self):
        """Graceful shutdown сервиса"""
        logger.info("🔄 Начинаем graceful shutdown UnifiedLLMService...")
        
        self._shutdown_requested = True
        
        # Ждем завершения активных запросов (максимум 30 секунд)
        shutdown_timeout = 30
        start_time = time.time()
        
        while self._active_requests and (time.time() - start_time) < shutdown_timeout:
            logger.info("⏳ Ждем завершения %d активных запросов...", len(self._active_requests))
            await asyncio.sleep(1)
        
        # Отменяем фоновые задачи
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ UnifiedLLMService успешно остановлен")


# Глобальный экземпляр сервиса
unified_llm_service = UnifiedLLMService()