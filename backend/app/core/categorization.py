import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

logger = logging.getLogger(__name__)

@dataclass
class CategoryResult:
    """Результат категоризации"""
    text: str
    category: str
    confidence: float
    subcategory: Optional[str]
    keywords: List[str]
    reasoning: str
    timestamp: datetime

@dataclass
class CategoryDefinition:
    """Определение категории"""
    name: str
    display_name: str
    description: str
    keywords: List[str]
    patterns: List[str]
    subcategories: Dict[str, List[str]]
    priority: int

class LegalQuestionCategorizer:
    """Классификатор юридических вопросов"""
    
    def __init__(self):
        self.categories = self._initialize_categories()
        self.stop_words = {
            "как", "что", "где", "когда", "почему", "зачем", "кто", "чей", "какой",
            "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то",
            "все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за"
        }
    
    def _initialize_categories(self) -> Dict[str, CategoryDefinition]:
        """Инициализация категорий"""
        return {
            "трудовое_право": CategoryDefinition(
                name="трудовое_право",
                display_name="Трудовое право",
                description="Вопросы трудовых отношений, договоров, прав работников",
                keywords=[
                    "трудовой договор", "работа", "зарплата", "отпуск", "увольнение",
                    "рабочее время", "трудовые споры", "охрана труда", "работник",
                    "работодатель", "трудовая книжка", "больничный", "декрет",
                    "сверхурочные", "командировка", "стаж", "пенсия", "трудовые права"
                ],
                patterns=[
                    r"трудовой\s+договор",
                    r"рабочее\s+время",
                    r"увольнение",
                    r"зарплата",
                    r"отпуск",
                    r"трудовые\s+споры"
                ],
                subcategories={
                    "трудовой_договор": ["договор", "контракт", "соглашение", "прием на работу"],
                    "зарплата": ["зарплата", "оплата", "выплаты", "премия", "надбавка"],
                    "увольнение": ["увольнение", "уволить", "расторжение", "уход с работы"],
                    "отпуск": ["отпуск", "каникулы", "отдых", "больничный", "декрет"],
                    "трудовые_споры": ["спор", "конфликт", "жалоба", "суд", "комиссия"]
                },
                priority=1
            ),
            
            "гражданское_право": CategoryDefinition(
                name="гражданское_право",
                display_name="Гражданское право",
                description="Гражданские правоотношения, договоры, сделки, собственность",
                keywords=[
                    "договор", "сделка", "обязательства", "наследование", "собственность",
                    "защита прав", "возмещение ущерба", "долг", "кредит", "займ",
                    "купля-продажа", "аренда", "дарение", "завещание", "наследство",
                    "гражданские права", "дееспособность", "правоспособность"
                ],
                patterns=[
                    r"гражданский\s+договор",
                    r"сделка",
                    r"обязательства",
                    r"наследование",
                    r"собственность"
                ],
                subcategories={
                    "договоры": ["договор", "соглашение", "контракт", "сделка"],
                    "собственность": ["собственность", "имущество", "недвижимость", "движимое"],
                    "наследование": ["наследование", "завещание", "наследство", "наследники"],
                    "обязательства": ["долг", "кредит", "займ", "обязательства", "возврат"]
                },
                priority=2
            ),
            
            "налоговое_право": CategoryDefinition(
                name="налоговое_право",
                display_name="Налоговое право",
                description="Налогообложение, налоговые льготы, отчетность",
                keywords=[
                    "налог", "налогообложение", "ндс", "подоходный налог", "налоговые льготы",
                    "налоговая отчетность", "штрафы", "налоговая инспекция", "декларация",
                    "налоговый кодекс", "налоговые вычеты", "налоговая база", "ставка налога"
                ],
                patterns=[
                    r"налог",
                    r"налогообложение",
                    r"ндс",
                    r"налоговая\s+отчетность",
                    r"налоговые\s+льготы"
                ],
                subcategories={
                    "подоходный_налог": ["ндфл", "подоходный", "13%", "налог с доходов"],
                    "ндс": ["ндс", "налог на добавленную стоимость", "20%", "10%"],
                    "отчетность": ["декларация", "отчет", "налоговая отчетность", "сроки"],
                    "льготы": ["льготы", "вычеты", "освобождение", "налоговые льготы"]
                },
                priority=3
            ),
            
            "корпоративное_право": CategoryDefinition(
                name="корпоративное_право",
                display_name="Корпоративное право",
                description="Корпоративное право, ООО, АО, управление компаниями",
                keywords=[
                    "ооо", "акционерное общество", "устав", "директор", "акции",
                    "дивиденды", "реорганизация", "ликвидация", "учредители", "управление",
                    "корпоративное управление", "собрание", "решение", "протокол"
                ],
                patterns=[
                    r"ооо",
                    r"акционерное\s+общество",
                    r"корпоративное\s+управление",
                    r"устав",
                    r"директор"
                ],
                subcategories={
                    "создание": ["создание", "регистрация", "учредители", "уставной капитал"],
                    "управление": ["директор", "собрание", "решение", "протокол"],
                    "реорганизация": ["реорганизация", "слияние", "присоединение", "разделение"],
                    "ликвидация": ["ликвидация", "банкротство", "прекращение деятельности"]
                },
                priority=4
            ),
            
            "семейное_право": CategoryDefinition(
                name="семейное_право",
                display_name="Семейное право",
                description="Семейные отношения, брак, развод, алименты",
                keywords=[
                    "брак", "развод", "алименты", "опека", "усыновление", "раздел имущества",
                    "брачный договор", "семейные отношения", "дети", "родители", "супруги"
                ],
                patterns=[
                    r"брак",
                    r"развод",
                    r"алименты",
                    r"семейные\s+отношения",
                    r"брачный\s+договор"
                ],
                subcategories={
                    "брак": ["брак", "регистрация", "свадьба", "супруги"],
                    "развод": ["развод", "расторжение брака", "раздельное проживание"],
                    "алименты": ["алименты", "содержание", "выплаты на детей"],
                    "имущество": ["раздел имущества", "брачный договор", "совместная собственность"]
                },
                priority=5
            ),
            
            "жилищное_право": CategoryDefinition(
                name="жилищное_право",
                display_name="Жилищное право",
                description="Жилищные вопросы, недвижимость, аренда",
                keywords=[
                    "квартира", "дом", "недвижимость", "прописка", "аренда", "ипотека",
                    "приватизация", "выселение", "жилищные права", "коммунальные услуги",
                    "управляющая компания", "тсж", "жилищный кодекс"
                ],
                patterns=[
                    r"жилищные\s+права",
                    r"недвижимость",
                    r"аренда",
                    r"ипотека",
                    r"приватизация"
                ],
                subcategories={
                    "собственность": ["собственность", "приватизация", "купля-продажа"],
                    "аренда": ["аренда", "найм", "договор аренды", "арендная плата"],
                    "ипотека": ["ипотека", "кредит", "залог", "банк"],
                    "коммунальные_услуги": ["коммунальные услуги", "управляющая компания", "тсж"]
                },
                priority=6
            ),
            
            "уголовное_право": CategoryDefinition(
                name="уголовное_право",
                display_name="Уголовное право",
                description="Уголовное право, преступления, наказания",
                keywords=[
                    "преступление", "наказание", "суд", "следствие", "адвокат", "прокурор",
                    "приговор", "апелляция", "уголовный кодекс", "уголовная ответственность",
                    "следствие", "дознание", "обвинение", "защита"
                ],
                patterns=[
                    r"уголовное\s+право",
                    r"преступление",
                    r"уголовная\s+ответственность",
                    r"следствие",
                    r"суд"
                ],
                subcategories={
                    "преступления": ["преступление", "состав преступления", "вина"],
                    "наказания": ["наказание", "приговор", "лишение свободы", "штраф"],
                    "процесс": ["следствие", "суд", "адвокат", "прокурор"],
                    "защита": ["защита", "адвокат", "права обвиняемого"]
                },
                priority=7
            ),
            
            "административное_право": CategoryDefinition(
                name="административное_право",
                display_name="Административное право",
                description="Административные правонарушения, штрафы, лицензии",
                keywords=[
                    "административные правонарушения", "штрафы", "лицензии", "разрешения",
                    "государственные услуги", "жалобы", "административный кодекс",
                    "административная ответственность", "постановление", "обжалование"
                ],
                patterns=[
                    r"административные\s+правонарушения",
                    r"штрафы",
                    r"лицензии",
                    r"государственные\s+услуги",
                    r"жалобы"
                ],
                subcategories={
                    "правонарушения": ["правонарушения", "штрафы", "постановление"],
                    "лицензии": ["лицензии", "разрешения", "государственные услуги"],
                    "жалобы": ["жалобы", "обжалование", "апелляция"],
                    "ответственность": ["административная ответственность", "наказание"]
                },
                priority=8
            )
        }
    
    def categorize_question(self, text: str) -> CategoryResult:
        """Категоризация вопроса"""
        try:
            # Предобработка текста
            processed_text = self._preprocess_text(text)
            
            # Анализ по категориям
            category_scores = self._analyze_categories(processed_text)
            
            # Выбор лучшей категории
            best_category = max(category_scores.items(), key=lambda x: x[1])
            
            # Определение подкатегории
            subcategory = self._determine_subcategory(
                processed_text, 
                best_category[0], 
                best_category[1]
            )
            
            # Извлечение ключевых слов
            keywords = self._extract_keywords(processed_text, best_category[0])
            
            # Генерация объяснения
            reasoning = self._generate_reasoning(
                processed_text, 
                best_category[0], 
                keywords
            )
            
            return CategoryResult(
                text=text,
                category=best_category[0],
                confidence=best_category[1],
                subcategory=subcategory,
                keywords=keywords,
                reasoning=reasoning,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Categorization error: {str(e)}")
            return CategoryResult(
                text=text,
                category="общие_вопросы",
                confidence=0.0,
                subcategory=None,
                keywords=[],
                reasoning="Ошибка при категоризации",
                timestamp=datetime.now()
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем знаки препинания
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text.strip()
    
    def _analyze_categories(self, text: str) -> Dict[str, float]:
        """Анализ текста по категориям"""
        scores = {}
        words = text.split()
        
        for category_name, category_def in self.categories.items():
            score = 0.0
            
            # Анализ по ключевым словам
            keyword_matches = 0
            for keyword in category_def.keywords:
                if keyword in text:
                    keyword_matches += 1
                    # Учитываем длину ключевого слова
                    score += len(keyword.split()) * 2
            
            # Анализ по паттернам
            pattern_matches = 0
            for pattern in category_def.patterns:
                if re.search(pattern, text):
                    pattern_matches += 1
                    score += 5
            
            # Анализ по отдельным словам
            word_matches = 0
            for word in words:
                if word not in self.stop_words:
                    for keyword in category_def.keywords:
                        if word in keyword.split():
                            word_matches += 1
                            score += 1
            
            # Нормализация с учетом приоритета
            total_possible = len(category_def.keywords) + len(category_def.patterns)
            if total_possible > 0:
                normalized_score = (score / total_possible) * (1.0 / category_def.priority)
                scores[category_name] = normalized_score
            else:
                scores[category_name] = 0.0
        
        return scores
    
    def _determine_subcategory(self, text: str, category: str, confidence: float) -> Optional[str]:
        """Определение подкатегории"""
        if confidence < 0.3:
            return None
        
        category_def = self.categories.get(category)
        if not category_def or not category_def.subcategories:
            return None
        
        subcategory_scores = {}
        for subcat_name, subcat_keywords in category_def.subcategories.items():
            score = 0
            for keyword in subcat_keywords:
                if keyword in text:
                    score += 1
            subcategory_scores[subcat_name] = score
        
        if subcategory_scores:
            best_subcategory = max(subcategory_scores.items(), key=lambda x: x[1])
            if best_subcategory[1] > 0:
                return best_subcategory[0]
        
        return None
    
    def _extract_keywords(self, text: str, category: str) -> List[str]:
        """Извлечение ключевых слов"""
        category_def = self.categories.get(category)
        if not category_def:
            return []
        
        found_keywords = []
        words = text.split()
        
        for keyword in category_def.keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        # Добавляем отдельные слова из ключевых фраз
        for word in words:
            if word not in self.stop_words and len(word) > 3:
                for keyword in category_def.keywords:
                    if word in keyword.split():
                        if word not in found_keywords:
                            found_keywords.append(word)
        
        return found_keywords[:10]  # Ограничиваем количество
    
    def _generate_reasoning(self, text: str, category: str, keywords: List[str]) -> str:
        """Генерация объяснения категоризации"""
        category_def = self.categories.get(category)
        if not category_def:
            return "Категория не определена"
        
        reasoning_parts = [
            f"Вопрос отнесен к категории '{category_def.display_name}'"
        ]
        
        if keywords:
            reasoning_parts.append(f"на основе ключевых слов: {', '.join(keywords[:3])}")
        
        reasoning_parts.append(f"({category_def.description})")
        
        return ". ".join(reasoning_parts)
    
    def get_category_info(self, category_name: str) -> Optional[CategoryDefinition]:
        """Получение информации о категории"""
        return self.categories.get(category_name)
    
    def get_all_categories(self) -> List[CategoryDefinition]:
        """Получение всех категорий"""
        return list(self.categories.values())
    
    def get_categories_with_stats(self) -> Dict[str, Any]:
        """Получение категорий со статистикой"""
        categories_info = {}
        
        for name, category_def in self.categories.items():
            categories_info[name] = {
                "name": category_def.name,
                "display_name": category_def.display_name,
                "description": category_def.description,
                "keywords_count": len(category_def.keywords),
                "patterns_count": len(category_def.patterns),
                "subcategories_count": len(category_def.subcategories),
                "priority": category_def.priority
            }
        
        return categories_info

# Глобальный экземпляр классификатора
question_categorizer = LegalQuestionCategorizer()

def get_question_categorizer() -> LegalQuestionCategorizer:
    """Получение экземпляра классификатора вопросов"""
    return question_categorizer
