"""
Strict domain whitelist configuration for ADVAKOD production security.
This module enforces strict domain validation to prevent localhost and unauthorized domains.
"""

from typing import List, Set
import re
from urllib.parse import urlparse
import os


class DomainWhitelist:
    """Strict domain whitelist manager for production security."""
    
    # Production domains - NEVER include localhost here
    PRODUCTION_DOMAINS: Set[str] = {
        "advacodex.com",
        "www.advacodex.com",
    }
    
    # Docker service names (internal communication only)
    INTERNAL_SERVICES: Set[str] = {
        "backend",
        "frontend", 
        "nginx",
        "postgres",
        "redis",
        "qdrant",
        "advakod_backend",
        "advakod_frontend",
        "advakod_nginx",
        "advakod_postgres",
        "advakod_redis",
        "advakod_qdrant"
    }
    
    # Development domains (only allowed in development environment)
    DEVELOPMENT_DOMAINS: Set[str] = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0"
    }
    
    def __init__(self, environment: str = "production"):
        """Initialize domain whitelist based on environment."""
        self.environment = environment.lower()
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """Validate that environment is properly set."""
        if self.environment not in ["development", "production", "testing"]:
            raise ValueError(f"Invalid environment: {self.environment}")
    
    def get_allowed_cors_origins(self) -> List[str]:
        """Get allowed CORS origins based on environment."""
        if self.environment == "development":
            # Development: allow localhost with specific ports
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "https://localhost:3000",
                "https://localhost:3001"
            ]
        elif self.environment == "production":
            # Production: only HTTPS production domains
            return [
                f"https://{domain}" for domain in self.PRODUCTION_DOMAINS
            ]
        else:  # testing
            return ["http://testserver"]
    
    def get_allowed_websocket_origins(self) -> List[str]:
        """Get allowed WebSocket origins based on environment."""
        if self.environment == "development":
            return [
                "ws://localhost:3000",
                "ws://localhost:3001",
                "ws://127.0.0.1:3000", 
                "ws://127.0.0.1:3001",
                "wss://localhost:3000",
                "wss://localhost:3001"
            ]
        elif self.environment == "production":
            # Production: only WSS production domains
            return [
                f"wss://{domain}" for domain in self.PRODUCTION_DOMAINS
            ]
        else:  # testing
            return ["ws://testserver"]
    
    def get_trusted_hosts(self) -> List[str]:
        """Get trusted hosts based on environment."""
        trusted = list(self.INTERNAL_SERVICES)
        
        # КРИТИЧНО: Добавляем localhost для работы системы
        trusted.extend(["localhost", "127.0.0.1", "0.0.0.0"])
        
        if self.environment == "development":
            trusted.extend(self.DEVELOPMENT_DOMAINS)
            trusted.extend([f"{domain}:3000" for domain in self.DEVELOPMENT_DOMAINS])
            trusted.extend([f"{domain}:3001" for domain in self.DEVELOPMENT_DOMAINS])
        elif self.environment == "production":
            trusted.extend(self.PRODUCTION_DOMAINS)
            trusted.extend([f"*.{domain}" for domain in self.PRODUCTION_DOMAINS])
        
        return trusted
    
    def validate_origin(self, origin: str) -> bool:
        """Validate if an origin is allowed."""
        if not origin:
            return False
        
        try:
            parsed = urlparse(origin)
            domain = parsed.hostname
            
            if not domain:
                return False
            
            # Check against allowed origins
            allowed_origins = self.get_allowed_cors_origins() + self.get_allowed_websocket_origins()
            
            # Direct match
            if origin in allowed_origins:
                return True
            
            # Domain match for production
            if self.environment == "production":
                return domain in self.PRODUCTION_DOMAINS
            
            # Development domain match
            if self.environment == "development":
                return domain in self.DEVELOPMENT_DOMAINS or domain in self.PRODUCTION_DOMAINS
            
            return False
            
        except Exception:
            return False
    
    def validate_host(self, host: str) -> bool:
        """Validate if a host is trusted."""
        if not host:
            return False
        
        # Remove port if present
        host_without_port = host.split(':')[0]
        
        trusted_hosts = self.get_trusted_hosts()
        
        # Direct match
        if host in trusted_hosts or host_without_port in trusted_hosts:
            return True
        
        # Wildcard match for production subdomains
        if self.environment == "production":
            for domain in self.PRODUCTION_DOMAINS:
                if host_without_port.endswith(f".{domain}"):
                    return True
        
        return False
    
    def block_localhost_in_production(self) -> None:
        """Raise error if localhost is detected in production environment."""
        if self.environment == "production":
            # Check environment variables for localhost
            dangerous_vars = []
            
            for key, value in os.environ.items():
                if value and isinstance(value, str):
                    if re.search(r'localhost|127\.0\.0\.1', value, re.IGNORECASE):
                        # Skip development-specific variables
                        if not any(dev_key in key.lower() for dev_key in ['dev', 'test', 'local']):
                            dangerous_vars.append(f"{key}={value}")
            
            if dangerous_vars:
                raise ValueError(
                    f"Localhost references found in production environment variables: "
                    f"{', '.join(dangerous_vars)}. This is a security risk!"
                )
    
    def get_nginx_allowed_domains(self) -> List[str]:
        """Get domains allowed in Nginx configuration."""
        if self.environment == "production":
            return list(self.PRODUCTION_DOMAINS)
        else:
            return list(self.DEVELOPMENT_DOMAINS) + list(self.PRODUCTION_DOMAINS)
    
    @classmethod
    def create_for_environment(cls, environment: str = None) -> 'DomainWhitelist':
        """Factory method to create domain whitelist for current environment."""
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        whitelist = cls(environment)
        
        # Block localhost in production
        if environment == "production":
            whitelist.block_localhost_in_production()
        
        return whitelist


# Global instance
domain_whitelist = DomainWhitelist.create_for_environment()