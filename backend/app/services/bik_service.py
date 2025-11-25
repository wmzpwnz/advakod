"""
Сервис для работы со справочником БИК
Загружает данные с сайта ЦБ РФ и хранит в локальной БД
"""
import logging
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.bik_directory import BIKDirectory

logger = logging.getLogger(__name__)


class BIKService:
    """Сервис для работы со справочником БИК"""
    
    def __init__(self):
        self.cbr_base_url = "https://www.cbr.ru"
        self.bik_directory_url = f"{self.cbr_base_url}/Queries/UniDbQuery/DownloadExcel/UniDbQuery"
        self.timeout = 30.0
    
    async def get_bank_by_bik(
        self,
        bik: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Получает данные банка по БИК из локальной БД
        
        Args:
            bik: БИК банка (9 цифр)
            db: Сессия БД
            
        Returns:
            Словарь с данными банка или None
        """
        # Валидация БИК
        if not bik or not bik.isdigit() or len(bik) != 9:
            logger.warning(f"Некорректный БИК: {bik}")
            return None
        
        try:
            # Ищем в локальной БД
            result = await asyncio.to_thread(
                db.execute,
                select(BIKDirectory).where(BIKDirectory.bik == bik)
            )
            bank = result.scalar_one_or_none()
            
            if bank:
                return {
                    "name": bank.name,
                    "name_full": bank.name_full or bank.name,
                    "bik": bank.bik,
                    "correspondent_account": bank.correspondent_account,
                    "swift": bank.swift,
                    "address": bank.address,
                    "address_postal": bank.address_postal,
                    "phone": bank.phone,
                    "okpo": bank.okpo
                }
            
            logger.debug(f"Банк с БИК {bik} не найден в локальной БД")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска банка по БИК {bik}: {e}")
            return None
    
    async def download_and_update_directory(self, db: Session) -> bool:
        """
        Скачивает справочник БИК с сайта ЦБ РФ и обновляет БД
        
        Args:
            db: Сессия БД
            
        Returns:
            True если успешно, False иначе
        """
        try:
            logger.info("Начинаем загрузку справочника БИК с сайта ЦБ РФ")
            
            # Скачиваем файл
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "UniDbQueryID": "BIC"  # Идентификатор запроса БИК
                }
                
                response = await client.get(
                    self.bik_directory_url,
                    params=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*"
                    }
                )
                response.raise_for_status()
                
                # Сохраняем во временный файл
                import tempfile
                import os
                from pathlib import Path
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                try:
                    # Парсим Excel файл
                    banks_data = await self._parse_excel_file(tmp_path)
                    
                    if not banks_data:
                        logger.error("Не удалось распарсить файл справочника БИК")
                        return False
                    
                    # Обновляем БД
                    await self._update_database(banks_data, db)
                    
                    logger.info(f"Справочник БИК успешно обновлен. Записей: {len(banks_data)}")
                    return True
                    
                finally:
                    # Удаляем временный файл
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
        except httpx.TimeoutException:
            logger.error("Таймаут при загрузке справочника БИК")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при загрузке справочника БИК: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при загрузке справочника БИК: {e}")
            return False
    
    async def _parse_excel_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Парсит Excel файл со справочником БИК
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Список словарей с данными банков
        """
        try:
            import pandas as pd
            
            # Читаем Excel файл
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Преобразуем в список словарей
            banks_data = []
            
            for _, row in df.iterrows():
                # Адаптируем под структуру файла ЦБ РФ
                # Структура может меняться, поэтому используем гибкий парсинг
                bik = str(row.get('БИК', '')).strip()
                if not bik or len(bik) != 9 or not bik.isdigit():
                    continue
                
                bank_data = {
                    'bik': bik,
                    'name': str(row.get('Наименование', row.get('Название', ''))).strip(),
                    'name_full': str(row.get('Полное наименование', '')).strip() or None,
                    'correspondent_account': str(row.get('Корр. счет', row.get('Корреспондентский счет', ''))).strip() or None,
                    'swift': str(row.get('SWIFT', '')).strip() or None,
                    'address': str(row.get('Адрес', '')).strip() or None,
                    'address_postal': str(row.get('Индекс', row.get('Почтовый индекс', ''))).strip() or None,
                    'phone': str(row.get('Телефон', '')).strip() or None,
                    'okpo': str(row.get('ОКПО', '')).strip() or None,
                }
                
                if bank_data['name']:
                    banks_data.append(bank_data)
            
            return banks_data
            
        except ImportError:
            logger.error("Библиотека pandas или openpyxl не установлена")
            return []
        except Exception as e:
            logger.error(f"Ошибка парсинга Excel файла: {e}")
            return []
    
    async def _update_database(
        self,
        banks_data: List[Dict[str, Any]],
        db: Session
    ) -> None:
        """
        Обновляет БД данными из справочника
        
        Args:
            banks_data: Список словарей с данными банков
            db: Сессия БД
        """
        try:
            updated_count = 0
            created_count = 0
            
            for bank_data in banks_data:
                # Ищем существующую запись
                existing = await asyncio.to_thread(
                    db.execute,
                    select(BIKDirectory).where(BIKDirectory.bik == bank_data['bik'])
                )
                bank = existing.scalar_one_or_none()
                
                if bank:
                    # Обновляем существующую запись
                    for key, value in bank_data.items():
                        if hasattr(bank, key):
                            setattr(bank, key, value)
                    updated_count += 1
                else:
                    # Создаем новую запись
                    new_bank = BIKDirectory(**bank_data)
                    db.add(new_bank)
                    created_count += 1
            
            # Сохраняем изменения
            await asyncio.to_thread(db.commit)
            
            logger.info(f"Обновлено записей: {updated_count}, создано: {created_count}")
            
        except Exception as e:
            await asyncio.to_thread(db.rollback)
            logger.error(f"Ошибка обновления БД справочника БИК: {e}")
            raise


# Singleton instance
bik_service = BIKService()

