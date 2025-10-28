import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TrainingData:
    """Данные для обучения модели"""
    prompt: str
    completion: str
    category: str
    confidence: float
    source: str

@dataclass
class ModelMetrics:
    """Метрики модели"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    loss: float
    perplexity: float

@dataclass
class FineTuningJob:
    """Задача fine-tuning"""
    job_id: str
    model_name: str
    training_data: List[TrainingData]
    hyperparameters: Dict[str, Any]
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    metrics: Optional[ModelMetrics] = None
    error_message: Optional[str] = None

class LegalDataProcessor:
    """Процессор юридических данных для fine-tuning"""
    
    def __init__(self):
        self.legal_categories = {
            "трудовое_право": [
                "трудовой договор", "зарплата", "отпуск", "увольнение",
                "рабочее время", "трудовые споры", "охрана труда"
            ],
            "гражданское_право": [
                "договоры", "сделки", "обязательства", "наследование",
                "собственность", "защита прав", "возмещение ущерба"
            ],
            "налоговое_право": [
                "налоги", "налогообложение", "ндс", "подоходный налог",
                "налоговые льготы", "налоговая отчетность", "штрафы"
            ],
            "корпоративное_право": [
                "ооо", "акционерное общество", "устав", "директор",
                "акции", "дивиденды", "реорганизация", "ликвидация"
            ],
            "семейное_право": [
                "брак", "развод", "алименты", "опека", "усыновление",
                "раздел имущества", "брачный договор"
            ],
            "жилищное_право": [
                "квартира", "дом", "недвижимость", "прописка",
                "аренда", "ипотека", "приватизация", "выселение"
            ],
            "уголовное_право": [
                "преступление", "наказание", "суд", "следствие",
                "адвокат", "прокурор", "приговор", "апелляция"
            ],
            "административное_право": [
                "административные правонарушения", "штрафы", "лицензии",
                "разрешения", "государственные услуги", "жалобы"
            ]
        }
    
    def process_legal_documents(self, documents: List[Dict[str, Any]]) -> List[TrainingData]:
        """Обработка юридических документов для создания обучающих данных"""
        training_data = []
        
        for doc in documents:
            try:
                # Извлекаем вопросы и ответы из документа
                questions = doc.get("questions", [])
                answers = doc.get("answers", [])
                category = doc.get("category", "общие_вопросы")
                
                for i, question in enumerate(questions):
                    if i < len(answers):
                        training_data.append(TrainingData(
                            prompt=self._format_prompt(question, category),
                            completion=self._format_completion(answers[i]),
                            category=category,
                            confidence=0.9,
                            source=doc.get("source", "legal_database")
                        ))
                
                # Создаем дополнительные примеры на основе контекста
                if "context" in doc:
                    additional_examples = self._generate_additional_examples(
                        doc["context"], category
                    )
                    training_data.extend(additional_examples)
                    
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                continue
        
        return training_data
    
    def _format_prompt(self, question: str, category: str) -> str:
        """Форматирование промпта для обучения"""
        return f"Вопрос по {category}: {question}\n\nОтвет:"
    
    def _format_completion(self, answer: str) -> str:
        """Форматирование ответа для обучения"""
        return f" {answer.strip()}\n\n###"
    
    def _generate_additional_examples(self, context: str, category: str) -> List[TrainingData]:
        """Генерация дополнительных примеров на основе контекста"""
        examples = []
        
        # Создаем вариации вопросов на основе контекста
        base_questions = [
            f"Что нужно знать о {category}?",
            f"Какие особенности {category}?",
            f"Как правильно оформить документы по {category}?",
            f"Какие права и обязанности в {category}?",
            f"Какие штрафы предусмотрены за нарушения в {category}?"
        ]
        
        for question in base_questions:
            examples.append(TrainingData(
                prompt=self._format_prompt(question, category),
                completion=self._format_completion(f"На основе контекста: {context[:200]}..."),
                category=category,
                confidence=0.7,
                source="generated"
            ))
        
        return examples
    
    def create_conversation_data(self, conversations: List[Dict[str, Any]]) -> List[TrainingData]:
        """Создание обучающих данных из диалогов"""
        training_data = []
        
        for conv in conversations:
            try:
                messages = conv.get("messages", [])
                category = conv.get("category", "общие_вопросы")
                
                for i in range(0, len(messages) - 1, 2):
                    if i + 1 < len(messages):
                        user_msg = messages[i]
                        assistant_msg = messages[i + 1]
                        
                        if user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant":
                            training_data.append(TrainingData(
                                prompt=self._format_prompt(user_msg["content"], category),
                                completion=self._format_completion(assistant_msg["content"]),
                                category=category,
                                confidence=0.8,
                                source="conversation"
                            ))
                            
            except Exception as e:
                logger.error(f"Error processing conversation: {str(e)}")
                continue
        
        return training_data

class FineTuningManager:
    """Менеджер fine-tuning модели"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_model = "gpt-3.5-turbo"
        self.training_jobs: Dict[str, FineTuningJob] = {}
        self.data_processor = LegalDataProcessor()
    
    async def create_fine_tuning_job(
        self, 
        model_name: str,
        training_data: List[TrainingData],
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> FineTuningJob:
        """Создание задачи fine-tuning"""
        
        job_id = f"ft_{int(datetime.now().timestamp())}"
        
        job = FineTuningJob(
            job_id=job_id,
            model_name=model_name,
            training_data=training_data,
            hyperparameters=hyperparameters or self._get_default_hyperparameters(),
            status="created",
            created_at=datetime.now()
        )
        
        self.training_jobs[job_id] = job
        
        # Запускаем обучение в фоне
        asyncio.create_task(self._run_fine_tuning(job))
        
        return job
    
    async def _run_fine_tuning(self, job: FineTuningJob):
        """Запуск процесса fine-tuning"""
        try:
            job.status = "running"
            logger.info(f"Starting fine-tuning job: {job.job_id}")
            
            # Подготавливаем данные для OpenAI
            training_file = await self._prepare_training_file(job.training_data)
            
            # Отправляем запрос на fine-tuning
            if self.openai_api_key:
                await self._submit_to_openai(job, training_file)
            else:
                # Имитация fine-tuning для демонстрации
                await self._simulate_fine_tuning(job)
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Fine-tuning job failed: {str(e)}")
    
    async def _prepare_training_file(self, training_data: List[TrainingData]) -> str:
        """Подготовка файла с обучающими данными"""
        training_file_path = f"training_data_{int(datetime.now().timestamp())}.jsonl"
        
        with open(training_file_path, 'w', encoding='utf-8') as f:
            for data in training_data:
                training_example = {
                    "messages": [
                        {"role": "user", "content": data.prompt},
                        {"role": "assistant", "content": data.completion}
                    ]
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
        
        return training_file_path
    
    async def _submit_to_openai(self, job: FineTuningJob, training_file: str):
        """Отправка задачи fine-tuning в OpenAI"""
        try:
            # Загружаем файл в OpenAI
            async with aiohttp.ClientSession() as session:
                # Загрузка файла
                with open(training_file, 'rb') as f:
                    files = {'file': f}
                    data = {'purpose': 'fine-tune'}
                    
                    async with session.post(
                        'https://api.openai.com/v1/files',
                        headers={'Authorization': f'Bearer {self.openai_api_key}'},
                        data=data,
                        files=files
                    ) as response:
                        if response.status == 200:
                            file_data = await response.json()
                            file_id = file_data['id']
                            
                            # Создание задачи fine-tuning
                            fine_tune_data = {
                                'training_file': file_id,
                                'model': self.base_model,
                                'hyperparameters': job.hyperparameters
                            }
                            
                            async with session.post(
                                'https://api.openai.com/v1/fine_tuning/jobs',
                                headers={
                                    'Authorization': f'Bearer {self.openai_api_key}',
                                    'Content-Type': 'application/json'
                                },
                                json=fine_tune_data
                            ) as ft_response:
                                if ft_response.status == 200:
                                    ft_data = await ft_response.json()
                                    job.status = "submitted"
                                    logger.info(f"Fine-tuning job submitted to OpenAI: {ft_data['id']}")
                                else:
                                    raise Exception(f"OpenAI API error: {ft_response.status}")
                        else:
                            raise Exception(f"File upload error: {response.status}")
                            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            raise
    
    async def _simulate_fine_tuning(self, job: FineTuningJob):
        """Имитация процесса fine-tuning"""
        logger.info(f"Simulating fine-tuning for job: {job.job_id}")
        
        # Имитируем процесс обучения
        await asyncio.sleep(10)  # Имитация времени обучения
        
        # Создаем фиктивные метрики
        job.metrics = ModelMetrics(
            accuracy=0.92,
            precision=0.89,
            recall=0.91,
            f1_score=0.90,
            loss=0.15,
            perplexity=2.3
        )
        
        job.status = "completed"
        job.completed_at = datetime.now()
        
        logger.info(f"Fine-tuning job completed: {job.job_id}")
    
    def _get_default_hyperparameters(self) -> Dict[str, Any]:
        """Получение гиперпараметров по умолчанию"""
        return {
            "n_epochs": 3,
            "batch_size": 1,
            "learning_rate_multiplier": 0.1,
            "prompt_loss_weight": 0.01
        }
    
    async def get_job_status(self, job_id: str) -> Optional[FineTuningJob]:
        """Получение статуса задачи fine-tuning"""
        return self.training_jobs.get(job_id)
    
    async def list_jobs(self) -> List[FineTuningJob]:
        """Список всех задач fine-tuning"""
        return list(self.training_jobs.values())
    
    async def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи fine-tuning"""
        if job_id in self.training_jobs:
            job = self.training_jobs[job_id]
            if job.status in ["created", "running"]:
                job.status = "cancelled"
                return True
        return False
    
    async def evaluate_model(self, model_name: str, test_data: List[TrainingData]) -> ModelMetrics:
        """Оценка качества модели"""
        logger.info(f"Evaluating model: {model_name}")
        
        # Имитация оценки модели
        await asyncio.sleep(5)
        
        return ModelMetrics(
            accuracy=0.88,
            precision=0.85,
            recall=0.87,
            f1_score=0.86,
            loss=0.18,
            perplexity=2.5
        )
    
    async def deploy_model(self, job_id: str) -> bool:
        """Развертывание обученной модели"""
        job = self.training_jobs.get(job_id)
        if not job or job.status != "completed":
            return False
        
        try:
            # Здесь будет логика развертывания модели
            logger.info(f"Deploying model from job: {job_id}")
            
            # Имитация развертывания
            await asyncio.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Model deployment failed: {str(e)}")
            return False

# Глобальный экземпляр менеджера fine-tuning
fine_tuning_manager = FineTuningManager()

def get_fine_tuning_manager() -> FineTuningManager:
    """Получение экземпляра менеджера fine-tuning"""
    return fine_tuning_manager
