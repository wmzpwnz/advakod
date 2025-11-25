"""
Enhanced Legal Text Chunking System
Splits legal documents by semantic structure: articles, parts, paragraphs, sentences
"""

import re
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class LegalStructureType(Enum):
    """Types of legal document structures"""
    ARTICLE = "article"
    PART = "part"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CHAPTER = "chapter"
    ITEM = "item"
    SUBITEM = "subitem"


@dataclass
class LegalChunk:
    """Legal text chunk with hierarchical metadata"""
    id: str
    content: str
    chunk_type: LegalStructureType
    hierarchy: Dict[str, Any]
    token_count: int
    start_pos: int
    end_pos: int
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}


class LegalTextChunker:
    """Enhanced chunker for legal texts with proper structure recognition"""
    
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 75):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        
        # Legal structure patterns (Russian legal system)
        self.patterns = {
            'article': [
                r'Статья\s+(\d+(?:\.\d+)?)\.\s*(.*?)(?=\n|$)',
                r'Ст\.\s*(\d+(?:\.\d+)?)\.\s*(.*?)(?=\n|$)',
                r'Article\s+(\d+(?:\.\d+)?)\.\s*(.*?)(?=\n|$)'
            ],
            'part': [
                r'(\d+)\.\s*(.*?)(?=\n\d+\.|$)',
                r'Часть\s+(\d+)\.\s*(.*?)(?=\n|$)',
                r'ч\.\s*(\d+)\.\s*(.*?)(?=\n|$)'
            ],
            'paragraph': [
                r'(\d+)\)\s*(.*?)(?=\n\d+\)|$)',
                r'Пункт\s+(\d+)\.\s*(.*?)(?=\n|$)',
                r'п\.\s*(\d+)\.\s*(.*?)(?=\n|$)'
            ],
            'section': [
                r'Раздел\s+([IVX]+|(\d+))\.\s*(.*?)(?=\n|$)',
                r'Section\s+(\d+)\.\s*(.*?)(?=\n|$)'
            ],
            'chapter': [
                r'Глава\s+(\d+)\.\s*(.*?)(?=\n|$)',
                r'Chapter\s+(\d+)\.\s*(.*?)(?=\n|$)'
            ],
            'item': [
                r'([а-я])\)\s*(.*?)(?=\n[а-я]\)|$)',
                r'([a-z])\)\s*(.*?)(?=\n[a-z]\)|$)'
            ]
        }
        
        # Compiled patterns for performance
        self.compiled_patterns = {}
        for structure_type, pattern_list in self.patterns.items():
            self.compiled_patterns[structure_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for pattern in pattern_list
            ]
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (1 token ≈ 4 characters for Russian)"""
        return max(1, len(text) // 4)
    
    def extract_legal_hierarchy(self, text: str) -> Dict[str, Any]:
        """Extract legal document hierarchy from text"""
        hierarchy = {
            "code": None,
            "section": None,
            "chapter": None,
            "article": None,
            "part": None,
            "paragraph": None,
            "item": None
        }
        
        # Extract code name (ГК РФ, УК РФ, etc.)
        code_patterns = [
            r'(ГК\s+РФ|Гражданский\s+кодекс)',
            r'(УК\s+РФ|Уголовный\s+кодекс)',
            r'(ТК\s+РФ|Трудовой\s+кодекс)',
            r'(НК\s+РФ|Налоговый\s+кодекс)',
            r'(СК\s+РФ|Семейный\s+кодекс)',
            r'(КоАП\s+РФ|Административный\s+кодекс)',
            r'(ФЗ\s*№?\s*\d+)',
            r'(Закон\s+[^.\n]{5,50})'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hierarchy["code"] = match.group(1).strip()
                break
        
        # Extract article
        for pattern in self.compiled_patterns['article']:
            match = pattern.search(text)
            if match:
                hierarchy["article"] = match.group(1)
                break
        
        # Extract part
        for pattern in self.compiled_patterns['part']:
            match = pattern.search(text)
            if match:
                hierarchy["part"] = match.group(1)
                break
        
        # Extract paragraph/item
        for pattern in self.compiled_patterns['paragraph']:
            match = pattern.search(text)
            if match:
                hierarchy["paragraph"] = match.group(1)
                break
        
        return hierarchy
    
    def split_by_articles(self, text: str) -> List[Dict[str, Any]]:
        """Split text by articles (primary legal structure)"""
        articles = []
        
        # Find all article boundaries
        article_boundaries = []
        for pattern in self.compiled_patterns['article']:
            for match in pattern.finditer(text):
                article_boundaries.append({
                    'start': match.start(),
                    'end': match.end(),
                    'number': match.group(1),
                    'title': match.group(2).strip() if len(match.groups()) > 1 else '',
                    'match': match
                })
        
        # Sort by position
        article_boundaries.sort(key=lambda x: x['start'])
        
        if not article_boundaries:
            # No articles found, treat as single block
            return [{
                'content': text,
                'type': LegalStructureType.PARAGRAPH,
                'hierarchy': self.extract_legal_hierarchy(text),
                'start': 0,
                'end': len(text)
            }]
        
        # Extract article content
        for i, boundary in enumerate(article_boundaries):
            start_pos = boundary['start']
            end_pos = article_boundaries[i + 1]['start'] if i + 1 < len(article_boundaries) else len(text)
            
            article_content = text[start_pos:end_pos].strip()
            hierarchy = self.extract_legal_hierarchy(article_content)
            hierarchy['article'] = boundary['number']
            
            articles.append({
                'content': article_content,
                'type': LegalStructureType.ARTICLE,
                'hierarchy': hierarchy,
                'start': start_pos,
                'end': end_pos,
                'article_number': boundary['number'],
                'article_title': boundary['title']
            })
        
        return articles
    
    def split_by_parts(self, article_content: str) -> List[Dict[str, Any]]:
        """Split article content by parts"""
        parts = []
        
        # Find part boundaries
        part_boundaries = []
        for pattern in self.compiled_patterns['part']:
            for match in pattern.finditer(article_content):
                part_boundaries.append({
                    'start': match.start(),
                    'end': match.end(),
                    'number': match.group(1),
                    'content': match.group(2).strip() if len(match.groups()) > 1 else '',
                    'match': match
                })
        
        part_boundaries.sort(key=lambda x: x['start'])
        
        if not part_boundaries:
            # No parts found, return as single part
            return [{
                'content': article_content,
                'type': LegalStructureType.PARAGRAPH,
                'start': 0,
                'end': len(article_content)
            }]
        
        # Extract parts
        for i, boundary in enumerate(part_boundaries):
            start_pos = boundary['start']
            end_pos = part_boundaries[i + 1]['start'] if i + 1 < len(part_boundaries) else len(article_content)
            
            part_content = article_content[start_pos:end_pos].strip()
            
            parts.append({
                'content': part_content,
                'type': LegalStructureType.PART,
                'start': start_pos,
                'end': end_pos,
                'part_number': boundary['number']
            })
        
        return parts
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences with legal document awareness"""
        # Legal sentence boundaries - avoid breaking on abbreviations
        sentence_endings = r'[.!?]+(?=\s+[А-ЯA-Z]|\s*$)'
        
        # Split while preserving legal references
        sentences = []
        current_sentence = ""
        
        # First, split by potential sentence boundaries
        parts = re.split(f'({sentence_endings})', text)
        
        for i in range(0, len(parts), 2):
            sentence_part = parts[i]
            ending = parts[i + 1] if i + 1 < len(parts) else ""
            
            full_sentence = (sentence_part + ending).strip()
            
            if full_sentence:
                # Check if this is a legal reference (like "ст. 432 ГК РФ")
                if re.search(r'\b(ст|статья|п|пункт|ч|часть)\.\s*\d+', full_sentence, re.IGNORECASE):
                    # Combine with previous sentence if short
                    if current_sentence and len(full_sentence) < 100:
                        current_sentence += " " + full_sentence
                    else:
                        if current_sentence:
                            sentences.append(current_sentence)
                        current_sentence = full_sentence
                else:
                    if current_sentence:
                        current_sentence += " " + full_sentence
                    else:
                        current_sentence = full_sentence
                    
                    # End sentence if it's long enough or ends with strong punctuation
                    if len(current_sentence) > 50 or re.search(r'[.!?]$', current_sentence):
                        sentences.append(current_sentence)
                        current_sentence = ""
        
        if current_sentence:
            sentences.append(current_sentence)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_document(self, text: str, document_id: str, edition: str = "v0") -> List[LegalChunk]:
        """Main method to chunk legal document"""
        logger.info(f"🔪 Starting legal chunking for document {document_id}")
        
        chunks = []
        
        # Create document signature for unique IDs
        doc_signature = hashlib.md5(f"{document_id}:{edition}:{text[:2000]}".encode()).hexdigest()[:8]
        
        # Step 1: Split by articles
        articles = self.split_by_articles(text)
        logger.info(f"📑 Found {len(articles)} articles/sections")
        
        chunk_index = 0
        
        for article_idx, article in enumerate(articles):
            article_content = article['content']
            article_hierarchy = article['hierarchy']
            
            # Step 2: Split article by parts if too large
            if self.count_tokens(article_content) > self.max_tokens:
                parts = self.split_by_parts(article_content)
                logger.info(f"📝 Article {article_idx + 1} split into {len(parts)} parts")
                
                for part_idx, part in enumerate(parts):
                    part_content = part['content']
                    
                    # Step 3: Split part by sentences if still too large
                    if self.count_tokens(part_content) > self.max_tokens:
                        sentences = self.split_by_sentences(part_content)
                        
                        # Combine sentences into chunks
                        current_chunk = ""
                        current_tokens = 0
                        
                        for sentence in sentences:
                            sentence_tokens = self.count_tokens(sentence)
                            
                            if current_tokens + sentence_tokens > self.max_tokens and current_chunk:
                                # Save current chunk
                                chunk = self._create_chunk(
                                    content=current_chunk.strip(),
                                    chunk_index=chunk_index,
                                    doc_signature=doc_signature,
                                    hierarchy=article_hierarchy,
                                    chunk_type=LegalStructureType.PARAGRAPH,
                                    start_pos=article['start'],
                                    end_pos=article['start'] + len(current_chunk)
                                )
                                chunks.append(chunk)
                                chunk_index += 1
                                
                                # Start new chunk with overlap
                                overlap_sentences = self._get_overlap_sentences(sentences, sentence)
                                current_chunk = " ".join(overlap_sentences + [sentence])
                                current_tokens = self.count_tokens(current_chunk)
                            else:
                                current_chunk += " " + sentence if current_chunk else sentence
                                current_tokens += sentence_tokens
                        
                        # Save final chunk
                        if current_chunk.strip():
                            chunk = self._create_chunk(
                                content=current_chunk.strip(),
                                chunk_index=chunk_index,
                                doc_signature=doc_signature,
                                hierarchy=article_hierarchy,
                                chunk_type=LegalStructureType.PARAGRAPH,
                                start_pos=article['start'],
                                end_pos=article['end']
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                    else:
                        # Part fits in one chunk
                        chunk = self._create_chunk(
                            content=part_content,
                            chunk_index=chunk_index,
                            doc_signature=doc_signature,
                            hierarchy=article_hierarchy,
                            chunk_type=LegalStructureType.PART,
                            start_pos=article['start'] + part['start'],
                            end_pos=article['start'] + part['end']
                        )
                        chunks.append(chunk)
                        chunk_index += 1
            else:
                # Article fits in one chunk
                chunk = self._create_chunk(
                    content=article_content,
                    chunk_index=chunk_index,
                    doc_signature=doc_signature,
                    hierarchy=article_hierarchy,
                    chunk_type=LegalStructureType.ARTICLE,
                    start_pos=article['start'],
                    end_pos=article['end']
                )
                chunks.append(chunk)
                chunk_index += 1
        
        logger.info(f"✅ Legal chunking completed: {len(chunks)} chunks created")
        return chunks
    
    def _create_chunk(self, content: str, chunk_index: int, doc_signature: str, 
                     hierarchy: Dict[str, Any], chunk_type: LegalStructureType,
                     start_pos: int, end_pos: int) -> LegalChunk:
        """Create a legal chunk with unique ID"""
        
        # Create content hash for uniqueness
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Create unique chunk ID
        chunk_id = f"{doc_signature}:chunk:{chunk_index}:{content_hash}"
        
        return LegalChunk(
            id=chunk_id,
            content=content,
            chunk_type=chunk_type,
            hierarchy=hierarchy,
            token_count=self.count_tokens(content),
            start_pos=start_pos,
            end_pos=end_pos,
            metadata={
                "chunk_index": chunk_index,
                "content_hash": content_hash,
                "doc_signature": doc_signature,
                "created_at": datetime.now().isoformat()
            }
        )
    
    def _get_overlap_sentences(self, all_sentences: List[str], current_sentence: str) -> List[str]:
        """Get sentences for overlap to maintain context"""
        try:
            current_idx = all_sentences.index(current_sentence)
            overlap_count = max(1, self.overlap_tokens // 20)  # Rough estimate
            start_idx = max(0, current_idx - overlap_count)
            return all_sentences[start_idx:current_idx]
        except ValueError:
            return []


# Global instance
legal_chunker = LegalTextChunker()


def chunk_legal_document(text: str, document_id: str, edition: str = "v0", 
                        max_tokens: int = 512) -> List[LegalChunk]:
    """
    Main function to chunk legal documents
    
    Args:
        text: Document text to chunk
        document_id: Unique document identifier
        edition: Document edition/version
        max_tokens: Maximum tokens per chunk
    
    Returns:
        List of legal chunks
    """
    chunker = LegalTextChunker(max_tokens=max_tokens)
    return chunker.chunk_document(text, document_id, edition)