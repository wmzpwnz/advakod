"""
Вспомогательный сервис для получения данных по БИК c сайта bik-info.ru
"""
import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BikLookupService:
    def __init__(self):
        self.base_url = "https://bik-info.ru/bik"
        self.timeout = 10.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    
    async def get_bank_by_bik(self, bik: str) -> Optional[Dict[str, Any]]:
        if not bik or len(bik) != 9:
            return None
        
        url = f"{self.base_url}/{bik}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return self._parse_html(response.text, bik)
        except httpx.HTTPStatusError as exc:
            logger.warning(f"bik-info.ru вернул статус {exc.response.status_code} для БИК {bik}")
        except Exception as exc:
            logger.warning(f"Ошибка запроса к bik-info.ru для БИК {bik}: {exc}")
        return None
    
    def _parse_html(self, html: str, bik: str) -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='table')
        data: Dict[str, Any] = {
            "bik": bik,
        }
        
        if table:
            for row in table.find_all('tr'):
                header = row.find('th')
                value = row.find('td')
                if not header or not value:
                    continue
                key = header.get_text(strip=True).lower()
                val = value.get_text(strip=True)
                if 'корреспондентский' in key:
                    data['correspondent_account'] = val
                elif 'наименование банка' in key and not data.get('name'):
                    data['name'] = val
                elif 'наименование банка' in key and data.get('name'):
                    data['name_full'] = val
                elif 'адрес' in key and not data.get('address'):
                    data['address'] = val
                elif 'swift' in key:
                    codes = [c.strip() for c in val.replace('\n', ' ').split() if c.strip()]
                    if codes:
                        data['swift'] = codes[0]
        
        # Дополнительные данные из списка
        info_block = soup.find('div', id='info')
        if info_block:
            for li in info_block.find_all('li'):
                text = li.get_text(separator=' ', strip=True)
                if 'Корреспондентский счет' in text and not data.get('correspondent_account'):
                    data['correspondent_account'] = self._extract_value(text)
                elif 'Наименование банка' in text and not data.get('name'):
                    data['name'] = self._extract_value(text)
                elif 'Расположение банка' in text and not data.get('address'):
                    data['address'] = self._extract_value(text)
        
        if not data.get('name'):
            return None
        
        if not data.get('name_full'):
            data['name_full'] = data['name']
        
        return data
    
    @staticmethod
    def _extract_value(text: str) -> str:
        if ':' in text:
            return text.split(':', 1)[1].strip()
        return text.strip()


bik_lookup_service = BikLookupService()
