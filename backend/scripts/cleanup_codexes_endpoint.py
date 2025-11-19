#!/usr/bin/env python3
"""
Быстрое удаление старых заглушек через API endpoint
Использование: python cleanup_codexes_endpoint.py
"""

import requests
import json

API_BASE_URL = "https://advacodex.com/api/v1"
# Для локального теста: API_BASE_URL = "http://localhost:8000/api/v1"

# Список старых заглушек для удаления
OLD_CODEXES_IDS = [
    "0001201412140001",  # Трудовой кодекс РФ
    "0001201412140002",  # Семейный кодекс РФ
    "0001201412140003",  # Жилищный кодекс РФ
    "0001201412140004",  # Налоговый кодекс РФ
    "0001201412140005",  # Бюджетный кодекс РФ
    "0001201412140006",  # Кодекс об административных правонарушениях РФ
    "0001201410140002",  # Гражданский кодекс РФ (часть 1) - заглушка
    "0001201905010039",  # Налоговый кодекс РФ (часть 1) - заглушка
    "0001202203030006",  # Уголовный кодекс РФ - заглушка
    "198",
    "289-11",
]

def get_token():
    """Получает токен из переменной окружения или запрашивает"""
    import os
    token = os.getenv("ADMIN_TOKEN")
    if not token:
        token = input("Введите токен администратора: ").strip()
    return token

def get_documents(token):
    """Получает список документов"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/admin/documents?skip=0&limit=1000", headers=headers)
    
    if response.status_code == 200:
        return response.json().get("documents", [])
    else:
        print(f"❌ Ошибка получения документов: {response.status_code}")
        print(response.text)
        return []

def delete_document(token, document_id):
    """Удаляет документ"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_BASE_URL}/admin/documents/{document_id}", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"success": False, "error": response.text}

def main():
    print("="*60)
    print("🧹 Удаление старых заглушек кодексов")
    print("="*60)
    print()
    
    token = get_token()
    if not token:
        print("❌ Токен не предоставлен")
        return
    
    # Получаем список документов
    print("📋 Получаем список документов...")
    documents = get_documents(token)
    
    if not documents:
        print("⚠️ Не удалось получить список документов")
        return
    
    print(f"✅ Найдено документов: {len(documents)}\n")
    
    # Находим документы для удаления
    to_delete = []
    for doc in documents:
        doc_id = doc.get("id") or doc.get("document_id")
        filename = doc.get("filename") or doc.get("file_name", "")
        size = doc.get("size", 0)
        
        # Проверяем по ID или имени файла
        for old_id in OLD_CODEXES_IDS:
            if old_id in str(doc_id) or old_id in filename:
                to_delete.append({
                    "id": doc_id,
                    "title": doc.get("title", "Unknown"),
                    "filename": filename,
                    "size": size
                })
                break
        
        # Также проверяем маленькие файлы кодексов
        if size <= 1000 and doc not in to_delete:
            title = doc.get("title", "").lower()
            if any(kw in title for kw in ["кодекс", "codex"]):
                to_delete.append({
                    "id": doc_id,
                    "title": doc.get("title", "Unknown"),
                    "filename": filename,
                    "size": size
                })
    
    if not to_delete:
        print("✅ Старые заглушки не найдены!")
        return
    
    print(f"🗑️ Найдено документов для удаления: {len(to_delete)}\n")
    for i, doc in enumerate(to_delete, 1):
        print(f"{i}. {doc['title']} ({doc['id']}) - {doc['size']} байт")
    
    print()
    confirm = input("⚠️ Удалить эти документы? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено")
        return
    
    # Удаляем
    print("\n🗑️ Удаляем документы...\n")
    results = []
    for doc in to_delete:
        print(f"Удаляем: {doc['title']}...", end=" ")
        result = delete_document(token, doc['id'])
        
        if result.get('success', False):
            chunks = result.get('total_chunks_deleted', 0)
            print(f"✅ Удалено (чанков: {chunks})")
            results.append(True)
        else:
            print(f"❌ Ошибка: {result.get('error', 'Unknown')}")
            results.append(False)
    
    # Итоги
    print("\n" + "="*60)
    print(f"✅ Успешно удалено: {sum(results)}/{len(to_delete)}")
    print("="*60)

if __name__ == "__main__":
    main()

