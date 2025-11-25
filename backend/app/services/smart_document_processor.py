"""
Интеллектуальная система обработки документов при загрузке
"""

import asyncio
import logging
import re
import time
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .unified_llm_service import unified_llm_service
from .embeddings_service import embeddings_service
from .vector_store_service import vector_store_service
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Метаданные документа"""
    title: str
    document_type: str  # "кодекс", "закон", "постановление", etc.
    sections: List[str]  # Список разделов/глав
    articles: List[Dict[str, Any]]  # Статьи с номерами и названиями
    keywords: List[str]  # Ключевые слова
    legal_entities: List[str]  # Правовые субъекты
    dates: List[str]  # Даты в документе
    structure_score: float  # Оценка структурированности


@dataclass
class SmartChunk:
    """Умный чанк с дополнительной информацией"""
    content: str
    chunk_type: str  # "статья", "раздел", "определение", "пример"
    article_number: Optional[str] = None
    section_title: Optional[str] = None
    keywords: List[str] = None
    legal_entities: List[str] = None
    importance_score: float = 0.0
    context: str = ""  # Дополнительный контекст


class SmartDocumentProcessor:
    """Интеллектуальный процессор документов"""
    
    def __init__(self):
        self.llm_service = unified_llm_service
        self.embeddings_service = embeddings_service
        self.vector_store_service = vector_store_service
        
        # Паттерны для извлечения информации
        self.article_pattern = re.compile(r'статья\s+(\d+(?:\.\d+)?)', re.IGNORECASE)
        self.section_pattern = re.compile(r'раздел\s+[ivx\d]+|глава\s+\d+', re.IGNORECASE)
        self.definition_pattern = re.compile(r'определение|понятие|термин', re.IGNORECASE)
        
        # Ключевые слова для классификации
        self.legal_keywords = {
            'уголовный': ['преступление', 'наказание', 'ответственность', 'суд'],
            'гражданский': ['договор', 'обязательство', 'собственность', 'наследство'],
            'трудовой': ['трудовой договор', 'зарплата', 'отпуск', 'увольнение'],
            'налоговый': ['налог', 'сбор', 'декларация', 'штраф'],
            'административный': ['административное правонарушение', 'штраф', 'предупреждение']
        }
    
    async def process_document(self, file_path: str, content: str) -> Dict[str, Any]:
        """Обрабатывает документ при загрузке"""
        logger.info(f"🔍 Начинаем интеллектуальную обработку документа: {file_path}")
        
        start_time = time.time()
        
        try:
            # 1. Анализ структуры документа
            metadata = await self._analyze_document_structure(content)
            
            # 2. Извлечение ключевой информации
            extracted_info = await self._extract_key_information(content, metadata)
            
            # 3. Создание умных чанков
            smart_chunks = await self._create_smart_chunks(content, metadata, extracted_info)
            
            # 4. Генерация эмбеддингов с контекстом
            enhanced_chunks = await self._enhance_chunks_with_embeddings(smart_chunks)
            
            # 5. Сохранение в векторную базу
            await self._save_enhanced_chunks(file_path, enhanced_chunks, metadata)
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Документ обработан за {processing_time:.2f}с")
            logger.info(f"📊 Создано {len(enhanced_chunks)} умных чанков")
            logger.info(f"📋 Извлечено {len(metadata.articles)} статей")
            
            return {
                "success": True,
                "processing_time": processing_time,
                "chunks_count": len(enhanced_chunks),
                "articles_count": len(metadata.articles),
                "sections_count": len(metadata.sections),
                "metadata": metadata.__dict__,
                "chunks_preview": [chunk.__dict__ for chunk in enhanced_chunks[:3]]
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки документа: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def _analyze_document_structure(self, content: str) -> DocumentMetadata:
        """Анализирует структуру документа"""
        logger.info("🔍 Анализируем структуру документа...")
        
        # Извлекаем статьи
        articles = []
        article_matches = self.article_pattern.findall(content)
        for i, article_num in enumerate(article_matches):
            # Находим название статьи
            article_text = self._extract_article_text(content, article_num)
            articles.append({
                "number": article_num,
                "title": self._extract_article_title(article_text),
                "content_preview": article_text[:200] + "..." if len(article_text) > 200 else article_text
            })
        
        # Извлекаем разделы
        sections = []
        section_matches = self.section_pattern.findall(content)
        for section in section_matches:
            sections.append(section.strip())
        
        # Определяем тип документа
        document_type = self._classify_document_type(content)
        
        # Извлекаем ключевые слова
        keywords = self._extract_keywords(content)
        
        # Извлекаем правовые субъекты
        legal_entities = self._extract_legal_entities(content)
        
        # Извлекаем даты
        dates = self._extract_dates(content)
        
        # Оцениваем структурированность
        structure_score = self._calculate_structure_score(content, articles, sections)
        
        return DocumentMetadata(
            title=self._extract_document_title(content),
            document_type=document_type,
            sections=sections,
            articles=articles,
            keywords=keywords,
            legal_entities=legal_entities,
            dates=dates,
            structure_score=structure_score
        )
    
    async def _extract_key_information(self, content: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Извлекает ключевую информацию с помощью AI"""
        logger.info("🤖 Извлекаем ключевую информацию с помощью AI...")
        
        # Создаем промпт для анализа документа
        analysis_prompt = f"""
        Проанализируй следующий юридический документ и извлеки ключевую информацию:

        ДОКУМЕНТ:
        {content[:1500]}...

        Извлеки:
        1. Основные правовые понятия и определения
        2. Ключевые процедуры и сроки
        3. Важные правовые субъекты
        4. Основные виды ответственности
        5. Специфические термины и их значения

        Ответь структурированно в формате JSON.
        """
        
        try:
            # Используем унифицированный LLM сервис для анализа
            import asyncio
            analysis_result = ""
            async for chunk in self.llm_service.generate_response(
                prompt=analysis_prompt,
                max_tokens=settings.AI_DOCUMENT_ANALYSIS_TOKENS,  # Используем настройку токенов из конфигурации (4000)
                temperature=0.1,
                stream=True
            ):
                analysis_result += chunk
            
            # Парсим результат (упрощенная версия)
            extracted_info = {
                "legal_concepts": self._extract_legal_concepts(analysis_result),
                "procedures": self._extract_procedures(analysis_result),
                "entities": self._extract_entities(analysis_result),
                "responsibilities": self._extract_responsibilities(analysis_result),
                "terms": self._extract_terms(analysis_result)
            }
            
            return extracted_info
            
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ AI анализ превысил таймаут ({settings.AI_DOCUMENT_ANALYSIS_TIMEOUT} сек), пропускаем анализ")
            return {"error": "AI analysis timeout", "skipped": True}
        except Exception as e:
            logger.warning(f"⚠️ Ошибка AI анализа: {e}")
            return {"error": str(e), "skipped": True}
    
    async def _create_smart_chunks(self, content: str, metadata: DocumentMetadata, extracted_info: Dict[str, Any]) -> List[SmartChunk]:
        """Создает умные чанки с контекстом"""
        logger.info("🧩 Создаем умные чанки...")
        
        smart_chunks = []
        
        # Разбиваем по статьям
        for article in metadata.articles:
            article_content = self._extract_article_content(content, article["number"])
            if article_content:
                chunk = SmartChunk(
                    content=article_content,
                    chunk_type="статья",
                    article_number=article["number"],
                    section_title=article["title"],
                    keywords=metadata.keywords,
                    legal_entities=metadata.legal_entities,
                    importance_score=self._calculate_importance_score(article_content),
                    context=f"Статья {article['number']} из {metadata.document_type}"
                )
                smart_chunks.append(chunk)
        
        # Разбиваем по разделам
        for section in metadata.sections:
            section_content = self._extract_section_content(content, section)
            if section_content:
                chunk = SmartChunk(
                    content=section_content,
                    chunk_type="раздел",
                    section_title=section,
                    keywords=metadata.keywords,
                    legal_entities=metadata.legal_entities,
                    importance_score=self._calculate_importance_score(section_content),
                    context=f"Раздел {section} из {metadata.document_type}"
                )
                smart_chunks.append(chunk)
        
        # FALLBACK: Если нет статей и разделов, создаем простые чанки
        if not smart_chunks and not metadata.articles and not metadata.sections:
            logger.info("🔄 Создаем fallback чанки (нет статей/разделов)")
            smart_chunks = self._create_fallback_chunks(content, metadata)
        
        # Создаем чанки для определений
        definition_chunks = self._extract_definitions(content)
        for definition in definition_chunks:
            chunk = SmartChunk(
                content=definition,
                chunk_type="определение",
                keywords=metadata.keywords,
                legal_entities=metadata.legal_entities,
                importance_score=0.9,  # Определения важны
                context=f"Определение из {metadata.document_type}"
            )
            smart_chunks.append(chunk)
        
        return smart_chunks
    
    async def _enhance_chunks_with_embeddings(self, smart_chunks: List[SmartChunk]) -> List[Dict[str, Any]]:
        """Улучшает чанки эмбеддингами (батчевая обработка)"""
        logger.info("🔗 Генерируем эмбеддинги для чанков...")
        
        if not smart_chunks:
            return []
        
        # Подготавливаем тексты для батчевой обработки
        enhanced_texts = []
        chunk_metadata = []
        
        for chunk in smart_chunks:
            # Создаем расширенный текст для эмбеддинга
            enhanced_text = f"{chunk.content}\n\nКонтекст: {chunk.context}"
            if chunk.keywords:
                enhanced_text += f"\nКлючевые слова: {', '.join(chunk.keywords)}"
            
            enhanced_texts.append(enhanced_text)
            
            # Создаем метаданные
            metadata = {
                "chunk_type": chunk.chunk_type,
                "article_number": chunk.article_number,
                "section_title": chunk.section_title,
                "keywords": chunk.keywords or [],
                "legal_entities": chunk.legal_entities or [],
                "importance_score": chunk.importance_score,
                "context": chunk.context,
                "enhanced_text": enhanced_text
            }
            chunk_metadata.append(metadata)
        
        # БАТЧЕВАЯ ОБРАБОТКА: генерируем все эмбеддинги сразу
        logger.info(f"🚀 Обрабатываем {len(enhanced_texts)} текстов батчем...")
        embeddings = await self.embeddings_service.encode_texts(enhanced_texts)
        
        # Собираем результаты
        enhanced_chunks = []
        for i, (chunk, embedding) in enumerate(zip(smart_chunks, embeddings)):
            if embedding is None:
                logger.warning(f"⚠️ Пропускаем чанк {i} - embedding не сгенерирован")
                continue
                
            enhanced_chunks.append({
                "content": chunk.content,
                "embedding": embedding,
                "metadata": chunk_metadata[i]
            })
        
        logger.info(f"✅ Создано {len(enhanced_chunks)} чанков с эмбеддингами")
        return enhanced_chunks
    
    async def _save_enhanced_chunks(self, file_path: str, enhanced_chunks: List[Dict[str, Any]], metadata: DocumentMetadata):
        """Сохраняет улучшенные чанки в векторную базу"""
        logger.info("💾 Сохраняем чанки в векторную базу...")
        
        # Подготавливаем данные для сохранения
        contents = [chunk["content"] for chunk in enhanced_chunks]
        embeddings = [chunk["embedding"] for chunk in enhanced_chunks]
        metadatas = []
        
        for i, chunk in enumerate(enhanced_chunks):
            chunk_metadata = chunk["metadata"].copy()
            chunk_metadata.update({
                "filename": Path(file_path).name,
                "document_type": metadata.document_type,
                "document_title": metadata.title,
                "chunk_index": i,
                "total_chunks": len(enhanced_chunks),
                "structure_score": metadata.structure_score
            })
            metadatas.append(chunk_metadata)
        
        # Генерируем уникальный document_id
        document_uuid = str(uuid.uuid4())
        
        # Сохраняем каждый чанк отдельно
        added_count = 0
        for i, (content, embedding, metadata) in enumerate(zip(contents, embeddings, metadatas)):
            # Валидация embedding перед сохранением
            if not embedding or len(embedding) < 100:  # Минимальный размер embedding
                logger.warning(f"⚠️ Пропускаем чанк {i} из-за невалидного embedding")
                continue
            
            # Генерируем уникальный chunk_id
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            chunk_id = f"{document_uuid}_{i}_{content_hash}"
            
            # Обновляем metadata с уникальными ID
            metadata['document_id'] = document_uuid
            metadata['chunk_id'] = chunk_id
            
            success = await self.vector_store_service.add_document(
                content=content,
                embedding=embedding,  # ИСПРАВЛЕНО: передаем embedding
                metadata=metadata,
                document_id=chunk_id  # Используем уникальный chunk_id
            )
            if success:
                added_count += 1
        
        logger.info(f"✅ Сохранено {len(enhanced_chunks)} чанков")
    
    # Вспомогательные методы
    def _extract_article_text(self, content: str, article_num: str) -> str:
        """Извлекает текст статьи с улучшенным парсингом"""
        # Нормализуем номер статьи
        normalized_num = article_num.replace('.', r'\.').replace('№', '')
        
        # Улучшенные паттерны для поиска статей
        patterns = [
            # Статья 123
            rf'\bстатья\s+{normalized_num}\b.*?(?=\bстатья\s+\d+|$)',
            # Ст. 123
            rf'\bст\.\s*{normalized_num}\b.*?(?=\bст\.\s*\d+|$)',
            # Статья № 123
            rf'\bстатья\s*№\s*{normalized_num}\b.*?(?=\bстатья\s*№\s*\d+|$)',
            # Ст № 123
            rf'\bст\s*№\s*{normalized_num}\b.*?(?=\bст\s*№\s*\d+|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0).strip()
        
        return ""
    
    def _extract_article_title(self, article_text: str) -> str:
        """Извлекает название статьи"""
        lines = article_text.split('\n')
        for line in lines[1:3]:  # Ищем в первых 3 строках
            if line.strip() and not line.strip().startswith('статья'):
                return line.strip()
        return "Без названия"
    
    def _classify_document_type(self, content: str) -> str:
        """Классифицирует тип документа"""
        content_lower = content.lower()
        
        if 'уголовный кодекс' in content_lower or 'ук рф' in content_lower:
            return 'уголовный_кодекс'
        elif 'гражданский кодекс' in content_lower or 'гк рф' in content_lower:
            return 'гражданский_кодекс'
        elif 'трудовой кодекс' in content_lower or 'тк рф' in content_lower:
            return 'трудовой_кодекс'
        elif 'конституция' in content_lower:
            return 'конституция'
        else:
            return 'другой_документ'
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Извлекает ключевые слова"""
        # Упрощенная версия - можно улучшить
        words = re.findall(r'\b[а-яё]{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Возвращаем топ-20 слов
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    
    def _extract_legal_entities(self, content: str) -> List[str]:
        """Извлекает правовые субъекты"""
        entities = []
        patterns = [
            r'государство',
            r'гражданин',
            r'юридическое лицо',
            r'орган власти',
            r'суд',
            r'прокуратура',
            r'полиция'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_dates(self, content: str) -> List[str]:
        """Извлекает даты из документа"""
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}|\d{4}\s*года'
        return re.findall(date_pattern, content)
    
    def _calculate_structure_score(self, content: str, articles: List[Dict], sections: List[str]) -> float:
        """Оценивает структурированность документа"""
        score = 0.0
        
        # Бонус за статьи
        score += min(len(articles) * 0.1, 0.5)
        
        # Бонус за разделы
        score += min(len(sections) * 0.05, 0.3)
        
        # Бонус за длину (структурированные документы обычно длинные)
        if len(content) > 10000:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_importance_score(self, content: str) -> float:
        """Оценивает важность чанка"""
        score = 0.0
        
        # Бонус за определения
        if any(word in content.lower() for word in ['определение', 'понятие', 'термин']):
            score += 0.3
        
        # Бонус за процедуры
        if any(word in content.lower() for word in ['порядок', 'процедура', 'срок']):
            score += 0.2
        
        # Бонус за ответственность
        if any(word in content.lower() for word in ['ответственность', 'наказание', 'штраф']):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_document_title(self, content: str) -> str:
        """Извлекает название документа"""
        lines = content.split('\n')
        for line in lines[:5]:
            if line.strip() and len(line.strip()) > 10:
                return line.strip()
        return "Без названия"
    
    def _extract_article_content(self, content: str, article_num: str) -> str:
        """Извлекает полное содержание статьи"""
        return self._extract_article_text(content, article_num)
    
    def _extract_section_content(self, content: str, section: str) -> str:
        """Извлекает содержание раздела"""
        pattern = rf'{re.escape(section)}.*?(?=раздел|глава|$)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        return match.group(0) if match else ""
    
    def _extract_definitions(self, content: str) -> List[str]:
        """Извлекает определения из документа"""
        definitions = []
        pattern = r'определение.*?(?=статья|раздел|$)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        definitions.extend(matches)
        return definitions
    
    # Методы для извлечения информации с помощью AI
    def _extract_legal_concepts(self, analysis_result: str) -> List[str]:
        """Извлекает правовые понятия из AI анализа"""
        concepts = []
        
        # Ищем ключевые правовые понятия в AI-ответе
        keywords = [
            'право', 'обязанность', 'ответственность', 'процедура', 'срок', 'порядок',
            'свобода', 'равенство', 'справедливость', 'закон', 'норма', 'принцип',
            'гарантия', 'защита', 'охрана', 'регулирование', 'управление'
        ]
        
        for keyword in keywords:
            if keyword in analysis_result.lower():
                concepts.append(keyword)
        
        # Ищем статьи и разделы
        article_pattern = r'статья\s+\d+'
        articles = re.findall(article_pattern, analysis_result, re.IGNORECASE)
        concepts.extend(articles)
        
        return list(set(concepts))
    
    def _extract_procedures(self, analysis_result: str) -> List[str]:
        """Извлекает процедуры из AI анализа"""
        procedures = []
        
        # Ищем ключевые процедурные термины
        keywords = [
            'порядок', 'процедура', 'срок', 'этап', 'стадия', 'процесс',
            'реализация', 'применение', 'исполнение', 'соблюдение'
        ]
        
        for keyword in keywords:
            if keyword in analysis_result.lower():
                procedures.append(keyword)
        
        return list(set(procedures))
    
    def _extract_entities(self, analysis_result: str) -> List[str]:
        """Извлекает субъекты из AI анализа"""
        entities = []
        
        # Ищем ключевые субъекты права
        keywords = [
            'государство', 'гражданин', 'юридическое лицо', 'орган власти',
            'суд', 'прокуратура', 'полиция', 'президент', 'правительство',
            'парламент', 'министерство', 'администрация'
        ]
        
        for keyword in keywords:
            if keyword in analysis_result.lower():
                entities.append(keyword)
        
        return list(set(entities))
    
    def _extract_responsibilities(self, analysis_result: str) -> List[str]:
        """Извлекает виды ответственности из AI анализа"""
        responsibilities = []
        
        # Ищем ключевые термины ответственности
        keywords = [
            'ответственность', 'наказание', 'штраф', 'лишение', 'арест',
            'обязательные работы', 'исправительные работы', 'лишение свободы',
            'административная ответственность', 'уголовная ответственность'
        ]
        
        for keyword in keywords:
            if keyword in analysis_result.lower():
                responsibilities.append(keyword)
        
        return list(set(responsibilities))
    
    def _extract_terms(self, analysis_result: str) -> List[str]:
        """Извлекает термины из AI анализа"""
        terms = []
        
        # Ищем ключевые правовые термины
        keywords = [
            'определение', 'понятие', 'термин', 'содержание', 'признак', 'элемент',
            'конституция', 'закон', 'норма', 'принцип', 'гарантия', 'свобода',
            'равенство', 'справедливость', 'демократия', 'федерация'
        ]
        
        for keyword in keywords:
            if keyword in analysis_result.lower():
                terms.append(keyword)
        
        return list(set(terms))
    
    def _create_fallback_chunks(self, content: str, metadata: DocumentMetadata) -> List[SmartChunk]:
        """Создает простые чанки если AI-анализ не дал результатов"""
        logger.info("🔄 Создаем fallback чанки...")
        
        chunks = []
        chunk_size = 2000  # Размер чанка
        overlap = 200      # Перекрытие между чанками
        
        # Разбиваем документ на части
        for i in range(0, len(content), chunk_size - overlap):
            chunk_content = content[i:i + chunk_size]
            if len(chunk_content.strip()) < 100:  # Пропускаем слишком короткие чанки
                continue
                
            chunk = SmartChunk(
                content=chunk_content,
                chunk_type="fallback",
                section_title=f"Часть {i // (chunk_size - overlap) + 1}",
                keywords=metadata.keywords or [],
                legal_entities=metadata.legal_entities or [],
                importance_score=0.5,  # Средняя важность
                context=f"Документ: {metadata.document_type}"
            )
            chunks.append(chunk)
        
        logger.info(f"✅ Создано {len(chunks)} fallback чанков")
        return chunks


# Глобальный экземпляр
smart_document_processor = SmartDocumentProcessor()
