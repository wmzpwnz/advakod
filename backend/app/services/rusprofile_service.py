"""
Сервис для получения дополнительных сведений об организациях и ИП с rusprofile.ru
Используется как бесплатный источник для автозаполнения реквизитов.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RusprofileService:
    def __init__(self):
        self.base_url = "https://www.rusprofile.ru"
        self.timeout = 15.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    
    async def get_organization_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        if not inn:
            return None
        
        url = f"{self.base_url}/search"
        params = {"query": inn}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return self._parse_html(response.text, inn)
        except httpx.HTTPStatusError as exc:
            logger.warning(f"Rusprofile вернул ошибку {exc.response.status_code} для ИНН {inn}")
        except Exception as exc:
            logger.warning(f"Не удалось получить данные с rusprofile.ru: {exc}")
        
        return None
    
    def _parse_html(self, html: str, inn: str) -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        
        def text_by_id(element_id: str) -> str:
            node = soup.select_one(f"#{element_id}")
            return node.get_text(strip=True) if node else ""
        
        def value_by_label(label: str) -> str:
            label_nodes = soup.find_all(class_="company-info__title")
            for node in label_nodes:
                if label.lower() in node.get_text(strip=True).lower():
                    sibling = node.find_next(class_="company-info__text")
                    if sibling:
                        return sibling.get_text(" ", strip=True)
            return ""
        
        data: Dict[str, Any] = {
            "name": text_by_id("clip_name") or text_by_id("clip_name-long") or \
                    (soup.find('h1').get_text(strip=True) if soup.find('h1') else ""),
            "inn": text_by_id("clip_inn") or inn,
            "kpp": text_by_id("clip_kpp"),
            "ogrn": text_by_id("clip_ogrn"),
            "ogrnip": text_by_id("clip_ogrnip"),
            "address": text_by_id("clip_address") or \
                        value_by_label("юридический адрес") or \
                        value_by_label("адрес"),
        }
        
        if not data["name"]:
            return None
        
        # Регион можно извлечь из адреса (первый сегмент до запятой)
        if data["address"] and "," in data["address"]:
            data["region"] = data["address"].split(",", 1)[0].strip()
        
        return data


rusprofile_service = RusprofileService()
