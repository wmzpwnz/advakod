"""
ИИ-сервис для категоризации данных по сложности
"""
import logging
import re
from typing import Dict, List, Tuple, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.training_data import TrainingData, QualityEvaluation
from ..models.user import User

logger = logging.getLogger(__name__)


class AICategorizationService:
    """ИИ-сервис для категоризации и оценки данных"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Ключевые слова для определения сложности
        self.simple_keywords = [
            'что такое', 'как получить', 'где найти', 'сколько стоит',
            'какие права', 'какие обязанности', 'как оформить',
            'что нужно', 'какие документы', 'как подать'
        ]
        
        self.complex_keywords = [
            'сложный случай', 'спорная ситуация', 'противоречие',
            'конфликт интересов', 'неоднозначная трактовка',
            'альтернативные варианты', 'риски и последствия',
            'судебная практика', 'прецедент', 'исключение'
        ]
        
        # Юридические термины для оценки качества
        self.legal_terms = {
            'high_priority': [
                'статья', 'пункт', 'часть', 'глава', 'раздел',
                'федеральный закон', 'кодекс', 'постановление',
                'приказ', 'инструкция', 'положение'
            ],
            'medium_priority': [
                'закон', 'право', 'обязанность', 'ответственность',
                'договор', 'соглашение', 'сделка', 'согласие',
                'разрешение', 'лицензия', 'патент'
            ],
            'low_priority': [
                'суд', 'судья', 'заседание', 'слушание',
                'иск', 'жалоба', 'заявление', 'ходатайство',
                'апелляция', 'кассация', 'надзор'
            ]
        }
    
    def categorize_complexity_advanced(self, instruction: str, output: str) -> Dict[str, Any]:
        """
        Продвинутая категоризация по сложности
        
        Args:
            instruction: Вопрос пользователя
            output: Ответ ИИ
        
        Returns:
            Словарь с категорией и деталями анализа
        """
        try:
            analysis = {
                'complexity': 'medium',  # По умолчанию средняя
                'confidence': 0.0,
                'factors': [],
                'score': 0.0
            }
            
            # Анализ длины
            instruction_len = len(instruction)
            output_len = len(output)
            
            # Анализ ключевых слов
            simple_score = self._analyze_simple_keywords(instruction)
            complex_score = self._analyze_complex_keywords(instruction)
            
            # Анализ структуры вопроса
            question_structure = self._analyze_question_structure(instruction)
            
            # Анализ юридической сложности ответа
            legal_complexity = self._analyze_legal_complexity(output)
            
            # Анализ множественности вопросов
            multiple_questions = instruction.count('?') > 1
            
            # Анализ специальных символов и форматирования
            special_formatting = self._analyze_special_formatting(output)
            
            # Подсчет общего балла сложности
            total_score = 0
            
            # Факторы простоты (уменьшают сложность)
            if simple_score > 0:
                total_score -= simple_score * 2
                analysis['factors'].append(f"Простые ключевые слова: {simple_score}")
            
            if instruction_len < 100 and output_len < 1000:
                total_score -= 1
                analysis['factors'].append("Короткий и простой вопрос")
            
            if question_structure['is_direct']:
                total_score -= 1
                analysis['factors'].append("Прямой вопрос")
            
            # Факторы сложности (увеличивают сложность)
            if complex_score > 0:
                total_score += complex_score * 3
                analysis['factors'].append(f"Сложные ключевые слова: {complex_score}")
            
            if instruction_len > 300 or output_len > 2000:
                total_score += 2
                analysis['factors'].append("Длинный вопрос или ответ")
            
            if multiple_questions:
                total_score += 1
                analysis['factors'].append("Множественные вопросы")
            
            if legal_complexity['is_complex']:
                total_score += 2
                analysis['factors'].append("Сложная юридическая тематика")
            
            if special_formatting['has_lists'] or special_formatting['has_tables']:
                total_score += 1
                analysis['factors'].append("Структурированный ответ")
            
            # Определение категории
            if total_score <= -2:
                analysis['complexity'] = 'simple'
                analysis['confidence'] = 0.8
            elif total_score >= 3:
                analysis['complexity'] = 'complex'
                analysis['confidence'] = 0.8
            else:
                analysis['complexity'] = 'medium'
                analysis['confidence'] = 0.6
            
            analysis['score'] = total_score
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка категоризации: {e}")
            return {
                'complexity': 'medium',
                'confidence': 0.0,
                'factors': ['Ошибка анализа'],
                'score': 0.0
            }
    
    def evaluate_quality_advanced(self, instruction: str, output: str) -> Dict[str, Any]:
        """
        Продвинутая оценка качества данных
        
        Args:
            instruction: Вопрос пользователя
            output: Ответ ИИ
        
        Returns:
            Словарь с оценкой и деталями анализа
        """
        try:
            evaluation = {
                'score': 3.0,  # По умолчанию средняя оценка
                'confidence': 0.0,
                'criteria': {},
                'recommendations': []
            }
            
            # 1. Анализ длины ответа
            output_len = len(output)
            length_score = self._evaluate_length(output_len)
            evaluation['criteria']['length'] = length_score
            
            # 2. Анализ юридических терминов
            legal_score = self._evaluate_legal_terms(output)
            evaluation['criteria']['legal_terms'] = legal_score
            
            # 3. Анализ ссылок на законы
            references_score = self._evaluate_legal_references(output)
            evaluation['criteria']['references'] = references_score
            
            # 4. Анализ структуры ответа
            structure_score = self._evaluate_structure(output)
            evaluation['criteria']['structure'] = structure_score
            
            # 5. Анализ качества вопроса
            question_score = self._evaluate_question_quality(instruction)
            evaluation['criteria']['question'] = question_score
            
            # 6. Анализ уникальности
            uniqueness_score = self._evaluate_uniqueness(instruction, output)
            evaluation['criteria']['uniqueness'] = uniqueness_score
            
            # Подсчет общей оценки
            total_score = (
                length_score['score'] * 0.2 +
                legal_score['score'] * 0.25 +
                references_score['score'] * 0.2 +
                structure_score['score'] * 0.15 +
                question_score['score'] * 0.1 +
                uniqueness_score['score'] * 0.1
            )
            
            evaluation['score'] = round(min(5.0, max(1.0, total_score)), 2)
            evaluation['confidence'] = self._calculate_confidence(evaluation['criteria'])
            
            # Рекомендации
            if length_score['score'] < 3:
                evaluation['recommendations'].append("Ответ слишком короткий")
            if legal_score['score'] < 3:
                evaluation['recommendations'].append("Недостаточно юридических терминов")
            if references_score['score'] < 3:
                evaluation['recommendations'].append("Отсутствуют ссылки на законы")
            if structure_score['score'] < 3:
                evaluation['recommendations'].append("Плохая структура ответа")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Ошибка оценки качества: {e}")
            return {
                'score': 3.0,
                'confidence': 0.0,
                'criteria': {},
                'recommendations': ['Ошибка анализа']
            }
    
    def _analyze_simple_keywords(self, instruction: str) -> int:
        """Анализ простых ключевых слов"""
        instruction_lower = instruction.lower()
        return sum(1 for keyword in self.simple_keywords if keyword in instruction_lower)
    
    def _analyze_complex_keywords(self, instruction: str) -> int:
        """Анализ сложных ключевых слов"""
        instruction_lower = instruction.lower()
        return sum(1 for keyword in self.complex_keywords if keyword in instruction_lower)
    
    def _analyze_question_structure(self, instruction: str) -> Dict[str, Any]:
        """Анализ структуры вопроса"""
        return {
            'is_direct': instruction.strip().endswith('?'),
            'has_question_words': any(word in instruction.lower() for word in ['что', 'как', 'где', 'когда', 'почему', 'зачем']),
            'has_conditions': 'если' in instruction.lower() or 'при условии' in instruction.lower(),
            'word_count': len(instruction.split())
        }
    
    def _analyze_legal_complexity(self, output: str) -> Dict[str, Any]:
        """Анализ юридической сложности ответа"""
        output_lower = output.lower()
        
        # Подсчет юридических терминов
        high_priority_count = sum(1 for term in self.legal_terms['high_priority'] if term in output_lower)
        medium_priority_count = sum(1 for term in self.legal_terms['medium_priority'] if term in output_lower)
        low_priority_count = sum(1 for term in self.legal_terms['low_priority'] if term in output_lower)
        
        # Анализ сложности
        is_complex = (
            high_priority_count > 3 or
            'статья' in output_lower and 'пункт' in output_lower or
            'исключение' in output_lower or
            'альтернативно' in output_lower
        )
        
        return {
            'is_complex': is_complex,
            'high_priority_terms': high_priority_count,
            'medium_priority_terms': medium_priority_count,
            'low_priority_terms': low_priority_count,
            'total_legal_terms': high_priority_count + medium_priority_count + low_priority_count
        }
    
    def _analyze_special_formatting(self, output: str) -> Dict[str, Any]:
        """Анализ специального форматирования"""
        return {
            'has_lists': bool(re.search(r'^\s*[-*•]\s', output, re.MULTILINE)),
            'has_numbered_lists': bool(re.search(r'^\s*\d+\.\s', output, re.MULTILINE)),
            'has_tables': '|' in output and '\n' in output,
            'has_quotes': '"' in output or "'" in output,
            'has_bold': '**' in output or '__' in output
        }
    
    def _evaluate_length(self, output_len: int) -> Dict[str, Any]:
        """Оценка длины ответа"""
        if 50 <= output_len <= 1000:
            return {'score': 5.0, 'reason': 'Оптимальная длина'}
        elif 20 <= output_len <= 1500:
            return {'score': 4.0, 'reason': 'Хорошая длина'}
        elif 10 <= output_len <= 2000:
            return {'score': 3.0, 'reason': 'Приемлемая длина'}
        else:
            return {'score': 2.0, 'reason': 'Неоптимальная длина'}
    
    def _evaluate_legal_terms(self, output: str) -> Dict[str, Any]:
        """Оценка юридических терминов"""
        output_lower = output.lower()
        
        high_count = sum(1 for term in self.legal_terms['high_priority'] if term in output_lower)
        medium_count = sum(1 for term in self.legal_terms['medium_priority'] if term in output_lower)
        low_count = sum(1 for term in self.legal_terms['low_priority'] if term in output_lower)
        
        total_score = high_count * 2 + medium_count * 1.5 + low_count * 1
        
        if total_score >= 6:
            return {'score': 5.0, 'reason': 'Отличное использование юридических терминов'}
        elif total_score >= 4:
            return {'score': 4.0, 'reason': 'Хорошее использование юридических терминов'}
        elif total_score >= 2:
            return {'score': 3.0, 'reason': 'Умеренное использование юридических терминов'}
        else:
            return {'score': 2.0, 'reason': 'Недостаточно юридических терминов'}
    
    def _evaluate_legal_references(self, output: str) -> Dict[str, Any]:
        """Оценка ссылок на законы"""
        references = [
            'ст.', 'статья', 'ФЗ', 'ГК РФ', 'ТК РФ', 'УК РФ', 'КоАП РФ',
            'постановление', 'приказ', 'инструкция', 'положение'
        ]
        
        found_refs = sum(1 for ref in references if ref in output)
        
        if found_refs >= 3:
            return {'score': 5.0, 'reason': 'Множественные ссылки на законы'}
        elif found_refs >= 2:
            return {'score': 4.0, 'reason': 'Хорошие ссылки на законы'}
        elif found_refs >= 1:
            return {'score': 3.0, 'reason': 'Есть ссылки на законы'}
        else:
            return {'score': 2.0, 'reason': 'Отсутствуют ссылки на законы'}
    
    def _evaluate_structure(self, output: str) -> Dict[str, Any]:
        """Оценка структуры ответа"""
        has_paragraphs = '\n\n' in output
        has_lists = bool(re.search(r'^\s*[-*•]\s', output, re.MULTILINE))
        has_numbering = bool(re.search(r'^\s*\d+\.\s', output, re.MULTILINE))
        
        structure_score = 0
        if has_paragraphs:
            structure_score += 2
        if has_lists or has_numbering:
            structure_score += 2
        if len(output.split('.')) > 3:  # Множественные предложения
            structure_score += 1
        
        if structure_score >= 4:
            return {'score': 5.0, 'reason': 'Отличная структура'}
        elif structure_score >= 3:
            return {'score': 4.0, 'reason': 'Хорошая структура'}
        elif structure_score >= 2:
            return {'score': 3.0, 'reason': 'Удовлетворительная структура'}
        else:
            return {'score': 2.0, 'reason': 'Плохая структура'}
    
    def _evaluate_question_quality(self, instruction: str) -> Dict[str, Any]:
        """Оценка качества вопроса"""
        question_len = len(instruction)
        word_count = len(instruction.split())
        
        if 20 <= question_len <= 200 and word_count >= 5:
            return {'score': 5.0, 'reason': 'Отличный вопрос'}
        elif 10 <= question_len <= 300 and word_count >= 3:
            return {'score': 4.0, 'reason': 'Хороший вопрос'}
        elif 5 <= question_len <= 500:
            return {'score': 3.0, 'reason': 'Удовлетворительный вопрос'}
        else:
            return {'score': 2.0, 'reason': 'Плохой вопрос'}
    
    def _evaluate_uniqueness(self, instruction: str, output: str) -> Dict[str, Any]:
        """Оценка уникальности"""
        # Простая проверка на повторения
        instruction_words = set(instruction.lower().split())
        output_words = set(output.lower().split())
        
        # Проверка на избыточные повторения
        instruction_repeats = len(instruction_words) < len(instruction.split()) * 0.7
        output_repeats = len(output_words) < len(output.split()) * 0.7
        
        if not instruction_repeats and not output_repeats:
            return {'score': 5.0, 'reason': 'Высокая уникальность'}
        elif not instruction_repeats or not output_repeats:
            return {'score': 4.0, 'reason': 'Хорошая уникальность'}
        else:
            return {'score': 3.0, 'reason': 'Средняя уникальность'}
    
    def _calculate_confidence(self, criteria: Dict[str, Any]) -> float:
        """Расчет уверенности в оценке"""
        if not criteria:
            return 0.0
        
        # Простой расчет уверенности на основе количества критериев
        total_criteria = len(criteria)
        high_score_criteria = sum(1 for crit in criteria.values() if crit['score'] >= 4)
        
        return min(1.0, high_score_criteria / total_criteria + 0.3)
    
    def process_batch_categorization(self, data_ids: List[int]) -> Dict[str, Any]:
        """Пакетная обработка категоризации"""
        try:
            results = {
                'processed': 0,
                'simple': 0,
                'medium': 0,
                'complex': 0,
                'errors': 0
            }
            
            for data_id in data_ids:
                try:
                    training_data = self.db.query(TrainingData).filter(
                        TrainingData.id == data_id
                    ).first()
                    
                    if not training_data:
                        results['errors'] += 1
                        continue
                    
                    # Продвинутая категоризация
                    complexity_analysis = self.categorize_complexity_advanced(
                        training_data.instruction,
                        training_data.output
                    )
                    
                    # Продвинутая оценка качества
                    quality_analysis = self.evaluate_quality_advanced(
                        training_data.instruction,
                        training_data.output
                    )
                    
                    # Обновление данных
                    training_data.complexity = complexity_analysis['complexity']
                    training_data.quality_score = quality_analysis['score']
                    
                    # Сохранение детального анализа в метаданные
                    training_data.metadata = training_data.metadata or {}
                    training_data.metadata['complexity_analysis'] = complexity_analysis
                    training_data.metadata['quality_analysis'] = quality_analysis
                    training_data.metadata['processed_at'] = datetime.utcnow().isoformat()
                    
                    results[complexity_analysis['complexity']] += 1
                    results['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки данных {data_id}: {e}")
                    results['errors'] += 1
            
            self.db.commit()
            
            logger.info(f"Пакетная обработка завершена: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка пакетной обработки: {e}")
            self.db.rollback()
            return {'error': str(e)}
