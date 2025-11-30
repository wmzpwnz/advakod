from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..services.audit_service import log_chat_message
# from ..services.legacy.saiga_service import saiga_service  # Архивирован
from ..schemas.chat import (
    ChatSessionCreate, 
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatRequest,
    ChatResponse
)
from ..services.auth_service import AuthService
# Используем новый унифицированный LLM сервис
from ..services.unified_llm_service import unified_llm_service
from ..services.websocket_service import websocket_service
from ..services.token_service import token_service
from ..core.rate_limiter import user_rate_limit
from ..core.cache import cache_service, ChatCache
from ..core.config import settings

router = APIRouter()
auth_service = AuthService()

# Конфигурация режимов чата
CHAT_MODE_CONFIG = {
    "basic": {
        "temperature": 0.3,
        "top_p": 0.6,
        "max_tokens": 2000,  # Ограничено для быстрого ответа
        "description": "Простой и понятный режим"
    },
    "expert": {
        "temperature": 0.5,
        "top_p": 0.75,
        "max_tokens": 2300,  # Баланс скорости и глубины
        "description": "Профессиональный режим с терминологией"
    }
}

HISTORY_MESSAGE_LIMIT = 4

HISTORY_CHAR_LIMITS = {
    "basic": 1200,
    "expert": 1600
}

async def load_chat_history(session_id: int, chat_mode: str, db: Session, exclude_message_id: Optional[int] = None) -> str:
    """Загружает историю диалога для формирования контекста"""
    from ..models.chat import ChatMessage

    def _fetch_messages():
        query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        if exclude_message_id is not None:
            query = query.filter(ChatMessage.id != exclude_message_id)
        return query.order_by(ChatMessage.created_at.desc()).limit(HISTORY_MESSAGE_LIMIT).all()

    recent_messages = await asyncio.to_thread(_fetch_messages)
    if not recent_messages:
        return ""

    history_parts = []
    for msg in reversed(recent_messages):
        if msg.role == "user":
            history_parts.append(f"Пользователь: {msg.content}")
        elif msg.role == "assistant":
            history_parts.append(f"Ассистент: {msg.content}")

    if not history_parts:
        return ""

    history_text = "\n".join(history_parts)
    char_limit = HISTORY_CHAR_LIMITS.get(chat_mode, 1200)
    if len(history_text) > char_limit:
        history_text = history_text[-char_limit:]
        first_msg = max(history_text.find("Пользователь:"), history_text.find("Ассистент:"))
        if first_msg > 0:
            history_text = history_text[first_msg:]
    return history_text

async def get_history_with_cache(session_id: int, chat_mode: str, db: Session, context_key: str, exclude_message_id: Optional[int] = None) -> str:
    try:
        cached_context = await asyncio.wait_for(
            ChatCache.get_cached_rag_context(context_key),
            timeout=0.1
        )
        if cached_context:
            return cached_context
    except (asyncio.TimeoutError, Exception) as cache_err:
        logger.debug(f"Контекст из кеша недоступен: {cache_err}")

    history_text = await load_chat_history(session_id, chat_mode, db, exclude_message_id)
    if history_text:
        asyncio.create_task(
            ChatCache.cache_rag_context(
                context_key,
                history_text,
                ttl=settings.CACHE_TTL_AI_RESPONSE
            )
        )
    return history_text

@router.post("/sessions", response_model=ChatSessionSchema)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создание новой сессии чата"""
    # Валидация режима чата
    chat_mode = session_data.chat_mode if session_data.chat_mode in CHAT_MODE_CONFIG else 'basic'
    
    db_session = ChatSession(
        user_id=current_user.id,
        title=session_data.title,
        chat_mode=chat_mode
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/sessions", response_model=List[ChatSessionSchema])
async def get_chat_sessions(
    include_empty: bool = False,  # Параметр для включения пустых чатов
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение всех сессий чата пользователя с последними сообщениями"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()  # Сортируем по последнему обновлению (новые сверху)
    
    # Добавляем информацию о последнем сообщении для каждой сессии
    sessions_with_info = []
    for session in sessions:
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).first()
        
        if last_message:
            # Чат с сообщениями
            session.last_message_preview = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
            session.last_message_time = last_message.created_at
            session.has_messages = True
            sessions_with_info.append(session)
        else:
            # Пустой чат
            session.last_message_preview = "Новый чат"
            session.last_message_time = session.created_at
            session.has_messages = False
            
            # Включаем пустые чаты только если запрошено
            if include_empty:
                sessions_with_info.append(session)
    
    return sessions_with_info


@router.get("/sessions/{session_id}", response_model=ChatSessionSchema)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение конкретной сессии чата"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    return session


@router.put("/sessions/{session_id}", response_model=ChatSessionSchema)
async def update_chat_session(
    session_id: int,
    session_data: ChatSessionCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновление сессии чата (например, изменение названия или режима)"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    # Обновляем поля
    if session_data.title is not None:
        session.title = session_data.title
    
    # Обновляем режим чата, если указан и валиден
    if session_data.chat_mode is not None:
        if session_data.chat_mode in CHAT_MODE_CONFIG:
            session.chat_mode = session_data.chat_mode
            logger.info(f"Режим сессии {session_id} изменен на: {session_data.chat_mode}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый режим чата. Доступные режимы: {', '.join(CHAT_MODE_CONFIG.keys())}"
            )
    
    db.commit()
    db.refresh(session)
    
    return session


@router.patch("/sessions/{session_id}/mode", response_model=ChatSessionSchema)
async def update_chat_mode(
    session_id: int,
    chat_mode: str = Query(..., description="Режим чата: 'basic' или 'expert'"),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Изменение режима чата для сессии"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    # Валидация режима
    if chat_mode not in CHAT_MODE_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый режим чата. Доступные режимы: {', '.join(CHAT_MODE_CONFIG.keys())}"
        )
    
    # Обновляем режим
    old_mode = getattr(session, 'chat_mode', 'basic')
    session.chat_mode = chat_mode
    db.commit()
    db.refresh(session)
    
    logger.info(f"Режим сессии {session_id} изменен с {old_mode} на {chat_mode} пользователем {current_user.id}")
    
    return session


@router.post("/message", response_model=ChatResponse)
@user_rate_limit("chat")
async def send_message(
    chat_request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отправка сообщения в чат"""
    start_time = time.time()
    
    # ЛОГИРОВАНИЕ для отладки
    logger.info(f"Получен запрос на отправку сообщения от пользователя {current_user.id}")
    logger.info(f"Данные запроса: message='{chat_request.message[:100]}...', session_id={chat_request.session_id}")
    
    # Получаем или создаем сессию
    if chat_request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == chat_request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия чата не найдена"
            )
        
        # Обновляем режим сессии, если указан
        if chat_request.set_chat_mode and chat_request.set_chat_mode in CHAT_MODE_CONFIG:
            session.chat_mode = chat_request.set_chat_mode
            db.commit()
            db.refresh(session)
            logger.info(f"Режим сессии {session.id} изменен на: {chat_request.set_chat_mode}")
    else:
        # Создаем новую сессию
        chat_mode = chat_request.set_chat_mode if chat_request.set_chat_mode in CHAT_MODE_CONFIG else 'basic'
        session = ChatSession(
            user_id=current_user.id,
            title="Новый чат",
            chat_mode=chat_mode
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Получаем режим чата из сессии (с fallback на 'basic' для старых сессий)
    chat_mode = getattr(session, 'chat_mode', 'basic')
    if chat_mode not in CHAT_MODE_CONFIG:
        chat_mode = 'basic'
    config = CHAT_MODE_CONFIG[chat_mode]
    logger.info(f"Используется режим чата: {chat_mode} для сессии {session.id}")
    normalized_question = " ".join(chat_request.message.strip().lower().split())
    
    # Сохраняем сообщение пользователя
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Логируем отправку сообщения
    log_chat_message(
        db=db,
        user=current_user,
        message_id=str(user_message.id),
        request=http_request
    )
    
    try:
        logger.info(f"Обрабатываем сообщение от пользователя {current_user.id}: {chat_request.message}")
        # Быстрый ответ для простых приветствий без обращения к ИИ
        message_text_lower = (chat_request.message or "").strip().lower()
        greetings = {"привет", "здравствуйте", "добрый день", "добрый вечер", "hello", "hi"}
        if any(message_text_lower == g or message_text_lower.startswith(g + ",") for g in greetings):
            response_text = (
                "Здравствуйте! Я ваш ИИ‑юрист по российскому праву. Задайте, пожалуйста, конкретный вопрос "
                "(например: 'как оформить договор аренды помещения?' или 'сроки исковой давности по ДТП?'), "
                "и я отвечу подробно со ссылками на нормы."
            )
            actual_cost = 5
            sources = [{"title": "Система", "text": "Приветствие без вызова модели"}]
            processing_time = time.time() - start_time
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=response_text,
                message_metadata={
                    "sources": sources,
                    "processing_time": processing_time,
                    "context_used": False,  # Для приветствия контекст не используется
                    "tokens_cost": actual_cost
                }
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            try:
                await websocket_service.notify_new_message(assistant_message, session.id)
            except Exception as ws_error:
                logger.error(f"Failed to send WebSocket notification: {ws_error}")
            return ChatResponse(
                message=response_text,
                session_id=session.id,
                message_id=assistant_message.id,
                sources=sources,
                processing_time=processing_time
            )
        
        # Проверка на вопросы о создателе/модели
        creator_questions = {
            "кто тебя создал", "кто создал", "кто твой создатель", "кто разработал",
            "что ты такое", "кто ты", "расскажи о себе", "что ты за модель",
            "кто тебя сделал", "кто твой разработчик", "кто тебя придумал",
            "что такое адвакодекс", "что такое advacodex", "расскажи про адвакодекс",
            "кто создал адвакодекс", "кто создал advacodex"
        }
        
        if any(keyword in message_text_lower for keyword in creator_questions):
            response_text = (
                "Меня создала команда Advacodex (Адвакодекс) под руководством Азиза Багбекова. "
                "Я - специализированный ИИ-юрист, разработанный для помощи в вопросах российского законодательства. "
                "Моя задача - предоставлять профессиональные консультации со ссылками на нормы права и помогать пользователям "
                "разбираться в различных аспектах российского законодательства. Advacodex - это платформа для юридических консультаций "
                "с использованием искусственного интеллекта."
            )
            actual_cost = 5
            sources = [{"title": "Система", "text": "Информация о создателе без вызова модели"}]
            processing_time = time.time() - start_time
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=response_text,
                message_metadata={
                    "sources": sources,
                    "processing_time": processing_time,
                    "context_used": False,
                    "tokens_cost": actual_cost
                }
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            # Не отправляем через WebSocket, так как ответ уже возвращается через HTTP
            # Фронтенд получит ответ через HTTP и отобразит его
            return ChatResponse(
                message=response_text,
                session_id=session.id,
                message_id=assistant_message.id,
                sources=sources,
                processing_time=processing_time
            )
        
        # Получаем историю чата для контекста (подготовка параллельно)
        chat_history = ""
        context_used = False
        prompt = None
        history_task: Optional[asyncio.Task] = None
        context_key = f"session_{session.id}_context"

        try:
            cached_prompt_data = await ChatCache.get_cached_prompt(session.id)
        except Exception as prompt_cache_err:
            logger.debug(f"Кеш промпта недоступен: {prompt_cache_err}")
            cached_prompt_data = None

        if cached_prompt_data and cached_prompt_data.get("question") == normalized_question:
            prompt = cached_prompt_data.get("prompt")
            chat_history = cached_prompt_data.get("history", "")
            context_used = bool(chat_history)
            logger.info(f"✅ Промпт найден в кеше для сессии {session.id}")
        else:
            history_task = asyncio.create_task(
                get_history_with_cache(
                    session.id,
                    chat_mode,
                    db,
                    context_key,
                    user_message.id
                )
            )

        # Проверяем баланс токенов (мягкая проверка)
        estimated_cost = 150  # Примерная стоимость запроса
        current_balance = token_service.get_user_balance(db, current_user.id)
        logger.info(f"Баланс пользователя {current_user.id}: {current_balance} токенов, требуется: {estimated_cost}")
        
        if current_balance < estimated_cost:
            logger.warning(f"Недостаточно токенов у пользователя {current_user.id}: {current_balance} < {estimated_cost}")
            # Не блокируем запрос, просто предупреждаем
        
        # Используем Vistral-24B модель через unified_llm_service
        logger.info("Используем Vistral-24B модель через unified_llm_service")
        
        # ДОБАВЛЕНО: Кэширование ответов AI
        # Нормализуем вопрос для кэша (убираем лишние пробелы, приводим к нижнему регистру)
        cached_response = None
        
        # Проверяем кэш только если нет истории чата (первый вопрос в сессии)
        # Это позволяет кэшировать стандартные вопросы, но учитывать контекст в диалоге
        # Кеш учитывает режим чата для правильного ответа
        if not chat_history:
            try:
                cache_key = f"{chat_mode}:{normalized_question}"
                cached_response = await ChatCache.get_cached_ai_response(cache_key)
                if cached_response:
                    logger.info(f"✅ Найден кэшированный ответ для вопроса пользователя {current_user.id}")
                    response_text = cached_response
                    actual_cost = 5  # Минимальная стоимость за кэшированный ответ
                    sources = [{"title": "Vistral-24B (кэш)", "text": "Ответ из кэша - быстрый ответ на часто задаваемый вопрос"}]
                else:
                    logger.debug(f"Кэш промах для вопроса: {normalized_question[:50]}...")
            except Exception as cache_err:
                logger.warning(f"Ошибка при проверке кэша: {cache_err}")
                cached_response = None
        
        # Если ответ не найден в кэше, генерируем новый
        if not cached_response:
            # ДОБАВЛЕНО: Проверяем готовность модели перед генерацией
            if not unified_llm_service.is_model_ready():
                model_status = await unified_llm_service.get_model_status()
                if not model_status.get("model_loaded"):
                    logger.warning(f"AI модель не загружена для пользователя {current_user.id}")
                    response_text = "AI-консультант временно недоступен. Система находится в процессе инициализации. Пожалуйста, попробуйте через несколько минут."
                    actual_cost = 10
                    sources = [{"title": "Система", "text": "Уведомление о недоступности AI"}]
                elif model_status.get("active_requests", 0) >= model_status.get("max_concurrency", 1):
                    logger.warning(f"Система перегружена для пользователя {current_user.id}")
                    response_text = "Система временно перегружена. Пожалуйста, попробуйте через несколько секунд."
                    actual_cost = 10
                    sources = [{"title": "Система", "text": "Уведомление о перегрузке"}]
                else:
                    logger.warning(f"AI модель не готова для пользователя {current_user.id}: {model_status}")
                    response_text = "AI-консультант временно недоступен. Попробуйте позже."
                    actual_cost = 10
                    sources = [{"title": "Система", "text": "Уведомление о недоступности"}]
            else:
                try:
                    if prompt is None:
                        if history_task:
                            try:
                                chat_history = await asyncio.wait_for(history_task, timeout=0.5)
                            except asyncio.TimeoutError:
                                logger.warning("Таймаут подготовки истории, продолжаем без контекста")
                                chat_history = ""
                            except Exception as history_err:
                                logger.warning(f"Ошибка подготовки истории: {history_err}")
                                chat_history = ""
                            finally:
                                history_task = None
                        context_used = bool(chat_history)
                        prompt = unified_llm_service.create_legal_prompt(
                            question=chat_request.message,
                            context=chat_history,
                            chat_mode=chat_mode
                        )
                        asyncio.create_task(
                            ChatCache.cache_prompt(
                                session.id,
                                {"question": normalized_question, "prompt": prompt, "history": chat_history},
                                ttl=settings.CACHE_TTL_AI_RESPONSE
                            )
                        )
                    logger.info(f"Вызываем unified_llm_service.generate_response с промптом (режим: {chat_mode}): {prompt[:100]}...")
                    
                    # Генерируем с параметрами из конфигурации режима
                    response_text = await asyncio.wait_for(
                        unified_llm_service._generate_response_internal(
                            prompt=prompt,
                            max_tokens=config["max_tokens"],
                            temperature=config["temperature"],
                            top_p=config["top_p"]
                        ),
                        timeout=settings.AI_CHAT_RESPONSE_TIMEOUT
                    )
                    
                    # ДОБАВЛЕНО: Проверяем качество ответа
                    if not response_text or response_text.startswith("[ERROR]") or response_text.startswith("[TIMEOUT]") or response_text.startswith("[СИСТЕМА]"):
                        if response_text.startswith("[TIMEOUT]"):
                            logger.warning(f"⚠️ AI чат превысил таймаут для пользователя {current_user.id}")
                            response_text = "Извините, обработка вашего запроса заняла слишком много времени. Попробуйте переформулировать вопрос более кратко или разбить его на несколько простых вопросов."
                            actual_cost = 30
                            sources = [{"title": "AI Lawyer (Timeout)", "text": "Ответ при превышении времени обработки"}]
                        elif response_text.startswith("[ERROR]"):
                            logger.error(f"❌ AI ошибка для пользователя {current_user.id}: {response_text}")
                            response_text = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте переформулировать вопрос или обратитесь к юристу для получения надежной консультации."
                            actual_cost = 30
                            sources = [{"title": "AI Lawyer (Error)", "text": "Ответ при ошибке обработки"}]
                        elif response_text.startswith("[СИСТЕМА]"):
                            # Системный fallback ответ уже готов
                            actual_cost = 20
                            sources = [{"title": "Система", "text": "Системное уведомление"}]
                        else:
                            logger.error(f"❌ Пустой ответ от AI для пользователя {current_user.id}")
                            response_text = "Не удалось получить ответ от AI-консультанта. Попробуйте переформулировать вопрос или обратитесь к квалифицированному юристу."
                            actual_cost = 20
                            sources = [{"title": "AI Lawyer (Empty)", "text": "Ответ при пустом результате"}]
                    else:
                        logger.info(f"✅ Unified LLM сервис вернул ответ длиной: {len(response_text)} символов для пользователя {current_user.id}")
                        actual_cost = min(len(response_text) // 3, 200)  # Примерно 1 токен за 3 символа
                        sources = [{"title": "Vistral-24B", "text": "Ответ от русскоязычной ИИ-модели Vistral-24B"}]
                        
                        # Сохраняем в кэш только если нет истории (стандартные вопросы)
                        # и ответ успешно сгенерирован (с учетом режима)
                        if not chat_history:
                            try:
                                cache_key = f"{chat_mode}:{normalized_question}"
                                await ChatCache.cache_ai_response(
                                    cache_key, 
                                    response_text, 
                                    ttl=settings.CACHE_TTL_AI_RESPONSE
                                )
                                logger.info(f"✅ Ответ сохранен в кэш для вопроса (режим: {chat_mode}): {normalized_question[:50]}...")
                            except Exception as cache_save_err:
                                logger.warning(f"Ошибка при сохранении в кэш: {cache_save_err}")
                    
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ AI чат превысил таймаут ({settings.AI_CHAT_RESPONSE_TIMEOUT} сек) для пользователя {current_user.id}")
                    response_text = "Извините, обработка вашего запроса заняла слишком много времени. Попробуйте переформулировать вопрос более кратко."
                    actual_cost = 50
                    sources = [{"title": "AI Lawyer (Timeout)", "text": "Ответ при превышении времени обработки"}]
                except Exception as llm_err:
                    logger.error(f"❌ Ошибка в unified_llm_service для пользователя {current_user.id}: {llm_err}")
                    response_text = "Извините, произошла ошибка при обработке вашего запроса. Рекомендую обратиться к квалифицированному юристу для получения надежной консультации."
                    actual_cost = 50
                    sources = [{"title": "AI Lawyer (Error)", "text": "Ответ при ошибке обработки"}]
        
        processing_time = time.time() - start_time
        
        # Списываем токены за сообщение (если достаточно)
        if current_balance >= actual_cost:
            token_service.spend_tokens(
                db=db,
                user_id=current_user.id,
                amount=actual_cost,
                transaction_type="chat_message",
                description=f"Ответ ИИ ({len(response_text)} символов)",
                chat_session_id=session.id
            )
        else:
            logger.warning(f"Не списываем токены: недостаточно баланса ({current_balance} < {actual_cost})")
        
        # Сохраняем ответ ИИ
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            message_metadata={
                "sources": sources,
                "processing_time": processing_time,
                "context_used": context_used,
                "tokens_cost": actual_cost
            }
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # ИНВАЛИДИРУЕМ кеш контекста после сохранения ответа
        # Это гарантирует, что следующий запрос загрузит актуальную историю из БД
        try:
            context_key = f"session_{session.id}_context"
            # Используем delete из cache_service напрямую
            await cache_service.delete(context_key)
            logger.debug(f"Кеш контекста инвалидирован для сессии {session.id} после сохранения ответа")
        except Exception as cache_invalidate_err:
            logger.warning(f"Ошибка инвалидации кеша контекста: {cache_invalidate_err}")
        
        # Отправляем уведомление через WebSocket
        try:
            await websocket_service.notify_new_message(assistant_message, session.id)
            logger.info(f"WebSocket notification sent for message {assistant_message.id}")
        except Exception as ws_error:
            logger.error(f"Failed to send WebSocket notification: {ws_error}")
        
        return ChatResponse(
            message=response_text,
            session_id=session.id,
            message_id=assistant_message.id,
            sources=sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        # В случае ошибки сохраняем сообщение об ошибке
        logger.error(f"Ошибка в chat API: {e}", exc_info=True)
        error_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
        
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=error_message,
            message_metadata={"error": str(e)}
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatResponse(
            message=error_message,
            session_id=session.id,
            message_id=assistant_message.id,
            processing_time=time.time() - start_time
        )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
async def get_chat_messages(
    session_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение сообщений сессии чата"""
    # Проверяем, что сессия принадлежит пользователю
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        logger.warning(f"User {current_user.id} ({current_user.email}) tried to access non-existent session {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return messages


@router.delete("/sessions/all")
async def delete_all_chat_sessions(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удаление всех сессий чата пользователя"""
    try:
        from ..models import TokenTransaction, ChatMessage
        
        # Получаем все сессии пользователя
        user_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).all()
        
        if not user_sessions:
            return {"message": "Нет сессий для удаления", "deleted_count": 0}
        
        session_ids = [session.id for session in user_sessions]
        
        # 1) Отвязываем транзакции токенов от всех сессий
        db.query(TokenTransaction).filter(
            TokenTransaction.chat_session_id.in_(session_ids)
        ).update({TokenTransaction.chat_session_id: None}, synchronize_session=False)
        
        # 2) Удаляем все сообщения всех сессий
        db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(session_ids)
        ).delete(synchronize_session=False)
        
        # 3) Удаляем все сессии
        deleted_count = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).delete(synchronize_session=False)
        
        db.commit()
        logger.info(f"Пользователь {current_user.id} удалил все свои чаты ({deleted_count} сессий)")
        return {"message": "Все сессии чата удалены", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления всех сессий пользователя {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении всех сессий"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удаление сессии чата"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    # Мягкая очистка связанных сущностей, чтобы не нарушать внешние ключи
    try:
        # 1) Отвязываем транзакции токенов от сессии
        from ..models import TokenTransaction, ChatMessage
        db.query(TokenTransaction).filter(
            TokenTransaction.chat_session_id == session_id
        ).update({TokenTransaction.chat_session_id: None})
        
        # 2) Удаляем сообщения сессии
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete(synchronize_session=False)
        
        # 3) Удаляем саму сессию
        db.delete(session)
        db.commit()
        return {"message": "Сессия чата удалена"}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления сессии {session_id}: {e}", exc_info=True)
        # Возвращаем 409, чтобы фронтенд не зациклевал попытки
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Сессию нельзя удалить из-за связанных записей"
        )


@router.post("/message/stream")
@user_rate_limit("chat")
async def send_message_stream(
    chat_request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отправка сообщения в чат с стримингом ответа"""
    start_time = time.time()
    
    # Получаем или создаем сессию
    if chat_request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == chat_request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия чата не найдена"
            )
        
        # Обновляем режим сессии, если указан
        if chat_request.set_chat_mode and chat_request.set_chat_mode in CHAT_MODE_CONFIG:
            session.chat_mode = chat_request.set_chat_mode
            db.commit()
            db.refresh(session)
            logger.info(f"Режим сессии {session.id} изменен на: {chat_request.set_chat_mode}")
    else:
        # Создаем новую сессию
        chat_mode = chat_request.set_chat_mode if chat_request.set_chat_mode in CHAT_MODE_CONFIG else 'basic'
        session = ChatSession(
            user_id=current_user.id,
            title="Новый чат",
            chat_mode=chat_mode
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Получаем режим чата из сессии (с fallback на 'basic' для старых сессий)
    chat_mode = getattr(session, 'chat_mode', 'basic')
    if chat_mode not in CHAT_MODE_CONFIG:
        chat_mode = 'basic'
    config = CHAT_MODE_CONFIG[chat_mode]
    logger.info(f"Используется режим чата: {chat_mode} для сессии {session.id} (streaming)")
    normalized_question = " ".join(chat_request.message.strip().lower().split())
    context_key = f"session_{session.id}_context"
    
    # Сохраняем сообщение пользователя
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    
    # Проверка на вопросы о создателе/модели (для streaming)
    message_text_lower = (chat_request.message or "").strip().lower()
    creator_questions = {
        "кто тебя создал", "кто создал", "кто твой создатель", "кто разработал",
        "что ты такое", "кто ты", "расскажи о себе", "что ты за модель",
        "кто тебя сделал", "кто твой разработчик", "кто тебя придумал",
        "что такое адвакодекс", "что такое advacodex", "расскажи про адвакодекс",
        "кто создал адвакодекс", "кто создал advacodex"
    }
    
    if any(keyword in message_text_lower for keyword in creator_questions):
        response_text = (
            "Меня создала команда Advacodex (Адвакодекс) под руководством Азиза Багбекова. "
            "Я - специализированный ИИ-юрист, разработанный для помощи в вопросах российского законодательства. "
            "Моя задача - предоставлять профессиональные консультации со ссылками на нормы права и помогать пользователям "
            "разбираться в различных аспектах российского законодательства. Advacodex - это платформа для юридических консультаций "
            "с использованием искусственного интеллекта."
        )
        actual_cost = 5
        sources = [{"title": "Система", "text": "Информация о создателе без вызова модели"}]
        processing_time = time.time() - start_time
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            message_metadata={
                "sources": sources,
                "processing_time": processing_time,
                "context_used": False,
                "tokens_cost": actual_cost
            }
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        # Не отправляем через WebSocket для streaming, так как ответ уже отправляется через SSE
        # Для streaming возвращаем ответ как один чанк
        async def quick_response_stream():
            yield f"data: {json.dumps({'type': 'start', 'session_id': session.id, 'message_id': assistant_message.id})}\n\n"
            yield f"data: {json.dumps({'type': 'chunk', 'content': response_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'session_id': session.id, 'message_id': assistant_message.id})}\n\n"
        
        return StreamingResponse(quick_response_stream(), media_type="text/event-stream")
    
    async def generate_stream():
        try:
            # Определяем context_key внутри функции для доступа
            stream_context_key = f"session_{session.id}_context"
            
            # Отправляем начальную информацию СРАЗУ (не ждем загрузки истории)
            yield f"data: {json.dumps({'type': 'start', 'session_id': session.id, 'message_id': user_message.id})}\n\n"
            
            # Загружаем историю БЫСТРО перед началом стриминга (с коротким таймаутом)
            # Это нужно для понимания контекста, но не должно сильно замедлять
            chat_history = ""
            context_used = False
            prompt = None
            history_task: Optional[asyncio.Task] = None
            
            try:
                cached_prompt_data = await ChatCache.get_cached_prompt(session.id)
            except Exception as prompt_cache_err:
                logger.debug(f"Кеш промпта недоступен: {prompt_cache_err}")
                cached_prompt_data = None
            
            if cached_prompt_data and cached_prompt_data.get("question") == normalized_question:
                prompt = cached_prompt_data.get("prompt")
                chat_history = cached_prompt_data.get("history", "")
                context_used = bool(chat_history)
                logger.info(f"✅ Промпт найден в кеше (streaming) для сессии {session.id}")
            else:
                history_task = asyncio.create_task(
                    get_history_with_cache(
                        session.id,
                        chat_mode,
                        db,
                        stream_context_key,
                        user_message.id
                    )
                )
            
            # Используем Vistral-24B модель для стриминга через unified_llm_service
            # Используем Vistral-24B модель для стриминга через unified_llm_service
            full_response = ""
            sources = [{"title": "Vistral-24B", "text": "Ответ от русскоязычной ИИ-модели Vistral-24B"}]
            
            if chat_history:
                logger.info(f"Используем Vistral-24B для стриминга С КОНТЕКСТОМ ({len(chat_history)} символов истории)")
            else:
                logger.info("Используем Vistral-24B для стриминга БЕЗ истории (первое сообщение или ошибка загрузки)")
            
            try:
                if prompt is None:
                    if history_task:
                        try:
                            chat_history = await asyncio.wait_for(history_task, timeout=0.5)
                        except asyncio.TimeoutError:
                            logger.warning("Таймаут подготовки истории (streaming), продолжаем без контекста")
                            chat_history = ""
                        except Exception as history_err:
                            logger.warning(f"Ошибка подготовки истории (streaming): {history_err}")
                            chat_history = ""
                        finally:
                            history_task = None
                    context_used = bool(chat_history)
                    prompt = unified_llm_service.create_legal_prompt(
                        question=chat_request.message,
                        context=chat_history if chat_history else None,  # Используем историю если загрузилась
                        chat_mode=chat_mode
                    )
                    asyncio.create_task(
                        ChatCache.cache_prompt(
                            session.id,
                            {"question": normalized_question, "prompt": prompt, "history": chat_history},
                            ttl=settings.CACHE_TTL_AI_RESPONSE
                        )
                    )
                logger.info(f"Вызываем unified_llm_service.generate_response (stream, режим: {chat_mode}) с промптом {'С историей' if chat_history else 'БЕЗ истории'}: {prompt[:100]}...")
                chunk_sent_count = 0
                
                # Определяем приоритет: для новых пользователей (первый запрос) - высокий приоритет
                from ..services.unified_llm_service import RequestPriority
                # Проверяем количество сообщений через запрос к БД (session.message_count не существует)
                # Учитываем, что user_message уже сохранен, поэтому проверяем количество assistant сообщений
                # Первое сообщение = нет истории И нет предыдущих ответов от AI
                assistant_message_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id,
                    ChatMessage.role == "assistant"
                ).count()
                is_first_message = not chat_history and assistant_message_count == 0
                priority = RequestPriority.HIGH if is_first_message else RequestPriority.NORMAL
                if is_first_message:
                    logger.info(f"🚀 Первый запрос от нового пользователя {current_user.id}, устанавливаем высокий приоритет")
                
                async for chunk in unified_llm_service.generate_response(
                    prompt=prompt,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    top_p=config["top_p"],
                    stream=True,
                    user_id=str(current_user.id),
                    priority=priority
                ):
                    chunk_sent_count += 1
                    # Обрабатываем маркер двухфазной генерации отдельно
                    if chunk == "__QUICK_RESPONSE_READY__":
                        # Отправляем как отдельное событие SSE (не часть текста)
                        yield f"data: {json.dumps({'type': 'quick_response_ready'})}\n\n"
                        logger.info(f"✅ Отправлен маркер quick_response_ready клиенту")
                        continue
                    
                    # Обычные текстовые чанки - сохраняем и отправляем
                    full_response += chunk
                    chunk_data = f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    yield chunk_data
                    # Логируем первые 10 чанков и каждые 50 для диагностики
                    if chunk_sent_count <= 10 or chunk_sent_count % 50 == 0:
                        logger.info(f"📤 Отправлен чанк {chunk_sent_count} клиенту: {chunk[:50]}... (длина: {len(chunk)})")
                logger.info(f"✅ Unified LLM сервис завершил стриминг: отправлено {chunk_sent_count} чанков, общая длина ответа: {len(full_response)} символов")
            except Exception as e:
                # Улучшенная обработка ошибок с логированием и отправкой клиенту
                logger.error(f"Ошибка в streaming генерации ответа: {e}", exc_info=True)
                
                # Отправляем ошибку клиенту через SSE
                error_message = "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз."
                try:
                    yield f"data: {json.dumps({'type': 'error', 'content': error_message, 'error_code': 'generation_error'})}\n\n"
                except Exception as send_err:
                    logger.error(f"Не удалось отправить сообщение об ошибке клиенту: {send_err}")
                
                # Используем fallback ответ
                sources = [{"title": "Система", "text": "Ответ не может быть сгенерирован из-за технической ошибки"}]
                fallback_text = error_message
                full_response = fallback_text

            
            # Сохраняем полный ответ ИИ
            processing_time = time.time() - start_time
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_response,
                message_metadata={
                    "sources": sources,
                    "processing_time": processing_time,
                    "context_used": context_used
                }
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            # ИНВАЛИДИРУЕМ кеш контекста после сохранения ответа (для streaming)
            # Это гарантирует, что следующий запрос загрузит актуальную историю из БД
            try:
                await cache_service.delete(stream_context_key)
                logger.debug(f"Кеш контекста инвалидирован для сессии {session.id} после сохранения ответа (streaming)")
            except Exception as cache_invalidate_err:
                logger.warning(f"Ошибка инвалидации кеша контекста (streaming): {cache_invalidate_err}")
            
            # Уведомляем через WebSocket о новом сообщении (отключено для streaming API)
            # try:
            #     await websocket_service.notify_new_message(assistant_message, session.id)
            # except Exception as e:
            #     logger.error(f"Failed to send WebSocket notification: {e}")

            # Отправляем финальную информацию
            yield f"data: {json.dumps({'type': 'end', 'message_id': assistant_message.id, 'processing_time': processing_time})}\n\n"
                
        except Exception as e:
            logger.error(f"Критическая ошибка в стриминг chat API: {e}", exc_info=True)
            error_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
            
            # Сохраняем сообщение об ошибке
            try:
                assistant_message = ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=error_message,
                    message_metadata={"error": str(e), "error_type": type(e).__name__}
                )
                db.add(assistant_message)
                db.commit()
                db.refresh(assistant_message)
                message_id = assistant_message.id
            except Exception as db_err:
                logger.error(f"Не удалось сохранить сообщение об ошибке в БД: {db_err}")
                message_id = None
            
            # Отправляем ошибку клиенту
            try:
                yield f"data: {json.dumps({'type': 'error', 'content': error_message, 'message_id': message_id, 'error_code': 'critical_error'})}\n\n"
            except Exception as send_err:
                logger.error(f"Не удалось отправить сообщение об ошибке клиенту: {send_err}")
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/voice-message", response_model=ChatResponse)
@user_rate_limit("chat")
async def send_voice_message(
    audio: UploadFile = File(...),
    session_id: int = Form(None),
    duration: int = Form(...),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отправка голосового сообщения в чат"""
    start_time = time.time()
    
    # Валидация аудио файла
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть аудио"
        )
    
    # Получаем размер файла
    audio.file.seek(0, 2)  # Переходим в конец файла
    file_size = audio.file.tell()
    audio.file.seek(0)  # Возвращаемся в начало
    
    # Валидация размера аудио файла (максимум 50 МБ)
    max_audio_size = 50 * 1024 * 1024  # 50 MB
    if file_size > max_audio_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аудио файл слишком большой. Максимальный размер: {max_audio_size // (1024*1024)} МБ"
        )
    
    # Валидация имени файла
    if audio.filename:
        from ..core.validators import validate_file_upload
        from pydantic import ValidationError
        try:
            validate_file_upload(audio.filename, audio.content_type, file_size)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.detail)
            )
    
    
    # Получаем или создаем сессию
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия чата не найдена"
            )
    else:
        # Создаем новую сессию (голосовой чат использует базовый режим по умолчанию)
        session = ChatSession(
            user_id=current_user.id,
            title="Голосовой чат",
            chat_mode='basic'
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Получаем режим чата из сессии (с fallback на 'basic' для старых сессий)
    chat_mode = getattr(session, 'chat_mode', 'basic')
    if chat_mode not in CHAT_MODE_CONFIG:
        chat_mode = 'basic'
    config = CHAT_MODE_CONFIG[chat_mode]
    
    try:
        # Сохраняем аудио файл
        import os
        import uuid
        from ..core.config import settings
        
        upload_dir = settings.VOICE_UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_extension = ".webm"  # По умолчанию webm
        if audio.filename:
            # Безопасное извлечение расширения
            safe_filename = os.path.basename(audio.filename)
            _, ext = os.path.splitext(safe_filename)
            # Разрешаем только безопасные расширения
            allowed_extensions = {'.webm', '.wav', '.mp3', '.ogg', '.m4a'}
            if ext.lower() in allowed_extensions:
                file_extension = ext
        
        file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        # Создаем сообщение пользователя
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content="[Голосовое сообщение]",
            audio_url=f"/uploads/voice/{file_id}{file_extension}",
            audio_duration=duration
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Логируем отправку голосового сообщения
        log_chat_message(
            db=db,
            user=current_user,
            message_id=str(user_message.id),
            request=None  # TODO: добавить request
        )
        
        # TODO: Здесь можно добавить распознавание речи (Speech-to-Text)
        # Для демонстрации используем заглушку
        transcribed_text = "Голосовое сообщение получено. Обработка речи временно недоступна."
        
        # Генерируем ответ ИИ с учетом режима
        prompt = unified_llm_service.create_legal_prompt(transcribed_text, chat_mode=chat_mode)
        response_generator = unified_llm_service.generate_response(
            prompt=prompt,
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            stream=False
        )
        
        # Собираем ответ из генератора
        response_text = ""
        async for chunk in response_generator:
            response_text += chunk
        
        # Создаем ответ ИИ
        ai_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            metadata={
                "processing_time": time.time() - start_time,
                "voice_message": True,
                "transcribed_text": transcribed_text
            }
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        processing_time = time.time() - start_time
        
        return {
            "user_message": {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "audio_url": user_message.audio_url,
                "audio_duration": user_message.audio_duration,
                "created_at": user_message.created_at.isoformat()
            },
            "ai_message": {
                "id": ai_message.id,
                "role": ai_message.role,
                "content": ai_message.content,
                "created_at": ai_message.created_at.isoformat(),
                "metadata": ai_message.metadata
            },
            "session_id": session.id,
            "processing_time": processing_time,
            "sources": [{"title": "Saiga Mistral 7B", "text": "Ответ основан на знаниях модели Saiga Mistral 7B"}]
        }
        
    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обработки голосового сообщения"
        )
