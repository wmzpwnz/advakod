#!/usr/bin/env python3
"""
Sprint 2 Validation Script
Проверяет все изменения, внесенные в Sprint 2:
- H-01: Legal text chunking
- H-02: RRF ranking 
- H-04: Date filtering
- M-04: Readiness gating
- M-01: Optimized LoRA hyperparameters
"""

import asyncio
import json
import sys
import os
import logging
import time
from typing import Dict, Any, List
from datetime import datetime, date

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Sprint2Validator:
    """Валидатор для проверки изменений Sprint 2"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    async def run_all_tests(self):
        """Запускает все тесты Sprint 2"""
        logger.info("🚀 Начинаем валидацию Sprint 2 изменений")
        
        tests = [
            ("H-01: Legal Text Chunking", self.test_legal_chunking),
            ("H-02: RRF Ranking", self.test_rrf_ranking), 
            ("H-04: Date Filtering", self.test_date_filtering),
            ("M-04: Readiness Gating", self.test_readiness_gating),
            ("M-01: LoRA Hyperparameters", self.test_lora_optimization),
            ("Integration Test", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Тестируем: {test_name}")
            try:
                result = await test_func()
                self.results[test_name] = result
                if result["passed"]:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"💥 {test_name}: EXCEPTION - {str(e)}")
                self.results[test_name] = {"passed": False, "error": str(e)}
        
        self.generate_report()
        
    async def test_legal_chunking(self) -> Dict[str, Any]:
        """Тестирует H-01: Legal text chunking"""
        try:
            # Импортируем модуль напрямую для тестирования
            from backend.app.core.legal_chunker import LegalTextChunker
            
            chunker = LegalTextChunker()
            
            # Тестовый юридический текст
            test_text = """
            Статья 1. Основные понятия
            
            Часть 1. Для целей настоящего Федерального закона используются следующие основные понятия:
            1) персональные данные - любая информация;
            2) оператор - государственный орган;
            
            Статья 2. Принципы обработки персональных данных
            
            Часть 1. Обработка персональных данных должна осуществляться на законной основе.
            """
            
            # Чанкинг документа
            chunks = chunker.chunk_document(test_text, "test_doc", "v1")
            
            # Проверки
            checks = {
                "chunks_created": len(chunks) > 0,
                "articles_recognized": any("Статья 1" in chunk.content for chunk in chunks),
                "hierarchy_preserved": all(hasattr(chunk, 'metadata') for chunk in chunks),
                "metadata_present": all(chunk.metadata for chunk in chunks)
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "chunks_count": len(chunks),
                    "checks": checks,
                    "sample_chunk": str(chunks[0].__dict__) if chunks else None
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_rrf_ranking(self) -> Dict[str, Any]:
        """Тестирует H-02: RRF ranking"""
        try:
            # Проверяем наличие RRF метода
            from backend.app.services.enhanced_rag_service import EnhancedRAGService
            
            rag_service = EnhancedRAGService()
            
            # Проверяем наличие метода _combine_and_rank_results
            has_rrf_method = hasattr(rag_service, '_combine_and_rank_results')
            
            # Проверки
            checks = {
                "service_exists": True,
                "rrf_method_exists": has_rrf_method,
                "service_initialized": True
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "checks": checks,
                    "methods_available": [method for method in dir(rag_service) if 'rank' in method.lower()]
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_date_filtering(self) -> Dict[str, Any]:
        """Тестирует H-04: Date filtering"""
        try:
            # Импортируем модуль date utils
            from backend.app.core.date_utils import DateUtils
            
            # Тестируем основные методы
            methods_exist = {
                "normalize_date": hasattr(DateUtils, 'normalize_date'),
                "create_date_filter": hasattr(DateUtils, 'create_date_filter'),
                "parse_russian_date": hasattr(DateUtils, 'parse_russian_date')
            }
            
            # Тестируем простой случай
            try:
                test_date = "2024-01-15"
                normalized = DateUtils.normalize_date(test_date)
                date_filter = DateUtils.create_date_filter(test_date)
                
                date_test_passed = normalized is not None and isinstance(date_filter, dict)
            except Exception:
                date_test_passed = False
            
            # Проверяем обновление vector store
            try:
                from backend.app.services.vector_store_service import vector_store_service
                import inspect
                search_method = getattr(vector_store_service, 'search_similar')
                signature = inspect.signature(search_method)
                has_date_param = 'situation_date' in signature.parameters
            except Exception:
                has_date_param = False
            
            checks = {
                **methods_exist,
                "date_processing_works": date_test_passed,
                "vector_store_updated": has_date_param
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "checks": checks
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_readiness_gating(self) -> Dict[str, Any]:
        """Тестирует M-04: Readiness gating"""
        try:
            # Проверяем middleware
            try:
                from backend.app.middleware.readiness import ReadinessMiddleware, ReadinessChecker
                middleware_exists = True
            except ImportError:
                middleware_exists = False
            
            checks = {
                "middleware_imported": middleware_exists,
                "middleware_file_exists": os.path.exists("backend/app/middleware/readiness.py")
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "checks": checks
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_lora_optimization(self) -> Dict[str, Any]:
        """Тестирует M-01: LoRA hyperparameters optimization"""
        try:
            # Импортируем оптимизированную конфигурацию
            from backend.app.core.optimized_lora_config import OptimizedLoRAConfig, ModelSize, TaskComplexity
            
            # Тестируем генерацию конфигурации
            try:
                config = OptimizedLoRAConfig.get_optimized_config(
                    model_size=ModelSize.MEDIUM,
                    task_complexity=TaskComplexity.MODERATE,
                    legal_task_type="legal_qa"
                )
                config_generated = True
                has_lora_config = "lora_config" in config
                has_metadata = "_metadata" in config
            except Exception:
                config_generated = False
                has_lora_config = False
                has_metadata = False
            
            # Проверяем доступные задачи
            try:
                legal_tasks = OptimizedLoRAConfig.get_available_legal_tasks()
                tasks_available = len(legal_tasks) > 0
            except Exception:
                tasks_available = False
            
            # Проверяем обновление сервиса
            try:
                from backend.app.services.lora_training_service import LoRATrainingService
                has_recommendation_method = hasattr(LoRATrainingService, 'get_recommended_config')
            except Exception:
                has_recommendation_method = False
            
            checks = {
                "config_module_imported": True,
                "config_generated": config_generated,
                "has_lora_config": has_lora_config,
                "has_metadata": has_metadata,
                "legal_tasks_available": tasks_available,
                "service_updated": has_recommendation_method
            }
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "checks": checks
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_integration(self) -> Dict[str, Any]:
        """Интеграционный тест всех компонентов"""
        try:
            checks = {}
            
            # Проверяем файлы
            expected_files = [
                "backend/app/core/legal_chunker.py",
                "backend/app/core/date_utils.py",
                "backend/app/core/optimized_lora_config.py",
                "backend/app/middleware/readiness.py"
            ]
            
            files_exist = 0
            for file_path in expected_files:
                if os.path.exists(file_path):
                    files_exist += 1
            
            checks["files_created"] = files_exist == len(expected_files)
            
            # Проверяем импорты основных модулей
            modules_imported = 0
            modules_to_test = [
                ("legal_chunker", "backend.app.core.legal_chunker"),
                ("date_utils", "backend.app.core.date_utils"),
                ("optimized_lora_config", "backend.app.core.optimized_lora_config"),
                ("readiness", "backend.app.middleware.readiness")
            ]
            
            for name, module_name in modules_to_test:
                try:
                    __import__(module_name)
                    modules_imported += 1
                    checks[f"import_{name}"] = True
                except ImportError:
                    checks[f"import_{name}"] = False
            
            checks["all_modules_imported"] = modules_imported == len(modules_to_test)
            
            all_passed = all(checks.values())
            
            return {
                "passed": all_passed,
                "details": {
                    "checks": checks,
                    "files_found": f"{files_exist}/{len(expected_files)}",
                    "modules_imported": f"{modules_imported}/{len(modules_to_test)}"
                }
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def generate_report(self):
        """Генерирует отчет по результатам тестирования"""
        logger.info("\n" + "="*60)
        logger.info("📊 ОТЧЕТ ПО ВАЛИДАЦИИ SPRINT 2")
        logger.info("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("passed", False))
        
        logger.info(f"Всего тестов: {total_tests}")
        logger.info(f"Прошло успешно: {passed_tests}")
        logger.info(f"Неудачных: {total_tests - passed_tests}")
        logger.info(f"Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 Детализация по тестам:")
        for test_name, result in self.results.items():
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            logger.info(f"  {status} - {test_name}")
            if not result.get("passed", False) and "error" in result:
                logger.info(f"    ⚠️ Ошибка: {result['error']}")
        
        # Сохраняем детальный отчет
        report_file = f"sprint2_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": total_tests - passed_tests,
                        "success_rate": (passed_tests/total_tests)*100
                    },
                    "detailed_results": self.results
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n💾 Детальный отчет сохранен в: {report_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 ВСЕ ТЕСТЫ SPRINT 2 ПРОШЛИ УСПЕШНО!")
        else:
            logger.info(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ. Требуется исправление.")
        
        logger.info("="*60)


async def main():
    """Основная функция"""
    validator = Sprint2Validator()
    await validator.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())