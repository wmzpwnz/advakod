import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)

class AnnotationType(Enum):
    """Типы аннотаций"""
    HIGHLIGHT = "highlight"  # Выделение
    COMMENT = "comment"  # Комментарий
    NOTE = "note"  # Заметка
    BOOKMARK = "bookmark"  # Закладка
    TAG = "tag"  # Тег
    LINK = "link"  # Ссылка
    CROSS_REFERENCE = "cross_reference"  # Перекрестная ссылка

class AnnotationStatus(Enum):
    """Статусы аннотаций"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

@dataclass
class TextRange:
    """Диапазон текста"""
    start_offset: int
    end_offset: int
    start_line: int
    end_line: int
    text: str

@dataclass
class Annotation:
    """Аннотация"""
    id: str
    document_id: str
    user_id: int
    annotation_type: AnnotationType
    text_range: TextRange
    content: str  # Содержимое аннотации (комментарий, заметка и т.д.)
    color: Optional[str] = None  # Цвет выделения
    style: Optional[Dict[str, Any]] = None  # Стиль (жирный, курсив и т.д.)
    tags: List[str] = None  # Теги
    metadata: Dict[str, Any] = None  # Дополнительные метаданные
    created_at: datetime = None
    updated_at: datetime = None
    status: AnnotationStatus = AnnotationStatus.ACTIVE
    is_public: bool = False  # Публичная аннотация
    replies: List[str] = None  # ID ответов на комментарии

@dataclass
class AnnotationReply:
    """Ответ на аннотацию"""
    id: str
    annotation_id: str
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    status: AnnotationStatus = AnnotationStatus.ACTIVE

@dataclass
class DocumentVersion:
    """Версия документа"""
    id: str
    document_id: str
    version_number: int
    content: str
    created_at: datetime
    created_by: int
    change_summary: str
    annotations_count: int = 0

class AnnotationManager:
    """Менеджер аннотаций"""
    
    def __init__(self):
        self.annotations: Dict[str, Annotation] = {}
        self.annotation_replies: Dict[str, AnnotationReply] = {}
        self.document_versions: Dict[str, List[DocumentVersion]] = {}
        self.user_annotations: Dict[int, List[str]] = {}  # user_id -> annotation_ids
    
    def create_annotation(
        self,
        document_id: str,
        user_id: int,
        annotation_type: AnnotationType,
        text_range: TextRange,
        content: str,
        color: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> Annotation:
        """Создание аннотации"""
        try:
            annotation_id = f"ann_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            annotation = Annotation(
                id=annotation_id,
                document_id=document_id,
                user_id=user_id,
                annotation_type=annotation_type,
                text_range=text_range,
                content=content,
                color=color,
                style=style or {},
                tags=tags or [],
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=AnnotationStatus.ACTIVE,
                is_public=is_public,
                replies=[]
            )
            
            self.annotations[annotation_id] = annotation
            
            # Добавляем в список аннотаций пользователя
            if user_id not in self.user_annotations:
                self.user_annotations[user_id] = []
            self.user_annotations[user_id].append(annotation_id)
            
            logger.info(f"Created annotation {annotation_id} for document {document_id}")
            return annotation
            
        except Exception as e:
            logger.error(f"Annotation creation error: {str(e)}")
            raise
    
    def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """Получение аннотации по ID"""
        return self.annotations.get(annotation_id)
    
    def get_document_annotations(
        self,
        document_id: str,
        user_id: Optional[int] = None,
        annotation_type: Optional[AnnotationType] = None,
        include_public: bool = True
    ) -> List[Annotation]:
        """Получение аннотаций документа"""
        document_annotations = []
        
        for annotation in self.annotations.values():
            if annotation.document_id != document_id:
                continue
            
            if annotation.status != AnnotationStatus.ACTIVE:
                continue
            
            # Фильтр по пользователю
            if user_id is not None and annotation.user_id != user_id and not annotation.is_public:
                continue
            
            # Фильтр по типу
            if annotation_type is not None and annotation.annotation_type != annotation_type:
                continue
            
            # Фильтр по публичности
            if not include_public and annotation.is_public:
                continue
            
            document_annotations.append(annotation)
        
        # Сортируем по позиции в тексте
        document_annotations.sort(key=lambda x: x.text_range.start_offset)
        
        return document_annotations
    
    def update_annotation(
        self,
        annotation_id: str,
        content: Optional[str] = None,
        color: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None
    ) -> bool:
        """Обновление аннотации"""
        try:
            annotation = self.get_annotation(annotation_id)
            if not annotation:
                return False
            
            if content is not None:
                annotation.content = content
            
            if color is not None:
                annotation.color = color
            
            if style is not None:
                annotation.style = style
            
            if tags is not None:
                annotation.tags = tags
            
            if metadata is not None:
                annotation.metadata.update(metadata)
            
            if is_public is not None:
                annotation.is_public = is_public
            
            annotation.updated_at = datetime.now()
            
            logger.info(f"Updated annotation {annotation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Annotation update error: {str(e)}")
            return False
    
    def delete_annotation(self, annotation_id: str, user_id: int) -> bool:
        """Удаление аннотации"""
        try:
            annotation = self.get_annotation(annotation_id)
            if not annotation:
                return False
            
            # Проверяем права доступа
            if annotation.user_id != user_id:
                return False
            
            # Мягкое удаление
            annotation.status = AnnotationStatus.DELETED
            annotation.updated_at = datetime.now()
            
            # Удаляем из списка пользователя
            if user_id in self.user_annotations:
                if annotation_id in self.user_annotations[user_id]:
                    self.user_annotations[user_id].remove(annotation_id)
            
            logger.info(f"Deleted annotation {annotation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Annotation deletion error: {str(e)}")
            return False
    
    def add_annotation_reply(
        self,
        annotation_id: str,
        user_id: int,
        content: str
    ) -> AnnotationReply:
        """Добавление ответа на аннотацию"""
        try:
            annotation = self.get_annotation(annotation_id)
            if not annotation:
                raise ValueError("Annotation not found")
            
            reply_id = f"reply_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            reply = AnnotationReply(
                id=reply_id,
                annotation_id=annotation_id,
                user_id=user_id,
                content=content,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=AnnotationStatus.ACTIVE
            )
            
            self.annotation_replies[reply_id] = reply
            annotation.replies.append(reply_id)
            annotation.updated_at = datetime.now()
            
            logger.info(f"Added reply {reply_id} to annotation {annotation_id}")
            return reply
            
        except Exception as e:
            logger.error(f"Annotation reply creation error: {str(e)}")
            raise
    
    def get_annotation_replies(self, annotation_id: str) -> List[AnnotationReply]:
        """Получение ответов на аннотацию"""
        replies = []
        
        for reply in self.annotation_replies.values():
            if reply.annotation_id == annotation_id and reply.status == AnnotationStatus.ACTIVE:
                replies.append(reply)
        
        # Сортируем по дате создания
        replies.sort(key=lambda x: x.created_at)
        
        return replies
    
    def search_annotations(
        self,
        query: str,
        user_id: Optional[int] = None,
        document_id: Optional[str] = None,
        annotation_type: Optional[AnnotationType] = None,
        tags: Optional[List[str]] = None
    ) -> List[Annotation]:
        """Поиск аннотаций"""
        results = []
        
        for annotation in self.annotations.values():
            if annotation.status != AnnotationStatus.ACTIVE:
                continue
            
            # Фильтр по пользователю
            if user_id is not None and annotation.user_id != user_id and not annotation.is_public:
                continue
            
            # Фильтр по документу
            if document_id is not None and annotation.document_id != document_id:
                continue
            
            # Фильтр по типу
            if annotation_type is not None and annotation.annotation_type != annotation_type:
                continue
            
            # Фильтр по тегам
            if tags is not None and not any(tag in annotation.tags for tag in tags):
                continue
            
            # Поиск по содержимому
            if query.lower() in annotation.content.lower() or query.lower() in annotation.text_range.text.lower():
                results.append(annotation)
        
        # Сортируем по релевантности (простая эвристика)
        results.sort(key=lambda x: (
            query.lower() in x.content.lower(),
            x.created_at
        ), reverse=True)
        
        return results
    
    def get_user_annotations(
        self,
        user_id: int,
        annotation_type: Optional[AnnotationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Annotation]:
        """Получение аннотаций пользователя"""
        user_annotation_ids = self.user_annotations.get(user_id, [])
        user_annotations = []
        
        for annotation_id in user_annotation_ids:
            annotation = self.get_annotation(annotation_id)
            if annotation and annotation.status == AnnotationStatus.ACTIVE:
                if annotation_type is None or annotation.annotation_type == annotation_type:
                    user_annotations.append(annotation)
        
        # Сортируем по дате создания
        user_annotations.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_annotations[offset:offset + limit]
    
    def create_document_version(
        self,
        document_id: str,
        content: str,
        created_by: int,
        change_summary: str
    ) -> DocumentVersion:
        """Создание версии документа"""
        try:
            # Получаем текущую версию
            current_version = 0
            if document_id in self.document_versions:
                current_version = max(v.version_number for v in self.document_versions[document_id])
            
            version_id = f"ver_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            new_version = current_version + 1
            
            # Подсчитываем количество аннотаций
            annotations_count = len(self.get_document_annotations(document_id))
            
            version = DocumentVersion(
                id=version_id,
                document_id=document_id,
                version_number=new_version,
                content=content,
                created_at=datetime.now(),
                created_by=created_by,
                change_summary=change_summary,
                annotations_count=annotations_count
            )
            
            if document_id not in self.document_versions:
                self.document_versions[document_id] = []
            
            self.document_versions[document_id].append(version)
            
            logger.info(f"Created version {new_version} for document {document_id}")
            return version
            
        except Exception as e:
            logger.error(f"Document version creation error: {str(e)}")
            raise
    
    def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """Получение версий документа"""
        return self.document_versions.get(document_id, [])
    
    def get_annotation_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Получение статистики аннотаций"""
        total_annotations = len([a for a in self.annotations.values() if a.status == AnnotationStatus.ACTIVE])
        total_replies = len([r for r in self.annotation_replies.values() if r.status == AnnotationStatus.ACTIVE])
        
        # Статистика по типам
        type_stats = {}
        for annotation_type in AnnotationType:
            count = len([a for a in self.annotations.values() 
                        if a.annotation_type == annotation_type and a.status == AnnotationStatus.ACTIVE])
            type_stats[annotation_type.value] = count
        
        # Статистика пользователя
        user_stats = {}
        if user_id:
            user_annotations = self.get_user_annotations(user_id)
            user_stats = {
                "total_annotations": len(user_annotations),
                "public_annotations": len([a for a in user_annotations if a.is_public]),
                "private_annotations": len([a for a in user_annotations if not a.is_public]),
                "total_replies": len([r for r in self.annotation_replies.values() 
                                    if r.user_id == user_id and r.status == AnnotationStatus.ACTIVE])
            }
        
        return {
            "total_annotations": total_annotations,
            "total_replies": total_replies,
            "type_distribution": type_stats,
            "user_stats": user_stats if user_id else None
        }

# Глобальный экземпляр менеджера аннотаций
annotation_manager = AnnotationManager()

def get_annotation_manager() -> AnnotationManager:
    """Получение экземпляра менеджера аннотаций"""
    return annotation_manager
