import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Документ в базе знаний"""
    id: str
    title: str
    content: str
    category: str
    source: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class SearchResult:
    """Результат поиска"""
    document: Document
    score: float
    relevance: float
    matched_snippets: List[str]

@dataclass
class QueryContext:
    """Контекст запроса"""
    query: str
    user_id: int
    session_id: Optional[str]
    category: Optional[str]
    filters: Dict[str, Any]
    max_results: int = 10

class DocumentProcessor:
    """Процессор документов для RAG системы"""
    
    def __init__(self):
        self.stop_words = {
            "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может", "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без", "будто", "чего", "раз", "тоже", "себе", "под", "будет", "ж", "тогда", "кто", "этот", "того", "потому", "этого", "какой", "совсем", "ним", "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "сейчас", "были", "куда", "зачем", "всех", "никогда", "можно", "при", "наконец", "два", "об", "другой", "хоть", "после", "над", "больше", "тот", "через", "эти", "нас", "про", "всего", "них", "какая", "много", "разве", "три", "эту", "моя", "впрочем", "хорошо", "свою", "этой", "перед", "иногда", "лучше", "чуть", "том", "нельзя", "такой", "им", "более", "всегда", "конечно", "всю", "между"
        }
    
    def preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы, оставляем только буквы, цифры и пробелы
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем стоп-слова
        words = text.split()
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return ' '.join(words)
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Извлечение ключевых слов из текста"""
        processed_text = self.preprocess_text(text)
        words = processed_text.split()
        
        # Подсчитываем частоту слов
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        # Сортируем по частоте и возвращаем топ ключевых слов
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def split_document(self, document: Document, chunk_size: int = 500, overlap: int = 50) -> List[Document]:
        """Оригинальное разбиение документа на чанки (для не-юридических документов)"""
        import hashlib
        
        content = document.content
        chunks = []
        
        # Create document signature for unique parent_doc_id
        doc_signature_data = f"{document.source}:{document.metadata.get('edition', 'v0')}:{content[:2000]}"
        doc_sig = hashlib.md5(doc_signature_data.encode()).hexdigest()[:8]
        parent_doc_id = f"{document.source}:{document.metadata.get('edition', 'v0')}:{doc_sig}"
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Пытаемся закончить на границе предложения
            if end < len(content):
                # Ищем последнюю точку, восклицательный или вопросительный знак
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                # Create unique chunk ID with content hash to prevent collisions
                content_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                chunk_id = f"{parent_doc_id}:chunk:{chunk_index}:{content_hash}"
                
                chunk = Document(
                    id=chunk_id,
                    title=f"{document.title} (часть {chunk_index + 1})",
                    content=chunk_content,
                    category=document.category,
                    source=document.source,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_index,
                        "original_doc_id": document.id,
                        "parent_doc_id": parent_doc_id,
                        "content_hash": content_hash,
                        "start_pos": start,
                        "end_pos": end,
                        "chunk_type": "paragraph"  # Default for non-legal
                    },
                    created_at=document.created_at,
                    updated_at=document.updated_at
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap
        
        return chunks
        import hashlib
        from ..core.legal_chunker import chunk_legal_document
        
        # Use enhanced legal chunking for legal documents
        if self._is_legal_document(document):
            logger.info(f"🏦 Using legal chunking for document: {document.id}")
            
            legal_chunks = chunk_legal_document(
                text=document.content,
                document_id=document.id,
                edition=document.metadata.get('edition', 'v0'),
                max_tokens=chunk_size // 4  # Convert chars to approximate tokens
            )
            
            # Convert LegalChunk to Document format
            chunks = []
            for legal_chunk in legal_chunks:
                chunk_doc = Document(
                    id=legal_chunk.id,
                    title=f"{document.title} ({legal_chunk.chunk_type.value} {legal_chunk.hierarchy.get('article', '')})",
                    content=legal_chunk.content,
                    category=document.category,
                    source=document.source,
                    metadata={
                        **document.metadata,
                        **legal_chunk.hierarchy,
                        "chunk_type": legal_chunk.chunk_type.value,
                        "token_count": legal_chunk.token_count,
                        "chunk_index": legal_chunk.metadata.get("chunk_index"),
                        "content_hash": legal_chunk.metadata.get("content_hash"),
                        "start_pos": legal_chunk.start_pos,
                        "end_pos": legal_chunk.end_pos,
                        "original_doc_id": document.id,
                        "parent_doc_id": legal_chunk.metadata.get("doc_signature")
                    },
                    created_at=document.created_at,
                    updated_at=document.updated_at
                )
                chunks.append(chunk_doc)
            
            return chunks
        else:
            # Use original chunking for non-legal documents
            return self._split_document_original(document, chunk_size, overlap)
    
    def _is_legal_document(self, document: Document) -> bool:
        """Определяет, является ли документ юридическим"""
        # Check category
        if document.category in ['law', 'legal', 'закон', 'право']:
            return True
        
        # Check content for legal indicators
        content_lower = document.content.lower()
        legal_indicators = [
            'статья', 'гк рф', 'ук рф', 'тк рф', 'нк рф',
            'коап рф', 'федеральный закон', 'кодекс',
            'article', 'law', 'legal code', 'пункт', 'часть'
        ]
        
        return any(indicator in content_lower for indicator in legal_indicators)
    
    def _split_document_original(self, document: Document, chunk_size: int = 500, overlap: int = 50) -> List[Document]:
        """Разбиение документа на чанки с уникальными ID"""
        import hashlib
        
        content = document.content
        chunks = []
        
        # Create document signature for unique parent_doc_id
        doc_signature_data = f"{document.source}:{document.metadata.get('edition', 'v0')}:{content[:2000]}"
        doc_sig = hashlib.md5(doc_signature_data.encode()).hexdigest()[:8]
        parent_doc_id = f"{document.source}:{document.metadata.get('edition', 'v0')}:{doc_sig}"
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Пытаемся закончить на границе предложения
            if end < len(content):
                # Ищем последнюю точку, восклицательный или вопросительный знак
                for i in range(end, max(start + chunk_size - 100, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                # Create unique chunk ID with content hash to prevent collisions
                content_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]
                chunk_id = f"{parent_doc_id}:chunk:{chunk_index}:{content_hash}"
                
                chunk = Document(
                    id=chunk_id,
                    title=f"{document.title} (часть {chunk_index + 1})",
                    content=chunk_content,
                    category=document.category,
                    source=document.source,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_index,
                        "original_doc_id": document.id,
                        "parent_doc_id": parent_doc_id,
                        "content_hash": content_hash,
                        "start_pos": start,
                        "end_pos": end
                    },
                    created_at=document.created_at,
                    updated_at=document.updated_at
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap
        
        return chunks
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Извлечение именованных сущностей"""
        entities = {
            "organizations": [],
            "laws": [],
            "dates": [],
            "numbers": []
        }
        
        # Извлечение организаций (ООО, АО, ИП и т.д.)
        org_pattern = r'\b(?:ООО|АО|ЗАО|ОАО|ИП|ПАО|АО|ТОО|ЧП)\s+[А-Яа-я\s"]+'
        entities["organizations"] = re.findall(org_pattern, text)
        
        # Извлечение законов и нормативных актов
        law_pattern = r'\b(?:ФЗ|ГК|ТК|НК|УК|КоАП|ГПК|АПК|УПК)\s*[№#]?\s*\d+'
        entities["laws"] = re.findall(law_pattern, text)
        
        # Извлечение дат
        date_pattern = r'\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b'
        entities["dates"] = re.findall(date_pattern, text)
        
        # Извлечение чисел
        number_pattern = r'\b\d+(?:[.,]\d+)?\s*(?:руб|долл|евро|%|тыс|млн|млрд)?\b'
        entities["numbers"] = re.findall(number_pattern, text)
        
        return entities

class EmbeddingService:
    """Сервис для создания эмбеддингов"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = "text-embedding-ada-002"
        self.cache = {}  # Кэш эмбеддингов
    
    async def get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга для текста"""
        # Проверяем кэш
        text_hash = hash(text)
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        try:
            if self.openai_api_key:
                # Используем OpenAI API
                embedding = await self._get_openai_embedding(text)
            else:
                # Используем простой эмбеддинг на основе TF-IDF
                embedding = self._get_simple_embedding(text)
            
            # Кэшируем результат
            self.cache[text_hash] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Возвращаем нулевой вектор в случае ошибки
            return [0.0] * 1536  # Размер эмбеддинга OpenAI
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга через OpenAI API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.embedding_model,
                    'input': text
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data'][0]['embedding']
                else:
                    raise Exception(f"OpenAI API error: {response.status}")
    
    def _get_simple_embedding(self, text: str) -> List[float]:
        """Простой эмбеддинг на основе TF-IDF"""
        # Это упрощенная реализация для демонстрации
        # В реальном приложении можно использовать sentence-transformers
        
        words = text.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Создаем вектор фиксированной длины
        embedding = [0.0] * 1536
        
        # Заполняем вектор на основе хешей слов
        for i, word in enumerate(words[:1536]):
            word_hash = hash(word) % 1000
            embedding[i] = word_freq[word] / len(words) * (word_hash / 1000.0)
        
        return embedding
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Вычисление косинусного сходства"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Нормализуем векторы
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Вычисляем косинусное сходство
        dot_product = np.dot(embedding1, embedding2)
        return dot_product / (norm1 * norm2)

class RAGSystem:
    """Улучшенная RAG система"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.search_index = {}  # Индекс для быстрого поиска
    
    async def add_document(self, document: Document) -> str:
        """Добавление документа в базу знаний"""
        try:
            # Обрабатываем документ
            processed_content = self.document_processor.preprocess_text(document.content)
            
            # Извлекаем ключевые слова
            keywords = self.document_processor.extract_keywords(document.content)
            
            # Извлекаем сущности
            entities = self.document_processor.extract_entities(document.content)
            
            # Создаем эмбеддинг
            embedding = await self.embedding_service.get_embedding(processed_content)
            
            # Обновляем документ
            document.embedding = embedding
            document.metadata.update({
                "keywords": keywords,
                "entities": entities,
                "processed_content": processed_content
            })
            
            # Добавляем в хранилище
            self.documents[document.id] = document
            
            # Обновляем поисковый индекс
            self._update_search_index(document)
            
            logger.info(f"Document added: {document.id}")
            return document.id
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise
    
    async def add_documents_batch(self, documents: List[Document]) -> List[str]:
        """Добавление нескольких документов"""
        added_ids = []
        
        for document in documents:
            try:
                doc_id = await self.add_document(document)
                added_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Error adding document {document.id}: {str(e)}")
                continue
        
        return added_ids
    
    def _update_search_index(self, document: Document):
        """Обновление поискового индекса"""
        # Индексируем по ключевым словам
        for keyword in document.metadata.get("keywords", []):
            if keyword not in self.search_index:
                self.search_index[keyword] = []
            self.search_index[keyword].append(document.id)
        
        # Индексируем по категории
        category_key = f"category:{document.category}"
        if category_key not in self.search_index:
            self.search_index[category_key] = []
        self.search_index[category_key].append(document.id)
        
        # Индексируем по сущностям
        for entity_type, entities in document.metadata.get("entities", {}).items():
            for entity in entities:
                entity_key = f"entity:{entity_type}:{entity}"
                if entity_key not in self.search_index:
                    self.search_index[entity_key] = []
                self.search_index[entity_key].append(document.id)
    
    async def search(self, query_context: QueryContext) -> List[SearchResult]:
        """Поиск документов по запросу"""
        try:
            # Обрабатываем запрос
            processed_query = self.document_processor.preprocess_text(query_context.query)
            query_embedding = await self.embedding_service.get_embedding(processed_query)
            
            # Извлекаем ключевые слова из запроса
            query_keywords = self.document_processor.extract_keywords(query_context.query)
            
            # Получаем кандидатов для поиска
            candidates = self._get_search_candidates(query_context, query_keywords)
            
            # Вычисляем релевантность для каждого кандидата
            results = []
            for doc_id in candidates:
                document = self.documents.get(doc_id)
                if not document or not document.embedding:
                    continue
                
                # Семантическое сходство
                semantic_score = self.embedding_service.cosine_similarity(
                    query_embedding, document.embedding
                )
                
                # Ключевое слово сходство
                keyword_score = self._calculate_keyword_score(
                    query_keywords, document.metadata.get("keywords", [])
                )
                
                # Общая релевантность
                relevance = (semantic_score * 0.7) + (keyword_score * 0.3)
                
                # Фильтруем по минимальной релевантности
                if relevance > 0.1:
                    # Находим релевантные фрагменты
                    snippets = self._extract_relevant_snippets(
                        query_context.query, document.content
                    )
                    
                    results.append(SearchResult(
                        document=document,
                        score=semantic_score,
                        relevance=relevance,
                        matched_snippets=snippets
                    ))
            
            # Сортируем по релевантности
            results.sort(key=lambda x: x.relevance, reverse=True)
            
            # Ограничиваем количество результатов
            return results[:query_context.max_results]
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def _get_search_candidates(self, query_context: QueryContext, query_keywords: List[str]) -> List[str]:
        """Получение кандидатов для поиска"""
        candidates = set()
        
        # Поиск по ключевым словам
        for keyword in query_keywords:
            if keyword in self.search_index:
                candidates.update(self.search_index[keyword])
        
        # Поиск по категории
        if query_context.category:
            category_key = f"category:{query_context.category}"
            if category_key in self.search_index:
                candidates.update(self.search_index[category_key])
        
        # Если кандидатов мало, добавляем все документы
        if len(candidates) < 10:
            candidates.update(self.documents.keys())
        
        return list(candidates)
    
    def _calculate_keyword_score(self, query_keywords: List[str], doc_keywords: List[str]) -> float:
        """Вычисление сходства по ключевым словам"""
        if not query_keywords or not doc_keywords:
            return 0.0
        
        # Переводим в множества для быстрого поиска
        query_set = set(query_keywords)
        doc_set = set(doc_keywords)
        
        # Вычисляем пересечение
        intersection = query_set.intersection(doc_set)
        
        # Возвращаем долю пересечения
        return len(intersection) / len(query_set)
    
    def _extract_relevant_snippets(self, query: str, content: str, max_snippets: int = 3) -> List[str]:
        """Извлечение релевантных фрагментов"""
        snippets = []
        query_words = set(query.lower().split())
        
        # Разбиваем контент на предложения
        sentences = re.split(r'[.!?]+', content)
        
        # Вычисляем релевантность каждого предложения
        sentence_scores = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            intersection = query_words.intersection(sentence_words)
            score = len(intersection) / len(query_words) if query_words else 0
            sentence_scores.append((sentence.strip(), score))
        
        # Сортируем по релевантности
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ фрагменты
        for sentence, score in sentence_scores[:max_snippets]:
            if score > 0 and sentence:
                snippets.append(sentence)
        
        return snippets
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Получение документа по ID"""
        return self.documents.get(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """Удаление документа"""
        if doc_id in self.documents:
            document = self.documents[doc_id]
            
            # Удаляем из индекса
            self._remove_from_index(document)
            
            # Удаляем из хранилища
            del self.documents[doc_id]
            
            logger.info(f"Document deleted: {doc_id}")
            return True
        
        return False
    
    def _remove_from_index(self, document: Document):
        """Удаление документа из индекса"""
        # Удаляем по ключевым словам
        for keyword in document.metadata.get("keywords", []):
            if keyword in self.search_index:
                if document.id in self.search_index[keyword]:
                    self.search_index[keyword].remove(document.id)
                if not self.search_index[keyword]:
                    del self.search_index[keyword]
        
        # Удаляем по категории
        category_key = f"category:{document.category}"
        if category_key in self.search_index:
            if document.id in self.search_index[category_key]:
                self.search_index[category_key].remove(document.id)
            if not self.search_index[category_key]:
                del self.search_index[category_key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики RAG системы"""
        total_docs = len(self.documents)
        categories = {}
        
        for doc in self.documents.values():
            category = doc.category
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_documents": total_docs,
            "categories": categories,
            "index_size": len(self.search_index),
            "embedding_cache_size": len(self.embedding_service.cache)
        }

# Глобальный экземпляр RAG системы
rag_system = RAGSystem()

def get_rag_system() -> RAGSystem:
    """Получение экземпляра RAG системы"""
    return rag_system
