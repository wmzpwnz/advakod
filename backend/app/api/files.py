"""
API для загрузки и обработки файлов
"""
import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()

# Создаем директорию для загрузок если её нет
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Разрешенные типы файлов
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'txt', 'rtf',
    'jpg', 'jpeg', 'png', 'gif', 'bmp',
    'xls', 'xlsx', 'csv'
}

# Максимальный размер файла (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file(file: UploadFile) -> bool:
    """Проверка файла на валидность"""
    # Проверяем размер файла
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False
    
    # Проверяем расширение файла
    if file.filename:
        extension = file.filename.split('.')[-1].lower()
        return extension in ALLOWED_EXTENSIONS
    
    return False


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Загрузка файла"""
    
    # Проверяем валидность файла
    if not validate_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый тип файла или размер превышает 10MB"
        )
    
    try:
        # Генерируем уникальное имя файла
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Получаем размер файла
        file_size = len(content)
        
        logger.info(f"File uploaded: {file.filename} -> {unique_filename} ({file_size} bytes)")
        
        return {
            "filename": file.filename,
            "unique_filename": unique_filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_type": file.content_type,
            "message": "Файл успешно загружен"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке файла"
        )


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Загрузка нескольких файлов"""
    
    if len(files) > 5:  # Максимум 5 файлов за раз
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимум 5 файлов за раз"
        )
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            if validate_file(file):
                # Генерируем уникальное имя файла
                file_extension = file.filename.split('.')[-1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, unique_filename)
                
                # Сохраняем файл
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                uploaded_files.append({
                    "filename": file.filename,
                    "unique_filename": unique_filename,
                    "file_path": file_path,
                    "file_size": len(content),
                    "content_type": file.content_type
                })
            else:
                errors.append(f"Файл {file.filename} не прошел валидацию")
                
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            errors.append(f"Ошибка при загрузке файла {file.filename}")
    
    return {
        "uploaded_files": uploaded_files,
        "errors": errors,
        "message": f"Загружено {len(uploaded_files)} файлов"
    }


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Скачивание файла"""
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.delete("/delete/{filename}")
async def delete_file(
    filename: str,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Удаление файла"""
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    try:
        os.remove(file_path)
        logger.info(f"File deleted: {filename}")
        
        return {
            "message": "Файл успешно удален",
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении файла"
        )


@router.get("/list")
async def list_files(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получение списка загруженных файлов"""
    
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    files.append({
                        "filename": filename,
                        "file_size": file_size,
                        "created_at": os.path.getctime(file_path)
                    })
        
        return {
            "files": files,
            "total_files": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка файлов"
        )
