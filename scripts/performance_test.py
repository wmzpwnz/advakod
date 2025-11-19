#!/usr/bin/env python3
"""
Скрипт для тестирования производительности системы ИИ-юрист
"""

import requests
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_single_request(self, endpoint: str, method: str = "GET", 
                          data: Dict = None, headers: Dict = None) -> Tuple[float, int]:
        """Тест одного запроса"""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(
                    f"{self.base_url}{endpoint}", 
                    json=data, 
                    headers=headers
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            end_time = time.time()
            response_time = end_time - start_time
            
            return response_time, response.status_code
            
        except Exception as e:
            end_time = time.time()
            return end_time - start_time, 0
    
    def test_latency(self, endpoint: str, method: str = "GET", 
                    data: Dict = None, headers: Dict = None, 
                    iterations: int = 100) -> Dict:
        """Тест латентности"""
        print(f"🔍 Тестирование латентности {endpoint}...")
        
        response_times = []
        status_codes = []
        
        for i in range(iterations):
            response_time, status_code = self.test_single_request(
                endpoint, method, data, headers
            )
            response_times.append(response_time)
            status_codes.append(status_code)
            
        # Статистика
        stats = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self.percentile(response_times, 95),
                "p99": self.percentile(response_times, 99)
            },
            "status_codes": {
                "200": status_codes.count(200),
                "other": len(status_codes) - status_codes.count(200)
            },
            "success_rate": status_codes.count(200) / len(status_codes) * 100
        }
        
        return stats
    
    def test_concurrent_requests(self, endpoint: str, method: str = "GET",
                               data: Dict = None, headers: Dict = None,
                               concurrent_users: int = 10, 
                               requests_per_user: int = 10) -> Dict:
        """Тест конкурентных запросов"""
        print(f"🔍 Тестирование конкурентности {endpoint} с {concurrent_users} пользователями...")
        
        def make_requests():
            results = []
            for _ in range(requests_per_user):
                response_time, status_code = self.test_single_request(
                    endpoint, method, data, headers
                )
                results.append((response_time, status_code))
            return results
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
            
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Анализ результатов
        response_times = [r[0] for r in all_results]
        status_codes = [r[1] for r in all_results]
        
        stats = {
            "endpoint": endpoint,
            "method": method,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(all_results),
            "total_time": total_time,
            "requests_per_second": len(all_results) / total_time,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self.percentile(response_times, 95),
                "p99": self.percentile(response_times, 99)
            },
            "status_codes": {
                "200": status_codes.count(200),
                "other": len(status_codes) - status_codes.count(200)
            },
            "success_rate": status_codes.count(200) / len(status_codes) * 100
        }
        
        return stats
    
    def test_memory_usage(self) -> Dict:
        """Тест использования памяти"""
        print("🔍 Тестирование использования памяти...")
        
        # Простой тест - отправляем большие запросы
        large_message = "Тестовое сообщение " * 1000  # ~20KB
        
        response_times = []
        for i in range(50):
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/message",
                    json={
                        "message": large_message,
                        "session_id": 1
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                end_time = time.time()
                response_times.append(end_time - start_time)
                
            except Exception as e:
                print(f"Ошибка в тесте памяти: {e}")
                
        return {
            "test": "memory_usage",
            "large_message_size": len(large_message),
            "iterations": len(response_times),
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": statistics.mean(response_times) if response_times else 0
            }
        }
    
    def test_database_performance(self) -> Dict:
        """Тест производительности БД"""
        print("🔍 Тестирование производительности БД...")
        
        # Тестируем различные операции с БД
        endpoints = [
            "/api/v1/chat/sessions",
            "/api/v1/auth/me",
            "/api/v1/admin/users"
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                stats = self.test_latency(endpoint, iterations=20)
                results[endpoint] = stats
            except Exception as e:
                results[endpoint] = {"error": str(e)}
                
        return {
            "test": "database_performance",
            "results": results
        }
    
    def test_ai_model_performance(self) -> Dict:
        """Тест производительности AI модели"""
        print("🔍 Тестирование производительности AI модели...")
        
        test_messages = [
            "Какие права у потребителя?",
            "Как оформить договор купли-продажи?",
            "Что такое трудовой договор?",
            "Как защитить интеллектуальную собственность?",
            "Какие документы нужны для регистрации ИП?"
        ]
        
        results = []
        for message in test_messages:
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/message",
                    json={
                        "message": message,
                        "session_id": 1
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        "message": message,
                        "response_time": response_time,
                        "response_length": len(data.get("message", "")),
                        "status": "success"
                    })
                else:
                    results.append({
                        "message": message,
                        "response_time": response_time,
                        "status": "error",
                        "status_code": response.status_code
                    })
                    
            except Exception as e:
                results.append({
                    "message": message,
                    "status": "error",
                    "error": str(e)
                })
        
        # Статистика
        successful_results = [r for r in results if r["status"] == "success"]
        response_times = [r["response_time"] for r in successful_results]
        
        return {
            "test": "ai_model_performance",
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "success_rate": len(successful_results) / len(results) * 100,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0
            },
            "results": results
        }
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Вычисление перцентиля"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def run_all_tests(self) -> Dict:
        """Запуск всех тестов производительности"""
        print("🚀 Запуск тестов производительности...")
        
        results = {}
        
        # Тест латентности основных эндпоинтов
        endpoints = [
            ("/api/v1/chat/sessions", "GET"),
            ("/api/v1/auth/me", "GET"),
            ("/health", "GET"),
            ("/ready", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                results[f"latency_{endpoint.replace('/', '_')}"] = self.test_latency(
                    endpoint, method, iterations=50
                )
            except Exception as e:
                results[f"latency_{endpoint.replace('/', '_')}"] = {"error": str(e)}
        
        # Тест конкурентности
        try:
            results["concurrent_chat"] = self.test_concurrent_requests(
                "/api/v1/chat/message",
                "POST",
                data={"message": "Тестовое сообщение", "session_id": 1},
                concurrent_users=5,
                requests_per_user=10
            )
        except Exception as e:
            results["concurrent_chat"] = {"error": str(e)}
        
        # Тест памяти
        try:
            results["memory_usage"] = self.test_memory_usage()
        except Exception as e:
            results["memory_usage"] = {"error": str(e)}
        
        # Тест БД
        try:
            results["database_performance"] = self.test_database_performance()
        except Exception as e:
            results["database_performance"] = {"error": str(e)}
        
        # Тест AI модели
        try:
            results["ai_model_performance"] = self.test_ai_model_performance()
        except Exception as e:
            results["ai_model_performance"] = {"error": str(e)}
        
        return results

if __name__ == "__main__":
    tester = PerformanceTester()
    results = tester.run_all_tests()
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("=" * 60)
    
    for test_name, result in results.items():
        if "error" in result:
            print(f"❌ {test_name}: ERROR - {result['error']}")
        else:
            print(f"✅ {test_name}: Успешно")
            
            # Выводим ключевые метрики
            if "response_times" in result:
                rt = result["response_times"]
                print(f"   📈 Среднее время ответа: {rt.get('mean', 0):.3f}s")
                print(f"   📈 P95: {rt.get('p95', 0):.3f}s")
                print(f"   📈 P99: {rt.get('p99', 0):.3f}s")
            
            if "requests_per_second" in result:
                print(f"   🚀 RPS: {result['requests_per_second']:.2f}")
            
            if "success_rate" in result:
                print(f"   ✅ Успешность: {result['success_rate']:.1f}%")
    
    # Сохраняем результаты
    with open("performance_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 Результаты сохранены в performance_test_results.json")
