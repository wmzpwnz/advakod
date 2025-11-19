#!/usr/bin/env python3
"""Проверка статуса загруженных кодексов"""
import sys
import os
sys.path.insert(0, '/app')

from pathlib import Path
import json

# Маппинг eo_number -> название кодекса
CODEX_MAP = {
    '0001201410140002': 'Гражданский кодекс РФ (часть 1)',
    '0001201412140001': 'Трудовой кодекс РФ',
    '0001201412140002': 'Семейный кодекс РФ',
    '0001201412140003': 'Жилищный кодекс РФ',
    '0001201412140004': 'Налоговый кодекс РФ (часть 1)',
    '0001201412140005': 'Бюджетный кодекс РФ',
    '0001201412140006': 'Кодекс об административных правонарушениях РФ',
    '0001202203030006': 'Уголовный кодекс РФ'
}

def check_codexes_status():
    """Проверяет статус загруженных кодексов"""
    codes_dir = Path("/app/data/codes_downloads")
    
    print("="*70)
    print("📊 СТАТУС ЗАГРУЖЕННЫХ КОДЕКСОВ В СИСТЕМЕ")
    print("="*70)
    
    if not codes_dir.exists():
        print("❌ Директория с кодексами не найдена")
        return
    
    txt_files = list(codes_dir.glob("*.txt"))
    
    if not txt_files:
        print("✅ Кодексы не загружены")
        return
    
    print(f"\n📁 Найдено файлов: {len(txt_files)}")
    print("\n" + "-"*70)
    
    stubs = []
    full_codexes = []
    
    for file_path in sorted(txt_files):
        eo_number = file_path.stem
        size = file_path.stat().st_size
        codex_name = CODEX_MAP.get(eo_number, f'Неизвестный кодекс ({eo_number})')
        
        # Читаем первые строки
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                first_line = lines[0][:80] if lines else ""
        except:
            first_line = "Ошибка чтения"
        
        is_stub = size <= 2000
        
        if is_stub:
            stubs.append({
                'name': codex_name,
                'eo_number': eo_number,
                'size': size,
                'file': file_path.name
            })
            status = "❌ ЗАГЛУШКА"
        else:
            full_codexes.append({
                'name': codex_name,
                'eo_number': eo_number,
                'size': size,
                'file': file_path.name
            })
            status = "✅ ПОЛНЫЙ"
        
        size_kb = size / 1024
        size_mb = size / 1024 / 1024
        
        print(f"\n{status} {codex_name}")
        print(f"   📄 Файл: {file_path.name}")
        print(f"   📊 Размер: {size:,} bytes ({size_kb:.2f} KB / {size_mb:.2f} MB)")
        print(f"   🔑 eo_number: {eo_number}")
        print(f"   📝 Превью: {first_line}...")
    
    # Проверяем ChromaDB
    print("\n" + "="*70)
    print("📚 СТАТУС В RAG СИСТЕМЕ (ChromaDB)")
    print("="*70)
    
    try:
        from app.services.vector_store_service import vector_store_service
        vector_store_service.initialize()
        collection = vector_store_service.collection
        count = collection.count()
        print(f"📊 Всего документов в ChromaDB: {count}")
        
        if count == 0:
            print("⚠️ Кодексы НЕ загружены в RAG систему")
        else:
            print("✅ Кодексы загружены в RAG систему")
    except Exception as e:
        print(f"❌ Ошибка проверки ChromaDB: {e}")
    
    # Итоговая статистика
    print("\n" + "="*70)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("="*70)
    print(f"✅ Полных кодексов: {len(full_codexes)}")
    print(f"❌ Заглушек: {len(stubs)}")
    print(f"📁 Всего файлов: {len(txt_files)}")
    
    if stubs:
        print("\n⚠️ ВНИМАНИЕ: Обнаружены заглушки, которые нужно удалить!")
        print("   Запустите скрипт cleanup_old_codexes.py для очистки")
    
    if not full_codexes:
        print("\n💡 РЕКОМЕНДАЦИЯ: Загрузите полные кодексы через гибридный загрузчик")
        print("   Используйте кнопку 'Загрузить кодексы РФ' в админке")

if __name__ == "__main__":
    check_codexes_status()

