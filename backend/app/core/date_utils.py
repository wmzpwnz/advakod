"""
Date utilities for legal document filtering
Provides consistent ISO8601 date handling and comparison
"""

import re
from datetime import datetime, date
from typing import Optional, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DateUtils:
    """Utilities for handling dates in legal documents"""
    
    # Common date formats found in legal documents
    DATE_PATTERNS = [
        # ISO format
        r'(\d{4})-(\d{2})-(\d{2})',  # 2024-01-01
        # Russian format
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 01.01.2024
        # Alternative formats
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 01/01/2024
        r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2024.01.01
    ]
    
    @staticmethod
    def normalize_date(date_input: Union[str, date, datetime, None]) -> Optional[str]:
        """
        Normalize date to ISO8601 format (YYYY-MM-DD)
        
        Args:
            date_input: Date in various formats
            
        Returns:
            ISO8601 date string or None if invalid
        """
        if date_input is None:
            return None
            
        if isinstance(date_input, datetime):
            return date_input.date().isoformat()
            
        if isinstance(date_input, date):
            return date_input.isoformat()
            
        if isinstance(date_input, str):
            # Try to parse string date
            return DateUtils._parse_date_string(date_input)
            
        logger.warning(f"Unsupported date type: {type(date_input)}")
        return None
    
    @staticmethod
    def _parse_date_string(date_str: str) -> Optional[str]:
        """Parse date string in various formats"""
        if not date_str or not date_str.strip():
            return None
            
        date_str = date_str.strip()
        
        # Try ISO format first
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                # Validate by parsing
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
        except ValueError:
            pass
        
        # Try Russian format (dd.mm.yyyy)
        try:
            match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', date_str)
            if match:
                day, month, year = match.groups()
                parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d')
                return parsed_date.date().isoformat()
        except ValueError:
            pass
        
        # Try US format (mm/dd/yyyy)
        try:
            match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
            if match:
                month, day, year = match.groups()
                parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d')
                return parsed_date.date().isoformat()
        except ValueError:
            pass
        
        # Try alternative format (yyyy.mm.dd)
        try:
            match = re.match(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
            if match:
                year, month, day = match.groups()
                parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d')
                return parsed_date.date().isoformat()
        except ValueError:
            pass
        
        logger.warning(f"Could not parse date string: {date_str}")
        return None
    
    @staticmethod
    def parse_russian_date(date_str: str) -> Optional[datetime]:
        """
        Парсит русские форматы дат
        
        Args:
            date_str: Строка с датой в русском формате
            
        Returns:
            datetime объект или None
        """
        if not isinstance(date_str, str):
            return None
        
        date_str = date_str.strip()
        
        # Русские месяцы
        month_names = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
            'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
            'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
            'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
        }
        
        # Паттерны для русских дат
        patterns = [
            # "1 января 2024", "15 мая 2023"
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',
            # "января 2024", "май 2023" (без дня)
            r'(\w+)\s+(\d{4})',
            # "1 янв. 2024" (сокращенные месяцы)
            r'(\d{1,2})\s+(\w+)\.\s+(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:  # день месяц год
                    day, month_str, year = groups
                    day = int(day)
                elif len(groups) == 2:  # месяц год
                    month_str, year = groups
                    day = 1
                else:
                    continue
                
                # Поиск месяца
                month = None
                month_str = month_str.lower().rstrip('.')
                
                for month_name, month_num in month_names.items():
                    if month_str.startswith(month_name[:3]):  # Минимум 3 символа
                        month = month_num
                        break
                
                if month:
                    try:
                        return datetime(int(year), month, day)
                    except ValueError:
                        continue
        
        return None
    
    @staticmethod
    def create_date_filter(situation_date: Optional[Union[str, date, datetime]] = None) -> Dict[str, Any]:
        """
        Create ChromaDB/Qdrant compatible date filter
        
        Args:
            situation_date: Date to filter by (default: today)
            
        Returns:
            Filter dictionary for vector database
        """
        if situation_date is None:
            situation_date = datetime.now().date()
        
        # Normalize the situation date
        situation_iso = DateUtils.normalize_date(situation_date)
        
        if not situation_iso:
            logger.warning("Invalid situation date, using today")
            situation_iso = datetime.now().date().isoformat()
        
        # Create filter for ChromaDB
        # Document is valid if:
        # 1. valid_from is None OR valid_from <= situation_date
        # 2. valid_to is None OR valid_to >= situation_date
        
        date_filter = {
            "$and": [
                # Valid from condition
                {
                    "$or": [
                        {"valid_from": {"$eq": None}},  # No start date (always valid)
                        {"valid_from": {"$lte": situation_iso}}  # Start date <= situation
                    ]
                },
                # Valid to condition  
                {
                    "$or": [
                        {"valid_to": {"$eq": None}},  # No end date (still valid)
                        {"valid_to": {"$gte": situation_iso}}  # End date >= situation
                    ]
                }
            ]
        }
        
        logger.info(f"Created date filter for situation date: {situation_iso}")
        return date_filter
    
    @staticmethod
    def validate_date_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize date fields in metadata
        
        Args:
            metadata: Document metadata
            
        Returns:
            Metadata with normalized dates
        """
        validated_metadata = metadata.copy()
        
        date_fields = ['valid_from', 'valid_to', 'created_at', 'updated_at', 'effective_date']
        
        for field in date_fields:
            if field in validated_metadata:
                original_value = validated_metadata[field]
                normalized_value = DateUtils.normalize_date(original_value)
                
                if normalized_value != original_value:
                    logger.info(f"Normalized {field}: {original_value} -> {normalized_value}")
                    validated_metadata[field] = normalized_value
        
        return validated_metadata
    
    @staticmethod
    def is_date_valid_for_situation(doc_metadata: Dict[str, Any], 
                                   situation_date: Optional[Union[str, date, datetime]] = None) -> bool:
        """
        Check if document is valid for given situation date
        
        Args:
            doc_metadata: Document metadata with date fields
            situation_date: Date to check against (default: today)
            
        Returns:
            True if document is valid for the situation date
        """
        if situation_date is None:
            situation_date = datetime.now().date()
        
        situation_iso = DateUtils.normalize_date(situation_date)
        
        if not situation_iso:
            return True  # If we can't parse situation date, include document
        
        # Check valid_from
        valid_from = doc_metadata.get('valid_from')
        if valid_from is not None:
            valid_from_iso = DateUtils.normalize_date(valid_from)
            if valid_from_iso and valid_from_iso > situation_iso:
                return False  # Document not yet valid
        
        # Check valid_to
        valid_to = doc_metadata.get('valid_to')
        if valid_to is not None:
            valid_to_iso = DateUtils.normalize_date(valid_to)
            if valid_to_iso and valid_to_iso < situation_iso:
                return False  # Document no longer valid
        
        return True
    
    @staticmethod
    def extract_dates_from_text(text: str) -> list[str]:
        """
        Extract date mentions from legal text
        
        Args:
            text: Text to search for dates
            
        Returns:
            List of normalized dates found in text
        """
        dates_found = []
        
        for pattern in DateUtils.DATE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str = match.group(0)
                normalized = DateUtils._parse_date_string(date_str)
                if normalized and normalized not in dates_found:
                    dates_found.append(normalized)
        
        return sorted(dates_found)


# Global instance
date_utils = DateUtils()