#!/usr/bin/env python3
"""
Скрипт для парсинга всех доступных кодексов с pravo.gov.ru
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin, urlparse
import time

def parse_codexes():
    """Парсит все доступные кодексы с pravo.gov.ru"""
    
    url = "http://pravo.gov.ru/codex/"
    
    try:
        print(f"🔍 Загружаем страницу: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Находим все ссылки на кодексы
        codex_links = []
        
        # Ищем все ссылки с actual.pravo.gov.ru
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if 'actual.pravo.gov.ru' in href:
                # Извлекаем текст ссылки
                text = link.get_text(strip=True)
                if text and len(text) > 10:  # Фильтруем короткие тексты
                    codex_links.append({
                        'title': text,
                        'url': href
                    })
        
        print(f"📋 Найдено ссылок: {len(codex_links)}")
        
        # Группируем кодексы по названиям
        codexes = {}
        
        for link in codex_links:
            title = link['title']
            url = link['url']
            
            # Определяем тип кодекса по названию
            if 'Гражданский кодекс' in title:
                codex_name = 'Гражданский кодекс РФ'
            elif 'Налоговый кодекс' in title:
                codex_name = 'Налоговый кодекс РФ'
            elif 'Трудовой кодекс' in title:
                codex_name = 'Трудовой кодекс РФ'
            elif 'Уголовный кодекс' in title and 'процессуальный' not in title:
                codex_name = 'Уголовный кодекс РФ'
            elif 'Кодекс об административных правонарушениях' in title:
                codex_name = 'Кодекс об административных правонарушениях РФ'
            elif 'Семейный кодекс' in title:
                codex_name = 'Семейный кодекс РФ'
            elif 'Жилищный кодекс' in title:
                codex_name = 'Жилищный кодекс РФ'
            elif 'Земельный кодекс' in title:
                codex_name = 'Земельный кодекс РФ'
            elif 'Градостроительный кодекс' in title:
                codex_name = 'Градостроительный кодекс РФ'
            elif 'Гражданский процессуальный кодекс' in title:
                codex_name = 'Гражданский процессуальный кодекс РФ'
            elif 'Арбитражный процессуальный кодекс' in title:
                codex_name = 'Арбитражный процессуальный кодекс РФ'
            elif 'Уголовно-процессуальный кодекс' in title:
                codex_name = 'Уголовно-процессуальный кодекс РФ'
            elif 'Кодекс административного судопроизводства' in title:
                codex_name = 'Кодекс административного судопроизводства РФ'
            else:
                # Для неизвестных кодексов используем первые слова
                words = title.split()[:3]
                codex_name = ' '.join(words)
            
            if codex_name not in codexes:
                codexes[codex_name] = {
                    'priority': 1 if any(x in codex_name for x in ['Гражданский', 'Налоговый', 'Трудовой', 'Уголовный']) else 2,
                    'urls': [],
                    'keywords': []
                }
            
            codexes[codex_name]['urls'].append(url)
            
            # Добавляем ключевые слова
            keywords = []
            if 'Гражданский' in codex_name:
                keywords.extend(['гражданский кодекс', 'гк рф', '51-ФЗ'])
            elif 'Налоговый' in codex_name:
                keywords.extend(['налоговый кодекс', 'нк рф', '146-ФЗ'])
            elif 'Трудовой' in codex_name:
                keywords.extend(['трудовой кодекс', 'тк рф', '197-ФЗ'])
            elif 'Уголовный' in codex_name and 'процессуальный' not in codex_name:
                keywords.extend(['уголовный кодекс', 'ук рф', '63-ФЗ'])
            elif 'административных правонарушениях' in codex_name:
                keywords.extend(['кодекс об административных правонарушениях', 'коап рф', '195-ФЗ'])
            elif 'Семейный' in codex_name:
                keywords.extend(['семейный кодекс', 'ск рф', '223-ФЗ'])
            elif 'Жилищный' in codex_name:
                keywords.extend(['жилищный кодекс', 'жк рф', '188-ФЗ'])
            elif 'Земельный' in codex_name:
                keywords.extend(['земельный кодекс', 'зк рф', '136-ФЗ'])
            
            codexes[codex_name]['keywords'] = list(set(keywords))
        
        # Удаляем дубликаты URL
        for codex_name in codexes:
            codexes[codex_name]['urls'] = list(set(codexes[codex_name]['urls']))
        
        print(f"📚 Найдено уникальных кодексов: {len(codexes)}")
        
        # Выводим результат
        for codex_name, info in codexes.items():
            print(f"\n📖 {codex_name}")
            print(f"   Приоритет: {info['priority']}")
            print(f"   Ссылок: {len(info['urls'])}")
            print(f"   Ключевые слова: {', '.join(info['keywords'])}")
            for i, url in enumerate(info['urls'], 1):
                print(f"   {i}. {url}")
        
        # Сохраняем в файл
        output_file = '/root/advakod/parsed_codexes.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(codexes, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результат сохранен в: {output_file}")
        
        return codexes
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        return {}

if __name__ == "__main__":
    parse_codexes()
