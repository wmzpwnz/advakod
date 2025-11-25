"""
Унифицированный сервис для получения данных организаций и банков
Объединяет бесплатные источники (ФНС, ЦБ РФ) с опциональным fallback на DaData
"""
import logging
import os
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..services.egrul_service import egrul_service
from ..services.bik_service import bik_service
from ..services.bik_lookup_service import bik_lookup_service
from ..services.rusprofile_service import rusprofile_service
from ..core.config import settings
from ..models.bik_directory import BIKDirectory

logger = logging.getLogger(__name__)


class OrganizationService:
    """Унифицированный сервис для работы с данными организаций и банков"""
    
    def __init__(self):
        self.dadata_api_key = os.getenv("DADATA_API_KEY", None)
        self.dadata_secret_key = os.getenv("DADATA_SECRET_KEY", None)
        self.use_dadata_fallback = bool(self.dadata_api_key and self.dadata_secret_key)
        
        if self.use_dadata_fallback:
            logger.info("DaData API доступен, будет использоваться как fallback")
        else:
            logger.info("DaData API не настроен, используется только бесплатный вариант")
    
    async def get_organization_by_inn(
        self,
        inn: str,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Получает данные организации по ИНН
        
        Приоритет:
        1. Парсинг сайта ФНС (бесплатно)
        2. DaData API (если настроен и парсинг не удался)
        
        Args:
            inn: ИНН организации (10 или 12 цифр)
            db: Сессия БД (не используется, но оставлена для совместимости)
            
        Returns:
            Словарь с данными организации или None
        """
        # Валидация ИНН
        if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
            logger.warning(f"Некорректный ИНН: {inn}")
            return None
        
        merged_data: Dict[str, Any] = {}
        
        # Основной источник — ФНС
        try:
            fns_data = await egrul_service.get_organization_by_inn(inn)
            if fns_data:
                merged_data.update(fns_data)
        except Exception as e:
            logger.warning(f"Ошибка получения данных ФНС для ИНН {inn}: {e}")
        
        # Дополняем адресами/ОГРНИП через rusprofile
        try:
            profile_data = await rusprofile_service.get_organization_by_inn(inn)
            if profile_data:
                logger.info(f"Данные по ИНН {inn} дополнены через rusprofile")
                for key, value in profile_data.items():
                    if value and not merged_data.get(key):
                        merged_data[key] = value
            else:
                logger.warning(f"Rusprofile не вернул данные для ИНН {inn}")
        except Exception as e:
            logger.warning(f"Rusprofile недоступен для ИНН {inn}: {e}")
        
        if merged_data:
            return merged_data
        
        # Fallback на DaData (если настроен)
        if self.use_dadata_fallback:
            try:
                result = await self._get_organization_by_inn_dadata(inn)
                if result:
                    logger.info(f"Данные по ИНН {inn} получены через DaData API")
                    return result
            except Exception as e:
                logger.error(f"Ошибка получения данных через DaData для ИНН {inn}: {e}")
        
        logger.warning(f"Не удалось получить данные по ИНН {inn}")
        return None
    
    async def get_bank_by_bik(
        self,
        bik: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Получает данные банка по БИК
        
        Приоритет:
        1. Локальная БД (справочник ЦБ РФ)
        2. DaData API (если настроен и не найдено в БД)
        
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
        
        # Пробуем локальную БД
        if db is not None:
            try:
                result = await bik_service.get_bank_by_bik(bik, db)
                if result:
                    logger.info(f"Данные по БИК {bik} получены из локальной БД")
                    return result
            except Exception as e:
                logger.warning(f"Ошибка поиска в локальной БД для БИК {bik}: {e}")
        
        # Пробуем bik-info.ru
        try:
            lookup = await bik_lookup_service.get_bank_by_bik(bik)
            if lookup:
                logger.info(f"Данные по БИК {bik} получены через bik-info.ru")
                if db:
                    try:
                        await asyncio.to_thread(self._upsert_bik_entry, db, lookup)
                    except Exception as db_exc:
                        logger.warning(f"Не удалось сохранить БИК {bik} в локальную БД: {db_exc}")
                return lookup
        except Exception as e:
            logger.warning(f"bik-info.ru недоступен для БИК {bik}: {e}")
        
        # Fallback на DaData (если настроен)
        if self.use_dadata_fallback:
            try:
                result = await self._get_bank_by_bik_dadata(bik)
                if result:
                    logger.info(f"Данные по БИК {bik} получены через DaData API")
                    if db:
                        await asyncio.to_thread(self._upsert_bik_entry, db, result)
                    return result
            except Exception as e:
                logger.error(f"Ошибка получения данных через DaData для БИК {bik}: {e}")
        
        logger.warning(f"Не удалось получить данные по БИК {bik}")
        return None

    def _upsert_bik_entry(self, db: Session, data: Dict[str, Any]) -> None:
        """Сохраняет полученные реквизиты банка в локальной БД для дальнейшего использования"""
        if not data.get("bik"):
            return
        bank = db.query(BIKDirectory).filter(BIKDirectory.bik == data["bik"]).first()
        swift_value = data.get("swift")
        if swift_value and len(swift_value) > 11:
            swift_value = swift_value.split()[0]

        fields = {
            "name": data.get("name") or data.get("name_full"),
            "name_full": data.get("name_full") or data.get("name"),
            "correspondent_account": data.get("correspondent_account"),
            "swift": swift_value,
            "address": data.get("address"),
            "address_postal": data.get("address_postal"),
            "phone": data.get("phone"),
            "okpo": data.get("okpo"),
        }
        if bank:
            for key, value in fields.items():
                if value:
                    setattr(bank, key, value)
        else:
            db.add(BIKDirectory(bik=data["bik"], **fields))
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    
    async def _get_organization_by_inn_dadata(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Получает данные организации через DaData API
        
        Args:
            inn: ИНН организации
            
        Returns:
            Словарь с данными организации или None
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Token {self.dadata_api_key}",
                        "X-Secret": self.dadata_secret_key
                    },
                    json={"query": inn}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("suggestions") and len(data["suggestions"]) > 0:
                    org_data = data["suggestions"][0]["data"]
                    
                    return {
                        "name": org_data.get("name", {}).get("full_with_opf", ""),
                        "name_short": org_data.get("name", {}).get("short_with_opf", ""),
                        "inn": org_data.get("inn", ""),
                        "kpp": org_data.get("kpp", ""),
                        "ogrn": org_data.get("ogrn", ""),
                        "ogrn_date": org_data.get("ogrn_date", ""),
                        "address": org_data.get("address", {}).get("value", ""),
                        "address_postal": org_data.get("address", {}).get("data", {}).get("postal_code", ""),
                        "management": {
                            "name": org_data.get("management", {}).get("name", ""),
                            "post": org_data.get("management", {}).get("post", "")
                        },
                        "status": org_data.get("state", {}).get("status", ""),
                        "okved": org_data.get("okved", ""),
                        "okved_name": org_data.get("okved_name", "")
                    }
                    
        except ImportError:
            logger.error("Библиотека httpx не установлена для DaData")
        except Exception as e:
            logger.error(f"Ошибка запроса к DaData API: {e}")
        
        return None
    
    async def _get_bank_by_bik_dadata(self, bik: str) -> Optional[Dict[str, Any]]:
        """
        Получает данные банка через DaData API
        
        Args:
            bik: БИК банка
            
        Returns:
            Словарь с данными банка или None
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/bank",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Token {self.dadata_api_key}",
                        "X-Secret": self.dadata_secret_key
                    },
                    json={"query": bik}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("suggestions") and len(data["suggestions"]) > 0:
                    bank_data = data["suggestions"][0]["data"]
                    
                    return {
                        "name": bank_data.get("name", {}).get("payment", ""),
                        "name_full": bank_data.get("name", {}).get("full", ""),
                        "bik": bank_data.get("bik", ""),
                        "correspondent_account": bank_data.get("correspondent_account", ""),
                        "swift": bank_data.get("swift", ""),
                        "address": bank_data.get("address", {}).get("value", ""),
                        "address_postal": bank_data.get("address", {}).get("data", {}).get("postal_code", ""),
                        "phone": bank_data.get("phone", ""),
                        "okpo": bank_data.get("okpo", "")
                    }
                    
        except ImportError:
            logger.error("Библиотека httpx не установлена для DaData")
        except Exception as e:
            logger.error(f"Ошибка запроса к DaData API: {e}")
        
        return None


# Singleton instance
organization_service = OrganizationService()

