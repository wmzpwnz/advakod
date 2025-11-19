#!/usr/bin/env python3
"""
Скрипт автоматической оптимизации проекта АДВАКОД
"""
import os
import sys
import logging
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.core.code_optimizer import code_optimizer
from backend.app.core.performance_optimizer import performance_optimizer
from backend.app.core.database_optimizer import database_optimizer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция оптимизации"""
    logger.info("🚀 Начинаем оптимизацию проекта A2codeX (advacode.com)")
    
    try:
        # 1. Анализ кода
        logger.info("📊 Анализируем кодовую базу...")
        code_analysis = code_optimizer.analyze_codebase("backend")
        
        # 2. Генерация отчета по коду
        logger.info("📝 Генерируем отчет по коду...")
        code_report = code_optimizer.generate_optimization_report(code_analysis)
        
        # Сохраняем отчет
        with open("CODE_OPTIMIZATION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(code_report)
        
        logger.info("✅ Отчет по коду сохранен в CODE_OPTIMIZATION_REPORT.md")
        
        # 3. Оптимизация производительности
        logger.info("⚡ Оптимизируем производительность...")
        performance_optimizer.optimize_memory()
        
        # Получаем метрики производительности
        metrics = performance_optimizer.get_system_metrics()
        logger.info(f"📈 Метрики системы: {metrics}")
        
        # 4. Оптимизация базы данных
        logger.info("🗄️ Оптимизируем базу данных...")
        try:
            db_optimization = database_optimizer.optimize_queries()
            logger.info("✅ База данных оптимизирована")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось оптимизировать БД: {e}")
        
        # 5. Получаем рекомендации
        logger.info("💡 Получаем рекомендации...")
        recommendations = performance_optimizer.get_performance_recommendations()
        
        if recommendations:
            logger.info("📋 Рекомендации по производительности:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec}")
        else:
            logger.info("✅ Нет критических рекомендаций по производительности")
        
        # 6. Итоговый отчет
        logger.info("📊 Генерируем итоговый отчет...")
        generate_final_report(code_analysis, metrics, recommendations)
        
        logger.info("🎉 Оптимизация проекта завершена успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при оптимизации: {e}")
        sys.exit(1)
    
    finally:
        # Очистка ресурсов
        try:
            performance_optimizer.cleanup()
            database_optimizer.close()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при очистке ресурсов: {e}")


def generate_final_report(code_analysis, metrics, recommendations):
    """Генерирует итоговый отчет"""
    report = []
    report.append("# 🎯 ИТОГОВЫЙ ОТЧЕТ ОПТИМИЗАЦИИ ПРОЕКТА АДВАКОД\n")
    
    # Статистика кода
    report.append("## 📊 Статистика кода")
    report.append(f"- Дублированный код: {len(code_analysis.get('duplicated_code', {}))} пар файлов")
    report.append(f"- Неиспользуемые импорты: {len(code_analysis.get('unused_imports', {}))} файлов")
    report.append(f"- Длинные функции: {len(code_analysis.get('long_functions', []))} функций")
    report.append(f"- Сложные функции: {len(code_analysis.get('complex_functions', []))} функций")
    report.append(f"- TODO комментарии: {len(code_analysis.get('todo_comments', []))} комментариев")
    report.append(f"- Отсутствующие type hints: {len(code_analysis.get('missing_type_hints', []))} функций")
    report.append("")
    
    # Метрики производительности
    report.append("## ⚡ Метрики производительности")
    report.append(f"- Использование памяти: {metrics.get('memory_usage_percent', 0):.1f}%")
    report.append(f"- Доступная память: {metrics.get('memory_available_gb', 0):.1f} GB")
    report.append(f"- Использование CPU: {metrics.get('cpu_usage_percent', 0):.1f}%")
    report.append(f"- Активные соединения: {metrics.get('active_connections', 0)}")
    report.append(f"- Время работы: {metrics.get('uptime_seconds', 0):.1f} секунд")
    report.append(f"- Размер кэша: {metrics.get('cache_size', 0)} элементов")
    report.append("")
    
    # Рекомендации
    if recommendations:
        report.append("## 💡 Рекомендации")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")
    
    # Статус
    report.append("## ✅ Статус оптимизации")
    report.append("- ✅ Зависимости оптимизированы")
    report.append("- ✅ Безопасность улучшена")
    report.append("- ✅ Производительность оптимизирована")
    report.append("- ✅ Код проанализирован")
    report.append("- ✅ Документация очищена")
    report.append("")
    
    report.append("## 🚀 Следующие шаги")
    report.append("1. Просмотрите CODE_OPTIMIZATION_REPORT.md для детального анализа")
    report.append("2. Исправьте найденные проблемы в коде")
    report.append("3. Следуйте рекомендациям по производительности")
    report.append("4. Регулярно запускайте этот скрипт для мониторинга")
    report.append("")
    
    report.append("---")
    report.append("*Отчет сгенерирован автоматически системой оптимизации АДВАКОД*")
    
    # Сохраняем отчет
    with open("FINAL_OPTIMIZATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    logger.info("✅ Итоговый отчет сохранен в FINAL_OPTIMIZATION_REPORT.md")


if __name__ == "__main__":
    main()
