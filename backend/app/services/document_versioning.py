"""
Сервис версионирования документов
Управляет версиями юридических документов и их актуальностью
"""

import logging
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentStatus(str, Enum):
    """Статус документа"""
    CURRENT = "current"  # Текущая версия
    SUPERSEDED = "superseded"  # Заменена новой версией
    DRAFT = "draft"  # Черновик
    ARCHIVED = "archived"  # Архивирован

@dataclass
class DocumentVersion:
    """Версия документа"""
    document_id: str
    version: str
    effective_date: Optional[date]
    replaces_version: Optional[str]
    status: DocumentStatus
    last_updated: datetime
    file_hash: str
    content_preview: str
    metadata: Dict[str, Any]

class DocumentVersioningService:
    """Сервис версионирования документов"""
    
    def __init__(self):
        self.versions = {}  # document_id -> List[DocumentVersion]
        
    def extract_version_info(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Извлекает информацию о версии из текста документа"""
        version_info = {
            "version": "1.0.0",
            "effective_date": None,
            "replaces_version": None,
            "status": DocumentStatus.CURRENT,
            "is_draft": False,
            "is_amendment": False
        }
        
        text_lower = text.lower()
        
        # 1. Поиск даты вступления в силу
        effective_date = self._extract_effective_date(text)
        if effective_date:
            version_info["effective_date"] = effective_date
        
        # 2. Поиск номера версии
        version = self._extract_version_number(text, filename)
        if version:
            version_info["version"] = version
        
        # 3. Поиск информации о замене
        replaces_version = self._extract_replaces_version(text)
        if replaces_version:
            version_info["replaces_version"] = replaces_version
            version_info["status"] = DocumentStatus.SUPERSEDED
        
        # 4. Проверка на черновик
        if self._is_draft(text):
            version_info["is_draft"] = True
            version_info["status"] = DocumentStatus.DRAFT
        
        # 5. Проверка на поправки
        if self._is_amendment(text):
            version_info["is_amendment"] = True
        
        return version_info
    
    def _extract_effective_date(self, text: str) -> Optional[date]:
        """Извлекает дату вступления в силу"""
        # Паттерны для поиска дат
        date_patterns = [
            r'вступает в силу с (\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'действует с (\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'принят (\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'утвержден (\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'от (\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4}) г\.',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4}) года'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    day, month, year = matches[0]
                    return date(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    def _extract_version_number(self, text: str, filename: str = None) -> Optional[str]:
        """Извлекает номер версии"""
        # Поиск в тексте
        version_patterns = [
            r'версия\s+(\d+\.\d+\.\d+)',
            r'версия\s+(\d+\.\d+)',
            r'версия\s+(\d+)',
            r'редакция\s+(\d+\.\d+\.\d+)',
            r'редакция\s+(\d+\.\d+)',
            r'редакция\s+(\d+)',
            r'изменения\s+от\s+(\d+\.\d+\.\d+)',
            r'в редакции\s+(\d+\.\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Поиск в имени файла
        if filename:
            filename_patterns = [
                r'v(\d+\.\d+\.\d+)',
                r'v(\d+\.\d+)',
                r'v(\d+)',
                r'(\d+\.\d+\.\d+)',
                r'(\d+\.\d+)',
                r'(\d+)'
            ]
            
            for pattern in filename_patterns:
                matches = re.findall(pattern, filename)
                if matches:
                    return matches[0]
        
        return None
    
    def _extract_replaces_version(self, text: str) -> Optional[str]:
        """Извлекает информацию о заменяемой версии"""
        replace_patterns = [
            r'заменяет\s+версию\s+(\d+\.\d+\.\d+)',
            r'заменяет\s+редакцию\s+(\d+\.\d+\.\d+)',
            r'вместо\s+версии\s+(\d+\.\d+\.\d+)',
            r'отменяет\s+версию\s+(\d+\.\d+\.\d+)'
        ]
        
        for pattern in replace_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _is_draft(self, text: str) -> bool:
        """Проверяет, является ли документ черновиком"""
        draft_indicators = [
            'черновик', 'проект', 'проект закона', 'проект постановления',
            'для обсуждения', 'на рассмотрении', 'в разработке',
            'предварительная версия', 'рабочая версия'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in draft_indicators)
    
    def _is_amendment(self, text: str) -> bool:
        """Проверяет, является ли документ поправкой"""
        amendment_indicators = [
            'поправка', 'изменения', 'дополнения', 'уточнения',
            'в редакции', 'с изменениями', 'с дополнениями',
            'внесены изменения', 'внесены дополнения'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in amendment_indicators)
    
    def create_document_version(self, 
                              document_id: str,
                              text: str,
                              filename: str = None,
                              file_hash: str = None,
                              metadata: Dict[str, Any] = None) -> DocumentVersion:
        """Создает новую версию документа"""
        
        # Извлекаем информацию о версии
        version_info = self.extract_version_info(text, filename)
        
        # Создаем версию
        version = DocumentVersion(
            document_id=document_id,
            version=version_info["version"],
            effective_date=version_info["effective_date"],
            replaces_version=version_info["replaces_version"],
            status=version_info["status"],
            last_updated=datetime.now(),
            file_hash=file_hash or "",
            content_preview=text[:200] + "..." if len(text) > 200 else text,
            metadata=metadata or {}
        )
        
        # Добавляем в список версий
        if document_id not in self.versions:
            self.versions[document_id] = []
        
        self.versions[document_id].append(version)
        
        # Обновляем статусы предыдущих версий
        self._update_version_statuses(document_id)
        
        return version
    
    def _update_version_statuses(self, document_id: str):
        """Обновляет статусы версий документа"""
        if document_id not in self.versions:
            return
        
        versions = self.versions[document_id]
        
        # Сортируем по дате создания
        versions.sort(key=lambda v: v.last_updated)
        
        # Последняя версия - текущая
        if versions:
            versions[-1].status = DocumentStatus.CURRENT
            
            # Предыдущие версии - заменены
            for version in versions[:-1]:
                if version.status == DocumentStatus.CURRENT:
                    version.status = DocumentStatus.SUPERSEDED
    
    def get_current_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Получает текущую версию документа"""
        if document_id not in self.versions:
            return None
        
        versions = self.versions[document_id]
        current_versions = [v for v in versions if v.status == DocumentStatus.CURRENT]
        
        return current_versions[0] if current_versions else None
    
    def get_all_versions(self, document_id: str) -> List[DocumentVersion]:
        """Получает все версии документа"""
        return self.versions.get(document_id, [])
    
    def search_in_current_versions(self, query: str) -> List[DocumentVersion]:
        """Поиск только в текущих версиях"""
        current_versions = []
        for document_id, versions in self.versions.items():
            current_version = self.get_current_version(document_id)
            if current_version and query.lower() in current_version.content_preview.lower():
                current_versions.append(current_version)
        
        return current_versions
    
    def search_in_all_versions(self, query: str) -> List[DocumentVersion]:
        """Поиск во всех версиях"""
        matching_versions = []
        for document_id, versions in self.versions.items():
            for version in versions:
                if query.lower() in version.content_preview.lower():
                    matching_versions.append(version)
        
        return matching_versions
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """Получает статистику версий"""
        total_documents = len(self.versions)
        total_versions = sum(len(versions) for versions in self.versions.values())
        
        status_counts = {}
        for versions in self.versions.values():
            for version in versions:
                status = version.status
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_versions": total_versions,
            "status_counts": status_counts,
            "average_versions_per_document": total_versions / total_documents if total_documents > 0 else 0
        }

# Глобальный экземпляр сервиса версионирования
document_versioning_service = DocumentVersioningService()
