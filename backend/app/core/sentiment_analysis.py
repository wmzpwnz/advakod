import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Результат сентимент анализа"""
    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    scores: Dict[str, float]  # Детальные оценки
    emotions: Dict[str, float]  # Эмоции
    keywords: List[str]  # Ключевые слова
    timestamp: datetime

@dataclass
class EmotionAnalysis:
    """Анализ эмоций"""
    joy: float
    sadness: float
    anger: float
    fear: float
    surprise: float
    disgust: float
    trust: float
    anticipation: float

class RussianSentimentAnalyzer:
    """Анализатор тональности для русского языка"""
    
    def __init__(self):
        # Словари для анализа тональности
        self.positive_words = {
            "хорошо", "отлично", "прекрасно", "замечательно", "супер", "великолепно",
            "потрясающе", "восхитительно", "превосходно", "идеально", "безупречно",
            "замечательный", "отличный", "прекрасный", "чудесный", "потрясающий",
            "восхитительный", "превосходный", "идеальный", "безупречный",
            "люблю", "нравится", "обожаю", "восхищаюсь", "ценю", "уважаю",
            "спасибо", "благодарю", "признателен", "доволен", "счастлив",
            "рад", "восторг", "удовольствие", "наслаждение", "радость",
            "успех", "победа", "достижение", "результат", "прогресс",
            "качественно", "профессионально", "компетентно", "эффективно",
            "быстро", "своевременно", "точно", "правильно", "корректно"
        }
        
        self.negative_words = {
            "плохо", "ужасно", "кошмар", "проблема", "ошибка", "неправильно",
            "некачественно", "непрофессионально", "некомпетентно", "неэффективно",
            "медленно", "несвоевременно", "неточно", "некорректно",
            "ненавижу", "не нравится", "отвратительно", "мерзко", "гадко",
            "жалуюсь", "недоволен", "расстроен", "злой", "сердитый",
            "разочарован", "обижен", "огорчен", "печален", "грустен",
            "провал", "поражение", "неудача", "проблема", "сложность",
            "задержка", "опоздание", "сбой", "неисправность", "дефект",
            "дорого", "переплата", "накрутка", "обман", "мошенничество",
            "нечестно", "несправедливо", "незаконно", "нарушение", "штраф"
        }
        
        # Интенсификаторы
        self.intensifiers = {
            "очень", "крайне", "чрезвычайно", "невероятно", "необычайно",
            "исключительно", "особенно", "особо", "весьма", "довольно",
            "достаточно", "вполне", "абсолютно", "полностью", "совершенно",
            "совсем", "вовсе", "никак", "ничуть", "нисколько"
        }
        
        # Отрицания
        self.negations = {
            "не", "ни", "нет", "никак", "ничуть", "нисколько", "вовсе не",
            "отнюдь не", "далеко не", "вовсе не", "совсем не"
        }
        
        # Эмоциональные словари
        self.emotion_words = {
            "joy": {
                "радость", "счастье", "восторг", "ликование", "веселье", "смех",
                "улыбка", "праздник", "торжество", "триумф", "победа", "успех"
            },
            "sadness": {
                "грусть", "печаль", "тоска", "уныние", "депрессия", "отчаяние",
                "горе", "скорбь", "плач", "слезы", "потеря", "разлука"
            },
            "anger": {
                "злость", "гнев", "ярость", "бешенство", "негодование", "возмущение",
                "раздражение", "досада", "обида", "ненависть", "враждебность"
            },
            "fear": {
                "страх", "боязнь", "тревога", "беспокойство", "паника", "ужас",
                "испуг", "волнение", "нервозность", "опасение", "предчувствие"
            },
            "surprise": {
                "удивление", "изумление", "потрясение", "шок", "неожиданность",
                "сюрприз", "ошеломление", "оцепенение", "ошарашенность"
            },
            "disgust": {
                "отвращение", "омерзение", "неприязнь", "антипатия", "брезгливость",
                "гадливость", "мерзость", "гадость", "мерзко", "противно"
            },
            "trust": {
                "доверие", "уверенность", "надежность", "честность", "порядочность",
                "верность", "преданность", "лояльность", "надежный", "честный"
            },
            "anticipation": {
                "ожидание", "предвкушение", "надежда", "мечта", "планы", "цели",
                "стремление", "желание", "намерение", "готовность", "нетерпение"
            }
        }
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Анализ тональности текста"""
        try:
            # Предобработка текста
            processed_text = self._preprocess_text(text)
            
            # Анализ тональности
            sentiment_scores = self._calculate_sentiment_scores(processed_text)
            
            # Анализ эмоций
            emotions = self._analyze_emotions(processed_text)
            
            # Извлечение ключевых слов
            keywords = self._extract_keywords(processed_text)
            
            # Определение общей тональности
            overall_sentiment = self._determine_overall_sentiment(sentiment_scores)
            
            # Вычисление уверенности
            confidence = self._calculate_confidence(sentiment_scores)
            
            return SentimentResult(
                text=text,
                sentiment=overall_sentiment,
                confidence=confidence,
                scores=sentiment_scores,
                emotions=emotions,
                keywords=keywords,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return SentimentResult(
                text=text,
                sentiment="neutral",
                confidence=0.0,
                scores={"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                emotions={},
                keywords=[],
                timestamp=datetime.now()
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем знаки препинания (кроме восклицательных и вопросительных)
        text = re.sub(r'[^\w\s!?]', ' ', text)
        
        return text.strip()
    
    def _calculate_sentiment_scores(self, text: str) -> Dict[str, float]:
        """Вычисление оценок тональности"""
        words = text.split()
        positive_score = 0.0
        negative_score = 0.0
        neutral_score = 0.0
        
        for i, word in enumerate(words):
            word_score = 0.0
            is_negated = False
            
            # Проверяем на отрицание
            if i > 0 and words[i-1] in self.negations:
                is_negated = True
            
            # Проверяем на интенсификаторы
            intensity = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensity = 1.5
            
            # Анализируем слово
            if word in self.positive_words:
                word_score = 1.0 * intensity
            elif word in self.negative_words:
                word_score = -1.0 * intensity
            
            # Применяем отрицание
            if is_negated:
                word_score = -word_score
            
            # Добавляем к общим оценкам
            if word_score > 0:
                positive_score += word_score
            elif word_score < 0:
                negative_score += abs(word_score)
            else:
                neutral_score += 1.0
        
        # Нормализуем оценки
        total_words = len(words)
        if total_words > 0:
            positive_score /= total_words
            negative_score /= total_words
            neutral_score /= total_words
        
        # Нормализуем до 1.0
        total_score = positive_score + negative_score + neutral_score
        if total_score > 0:
            positive_score /= total_score
            negative_score /= total_score
            neutral_score /= total_score
        
        return {
            "positive": positive_score,
            "negative": negative_score,
            "neutral": neutral_score
        }
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Анализ эмоций"""
        words = text.split()
        emotions = {emotion: 0.0 for emotion in self.emotion_words.keys()}
        
        for word in words:
            for emotion, emotion_words in self.emotion_words.items():
                if word in emotion_words:
                    emotions[emotion] += 1.0
        
        # Нормализуем
        total_words = len(words)
        if total_words > 0:
            for emotion in emotions:
                emotions[emotion] /= total_words
        
        return emotions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов"""
        words = text.split()
        word_freq = {}
        
        for word in words:
            if len(word) > 3:  # Игнорируем короткие слова
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Сортируем по частоте
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ-5 ключевых слов
        return [word for word, freq in sorted_words[:5]]
    
    def _determine_overall_sentiment(self, scores: Dict[str, float]) -> str:
        """Определение общей тональности"""
        positive = scores["positive"]
        negative = scores["negative"]
        neutral = scores["neutral"]
        
        # Определяем доминирующую тональность
        if positive > negative and positive > neutral:
            return "positive"
        elif negative > positive and negative > neutral:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """Вычисление уверенности в результате"""
        max_score = max(scores.values())
        min_score = min(scores.values())
        
        # Уверенность зависит от разности между максимальной и минимальной оценкой
        confidence = max_score - min_score
        
        # Нормализуем до 0-1
        return min(confidence, 1.0)

class AdvancedSentimentAnalyzer:
    """Продвинутый анализатор тональности с использованием ML"""
    
    def __init__(self):
        self.russian_analyzer = RussianSentimentAnalyzer()
        self.openai_api_key = None  # Для использования GPT моделей
    
    async def analyze_with_ml(self, text: str) -> SentimentResult:
        """Анализ тональности с использованием ML"""
        try:
            # Сначала используем правило-основанный анализ
            rule_based_result = self.russian_analyzer.analyze_sentiment(text)
            
            # Если есть API ключ, используем ML модель
            if self.openai_api_key:
                ml_result = await self._analyze_with_openai(text)
                
                # Комбинируем результаты
                combined_result = self._combine_results(rule_based_result, ml_result)
                return combined_result
            
            return rule_based_result
            
        except Exception as e:
            logger.error(f"ML sentiment analysis error: {str(e)}")
            return self.russian_analyzer.analyze_sentiment(text)
    
    async def _analyze_with_openai(self, text: str) -> SentimentResult:
        """Анализ тональности с использованием OpenAI"""
        try:
            prompt = f"""
            Проанализируй тональность следующего текста на русском языке.
            Определи:
            1. Общую тональность (positive/negative/neutral)
            2. Уверенность (0-1)
            3. Эмоции (joy, sadness, anger, fear, surprise, disgust, trust, anticipation)
            4. Ключевые слова
            
            Текст: "{text}"
            
            Ответ в формате JSON:
            {{
                "sentiment": "positive/negative/neutral",
                "confidence": 0.0-1.0,
                "emotions": {{
                    "joy": 0.0-1.0,
                    "sadness": 0.0-1.0,
                    "anger": 0.0-1.0,
                    "fear": 0.0-1.0,
                    "surprise": 0.0-1.0,
                    "disgust": 0.0-1.0,
                    "trust": 0.0-1.0,
                    "anticipation": 0.0-1.0
                }},
                "keywords": ["слово1", "слово2", ...]
            }}
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.openai_api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-3.5-turbo',
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.1
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Парсим JSON ответ
                        result_data = json.loads(content)
                        
                        return SentimentResult(
                            text=text,
                            sentiment=result_data['sentiment'],
                            confidence=result_data['confidence'],
                            scores={
                                "positive": 0.0,
                                "negative": 0.0,
                                "neutral": 0.0
                            },
                            emotions=result_data['emotions'],
                            keywords=result_data['keywords'],
                            timestamp=datetime.now()
                        )
                    else:
                        raise Exception(f"OpenAI API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"OpenAI sentiment analysis error: {str(e)}")
            raise
    
    def _combine_results(self, rule_result: SentimentResult, ml_result: SentimentResult) -> SentimentResult:
        """Комбинирование результатов правил и ML"""
        # Взвешенное среднее (70% ML, 30% правила)
        ml_weight = 0.7
        rule_weight = 0.3
        
        # Комбинируем тональность
        if ml_result.sentiment == rule_result.sentiment:
            combined_sentiment = ml_result.sentiment
            combined_confidence = (ml_result.confidence * ml_weight + 
                                 rule_result.confidence * rule_weight)
        else:
            # Если тональности разные, выбираем с большей уверенностью
            if ml_result.confidence > rule_result.confidence:
                combined_sentiment = ml_result.sentiment
                combined_confidence = ml_result.confidence
            else:
                combined_sentiment = rule_result.sentiment
                combined_confidence = rule_result.confidence
        
        # Комбинируем эмоции
        combined_emotions = {}
        for emotion in ml_result.emotions:
            combined_emotions[emotion] = (
                ml_result.emotions[emotion] * ml_weight +
                rule_result.emotions.get(emotion, 0.0) * rule_weight
            )
        
        # Комбинируем ключевые слова
        combined_keywords = list(set(ml_result.keywords + rule_result.keywords))[:10]
        
        return SentimentResult(
            text=ml_result.text,
            sentiment=combined_sentiment,
            confidence=combined_confidence,
            scores=rule_result.scores,  # Оставляем детальные оценки от правил
            emotions=combined_emotions,
            keywords=combined_keywords,
            timestamp=datetime.now()
        )
    
    async def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Анализ тональности для списка текстов"""
        results = []
        
        for text in texts:
            try:
                result = await self.analyze_with_ml(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch analysis error for text: {str(e)}")
                # Добавляем нейтральный результат в случае ошибки
                results.append(SentimentResult(
                    text=text,
                    sentiment="neutral",
                    confidence=0.0,
                    scores={"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                    emotions={},
                    keywords=[],
                    timestamp=datetime.now()
                ))
        
        return results

# Глобальный экземпляр анализатора
sentiment_analyzer = AdvancedSentimentAnalyzer()

def get_sentiment_analyzer() -> AdvancedSentimentAnalyzer:
    """Получение экземпляра анализатора тональности"""
    return sentiment_analyzer
