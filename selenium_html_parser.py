#!/usr/bin/env python3
"""
Улучшенный HTML парсер с Selenium для извлечения текста кодексов с pravo.gov.ru
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class SeleniumHTMLCodexParser:
    """Парсер HTML страниц кодексов с использованием Selenium"""
    
    def __init__(self, output_dir: str = "/root/advakod/unified_codexes/html_codexes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Настройка Chrome для headless режима
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        self.driver = None
        
        # Конфигурация HTML кодексов (только основные для тестирования)
        self.html_codexes = {
            "Гражданский кодекс РФ (часть 1)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=ba747b7c430fdfb9405741d818463a26af1577a680f7a9ab6318cc6f4faa1121&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "51-ФЗ", "часть первая"]
            },
            "Трудовой кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=03bdee8f44a71247d7ba3342484326dbc3fa292d3caae9f88ada4b1ee38c20d9&ttl=1",
                "priority": 1,
                "keywords": ["трудовой кодекс", "тк рф", "197-ФЗ"]
            },
            "Уголовный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=f29a592d348b400651a6760273edea9dfcbb75f4d56777c1c5b99233244b404c&ttl=1",
                "priority": 1,
                "keywords": ["уголовный кодекс", "ук рф", "63-ФЗ"]
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
    
    def init_driver(self):
        """Инициализирует WebDriver"""
        try:
            from selenium.webdriver.chrome.service import Service
            
            # Используем системный chromedriver
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info("✅ WebDriver инициализирован")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Закрывает WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("✅ WebDriver закрыт")
            except Exception as e:
                self.logger.error(f"❌ Ошибка закрытия WebDriver: {e}")
    
    def wait_for_content(self, timeout: int = 30) -> bool:
        """Ждет загрузки контента на странице"""
        try:
            # Ждем появления основного контента
            wait = WebDriverWait(self.driver, timeout)
            
            # Пробуем разные селекторы для контента
            content_selectors = [
                ".view-col-contaner",
                ".content",
                ".main-content",
                ".text-content",
                ".document-content",
                "main",
                "article"
            ]
            
            for selector in content_selectors:
                try:
                    element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element and element.text.strip():
                        self.logger.info(f"✅ Контент найден по селектору: {selector}")
                        return True
                except TimeoutException:
                    continue
            
            # Если не нашли по селекторам, ждем появления любого текста в body
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                if body and len(body.text.strip()) > 1000:
                    self.logger.info("✅ Контент найден в body")
                    return True
            except:
                pass
            
            self.logger.warning("⚠️ Контент не найден, но продолжаем")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка ожидания контента: {e}")
            return False
    
    def extract_codex_text(self, codex_name: str) -> str:
        """Извлекает текст кодекса из загруженной страницы"""
        try:
            # Ждем загрузки контента
            if not self.wait_for_content():
                self.logger.warning(f"⚠️ Контент не загрузился для {codex_name}")
            
            # Даем дополнительное время для загрузки JavaScript
            time.sleep(5)
            
            # Пробуем разные способы извлечения текста
            text_content = ""
            
            # Способ 1: Ищем основной контейнер
            content_selectors = [
                ".view-col-contaner",
                ".content",
                ".main-content",
                ".text-content",
                ".document-content",
                "main",
                "article"
            ]
            
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.text.strip():
                            text_content = element.text.strip()
                            self.logger.info(f"✅ Текст найден по селектору {selector}: {len(text_content)} символов")
                            break
                    if text_content:
                        break
                except:
                    continue
            
            # Способ 2: Если не нашли, берем весь body
            if not text_content:
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    text_content = body.text.strip()
                    self.logger.info(f"✅ Текст извлечен из body: {len(text_content)} символов")
                except:
                    pass
            
            # Способ 3: Пробуем получить текст через JavaScript
            if not text_content or len(text_content) < 1000:
                try:
                    text_content = self.driver.execute_script("return document.body.innerText;")
                    if text_content:
                        self.logger.info(f"✅ Текст получен через JavaScript: {len(text_content)} символов")
                except:
                    pass
            
            # Очищаем текст
            if text_content:
                lines = text_content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3:
                        # Убираем служебную информацию
                        if not any(skip in line.lower() for skip in [
                            'cookie', 'javascript', 'css', 'script', 'style',
                            'навигация', 'меню', 'footer', 'header', 'sidebar',
                            'справка', 'помощь', 'закрыть', 'открыть'
                        ]):
                            cleaned_lines.append(line)
                
                cleaned_text = '\n'.join(cleaned_lines)
                self.logger.info(f"✅ Очищенный текст: {len(cleaned_text)} символов")
                return cleaned_text
            
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения текста: {e}")
            return ""
    
    def save_codex_text(self, codex_name: str, text: str) -> Optional[Path]:
        """Сохраняет текст кодекса в файл"""
        try:
            # Создаем безопасное имя файла
            import re
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
            self.logger.info(f"🌐 Загружаем страницу: {codex_info['url']}")
            self.driver.get(codex_info['url'])
            
            # Ждем загрузки страницы
            time.sleep(3)
            
            # Извлекаем текст
            text = self.extract_codex_text(codex_name)
            if not text or len(text) < 1000:
                result['error'] = f'Не удалось извлечь достаточный текст ({len(text) if text else 0} символов)'
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
        
        # Инициализируем WebDriver
        if not self.init_driver():
            return []
        
        results = []
        sorted_codexes = sorted(
            self.html_codexes.items(),
            key=lambda x: x[1]['priority']
        )
        
        try:
            for i, (codex_name, codex_info) in enumerate(sorted_codexes, 1):
                self.logger.info(f"📋 Обрабатываем кодекс {i}/{len(sorted_codexes)}: {codex_name}")
                
                result = self.process_codex(codex_name, codex_info)
                results.append(result)
                
                if result['status'] == 'success':
                    self.logger.info(f"✅ {codex_name}: {result['text_length']} символов")
                else:
                    self.logger.error(f"❌ {codex_name}: {result['error']}")
                
                # Пауза между запросами
                time.sleep(3)
        
        finally:
            # Закрываем WebDriver
            self.close_driver()
        
        # Сохраняем обновленный список обработанных
        self.save_processed_html_codexes()
        
        # Статистика
        successful = sum(1 for r in results if r['status'] == 'success')
        total_text = sum(r['text_length'] for r in results if r['status'] == 'success')
        
        self.logger.info(f"📊 Обработка завершена: {successful}/{len(results)} успешно, {total_text:,} символов")
        
        return results

def main():
    """Основная функция"""
    parser = SeleniumHTMLCodexParser()
    results = parser.process_all_codexes()
    
    # Сохраняем отчет
    report_file = parser.output_dir / f"selenium_html_parsing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📊 Отчет сохранен: {report_file}")

if __name__ == "__main__":
    main()
