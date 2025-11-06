#!/usr/bin/env python3
"""
Сервис интеграции скачанных документов с RAG системой
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path

class RAGIntegrationService:
    """Сервис интеграции с RAG системой"""
    
    def __init__(self, output_dir="/root/advakod/rag_integration"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректории для RAG
        (self.output_dir / "processed_documents").mkdir(exist_ok=True)
        (self.output_dir / "chunks").mkdir(exist_ok=True)
        (self.output_dir / "embeddings").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        # Настройки для чанкинга
        self.chunk_size = 1000  # Размер чанка в символах
        self.chunk_overlap = 200  # Перекрытие между чанками
        
        # Счетчики
        self.processed_documents = 0
        self.total_chunks = 0
        self.integration_results = []
        
        print(f"✅ RAGIntegrationService инициализирован")
        print(f"📁 Выходная директория: {self.output_dir}")
    
    def log(self, message, level="INFO"):
        """Логирование"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Сохраняем в файл
        log_file = self.output_dir / "logs" / f"integration_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def extract_text_from_html(self, html_content):
        """Извлекает текст из HTML"""
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы, но оставляем правовые
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\"\'№]', ' ', text)
        
        return text.strip()
    
    def clean_text(self, text):
        """Очищает текст для RAG"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем служебные символы
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\"\'№]', ' ', text)
        
        # Удаляем очень короткие строки
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return ' '.join(cleaned_lines)
    
    def create_chunks(self, text, document_id, metadata=None):
        """Создает чанки из текста"""
        if not text or len(text) < self.chunk_size:
            return [{
                'id': f"{document_id}_chunk_0",
                'text': text,
                'metadata': metadata or {},
                'chunk_index': 0,
                'total_chunks': 1
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Определяем конец чанка
            end = start + self.chunk_size
            
            # Пытаемся закончить на границе предложения
            if end < len(text):
                # Ищем последнюю точку, восклицательный или вопросительный знак
                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    'id': f"{document_id}_chunk_{chunk_index}",
                    'text': chunk_text,
                    'metadata': {
                        **(metadata or {}),
                        'chunk_index': chunk_index,
                        'start_position': start,
                        'end_position': end,
                        'chunk_length': len(chunk_text)
                    },
                    'chunk_index': chunk_index,
                    'total_chunks': 0  # Будет обновлено позже
                }
                chunks.append(chunk)
                chunk_index += 1
            
            # Перемещаемся с учетом перекрытия
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        # Обновляем total_chunks для всех чанков
        for chunk in chunks:
            chunk['total_chunks'] = len(chunks)
            chunk['metadata']['total_chunks'] = len(chunks)
        
        return chunks
    
    def process_html_document(self, file_path, validation_result=None):
        """Обрабатывает HTML документ"""
        self.log(f"📄 Обрабатываем HTML документ: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Извлекаем текст
            text = self.extract_text_from_html(html_content)
            text = self.clean_text(text)
            
            if not text or len(text) < 50:
                self.log(f"⚠️ Документ {file_path.name} содержит слишком мало текста", "WARNING")
                return None
            
            # Создаем метаданные
            metadata = {
                'source': 'pravo.gov.ru',
                'file_type': 'html',
                'file_name': file_path.name,
                'file_path': str(file_path),
                'processing_timestamp': datetime.now().isoformat(),
                'text_length': len(text)
            }
            
            # Добавляем данные валидации, если есть
            if validation_result:
                metadata.update({
                    'legal_score': validation_result.get('legal_score', 0),
                    'document_type': validation_result.get('document_type', 'unknown'),
                    'is_valid': validation_result.get('is_valid', False)
                })
            
            # Создаем уникальный document_id на основе имени файла и его содержимого
            # Это предотвращает дублирование при повторной обработке
            content_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()[:8]
            document_id = f"html_{file_path.stem}_{content_hash}"
            
            # Проверяем, не был ли документ уже обработан
            processed_file = self.output_dir / "processed_documents" / f"{document_id}.json"
            if processed_file.exists():
                self.log(f"⏭️ Документ {file_path.name} уже обработан, пропускаем", "INFO")
                with open(processed_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                return {
                    'document_id': document_id,
                    'chunks_count': len(existing_data.get('chunks', [])),
                    'text_length': existing_data.get('text_length', 0),
                    'processed_file': str(processed_file),
                    'skipped': True
                }
            
            chunks = self.create_chunks(text, document_id, metadata)
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'document_id': document_id,
                    'original_file': str(file_path),
                    'text': text,
                    'metadata': metadata,
                    'chunks': chunks
                }, f, ensure_ascii=False, indent=2)
            
            # Сохраняем чанки отдельно
            for chunk in chunks:
                chunk_file = self.output_dir / "chunks" / f"{chunk['id']}.json"
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
            
            self.processed_documents += 1
            self.total_chunks += len(chunks)
            
            self.log(f"✅ Обработан документ {file_path.name}: {len(chunks)} чанков")
            
            return {
                'document_id': document_id,
                'chunks_count': len(chunks),
                'text_length': len(text),
                'processed_file': str(processed_file)
            }
            
        except Exception as e:
            self.log(f"❌ Ошибка обработки {file_path.name}: {e}", "ERROR")
            return None
    
    def process_pdf_document(self, file_path, validation_result=None):
        """Обрабатывает PDF документ (упрощенная версия)"""
        self.log(f"📄 Обрабатываем PDF документ: {file_path.name}")
        
        try:
            # Для PDF пытаемся извлечь текст (упрощенная версия)
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Пытаемся декодировать как текст
            try:
                text = content.decode('utf-8', errors='ignore')
                # Очищаем от бинарных данных
                text = re.sub(r'[^\x20-\x7E\u0400-\u04FF]', ' ', text)
                text = self.clean_text(text)
            except:
                text = ""
            
            if not text or len(text) < 50:
                self.log(f"⚠️ PDF {file_path.name} не содержит извлекаемого текста", "WARNING")
                # Создаем заглушку для PDF
                text = f"PDF документ: {file_path.name}\nИсточник: pravo.gov.ru\nТип: Правовой документ"
            
            # Создаем метаданные
            metadata = {
                'source': 'pravo.gov.ru',
                'file_type': 'pdf',
                'file_name': file_path.name,
                'file_path': str(file_path),
                'processing_timestamp': datetime.now().isoformat(),
                'text_length': len(text),
                'file_size': file_path.stat().st_size
            }
            
            # Добавляем данные валидации, если есть
            if validation_result:
                metadata.update({
                    'legal_score': validation_result.get('legal_score', 0),
                    'document_type': validation_result.get('document_type', 'unknown'),
                    'is_valid': validation_result.get('is_valid', False)
                })
            
            # Создаем уникальный document_id на основе имени файла и его содержимого
            # Это предотвращает дублирование при повторной обработке
            file_hash = hashlib.md5(content).hexdigest()[:8]
            document_id = f"pdf_{file_path.stem}_{file_hash}"
            
            # Проверяем, не был ли документ уже обработан
            processed_file = self.output_dir / "processed_documents" / f"{document_id}.json"
            if processed_file.exists():
                self.log(f"⏭️ Документ {file_path.name} уже обработан, пропускаем", "INFO")
                with open(processed_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                return {
                    'document_id': document_id,
                    'chunks_count': len(existing_data.get('chunks', [])),
                    'text_length': existing_data.get('text_length', 0),
                    'processed_file': str(processed_file),
                    'skipped': True
                }
            
            chunks = self.create_chunks(text, document_id, metadata)
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'document_id': document_id,
                    'original_file': str(file_path),
                    'text': text,
                    'metadata': metadata,
                    'chunks': chunks
                }, f, ensure_ascii=False, indent=2)
            
            # Сохраняем чанки отдельно
            for chunk in chunks:
                chunk_file = self.output_dir / "chunks" / f"{chunk['id']}.json"
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
            
            self.processed_documents += 1
            self.total_chunks += len(chunks)
            
            self.log(f"✅ Обработан PDF {file_path.name}: {len(chunks)} чанков")
            
            return {
                'document_id': document_id,
                'chunks_count': len(chunks),
                'text_length': len(text),
                'processed_file': str(processed_file)
            }
            
        except Exception as e:
            self.log(f"❌ Ошибка обработки PDF {file_path.name}: {e}", "ERROR")
            return None
    
    def integrate_documents(self, documents_dir, validation_results=None):
        """Интегрирует все документы в RAG систему"""
        documents_dir = Path(documents_dir)
        
        if not documents_dir.exists():
            self.log(f"❌ Директория не найдена: {documents_dir}", "ERROR")
            return []
        
        self.log(f"🚀 Начинаем интеграцию документов из: {documents_dir}")
        
        # Создаем словарь результатов валидации для быстрого поиска
        validation_dict = {}
        if validation_results:
            for result in validation_results:
                file_path = Path(result['file_path'])
                validation_dict[file_path.name] = result
        
        # Находим все файлы
        html_files = list(documents_dir.glob("**/*.html"))
        pdf_files = list(documents_dir.glob("**/*.pdf"))
        
        all_files = html_files + pdf_files
        self.log(f"📄 Найдено файлов для интеграции: {len(all_files)}")
        
        # Обрабатываем каждый файл
        for i, file_path in enumerate(all_files, 1):
            self.log(f"🔄 Обрабатываем файл {i}/{len(all_files)}: {file_path.name}")
            
            # Получаем результат валидации
            validation_result = validation_dict.get(file_path.name)
            
            # Обрабатываем в зависимости от типа файла
            if file_path.suffix.lower() == '.html':
                result = self.process_html_document(file_path, validation_result)
            elif file_path.suffix.lower() == '.pdf':
                result = self.process_pdf_document(file_path, validation_result)
            else:
                self.log(f"⚠️ Неподдерживаемый тип файла: {file_path.name}", "WARNING")
                continue
            
            if result:
                self.integration_results.append(result)
        
        return self.integration_results
    
    def create_rag_metadata(self):
        """Создает метаданные для RAG системы"""
        metadata = {
            'integration_timestamp': datetime.now().isoformat(),
            'total_documents': self.processed_documents,
            'total_chunks': self.total_chunks,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'source': 'pravo.gov.ru',
            'integration_results': self.integration_results
        }
        
        metadata_file = self.output_dir / "metadata" / "rag_integration_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Метаданные RAG сохранены: {metadata_file}")
        return metadata
    
    def save_integration_report(self):
        """Сохраняет отчет об интеграции"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_documents_processed': self.processed_documents,
                'total_chunks_created': self.total_chunks,
                'successful_integrations': len(self.integration_results),
                'failed_integrations': self.processed_documents - len(self.integration_results)
            },
            'integration_results': self.integration_results,
            'output_directory': str(self.output_dir)
        }
        
        report_file = self.output_dir / "metadata" / "integration_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 Отчет интеграции сохранен: {report_file}")
        return report

def main():
    """Основная функция"""
    print("🚀 Запуск сервиса интеграции с RAG")
    print("=" * 50)
    
    integration_service = RAGIntegrationService()
    
    # Интегрируем скачанные документы
    downloaded_dir = "/root/advakod/downloaded_documents"
    if not Path(downloaded_dir).exists():
        print(f"❌ Директория не найдена: {downloaded_dir}")
        return
    
    # Загружаем результаты валидации, если есть
    validation_results = None
    validation_report_file = "/root/advakod/validation_results/reports/validation_report_20251026_015020.json"
    if Path(validation_report_file).exists():
        with open(validation_report_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
            validation_results = validation_data.get('detailed_results', [])
        print(f"📊 Загружены результаты валидации: {len(validation_results)} документов")
    
    # Интегрируем документы
    results = integration_service.integrate_documents(downloaded_dir, validation_results)
    
    # Создаем метаданные и отчет
    integration_service.create_rag_metadata()
    report = integration_service.save_integration_report()
    
    if report:
        print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ ИНТЕГРАЦИИ:")
        print(f"   📄 Обработано документов: {report['summary']['total_documents_processed']}")
        print(f"   🔗 Создано чанков: {report['summary']['total_chunks_created']}")
        print(f"   ✅ Успешных интеграций: {report['summary']['successful_integrations']}")
        print(f"   ❌ Неудачных интеграций: {report['summary']['failed_integrations']}")
        print(f"   📁 Выходная директория: {report['output_directory']}")
        
        if results:
            print(f"\n📋 ДЕТАЛИ ИНТЕГРАЦИИ:")
            for result in results:
                print(f"   • {result['document_id']}: {result['chunks_count']} чанков, {result['text_length']} символов")
    
    print(f"\n🎉 Интеграция с RAG завершена!")

if __name__ == "__main__":
    main()
