"""
Гибридный загрузчик кодексов - комбинированный подход
1. Пытается скачать PDF через API (быстро, если есть правильный eo_number)
2. Если PDF маленький - использует HTML парсинг для полного текста (надежно)
3. Сохраняет лучший вариант
"""

import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import re

# Импорт модуля очистки текста
try:
    from ..core.text_cleaner import clean_legal_text, LegalTextCleaner
    TEXT_CLEANER_AVAILABLE = True
except ImportError:
    TEXT_CLEANER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Модуль очистки текста недоступен. Очистка будет базовой.")

# Опциональный импорт selenium (может отсутствовать)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Selenium не установлен. HTML парсинг будет недоступен.")

logger = logging.getLogger(__name__)

class HybridCodesDownloader:
    """
    Гибридный загрузчик кодексов:
    - Пытается PDF через API (быстро)
    - Если маленький - парсит HTML (надежно)
    - Сохраняет лучший результат
    """
    
    def __init__(self, output_dir: str = "data/codes_downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Минимальный размер для полного кодекса (в байтах)
        # Если PDF меньше - считаем заглушкой
        self.MIN_FULL_CODEX_SIZE = 500 * 1024  # 500 КБ
        self.MIN_PAGES_COUNT = 50  # Минимум страниц для полного кодекса
        
        # Список кодексов с их HTML URL (для парсинга)
        self.codexes = {
            "Гражданский кодекс РФ (часть 1)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=ba747b7c430fdfb9405741d818463a26af1577a680f7a9ab6318cc6f4faa1121&ttl=1",
                "eo_number": "0001201410140002",  # Может быть неправильным
                "expected_pages": 200
            },
            "Гражданский кодекс РФ (часть 2)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=c5515b06c932bdfbd67b34f5b856bb8317deaabded3eacae2ebadfd4c6703785&ttl=1",
                "eo_number": None,
                "expected_pages": 150
            },
            "Гражданский кодекс РФ (часть 3)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=4420d99c9eb3a210be9c946b1668b59acfb944f1129f0beaf1bd82d03449122c&ttl=1",
                "eo_number": None,
                "expected_pages": 150
            },
            "Гражданский кодекс РФ (часть 4)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=3edc1b4f0e70ca1c9191422c7c01743f4316210d72f59b4a45581dd70060fb13&ttl=1",
                "eo_number": None,
                "expected_pages": 150
            },
            "Трудовой кодекс РФ": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=03bdee8f44a71247d7ba3342484326dbc3fa292d3caae9f88ada4b1ee38c20d9&ttl=1",
                "eo_number": "0001201412140001",
                "expected_pages": 400
            },
            "Налоговый кодекс РФ (часть 1)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=b113c2e08341853ef53a8dad4585b513d96f85e0f3d0d246a25ecf52e40608db&ttl=1",
                "eo_number": "0001201905010039",
                "expected_pages": 300
            },
            "Налоговый кодекс РФ (часть 2)": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=6d30a92f830312a1b62d0a002c635c3e667c52e1059a82525dd65cb8e2bbe0a6&ttl=1",
                "eo_number": None,
                "expected_pages": 300
            },
            "Уголовный кодекс РФ": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=f29a592d348b400651a6760273edea9dfcbb75f4d56777c1c5b99233244b404c&ttl=1",
                "eo_number": "0001202203030006",
                "expected_pages": 300
            },
            "Семейный кодекс РФ": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=67c8f9935a6c27bd4075a7e8c1965e7acabbdf019e8dcf764d9203a17ddfcf67&ttl=1",
                "eo_number": None,
                "expected_pages": 200
            },
            "Жилищный кодекс РФ": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=8b4a1920bd1b392ecc9684dc74ddebb02da5af465df06bc4a7ff8c2baf3915ce&ttl=1",
                "eo_number": None,
                "expected_pages": 200
            },
            "Кодекс об административных правонарушениях РФ": {
                "html_url": "http://actual.pravo.gov.ru/content/content.html#hash=6639c6c6580e8aa0bdf84170d25823669dfb6a4144b03da245ef4889f24765c0&ttl=1",
                "eo_number": "0001201412140006",
                "expected_pages": 400
            },
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.driver: Optional[webdriver.Chrome] = None
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=aiohttp.ClientTimeout(total=300)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def init_selenium(self):
        """Инициализирует Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium недоступен, HTML парсинг отключен")
            return
            
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(60)
            logger.info("✅ Selenium WebDriver инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Selenium: {e}")
            self.driver = None
    
    def _basic_text_cleanup(self, text: str) -> str:
        """Базовая очистка текста (fallback если модуль очистки недоступен)"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                # Убираем ТОЛЬКО явно служебную информацию
                skip_keywords = [
                    'cookie', 'javascript', 'css', 'script', 'style',
                    'навигация', 'меню', 'footer', 'header', 'sidebar',
                    'справка', 'помощь', 'закрыть', 'открыть',
                    'печать текста полностью', 'печать выделенного фрагмента',
                    'a-', 'a+', 'фон документа', 'белый', 'серый',
                    'размер шрифта', 'стандарт',
                    'свидетельство о регистрации'
                ]
                
                line_lower = line.lower()
                should_skip = False
                
                for skip in skip_keywords:
                    if len(line) < 20 and skip in line_lower:
                        should_skip = True
                        break
                    if line_lower in ['закрыть', 'открыть', 'a-', 'a+', 'cookie', 'javascript']:
                        should_skip = True
                        break
                
                if not should_skip:
                    cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        # Удаляем множественные пустые строки
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        return cleaned_text.strip()

    async def download_pdf_via_api(self, eo_number: str) -> Tuple[Optional[bytes], Dict]:
        """Пытается скачать PDF через API"""
        if not eo_number:
            return None, {}
        
        try:
            pdf_url = f"http://publication.pravo.gov.ru/file/pdf?eoNumber={eo_number}"
            logger.info(f"📥 Попытка скачать PDF через API: {pdf_url}")
            
            async with self.session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ API вернул статус {response.status}")
                    return None, {}
                
                content = await response.read()
                
                if not content.startswith(b'%PDF'):
                    logger.warning(f"⚠️ Получен не PDF файл")
                    return None, {}
                
                # Проверяем размер
                file_size = len(content)
                
                # Получаем метаданные
                metadata = await self.get_metadata(eo_number)
                
                return content, {
                    "size": file_size,
                    "method": "api_pdf",
                    "metadata": metadata
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка скачивания PDF через API: {e}")
            return None, {}

    async def get_metadata(self, eo_number: str) -> Dict:
        """Получает метаданные через API"""
        try:
            api_url = f"http://publication.pravo.gov.ru/api/Document?eoNumber={eo_number}"
            async with self.session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    if "message" in data:
                        return {}
                    return {
                        "pages_count": data.get("pagesCount"),
                        "pdf_file_length": data.get("pdfFileLength"),
                        "name": data.get("name"),
                    }
        except:
            pass
        return {}

    async def parse_html_codex(self, html_url: str, codex_name: str) -> Tuple[Optional[str], Dict]:
        """Парсит HTML кодекс через Selenium"""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium недоступен, HTML парсинг отключен")
            return None, {}
            
        if not self.driver:
            self.init_selenium()
        
        if not self.driver:
            logger.error("❌ Selenium не инициализирован")
            return None, {}
        
        try:
            logger.info(f"🌐 Парсинг HTML: {codex_name}")
            logger.info(f"   URL: {html_url}")
            
            self.driver.get(html_url)
            
            # Ждем загрузки страницы
            await asyncio.sleep(5)
            
            # Ждем появления контента документа
            try:
                wait = WebDriverWait(self.driver, 60)
                # Ищем контент документа - разные возможные селекторы
                content_selectors = [
                    ".view-col-contaner",
                    ".document-content",
                    "#document-content",
                    ".content",
                    "main",
                    "article"
                ]
                
                content_found = False
                for selector in content_selectors:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        content_found = True
                        logger.info(f"✅ Найден контент через селектор: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if not content_found:
                    logger.warning("⚠️ Не удалось найти контент, пробуем получить весь текст")
                
            except TimeoutException:
                logger.warning("⚠️ Таймаут ожидания контента")
            
            # УЛУЧШЕННЫЙ ПАРСИНГ: Агрессивный скроллинг с проверкой кнопок и пагинации
            logger.info("📜 Агрессивная прокрутка страницы для загрузки всего контента...")
            
            # ШАГ 1: Ищем и кликаем на все кнопки "Показать все", "Раскрыть" и т.д.
            logger.info("🔍 Ищем кнопки раскрытия контента...")
            try:
                expand_buttons = self.driver.execute_script("""
                    var buttons = [];
                    var allElements = document.querySelectorAll('button, a, span, div, [onclick], [class*="expand"], [class*="show"], [class*="more"]');
                    allElements.forEach(el => {
                        var text = (el.innerText || el.textContent || '').toLowerCase();
                        var className = (el.className || '').toLowerCase();
                        var id = (el.id || '').toLowerCase();
                        
                        // Ищем кнопки с текстом "показать", "раскрыть", "далее", "еще" и т.д.
                        if (text.includes('показать') || text.includes('раскрыть') || text.includes('развернуть') || 
                            text.includes('далее') || text.includes('еще') || text.includes('more') || 
                            text.includes('expand') || text.includes('show') || text.includes('дальше') ||
                            className.includes('expand') || className.includes('show') || className.includes('more') ||
                            id.includes('expand') || id.includes('show') || id.includes('more')) {
                            buttons.push(el);
                        }
                    });
                    return buttons.length;
                """)
                logger.info(f"   Найдено потенциальных кнопок раскрытия: {expand_buttons}")
                
                # Кликаем на все найденные кнопки
                for i in range(expand_buttons):
                    try:
                        self.driver.execute_script(f"""
                            var buttons = [];
                            var allElements = document.querySelectorAll('button, a, span, div, [onclick], [class*="expand"], [class*="show"], [class*="more"]');
                            allElements.forEach(el => {{
                                var text = (el.innerText || el.textContent || '').toLowerCase();
                                var className = (el.className || '').toLowerCase();
                                var id = (el.id || '').toLowerCase();
                                if (text.includes('показать') || text.includes('раскрыть') || text.includes('развернуть') || 
                                    text.includes('далее') || text.includes('еще') || text.includes('more') || 
                                    text.includes('expand') || text.includes('show') || text.includes('дальше') ||
                                    className.includes('expand') || className.includes('show') || className.includes('more') ||
                                    id.includes('expand') || id.includes('show') || id.includes('more')) {{
                                    buttons.push(el);
                                }}
                            }});
                            if (buttons[{i}]) {{
                                buttons[{i}].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                buttons[{i}].click();
                            }}
                        """)
                        await asyncio.sleep(2)  # Ждем загрузки после каждого клика
                    except:
                        pass
                await asyncio.sleep(3)  # Дополнительное ожидание после всех кликов
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при поиске кнопок раскрытия: {e}")
            
            # ШАГ 2: Улучшенный скроллинг - более медленный и тщательный
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 200  # Увеличиваем максимум прокруток
            no_change_count = 0
            scroll_step = 500  # Уменьшаем шаг прокрутки для более тщательной загрузки
            
            logger.info(f"   Начальная высота страницы: {last_height}px")
            
            while scroll_attempts < max_scrolls:
                # Прокручиваем вниз маленькими шагами
                current_scroll = self.driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop")
                target_scroll = current_scroll + scroll_step
                self.driver.execute_script(f"window.scrollTo({{top: {target_scroll}, behavior: 'smooth'}});")
                
                # УВЕЛИЧЕННОЕ время ожидания для загрузки контента
                await asyncio.sleep(2)  # Увеличено с 1 до 2 секунд
                
                # Периодически проверяем наличие новых элементов
                if scroll_attempts % 10 == 0:
                    # Пробуем кликнуть на элементы, которые могут появиться при прокрутке
                    try:
                        self.driver.execute_script("""
                            var lazyElements = document.querySelectorAll('[data-lazy], [loading="lazy"], .lazy-load');
                            lazyElements.forEach(el => {
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                            });
                        """)
                        await asyncio.sleep(1)
                    except:
                        pass
                
                # Проверяем, изменилась ли высота страницы
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 5:  # Увеличено с 3 до 5
                        # Пробуем прокрутить до самого конца несколько раз
                        for _ in range(3):
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            await asyncio.sleep(3)  # Увеличено ожидание
                            new_height = self.driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                break
                            last_height = new_height
                            no_change_count = 0
                        
                        if new_height == last_height:
                            logger.info(f"   Контент больше не загружается после {scroll_attempts} прокруток")
                            break
                        no_change_count = 0
                else:
                    no_change_count = 0
                
                last_height = new_height
                scroll_attempts += 1
                if scroll_attempts % 30 == 0:
                    logger.info(f"   Прокрутка {scroll_attempts}/{max_scrolls}, высота: {new_height}px, позиция: {current_scroll}px")
            
            # ШАГ 3: Проверяем наличие пагинации и переходим на следующие страницы
            logger.info("🔍 Проверяем наличие пагинации...")
            try:
                pagination_found = self.driver.execute_script("""
                    var pagination = document.querySelector('.pagination, .pager, [class*="page"], [class*="pagination"]');
                    var nextButtons = document.querySelectorAll('a[href*="page"], button[class*="next"], a[class*="next"]');
                    return {
                        hasPagination: !!pagination,
                        nextButtons: nextButtons.length
                    };
                """)
                
                if pagination_found.get('hasPagination') or pagination_found.get('nextButtons', 0) > 0:
                    logger.info(f"   Найдена пагинация, кнопок 'далее': {pagination_found.get('nextButtons', 0)}")
                    # Здесь можно добавить логику перехода по страницам, если нужно
            except:
                pass
            
            # ШАГ 4: Финальная прокрутка и ожидание
            logger.info("📜 Финальная прокрутка и ожидание загрузки...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(2)
            
            # Прокручиваем вниз и вверх несколько раз для полной загрузки
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(3)
                self.driver.execute_script("window.scrollTo(0, 0);")
                await asyncio.sleep(2)
            
            # УВЕЛИЧЕННОЕ время ожидания для финальной загрузки JavaScript
            await asyncio.sleep(8)  # Увеличено с 5 до 8 секунд
            
            # Пробуем разные методы извлечения текста
            text_content = None
            
            # МЕТОД 1: Улучшенное извлечение через JavaScript с множественными попытками
            text_content = None
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"🔍 Попытка {attempt + 1}/{max_attempts} извлечения текста...")
                    
                    # Улучшенный JavaScript для извлечения текста - АГРЕССИВНЫЙ ПОДХОД
                    extracted_text = self.driver.execute_script("""
                        // Убираем служебные элементы
                        var elements = document.querySelectorAll('script, style, nav, header, footer, .menu, .navigation, .sidebar, .cookie, .banner, .toolbar, .controls');
                        elements.forEach(el => el.remove());
                        
                        // Раскрываем ВСЕ скрытые элементы - БОЛЕЕ АГРЕССИВНО
                        var hiddenElements = document.querySelectorAll('[style*="display: none"], [style*="display:none"], [style*="visibility: hidden"], .hidden, [class*="collapse"], [class*="fold"], [aria-hidden="true"], [class*="hidden"], [class*="invisible"]');
                        hiddenElements.forEach(el => {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                            el.classList.remove('hidden', 'collapse', 'fold', 'invisible');
                            el.setAttribute('aria-hidden', 'false');
                            // Раскрываем все дочерние элементы
                            var children = el.querySelectorAll('*');
                            children.forEach(child => {
                                child.style.display = '';
                                child.style.visibility = '';
                                child.style.opacity = '';
                            });
                        });
                        
                        // Раскрываем все элементы с классом, содержащим "expand", "show", "open"
                        var expandButtons = document.querySelectorAll('[class*="expand"], [class*="show"], [class*="open"], [class*="unfold"], [onclick*="expand"], [onclick*="show"]');
                        expandButtons.forEach(btn => {
                            try {
                                if (btn.offsetParent !== null || btn.style.display !== 'none') {
                                    btn.click();
                                }
                            } catch(e) {}
                        });
                        
                        // Получаем основной контент
                        var content = document.querySelector('.view-col-contaner') || 
                                     document.querySelector('.view-col-container') ||
                                     document.querySelector('.document-content') ||
                                     document.querySelector('.content') ||
                                     document.querySelector('[class*="content"]') ||
                                     document.querySelector('[id*="content"]') ||
                                     document.querySelector('main') ||
                                     document.querySelector('article') ||
                                     document.querySelector('#content') ||
                                     document.body;
                        
                        var fullText = '';
                        var allMethods = [];
                        
                        // МЕТОД A: Через TreeWalker - САМЫЙ ТОЧНЫЙ (используем первым)
                        if (content) {
                            var allTextNodes = [];
                            var walker = document.createTreeWalker(
                                content,
                                NodeFilter.SHOW_TEXT,
                                {
                                    acceptNode: function(node) {
                                        var text = node.textContent.trim();
                                        if (text.length < 1) return NodeFilter.FILTER_REJECT;
                                        
                                        // Проверяем родителя
                                        var parent = node.parentElement;
                                        if (!parent) return NodeFilter.FILTER_REJECT;
                                        
                                        // Пропускаем служебные элементы
                                        var tagName = parent.tagName;
                                        if (tagName === 'SCRIPT' || tagName === 'STYLE' || tagName === 'NOSCRIPT') {
                                            return NodeFilter.FILTER_REJECT;
                                        }
                                        
                                        // Пропускаем элементы с служебными классами
                                        var classList = parent.classList;
                                        if (classList.contains('menu') || classList.contains('navigation') || 
                                            classList.contains('sidebar') || classList.contains('cookie') ||
                                            classList.contains('banner') || classList.contains('toolbar')) {
                                            return NodeFilter.FILTER_REJECT;
                                        }
                                        
                                        // Пропускаем очень короткие тексты в служебных элементах
                                        if (text.length < 2 && (tagName === 'SPAN' || tagName === 'DIV')) {
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
                                    // Добавляем перенос строки при смене родителя (для структуры)
                                    var currentParent = node.parentElement;
                                    if (lastParent && lastParent !== currentParent) {
                                        // Проверяем, нужно ли добавить перенос
                                        var parentTag = currentParent.tagName;
                                        if (parentTag === 'P' || parentTag === 'DIV' || parentTag === 'H1' || 
                                            parentTag === 'H2' || parentTag === 'H3' || parentTag === 'LI' ||
                                            parentTag === 'ARTICLE' || parentTag === 'SECTION') {
                                            allTextNodes.push('\\n');
                                        }
                                    }
                                    allTextNodes.push(text);
                                    lastParent = currentParent;
                                }
                            }
                            var treeWalkerText = allTextNodes.join(' ');
                            allMethods.push({method: 'TreeWalker', text: treeWalkerText, length: treeWalkerText.length});
                        }
                        
                        // МЕТОД B: Через innerHTML с сохранением структуры
                        if (content) {
                            var tempDiv = document.createElement('div');
                            tempDiv.innerHTML = content.innerHTML;
                            
                            // Удаляем служебные элементы из копии
                            var serviceElements = tempDiv.querySelectorAll('script, style, nav, header, footer, .menu, .navigation');
                            serviceElements.forEach(el => el.remove());
                            
                            // Извлекаем текст с сохранением структуры
                            var htmlText = '';
                            var paragraphs = tempDiv.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6, li, article, section, span');
                            if (paragraphs.length > 0) {
                                paragraphs.forEach(p => {
                                    var pText = (p.innerText || p.textContent || '').trim();
                                    if (pText && pText.length > 0) {
                                        htmlText += pText + '\\n';
                                    }
                                });
                            } else {
                                htmlText = tempDiv.innerText || tempDiv.textContent || '';
                            }
                            
                            if (htmlText.length > 1000) {
                                allMethods.push({method: 'innerHTML', text: htmlText, length: htmlText.length});
                            }
                        }
                        
                        // МЕТОД C: Прямое извлечение через textContent/innerText
                        if (content) {
                            var directText = content.innerText || content.textContent || '';
                            if (directText.length > 1000) {
                                allMethods.push({method: 'direct', text: directText, length: directText.length});
                            }
                        }
                        
                        // Выбираем самый длинный результат
                        if (allMethods.length > 0) {
                            allMethods.sort((a, b) => b.length - a.length);
                            fullText = allMethods[0].text;
                            console.log('Методы извлечения:', allMethods.map(m => m.method + ': ' + m.length).join(', '));
                        }
                        
                        return fullText;
                    """)
                    
                    # Проверяем результат - снижаем минимальный порог для первой проверки
                    if extracted_text and len(extracted_text) > 5000:  # Снижено с 10000 до 5000
                        if not text_content or len(extracted_text) > len(text_content):
                            text_content = extracted_text
                            logger.info(f"✅ Текст получен через JavaScript (попытка {attempt + 1}): {len(text_content)} символов")
                    
                    # Даем время для загрузки и повторяем попытку
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(3)
                        # Прокручиваем еще раз для загрузки контента
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        await asyncio.sleep(2)
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка получения текста через JavaScript (попытка {attempt + 1}): {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
            
            # Финальная проверка и обновление текста
            if text_content and len(text_content) > 5000:  # Снижено с 10000 до 5000
                logger.info(f"✅ Финальный текст: {len(text_content)} символов")
            else:
                logger.warning(f"⚠️ Недостаточно текста после всех попыток: {len(text_content) if text_content else 0} символов")
            
            # Метод 2: Если не получилось - пробуем через BeautifulSoup (если доступен)
            if not text_content or len(text_content) < 5000:  # Снижено с 10000 до 5000
                try:
                    from bs4 import BeautifulSoup
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Удаляем служебные элементы
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    
                    # Ищем основной контент
                    content = soup.find(class_='view-col-contaner') or \
                             soup.find(class_='document-content') or \
                             soup.find('main') or \
                             soup.find('article') or \
                             soup.find('body')
                    
                    if content:
                        text_content = content.get_text(separator='\n', strip=True)
                        logger.info(f"✅ Текст получен через BeautifulSoup: {len(text_content)} символов")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка BeautifulSoup: {e}")
            
            if not text_content or len(text_content) < 5000:  # Снижено с 10000 до 5000
                logger.error(f"❌ Не удалось извлечь достаточный текст: {len(text_content) if text_content else 0} символов")
                return None, {}
            
            # Очищаем текст с помощью модуля очистки
            original_length = len(text_content)
            
            if TEXT_CLEANER_AVAILABLE:
                logger.info("🧹 Используем модуль очистки текста для удаления служебной информации...")
                try:
                    cleaned_text = clean_legal_text(text_content, aggressive=True)
                    logger.info(f"✅ Текст очищен: {original_length} → {len(cleaned_text)} символов (удалено {original_length - len(cleaned_text)} символов)")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при очистке текста модулем: {e}, используем базовую очистку")
                    cleaned_text = self._basic_text_cleanup(text_content)
            else:
                logger.info("🧹 Используем базовую очистку текста...")
                cleaned_text = self._basic_text_cleanup(text_content)
            
            # Проверяем минимальную длину
            min_length = 5000  # Уменьшено с 10000 до 5000
            
            if len(cleaned_text) < min_length:
                logger.warning(f"⚠️ После очистки мало текста: {len(cleaned_text)} символов (было {original_length})")
                # Если очистка удалила слишком много, используем оригинальный текст с базовой очисткой
                if original_length > min_length * 2:
                    logger.info(f"   Используем оригинальный текст с базовой очисткой")
                    basic_cleaned = self._basic_text_cleanup(text_content)
                    if len(basic_cleaned) > min_length:
                        cleaned_text = basic_cleaned
                    else:
                        logger.error(f"❌ Даже базовая очистка дала мало текста: {len(basic_cleaned)} символов")
                        return None, {}
                else:
                    logger.error(f"❌ Недостаточно текста: {len(cleaned_text)} символов")
                    return None, {}
            
            return cleaned_text, {
                "size": len(cleaned_text.encode('utf-8')),
                "method": "html_parsing",
                "original_length": len(text_content),
                "cleaned_length": len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга HTML: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, {}

    async def download_codex(self, name: str, codex_info: Dict) -> Dict:
        """Загружает кодекс комбинированным методом"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 Обработка: {name}")
        logger.info(f"{'='*60}")
        
        html_url = codex_info["html_url"]
        eo_number = codex_info.get("eo_number")
        expected_pages = codex_info.get("expected_pages", 100)
        
        result = {
            "name": name,
            "success": False,
            "method_used": None,
            "file_size": 0,
            "pages_count": None,
            "errors": []
        }
        
        # ШАГ 1: Пытаемся скачать PDF через API (если есть eo_number)
        pdf_content = None
        pdf_info = {}
        
        if eo_number:
            logger.info(f"📥 ШАГ 1: Попытка скачать PDF через API...")
            pdf_content, pdf_info = await self.download_pdf_via_api(eo_number)
            
            if pdf_content:
                pdf_size = len(pdf_content)
                pdf_pages = pdf_info.get("metadata", {}).get("pages_count")
                
                logger.info(f"   📄 PDF скачан: {pdf_size / 1024 / 1024:.2f} МБ, {pdf_pages or '?'} страниц")
                
                # Проверяем, полный ли это кодекс
                is_full = (pdf_size >= self.MIN_FULL_CODEX_SIZE and 
                          (pdf_pages is None or pdf_pages >= self.MIN_PAGES_COUNT))
                
                if is_full:
                    logger.info(f"   ✅ PDF выглядит полным!")
                    # Сохраняем PDF
                    safe_name = re.sub(r'[^\w\s-]', '', name)
                    safe_name = re.sub(r'[-\s]+', '_', safe_name)
                    filename = f"{eo_number}_{safe_name}.pdf"
                    filepath = self.output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(pdf_content)
                    
                    result.update({
                        "success": True,
                        "method_used": "api_pdf",
                        "file_size": pdf_size,
                        "pages_count": pdf_pages,
                        "file_path": str(filepath)
                    })
                    
                    logger.info(f"✅ Успешно сохранен через API PDF: {filename}")
                    return result
                else:
                    logger.warning(f"   ⚠️ PDF слишком маленький (заглушка), пробуем HTML парсинг...")
            else:
                logger.warning(f"   ⚠️ Не удалось скачать PDF через API, пробуем HTML парсинг...")
        
        # ШАГ 2: Парсим HTML (надежный метод)
        logger.info(f"🌐 ШАГ 2: Парсинг HTML...")
        html_text, html_info = await self.parse_html_codex(html_url, name)
        
        if html_text:
            html_size = len(html_text.encode('utf-8'))
            logger.info(f"   📄 HTML распарсен: {html_size / 1024 / 1024:.2f} МБ текста")
            
            # Сохраняем как TXT
            safe_name = re.sub(r'[^\w\s-]', '', name)
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            filename = f"{safe_name}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_text)
            
            result.update({
                "success": True,
                "method_used": "html_parsing",
                "file_size": html_size,
                "file_path": str(filepath),
                "text_length": len(html_text)
            })
            
            logger.info(f"✅ Успешно сохранен через HTML парсинг: {filename}")
            return result
        
        # Если оба метода не сработали
        result["errors"].append("Не удалось загрузить ни через API, ни через HTML парсинг")
        logger.error(f"❌ Не удалось загрузить {name}")
        return result

    async def download_all_codexes(self) -> Dict:
        """Загружает все кодексы"""
        logger.info("🚀 Начало гибридной загрузки кодексов")
        logger.info(f"📁 Выходная директория: {self.output_dir}")
        logger.info(f"📋 Всего кодексов: {len(self.codexes)}")
        
        results = []
        success_count = 0
        total_size = 0
        
        async with self:
            for i, (name, codex_info) in enumerate(self.codexes.items(), 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"📚 Кодекс {i}/{len(self.codexes)}: {name}")
                logger.info(f"{'='*80}")
                
                result = await self.download_codex(name, codex_info)
                results.append(result)
                
                if result["success"]:
                    success_count += 1
                    total_size += result.get("file_size", 0)
                    method = result.get("method_used", "unknown")
                    size_mb = result.get("file_size", 0) / 1024 / 1024
                    logger.info(f"✅ Успешно ({method}): {size_mb:.2f} МБ")
                else:
                    logger.error(f"❌ Ошибка: {result.get('errors', ['Unknown'])[0]}")
                
                # Пауза между запросами
                if i < len(self.codexes):
                    await asyncio.sleep(5)
        
        summary = {
            "total_codexes": len(self.codexes),
            "successful": success_count,
            "failed": len(self.codexes) - success_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Сохраняем отчет
        report_file = self.output_dir / f"hybrid_download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 ИТОГО:")
        logger.info(f"   ✅ Успешно: {success_count}/{len(self.codexes)}")
        logger.info(f"   ❌ Ошибок: {len(self.codexes) - success_count}")
        logger.info(f"   📦 Общий размер: {total_size / 1024 / 1024:.2f} МБ")
        logger.info(f"   📄 Отчет: {report_file}")
        logger.info(f"{'='*80}")
        
        return summary

    def get_status(self) -> Dict:
        """Возвращает статус скачанных файлов"""
        pdf_files = list(self.output_dir.glob("*.pdf"))
        txt_files = list(self.output_dir.glob("*.txt"))
        json_files = list(self.output_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in pdf_files + txt_files)
        
        return {
            "total_pdf_files": len(pdf_files),
            "total_txt_files": len(txt_files),
            "total_metadata_files": len(json_files),
            "total_files": len(pdf_files) + len(txt_files),
            "files": [f.name for f in pdf_files + txt_files],
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "output_dir": str(self.output_dir)
        }

