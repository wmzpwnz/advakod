from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
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


@router.post("/sessions", response_model=ChatSessionSchema)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создание новой сессии чата"""
    db_session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
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
    """Обновление сессии чата (например, изменение названия)"""
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
    
    db.commit()
    db.refresh(session)
    
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
    else:
        # Создаем новую сессию
        session = ChatSession(
            user_id=current_user.id,
            title="Новый чат"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
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
                "(например: ‘как оформить договор аренды помещения?’ или ‘сроки исковой давности по ДТП?’), "
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
                    "context_used": False,
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
        
        # Получаем историю чата для контекста
        chat_history = ""
        try:
            # Получаем последние 10 сообщений для контекста
            recent_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.desc()).limit(10).all()
            
            # Формируем историю в обратном порядке (от старых к новым)
            history_parts = []
            for msg in reversed(recent_messages):
                if msg.role == "user":
                    history_parts.append(f"Пользователь: {msg.content}")
                elif msg.role == "assistant":
                    history_parts.append(f"Ассистент: {msg.content}")
            
            if history_parts:
                chat_history = "\n".join(history_parts)
                logger.info(f"Загружена история чата: {len(history_parts)} сообщений")
            else:
                logger.info("История чата пуста - это первое сообщение")
        except Exception as e:
            logger.warning(f"Ошибка загрузки истории чата: {e}")
            chat_history = ""
        
        # Проверяем баланс токенов (мягкая проверка)
        estimated_cost = 150  # Примерная стоимость запроса
        current_balance = token_service.get_user_balance(db, current_user.id)
        logger.info(f"Баланс пользователя {current_user.id}: {current_balance} токенов, требуется: {estimated_cost}")
        
        if current_balance < estimated_cost:
            logger.warning(f"Недостаточно токенов у пользователя {current_user.id}: {current_balance} < {estimated_cost}")
            # Не блокируем запрос, просто предупреждаем
        
        # Используем Vistral-24B модель через unified_llm_service
        logger.info("Используем Vistral-24B модель через unified_llm_service")
        
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
                # Создаем промпт с историей чата
                prompt = unified_llm_service.create_legal_prompt(
                    question=chat_request.message,
                    context=chat_history
                )
                logger.info(f"Вызываем unified_llm_service.generate_response с промптом: {prompt[:100]}...")
                
                # Генерируем с жестким таймаутом UI-чата
                response_text = await asyncio.wait_for(
                    unified_llm_service._generate_response_internal(
                        prompt=prompt,
                        max_tokens=settings.AI_CHAT_RESPONSE_TOKENS,
                        temperature=getattr(settings, "VISTRAL_TEMPERATURE", 0.3),
                        top_p=getattr(settings, "VISTRAL_TOP_P", 0.8)
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
                "context_used": False,
                "tokens_cost": actual_cost
            }
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия чата не найдена"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return messages


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
    else:
        # Создаем новую сессию
        session = ChatSession(
            user_id=current_user.id,
            title="Новый чат"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Сохраняем сообщение пользователя
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    
    async def generate_stream():
        try:
            # Получаем историю чата для контекста
            chat_history = ""
            try:
                # Получаем последние 10 сообщений для контекста
                recent_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                
                # Формируем историю в обратном порядке (от старых к новым)
                history_parts = []
                for msg in reversed(recent_messages):
                    if msg.role == "user":
                        history_parts.append(f"Пользователь: {msg.content}")
                    elif msg.role == "assistant":
                        history_parts.append(f"Ассистент: {msg.content}")
                
                if history_parts:
                    chat_history = "\n".join(history_parts)
                    logger.info(f"Загружена история чата для стриминга: {len(history_parts)} сообщений")
                else:
                    logger.info("История чата пуста - это первое сообщение")
            except Exception as e:
                logger.warning(f"Ошибка загрузки истории чата для стриминга: {e}")
                chat_history = ""
            
            # Создаем промпт для Vistral-24B
            # Отправляем начальную информацию
            yield f"data: {json.dumps({'type': 'start', 'session_id': session.id, 'message_id': user_message.id})}\n\n"
            
            # Используем Vistral-24B модель для стриминга через unified_llm_service
            full_response = ""
            sources = [{"title": "Vistral-24B", "text": "Ответ от русскоязычной ИИ-модели Vistral-24B"}]
            logger.info("Используем Vistral-24B для стриминга через unified_llm_service")
            try:
                # Создаем промпт с историей чата
                prompt = unified_llm_service.create_legal_prompt(
                    question=chat_request.message,
                    context=chat_history
                )
                logger.info(f"Вызываем unified_llm_service.generate_response (stream) с промптом: {prompt[:100]}...")
                async for chunk in unified_llm_service.generate_response(
                    prompt=prompt,
                    max_tokens=2500,
                    stream=True
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                logger.info(f"Unified LLM сервис завершил стриминг, общая длина ответа: {len(full_response)} символов")
            except Exception as e:
                # Простой fallback при ошибке
                logger.info(f"Ошибка в streaming: {e}, используем fallback")
                sources = [{"title": "AI Lawyer (Demo)", "text": "Ответ от демо-версии ИИ-юриста"}]
                fallback_text = f"Извините, произошла ошибка при обработке вашего запроса: {chat_request.message}"
                yield f"data: {json.dumps({'type': 'chunk', 'content': fallback_text})}\n\n"
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
                    "context_used": False
                }
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            # Уведомляем через WebSocket о новом сообщении (отключено для streaming API)
            # try:
            #     await websocket_service.notify_new_message(assistant_message, session.id)
            # except Exception as e:
            #     logger.error(f"Failed to send WebSocket notification: {e}")

            # Отправляем финальную информацию
            yield f"data: {json.dumps({'type': 'end', 'message_id': assistant_message.id, 'processing_time': processing_time})}\n\n"
                
        except Exception as e:
            logger.error(f"Ошибка в стриминг chat API: {e}")
            error_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
            
            # Сохраняем сообщение об ошибке
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=error_message,
                message_metadata={"error": str(e)}
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            yield f"data: {json.dumps({'type': 'error', 'content': error_message, 'message_id': assistant_message.id})}\n\n"
    
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
        # Создаем новую сессию
        session = ChatSession(
            user_id=current_user.id,
            title="Голосовой чат"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    try:
        # Сохраняем аудио файл
        import os
        import uuid
        from app.core.config import settings
        
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
        
        # Генерируем ответ ИИ
        prompt = unified_llm_service.create_legal_prompt(transcribed_text)
        response_generator = unified_llm_service.generate_response(
            prompt=prompt,
            max_tokens=1500,
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
