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
    
    def _load_model(self):
        """Синхронная загрузка модели Vistral"""
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
                n_threads = getattr(settings, "VISTRAL_N_THREADS", 8)
                n_gpu_layers = getattr(settings, "VISTRAL_N_GPU_LAYERS", 0)
                
                if not model_path or not os.path.exists(model_path):
                    raise FileNotFoundError(f"Файл модели не найден: {model_path}")
                
                logger.info("🚀 Загружаем унифицированную модель Vistral из %s", model_path)
                logger.info("📊 Параметры: n_ctx=%s, n_threads=%s, max_concurrency=%s, queue_size=%s", 
                          n_ctx, n_threads, self._max_concurrency, self._queue_size)

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
                logger.info("✅ Унифицированная модель Vistral успешно загружена")
                
            except Exception as e:
                logger.exception("❌ Ошибка загрузки унифицированной модели Vistral: %s", e)
                raise

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
        request = LLMRequest(
            id=str(uuid.uuid4()),
            prompt=self._prepare_prompt(prompt, context),
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
                    result = self.model(
                        prompt,
                        max_tokens=allowed_max,
                        temperature=temperature,
                        top_p=top_p,
                        stop=getattr(settings, "VISTRAL_STOP_TOKENS", None),
                        repeat_penalty=getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1),
                    )
                    return result
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
                    text = (result["choices"][0].get("text") or "").strip()
                else:
                    text = str(result)
                
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
            await self.ensure_model_loaded_async()
            self._ensure_semaphore()

            allowed_max = self._compute_max_gen_tokens(request.prompt, request.max_tokens)
            loop = asyncio.get_running_loop()
            q: asyncio.Queue = asyncio.Queue()

            stop_tokens = getattr(settings, "VISTRAL_STOP_TOKENS", "")
            if stop_tokens == "":
                stop_tokens = None
            repeat_penalty = getattr(settings, "VISTRAL_REPEAT_PENALTY", 1.1)

            def worker():
                try:
                    logger.info(f"🚀 Starting model generation with prompt: {request.prompt[:100]}...")
                    logger.info(f"📊 Model settings: max_tokens={allowed_max}, temperature={request.temperature}, top_p={request.top_p}")
                    
                    chunk_count = 0
                    # Используем правильные настройки для Vistral 24B
                    generation_params = {
                        "max_tokens": min(allowed_max, 2000),  # Увеличиваем лимит токенов
                        "temperature": getattr(settings, "VISTRAL_TEMPERATURE", 0.3),
                        "top_p": getattr(settings, "VISTRAL_TOP_P", 0.8),
                        "stream": True
                    }
                    
                    # Добавляем только необходимые параметры
                    if stop_tokens:
                        generation_params["stop"] = stop_tokens
                    
                    logger.info(f"🔧 Using optimized generation params: {generation_params}")
                    
                    start_time = time.time()
                    for chunk in self.model(request.prompt, **generation_params):
                        # Таймаут для генерации - используем настройку из конфигурации
                        if time.time() - start_time > self._inference_timeout:
                            logger.error(f"❌ MODEL GENERATION TIMEOUT after {self._inference_timeout}s! Force stopping...")
                            loop.call_soon_threadsafe(q.put_nowait, f"[TIMEOUT] Model generation exceeded {self._inference_timeout} seconds")
                            break
                            
                        chunk_count += 1
                        if not chunk:
                            logger.warning(f"⚠️ Empty chunk #{chunk_count}")
                            continue
                        choices = chunk.get("choices") or []
                        if not choices:
                            logger.warning(f"⚠️ No choices in chunk #{chunk_count}")
                            continue
                        delta = choices[0].get("text", "")
                        if delta:
                            logger.info(f"✅ Generated token #{chunk_count}: '{delta[:50]}...'")
                            loop.call_soon_threadsafe(q.put_nowait, delta)
                        else:
                            logger.warning(f"⚠️ Empty delta in chunk #{chunk_count}")
                    
                    logger.info(f"🏁 Model generation completed. Total chunks: {chunk_count}")
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

    def _prepare_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Подготавливает промпт для юридических вопросов"""
        return self.create_legal_prompt(question, context)

    def create_legal_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Создание промпта для юридических вопросов"""
        special_instructions = ""
        question_lower = (question or "").lower()
        
        if "ип" in question_lower or "индивидуальный предприниматель" in question_lower:
            special_instructions = "\n# Инструкция: см. справочные данные в базе (не хардкодить в коде)\n"
        
        prompt = f"""Ты - опытный юрист-консультант по российскому законодательству. Отвечай на русском языке максимально подробно, точно и профессионально.

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

Вопрос: {question}

Ответ:"""
        
        if context:
            context_section = f"\n\n=== ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ ===\n{context}\n=== КОНЕЦ КОНТЕКСТА ===\n\n"
            prompt = prompt.replace(f"Вопрос: {question}", f"{context_section}Вопрос: {question}")
        
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