#!/usr/bin/env python3
"""
Скрипт для загрузки потребительского кодекса
"""

import requests
import json
import os

# URL админ панели
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@ai-lawyer.ru"
ADMIN_PASSWORD = None  # Пароль будет запрошен интерактивно

def login_admin():
    """Вход в систему как администратор"""
    if ADMIN_PASSWORD is None:
        import getpass
        password = getpass.getpass("Введите пароль администратора: ")
    else:
        password = ADMIN_PASSWORD
    
    login_data = {
        "email": ADMIN_EMAIL,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/admin-login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Ошибка входа: {response.text}")
        return None

def upload_document(token, file_path):
    """Загружает документ"""
    headers = {"Authorization": f"Bearer {token}"}
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return None
    
    with open(file_path, 'rb') as file:
        # Определяем MIME тип по расширению файла
        if file_path.endswith('.txt'):
            mime_type = 'text/plain'
        elif file_path.endswith('.pdf'):
            mime_type = 'application/pdf'
        elif file_path.endswith('.docx'):
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            mime_type = 'text/plain'
            
        files = {'file': (os.path.basename(file_path), file, mime_type)}
        data = {'description': 'Потребительский кодекс РФ'}
        
        response = requests.post(f"{BASE_URL}/admin/documents/upload", headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Документ загружен успешно!")
            print(f"   Название: {result.get('message', 'N/A')}")
            return result
        else:
            print(f"❌ Ошибка загрузки: {response.text}")
            return None

def get_documents(token):
    """Получить список документов"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/admin/documents", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"\n📄 Документы ({result['total']}):")
        for doc in result['documents']:
            metadata = doc.get('metadata', {})
            print(f"  - {metadata.get('filename', 'Unknown')}")
            print(f"    Тип: {metadata.get('document_type', 'unknown')}")
            print(f"    Страниц: {metadata.get('pages', 'неизвестно')}")
            print(f"    Размер: {metadata.get('file_size', 0)} байт")
            print()
        return result
    else:
        print(f"❌ Ошибка получения документов: {response.text}")
        return None

def main():
    print("📄 Загрузка потребительского кодекса")
    print("=" * 50)
    
    # Входим в систему
    print("1. Вход в систему...")
    token = login_admin()
    if not token:
        return
    
    print("✅ Успешный вход")
    
    # Ищем файл потребительского кодекса
    possible_paths = [
        "/Users/macbook/Desktop/advakod/test_consumer_code.txt",
        "/Users/macbook/Desktop/advakod/backend/constitution.pdf",
        "/Users/macbook/Desktop/advakod/constitution.pdf",
        "/Users/macbook/Desktop/advakod/backend/documents/example_law.txt"
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        print("❌ Файл потребительского кодекса не найден")
        print("Доступные файлы:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    print(f"📁 Найден файл: {file_path}")
    
    # Загружаем документ
    print("2. Загрузка документа...")
    result = upload_document(token, file_path)
    
    if result:
        # Получаем документы после загрузки
        print("3. Проверяем загруженные документы...")
        get_documents(token)
    
    print("\n✅ Загрузка завершена!")

if __name__ == "__main__":
    main()
