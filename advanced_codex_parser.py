#!/usr/bin/env python3
"""
Продвинутый парсер раздела кодексов с глубоким анализом
"""

import urllib.request
import urllib.error
import urllib.parse
import re
import json
import os
import time
from datetime import datetime
from pathlib import Path

class AdvancedCodexParser:
    """Продвинутый парсер кодексов"""
    
    def __init__(self, output_dir="/root/advakod/parsed_codexes"):
        self.base_url = "http://pravo.gov.ru"
        self.codex_url = "http://pravo.gov.ru/codex/"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректории
        (self.output_dir / "raw_html").mkdir(exist_ok=True)
        (self.output_dir / "parsed_data").mkdir(exist_ok=True)
        (self.output_dir / "codex_links").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.download_delay = 1
        self.parsed_data = []
        self.found_codexes = []
        
        print(f"✅ AdvancedCodexParser инициализирован")
        print(f"📁 Выходная директория: {self.output_dir}")
    
    def log(self, message, level="INFO"):
        """Логирование"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Сохраняем в файл
        log_file = self.output_dir / "logs" / f"parser_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def download_and_save(self, url, filename, description=""):
        """Скачивает и сохраняет файл"""
        try:
            self.log(f"📥 Скачиваем: {description} - {url}")
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
                filepath = self.output_dir / "raw_html" / filename
                
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                self.log(f"✅ Сохранено: {filepath} ({len(content)} байт)")
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            self.log(f"❌ Ошибка скачивания {url}: {e}", "ERROR")
            return None
    
    def extract_codex_links_advanced(self, html_content, base_url):
        """Продвинутое извлечение ссылок на кодексы"""
        # Список известных кодексов РФ
        known_codexes = [
            'гражданский кодекс', 'налоговый кодекс', 'трудовой кодекс',
            'уголовный кодекс', 'административный кодекс', 'семейный кодекс',
            'жилищный кодекс', 'земельный кодекс', 'водный кодекс',
            'лесной кодекс', 'воздушный кодекс', 'таможенный кодекс',
            'бюджетный кодекс', 'арбитражный процессуальный кодекс',
            'гражданский процессуальный кодекс', 'уголовно-процессуальный кодекс',
            'уголовно-исполнительный кодекс', 'кодекс об административных правонарушениях'
        ]
        
        # Паттерны для поиска ссылок
        link_patterns = [
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>',
            r'href=["\']([^"\']*)["\']',
            r'<link[^>]*href=["\']([^"\']*)["\'][^>]*>'
        ]
        
        found_links = []
        
        for pattern in link_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                if isinstance(match, tuple):
                    url, text = match
                else:
                    url = match
                    text = ""
                
                # Проверяем, содержит ли ссылка или текст ключевые слова кодексов
                url_lower = url.lower()
                text_lower = text.lower()
                
                for codex in known_codexes:
                    if (codex in url_lower or codex in text_lower or 
                        any(word in url_lower for word in codex.split())):
                        
                        # Формируем полный URL
                        if url.startswith('/'):
                            full_url = self.base_url + url
                        elif url.startswith('http'):
                            full_url = url
                        else:
                            full_url = base_url.rstrip('/') + '/' + url
                        
                        found_links.append({
                            'url': full_url,
                            'text': text.strip(),
                            'codex_type': codex,
                            'confidence': self.calculate_confidence(url, text, codex)
                        })
        
        # Удаляем дубликаты и сортируем по уверенности
        unique_links = {}
        for link in found_links:
            if link['url'] not in unique_links or link['confidence'] > unique_links[link['url']]['confidence']:
                unique_links[link['url']] = link
        
        return sorted(unique_links.values(), key=lambda x: x['confidence'], reverse=True)
    
    def calculate_confidence(self, url, text, codex_type):
        """Вычисляет уверенность в том, что ссылка ведет на кодекс"""
        confidence = 0
        
        url_lower = url.lower()
        text_lower = text.lower()
        
        # Высокая уверенность для прямых упоминаний
        if codex_type in url_lower:
            confidence += 50
        if codex_type in text_lower:
            confidence += 40
        
        # Средняя уверенность для ключевых слов
        codex_words = codex_type.split()
        for word in codex_words:
            if word in url_lower:
                confidence += 10
            if word in text_lower:
                confidence += 8
        
        # Дополнительные индикаторы
        if 'кодекс' in url_lower or 'кодекс' in text_lower:
            confidence += 20
        
        if any(word in url_lower for word in ['закон', 'прав', 'норм']):
            confidence += 5
        
        return min(confidence, 100)  # Максимум 100
    
    def analyze_codex_page(self, url, html_content):
        """Анализирует страницу кодекса"""
        analysis = {
            'url': url,
            'title': self.extract_title(html_content),
            'content_length': len(html_content),
            'has_pdf_links': bool(re.search(r'\.pdf', html_content, re.IGNORECASE)),
            'has_document_links': bool(re.search(r'документ|акт|закон', html_content, re.IGNORECASE)),
            'codex_mentions': len(re.findall(r'кодекс', html_content, re.IGNORECASE)),
            'article_mentions': len(re.findall(r'статья|ст\.', html_content, re.IGNORECASE)),
            'chapter_mentions': len(re.findall(r'глава|раздел', html_content, re.IGNORECASE))
        }
        
        return analysis
    
    def extract_title(self, html_content):
        """Извлекает заголовок страницы"""
        title_patterns = [
            r'<title[^>]*>([^<]*)</title>',
            r'<h1[^>]*>([^<]*)</h1>',
            r'<h2[^>]*>([^<]*)</h2>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Неизвестный заголовок"
    
    def find_publication_links(self, html_content):
        """Ищет ссылки на систему публикаций"""
        pub_patterns = [
            r'href=["\']([^"\']*publication\.pravo\.gov\.ru[^"\']*)["\']',
            r'href=["\']([^"\']*Document/View[^"\']*)["\']',
            r'href=["\']([^"\']*documents/[^"\']*)["\']'
        ]
        
        pub_links = []
        for pattern in pub_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    full_url = self.base_url + match
                elif match.startswith('http'):
                    full_url = match
                else:
                    full_url = self.base_url + '/' + match
                
                pub_links.append(full_url)
        
        return list(set(pub_links))  # Удаляем дубликаты
    
    def parse_codex_section_deep(self):
        """Глубокий парсинг раздела кодексов"""
        self.log("🔍 Начинаем глубокий парсинг раздела кодексов")
        
        # 1. Скачиваем главную страницу раздела кодексов
        html_content = self.download_and_save(
            self.codex_url, 
            "codex_main_page.html",
            "Главная страница раздела кодексов"
        )
        
        if not html_content:
            return False
        
        # 2. Анализируем страницу
        analysis = self.analyze_codex_page(self.codex_url, html_content)
        self.log(f"📊 Анализ главной страницы: {analysis}")
        
        # 3. Ищем ссылки на кодексы
        codex_links = self.extract_codex_links_advanced(html_content, self.codex_url)
        self.log(f"🔗 Найдено ссылок на кодексы: {len(codex_links)}")
        
        # 4. Показываем найденные ссылки
        for i, link in enumerate(codex_links[:10], 1):  # Показываем первые 10
            self.log(f"   {i}. {link['codex_type']} (уверенность: {link['confidence']}%) - {link['url']}")
        
        # 5. Ищем ссылки на систему публикаций
        pub_links = self.find_publication_links(html_content)
        self.log(f"📚 Найдено ссылок на публикации: {len(pub_links)}")
        
        # 6. Скачиваем и анализируем найденные страницы кодексов
        for i, link in enumerate(codex_links[:5], 1):  # Ограничиваем первыми 5
            self.log(f"📥 Анализируем кодекс {i}/{min(5, len(codex_links))}: {link['codex_type']}")
            
            filename = f"codex_{i}_{link['confidence']}.html"
            page_content = self.download_and_save(
                link['url'],
                filename,
                f"Страница кодекса: {link['codex_type']}"
            )
            
            if page_content:
                page_analysis = self.analyze_codex_page(link['url'], page_content)
                page_analysis['codex_type'] = link['codex_type']
                page_analysis['confidence'] = link['confidence']
                
                self.parsed_data.append(page_analysis)
                self.found_codexes.append(link)
            
            time.sleep(self.download_delay)
        
        # 7. Скачиваем страницы из системы публикаций
        for i, pub_url in enumerate(pub_links[:3], 1):  # Ограничиваем первыми 3
            self.log(f"📚 Анализируем публикацию {i}/{min(3, len(pub_links))}: {pub_url}")
            
            filename = f"publication_{i}.html"
            page_content = self.download_and_save(
                pub_url,
                filename,
                f"Публикация {i}"
            )
            
            if page_content:
                page_analysis = self.analyze_codex_page(pub_url, page_content)
                page_analysis['type'] = 'publication'
                
                self.parsed_data.append(page_analysis)
            
            time.sleep(self.download_delay)
        
        return True
    
    def save_parsing_results(self):
        """Сохраняет результаты парсинга"""
        # Сохраняем найденные кодексы
        codexes_file = self.output_dir / "parsed_data" / "found_codexes.json"
        with open(codexes_file, 'w', encoding='utf-8') as f:
            json.dump(self.found_codexes, f, ensure_ascii=False, indent=2)
        
        # Сохраняем анализ страниц
        analysis_file = self.output_dir / "parsed_data" / "page_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(self.parsed_data, f, ensure_ascii=False, indent=2)
        
        # Создаем сводный отчет
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_codexes_found': len(self.found_codexes),
            'total_pages_analyzed': len(self.parsed_data),
            'codexes_by_type': {},
            'summary': {
                'high_confidence_codexes': len([c for c in self.found_codexes if c['confidence'] >= 70]),
                'medium_confidence_codexes': len([c for c in self.found_codexes if 40 <= c['confidence'] < 70]),
                'low_confidence_codexes': len([c for c in self.found_codexes if c['confidence'] < 40])
            }
        }
        
        # Группируем кодексы по типам
        for codex in self.found_codexes:
            codex_type = codex['codex_type']
            if codex_type not in report['codexes_by_type']:
                report['codexes_by_type'][codex_type] = 0
            report['codexes_by_type'][codex_type] += 1
        
        report_file = self.output_dir / "parsed_data" / "parsing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Результаты парсинга сохранены:")
        self.log(f"   🔗 Кодексы: {codexes_file}")
        self.log(f"   📊 Анализ: {analysis_file}")
        self.log(f"   📋 Отчет: {report_file}")
        
        return report
    
    def run_deep_parsing(self):
        """Запускает глубокий парсинг"""
        self.log("🚀 Запуск глубокого парсинга кодексов")
        start_time = datetime.now()
        
        try:
            # Выполняем глубокий парсинг
            success = self.parse_codex_section_deep()
            
            if success:
                # Сохраняем результаты
                report = self.save_parsing_results()
                
                end_time = datetime.now()
                duration = end_time - start_time
                
                self.log(f"🎉 Парсинг завершен!")
                self.log(f"⏱️ Время выполнения: {duration}")
                self.log(f"🔗 Найдено кодексов: {report['total_codexes_found']}")
                self.log(f"📊 Проанализировано страниц: {report['total_pages_analyzed']}")
                
                return report
            else:
                self.log("❌ Парсинг не удался", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"💥 Критическая ошибка: {e}", "ERROR")
            return None

def main():
    """Основная функция"""
    print("🚀 Запуск продвинутого парсера кодексов")
    print("=" * 50)
    
    parser = AdvancedCodexParser()
    report = parser.run_deep_parsing()
    
    if report:
        print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ ПАРСИНГА:")
        print(f"   🔗 Найдено кодексов: {report['total_codexes_found']}")
        print(f"   📊 Проанализировано страниц: {report['total_pages_analyzed']}")
        print(f"   ✅ Высокая уверенность: {report['summary']['high_confidence_codexes']}")
        print(f"   ⚠️ Средняя уверенность: {report['summary']['medium_confidence_codexes']}")
        print(f"   ❓ Низкая уверенность: {report['summary']['low_confidence_codexes']}")
        
        if report['codexes_by_type']:
            print(f"\n🏛️ КОДЕКСЫ ПО ТИПАМ:")
            for codex_type, count in report['codexes_by_type'].items():
                print(f"   • {codex_type}: {count}")
    
    print(f"\n🎉 Парсинг завершен!")

if __name__ == "__main__":
    main()

