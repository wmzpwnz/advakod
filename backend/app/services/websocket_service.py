"""
WebSocket сервис для real-time обновлений чата
"""
import json
import logging
import time
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Активные соединения по user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Соединения по session_id для групповых чатов
        self.session_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, session_id: int = None):
        """Подключение пользователя к WebSocket"""
        # Добавляем в активные соединения пользователя
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Добавляем в соединения сессии
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(websocket)
        
        logger.info(f"User {user_id} connected to WebSocket (session: {session_id})")
    
    async def disconnect(self, websocket: WebSocket, user_id: int, session_id: int = None):
        """Отключение конкретного WebSocket соединения"""
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
        
        logger.info(f"User {user_id} disconnected from WebSocket (session: {session_id})")
    
    def get_connection_count(self):
        """Получение статистики соединений"""
        total_users = len(self.active_connections)
        total_sessions = len(self.session_connections)
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "active_users": total_users,
            "active_sessions": total_sessions,
            "total_connections": total_connections
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
        """Отправка личного сообщения пользователю"""
        logger.info(f"Attempting to send message to user {user_id}, active connections: {list(self.active_connections.keys())}")
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.info(f"Message sent to user {user_id}")
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Удаляем отключенные соединения
            for connection in disconnected:
                self.active_connections[user_id].discard(connection)
            
            # Удаляем пользователя, если у него больше нет соединений
            if user_id in self.active_connections and not self.active_connections[user_id]:
                del self.active_connections[user_id]
        else:
            logger.warning(f"User {user_id} not found in active connections")
    
    async def send_to_session(self, message: dict, session_id: int):
        """Отправка сообщения всем участникам сессии"""
        if session_id in self.session_connections:
            message_json = json.dumps(message)
            message_size = len(message_json)
            logger.info(f"Sending message to session {session_id}, size: {message_size} bytes")
            
            if message_size > 65536:  # 64KB limit
                logger.warning(f"Message size {message_size} exceeds 64KB limit, truncating content")
                # Обрезаем content если сообщение слишком большое
                if 'data' in message and 'content' in message['data']:
                    original_content = message['data']['content']
                    message['data']['content'] = original_content[:1000] + "... [сообщение обрезано]"
                    message_json = json.dumps(message)
                    logger.info(f"Truncated message size: {len(message_json)} bytes")
            
            disconnected = set()
            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_text(message_json)
                    logger.info(f"Message sent successfully to session {session_id}")
                except Exception as e:
                    logger.error(f"Error sending message to session {session_id}: {e}")
                    disconnected.add(connection)
            
            # Удаляем отключенные соединения
            for connection in disconnected:
                self.session_connections[session_id].discard(connection)
            
            # Удаляем сессию, если в ней больше нет соединений
            if session_id in self.session_connections and not self.session_connections[session_id]:
                del self.session_connections[session_id]
    
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
        """Обработка сообщений от WebSocket клиента"""
        message_type = message_data.get("type")
        
        if message_type == "typing":
            # Уведомление о печати
            is_typing = message_data.get("is_typing", False)
            await self.manager.broadcast_typing(session_id, user_id, is_typing)
        
        elif message_type == "ping":
            # Ping для поддержания соединения
            logger.info(f"Received ping from user {user_id}, sending pong")
            await self.manager.send_personal_message({
                "type": "pong",
                "timestamp": message_data.get("timestamp")
            }, user_id)
            logger.info(f"Pong sent to user {user_id}")
        
        elif message_type == "join_session":
            # Присоединение к сессии
            new_session_id = message_data.get("session_id")
            if new_session_id and new_session_id != session_id:
                # Переподключаем к новой сессии
                logger.info(f"User {user_id} joining session {new_session_id}")
                # Note: WebSocket переподключение должно происходить на уровне endpoint
        
        elif message_type == "stop_generation":
            # Остановка генерации
            logger.info(f"User {user_id} requested to stop generation")
            await self.manager.send_personal_message({
                "type": "generation_stopped",
                "message": "Генерация остановлена пользователем"
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
    
    async def notify_session_update(self, session: ChatSession, user_id: int):
        """Уведомление об обновлении сессии через WebSocket"""
        session_data = {
            "id": session.id,
            "title": session.title,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "message_count": session.message_count
        }
        
        await self.manager.broadcast_session_update(session_data, user_id)
    
    def get_connection_count(self) -> dict:
        """Получение статистики соединений"""
        return {
            "active_users": len(self.manager.active_connections),
            "active_sessions": len(self.manager.session_connections),
            "total_connections": sum(len(conns) for conns in self.manager.active_connections.values())
        }


# Глобальный экземпляр сервиса
websocket_service = WebSocketService()
