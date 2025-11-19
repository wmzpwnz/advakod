#!/usr/bin/env python3
"""
Валидатор правовых документов
Проверяет, является ли документ правовым и релевантным для RAG системы
"""

import re
import json
import os
from datetime import datetime
from pathlib import Path

class DocumentValidator:
    """Валидатор правовых документов"""
    
    def __init__(self, output_dir="/var/www/advacodex.com/validation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректории
        (self.output_dir / "valid_documents").mkdir(exist_ok=True)
        (self.output_dir / "invalid_documents").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        # Ключевые слова для правовых документов
        self.legal_keywords = [
            # Основные правовые термины
            'статья', 'глава', 'раздел', 'часть', 'пункт', 'подпункт',
            'кодекс', 'закон', 'указ', 'постановление', 'распоряжение',
            'приказ', 'инструкция', 'положение', 'правила', 'регламент',
            
            # Правовые области
            'гражданский', 'уголовный', 'административный', 'трудовой',
            'налоговый', 'семейный', 'жилищный', 'земельный', 'водный',
            'лесной', 'воздушный', 'таможенный', 'бюджетный',
            'арбитражный', 'процессуальный', 'исполнительный',
            
            # Правовые субъекты
            'российская федерация', 'рф', 'государство', 'орган',
            'министерство', 'ведомство', 'служба', 'агентство',
            'суд', 'прокуратура', 'полиция', 'налоговая',
            
            # Правовые действия
            'право', 'обязанность', 'ответственность', 'нарушение',
            'преступление', 'правонарушение', 'санкция', 'наказание',
            'штраф', 'лишение', 'ограничение', 'приостановление'
        ]
        
        # Ключевые слова для исключения (неправовые документы)
        self.exclusion_keywords = [
            'назначение', 'освобождение', 'награждение', 'поощрение',
            'поздравление', 'приветствие', 'благодарность', 'соболезнование',
            'техническое', 'технологическое', 'инструкция по эксплуатации',
            'руководство пользователя', 'каталог', 'прейскурант', 'тариф',
            'расписание', 'график работы', 'меню', 'рецепт'
        ]
        
        # Паттерны для определения типа документа
        self.document_patterns = {
            'federal_law': r'федеральный закон|фз|№\s*\d+',
            'presidential_decree': r'указ президента|указом президента',
            'government_resolution': r'постановление правительства|постановлением правительства',
            'ministerial_order': r'приказ министерства|приказом министерства',
            'codex': r'кодекс|кодекса|кодексом',
            'constitution': r'конституция|конституции|конституцией',
            'regulation': r'положение|положения|положением',
            'instruction': r'инструкция|инструкции|инструкцией'
        }
        
        self.validation_results = []
        
        print(f"✅ DocumentValidator инициализирован")
        print(f"📁 Выходная директория: {self.output_dir}")
    
    def log(self, message, level="INFO"):
        """Логирование"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Сохраняем в файл
        log_file = self.output_dir / "logs" / f"validator_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def extract_text_from_html(self, html_content):
        """Извлекает текст из HTML"""
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\"\'№]', ' ', text)
        
        return text.strip()
    
    def extract_text_from_pdf(self, pdf_path):
        """Извлекает текст из PDF (упрощенная версия)"""
        try:
            # Для простоты, читаем как бинарный файл и ищем текстовые паттерны
            with open(pdf_path, 'rb') as f:
                content = f.read()
            
            # Пытаемся декодировать как текст (работает для некоторых PDF)
            try:
                text = content.decode('utf-8', errors='ignore')
                # Очищаем от бинарных данных
                text = re.sub(r'[^\x20-\x7E\u0400-\u04FF]', ' ', text)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            except:
                return ""
                
        except Exception as e:
            self.log(f"❌ Ошибка чтения PDF {pdf_path}: {e}", "ERROR")
            return ""
    
    def calculate_legal_score(self, text):
        """Вычисляет оценку правовости документа"""
        if not text:
            return 0
        
        text_lower = text.lower()
        score = 0
        
        # Подсчитываем правовые ключевые слова
        for keyword in self.legal_keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            score += count * 2  # Каждое ключевое слово дает 2 балла
        
        # Штрафы за исключающие ключевые слова
        for keyword in self.exclusion_keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            score -= count * 3  # Каждое исключающее слово отнимает 3 балла
        
        # Бонусы за правовые паттерны
        for pattern_name, pattern in self.document_patterns.items():
            if re.search(pattern, text_lower):
                score += 10  # Каждый паттерн дает 10 баллов
        
        # Нормализуем оценку относительно длины текста
        text_length = len(text.split())
        if text_length > 0:
            score = (score / text_length) * 100
        
        return max(0, min(100, score))  # Ограничиваем от 0 до 100
    
    def determine_document_type(self, text):
        """Определяет тип документа"""
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        type_scores = {}
        
        for doc_type, pattern in self.document_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            type_scores[doc_type] = matches
        
        # Возвращаем тип с наибольшим количеством совпадений
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        return "general_legal"
    
    def validate_document(self, file_path, content=None):
        """Валидирует документ"""
        file_path = Path(file_path)
        
        self.log(f"🔍 Валидируем документ: {file_path.name}")
        
        # Извлекаем текст в зависимости от типа файла
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.html', '.htm']:
            if content:
                text = self.extract_text_from_html(content)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                text = self.extract_text_from_html(html_content)
        else:
            # Для других типов файлов пытаемся читать как текст
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except:
                text = ""
        
        # Вычисляем оценку правовости
        legal_score = self.calculate_legal_score(text)
        
        # Определяем тип документа
        doc_type = self.determine_document_type(text)
        
        # Определяем, является ли документ валидным
        is_valid = legal_score >= 30  # Порог валидности
        
        # Создаем результат валидации
        validation_result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'legal_score': legal_score,
            'document_type': doc_type,
            'is_valid': is_valid,
            'text_length': len(text),
            'validation_timestamp': datetime.now().isoformat(),
            'recommendations': self.get_recommendations(legal_score, doc_type)
        }
        
        self.validation_results.append(validation_result)
        
        # Логируем результат
        status = "✅ ВАЛИДЕН" if is_valid else "❌ НЕВАЛИДЕН"
        self.log(f"{status} {file_path.name} (оценка: {legal_score:.1f}, тип: {doc_type})")
        
        return validation_result
    
    def get_recommendations(self, legal_score, doc_type):
        """Получает рекомендации по документу"""
        recommendations = []
        
        if legal_score >= 70:
            recommendations.append("Отличный правовой документ, рекомендуется для RAG")
        elif legal_score >= 50:
            recommendations.append("Хороший правовой документ, подходит для RAG")
        elif legal_score >= 30:
            recommendations.append("Слабый правовой документ, требует проверки")
        else:
            recommendations.append("Не рекомендуется для RAG системы")
        
        if doc_type == "codex":
            recommendations.append("Кодекс - приоритетный документ")
        elif doc_type == "federal_law":
            recommendations.append("Федеральный закон - важный документ")
        elif doc_type == "constitution":
            recommendations.append("Конституция - базовый документ")
        
        return recommendations
    
    def validate_directory(self, directory_path):
        """Валидирует все документы в директории"""
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            self.log(f"❌ Директория не найдена: {directory_path}", "ERROR")
            return []
        
        self.log(f"📁 Валидируем директорию: {directory_path}")
        
        # Находим все файлы
        file_extensions = ['.pdf', '.html', '.htm', '.txt', '.doc', '.docx']
        files = []
        
        for ext in file_extensions:
            files.extend(directory_path.glob(f"**/*{ext}"))
        
        self.log(f"📄 Найдено файлов для валидации: {len(files)}")
        
        # Валидируем каждый файл
        for i, file_path in enumerate(files, 1):
            self.log(f"🔍 Валидируем файл {i}/{len(files)}: {file_path.name}")
            self.validate_document(file_path)
        
        return self.validation_results
    
    def save_validation_report(self):
        """Сохраняет отчет о валидации"""
        if not self.validation_results:
            self.log("⚠️ Нет результатов валидации для сохранения", "WARNING")
            return None
        
        # Создаем сводный отчет
        total_files = len(self.validation_results)
        valid_files = len([r for r in self.validation_results if r['is_valid']])
        invalid_files = total_files - valid_files
        
        # Группируем по типам документов
        doc_types = {}
        for result in self.validation_results:
            doc_type = result['document_type']
            if doc_type not in doc_types:
                doc_types[doc_type] = {'count': 0, 'valid': 0, 'avg_score': 0}
            doc_types[doc_type]['count'] += 1
            if result['is_valid']:
                doc_types[doc_type]['valid'] += 1
            doc_types[doc_type]['avg_score'] += result['legal_score']
        
        # Вычисляем средние оценки
        for doc_type in doc_types:
            if doc_types[doc_type]['count'] > 0:
                doc_types[doc_type]['avg_score'] /= doc_types[doc_type]['count']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': total_files,
                'valid_files': valid_files,
                'invalid_files': invalid_files,
                'validation_rate': (valid_files / total_files * 100) if total_files > 0 else 0
            },
            'document_types': doc_types,
            'detailed_results': self.validation_results
        }
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / "reports" / f"validation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Отчет валидации сохранен: {report_file}")
        
        # Сохраняем валидные и невалидные документы отдельно
        valid_file = self.output_dir / "reports" / f"valid_documents_{timestamp}.json"
        invalid_file = self.output_dir / "reports" / f"invalid_documents_{timestamp}.json"
        
        valid_docs = [r for r in self.validation_results if r['is_valid']]
        invalid_docs = [r for r in self.validation_results if not r['is_valid']]
        
        with open(valid_file, 'w', encoding='utf-8') as f:
            json.dump(valid_docs, f, ensure_ascii=False, indent=2)
        
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_docs, f, ensure_ascii=False, indent=2)
        
        return report

def main():
    """Основная функция"""
    print("🚀 Запуск валидатора документов")
    print("=" * 50)
    
    validator = DocumentValidator()
    
    # Валидируем скачанные документы
    downloaded_dir = "/var/www/advacodex.com/downloaded_documents"
    if Path(downloaded_dir).exists():
        validator.validate_directory(downloaded_dir)
    else:
        print(f"❌ Директория не найдена: {downloaded_dir}")
        return
    
    # Сохраняем отчет
    report = validator.save_validation_report()
    
    if report:
        print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ ВАЛИДАЦИИ:")
        print(f"   📄 Всего файлов: {report['summary']['total_files']}")
        print(f"   ✅ Валидных: {report['summary']['valid_files']}")
        print(f"   ❌ Невалидных: {report['summary']['invalid_files']}")
        print(f"   📊 Процент валидности: {report['summary']['validation_rate']:.1f}%")
        
        if report['document_types']:
            print(f"\n📋 ТИПЫ ДОКУМЕНТОВ:")
            for doc_type, stats in report['document_types'].items():
                print(f"   • {doc_type}: {stats['count']} файлов (валидных: {stats['valid']}, средняя оценка: {stats['avg_score']:.1f})")
    
    print(f"\n🎉 Валидация завершена!")

if __name__ == "__main__":
    main()

