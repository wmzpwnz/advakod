import os
import hashlib
import mimetypes
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import aiofiles
import aiohttp
from pathlib import Path

class CDNManager:
    """Менеджер для работы с CDN и статическими ресурсами"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.cdn_url = os.getenv("CDN_URL", "")
        self.cache_dir = Path("static_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Настройки кэширования
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 час по умолчанию
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        
        # Поддерживаемые типы файлов
        self.supported_types = {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
            "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "videos": [".mp4", ".avi", ".mov", ".wmv", ".flv"],
            "audio": [".mp3", ".wav", ".ogg", ".aac", ".flac"]
        }
    
    def get_file_hash(self, file_path: str) -> str:
        """Генерация хеша файла для кэширования"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def get_cache_key(self, file_path: str) -> str:
        """Генерация ключа кэша"""
        file_hash = self.get_file_hash(file_path)
        return f"{file_hash}_{os.path.basename(file_path)}"
    
    def is_file_cached(self, cache_key: str) -> bool:
        """Проверка наличия файла в кэше"""
        cache_file = self.cache_dir / cache_key
        return cache_file.exists()
    
    def get_cached_file_path(self, cache_key: str) -> str:
        """Получение пути к кэшированному файлу"""
        return str(self.cache_dir / cache_key)
    
    def cache_file(self, file_path: str, cache_key: str) -> None:
        """Кэширование файла"""
        import shutil
        cache_file = self.cache_dir / cache_key
        shutil.copy2(file_path, cache_file)
    
    def get_file_type(self, file_path: str) -> str:
        """Определение типа файла"""
        ext = Path(file_path).suffix.lower()
        
        for file_type, extensions in self.supported_types.items():
            if ext in extensions:
                return file_type
        
        return "other"
    
    def get_optimized_url(self, file_path: str) -> str:
        """Получение оптимизированного URL для файла"""
        if self.cdn_url:
            cache_key = self.get_cache_key(file_path)
            return f"{self.cdn_url}/{cache_key}"
        
        return file_path
    
    def setup_static_routes(self):
        """Настройка маршрутов для статических файлов"""
        
        # Маршрут для кэшированных файлов
        @self.app.get("/cdn/{cache_key}")
        async def serve_cached_file(cache_key: str, request: Request):
            """Обслуживание кэшированных файлов"""
            cache_file = self.cache_dir / cache_key
            
            if not cache_file.exists():
                return Response(status_code=404)
            
            # Проверяем заголовки кэширования
            if_none_match = request.headers.get("if-none-match")
            if if_none_match == cache_key:
                return Response(status_code=304)
            
            # Определяем MIME тип
            mime_type, _ = mimetypes.guess_type(str(cache_file))
            
            return FileResponse(
                cache_file,
                media_type=mime_type,
                headers={
                    "Cache-Control": f"public, max-age={self.cache_ttl}",
                    "ETag": cache_key,
                    "Last-Modified": cache_file.stat().st_mtime
                }
            )
        
        # Маршрут для загрузки и кэширования файлов
        @self.app.post("/cdn/upload")
        async def upload_and_cache_file(request: Request):
            """Загрузка и кэширование файла"""
            try:
                form = await request.form()
                file = form.get("file")
                
                if not file:
                    return {"error": "No file provided"}
                
                # Проверяем размер файла
                if file.size > self.max_file_size:
                    return {"error": "File too large"}
                
                # Генерируем уникальное имя файла
                file_hash = hashlib.md5(file.file.read()).hexdigest()
                file.file.seek(0)  # Возвращаемся к началу файла
                
                cache_key = f"{file_hash}_{file.filename}"
                cache_file = self.cache_dir / cache_key
                
                # Сохраняем файл в кэш
                async with aiofiles.open(cache_file, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                return {
                    "cache_key": cache_key,
                    "url": f"/cdn/{cache_key}",
                    "size": file.size,
                    "type": self.get_file_type(file.filename)
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        # Маршрут для очистки кэша
        @self.app.delete("/cdn/cache")
        async def clear_cache():
            """Очистка кэша CDN"""
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                
                return {"message": "Cache cleared successfully"}
                
            except Exception as e:
                return {"error": str(e)}
        
        # Маршрут для получения статистики кэша
        @self.app.get("/cdn/stats")
        async def get_cache_stats():
            """Получение статистики кэша"""
            try:
                total_files = 0
                total_size = 0
                files_by_type = {}
                
                for file_path in self.cache_dir.iterdir():
                    if file_path.is_file():
                        total_files += 1
                        total_size += file_path.stat().st_size
                        
                        file_type = self.get_file_type(file_path.name)
                        files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
                
                return {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "files_by_type": files_by_type,
                    "cache_ttl": self.cache_ttl,
                    "max_file_size": self.max_file_size
                }
                
            except Exception as e:
                return {"error": str(e)}

# Глобальный экземпляр менеджера CDN
cdn_manager = None

def get_cdn_manager() -> CDNManager:
    """Получение экземпляра менеджера CDN"""
    return cdn_manager

def setup_cdn(app: FastAPI):
    """Настройка CDN для приложения"""
    global cdn_manager
    cdn_manager = CDNManager(app)
    cdn_manager.setup_static_routes()
    
    # Настраиваем статические файлы
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    return cdn_manager
