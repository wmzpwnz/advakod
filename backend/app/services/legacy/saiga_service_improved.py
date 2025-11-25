import logging
import time
import threading
import asyncio
from typing import Optional, AsyncGenerator, Any
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
        # заменим переносы и лишние пробелы
        return s.replace("\n", " ")
    return (s[:max_len//2] + " ... " + s[-max_len//2:]).replace("\n", " ")


def _estimate_tokens(text: str) -> int:
    """Приблизительная оценка токенов: 1 токен ≈ 3-4 символа.
       Для точности вместо этого используйте tiktoken или тот токенизатор,
       который совместим с вашей моделью, если он есть.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class SaigaService:
    def __init__(self):
        self.model: Optional[Llama] = None
        self._model_loaded: bool = False
        # Защита от одновременной загрузки модели (thread-safe)
        self._load_lock = threading.Lock()
        # Асинхронный семафор для ограничения одновременных инференсов
        # Будет инициализирован лениво при первом вызове ensure_settings
        self._async_semaphore: Optional[asyncio.Semaphore] = None

        # Настройки времени ожидания инференса (сек)
        self._inference_timeout = getattr(settings, "SAIGA_INFERENCE_TIMEOUT", 60)
        # Максимальная конкуренция (кол-во параллельных инференсов)
        self._max_concurrency = getattr(settings, "SAIGA_MAX_CONCURRENCY", 1)

    def _ensure_semaphore(self):
        if self._async_semaphore is None:
            # Создаём семафор в event loop при первом использовании
            try:
                loop = asyncio.get_running_loop()
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)
            except RuntimeError:
                # если мы в sync контексте, создаём обычный семафор
                self._async_semaphore = asyncio.Semaphore(self._max_concurrency)

    def _load_model(self):
        """Синхронная загрузка модели Saiga Mistral 7B.
        Блокирует поток — вызывается в отдельном потоке или под lock.
        """
        # Берём lock, чтобы только один поток загружал модель
        if self._model_loaded and self.model is not None:
            return

        with self._load_lock:
            if self._model_loaded and self.model is not None:
                return
            try:
                logger.info("Загружаем модель Saiga Mistral 7B из %s", settings.SAIGA_MODEL_PATH)
                logger.info("Параметры: n_ctx=%s, n_threads=%s", settings.SAIGA_N_CTX, settings.SAIGA_N_THREADS)

                self.model = Llama(
                    model_path=settings.SAIGA_MODEL_PATH,
                    n_ctx=settings.SAIGA_N_CTX,
                    n_threads=settings.SAIGA_N_THREADS,
                    n_gpu_layers=getattr(settings, "SAIGA_N_GPU_LAYERS", 0),
                    logits_all=False,
                    use_mmap=True,
                    use_mlock=False,
                    verbose=False  # по умолчанию - не подробный лог; переключается в настройках
                )
                self._model_loaded = True
                logger.info("✅ Модель Saiga успешно загружена")
            except Exception as e:
                logger.exception("Ошибка загрузки модели Saiga: %s", e)
                # не подавляем ошибку, чтобы вызывающий код мог её обработать
                raise

    async def ensure_model_loaded_async(self) -> None:
        """Асинхронная обёртка для загрузки модели через ThreadPool (если нужна при старте)."""
        if self._model_loaded and self.model is not None:
            return
        # Вызываем в отдельном потоке, чтобы не блокировать loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

    def ensure_model_loaded_sync(self) -> None:
        """Sync-версия для вызова из sync-кода (по возможности используйте async)."""
        if self._model_loaded and self.model is not None:
            return
        self._load_model()

    def _compute_max_gen_tokens(self, prompt: str, requested_max: int) -> int:
        """Ограничиваем max_tokens в зависимости от n_ctx и длины prompt."""
        n_ctx = getattr(settings, "SAIGA_N_CTX", 4096)
        prompt_tokens = _estimate_tokens(prompt)
        safety_margin = getattr(settings, "SAIGA_TOKEN_MARGIN", 32)
        available = max(1, n_ctx - prompt_tokens - safety_margin)
        if requested_max > available:
            logger.debug("requested_max (%s) > available (%s) -> limiting to available", requested_max, available)
            return available
        return requested_max

    async def generate_response_async(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8
    ) -> str:
        """Асинхронный интерфейс для генерации — безопасен для использования в FastAPI."""
        # Подготовка
        self._ensure_semaphore()
        await self.ensure_model_loaded_async()

        # Ограничение конкуренции
        assert self._async_semaphore is not None
        async with self._async_semaphore:
            # Проверяем max tokens относительно context window
            allowed_max = self._compute_max_gen_tokens(prompt, max_tokens)

            # Не логируем полный prompt — риски PII. Логируем редактированную версию.
            if getattr(settings, "LOG_PROMPTS", False):
                logger.info("Генерация ответа (async) prompt=%s... max_tokens=%s temp=%s", _redact_for_logs(prompt, 120), allowed_max, temperature)
            else:
                logger.info("Генерация ответа (async) max_tokens=%s temp=%s", allowed_max, temperature)

            loop = asyncio.get_running_loop()

            def _blocking_call():
                # Обёртка синхронного вызова модели
                try:
                    result = self.model(
                        prompt,
                        max_tokens=allowed_max,
                        temperature=temperature,
                        top_p=top_p,
                        stop=getattr(settings, "SAIGA_STOP_TOKENS", None),
                        repeat_penalty=getattr(settings, "SAIGA_REPEAT_PENALTY", 1.1),
                    )
                    # Обычно llama_cpp возвращает dict with choices
                    return result
                except Exception as e:
                    # пробрасываем наверх
                    logger.exception("Ошибка в blocking_call модели: %s", e)
                    raise

            try:
                # Запуск в executor с таймаутом
                result = await asyncio.wait_for(loop.run_in_executor(None, _blocking_call), timeout=self._inference_timeout)
            except asyncio.TimeoutError:
                logger.error("Inference timeout after %s seconds", self._inference_timeout)
                raise RuntimeError("Inference timeout")
            except Exception:
                raise

            try:
                text = ""
                if isinstance(result, dict) and "choices" in result and len(result["choices"]) > 0:
                    text = (result["choices"][0].get("text") or "").strip()
                else:
                    # Попробуем простой доступ, если API другой
                    text = str(result)
                logger.info("Генерация завершена (len=%s)", len(text))
                return text
            except Exception as e:
                logger.exception("Ошибка извлечения текста из результата модели: %s", e)
                raise

    # Синхронная оболочка (если код вызывает sync)
    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8
    ) -> str:
        """Sync-версия — вызывает async через asyncio.run в sync-контексте.
           Важно: вызывать её в отдельном thread, иначе может сломать event loop.
        """
        # Если модель не загружена — загружаем синхронно
        if not self._model_loaded or not self.model:
            self.ensure_model_loaded_sync()
        # Простая синхронная обёртка (не блокирует event loop если вы уже в ThreadPool)
        # Для безопасности рекомендуем вызывать generate_response_async() из async-эндпоинтов.
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop:
            # Если мы оказались в running loop -> запускаем blocking_call в executor
            # (обычно generate_response shouldn't be called inside active loop synchronously)
            fut = asyncio.run_coroutine_threadsafe(
                self.generate_response_async(prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p),
                asyncio.get_event_loop()
            )
            return fut.result()
        else:
            # Запускаем новый loop для этой корутины
            return asyncio.run(self.generate_response_async(prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p))

    async def stream_response(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        top_p: float = 0.8
    ) -> AsyncGenerator[str, None]:
        """Асинхронный стриминг-генератор. Не блокирует event loop.
           Реализован через worker-thread, который пишет токены в asyncio.Queue().
        """
        await self.ensure_model_loaded_async()
        self._ensure_semaphore()

        # ограничим токены
        allowed_max = self._compute_max_gen_tokens(prompt, max_tokens)

        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()

        stop_tokens = getattr(settings, "SAIGA_STOP_TOKENS", None)
        repeat_penalty = getattr(settings, "SAIGA_REPEAT_PENALTY", 1.1)

        def worker():
            """Worker runs in a real thread and пушит токены в asyncio.Queue через loop.call_soon_threadsafe."""
            try:
                # Вызов модели в sync-режиме с stream=True
                for chunk in self.model(
                    prompt,
                    max_tokens=allowed_max,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop_tokens,
                    repeat_penalty=repeat_penalty,
                    stream=True
                ):
                    # Ожидаем структуру chunk['choices'][0]['text'] подобную sync API
                    if not chunk:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("text", "")
                    if delta:
                        # Пушим в asyncio.Queue из потока
                        loop.call_soon_threadsafe(q.put_nowait, delta)
                # sentinel - конец
                loop.call_soon_threadsafe(q.put_nowait, None)
            except Exception as e:
                logger.exception("Ошибка в streaming worker: %s", e)
                loop.call_soon_threadsafe(q.put_nowait, f"[ERROR] {str(e)}")
                loop.call_soon_threadsafe(q.put_nowait, None)

        # Запускаем worker-поток
        t = threading.Thread(target=worker, daemon=True)
        t.start()

        # Читаем из asyncio.Queue и yield токены
        while True:
            token = await q.get()
            if token is None:
                break
            # Если пришла ошибка-подсказка, можно поднять исключение
            if isinstance(token, str) and token.startswith("[ERROR]"):
                raise RuntimeError(token)
            yield token

    def create_legal_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Создание промпта: оставляем как у вас, но НИЧЕГО не логируем и не хардкодим факты критичного характера.
           Рекомендация: фактические данные (штрафы, сроки) лучше добавлять через RAG-контекст, а не хардкодить.
        """
        # (я оставляю структуру вашего промпта, но важно проводить ревью事实 и держать этот текст в управляемом месте)
        special_instructions = ""
        question_lower = (question or "").lower()
        if "ип" in question_lower or "индивидуальный предприниматель" in question_lower:
            # Здесь рекомендуется либо ссылаться на RAG-контекст, либо хранить мелкие факты в конфигурации
            special_instructions = "\n# Инструкция: см. справочные данные в базе (не хардкодить в коде)\n"

        prompt = f"<s><system>\nТы - опытный юрист-консультант по российскому законодательству. ...\n</system>\n<user>\n{question}\n</user>\n<bot>"

        if context:
            context_section = f"\n\n=== ДОП.КОНТЕКСТ ===\n{context}\n=== КОНЕЦ ===\n\n"
            prompt = prompt.replace(f"<user>\n{question}", f"{context_section}<user>\n{question}")

        return prompt

    def is_model_loaded(self) -> bool:
        return self._model_loaded and self.model is not None


# global instance
saiga_service = SaigaService()
