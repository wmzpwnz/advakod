"""
Сервис для получения данных организации по ИНН через официальный сервис egrul.nalog.ru
"""
import logging
import asyncio
from typing import Optional, Dict, Any
import httpx
from ..core.cache import cache_service

logger = logging.getLogger(__name__)


class EgrulService:
    """Сервис обращения к egrul.nalog.ru"""
    
    def __init__(self):
        self.base_url = "https://egrul.nalog.ru/"
        self.search_url = "https://egrul.nalog.ru/search-result/"
        self.timeout = 10.0
        self.max_retries = 3
        self.request_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://egrul.nalog.ru",
            "Referer": "https://egrul.nalog.ru/",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
    async def get_organization_by_inn(
        self,
        inn: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
            logger.warning(f"Некорректный ИНН: {inn}")
            return None
        
        cache_key = f"egrul:org:inn:{inn}"
        if use_cache:
            cached = await cache_service.get(cache_key)
            if cached:
                logger.debug(f"Данные по ИНН {inn} взяты из кэша")
                return cached
        
        for attempt in range(self.max_retries):
            try:
                result = await self._request_egrul(inn)
                if result:
                    if use_cache:
                        await cache_service.set(cache_key, result, ttl=86400)
                    return result
            except Exception as exc:
                logger.error(
                    f"Ошибка обращения к ФНС (попытка {attempt + 1}/{self.max_retries}): {exc}"
                )
                await asyncio.sleep(0.5)
        
        return None
    
    async def _request_egrul(self, inn: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.request_headers,
            follow_redirects=True
        ) as client:
            response = await client.post(self.base_url, data={"query": inn})
            response.raise_for_status()
            token = response.json().get("t")
            
            if not token:
                logger.warning("ФНС не вернул токен поиска")
                return None
            
            for _ in range(self.max_retries):
                result_response = await client.get(f"{self.search_url}{token}")
                if result_response.status_code == 200:
                    payload = result_response.json()
                    rows = payload.get("rows") or []
                    if rows:
                        mapped = self._map_row(rows[0], inn)
                        if mapped:
                            return mapped
                await asyncio.sleep(0.3)
            
            return None
    
    def _map_row(self, row: Dict[str, Any], inn: str) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        
        entity_type_raw = (row.get("k") or "").lower()
        entity_type = "ip" if entity_type_raw == "fl" else "ul"
        name_full = row.get("n") or row.get("c") or ""
        name_short = row.get("c") or row.get("n") or ""
        ogrn_value = row.get("o") or ""
        
        data = {
            "name": name_full or name_short,
            "name_full": name_full or name_short,
            "name_short": name_short or name_full,
            "inn": row.get("i") or inn,
            "kpp": row.get("p") or "",
            "ogrn": ogrn_value if entity_type == "ul" else "",
            "ogrnip": ogrn_value if entity_type == "ip" else "",
            "registration_date": row.get("r") or "",
            "region": row.get("rn") or "",
            "entity_type": entity_type,
        }
        
        head = row.get("g")
        if head:
            data["management"] = {
                "name": head,
                "post": ""
            }
        
        return data if data.get("name") else None


# Singleton instance
egrul_service = EgrulService()
