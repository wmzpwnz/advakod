#!/usr/bin/env python3
"""
Скрипт для удаления старых заглушек кодексов (500 байт) из RAG системы
"""

import sys
import os
import asyncio
import aiohttp
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Список старых заглушек, которые нужно удалить
OLD_CODEXES = [
    "0001201412140001",  # Трудовой кодекс РФ (500 байт)
    "0001201412140002",  # Семейный кодекс РФ
    "0001201412140003",  # Жилищный кодекс РФ
    "0001201412140004",  # Налоговый кодекс РФ
    "0001201412140005",  # Бюджетный кодекс РФ
    "0001201412140006",  # Кодекс об административных правонарушениях РФ
    "0001201410140002",  # Гражданский кодекс РФ (часть 1) - Указ Президента (заглушка)
    "0001201905010039",  # Налоговый кодекс РФ (часть 1) - только 11 страниц
    "0001202203030006",  # Уголовный кодекс РФ - только 4 страницы
    "198",  # Указ Президента (заглушка)
    "289-11",  # Указ Президента (заглушка)
]

# Также удаляем по именам файлов
OLD_FILENAMES = [
    "0001201412140001.txt",
    "0001201412140002.txt",
    "0001201412140003.txt",
    "0001201412140004.txt",
    "0001201412140005.txt",
    "0001201412140006.txt",
    "0001201410140002.pdf",
    "0001201905010039.pdf",
    "0001202203030006.pdf",
    "198.pdf",
    "289-11.pdf",
]

# API URL
API_BASE_URL = "https://advacodex.com/api/v1"
# Для локального теста: API_BASE_URL = "http://localhost:8000/api/v1"

async def delete_document(session: aiohttp.ClientSession, document_id: str, token: str):
    """Удаляет документ через API"""
    try:
        url = f"{API_BASE_URL}/admin/documents/{document_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with session.delete(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "document_id": document_id,
                    "result": data
                }
            elif response.status == 404:
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": "Document not found"
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "document_id": document_id,
                    "error": f"HTTP {response.status}: {error_text}"
                }
    except Exception as e:
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e)
        }

async def get_documents_list(session: aiohttp.ClientSession, token: str):
    """Получает список документов"""
    try:
        url = f"{API_BASE_URL}/admin/documents"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with session.get(url, headers=headers, params={"skip": 0, "limit": 1000}) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("documents", [])
            else:
                error_text = await response.text()
                print(f"❌ Ошибка получения списка документов: HTTP {response.status}: {error_text}")
                return []
    except Exception as e:
        print(f"❌ Ошибка получения списка документов: {e}")
        return []

async def cleanup_old_codexes(token: str):
    """Удаляет старые заглушки кодексов"""
    print("🧹 Начинаем очистку старых заглушек кодексов...\n")
    
    async with aiohttp.ClientSession() as session:
        # Получаем список всех документов
        print("📋 Получаем список документов...")
        documents = await get_documents_list(session, token)
        
        if not documents:
            print("⚠️ Не удалось получить список документов или список пуст")
            return
        
        print(f"✅ Найдено документов: {len(documents)}\n")
        
        # Находим документы для удаления
        documents_to_delete = []
        
        for doc in documents:
            doc_id = doc.get("id") or doc.get("document_id")
            filename = doc.get("filename") or doc.get("file_name", "")
            size = doc.get("size", 0)
            
            # Проверяем по eo_number
            should_delete = False
            reason = ""
            
            # Проверяем по имени файла
            for old_filename in OLD_FILENAMES:
                if old_filename in filename:
                    should_delete = True
                    reason = f"Старая заглушка (по имени файла: {old_filename})"
                    break
            
            # Проверяем по eo_number в document_id или filename
            if not should_delete:
                for old_codex_id in OLD_CODEXES:
                    if old_codex_id in str(doc_id) or old_codex_id in filename:
                        should_delete = True
                        reason = f"Старая заглушка (по ID: {old_codex_id})"
                        break
            
            # Проверяем размер (маленькие файлы <= 1000 байт)
            if not should_delete and size <= 1000:
                # Проверяем, что это кодекс (по названию или типу)
                title = doc.get("title", "").lower()
                doc_type = doc.get("type", "").lower()
                if any(keyword in title or keyword in doc_type for keyword in ["кодекс", "codex", "трудовой", "гражданский", "налоговый", "бюджетный"]):
                    should_delete = True
                    reason = f"Маленький файл кодекса ({size} байт) - вероятно заглушка"
            
            if should_delete:
                documents_to_delete.append({
                    "id": doc_id,
                    "filename": filename,
                    "title": doc.get("title", "Unknown"),
                    "size": size,
                    "reason": reason
                })
        
        if not documents_to_delete:
            print("✅ Старые заглушки не найдены!\n")
            return
        
        print(f"🗑️ Найдено документов для удаления: {len(documents_to_delete)}\n")
        
        # Показываем список
        for i, doc in enumerate(documents_to_delete, 1):
            print(f"{i}. {doc['title']}")
            print(f"   ID: {doc['id']}")
            print(f"   Файл: {doc['filename']}")
            print(f"   Размер: {doc['size']} байт")
            print(f"   Причина: {doc['reason']}\n")
        
        # Подтверждение
        confirm = input("⚠️ Удалить эти документы? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y', 'да', 'д']:
            print("❌ Отменено пользователем")
            return
        
        # Удаляем документы
        print("\n🗑️ Удаляем документы...\n")
        results = []
        
        for doc in documents_to_delete:
            print(f"Удаляем: {doc['title']} ({doc['id']})...", end=" ")
            result = await delete_document(session, doc['id'], token)
            results.append(result)
            
            if result['success']:
                chunks_deleted = result.get('result', {}).get('total_chunks_deleted', 0)
                print(f"✅ Удалено (чанков: {chunks_deleted})")
            else:
                print(f"❌ Ошибка: {result.get('error', 'Unknown')}")
        
        # Итоги
        print("\n" + "="*60)
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        total_chunks = sum(r.get('result', {}).get('total_chunks_deleted', 0) for r in results if r['success'])
        
        print(f"✅ Успешно удалено: {successful}/{len(results)}")
        print(f"❌ Ошибок: {failed}")
        print(f"📦 Всего удалено чанков: {total_chunks}")
        print("="*60)

def main():
    """Главная функция"""
    print("="*60)
    print("🧹 Очистка старых заглушек кодексов")
    print("="*60)
    print()
    
    # Получаем токен
    token = os.getenv("ADMIN_TOKEN")
    if not token:
        token = input("Введите токен администратора: ").strip()
        if not token:
            print("❌ Токен не предоставлен")
            return
    
    # Запускаем очистку
    asyncio.run(cleanup_old_codexes(token))
    
    print("\n✅ Очистка завершена!")

if __name__ == "__main__":
    main()

