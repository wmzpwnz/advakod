#!/usr/bin/env python3
"""
Скрипт для тестирования качества RAG системы на golden dataset
"""

import requests
import json
import time
from typing import Dict, List, Tuple
import re

class GoldenRetrievalTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Golden dataset для тестирования
        self.golden_questions = [
            {
                "question": "Какие условия в ст. 432 ГК РФ?",
                "expected_article": "432",
                "expected_law": "ГК РФ",
                "expected_content": ["условия", "договор", "соглашение"]
            },
            {
                "question": "Какие права у потребителя при покупке товара?",
                "expected_law": "ЗоЗПП",
                "expected_content": ["потребитель", "права", "товар", "возврат", "обмен"]
            },
            {
                "question": "Как оформить трудовой договор?",
                "expected_law": "ТК РФ",
                "expected_content": ["трудовой договор", "оформление", "работник", "работодатель"]
            },
            {
                "question": "Что такое интеллектуальная собственность?",
                "expected_law": "ГК РФ",
                "expected_content": ["интеллектуальная собственность", "авторские права", "патент"]
            },
            {
                "question": "Какие документы нужны для регистрации ИП?",
                "expected_content": ["ИП", "регистрация", "документы", "заявление"]
            }
        ]
    
    def test_retrieval_quality(self, question: Dict) -> Dict:
        """Тест качества поиска для одного вопроса"""
        print(f"🔍 Тестирование: {question['question']}")
        
        start_time = time.time()
        
        try:
            # Отправляем запрос в RAG систему
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json={
                    "message": question["question"],
                    "session_id": 1
                },
                headers={"Content-Type": "application/json"}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code != 200:
                return {
                    "question": question["question"],
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response_time
                }
            
            data = response.json()
            answer = data.get("message", "")
            sources = data.get("sources", [])
            
            # Анализируем качество ответа
            quality_metrics = self.analyze_answer_quality(question, answer, sources)
            
            return {
                "question": question["question"],
                "status": "success",
                "response_time": response_time,
                "answer_length": len(answer),
                "sources_count": len(sources),
                "quality_metrics": quality_metrics,
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            return {
                "question": question["question"],
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def analyze_answer_quality(self, question: Dict, answer: str, sources: List[Dict]) -> Dict:
        """Анализ качества ответа"""
        metrics = {}
        
        # 1. Проверка наличия ожидаемых статей/законов
        if "expected_article" in question:
            article_found = question["expected_article"] in answer
            metrics["expected_article_found"] = article_found
        
        if "expected_law" in question:
            law_found = question["expected_law"] in answer
            metrics["expected_law_found"] = law_found
        
        # 2. Проверка наличия ключевых слов
        expected_content = question.get("expected_content", [])
        content_matches = 0
        for keyword in expected_content:
            if keyword.lower() in answer.lower():
                content_matches += 1
        
        metrics["content_match_rate"] = content_matches / len(expected_content) if expected_content else 0
        
        # 3. Проверка источников
        if sources:
            metrics["has_sources"] = True
            metrics["source_quality"] = self.analyze_source_quality(sources, question)
        else:
            metrics["has_sources"] = False
            metrics["source_quality"] = 0
        
        # 4. Проверка на галлюцинации (простая эвристика)
        hallucination_indicators = [
            "я не знаю", "не могу ответить", "нет информации",
            "данные отсутствуют", "не найдено"
        ]
        
        has_hallucination_indicators = any(
            indicator in answer.lower() for indicator in hallucination_indicators
        )
        metrics["potential_hallucination"] = has_hallucination_indicators
        
        # 5. Длина ответа (слишком короткие ответы могут быть неполными)
        metrics["answer_length_adequate"] = len(answer) > 100
        
        # 6. Наличие юридических терминов
        legal_terms = [
            "статья", "пункт", "часть", "закон", "кодекс", "право", "обязанность",
            "договор", "соглашение", "сделка", "ответственность"
        ]
        
        legal_terms_found = sum(1 for term in legal_terms if term in answer.lower())
        metrics["legal_terms_count"] = legal_terms_found
        metrics["legal_terms_adequate"] = legal_terms_found >= 3
        
        return metrics
    
    def analyze_source_quality(self, sources: List[Dict], question: Dict) -> float:
        """Анализ качества источников"""
        if not sources:
            return 0.0
        
        quality_score = 0.0
        
        for source in sources:
            source_score = 0.0
            
            # Проверяем релевантность по сходству
            similarity = source.get("similarity", 0.0)
            if similarity > 0.7:
                source_score += 0.4
            elif similarity > 0.5:
                source_score += 0.2
            
            # Проверяем наличие метаданных
            metadata = source.get("metadata", {})
            if metadata:
                source_score += 0.2
                
                # Проверяем наличие статьи/закона
                if "article" in metadata or "law" in metadata:
                    source_score += 0.2
                
                # Проверяем соответствие ожидаемому закону
                if "expected_law" in question:
                    if question["expected_law"] in str(metadata):
                        source_score += 0.2
            
            # Проверяем длину контента
            content = source.get("content", "")
            if len(content) > 100:
                source_score += 0.1
            
            quality_score += source_score
        
        return min(quality_score / len(sources), 1.0)
    
    def test_hit_at_k(self, k_values: List[int] = [1, 3, 5, 10]) -> Dict:
        """Тест Hit@K для различных значений K"""
        print("🔍 Тестирование Hit@K...")
        
        results = {}
        
        for k in k_values:
            hit_count = 0
            total_questions = len(self.golden_questions)
            
            for question in self.golden_questions:
                test_result = self.test_retrieval_quality(question)
                
                if test_result["status"] == "success":
                    sources = test_result.get("sources", [])
                    
                    # Проверяем, есть ли релевантные источники в топ-K
                    relevant_sources = 0
                    for source in sources[:k]:
                        similarity = source.get("similarity", 0.0)
                        if similarity > 0.5:  # Порог релевантности
                            relevant_sources += 1
                    
                    if relevant_sources > 0:
                        hit_count += 1
            
            hit_at_k = hit_count / total_questions
            results[f"hit_at_{k}"] = hit_at_k
            
            print(f"   Hit@{k}: {hit_at_k:.3f} ({hit_count}/{total_questions})")
        
        return results
    
    def test_citation_accuracy(self) -> Dict:
        """Тест точности цитирования"""
        print("🔍 Тестирование точности цитирования...")
        
        citation_results = []
        
        for question in self.golden_questions:
            test_result = self.test_retrieval_quality(question)
            
            if test_result["status"] == "success":
                sources = test_result.get("sources", [])
                answer = test_result.get("answer", "")
                
                # Проверяем, есть ли в ответе ссылки на источники
                has_citations = False
                for source in sources:
                    source_title = source.get("title", "")
                    if source_title and source_title in answer:
                        has_citations = True
                        break
                
                citation_results.append({
                    "question": question["question"],
                    "has_citations": has_citations,
                    "sources_count": len(sources)
                })
        
        total_questions = len(citation_results)
        questions_with_citations = sum(1 for r in citation_results if r["has_citations"])
        
        citation_accuracy = questions_with_citations / total_questions if total_questions > 0 else 0
        
        return {
            "citation_accuracy": citation_accuracy,
            "total_questions": total_questions,
            "questions_with_citations": questions_with_citations,
            "detailed_results": citation_results
        }
    
    def test_hallucination_rate(self) -> Dict:
        """Тест частоты галлюцинаций"""
        print("🔍 Тестирование частоты галлюцинаций...")
        
        hallucination_results = []
        
        for question in self.golden_questions:
            test_result = self.test_retrieval_quality(question)
            
            if test_result["status"] == "success":
                answer = test_result.get("answer", "")
                sources = test_result.get("sources", [])
                
                # Простая эвристика для определения галлюцинаций
                is_hallucination = False
                
                # Если нет источников, но есть длинный ответ
                if not sources and len(answer) > 200:
                    is_hallucination = True
                
                # Если есть противоречивые утверждения
                contradiction_indicators = [
                    "с одной стороны", "с другой стороны",
                    "однако", "но", "хотя"
                ]
                
                if any(indicator in answer.lower() for indicator in contradiction_indicators):
                    is_hallucination = True
                
                # Если есть слишком общие утверждения без конкретики
                vague_indicators = [
                    "в общем", "как правило", "обычно",
                    "в большинстве случаев"
                ]
                
                if any(indicator in answer.lower() for indicator in vague_indicators):
                    is_hallucination = True
                
                hallucination_results.append({
                    "question": question["question"],
                    "is_hallucination": is_hallucination,
                    "answer_length": len(answer),
                    "sources_count": len(sources)
                })
        
        total_questions = len(hallucination_results)
        hallucinations = sum(1 for r in hallucination_results if r["is_hallucination"])
        
        hallucination_rate = hallucinations / total_questions if total_questions > 0 else 0
        
        return {
            "hallucination_rate": hallucination_rate,
            "total_questions": total_questions,
            "hallucinations": hallucinations,
            "detailed_results": hallucination_results
        }
    
    def run_all_tests(self) -> Dict:
        """Запуск всех тестов качества RAG"""
        print("🚀 Запуск тестов качества RAG системы...")
        
        results = {}
        
        # Тест Hit@K
        try:
            results["hit_at_k"] = self.test_hit_at_k()
        except Exception as e:
            results["hit_at_k"] = {"error": str(e)}
        
        # Тест точности цитирования
        try:
            results["citation_accuracy"] = self.test_citation_accuracy()
        except Exception as e:
            results["citation_accuracy"] = {"error": str(e)}
        
        # Тест частоты галлюцинаций
        try:
            results["hallucination_rate"] = self.test_hallucination_rate()
        except Exception as e:
            results["hallucination_rate"] = {"error": str(e)}
        
        # Детальные результаты для каждого вопроса
        detailed_results = []
        for question in self.golden_questions:
            try:
                result = self.test_retrieval_quality(question)
                detailed_results.append(result)
            except Exception as e:
                detailed_results.append({
                    "question": question["question"],
                    "status": "error",
                    "error": str(e)
                })
        
        results["detailed_results"] = detailed_results
        
        return results

if __name__ == "__main__":
    tester = GoldenRetrievalTester()
    results = tester.run_all_tests()
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ КАЧЕСТВА RAG:")
    print("=" * 50)
    
    # Hit@K результаты
    if "hit_at_k" in results and "error" not in results["hit_at_k"]:
        print("🎯 Hit@K результаты:")
        for metric, value in results["hit_at_k"].items():
            print(f"   {metric}: {value:.3f}")
    
    # Точность цитирования
    if "citation_accuracy" in results and "error" not in results["citation_accuracy"]:
        ca = results["citation_accuracy"]
        print(f"📚 Точность цитирования: {ca['citation_accuracy']:.3f}")
        print(f"   Вопросов с цитатами: {ca['questions_with_citations']}/{ca['total_questions']}")
    
    # Частота галлюцинаций
    if "hallucination_rate" in results and "error" not in results["hallucination_rate"]:
        hr = results["hallucination_rate"]
        print(f"🤖 Частота галлюцинаций: {hr['hallucination_rate']:.3f}")
        print(f"   Галлюцинаций: {hr['hallucinations']}/{hr['total_questions']}")
    
    # Сохраняем результаты
    with open("golden_retrieval_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 Результаты сохранены в golden_retrieval_test_results.json")
