"""
Сервис сбора данных для LoRA обучения
"""
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

from ..models.chat import ChatMessage, ChatSession
from ..models.training_data import TrainingData, DataCollectionLog, QualityEvaluation
from ..models.user import User

logger = logging.getLogger(__name__)


class DataCollectionService:
    """Сервис сбора данных для обучения LoRA"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def collect_chat_data(
        self, 
        limit: int = 1000, 
        days_back: int = 30,
        collection_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Сбор данных из чатов пользователей
        
        Args:
            limit: Максимальное количество диалогов
            days_back: Количество дней назад для сбора
            collection_type: Тип сбора (auto, manual, scheduled)
        
        Returns:
            Статистика сбора данных
        """
        try:
            logger.info(f"🚀 Начинаем сбор данных из чатов (лимит: {limit}, дней назад: {days_back})")
            
            # Создаем лог сбора
            collection_log = DataCollectionLog(
                collection_type=collection_type,
                source="chats",
                created_at=datetime.utcnow()
            )
            self.db.add(collection_log)
            self.db.flush()
            
            # Получаем диалоги за последние N дней
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Находим пары сообщений пользователь-ИИ
            chat_pairs = self._get_chat_pairs(start_date, limit)
            
            total_found = len(chat_pairs)
            total_processed = 0
            total_approved = 0
            total_rejected = 0
            
            logger.info(f"📊 Найдено {total_found} диалогов для обработки")
            
            for user_msg, assistant_msg in chat_pairs:
                try:
                    # Проверяем, не существует ли уже такая пара
                    existing = self.db.query(TrainingData).filter(
                        and_(
                            TrainingData.instruction == user_msg.content,
                            TrainingData.output == assistant_msg.content
                        )
                    ).first()
                    
                    if existing:
                        logger.debug(f"Диалог уже существует, пропускаем")
                        continue
                    
                    # Создаем запись для обучения
                    training_data = TrainingData(
                        instruction=user_msg.content,
                        input="",  # Контекст можно добавить позже
                        output=assistant_msg.content,
                        source="chat",
                        quality_score=None,  # Будет оценено ИИ
                        complexity=None,     # Будет определена ИИ
                        is_approved=False,
                        is_used_for_training=False
                    )
                    
                    self.db.add(training_data)
                    self.db.flush()
                    
                    # Автоматическая оценка качества
                    quality_score = self._evaluate_quality_auto(
                        training_data.instruction, 
                        training_data.output
                    )
                    training_data.quality_score = quality_score
                    
                    # Автоматическая категоризация по сложности
                    complexity = self._categorize_complexity(
                        training_data.instruction, 
                        training_data.output
                    )
                    training_data.complexity = complexity
                    
                    # Автоматическое одобрение простых случаев
                    if complexity == "simple" and quality_score >= 4.0:
                        training_data.is_approved = True
                        training_data.approved_at = datetime.utcnow()
                        total_approved += 1
                        logger.debug(f"Автоматически одобрен простой случай (качество: {quality_score})")
                    elif complexity == "complex" or quality_score < 3.0:
                        total_rejected += 1
                        logger.debug(f"Требует ручной проверки (сложность: {complexity}, качество: {quality_score})")
                    
                    total_processed += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки диалога: {e}")
                    continue
            
            # Обновляем лог сбора
            collection_log.total_found = total_found
            collection_log.total_processed = total_processed
            collection_log.total_approved = total_approved
            collection_log.total_rejected = total_rejected
            collection_log.duration_seconds = (datetime.utcnow() - collection_log.created_at).total_seconds()
            
            self.db.commit()
            
            logger.info(f"✅ Сбор данных завершен: найдено {total_found}, обработано {total_processed}, одобрено {total_approved}")
            
            return {
                "total_found": total_found,
                "total_processed": total_processed,
                "total_approved": total_approved,
                "total_rejected": total_rejected,
                "collection_id": collection_log.id
            }
            
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
            self.db.rollback()
            return {
                "error": str(e),
                "total_found": 0,
                "total_processed": 0,
                "total_approved": 0,
                "total_rejected": 0
            }
    
    def _get_chat_pairs(self, start_date: datetime, limit: int) -> List[Tuple[ChatMessage, ChatMessage]]:
        """Получение пар сообщений пользователь-ИИ"""
        try:
            # Получаем сообщения пользователей
            user_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                and_(
                    ChatMessage.role == "user",
                    ChatSession.created_at >= start_date
                )
            ).order_by(desc(ChatMessage.created_at)).limit(limit * 2).all()
            
            pairs = []
            
            for user_msg in user_messages:
                # Ищем следующий ответ ИИ в той же сессии
                assistant_msg = self.db.query(ChatMessage).filter(
                    and_(
                        ChatMessage.session_id == user_msg.session_id,
                        ChatMessage.role == "assistant",
                        ChatMessage.created_at > user_msg.created_at
                    )
                ).order_by(ChatMessage.created_at).first()
                
                if assistant_msg:
                    pairs.append((user_msg, assistant_msg))
                    
                    if len(pairs) >= limit:
                        break
            
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения пар сообщений: {e}")
            return []
    
    def _evaluate_quality_auto(self, instruction: str, output: str) -> float:
        """
        Автоматическая оценка качества данных
        
        Args:
            instruction: Вопрос пользователя
            output: Ответ ИИ
        
        Returns:
            Оценка от 1 до 5
        """
        try:
            score = 0.0
            
            # 1. Длина ответа (ваши данные в среднем 1,425 символов)
            output_length = len(output)
            if 50 <= output_length <= 2000:  # Расширенный диапазон для ваших данных
                score += 2.0
            elif 20 <= output_length <= 3000:
                score += 1.0
            else:
                score += 0.5
            
            # 2. Юридические термины (ваши данные имеют 38-61%)
            legal_terms = [
                'закон', 'суд', 'договор', 'право', 'обязательство', 
                'ответственность', 'статья', 'кодекс', 'федеральный',
                'гражданский', 'трудовой', 'уголовный', 'административный'
            ]
            legal_count = sum(1 for term in legal_terms if term in output.lower())
            score += min(2.0, legal_count * 0.3)
            
            # 3. Ссылки на законы (добавить в обучение)
            if any(ref in output for ref in ['ст.', 'ФЗ', 'ГК РФ', 'ТК РФ', 'УК РФ', 'КоАП РФ']):
                score += 1.5
            
            # 4. Качество вопроса
            question_length = len(instruction)
            if 10 <= question_length <= 500:
                score += 1.0
            elif 5 <= question_length <= 1000:
                score += 0.5
            
            # 5. Отсутствие повторений
            if len(set(instruction.split())) > 3:  # Минимум 4 уникальных слова
                score += 0.5
            
            # Нормализация до 1-5
            final_score = min(5.0, max(1.0, score))
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Ошибка оценки качества: {e}")
            return 3.0  # Средняя оценка по умолчанию
    
    def _categorize_complexity(self, instruction: str, output: str) -> str:
        """
        Категоризация по сложности
        
        Args:
            instruction: Вопрос пользователя
            output: Ответ ИИ
        
        Returns:
            simple, medium, complex
        """
        try:
            # Простые (автоматически в обучение)
            if (len(output) >= 100 and 
                len(output) <= 1500 and
                any(term in output.lower() for term in ['закон', 'право', 'договор']) and
                len(instruction) >= 20 and
                len(instruction) <= 200):
                return "simple"
            
            # Сложные (требуют проверки)
            elif (len(output) > 2000 or 
                  len(instruction) > 500 or
                  any(complex_word in instruction.lower() for complex_word in [
                      'сложный', 'запутанный', 'спорный', 'неоднозначный',
                      'противоречивый', 'конфликт', 'диспут'
                  ]) or
                  instruction.count('?') > 2):  # Множественные вопросы
                return "complex"
            
            # Средние (быстрая проверка)
            else:
                return "medium"
                
        except Exception as e:
            logger.error(f"Ошибка категоризации: {e}")
            return "medium"  # По умолчанию средняя сложность
    
    def get_pending_review_data(self, limit: int = 50) -> List[TrainingData]:
        """Получение данных, требующих ручной проверки"""
        try:
            return self.db.query(TrainingData).filter(
                and_(
                    TrainingData.is_approved == False,
                    TrainingData.complexity.in_(["medium", "complex"])
                )
            ).order_by(desc(TrainingData.created_at)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Ошибка получения данных для проверки: {e}")
            return []
    
    def approve_training_data(self, data_id: int, approver_id: int) -> bool:
        """Одобрение данных для обучения"""
        try:
            training_data = self.db.query(TrainingData).filter(
                TrainingData.id == data_id
            ).first()
            
            if not training_data:
                return False
            
            training_data.is_approved = True
            training_data.approved_by = approver_id
            training_data.approved_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Данные {data_id} одобрены пользователем {approver_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка одобрения данных: {e}")
            self.db.rollback()
            return False
    
    def reject_training_data(self, data_id: int, reason: str = None) -> bool:
        """Отклонение данных для обучения"""
        try:
            training_data = self.db.query(TrainingData).filter(
                TrainingData.id == data_id
            ).first()
            
            if not training_data:
                return False
            
            # Помечаем как отклоненные (можно добавить поле is_rejected)
            training_data.metadata = training_data.metadata or {}
            training_data.metadata["rejected"] = True
            training_data.metadata["rejection_reason"] = reason
            training_data.metadata["rejected_at"] = datetime.utcnow().isoformat()
            
            self.db.commit()
            
            logger.info(f"Данные {data_id} отклонены. Причина: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отклонения данных: {e}")
            self.db.rollback()
            return False
    
    def get_collection_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики сбора данных"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Общая статистика
            total_data = self.db.query(TrainingData).filter(
                TrainingData.created_at >= start_date
            ).count()
            
            approved_data = self.db.query(TrainingData).filter(
                and_(
                    TrainingData.created_at >= start_date,
                    TrainingData.is_approved == True
                )
            ).count()
            
            pending_data = self.db.query(TrainingData).filter(
                and_(
                    TrainingData.created_at >= start_date,
                    TrainingData.is_approved == False
                )
            ).count()
            
            # Статистика по сложности
            simple_data = self.db.query(TrainingData).filter(
                and_(
                    TrainingData.created_at >= start_date,
                    TrainingData.complexity == "simple"
                )
            ).count()
            
            medium_data = self.db.query(TrainingData).filter(
                and_(
                    TrainingData.created_at >= start_date,
                    TrainingData.complexity == "medium"
                )
            ).count()
            
            complex_data = self.db.query(TrainingData).filter(
                and_(
                    TrainingData.created_at >= start_date,
                    TrainingData.complexity == "complex"
                )
            ).count()
            
            return {
                "total_data": total_data,
                "approved_data": approved_data,
                "pending_data": pending_data,
                "simple_data": simple_data,
                "medium_data": medium_data,
                "complex_data": complex_data,
                "approval_rate": (approved_data / total_data * 100) if total_data > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
