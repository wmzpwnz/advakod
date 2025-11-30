"""
WebSocket сервис для real-time обновлений чата
Реализует требования 8.1, 8.2, 8.3 из спецификации
"""
import json
import logging
import time
import asyncio
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatMessage, ChatSession
from ..core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Менеджер WebSocket соединений с улучшенной стабильностью"""
    
    def __init__(self):
        # Активные соединения по user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Соединения по session_id для групповых чатов
        self.session_connections: Dict[int, Set[WebSocket]] = {}
        # Метаданные соединений для мониторинга
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Ping/Pong мониторинг
        self.ping_tasks: Dict[WebSocket, asyncio.Task] = {}
        # Статистика соединений
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "reconnections": 0,
            "messages_sent": 0,
            "messages_failed": 0
        }
    
    async def connect(self, websocket: WebSocket, user_id: int, session_id: int = None):
        """Подключение пользователя к WebSocket с улучшенной стабильностью"""
        try:
            # Добавляем в активные соединения пользователя
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            # Добавляем в соединения сессии
            if session_id:
                if session_id not in self.session_connections:
                    self.session_connections[session_id] = set()
                self.session_connections[session_id].add(websocket)
            
            # Сохраняем метаданные соединения
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "session_id": session_id,
                "connected_at": time.time(),
                "last_ping": None,
                "last_pong": None,
                "message_count": 0,
                "client_ip": getattr(websocket.client, 'host', 'unknown') if websocket.client else 'unknown'
            }
            
            # Запускаем ping/pong мониторинг
            await self._start_ping_monitoring(websocket)
            
            # Обновляем статистику
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.connection_metadata)
            
            logger.info(f"User {user_id} connected to WebSocket (session: {session_id}, IP: {self.connection_metadata[websocket]['client_ip']})")
            
        except Exception as e:
            logger.error(f"Error connecting user {user_id} to WebSocket: {e}")
            raise
    
    async def disconnect(self, websocket: WebSocket, user_id: int, session_id: int = None):
        """Отключение конкретного WebSocket соединения с очисткой ресурсов"""
        try:
            # Останавливаем ping мониторинг
            await self._stop_ping_monitoring(websocket)
            
            # Удаляем конкретное соединение из активных соединений пользователя
            if user_id in self.active_connections:
                connections = self.active_connections[user_id]
                if websocket in connections:
                    connections.remove(websocket)
                # Удаляем пользователя, если у него больше нет соединений
                if not connections:
                    del self.active_connections[user_id]

            # Удаляем конкретное соединение из соединений сессии
            if session_id and session_id in self.session_connections:
                connections = self.session_connections[session_id]
                if websocket in connections:
                    connections.remove(websocket)
                # Удаляем сессию, если в ней больше нет соединений
                if not connections:
                    del self.session_connections[session_id]
            
            # Очищаем метаданные
            connection_info = self.connection_metadata.pop(websocket, {})
            
            # Обновляем статистику
            self.connection_stats["active_connections"] = len(self.connection_metadata)
            
            # Логируем информацию о соединении
            if connection_info:
                duration = time.time() - connection_info.get("connected_at", time.time())
                logger.info(f"User {user_id} disconnected from WebSocket (session: {session_id}, "
                          f"duration: {duration:.1f}s, messages: {connection_info.get('message_count', 0)})")
            else:
                logger.info(f"User {user_id} disconnected from WebSocket (session: {session_id})")
                
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id} from WebSocket: {e}")
    
    async def _start_ping_monitoring(self, websocket: WebSocket):
        """Запуск ping/pong мониторинга для соединения"""
        try:
            async def ping_loop():
                while websocket in self.connection_metadata:
                    try:
                        # Отправляем ping
                        ping_data = {
                            "type": "ping",
                            "timestamp": time.time()
                        }
                        await websocket.send_text(json.dumps(ping_data))
                        
                        # Обновляем время последнего ping
                        if websocket in self.connection_metadata:
                            self.connection_metadata[websocket]["last_ping"] = time.time()
                        
                        # Ждем интервал
                        await asyncio.sleep(settings.WEBSOCKET_PING_INTERVAL)
                        
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error in ping loop: {e}")
                        break
            
            # Создаем и запускаем задачу ping
            task = asyncio.create_task(ping_loop())
            self.ping_tasks[websocket] = task
            
        except Exception as e:
            logger.error(f"Error starting ping monitoring: {e}")
    
    async def _stop_ping_monitoring(self, websocket: WebSocket):
        """Остановка ping/pong мониторинга для соединения"""
        try:
            if websocket in self.ping_tasks:
                task = self.ping_tasks.pop(websocket)
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        except Exception as e:
            logger.error(f"Error stopping ping monitoring: {e}")
    
    async def handle_pong(self, websocket: WebSocket, pong_data: dict):
        """Обработка pong ответа от клиента"""
        try:
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_pong"] = time.time()
                
                # Проверяем время ответа
                ping_time = pong_data.get("timestamp")
                if ping_time:
                    latency = time.time() - ping_time
                    if latency > 5.0:  # Предупреждение при высокой задержке
                        logger.warning(f"High WebSocket latency: {latency:.2f}s for user {self.connection_metadata[websocket]['user_id']}")
                        
        except Exception as e:
            logger.error(f"Error handling pong: {e}")
    
    def get_connection_count(self):
        """Получение статистики соединений"""
        total_users = len(self.active_connections)
        total_sessions = len(self.session_connections)
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        # Проверяем здоровье соединений
        healthy_connections = 0
        stale_connections = 0
        current_time = time.time()
        
        for websocket, metadata in self.connection_metadata.items():
            last_pong = metadata.get("last_pong")
            if last_pong and (current_time - last_pong) < (settings.WEBSOCKET_PING_INTERVAL * 3):
                healthy_connections += 1
            else:
                stale_connections += 1
        
        return {
            "active_users": total_users,
            "active_sessions": total_sessions,
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "stale_connections": stale_connections,
            "connection_stats": self.connection_stats.copy()
        }
    
    async def _handle_typing_message(self, user_id: int, session_id: int, message_data: dict):
        """Обработка сообщения о печати"""
        is_typing = message_data.get("is_typing", False)
        
        # Отправляем уведомление о печати другим пользователям в сессии
        if session_id and session_id in self.session_connections:
            for websocket in self.session_connections[session_id]:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "typing",
                        "user_id": user_id,
                        "is_typing": is_typing,
                        "session_id": session_id
                    }))
                except:
                    pass
    
    async def _handle_join_session(self, user_id: int, message_data: dict):
        """Обработка присоединения к сессии"""
        new_session_id = message_data.get("session_id")
        if new_session_id:
            logger.warning(f"Client requested session change to {new_session_id}, but live session switch is not supported. Please reconnect with new session_id.")
    
    async def _send_pong(self, user_id: int, ping_timestamp: float = None):
        """Отправка pong ответа"""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": ping_timestamp or time.time()
                    }))
                except:
                    pass
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Отправка личного сообщения пользователю с улучшенной обработкой ошибок"""
        logger.info(f"Attempting to send message to user {user_id}, active connections: {list(self.active_connections.keys())}")
        
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} not found in active connections")
            return False
        
        # Проверяем размер сообщения
        message_json = json.dumps(message, ensure_ascii=False)
        if len(message_json.encode('utf-8')) > settings.WEBSOCKET_MAX_MESSAGE_SIZE:
            logger.warning(f"Message too large for user {user_id}: {len(message_json)} bytes")
            # Обрезаем сообщение
            if 'content' in message:
                message['content'] = message['content'][:1000] + "... [сообщение обрезано]"
                message_json = json.dumps(message, ensure_ascii=False)
        
        disconnected = set()
        sent_count = 0
        
        for connection in self.active_connections[user_id].copy():
            try:
                await asyncio.wait_for(
                    connection.send_text(message_json),
                    timeout=5.0  # 5 секунд таймаут на отправку
                )
                
                # Обновляем статистику
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1
                
                self.connection_stats["messages_sent"] += 1
                sent_count += 1
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout sending message to user {user_id}")
                disconnected.add(connection)
                self.connection_stats["messages_failed"] += 1
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id} during message send")
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected.add(connection)
                self.connection_stats["messages_failed"] += 1
        
        # Очищаем отключенные соединения
        await self._cleanup_disconnected_connections(user_id, disconnected)
        
        if sent_count > 0:
            logger.info(f"Message sent to {sent_count} connections for user {user_id}")
            return True
        else:
            logger.warning(f"Failed to send message to any connection for user {user_id}")
            return False
    
    async def send_to_session(self, message: dict, session_id: int):
        """Отправка сообщения всем участникам сессии с улучшенной обработкой ошибок"""
        if session_id not in self.session_connections:
            logger.warning(f"Session {session_id} not found in active sessions")
            return False
        
        # Проверяем и обрезаем сообщение при необходимости
        message_json = json.dumps(message, ensure_ascii=False)
        message_size = len(message_json.encode('utf-8'))
        logger.info(f"Sending message to session {session_id}, size: {message_size} bytes")
        
        if message_size > settings.WEBSOCKET_MAX_MESSAGE_SIZE:
            logger.warning(f"Message size {message_size} exceeds limit, truncating content")
            # Обрезаем content если сообщение слишком большое
            if 'data' in message and 'content' in message['data']:
                original_content = message['data']['content']
                message['data']['content'] = original_content[:1000] + "... [сообщение обрезано]"
                message_json = json.dumps(message, ensure_ascii=False)
                logger.info(f"Truncated message size: {len(message_json.encode('utf-8'))} bytes")
        
        disconnected = set()
        sent_count = 0
        
        for connection in self.session_connections[session_id].copy():
            try:
                await asyncio.wait_for(
                    connection.send_text(message_json),
                    timeout=5.0  # 5 секунд таймаут на отправку
                )
                
                # Обновляем статистику
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1
                
                self.connection_stats["messages_sent"] += 1
                sent_count += 1
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout sending message to session {session_id}")
                disconnected.add(connection)
                self.connection_stats["messages_failed"] += 1
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected in session {session_id} during message send")
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                disconnected.add(connection)
                self.connection_stats["messages_failed"] += 1
        
        # Очищаем отключенные соединения
        await self._cleanup_session_connections(session_id, disconnected)
        
        if sent_count > 0:
            logger.info(f"Message sent to {sent_count} connections in session {session_id}")
            return True
        else:
            logger.warning(f"Failed to send message to any connection in session {session_id}")
            return False
    
    async def broadcast_typing(self, session_id: int, user_id: int, is_typing: bool):
        """Уведомление о печати в чате"""
        message = {
            "type": "typing",
            "user_id": user_id,
            "is_typing": is_typing,
            "session_id": session_id
        }
        await self.send_to_session(message, session_id)
    
    async def broadcast_new_message(self, message_data: dict, session_id: int):
        """Уведомление о новом сообщении"""
        logger.info(f"broadcast_new_message called with data: {message_data}")
        message = {
            "type": "new_message",
            "data": message_data,
            "session_id": session_id
        }
        logger.info(f"Broadcasting message: {message}")
        await self.send_to_session(message, session_id)
    
    async def broadcast_message_update(self, message_data: dict, session_id: int):
        """Уведомление об обновлении сообщения"""
        message = {
            "type": "message_update",
            "data": message_data,
            "session_id": session_id
        }
        await self.send_to_session(message, session_id)
    
    async def broadcast_session_update(self, session_data: dict, user_id: int):
        """Уведомление об обновлении сессии"""
        message = {
            "type": "session_update",
            "data": session_data
        }
        await self.send_personal_message(message, user_id)
    
    async def _cleanup_disconnected_connections(self, user_id: int, disconnected: Set[WebSocket]):
        """Очистка отключенных соединений пользователя"""
        try:
            for connection in disconnected:
                # Удаляем из активных соединений пользователя
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(connection)
                
                # Удаляем из всех сессий
                for session_id, session_connections in self.session_connections.items():
                    session_connections.discard(connection)
                
                # Останавливаем ping мониторинг
                await self._stop_ping_monitoring(connection)
                
                # Очищаем метаданные
                self.connection_metadata.pop(connection, None)
            
            # Удаляем пользователя, если у него больше нет соединений
            if user_id in self.active_connections and not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            # Удаляем пустые сессии
            empty_sessions = [sid for sid, conns in self.session_connections.items() if not conns]
            for session_id in empty_sessions:
                del self.session_connections[session_id]
                
        except Exception as e:
            logger.error(f"Error cleaning up disconnected connections: {e}")
    
    async def _cleanup_session_connections(self, session_id: int, disconnected: Set[WebSocket]):
        """Очистка отключенных соединений сессии"""
        try:
            for connection in disconnected:
                # Удаляем из сессии
                if session_id in self.session_connections:
                    self.session_connections[session_id].discard(connection)
                
                # Находим пользователя и удаляем соединение
                metadata = self.connection_metadata.get(connection, {})
                user_id = metadata.get("user_id")
                if user_id and user_id in self.active_connections:
                    self.active_connections[user_id].discard(connection)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # Останавливаем ping мониторинг
                await self._stop_ping_monitoring(connection)
                
                # Очищаем метаданные
                self.connection_metadata.pop(connection, None)
            
            # Удаляем сессию, если в ней больше нет соединений
            if session_id in self.session_connections and not self.session_connections[session_id]:
                del self.session_connections[session_id]
                
        except Exception as e:
            logger.error(f"Error cleaning up session connections: {e}")
    
    async def cleanup_stale_connections(self):
        """Очистка устаревших соединений (вызывается периодически)"""
        try:
            current_time = time.time()
            stale_connections = []
            
            for websocket, metadata in self.connection_metadata.items():
                last_pong = metadata.get("last_pong")
                connected_at = metadata.get("connected_at", current_time)
                
                # Соединение считается устаревшим если:
                # 1. Нет pong более 3 ping интервалов
                # 2. Соединение существует более 5 минут без pong
                if last_pong:
                    if (current_time - last_pong) > (settings.WEBSOCKET_PING_INTERVAL * 3):
                        stale_connections.append(websocket)
                elif (current_time - connected_at) > 300:  # 5 минут
                    stale_connections.append(websocket)
            
            # Закрываем устаревшие соединения
            for websocket in stale_connections:
                try:
                    metadata = self.connection_metadata.get(websocket, {})
                    user_id = metadata.get("user_id")
                    session_id = metadata.get("session_id")
                    
                    logger.warning(f"Closing stale WebSocket connection for user {user_id}")
                    await websocket.close(code=1001, reason="Stale connection")
                    await self.disconnect(websocket, user_id, session_id)
                    
                except Exception as e:
                    logger.error(f"Error closing stale connection: {e}")
            
            if stale_connections:
                logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")
                
        except Exception as e:
            logger.error(f"Error in cleanup_stale_connections: {e}")


# Глобальный менеджер соединений
manager = ConnectionManager()


class WebSocketService:
    """Сервис для работы с WebSocket"""
    
    def __init__(self):
        self.manager = manager
    
    async def handle_websocket_connection(
        self, 
        websocket: WebSocket, 
        user_id: int, 
        session_id: int = None
    ):
        """Обработка WebSocket соединения - только подключение, без цикла"""
        await self.manager.connect(websocket, user_id, session_id)
        logger.info(f"WebSocket connection established for user {user_id}, session {session_id}")
    
    async def handle_message(self, user_id: int, session_id: int, message: str):
        """Обработка сообщения от WebSocket клиента"""
        logger.info(f"WebSocketService.handle_message called for user {user_id}, session {session_id}, message: {message}")
        
        # Проверяем готовность модели перед обработкой
        from ..services.unified_llm_service import unified_llm_service
        if not unified_llm_service.is_model_loaded():
            logger.warning(f"Model not loaded for user {user_id}, attempting to load...")
            try:
                await unified_llm_service.ensure_model_loaded_async()
                if not unified_llm_service.is_model_loaded():
                    logger.error(f"Failed to load model for user {user_id}")
                    await self.manager.send_personal_message({
                        "type": "error",
                        "message": "Модель ИИ временно недоступна. Попробуйте позже.",
                        "error_code": "model_not_loaded"
                    }, user_id)
                    return
            except Exception as e:
                logger.error(f"Error loading model for user {user_id}: {e}")
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": "Ошибка загрузки модели ИИ. Попробуйте позже.",
                    "error_code": "model_load_error"
                }, user_id)
                return
        
        try:
            message_data = json.loads(message)
            logger.info(f"Parsed message data: {message_data}")
            await self._handle_websocket_message(message_data, user_id, session_id)
            logger.info(f"Message handled successfully for user {user_id}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from user {user_id}: {message}, error: {e}")
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Неверный формат сообщения.",
                "error_code": "invalid_json"
            }, user_id)
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Произошла ошибка при обработке сообщения.",
                "error_code": "processing_error"
            }, user_id)
    
    async def _handle_websocket_message(self, message_data: dict, user_id: int, session_id: int):
        """Обработка сообщений от WebSocket клиента с улучшенной стабильностью"""
        message_type = message_data.get("type")
        
        try:
            if message_type == "typing":
                # Уведомление о печати
                is_typing = message_data.get("is_typing", False)
                await self.manager.broadcast_typing(session_id, user_id, is_typing)
            
            elif message_type == "ping":
                # Ping для поддержания соединения
                logger.debug(f"Received ping from user {user_id}")
                pong_response = {
                    "type": "pong",
                    "timestamp": message_data.get("timestamp", time.time())
                }
                await self.manager.send_personal_message(pong_response, user_id)
                logger.debug(f"Pong sent to user {user_id}")
            
            elif message_type == "pong":
                # Обработка pong ответа от клиента
                # Находим WebSocket соединение пользователя
                if user_id in self.manager.active_connections:
                    for websocket in self.manager.active_connections[user_id]:
                        await self.manager.handle_pong(websocket, message_data)
                        break
            
            elif message_type == "new_message":
                # Новое сообщение от пользователя через WebSocket
                content = message_data.get("content", "").strip()
                if not content:
                    logger.warning(f"User {user_id} sent empty message via WebSocket")
                    await self.manager.send_personal_message({
                        "type": "error",
                        "message": "Сообщение не может быть пустым",
                        "error_code": "empty_message"
                    }, user_id)
                    return
                
                # Проверяем длину сообщения
                if len(content) > 5000:
                    await self.manager.send_personal_message({
                        "type": "error",
                        "message": "Сообщение слишком длинное (максимум 5000 символов)",
                        "error_code": "message_too_long"
                    }, user_id)
                    return
                
                logger.info(f"User {user_id} sent message via WebSocket: {content[:50]}...")
                await self.manager.send_personal_message({
                    "type": "info",
                    "message": "Сообщение получено, обрабатывается..."
                }, user_id)
                # Примечание: реальная обработка сообщения должна происходить через POST /api/v1/chat/message
            
            elif message_type == "join_session":
                # Присоединение к сессии
                new_session_id = message_data.get("session_id")
                if new_session_id and new_session_id != session_id:
                    logger.info(f"User {user_id} requesting to join session {new_session_id}")
                    await self.manager.send_personal_message({
                        "type": "session_change_required",
                        "message": "Для смены сессии необходимо переподключиться",
                        "new_session_id": new_session_id
                    }, user_id)
            
            elif message_type == "stop_generation":
                # Остановка генерации
                logger.info(f"User {user_id} requested to stop generation")
                await self.manager.send_personal_message({
                    "type": "generation_stopped",
                    "message": "Генерация остановлена пользователем"
                }, user_id)
            
            elif message_type == "heartbeat":
                # Heartbeat от клиента
                await self.manager.send_personal_message({
                    "type": "heartbeat_ack",
                    "timestamp": time.time()
                }, user_id)
            
            elif message_type == "subscribe":
                # Подписка на канал админ-панели (простейший ACK)
                channel = message_data.get("channel")
                await self.manager.send_personal_message({
                    "type": "subscription_result",
                    "payload": {"channel": channel, "status": "subscribed"},
                    "timestamp": time.time()
                }, user_id)

            elif message_type == "unsubscribe":
                channel = message_data.get("channel")
                await self.manager.send_personal_message({
                    "type": "unsubscription_result",
                    "payload": {"channel": channel, "status": "unsubscribed"},
                    "timestamp": time.time()
                }, user_id)

            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": f"Неизвестный тип сообщения: {message_type}",
                    "error_code": "unknown_message_type"
                }, user_id)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message type '{message_type}' from user {user_id}: {e}")
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Ошибка обработки сообщения",
                "error_code": "message_processing_error"
            }, user_id)
    
    async def notify_new_message(self, message: ChatMessage, session_id: int):
        """Уведомление о новом сообщении через WebSocket"""
        logger.info(f"notify_new_message called for message {message.id}, session {session_id}")
        logger.info(f"Message content: {message.content[:100]}...")
        
        message_data = {
            "id": message.id,
            "content": message.content,
            "role": message.role,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "message_metadata": message.message_metadata
        }
        
        logger.info(f"Message data to send: {message_data}")
        await self.manager.broadcast_new_message(message_data, session_id)
    
    async def notify_message_update(self, message: ChatMessage, session_id: int):
        """Уведомление об обновлении сообщения через WebSocket"""
        message_data = {
            "id": message.id,
            "content": message.content,
            "role": message.role,
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
            "message_metadata": message.message_metadata
        }
        
        await self.manager.broadcast_message_update(message_data, session_id)
    
    async def notify_session_update(self, session: ChatSession, user_id: int, db: Session = None):
        """Уведомление об обновлении сессии через WebSocket"""
        # Вычисляем количество сообщений (session.message_count не существует)
        message_count = 0
        try:
            # Пытаемся использовать relationship, если он загружен
            if hasattr(session, 'messages') and session.messages is not None:
                message_count = len(session.messages)
            elif db is not None:
                # Если relationship не загружен, используем запрос к БД
                from ..models.chat import ChatMessage
                message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count()
        except Exception as e:
            logger.warning(f"Ошибка при получении количества сообщений для сессии {session.id}: {e}")
            message_count = 0
        
        session_data = {
            "id": session.id,
            "title": session.title,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "message_count": message_count
        }
        
        await self.manager.broadcast_session_update(session_data, user_id)
    
    def get_connection_count(self) -> dict:
        """Получение статистики соединений"""
        return self.manager.get_connection_count()
    
    def get_detailed_stats(self) -> dict:
        """Получение детальной статистики WebSocket соединений"""
        current_time = time.time()
        connection_details = []
        
        for websocket, metadata in self.manager.connection_metadata.items():
            connection_details.append({
                "user_id": metadata.get("user_id"),
                "session_id": metadata.get("session_id"),
                "client_ip": metadata.get("client_ip"),
                "connected_at": metadata.get("connected_at"),
                "duration": current_time - metadata.get("connected_at", current_time),
                "last_ping": metadata.get("last_ping"),
                "last_pong": metadata.get("last_pong"),
                "message_count": metadata.get("message_count", 0),
                "is_healthy": self._is_connection_healthy(metadata, current_time)
            })
        
        return {
            "summary": self.get_connection_count(),
            "connections": connection_details,
            "ping_tasks_active": len(self.manager.ping_tasks)
        }
    
    def _is_connection_healthy(self, metadata: dict, current_time: float) -> bool:
        """Проверка здоровья соединения"""
        last_pong = metadata.get("last_pong")
        connected_at = metadata.get("connected_at", current_time)
        
        if last_pong:
            return (current_time - last_pong) < (settings.WEBSOCKET_PING_INTERVAL * 2)
        else:
            # Если pong еще не было, проверяем время с момента подключения
            return (current_time - connected_at) < (settings.WEBSOCKET_PING_INTERVAL * 2)
    
    async def start_cleanup_task(self):
        """Запуск периодической очистки устаревших соединений"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(settings.WEBSOCKET_PING_INTERVAL * 2)  # Очистка каждые 2 ping интервала
                    await self.manager.cleanup_stale_connections()
                except Exception as e:
                    logger.error(f"Error in WebSocket cleanup loop: {e}")
        
        # Запускаем задачу в фоне
        asyncio.create_task(cleanup_loop())


# Глобальный экземпляр сервиса
websocket_service = WebSocketService()
