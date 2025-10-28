import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import difflib
import re

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Типы изменений"""
    INSERT = "insert"  # Добавление
    DELETE = "delete"  # Удаление
    REPLACE = "replace"  # Замена
    MOVE = "move"  # Перемещение
    UNCHANGED = "unchanged"  # Без изменений

@dataclass
class TextChange:
    """Изменение в тексте"""
    change_type: ChangeType
    old_text: str
    new_text: str
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    line_number: int

@dataclass
class DocumentDiff:
    """Различия между версиями документа"""
    old_version_id: str
    new_version_id: str
    changes: List[TextChange]
    total_changes: int
    added_lines: int
    deleted_lines: int
    modified_lines: int
    similarity_score: float
    created_at: datetime

class DocumentDiffEngine:
    """Движок для сравнения документов"""
    
    def __init__(self):
        self.diffs: Dict[str, DocumentDiff] = {}
    
    def compare_documents(
        self,
        old_content: str,
        new_content: str,
        old_version_id: str,
        new_version_id: str
    ) -> DocumentDiff:
        """Сравнение двух версий документа"""
        try:
            # Разбиваем на строки
            old_lines = old_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            
            # Создаем diff
            differ = difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"version_{old_version_id}",
                tofile=f"version_{new_version_id}",
                lineterm=""
            )
            
            # Парсим изменения
            changes = self._parse_unified_diff(list(differ), old_lines, new_lines)
            
            # Подсчитываем статистику
            added_lines = len([c for c in changes if c.change_type == ChangeType.INSERT])
            deleted_lines = len([c for c in changes if c.change_type == ChangeType.DELETE])
            modified_lines = len([c for c in changes if c.change_type == ChangeType.REPLACE])
            
            # Вычисляем коэффициент схожести
            similarity_score = self._calculate_similarity(old_content, new_content)
            
            # Создаем объект diff
            diff_id = f"diff_{old_version_id}_{new_version_id}"
            document_diff = DocumentDiff(
                old_version_id=old_version_id,
                new_version_id=new_version_id,
                changes=changes,
                total_changes=len(changes),
                added_lines=added_lines,
                deleted_lines=deleted_lines,
                modified_lines=modified_lines,
                similarity_score=similarity_score,
                created_at=datetime.now()
            )
            
            self.diffs[diff_id] = document_diff
            
            logger.info(f"Created diff between versions {old_version_id} and {new_version_id}")
            return document_diff
            
        except Exception as e:
            logger.error(f"Document comparison error: {str(e)}")
            raise
    
    def _parse_unified_diff(
        self,
        diff_lines: List[str],
        old_lines: List[str],
        new_lines: List[str]
    ) -> List[TextChange]:
        """Парсинг unified diff"""
        changes = []
        old_line_num = 0
        new_line_num = 0
        
        for line in diff_lines:
            if line.startswith('@@'):
                # Парсим заголовок hunk
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    old_line_num = old_start - 1
                    new_line_num = new_start - 1
            elif line.startswith('+'):
                # Добавленная строка
                new_text = line[1:]
                change = TextChange(
                    change_type=ChangeType.INSERT,
                    old_text="",
                    new_text=new_text,
                    old_start=old_line_num,
                    old_end=old_line_num,
                    new_start=new_line_num,
                    new_end=new_line_num,
                    line_number=new_line_num
                )
                changes.append(change)
                new_line_num += 1
            elif line.startswith('-'):
                # Удаленная строка
                old_text = line[1:]
                change = TextChange(
                    change_type=ChangeType.DELETE,
                    old_text=old_text,
                    new_text="",
                    old_start=old_line_num,
                    old_end=old_line_num,
                    new_start=new_line_num,
                    new_end=new_line_num,
                    line_number=old_line_num
                )
                changes.append(change)
                old_line_num += 1
            elif line.startswith(' '):
                # Неизмененная строка
                old_line_num += 1
                new_line_num += 1
        
        return changes
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление коэффициента схожести"""
        try:
            # Используем SequenceMatcher для вычисления схожести
            matcher = difflib.SequenceMatcher(None, text1, text2)
            return matcher.ratio()
        except Exception:
            return 0.0
    
    def get_diff(self, diff_id: str) -> Optional[DocumentDiff]:
        """Получение diff по ID"""
        return self.diffs.get(diff_id)
    
    def get_document_diffs(self, document_id: str) -> List[DocumentDiff]:
        """Получение всех diff для документа"""
        document_diffs = []
        
        for diff in self.diffs.values():
            if (diff.old_version_id.startswith(document_id) or 
                diff.new_version_id.startswith(document_id)):
                document_diffs.append(diff)
        
        # Сортируем по дате создания
        document_diffs.sort(key=lambda x: x.created_at, reverse=True)
        
        return document_diffs
    
    def compare_versions(
        self,
        version1_id: str,
        version2_id: str,
        version1_content: str,
        version2_content: str
    ) -> DocumentDiff:
        """Сравнение двух конкретных версий"""
        diff_id = f"diff_{version1_id}_{version2_id}"
        
        # Проверяем, есть ли уже такой diff
        existing_diff = self.get_diff(diff_id)
        if existing_diff:
            return existing_diff
        
        # Создаем новый diff
        return self.compare_documents(
            version1_content,
            version2_content,
            version1_id,
            version2_id
        )
    
    def get_change_summary(self, diff: DocumentDiff) -> Dict[str, Any]:
        """Получение сводки изменений"""
        return {
            "total_changes": diff.total_changes,
            "added_lines": diff.added_lines,
            "deleted_lines": diff.deleted_lines,
            "modified_lines": diff.modified_lines,
            "similarity_score": diff.similarity_score,
            "change_percentage": (diff.total_changes / max(len(diff.changes), 1)) * 100,
            "created_at": diff.created_at.isoformat()
        }
    
    def get_line_changes(self, diff: DocumentDiff, line_number: int) -> List[TextChange]:
        """Получение изменений для конкретной строки"""
        return [change for change in diff.changes if change.line_number == line_number]
    
    def get_changes_by_type(self, diff: DocumentDiff, change_type: ChangeType) -> List[TextChange]:
        """Получение изменений по типу"""
        return [change for change in diff.changes if change.change_type == change_type]
    
    def merge_changes(self, base_content: str, changes: List[TextChange]) -> str:
        """Применение изменений к базовому контенту"""
        try:
            lines = base_content.splitlines(keepends=True)
            
            # Сортируем изменения по позиции (в обратном порядке для корректного применения)
            sorted_changes = sorted(changes, key=lambda x: x.old_start, reverse=True)
            
            for change in sorted_changes:
                if change.change_type == ChangeType.INSERT:
                    lines.insert(change.new_start, change.new_text)
                elif change.change_type == ChangeType.DELETE:
                    if change.old_start < len(lines):
                        lines.pop(change.old_start)
                elif change.change_type == ChangeType.REPLACE:
                    if change.old_start < len(lines):
                        lines[change.old_start] = change.new_text
            
            return ''.join(lines)
            
        except Exception as e:
            logger.error(f"Merge changes error: {str(e)}")
            raise
    
    def get_diff_stats(self) -> Dict[str, Any]:
        """Получение статистики diff"""
        total_diffs = len(self.diffs)
        total_changes = sum(diff.total_changes for diff in self.diffs.values())
        avg_changes = total_changes / total_diffs if total_diffs > 0 else 0
        
        return {
            "total_diffs": total_diffs,
            "total_changes": total_changes,
            "average_changes_per_diff": avg_changes,
            "most_changed_document": self._get_most_changed_document()
        }
    
    def _get_most_changed_document(self) -> Optional[str]:
        """Получение документа с наибольшим количеством изменений"""
        if not self.diffs:
            return None
        
        document_changes = {}
        
        for diff in self.diffs.values():
            doc_id = diff.old_version_id.split('_')[0]  # Извлекаем ID документа
            if doc_id not in document_changes:
                document_changes[doc_id] = 0
            document_changes[doc_id] += diff.total_changes
        
        return max(document_changes.items(), key=lambda x: x[1])[0] if document_changes else None

# Глобальный экземпляр движка diff
document_diff_engine = DocumentDiffEngine()

def get_document_diff_engine() -> DocumentDiffEngine:
    """Получение экземпляра движка diff"""
    return document_diff_engine
