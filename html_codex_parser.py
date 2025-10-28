#!/usr/bin/env python3
"""
HTML парсер для извлечения текста кодексов с pravo.gov.ru
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

class HTMLCodexParser:
    """Парсер HTML страниц кодексов с pravo.gov.ru"""
    
    def __init__(self, output_dir: str = "/root/advakod/unified_codexes/html_codexes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Конфигурация HTML кодексов
        self.html_codexes = {
            "Гражданский кодекс РФ (часть 1)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=ba747b7c430fdfb9405741d818463a26af1577a680f7a9ab6318cc6f4faa1121&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "51-ФЗ", "часть первая"]
            },
            "Гражданский кодекс РФ (часть 2)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=c5515b06c932bdfbd67b34f5b856bb8317deaabded3eacae2ebadfd4c6703785&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "14-ФЗ", "часть вторая"]
            },
            "Гражданский кодекс РФ (часть 3)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=4420d99c9eb3a210be9c946b1668b59acfb944f1129f0beaf1bd82d03449122c&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "146-ФЗ", "часть третья"]
            },
            "Гражданский кодекс РФ (часть 4)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=3edc1b4f0e70ca1c9191422c7c01743f4316210d72f59b4a45581dd70060fb13&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "230-ФЗ", "часть четвертая"]
            },
            "Налоговый кодекс РФ (часть 1)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=b113c2e08341853ef53a8dad4585b513d96f85e0f3d0d246a25ecf52e40608db&ttl=1",
                "priority": 1,
                "keywords": ["налоговый кодекс", "нк рф", "146-ФЗ", "часть первая"]
            },
            "Налоговый кодекс РФ (часть 2)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=6d30a92f830312a1b62d0a002c635c3e667c52e1059a82525dd65cb8e2bbe0a6&ttl=1",
                "priority": 1,
                "keywords": ["налоговый кодекс", "нк рф", "117-ФЗ", "часть вторая"]
            },
            "Трудовой кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=03bdee8f44a71247d7ba3342484326dbc3fa292d3caae9f88ada4b1ee38c20d9&ttl=1",
                "priority": 1,
                "keywords": ["трудовой кодекс", "тк рф", "197-ФЗ"]
            },
            "Кодекс об административных правонарушениях РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=6639c6c6580e8aa0bdf84170d25823669dfb6a4144b03da245ef4889f24765c0&ttl=1",
                "priority": 2,
                "keywords": ["кодекс об административных правонарушениях", "коап рф", "195-ФЗ"]
            },
            "Кодекс административного судопроизводства РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=301b8e7807e422d78de841e939939cb07d46851f945e2039d13fa8b38623557f&ttl=1",
                "priority": 2,
                "keywords": ["кодекс административного судопроизводства", "кас рф", "21-ФЗ"]
            },
            "Градостроительный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=fc01bd4ee09272d641c80b86f8be9f750ca1137e1402dd267b5b991e64ad45b1&ttl=1",
                "priority": 2,
                "keywords": ["градостроительный кодекс", "гск рф", "190-ФЗ"]
            },
            "Гражданский процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=34099dcc0eb7647de8e2af5a8ff35414410745ba6b4f742a81842946c1a6670e&ttl=1",
                "priority": 2,
                "keywords": ["гражданский процессуальный кодекс", "гпк рф", "138-ФЗ"]
            },
            "Арбитражный процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=2464a0020ca4de3955dedd4369ba3d1bbbc846a28422a1b7c06ff6098086e8c3&ttl=1",
                "priority": 2,
                "keywords": ["арбитражный процессуальный кодекс", "апк рф", "95-ФЗ"]
            },
            "Уголовный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=f29a592d348b400651a6760273edea9dfcbb75f4d56777c1c5b99233244b404c&ttl=1",
                "priority": 1,
                "keywords": ["уголовный кодекс", "ук рф", "63-ФЗ"]
            },
            "Уголовно-процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=fe66afca01e13d9cd5c9372505774708c90daa44c9410084df9c1b64e0635a03&ttl=1",
                "priority": 2,
                "keywords": ["уголовно-процессуальный кодекс", "упк рф", "174-ФЗ"]
            },
            "Уголовно-исполнительный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=7f2d72fdcce53161ff2e24ed5f79b59257bb81285e5e7a77c33b32bc88d32848&ttl=1",
                "priority": 2,
                "keywords": ["уголовно-исполнительный кодекс", "уик рф", "1-ФЗ"]
            },
            "Земельный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=f7e8a05ab96295ade2be3c550c15fdb66646f0b16f0f65c5aad57b59577acb74&ttl=1",
                "priority": 2,
                "keywords": ["земельный кодекс", "зк рф", "136-ФЗ"]
            },
            "Жилищный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=8b4a1920bd1b392ecc9684dc74ddebb02da5af465df06bc4a7ff8c2baf3915ce&ttl=1",
                "priority": 2,
                "keywords": ["жилищный кодекс", "жк рф", "188-ФЗ"]
            },
            "Семейный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=67c8f9935a6c27bd4075a7e8c1965e7acabbdf019e8dcf764d9203a17ddfcf67&ttl=1",
                "priority": 2,
                "keywords": ["семейный кодекс", "ск рф", "223-ФЗ"]
            },
            "Водный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=22ab398631ebf15f4c8e7cfbc229e36cd2c98f61dd095934c64eb2106d370190&ttl=1",
                "priority": 2,
                "keywords": ["водный кодекс", "вк рф", "74-ФЗ"]
            },
            "Лесной кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=d7e701370b68103b6266adeef0600c62b8fdd7c8517eb57fcfdf22995ab90958&ttl=1",
                "priority": 2,
                "keywords": ["лесной кодекс", "лк рф", "200-ФЗ"]
            },
            "Воздушный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=24690944a51bce854e2e6669730e80e6290a77c2c2b574149c999989143e3a0c&ttl=1",
                "priority": 2,
                "keywords": ["воздушный кодекс", "взк рф", "60-ФЗ"]
            },
            "Бюджетный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=1e6024ba3941a2db83058b219a73643f87ad32f9f6bb5c9fd9b4bcb5aaa3f979&ttl=1",
                "priority": 2,
                "keywords": ["бюджетный кодекс", "бк рф", "145-ФЗ"]
            },
            "Кодекс внутреннего водного транспорта РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=1e0511819057ac27ce824e6862488cd24ce5a98760c6aa2116112515fd7fd3d0&ttl=1",
                "priority": 2,
                "keywords": ["кодекс внутреннего водного транспорта", "кввт рф", "24-ФЗ"]
            },
            "Кодекс торгового мореплавания РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=779dc3826f8590b9834ef488b94ccf833f26cde0f112edc741f9becd629adf96&ttl=1",
                "priority": 2,
                "keywords": ["кодекс торгового мореплавания", "ктм рф", "81-ФЗ"]
            }
        }
        
        # Файл для отслеживания обработанных HTML кодексов
        self.processed_html_file = self.output_dir / "processed_html_codexes.json"
        self.processed_html_codexes = self.load_processed_html_codexes()
    
    def load_processed_html_codexes(self) -> Dict[str, Dict[str, any]]:
        """Загружает список обработанных HTML кодексов"""
        if self.processed_html_file.exists():
            with open(self.processed_html_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {codex_name: {"processed_at": "2025-10-27T12:00:00"} for codex_name in data}
                return data
        return {}
    
    def save_processed_html_codexes(self):
        """Сохраняет список обработанных HTML кодексов"""
        with open(self.processed_html_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_html_codexes, f, ensure_ascii=False, indent=2)
    
    def fetch_html_content(self, url: str) -> Optional[str]:
        """Получает HTML содержимое страницы"""
        try:
            self.logger.info(f"🌐 Загружаем HTML: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки HTML: {e}")
            return None
    
    def extract_codex_text(self, html_content: str) -> str:
        """Извлекает текст кодекса из HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Ищем основной контент
            content_selectors = [
                '.content',
                '.main-content',
                '.text-content',
                '.document-content',
                'main',
                'article',
                '.article-content'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text(separator='\n', strip=True)
                    break
            
            # Если не нашли специальный контейнер, берем весь body
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(separator='\n', strip=True)
            
            # Очищаем текст
            lines = content_text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:  # Фильтруем короткие строки
                    # Убираем служебную информацию
                    if not any(skip in line.lower() for skip in [
                        'cookie', 'javascript', 'css', 'script', 'style',
                        'навигация', 'меню', 'footer', 'header', 'sidebar'
                    ]):
                        cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения текста: {e}")
            return ""
    
    def save_codex_text(self, codex_name: str, text: str) -> Optional[Path]:
        """Сохраняет текст кодекса в файл"""
        try:
            # Создаем безопасное имя файла
            safe_name = re.sub(r'[^\w\s-]', '', codex_name)
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            filename = f"{safe_name}.txt"
            
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.info(f"💾 Текст сохранен: {file_path} ({len(text)} символов)")
            return file_path
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения: {e}")
            return None
    
    def process_codex(self, codex_name: str, codex_info: Dict) -> Dict:
        """Обрабатывает один кодекс"""
        result = {
            'codex_name': codex_name,
            'status': 'failed',
            'text_length': 0,
            'file_path': None,
            'error': None
        }
        
        try:
            # Получаем HTML содержимое
            html_content = self.fetch_html_content(codex_info['url'])
            if not html_content:
                result['error'] = 'Не удалось загрузить HTML'
                return result
            
            # Извлекаем текст
            text = self.extract_codex_text(html_content)
            if not text or len(text) < 1000:  # Минимальная длина текста
                result['error'] = 'Не удалось извлечь достаточный текст'
                return result
            
            # Сохраняем текст
            file_path = self.save_codex_text(codex_name, text)
            if not file_path:
                result['error'] = 'Не удалось сохранить файл'
                return result
            
            result.update({
                'status': 'success',
                'text_length': len(text),
                'file_path': str(file_path)
            })
            
            # Обновляем список обработанных
            self.processed_html_codexes[codex_name] = {
                'processed_at': datetime.now().isoformat(),
                'text_length': len(text),
                'file_path': str(file_path),
                'url': codex_info['url']
            }
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Ошибка обработки {codex_name}: {e}")
        
        return result
    
    def process_all_codexes(self) -> List[Dict]:
        """Обрабатывает все HTML кодексы"""
        self.logger.info(f"🚀 Начинаем обработку {len(self.html_codexes)} HTML кодексов")
        
        results = []
        sorted_codexes = sorted(
            self.html_codexes.items(),
            key=lambda x: x[1]['priority']
        )
        
        for i, (codex_name, codex_info) in enumerate(sorted_codexes, 1):
            self.logger.info(f"📋 Обрабатываем кодекс {i}/{len(sorted_codexes)}: {codex_name}")
            
            result = self.process_codex(codex_name, codex_info)
            results.append(result)
            
            if result['status'] == 'success':
                self.logger.info(f"✅ {codex_name}: {result['text_length']} символов")
            else:
                self.logger.error(f"❌ {codex_name}: {result['error']}")
            
            # Небольшая пауза между запросами
            time.sleep(2)
        
        # Сохраняем обновленный список обработанных
        self.save_processed_html_codexes()
        
        # Статистика
        successful = sum(1 for r in results if r['status'] == 'success')
        total_text = sum(r['text_length'] for r in results if r['status'] == 'success')
        
        self.logger.info(f"📊 Обработка завершена: {successful}/{len(results)} успешно, {total_text:,} символов")
        
        return results

def main():
    """Основная функция"""
    parser = HTMLCodexParser()
    results = parser.process_all_codexes()
    
    # Сохраняем отчет
    report_file = parser.output_dir / f"html_parsing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📊 Отчет сохранен: {report_file}")

if __name__ == "__main__":
    main()
