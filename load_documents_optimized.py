#!/usr/bin/env python3
"""
Оптимизированный скрипт для загрузки документов в ChromaDB
- Batch-добавление (быстро)
- Определение типа документа (категоризация)
- Сохранение всех метаданных
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'backend')
from app.services.vector_store_service import vector_store_service, determine_document_type

print("🚀 Инициализируем ChromaDB...")
vector_store_service.initialize()

if not vector_store_service.is_ready():
    print("❌ ChromaDB не готов")
    exit(1)

# Загружаем обработанные документы
processed_dir = Path('/root/advakod/unified_codexes/rag_integration/processed_documents')
processed_files = sorted(list(processed_dir.glob('*.json')))

print(f"📄 Найдено {len(processed_files)} обработанных документов\n")

# Параметры батчинга
BATCH_SIZE = 500  # Размер батча для добавления
added_total = 0
doc_types_count = {}

for i, processed_file in enumerate(processed_files, 1):
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        chunks = doc_data.get('chunks', [])
        document_id = doc_data.get('document_id', '')
        file_name = doc_data.get('metadata', {}).get('file_name', 'unknown')
        
        # Определяем тип документа для всего документа
        doc_type = determine_document_type(
            file_name=file_name,
            document_id=document_id,
            text_content=chunks[0].get('text', '') if chunks else ''
        )
        doc_types_count[doc_type] = doc_types_count.get(doc_type, 0) + 1
        
        print(f"[{i}/{len(processed_files)}] {file_name}")
        print(f"   Тип: {doc_type}, Чанков: {len(chunks)}", end=' ... ')
        
        # Собираем все чанки в батчи
        batch_documents = []
        batch_metadatas = []
        batch_ids = []
        
        for chunk in chunks:
            chunk_metadata = {
                **chunk.get('metadata', {}),
                'document_id': document_id,
                'document_type': doc_type,  # Добавляем тип документа
                'added_at': chunk.get('metadata', {}).get('processing_timestamp', '')
            }
            
            batch_documents.append(chunk.get('text', ''))
            batch_metadatas.append(chunk_metadata)
            batch_ids.append(chunk.get('id', ''))
            
            # Когда батч заполнен, добавляем его
            if len(batch_documents) >= BATCH_SIZE:
                try:
                    vector_store_service.collection.add(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                    added_total += len(batch_documents)
                    print(f"✅ +{len(batch_documents)}", end=' ', flush=True)
                except Exception as e:
                    print(f"\n❌ Ошибка при добавлении батча: {e}")
                
                # Очищаем батч
                batch_documents = []
                batch_metadatas = []
                batch_ids = []
        
        # Добавляем оставшиеся чанки
        if batch_documents:
            try:
                vector_store_service.collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                added_total += len(batch_documents)
                print(f"✅ +{len(batch_documents)}", end=' ', flush=True)
            except Exception as e:
                print(f"\n❌ Ошибка при добавлении последнего батча: {e}")
        
        print(f" ✅ Всего: {added_total}")
        
    except Exception as e:
        print(f"❌ Ошибка при обработке {processed_file.name}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"✅ Всего добавлено: {added_total:,} чанков")
count = vector_store_service.collection.count()
print(f"📊 Документов в ChromaDB: {count:,}")

print(f"\n📋 Распределение по типам документов:")
for doc_type, count in sorted(doc_types_count.items()):
    print(f"   {doc_type}: {count} документов")

print(f"{'='*60}")

