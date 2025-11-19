#!/usr/bin/env python3
"""
Упрощенный автоматический скачиватель и интегратор кодексов
Все в одном файле - скачивание и интеграция в RAG систему
"""

import urllib.request
import urllib.error
import urllib.parse
import re
import json
import os
import time
import signal
import sys
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Добавляем путь к backend
sys.path.append('/var/www/advacodex.com/backend')

try:
    from document_validator import DocumentValidator
    from rag_integration_service import RAGIntegrationService
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что backend модули доступны")
    sys.exit(1)

class UnifiedCodexSystem:
    """Унифицированная система скачивания и интеграции кодексов"""
    
    def __init__(self, output_dir="/var/www/advacodex.com/unified_codexes"):
        self.base_url = "http://pravo.gov.ru"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректории
        (self.output_dir / "codexes").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "status").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.download_delay = 2.0
        self.downloaded_files = []
        self.errors = []
        self.is_running = False
        self.current_task = None
        
        # Настройка логирования
        self.setup_logging()
        
        # Статус файлы
        self.status_file = self.output_dir / "status" / "system_status.json"
        self.processed_files_file = self.output_dir / "status" / "processed_files.json"
        
        # Список обработанных файлов
        self.processed_files = self.load_processed_files()
        
        # Инициализация сервисов
        self.validator = DocumentValidator(output_dir=str(self.output_dir / "validation"))
        self.rag_integrator = RAGIntegrationService(output_dir=str(self.output_dir / "rag_integration"))
        
        # Список кодексов для скачивания (PDF + HTML)
        self.codexes_to_download = {
            "Гражданский кодекс РФ": {
                "priority": 1,
                "urls": [
                    "http://pravo.gov.ru/OpubVsootvetstvii/0001201410140002.pdf",
                    "http://pravo.gov.ru/OpubVsootvetstvii/289-11.pdf"
                ],
                "keywords": ["гражданский кодекс", "гк рф", "51-ФЗ"],
                "type": "pdf"
            },
            "Налоговый кодекс РФ": {
                "priority": 1,
                "urls": [
                    "http://pravo.gov.ru/OpubVsootvetstvii/0001201905010039.pdf"
                ],
                "keywords": ["налоговый кодекс", "нк рф", "146-ФЗ"],
                "type": "pdf"
            },
            "Трудовой кодекс РФ": {
                "priority": 1,
                "urls": [
                    "http://pravo.gov.ru/OpubVsootvetstvii/0001202203030006.pdf"
                ],
                "keywords": ["трудовой кодекс", "тк рф", "197-ФЗ"],
                "type": "pdf"
            },
            "Уголовный кодекс РФ": {
                "priority": 1,
                "urls": [
                    "http://pravo.gov.ru/OpubVsootvetstvii/198.pdf"
                ],
                "keywords": ["уголовный кодекс", "ук рф", "63-ФЗ"],
                "type": "pdf"
            }
        }
        
        # HTML кодексы для парсинга
        self.html_codexes = {
            "Гражданский кодекс РФ (часть 1)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=ba747b7c430fdfb9405741d818463a26af1577a680f7a9ab6318cc6f4faa1121&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "51-ФЗ", "часть первая"],
                "type": "html"
            },
            "Гражданский кодекс РФ (часть 2)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=c5515b06c932bdfbd67b34f5b856bb8317deaabded3eacae2ebadfd4c6703785&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "14-ФЗ", "часть вторая"],
                "type": "html"
            },
            "Гражданский кодекс РФ (часть 3)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=4420d99c9eb3a210be9c946b1668b59acfb944f1129f0beaf1bd82d03449122c&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "146-ФЗ", "часть третья"],
                "type": "html"
            },
            "Гражданский кодекс РФ (часть 4)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=3edc1b4f0e70ca1c9191422c7c01743f4316210d72f59b4a45581dd70060fb13&ttl=1",
                "priority": 1,
                "keywords": ["гражданский кодекс", "гк рф", "230-ФЗ", "часть четвертая"],
                "type": "html"
            },
            "Налоговый кодекс РФ (часть 1)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=b113c2e08341853ef53a8dad4585b513d96f85e0f3d0d246a25ecf52e40608db&ttl=1",
                "priority": 1,
                "keywords": ["налоговый кодекс", "нк рф", "146-ФЗ", "часть первая"],
                "type": "html"
            },
            "Налоговый кодекс РФ (часть 2)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=6d30a92f830312a1b62d0a002c635c3e667c52e1059a82525dd65cb8e2bbe0a6&ttl=1",
                "priority": 1,
                "keywords": ["налоговый кодекс", "нк рф", "117-ФЗ", "часть вторая"],
                "type": "html"
            },
            "Трудовой кодекс РФ (HTML)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=03bdee8f44a71247d7ba3342484326dbc3fa292d3caae9f88ada4b1ee38c20d9&ttl=1",
                "priority": 1,
                "keywords": ["трудовой кодекс", "тк рф", "197-ФЗ"],
                "type": "html"
            },
            "Уголовный кодекс РФ (HTML)": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=f29a592d348b400651a6760273edea9dfcbb75f4d56777c1c5b99233244b404c&ttl=1",
                "priority": 1,
                "keywords": ["уголовный кодекс", "ук рф", "63-ФЗ"],
                "type": "html"
            },
            "Кодекс об административных правонарушениях РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=6639c6c6580e8aa0bdf84170d25823669dfb6a4144b03da245ef4889f24765c0&ttl=1",
                "priority": 2,
                "keywords": ["кодекс об административных правонарушениях", "коап рф", "195-ФЗ"],
                "type": "html"
            },
            "Семейный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=67c8f9935a6c27bd4075a7e8c1965e7acabbdf019e8dcf764d9203a17ddfcf67&ttl=1",
                "priority": 2,
                "keywords": ["семейный кодекс", "ск рф", "223-ФЗ"],
                "type": "html"
            },
            "Жилищный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=8b4a1920bd1b392ecc9684dc74ddebb02da5af465df06bc4a7ff8c2baf3915ce&ttl=1",
                "priority": 2,
                "keywords": ["жилищный кодекс", "жк рф", "188-ФЗ"],
                "type": "html"
            },
            "Земельный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=f7e8a05ab96295ade2be3c550c15fdb66646f0b16f0f65c5aad57b59577acb74&ttl=1",
                "priority": 2,
                "keywords": ["земельный кодекс", "зк рф", "136-ФЗ"],
                "type": "html"
            },
            "Гражданский процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=34099dcc0eb7647de8e2af5a8ff35414410745ba6b4f742a81842946c1a6670e&ttl=1",
                "priority": 2,
                "keywords": ["гражданский процессуальный кодекс", "гпк рф", "138-ФЗ"],
                "type": "html"
            },
            "Арбитражный процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=2464a0020ca4de3955dedd4369ba3d1bbbc846a28422a1b7c06ff6098086e8c3&ttl=1",
                "priority": 2,
                "keywords": ["арбитражный процессуальный кодекс", "апк рф", "95-ФЗ"],
                "type": "html"
            },
            "Уголовно-процессуальный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=fe66afca01e13d9cd5c9372505774708c90daa44c9410084df9c1b64e0635a03&ttl=1",
                "priority": 2,
                "keywords": ["уголовно-процессуальный кодекс", "упк рф", "174-ФЗ"],
                "type": "html"
            },
            "Кодекс административного судопроизводства РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=301b8e7807e422d78de841e939939cb07d46851f945e2039d13fa8b38623557f&ttl=1",
                "priority": 2,
                "keywords": ["кодекс административного судопроизводства", "кас рф", "21-ФЗ"],
                "type": "html"
            },
            "Градостроительный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=fc01bd4ee09272d641c80b86f8be9f750ca1137e1402dd267b5b991e64ad45b1&ttl=1",
                "priority": 2,
                "keywords": ["градостроительный кодекс", "гск рф", "190-ФЗ"],
                "type": "html"
            },
            "Уголовно-исполнительный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=7f2d72fdcce53161ff2e24ed5f79b59257bb81285e5e7a77c33b32bc88d32848&ttl=1",
                "priority": 2,
                "keywords": ["уголовно-исполнительный кодекс", "уик рф", "1-ФЗ"],
                "type": "html"
            },
            "Водный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=22ab398631ebf15f4c8e7cfbc229e36cd2c98f61dd095934c64eb2106d370190&ttl=1",
                "priority": 2,
                "keywords": ["водный кодекс", "вк рф", "74-ФЗ"],
                "type": "html"
            },
            "Лесной кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=d7e701370b68103b6266adeef0600c62b8fdd7c8517eb57fcfdf22995ab90958&ttl=1",
                "priority": 2,
                "keywords": ["лесной кодекс", "лк рф", "200-ФЗ"],
                "type": "html"
            },
            "Воздушный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=24690944a51bce854e2e6669730e80e6290a77c2c2b574149c999989143e3a0c&ttl=1",
                "priority": 2,
                "keywords": ["воздушный кодекс", "взк рф", "60-ФЗ"],
                "type": "html"
            },
            "Бюджетный кодекс РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=1e6024ba3941a2db83058b219a73643f87ad32f9f6bb5c9fd9b4bcb5aaa3f979&ttl=1",
                "priority": 2,
                "keywords": ["бюджетный кодекс", "бк рф", "145-ФЗ"],
                "type": "html"
            },
            "Кодекс внутреннего водного транспорта РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=1e0511819057ac27ce824e6862488cd24ce5a98760c6aa2116112515fd7fd3d0&ttl=1",
                "priority": 2,
                "keywords": ["кодекс внутреннего водного транспорта", "кввт рф", "24-ФЗ"],
                "type": "html"
            },
            "Кодекс торгового мореплавания РФ": {
                "url": "http://actual.pravo.gov.ru/content/content.html#hash=779dc3826f8590b9834ef488b94ccf833f26cde0f112edc741f9becd629adf96&ttl=1",
                "priority": 2,
                "keywords": ["кодекс торгового мореплавания", "ктм рф", "81-ФЗ"],
                "type": "html"
            }
        }
        
        self.logger.info("✅ UnifiedCodexSystem инициализирован")
        self.logger.info(f"📁 Выходная директория: {self.output_dir}")
        self.logger.info(f"🎯 PDF кодексов для скачивания: {len(self.codexes_to_download)}")
        self.logger.info(f"🎯 HTML кодексов для парсинга: {len(self.html_codexes)}")
        
        # Инициализация WebDriver для HTML парсинга
        self.driver = None
        self.init_webdriver()
        
        # Настройка обработчиков сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Настройка логирования"""
        log_file = self.output_dir / "logs" / f"unified_system_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.logger.info(f"🛑 Получен сигнал {signum}, завершаем работу...")
        self.is_running = False
        self.close_webdriver()
        self.save_status()
        sys.exit(0)
    
    def load_processed_files(self) -> Dict[str, Dict[str, Any]]:
        """Загружает список обработанных файлов с метаданными"""
        if self.processed_files_file.exists():
            with open(self.processed_files_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Поддержка старого формата (список строк)
                if isinstance(data, list):
                    return {filename: {"processed_at": "2025-10-26T12:17:40"} for filename in data}
                return data
        return {}
    
    def save_processed_files(self):
        """Сохраняет список обработанных файлов"""
        with open(self.processed_files_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_files, f, ensure_ascii=False, indent=2)
    
    def save_status(self):
        """Сохраняет текущий статус"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'is_running': self.is_running,
            'current_task': self.current_task,
            'downloaded_files': len(self.downloaded_files),
            'processed_files': len(self.processed_files),
            'errors': len(self.errors),
            'total_codexes': len(self.codexes_to_download)
        }
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def init_webdriver(self):
        """Инициализирует WebDriver для HTML парсинга"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info("✅ WebDriver инициализирован для HTML парсинга")
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            self.driver = None
    
    def close_webdriver(self):
        """Закрывает WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("✅ WebDriver закрыт")
            except Exception as e:
                self.logger.error(f"❌ Ошибка закрытия WebDriver: {e}")
    
    def parse_html_codex(self, codex_name: str, codex_info: Dict) -> Dict:
        """Парсит HTML кодекс"""
        result = {
            'codex_name': codex_name,
            'status': 'failed',
            'text_length': 0,
            'file_path': None,
            'error': None
        }
        
        if not self.driver:
            result['error'] = 'WebDriver не инициализирован'
            return result
        
        try:
            self.logger.info(f"🌐 Загружаем HTML страницу: {codex_info['url']}")
            self.driver.get(codex_info['url'])
            
            # Ждем загрузки страницы
            time.sleep(3)
            
            # Ждем появления контента
            try:
                wait = WebDriverWait(self.driver, 30)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".view-col-contaner")))
            except TimeoutException:
                self.logger.warning("⚠️ Таймаут ожидания контента")
            
            # Даем дополнительное время для загрузки JavaScript
            time.sleep(5)
            
            # КРИТИЧЕСКИ ВАЖНО: Кликаем на все элементы оглавления для загрузки полного текста
            try:
                self.logger.info("🖱️ Кликаем на элементы оглавления для загрузки полного текста...")
                
                # Находим и кликаем на все ссылки/элементы оглавления
                clickable_elements = self.driver.execute_script("""
                    // Находим все кликабельные элементы в оглавлении
                    var elements = [];
                    
                    // Ищем ссылки в оглавлении
                    var tocLinks = document.querySelectorAll('a[href*="#"], a[href*="article"], a[href*="статья"], a[href*="Статья"], a[href*="chapter"], a[href*="раздел"]');
                    tocLinks.forEach(link => {
                        if (link.textContent.trim().length > 5 && 
                            (link.textContent.includes('Статья') || 
                             link.textContent.includes('статья') ||
                             link.textContent.includes('Глава') ||
                             link.textContent.includes('Раздел') ||
                             link.textContent.match(/\\d+\\./))) {
                            elements.push(link);
                        }
                    });
                    
                    // Ищем элементы с классами оглавления
                    var tocElements = document.querySelectorAll('[class*="toc"], [class*="content"], [class*="article"], [class*="chapter"], [id*="toc"], [id*="content"]');
                    tocElements.forEach(el => {
                        var links = el.querySelectorAll('a');
                        links.forEach(link => {
                            if (link.textContent.trim().length > 5) {
                                elements.push(link);
                            }
                        });
                    });
                    
                    return elements.length;
                """)
                
                self.logger.info(f"📋 Найдено {clickable_elements} элементов для клика")
                
                # Кликаем на элементы по частям, чтобы не перегрузить страницу
                if clickable_elements > 0:
                    # Кликаем через JavaScript для загрузки контента
                    self.driver.execute_script("""
                        // Кликаем на все ссылки оглавления для загрузки полного текста
                        var clicked = 0;
                        var links = document.querySelectorAll('a[href*="#"], a[href*="article"], a[href*="статья"], a[href*="Статья"]');
                        
                        links.forEach(function(link, index) {
                            try {
                                var text = link.textContent.trim();
                                if (text.length > 5 && 
                                    (text.includes('Статья') || text.includes('статья') || 
                                     text.includes('Глава') || text.includes('Раздел') ||
                                     text.match(/\\d+\\./))) {
                                    
                                    // Прокручиваем к элементу
                                    link.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    
                                    // Кликаем
                                    link.click();
                                    clicked++;
                                    
                                    // Небольшая задержка между кликами
                                    if (clicked % 10 === 0) {
                                        // Ждем загрузки после каждых 10 кликов
                                    }
                                }
                            } catch(e) {
                                // Игнорируем ошибки клика
                            }
                        });
                        
                        return clicked;
                    """)
                    
                    # Ждем загрузки контента после кликов
                    time.sleep(10)
                    
                    # Скроллим страницу вниз для загрузки всего контента
                    self.driver.execute_script("""
                        var scrollHeight = document.body.scrollHeight;
                        var currentPosition = 0;
                        var scrollStep = 500;
                        
                        function scrollDown() {
                            currentPosition += scrollStep;
                            window.scrollTo(0, currentPosition);
                            
                            if (currentPosition < scrollHeight) {
                                setTimeout(scrollDown, 100);
                            }
                        }
                        
                        scrollDown();
                    """)
                    time.sleep(5)
                    
                    # Скроллим обратно вверх
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка при клике на элементы оглавления: {e}")
            
            # Раскрываем все скрытые элементы и iframe
            try:
                self.driver.execute_script("""
                    // Раскрываем все скрытые элементы
                    var hiddenElements = document.querySelectorAll('[style*="display: none"], [style*="display:none"], [style*="visibility: hidden"], .hidden, [class*="collapse"]');
                    hiddenElements.forEach(el => {
                        el.style.display = 'block';
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                    });
                    
                    // Раскрываем все элементы с классом expand/show
                    var expandButtons = document.querySelectorAll('[class*="expand"], [class*="show"], [class*="open"], [onclick*="expand"]');
                    expandButtons.forEach(btn => {
                        try { btn.click(); } catch(e) {}
                    });
                    
                    // Работаем с iframe, если есть
                    var iframes = document.querySelectorAll('iframe');
                    iframes.forEach(function(iframe) {
                        try {
                            iframe.style.display = 'block';
                            iframe.style.visibility = 'visible';
                        } catch(e) {}
                    });
                """)
                time.sleep(3)  # Ждем раскрытия контента
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка раскрытия элементов: {e}")
            
            # Извлекаем текст улучшенным методом (включая iframe и динамический контент)
            text_content = ""
            try:
                # Улучшенный метод извлечения текста через TreeWalker с поддержкой iframe
                text_content = self.driver.execute_script("""
                    // Функция для извлечения текста из элемента
                    function extractTextFromElement(element) {
                        if (!element) return '';
                        
                        var allTextNodes = [];
                        var walker = document.createTreeWalker(
                            element,
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: function(node) {
                                    var text = node.textContent.trim();
                                    if (text.length < 1) return NodeFilter.FILTER_REJECT;
                                    
                                    var parent = node.parentElement;
                                    if (!parent) return NodeFilter.FILTER_REJECT;
                                    
                                    var tagName = parent.tagName;
                                    if (tagName === 'SCRIPT' || tagName === 'STYLE' || tagName === 'NOSCRIPT') {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    
                                    // Пропускаем только явно служебные элементы
                                    var classList = parent.classList;
                                    var className = parent.className || '';
                                    var id = parent.id || '';
                                    
                                    // Более мягкая фильтрация - пропускаем только явно служебные
                                    if (classList.contains('menu') || classList.contains('navigation') || 
                                        classList.contains('sidebar') || classList.contains('cookie') ||
                                        classList.contains('banner') || classList.contains('toolbar') ||
                                        className.includes('menu') || className.includes('navigation') ||
                                        id.includes('menu') || id.includes('navigation')) {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    
                                    return NodeFilter.FILTER_ACCEPT;
                                }
                            },
                            false
                        );
                        
                        var node;
                        var lastParent = null;
                        while (node = walker.nextNode()) {
                            var text = node.textContent.trim();
                            if (text && text.length > 0) {
                                var currentParent = node.parentElement;
                                if (lastParent && lastParent !== currentParent) {
                                    var parentTag = currentParent.tagName;
                                    if (parentTag === 'P' || parentTag === 'DIV' || parentTag === 'H1' || 
                                        parentTag === 'H2' || parentTag === 'H3' || parentTag === 'H4' ||
                                        parentTag === 'H5' || parentTag === 'H6' || parentTag === 'LI' ||
                                        parentTag === 'ARTICLE' || parentTag === 'SECTION' ||
                                        parentTag === 'BLOCKQUOTE' || parentTag === 'PRE') {
                                        allTextNodes.push('\\n');
                                    }
                                }
                                allTextNodes.push(text);
                                lastParent = currentParent;
                            }
                        }
                        
                        return allTextNodes.join(' ');
                    }
                    
                    var fullText = '';
                    
                    // 1. Извлекаем текст из основного контента
                    var content = document.querySelector('.view-col-contaner') || 
                                 document.querySelector('.view-col-container') ||
                                 document.querySelector('.document-content') ||
                                 document.querySelector('.content') ||
                                 document.querySelector('[class*="content"]') ||
                                 document.querySelector('[id*="content"]') ||
                                 document.querySelector('main') ||
                                 document.querySelector('article') ||
                                 document.body;
                    
                    if (content) {
                        fullText += extractTextFromElement(content);
                    }
                    
                    // 2. Извлекаем текст из iframe (если есть)
                    var iframes = document.querySelectorAll('iframe');
                    iframes.forEach(function(iframe) {
                        try {
                            var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                            if (iframeDoc && iframeDoc.body) {
                                var iframeText = extractTextFromElement(iframeDoc.body);
                                if (iframeText && iframeText.length > 100) {
                                    fullText += '\\n\\n' + iframeText;
                                }
                            }
                        } catch(e) {
                            // Игнорируем ошибки доступа к iframe (CORS)
                        }
                    });
                    
                    // 3. Если текста мало, извлекаем из всего body
                    if (fullText.length < 5000 && document.body) {
                        var bodyText = extractTextFromElement(document.body);
                        if (bodyText.length > fullText.length) {
                            fullText = bodyText;
                        }
                    }
                    
                    return fullText;
                """)
                
                if text_content:
                    self.logger.info(f"✅ Текст получен через TreeWalker: {len(text_content)} символов")
            except Exception as e:
                self.logger.error(f"❌ Ошибка получения текста через JavaScript: {e}")
                # Fallback на простой метод
                try:
                    text_content = self.driver.execute_script("return document.body.innerText;")
                    if text_content:
                        self.logger.info(f"✅ Текст получен через innerText (fallback): {len(text_content)} символов")
                except:
                    pass
            
            # Очищаем текст
            if text_content and len(text_content) > 1000:
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
                
                if len(cleaned_text) > 1000:
                    # Сохраняем текст в файл
                    safe_name = re.sub(r'[^\w\s-]', '', codex_name)
                    safe_name = re.sub(r'[-\s]+', '_', safe_name)
                    filename = f"{safe_name}.txt"
                    file_path = self.output_dir / "html_codexes" / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    
                    result.update({
                        'status': 'success',
                        'text_length': len(cleaned_text),
                        'file_path': str(file_path)
                    })
                    
                    self.logger.info(f"✅ HTML кодекс {codex_name}: {len(cleaned_text)} символов")
                else:
                    result['error'] = f'Недостаточно текста после очистки: {len(cleaned_text)} символов'
            else:
                result['error'] = f'Не удалось извлечь достаточный текст: {len(text_content) if text_content else 0} символов'
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Ошибка парсинга HTML кодекса {codex_name}: {e}")
        
        return result
    
    def test_pdf_link(self, url: str) -> bool:
        """Проверяет доступность PDF файла"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get('content-type', '')
                return 'pdf' in content_type.lower() and response.status == 200
        except:
            return False
    
    def download_pdf(self, url: str, filename: str = None, codex_name: str = "unknown") -> Optional[str]:
        """Скачивает PDF документ"""
        try:
            if not filename:
                parsed_url = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith('.pdf'):
                    safe_name = re.sub(r'[^\w\s-]', '', codex_name)
                    safe_name = re.sub(r'[-\s]+', '_', safe_name)
                    filename = f"{safe_name}_{len(self.downloaded_files) + 1}.pdf"
            
            self.logger.info(f"📄 Скачиваем PDF: {filename} - {url}")
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
                
                filepath = self.output_dir / "codexes" / filename
                
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                self.downloaded_files.append({
                    'url': url,
                    'filepath': str(filepath),
                    'type': 'pdf',
                    'size': len(content),
                    'filename': filename,
                    'codex_name': codex_name,
                    'timestamp': datetime.now().isoformat()
                })
                
                self.logger.info(f"✅ PDF сохранен: {filepath} ({len(content)} байт)")
                return str(filepath)
                
        except Exception as e:
            error_msg = f"❌ Ошибка скачивания PDF {url}: {e}"
            self.logger.error(error_msg)
            self.errors.append({'url': url, 'error': str(e), 'timestamp': datetime.now().isoformat()})
            return None
    
    def download_codex(self, codex_name: str, codex_info: Dict[str, Any]) -> Dict[str, Any]:
        """Скачивает конкретный кодекс"""
        self.current_task = f"Скачивание {codex_name}"
        self.save_status()
        
        self.logger.info(f"🎯 Обрабатываем кодекс: {codex_name}")
        
        downloaded_count = 0
        successful_links = []
        
        # Пробуем известные ссылки
        for url in codex_info["urls"]:
            if self.test_pdf_link(url):
                self.logger.info(f"✅ Найдена рабочая ссылка: {url}")
                if self.download_pdf(url, codex_name=codex_name):
                    downloaded_count += 1
                    successful_links.append(url)
                time.sleep(self.download_delay)
            else:
                self.logger.info(f"❌ Ссылка недоступна: {url}")
        
        return {
            'codex_name': codex_name,
            'downloaded': downloaded_count,
            'successful_links': successful_links,
            'status': 'success' if downloaded_count > 0 else 'failed'
        }
    
    def get_new_files(self) -> List[Path]:
        """Получает список новых файлов для обработки (PDF + HTML)"""
        new_files = []
        
        # Ищем PDF файлы
        if (self.output_dir / "codexes").exists():
            pdf_files = list((self.output_dir / "codexes").glob("*.pdf"))
            all_files = pdf_files
        else:
            all_files = []
        
        # Ищем HTML файлы
        if (self.output_dir / "html_codexes").exists():
            html_files = list((self.output_dir / "html_codexes").glob("*.txt"))
            all_files.extend(html_files)
        
        for file_path in all_files:
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Проверяем, является ли файл новым или обновленным
            is_new_file = True
            
            if file_path.name in self.processed_files:
                processed_info = self.processed_files[file_path.name]
                processed_at = datetime.fromisoformat(processed_info.get("processed_at", "2025-10-26T12:17:40"))
                processed_size = processed_info.get("file_size", 0)
                
                # Файл считается новым, если:
                # 1. Изменился размер файла
                # 2. Файл был модифицирован после последней обработки
                if file_size == processed_size and file_mtime <= processed_at:
                    is_new_file = False
                    self.logger.debug(f"📄 Файл {file_path.name} не изменился (размер: {file_size}, модификация: {file_mtime})")
                else:
                    self.logger.info(f"🔄 Файл {file_path.name} обновлен (размер: {processed_size} -> {file_size}, модификация: {file_mtime})")
            
            if is_new_file:
                new_files.append(file_path)
                file_type = "PDF" if file_path.suffix == ".pdf" else "HTML"
                self.logger.info(f"🆕 Новый {file_type} файл: {file_path.name} (размер: {file_size}, модификация: {file_mtime})")
        
        self.logger.info(f"📄 Найдено файлов: {len(all_files)}, новых/обновленных: {len(new_files)}")
        return new_files
    
    def integrate_new_files(self) -> Dict[str, Any]:
        """Интегрирует новые файлы в RAG систему"""
        self.current_task = "Интеграция новых файлов"
        self.save_status()
        
        new_files = self.get_new_files()
        
        if not new_files:
            self.logger.info("📭 Новых файлов для интеграции не найдено")
            return {
                'timestamp': datetime.now().isoformat(),
                'new_files_count': 0,
                'processed_files': 0,
                'created_chunks': 0,
                'status': 'no_new_files'
            }
        
        self.logger.info(f"🔄 Найдено {len(new_files)} новых файлов для интеграции")
        
        # Создаем временную директорию для новых файлов
        temp_dir = self.output_dir / "temp_new_files"
        temp_dir.mkdir(exist_ok=True)
        
        # Копируем новые файлы во временную директорию
        for file_path in new_files:
            import shutil
            shutil.copy2(file_path, temp_dir / file_path.name)
        
        self.current_task = f"Валидация {len(new_files)} файлов"
        self.save_status()
        
        # Валидация
        self.logger.info("✅ ЭТАП 1: ВАЛИДАЦИЯ НОВЫХ ФАЙЛОВ")
        validation_results = self.validator.validate_directory(temp_dir)
        self.validator.save_validation_report()
        
        total_files = len(validation_results)
        valid_files = len([r for r in validation_results if r.get('is_valid', False)])
        
        self.logger.info(f"✅ Валидация завершена: {total_files} файлов, {valid_files} валидных")
        
        self.current_task = f"Интеграция {valid_files} файлов в RAG"
        self.save_status()
        
        # Интеграция в RAG
        self.logger.info("🔗 ЭТАП 2: ИНТЕГРАЦИЯ С RAG СИСТЕМОЙ")
        integration_results = self.rag_integrator.integrate_documents(temp_dir)
        integration_report = self.rag_integrator.save_integration_report()
        
        successful_integrations = integration_report["summary"]["successful_integrations"]
        total_chunks = integration_report["summary"]["total_chunks_created"]
        
        self.logger.info(f"✅ Интеграция завершена: {successful_integrations} документов, {total_chunks} чанков")
        
        # Обновляем список обработанных файлов
        for file_path in new_files:
            file_stat = file_path.stat()
            self.processed_files[file_path.name] = {
                "processed_at": datetime.now().isoformat(),
                "file_size": file_stat.st_size,
                "file_mtime": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "integration_timestamp": datetime.now().isoformat()
            }
        
        self.save_processed_files()
        
        # Очищаем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'new_files_count': len(new_files),
            'processed_files': successful_integrations,
            'created_chunks': total_chunks,
            'validation_results': {
                'total_files': total_files,
                'valid_files': valid_files
            },
            'integration_results': integration_report,
            'status': 'success'
        }
        
        # Сохраняем отчет
        report_file = self.output_dir / "reports" / f"integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📊 Отчет сохранен: {report_file}")
        
        return result
    
    def run_download_cycle(self):
        """Выполняет один цикл скачивания (PDF + HTML)"""
        try:
            self.logger.info("🔄 Запускаем цикл скачивания PDF кодексов")
            
            # Обрабатываем PDF кодексы
            sorted_pdf_codexes = sorted(
                self.codexes_to_download.items(),
                key=lambda x: x[1]['priority']
            )
            
            for i, (codex_name, codex_info) in enumerate(sorted_pdf_codexes, 1):
                if not self.is_running:
                    break
                
                self.logger.info(f"📋 Обрабатываем PDF кодекс {i}/{len(sorted_pdf_codexes)}: {codex_name}")
                
                result = self.download_codex(codex_name, codex_info)
                
                if result['status'] == 'success':
                    self.logger.info(f"✅ PDF кодекс {codex_name} успешно скачан")
                else:
                    self.logger.info(f"❌ PDF кодекс {codex_name} не найден")
                
                time.sleep(self.download_delay * 2)
            
            # Обрабатываем HTML кодексы
            self.logger.info("🔄 Запускаем цикл парсинга HTML кодексов")
            
            sorted_html_codexes = sorted(
                self.html_codexes.items(),
                key=lambda x: x[1]['priority']
            )
            
            for i, (codex_name, codex_info) in enumerate(sorted_html_codexes, 1):
                if not self.is_running:
                    break
                
                self.logger.info(f"📋 Обрабатываем HTML кодекс {i}/{len(sorted_html_codexes)}: {codex_name}")
                
                result = self.parse_html_codex(codex_name, codex_info)
                
                if result['status'] == 'success':
                    self.logger.info(f"✅ HTML кодекс {codex_name} успешно обработан")
                else:
                    self.logger.info(f"❌ HTML кодекс {codex_name}: {result['error']}")
                
                time.sleep(self.download_delay * 2)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка в цикле скачивания: {e}")
    
    def run_integration_cycle(self):
        """Выполняет один цикл интеграции"""
        try:
            self.logger.info("🔄 Запускаем цикл интеграции")
            result = self.integrate_new_files()
            
            if result['status'] == 'success':
                self.logger.info(f"✅ Цикл интеграции завершен: {result['processed_files']} файлов, {result['created_chunks']} чанков")
            else:
                self.logger.info("📭 Новых файлов для обработки не найдено")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка в цикле интеграции: {e}")
    
    def run_background_system(self):
        """Запускает систему в фоновом режиме"""
        self.logger.info("🔄 Запускаем унифицированную систему в фоновом режиме")
        
        def system_worker():
            try:
                while self.is_running:
                    # Скачивание
                    self.run_download_cycle()
                    
                    # Интеграция
                    self.run_integration_cycle()
                    
                    # Пауза между циклами (30 минут)
                    self.logger.info("⏳ Пауза 30 минут до следующего цикла")
                    for _ in range(1800):  # 30 минут = 1800 секунд
                        if not self.is_running:
                            break
                        time.sleep(1)
                        
            except Exception as e:
                self.logger.error(f"❌ Ошибка в фоновой системе: {e}")
                self.is_running = False
                self.save_status()
        
        # Запускаем в отдельном потоке
        system_thread = threading.Thread(target=system_worker, daemon=True)
        system_thread.start()
        
        return system_thread
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус"""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'status': 'not_started'}

def main():
    """Основная функция"""
    print("🚀 Унифицированная система скачивания и интеграции кодексов")
    print("=" * 60)
    
    system = UnifiedCodexSystem()
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            # Запускаем один полный цикл
            system.is_running = True
            system.save_status()
            
            system.run_download_cycle()
            system.run_integration_cycle()
            
            system.is_running = False
            system.save_status()
            
        elif command == "background":
            # Запускаем в фоновом режиме
            system.is_running = True
            system.save_status()
            
            thread = system.run_background_system()
            print("🔄 Система запущена в фоновом режиме")
            print("📊 Для проверки статуса используйте: python3 unified_codex_system.py status")
            
            # Ждем завершения
            thread.join()
            
        elif command == "status":
            # Показываем статус
            status = system.get_status()
            print(f"📊 СТАТУС СИСТЕМЫ:")
            print(f"   🟢 Работает: {'Да' if status.get('is_running', False) else 'Нет'}")
            print(f"   📄 Скачано файлов: {status.get('downloaded_files', 0)}")
            print(f"   🔗 Обработано файлов: {status.get('processed_files', 0)}")
            print(f"   ❌ Ошибок: {status.get('errors', 0)}")
            print(f"   📋 Текущая задача: {status.get('current_task', 'Нет')}")
            print(f"   ⏰ Последнее обновление: {status.get('timestamp', 'Неизвестно')}")
            
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Доступные команды: start, background, status")
    else:
        # По умолчанию запускаем один цикл
        system.is_running = True
        system.save_status()
        
        system.run_download_cycle()
        system.run_integration_cycle()
        
        system.is_running = False
        system.save_status()
    
    print(f"\n🎉 Работа завершена!")

if __name__ == "__main__":
    main()

