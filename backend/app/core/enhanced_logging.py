"""
Улучшенная система логирования и аудита
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
from ..core.config import settings


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityEvent(Enum):
    """Типы событий безопасности"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"
    ADMIN_ACCESS = "admin_access"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    DATA_EXPORT = "data_export"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class EnhancedLogger:
    """Улучшенный логгер с аудитом безопасности"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
        self._setup_security_logger()
        
        # Добавляем методы стандартного логгера
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.debug = self.logger.debug
        self.critical = self.logger.critical
    
    def _setup_logger(self):
        """Настройка основного логгера"""
        if not self.logger.handlers:
            # Создаем форматтер
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Консольный хендлер
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            
            # Файловый хендлер
            log_dir = Path(settings.BASE_DIR) / "logs"
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f"{self.logger.name}.log",
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            
            # Настройка уровня логирования
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def _setup_security_logger(self):
        """Настройка логгера безопасности"""
        self.security_logger = logging.getLogger(f"{self.logger.name}.security")
        if not self.security_logger.handlers:
            # Форматтер для безопасности
            security_formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Файл безопасности
            log_dir = Path(settings.BASE_DIR) / "logs"
            security_handler = logging.FileHandler(
                log_dir / "security.log",
                encoding='utf-8'
            )
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(security_formatter)
            
            self.security_logger.setLevel(logging.WARNING)
            self.security_logger.addHandler(security_handler)
    
    def log_security_event(
        self,
        event: SecurityEvent,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: LogLevel = LogLevel.WARNING
    ):
        """
        Логирует событие безопасности
        
        Args:
            event: Тип события безопасности
            user_id: ID пользователя
            ip_address: IP адрес
            user_agent: User Agent
            details: Дополнительные детали
            severity: Уровень серьезности
        """
        try:
            security_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event.value,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "details": details or {},
                "severity": severity.value
            }
            
            message = json.dumps(security_data, ensure_ascii=False)
            
            if severity == LogLevel.CRITICAL:
                self.security_logger.critical(message)
            elif severity == LogLevel.ERROR:
                self.security_logger.error(message)
            elif severity == LogLevel.WARNING:
                self.security_logger.warning(message)
            else:
                self.security_logger.info(message)
                
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    def log_user_action(
        self,
        action: str,
        user_id: int,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Логирует действие пользователя
        
        Args:
            action: Действие пользователя
            user_id: ID пользователя
            resource: Ресурс
            details: Дополнительные детали
        """
        try:
            action_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "user_id": user_id,
                "resource": resource,
                "details": details or {}
            }
            
            message = json.dumps(action_data, ensure_ascii=False)
            self.logger.info(f"USER_ACTION: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log user action: {e}")
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        """
        Логирует API запрос
        
        Args:
            method: HTTP метод
            path: Путь запроса
            status_code: Код ответа
            response_time: Время ответа
            user_id: ID пользователя
            ip_address: IP адрес
        """
        try:
            request_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "user_id": user_id,
                "ip_address": ip_address
            }
            
            message = json.dumps(request_data, ensure_ascii=False)
            
            if status_code >= 500:
                self.logger.error(f"API_ERROR: {message}")
            elif status_code >= 400:
                self.logger.warning(f"API_WARNING: {message}")
            else:
                self.logger.info(f"API_REQUEST: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to log API request: {e}")
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ):
        """
        Логирует ошибку с контекстом
        
        Args:
            error: Исключение
            context: Контекст ошибки
            user_id: ID пользователя
        """
        try:
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "user_id": user_id
            }
            
            message = json.dumps(error_data, ensure_ascii=False)
            self.logger.error(f"ERROR: {message}", exc_info=True)
            
        except Exception as e:
            self.logger.error(f"Failed to log error: {e}")
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Логирует метрики производительности
        
        Args:
            operation: Операция
            duration: Длительность
            details: Дополнительные детали
        """
        try:
            perf_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation,
                "duration": duration,
                "details": details or {}
            }
            
            message = json.dumps(perf_data, ensure_ascii=False)
            self.logger.info(f"PERFORMANCE: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log performance: {e}")


def get_logger(name: str) -> EnhancedLogger:
    """
    Получает улучшенный логгер
    
    Args:
        name: Имя логгера
        
    Returns:
        Улучшенный логгер
    """
    return EnhancedLogger(name)


# Глобальные логгеры
app_logger = get_logger("app")
security_logger = get_logger("security")
api_logger = get_logger("api")
performance_logger = get_logger("performance")
