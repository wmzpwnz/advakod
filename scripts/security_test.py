#!/usr/bin/env python3
"""
Скрипт для тестирования безопасности системы ИИ-юрист
"""

import requests
import json
import time
from typing import Dict, List

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_secrets_exposure(self) -> Dict:
        """Тест на утечку секретов"""
        print("🔍 Тестирование утечки секретов...")
        
        # Проверяем доступность конфигурационных файлов
        config_files = [
            "/config.env",
            "/.env", 
            "/backend/config.env",
            "/backend/.env"
        ]
        
        results = []
        for file_path in config_files:
            try:
                response = self.session.get(f"{self.base_url}{file_path}")
                if response.status_code == 200:
                    content = response.text
                    if any(secret in content.lower() for secret in ['secret_key', 'password', 'api_key']):
                        results.append({
                            "file": file_path,
                            "status": "VULNERABLE",
                            "details": "Секреты найдены в открытом доступе"
                        })
            except:
                pass
                
        return {
            "test": "secrets_exposure",
            "results": results,
            "status": "FAIL" if results else "PASS"
        }
    
    def test_input_validation(self) -> Dict:
        """Тест валидации входных данных"""
        print("🔍 Тестирование валидации входных данных...")
        
        # Тестовые payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'; DROP TABLE users; --"
        ]
        
        results = []
        for payload in xss_payloads:
            try:
                # Тестируем чат API
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/message",
                    json={"message": payload, "session_id": 1},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    results.append({
                        "payload": payload,
                        "status": "VULNERABLE",
                        "details": "XSS payload принят без валидации"
                    })
            except Exception as e:
                results.append({
                    "payload": payload,
                    "status": "ERROR",
                    "details": str(e)
                })
                
        return {
            "test": "input_validation",
            "results": results,
            "status": "FAIL" if any(r["status"] == "VULNERABLE" for r in results) else "PASS"
        }
    
    def test_authentication_bypass(self) -> Dict:
        """Тест обхода аутентификации"""
        print("🔍 Тестирование обхода аутентификации...")
        
        # Попытка доступа к защищенным эндпоинтам без токена
        protected_endpoints = [
            "/api/v1/chat/sessions",
            "/api/v1/admin/dashboard",
            "/api/v1/users"
        ]
        
        results = []
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    results.append({
                        "endpoint": endpoint,
                        "status": "VULNERABLE",
                        "details": "Доступ без аутентификации"
                    })
                elif response.status_code == 401:
                    results.append({
                        "endpoint": endpoint,
                        "status": "SECURE",
                        "details": "Правильно требует аутентификацию"
                    })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "status": "ERROR",
                    "details": str(e)
                })
                
        return {
            "test": "authentication_bypass",
            "results": results,
            "status": "PASS" if all(r["status"] == "SECURE" for r in results) else "FAIL"
        }
    
    def test_rate_limiting(self) -> Dict:
        """Тест rate limiting"""
        print("🔍 Тестирование rate limiting...")
        
        # Отправляем много запросов подряд
        requests_count = 100
        success_count = 0
        rate_limited_count = 0
        
        for i in range(requests_count):
            try:
                response = self.session.get(f"{self.base_url}/api/v1/chat/sessions")
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    break
                time.sleep(0.1)  # Небольшая задержка
            except:
                pass
                
        return {
            "test": "rate_limiting",
            "results": {
                "total_requests": requests_count,
                "successful": success_count,
                "rate_limited": rate_limited_count
            },
            "status": "PASS" if rate_limited_count > 0 else "FAIL"
        }
    
    def test_sql_injection(self) -> Dict:
        """Тест SQL инъекций"""
        print("🔍 Тестирование SQL инъекций...")
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        results = []
        for payload in sql_payloads:
            try:
                # Тестируем в различных полях
                test_data = {
                    "username": payload,
                    "email": payload,
                    "message": payload
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    data=test_data
                )
                
                # Проверяем на признаки SQL ошибок
                if any(error in response.text.lower() for error in [
                    'sql', 'database', 'mysql', 'postgresql', 'syntax error'
                ]):
                    results.append({
                        "payload": payload,
                        "status": "VULNERABLE",
                        "details": "Возможная SQL инъекция"
                    })
                    
            except Exception as e:
                results.append({
                    "payload": payload,
                    "status": "ERROR",
                    "details": str(e)
                })
                
        return {
            "test": "sql_injection",
            "results": results,
            "status": "FAIL" if any(r["status"] == "VULNERABLE" for r in results) else "PASS"
        }
    
    def run_all_tests(self) -> Dict:
        """Запуск всех тестов безопасности"""
        print("🚀 Запуск тестов безопасности...")
        
        tests = [
            self.test_secrets_exposure,
            self.test_input_validation,
            self.test_authentication_bypass,
            self.test_rate_limiting,
            self.test_sql_injection
        ]
        
        results = {}
        for test in tests:
            try:
                result = test()
                results[result["test"]] = result
                print(f"✅ {result['test']}: {result['status']}")
            except Exception as e:
                print(f"❌ Ошибка в тесте: {e}")
                
        return results

if __name__ == "__main__":
    tester = SecurityTester()
    results = tester.run_all_tests()
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ БЕЗОПАСНОСТИ:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {result['status']}")
        
    # Сохраняем результаты
    with open("security_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 Результаты сохранены в security_test_results.json")
