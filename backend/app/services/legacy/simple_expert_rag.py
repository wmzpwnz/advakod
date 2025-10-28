"""
Упрощенная экспертная RAG система для демонстрации
Без внешних зависимостей, с базовой функциональностью
"""

import logging
import hashlib
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)

@dataclass
class LegalMetadata:
    """Метаданные для юридических документов"""
    source: str  # "ГК РФ", "УК РФ", etc.
    article: Optional[str] = None  # "ст. 432"
    part: Optional[str] = None  # "ч.2"
    item: Optional[str] = None  # "п.3"
    edition: Optional[str] = None  # "ред. от 01.07.2024"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    url: Optional[str] = None
    ingested_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Конвертируем даты в строки для JSON
        for key, value in result.items():
            if isinstance(value, (date, datetime)):
                result[key] = value.isoformat()
        return result

@dataclass
class LegalChunk:
    """Чанк юридического документа с метаданными"""
    id: str
    content: str
    metadata: LegalMetadata
    token_count: int
    chunk_index: int
    parent_doc_id: str
    neighbors: List[str] = None
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []

class SimpleExpertRAG:
    """Упрощенная экспертная RAG система"""
    
    def __init__(self):
        self.documents = {}  # Хранение документов в памяти
        self.chunks = {}      # Хранение чанков
        self.initialized = False
        self.persistence_file = "data/simple_rag_data.json"
        
    async def initialize(self):
        """Инициализация RAG системы"""
        try:
            logger.info("🚀 Инициализация упрощенной экспертной RAG системы...")
            
            # Загружаем данные из файла, если он существует
            await self._load_data()
            
            self.initialized = True
            logger.info("🎉 Упрощенная экспертная RAG система инициализирована!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    async def _save_data(self):
        """Сохранить данные в файл"""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            
            data = {
                "documents": self.documents,
                "chunks": self.chunks,
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Данные сохранены в {self.persistence_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных: {e}")
    
    async def _load_data(self):
        """Загрузить данные из файла"""
        try:
            if not os.path.exists(self.persistence_file):
                logger.info("📁 Файл данных не найден, начинаем с пустой базы")
                return
                
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.documents = data.get("documents", {})
            self.chunks = data.get("chunks", {})
            
            logger.info(f"📂 Загружено {len(self.documents)} документов и {len(self.chunks)} чанков")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {e}")
            # Начинаем с пустой базы при ошибке
            self.documents = {}
            self.chunks = {}
    
    def count_tokens(self, text: str) -> int:
        """Упрощенный подсчет токенов (1 токен ≈ 4 символа)"""
        return len(text) // 4
    
    def extract_hierarchy(self, text: str) -> Dict[str, Any]:
        """Извлечение иерархии из юридического текста"""
        hierarchy = {
            "code": None,
            "section": None,
            "chapter": None,
            "article": None,
            "part": None,
            "item": None,
            "paragraph": None
        }
        
        # Поиск кода (ГК РФ, УК РФ, ТК РФ и т.д.)
        code_patterns = [
            r'(Гражданский кодекс|ГК)\s*(?:РФ|Российской Федерации)',
            r'(Уголовный кодекс|УК)\s*(?:РФ|Российской Федерации)',
            r'(Трудовой кодекс|ТК)\s*(?:РФ|Российской Федерации)',
            r'(Семейный кодекс|СК)\s*(?:РФ|Российской Федерации)',
            r'(Жилищный кодекс|ЖК)\s*(?:РФ|Российской Федерации)'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hierarchy["code"] = match.group(1)
                break
        
        # Поиск статей
        article_match = re.search(r'ст\.\s*(\d+(?:\.\d+)*)', text, re.IGNORECASE)
        if article_match:
            hierarchy["article"] = f"ст. {article_match.group(1)}"
        
        # Поиск частей
        part_match = re.search(r'ч\.\s*(\d+)', text, re.IGNORECASE)
        if part_match:
            hierarchy["part"] = f"ч.{part_match.group(1)}"
        
        # Поиск пунктов
        item_match = re.search(r'п\.\s*(\d+)', text, re.IGNORECASE)
        if item_match:
            hierarchy["item"] = f"п.{item_match.group(1)}"
        
        return hierarchy
    
    def split_into_chunks(self, text: str, metadata: LegalMetadata) -> List[LegalChunk]:
        """Разбивка текста на токено-ориентированные чанки"""
        chunks = []
        
        # Нормализация текста
        normalized_text = self._normalize_text(text)
        
        # Извлечение иерархии
        hierarchy = self.extract_hierarchy(normalized_text)
        
        # Разбивка на предложения
        sentences = self._split_into_sentences(normalized_text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        chunk_size = 500  # токенов
        overlap_size = 75  # 15% от 500
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # Если добавление предложения превысит лимит
            if current_tokens + sentence_tokens > chunk_size:
                # Сохраняем текущий чанк
                if current_chunk.strip():
                    chunk = self._create_chunk(
                        current_chunk.strip(),
                        metadata,
                        hierarchy,
                        chunk_index,
                        len(chunks)
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Начинаем новый чанк с перекрытием
                overlap_text = self._get_overlap_text(current_chunk, overlap_size)
                current_chunk = overlap_text + " " + sentence
                current_tokens = self.count_tokens(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Добавляем последний чанк
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk.strip(),
                metadata,
                hierarchy,
                chunk_index,
                len(chunks)
            )
            chunks.append(chunk)
        
        # Устанавливаем связи между соседними чанками
        self._set_neighbors(chunks)
        
        return chunks
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста для юридических документов"""
        # Приведение кавычек к единому виду
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Склейка переносов строк
        text = re.sub(r'-\s*\n\s*', '', text)
        text = re.sub(r'\n\s*', ' ', text)
        
        # Удаление служебных элементов
        text = re.sub(r'Страница \d+', '', text)
        text = re.sub(r'Глава \d+', '', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Разбивка на предложения с учетом юридической структуры"""
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in '.!?':
                # Проверяем, не является ли это частью номера статьи/пункта
                if not re.search(r'\d+\.\d*$', current.strip()):
                    sentences.append(current.strip())
                    current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return [s for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Получение текста для перекрытия"""
        overlap_chars = overlap_tokens * 4  # 1 токен ≈ 4 символа
        if len(text) <= overlap_chars:
            return text
        
        return text[-overlap_chars:]
    
    def _create_chunk(self, content: str, metadata: LegalMetadata, hierarchy: Dict[str, Any], 
                     chunk_index: int, total_chunks: int) -> LegalChunk:
        """Создание чанка с метаданными"""
        chunk_id = f"{metadata.source}_{chunk_index}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        return LegalChunk(
            id=chunk_id,
            content=content,
            metadata=metadata,
            token_count=self.count_tokens(content),
            chunk_index=chunk_index,
            parent_doc_id=f"{metadata.source}_doc"
        )
    
    def _set_neighbors(self, chunks: List[LegalChunk]):
        """Установка связей между соседними чанками"""
        for i, chunk in enumerate(chunks):
            neighbors = []
            if i > 0:
                neighbors.append(chunks[i-1].id)
            if i < len(chunks) - 1:
                neighbors.append(chunks[i+1].id)
            chunk.neighbors = neighbors
    
    async def add_document(self, file_path: str, metadata: LegalMetadata) -> Dict[str, Any]:
        """Добавление документа в RAG систему"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"📄 Обработка документа: {file_path}")
            
            # Извлечение текста (заглушка)
            text = await self._extract_text(file_path)
            
            # Разбивка на чанки
            logger.info("✂️ Разбивка на токено-ориентированные чанки...")
            chunks = self.split_into_chunks(text, metadata)
            logger.info(f"📊 Создано {len(chunks)} чанков")
            
            # Сохранение в памяти
            for chunk in chunks:
                self.chunks[chunk.id] = chunk
            
            # Сохранение документа
            self.documents[metadata.source] = {
                "metadata": metadata,
                "chunks": [chunk.id for chunk in chunks],
                "total_chunks": len(chunks)
            }
            
            logger.info(f"✅ Документ успешно добавлен: {len(chunks)} чанков")
            
            # Сохраняем данные
            await self._save_data()
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "document_id": metadata.source,
                "status": "processed"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def add_document_with_text(self, text_content: str, metadata: LegalMetadata) -> Dict[str, Any]:
        """Добавление документа с готовым текстом в RAG систему"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"📄 Обработка документа с текстом: {metadata.source}")
            
            # Разбивка на чанки
            logger.info("✂️ Разбивка на токено-ориентированные чанки...")
            chunks = self.split_into_chunks(text_content, metadata)
            logger.info(f"📊 Создано {len(chunks)} чанков")
            
            # Сохранение в памяти
            for chunk in chunks:
                self.chunks[chunk.id] = chunk
            
            # Сохранение документа
            self.documents[metadata.source] = {
                "metadata": metadata,
                "chunks": [chunk.id for chunk in chunks],
                "total_chunks": len(chunks)
            }
            
            logger.info(f"✅ Документ успешно добавлен: {len(chunks)} чанков")
            
            # Сохраняем данные
            await self._save_data()
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "document_id": metadata.source,
                "status": "processed"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def search_documents(self, query: str, situation_date: Optional[date] = None, 
                             top_k: int = 20) -> List[Dict[str, Any]]:
        """Упрощенный поиск документов"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"🔍 Поиск: '{query[:50]}...'")
            
            results = []
            
            # Простой поиск по содержимому чанков
            for chunk_id, chunk in self.chunks.items():
                # Проверка даты ситуации
                if situation_date and chunk.metadata.valid_from:
                    if chunk.metadata.valid_from > situation_date:
                        continue
                    if chunk.metadata.valid_to and chunk.metadata.valid_to < situation_date:
                        continue
                
                # Простой поиск по ключевым словам
                query_words = query.lower().split()
                content_words = chunk.content.lower().split()
                
                # Подсчет совпадений
                matches = sum(1 for word in query_words if word in content_words)
                if matches > 0:
                    score = matches / len(query_words)
                    
                    results.append({
                        "id": chunk.id,
                        "content": chunk.content,
                        "metadata": chunk.metadata.to_dict(),
                        "final_score": score,
                        "is_neighbor": False
                    })
            
            # Сортировка по релевантности
            results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # Добавление соседних чанков (windowed retrieval)
            enhanced_results = []
            for result in results[:top_k]:
                enhanced_results.append(result)
                
                # Добавление соседних чанков
                chunk = self.chunks.get(result['id'])
                if chunk and chunk.neighbors:
                    for neighbor_id in chunk.neighbors:
                        if neighbor_id in self.chunks:
                            neighbor_chunk = self.chunks[neighbor_id]
                            enhanced_results.append({
                                "id": neighbor_id,
                                "content": neighbor_chunk.content,
                                "metadata": neighbor_chunk.metadata.to_dict(),
                                "final_score": 0.0,
                                "is_neighbor": True
                            })
            
            logger.info(f"📊 Найдено {len(enhanced_results)} релевантных фрагментов")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []
    
    async def _extract_text(self, file_path: str) -> str:
        """Извлечение текста из файла (заглушка)"""
        # Заглушка для демонстрации
        return """
        Статья 432. Договор считается заключенным, если между сторонами в требуемой в подлежащих случаях форме достигнуто соглашение по всем существенным условиям договора.
        
        Часть 2. Существенными являются условия о предмете договора, условия, которые названы в законе или иных правовых актах как существенные или необходимые для договоров данного вида, а также все те условия, относительно которых по заявлению одной из сторон должно быть достигнуто соглашение.
        
        Часть 3. Договор заключается посредством направления оферты (предложения заключить договор) одной из сторон и ее акцепта (принятия предложения) другой стороной.
        """
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Удалить документ и все его чанки из RAG системы"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"🗑️ Удаление документа: {document_id}")
            
            # Проверяем, существует ли документ
            if document_id not in self.documents:
                return {
                    "success": False,
                    "error": f"Документ {document_id} не найден",
                    "chunks_deleted": 0
                }
            
            # Получаем список чанков для удаления
            document_info = self.documents[document_id]
            chunk_ids = document_info.get("chunks", [])
            
            # Удаляем все чанки документа
            chunks_deleted = 0
            for chunk_id in chunk_ids:
                if chunk_id in self.chunks:
                    del self.chunks[chunk_id]
                    chunks_deleted += 1
            
            # Удаляем сам документ
            del self.documents[document_id]
            
            logger.info(f"✅ Документ {document_id} удален: {chunks_deleted} чанков")
            
            # Сохраняем данные
            await self._save_data()
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_deleted": chunks_deleted,
                "status": "deleted"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления документа {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_deleted": 0
            }
    
    async def clear_all_documents(self) -> Dict[str, Any]:
        """Очистить все документы и чанки из RAG системы"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info("🗑️ Очистка всех документов из simple_expert_rag")
            
            # Подсчитываем количество документов и чанков
            documents_count = len(self.documents)
            chunks_count = len(self.chunks)
            
            # Очищаем хранилища
            self.documents.clear()
            self.chunks.clear()
            
            logger.info(f"✅ Очищено: {documents_count} документов, {chunks_count} чанков")
            
            # Сохраняем данные
            await self._save_data()
            
            return {
                "success": True,
                "documents_deleted": documents_count,
                "chunks_deleted": chunks_count,
                "status": "cleared"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки документов: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_deleted": 0,
                "chunks_deleted": 0
            }

    def get_status(self) -> Dict[str, Any]:
        """Получить статус RAG системы"""
        return {
            "status": "simple_expert_rag_operational",
            "system_type": "simple_expert",
            "features": [
                "token_based_chunking",
                "hierarchy_extraction", 
                "versioning_support",
                "windowed_retrieval",
                "simple_search",
                "document_deletion",
                "bulk_clear"
            ],
            "documents_indexed": len(self.documents),
            "chunks_indexed": len(self.chunks),
            "initialized": self.initialized
        }

# Глобальный экземпляр сервиса
simple_expert_rag = SimpleExpertRAG()
