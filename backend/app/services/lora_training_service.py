"""
Сервис для обучения LoRA с оптимизированными гиперпараметрами
"""
import logging
import json
import os
import subprocess
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.training_data import TrainingData, TrainingJob, ModelVersion
from ..core.config import settings
from ..core.optimized_lora_config import OptimizedLoRAConfig, ModelSize, TaskComplexity

logger = logging.getLogger(__name__)


class LoRATrainingService:
    """Сервис для обучения LoRA"""
    
    def __init__(self, db: Session):
        self.db = db
        self.training_dir = os.path.join(settings.BASE_DIR, "lora_training")
        self.data_dir = os.path.join(self.training_dir, "data")
        self.models_dir = os.path.join(self.training_dir, "models")
        self.scripts_dir = os.path.join(self.training_dir, "scripts")
        
        # Создаем директории если не существуют
        os.makedirs(self.training_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
    
    async def run_training(self, job_id: int) -> Dict[str, Any]:
        """
        Запуск обучения LoRA
        
        Args:
            job_id: ID задачи обучения
        
        Returns:
            Результат обучения
        """
        try:
            logger.info(f"🚀 Запуск обучения LoRA для задачи {job_id}")
            
            # Получаем задачу обучения
            job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                logger.error(f"Задача {job_id} не найдена")
                return {"error": "Задача не найдена"}
            
            # Обновляем статус
            job.status = "running"
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            # Подготавливаем данные
            data_path = await self._prepare_training_data(job_id)
            if not data_path:
                job.status = "failed"
                job.error_message = "Ошибка подготовки данных"
                job.completed_at = datetime.utcnow()
                self.db.commit()
                return {"error": "Ошибка подготовки данных"}
            
            # Создаем конфигурацию обучения
            config_path = await self._create_training_config(job, data_path)
            
            # Запускаем обучение
            result = await self._execute_training(job, config_path)
            
            # Обновляем статус задачи
            if result["success"]:
                job.status = "completed"
                job.progress = 100.0
                job.loss = result.get("final_loss")
                job.accuracy = result.get("final_accuracy")
                
                # Создаем версию модели
                model_version = await self._create_model_version(job, result)
                if model_version:
                    job.metadata = job.metadata or {}
                    job.metadata["model_version_id"] = model_version.id
            else:
                job.status = "failed"
                job.error_message = result.get("error", "Неизвестная ошибка")
            
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"✅ Обучение завершено для задачи {job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}")
            
            # Обновляем статус задачи
            job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                self.db.commit()
            
            return {"error": str(e)}
    
    async def _prepare_training_data(self, job_id: int) -> Optional[str]:
        """Подготовка данных для обучения"""
        try:
            logger.info("📊 Подготовка данных для обучения")
            
            # Получаем одобренные данные
            training_data = self.db.query(TrainingData).filter(
                TrainingData.is_approved == True,
                TrainingData.is_used_for_training == False
            ).all()
            
            if not training_data:
                logger.error("Нет одобренных данных для обучения")
                return None
            
            # Конвертируем в формат для обучения
            formatted_data = []
            for data in training_data:
                formatted_item = {
                    "instruction": data.instruction,
                    "input": data.input or "",
                    "output": data.output
                }
                formatted_data.append(formatted_item)
            
            # Сохраняем в JSONL файл
            data_file = os.path.join(self.data_dir, f"training_data_{job_id}.jsonl")
            with open(data_file, 'w', encoding='utf-8') as f:
                for item in formatted_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            # Помечаем данные как использованные
            for data in training_data:
                data.is_used_for_training = True
            self.db.commit()
            
            logger.info(f"✅ Подготовлено {len(formatted_data)} примеров для обучения")
            return data_file
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных: {e}")
            return None
    
    async def _create_training_config(self, job: TrainingJob, data_path: str) -> str:
        """Создание оптимизированной конфигурации обучения"""
        try:
            logger.info("⚙️ Создание оптимизированной конфигурации обучения")
            
            # Получаем метаданные задачи
            metadata = job.metadata or {}
            
            # Определяем параметры оптимизации
            model_size = ModelSize(metadata.get("model_size", "medium"))
            task_complexity = TaskComplexity(metadata.get("task_complexity", "moderate"))
            legal_task_type = metadata.get("legal_task_type")
            
            # Получаем оптимизированную конфигурацию
            optimized_config = OptimizedLoRAConfig.get_optimized_config(
                model_size=model_size,
                task_complexity=task_complexity,
                legal_task_type=legal_task_type,
                custom_modifications=job.hyperparameters
            )
            
            # Проверяем конфигурацию
            warnings = OptimizedLoRAConfig.validate_config(optimized_config)
            if warnings:
                logger.warning(f"Предупреждения конфигурации: {warnings}")
            
            # Добавляем обязательные параметры
            final_config = {
                "model_name_or_path": settings.SAIGA_MODEL_PATH,
                "data_path": data_path,
                "output_dir": os.path.join(self.models_dir, f"lora_model_{job.id}"),
                "max_seq_length": 1024,  # Увеличиваем для юридических текстов
                "packing": False,
                "remove_unused_columns": False,
                "dataloader_pin_memory": False,
                "seed": 42,
                "report_to": "none",
                **optimized_config
            }
            
            # Сохраняем конфигурацию
            config_file = os.path.join(self.scripts_dir, f"training_config_{job.id}.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, indent=2, ensure_ascii=False)
            
            # Сохраняем оптимизированную конфигурацию в metadata задачи
            job.metadata = job.metadata or {}
            job.metadata["optimized_config"] = optimized_config
            job.metadata["config_warnings"] = warnings
            self.db.commit()
            
            logger.info(f"✅ Оптимизированная конфигурация сохранена: {config_file}")
            logger.info(f"📊 Параметры: {model_size.value}/{task_complexity.value}/{legal_task_type}")
            
            return config_file
            
        except Exception as e:
            logger.error(f"Ошибка создания конфигурации: {e}")
            raise
    
    async def _execute_training(self, job: TrainingJob, config_path: str) -> Dict[str, Any]:
        """Выполнение обучения"""
        try:
            logger.info("🤖 Запуск обучения модели")
            
            # Создаем скрипт обучения
            script_path = await self._create_training_script(config_path)
            
            # Запускаем обучение
            process = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            # Мониторим прогресс
            stdout_lines = []
            stderr_lines = []
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8').strip()
                stdout_lines.append(line_str)
                
                # Парсим прогресс
                if "loss" in line_str.lower():
                    try:
                        # Простой парсинг loss из лога
                        if "loss=" in line_str:
                            loss_str = line_str.split("loss=")[1].split()[0]
                            loss = float(loss_str)
                            job.loss = loss
                            
                            # Обновляем прогресс (примерно)
                            if "epoch" in line_str:
                                epoch_str = line_str.split("epoch")[1].split()[0]
                                epoch = float(epoch_str)
                                progress = (epoch / job.hyperparameters.get("num_train_epochs", 3)) * 100
                                job.progress = min(100.0, progress)
                                self.db.commit()
                    except:
                        pass
                
                logger.info(f"Training: {line_str}")
            
            # Ждем завершения
            return_code = await process.wait()
            
            # Читаем stderr
            stderr = await process.stderr.read()
            stderr_lines = stderr.decode('utf-8').split('\n')
            
            if return_code == 0:
                logger.info("✅ Обучение завершено успешно")
                return {
                    "success": True,
                    "final_loss": job.loss,
                    "final_accuracy": job.accuracy,
                    "output": stdout_lines
                }
            else:
                logger.error(f"❌ Ошибка обучения (код {return_code})")
                return {
                    "success": False,
                    "error": f"Ошибка обучения: {stderr_lines[-2] if stderr_lines else 'Неизвестная ошибка'}",
                    "output": stdout_lines,
                    "stderr": stderr_lines
                }
                
        except Exception as e:
            logger.error(f"Ошибка выполнения обучения: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_training_script(self, config_path: str) -> str:
        """Создание скрипта обучения"""
        try:
            logger.info("📝 Создание скрипта обучения")
            
            script_content = f'''
import json
import os
import sys
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path):
    """Загрузка конфигурации"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_dataset(data_path):
    """Подготовка датасета"""
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    
    # Форматируем данные для обучения
    formatted_data = []
    for item in data:
        instruction = item.get('instruction', '')
        input_text = item.get('input', '')
        output = item.get('output', '')
        
        # Создаем промпт в формате для Saiga
        if input_text:
            prompt = f"<s>system\\nТы - ИИ-юрист, специализирующийся на российском праве.\\n<|im_end|>\\n<|im_start|>user\\n{instruction}\\n{input_text}<|im_end|>\\n<|im_start|>assistant\\n{output}<|im_end|>"
        else:
            prompt = f"<s>system\\nТы - ИИ-юрист, специализирующийся на российском праве.\\n<|im_end|>\\n<|im_start|>user\\n{instruction}<|im_end|>\\n<|im_start|>assistant\\n{output}<|im_end|>"
        
        formatted_data.append({{"text": prompt}})
    
    return Dataset.from_list(formatted_data)

def main():
    """Основная функция обучения"""
    try:
        # Загружаем конфигурацию
        config = load_config("{config_path}")
        logger.info(f"Конфигурация загружена: {{config}}")
        
        # Загружаем токенизатор
        logger.info("Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(config["model_name_or_path"])
        
        # Настраиваем токенизатор
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Загружаем модель
        logger.info("Загрузка модели...")
        model = AutoModelForCausalLM.from_pretrained(
            config["model_name_or_path"],
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Настраиваем LoRA
        lora_config = LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            target_modules=config["lora_target_modules"],
            lora_dropout=config["lora_dropout"],
            bias=config["lora_bias"],
            task_type=TaskType.CAUSAL_LM,
        )
        
        # Применяем LoRA к модели
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Подготавливаем датасет
        logger.info("Подготовка датасета...")
        dataset = prepare_dataset(config["data_path"])
        logger.info(f"Датасет подготовлен: {{len(dataset)}} примеров")
        
        # Токенизация
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=config["max_seq_length"],
                return_tensors="pt"
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Настройки обучения
        training_args = TrainingArguments(
            output_dir=config["output_dir"],
            num_train_epochs=config["num_train_epochs"],
            per_device_train_batch_size=config["per_device_train_batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation_steps"],
            learning_rate=config["learning_rate"],
            warmup_steps=config["warmup_steps"],
            logging_steps=config["logging_steps"],
            save_steps=config["save_steps"],
            evaluation_strategy=config["evaluation_strategy"],
            eval_steps=config["eval_steps"],
            fp16=config["fp16"],
            bf16=config["bf16"],
            gradient_checkpointing=config["gradient_checkpointing"],
            optim=config["optim"],
            lr_scheduler_type=config["lr_scheduler_type"],
            warmup_ratio=config["warmup_ratio"],
            weight_decay=config["weight_decay"],
            max_grad_norm=config["max_grad_norm"],
            seed=config["seed"],
            report_to=config["report_to"],
            remove_unused_columns=config["remove_unused_columns"],
            dataloader_pin_memory=config["dataloader_pin_memory"],
        )
        
        # Создаем тренер
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        )
        
        # Запускаем обучение
        logger.info("Начало обучения...")
        trainer.train()
        
        # Сохраняем модель
        logger.info("Сохранение модели...")
        trainer.save_model()
        tokenizer.save_pretrained(config["output_dir"])
        
        logger.info("Обучение завершено успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка обучения: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
            
            script_path = os.path.join(self.scripts_dir, f"train_lora_{job.id}.py")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            logger.info(f"✅ Скрипт обучения создан: {script_path}")
            return script_path
            
        except Exception as e:
            logger.error(f"Ошибка создания скрипта: {e}")
            raise
    
    async def _create_model_version(self, job: TrainingJob, result: Dict[str, Any]) -> Optional[ModelVersion]:
        """Создание версии модели"""
        try:
            logger.info("📦 Создание версии модели")
            
            # Генерируем версию
            version = f"v{job.id}.0.0"
            
            # Путь к обученной модели
            model_path = os.path.join(self.models_dir, f"lora_model_{job.id}")
            
            # Создаем запись в БД
            model_version = ModelVersion(
                version=version,
                base_model=settings.SAIGA_MODEL_PATH,
                lora_config=job.hyperparameters.get("lora_config", {}),
                training_data_count=job.training_data_count,
                performance_metrics={
                    "final_loss": result.get("final_loss"),
                    "final_accuracy": result.get("final_accuracy"),
                    "training_duration": (job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None
                },
                model_path=model_path,
                created_by=job.created_by
            )
            
            self.db.add(model_version)
            self.db.commit()
            self.db.refresh(model_version)
            
            logger.info(f"✅ Версия модели создана: {version}")
            return model_version
            
        except Exception as e:
            logger.error(f"Ошибка создания версии модели: {e}")
            return None
    
    def get_training_status(self, job_id: int) -> Dict[str, Any]:
        """Получение статуса обучения"""
        try:
            job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                return {"error": "Задача не найдена"}
            
            return {
                "id": job.id,
                "job_name": job.job_name,
                "status": job.status,
                "progress": job.progress,
                "current_epoch": job.current_epoch,
                "total_epochs": job.total_epochs,
                "loss": job.loss,
                "accuracy": job.accuracy,
                "error_message": job.error_message,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {"error": str(e)}
    
    @classmethod
    def get_recommended_config(
        cls, 
        model_size: str = "medium",
        task_type: str = "legal_qa",
        dataset_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Получить рекомендуемую конфигурацию LoRA
        
        Args:
            model_size: Размер модели ('small', 'medium', 'large')
            task_type: Тип задачи
            dataset_size: Размер датасета
            
        Returns:
            Рекомендуемая конфигурация
        """
        try:
            # Определяем сложность задачи на основе размера датасета
            if dataset_size < 500:
                complexity = TaskComplexity.SIMPLE
            elif dataset_size < 2000:
                complexity = TaskComplexity.MODERATE
            else:
                complexity = TaskComplexity.COMPLEX
            
            # Получаем оптимизированную конфигурацию
            config = OptimizedLoRAConfig.get_optimized_config(
                model_size=ModelSize(model_size),
                task_complexity=complexity,
                legal_task_type=task_type
            )
            
            # Добавляем метаданные рекомендации
            config["recommendation_info"] = {
                "model_size": model_size,
                "task_type": task_type,
                "dataset_size": dataset_size,
                "complexity": complexity.value,
                "estimated_training_time": cls._estimate_training_time(config, dataset_size),
                "memory_requirements": cls._estimate_memory_requirements(config),
                "available_legal_tasks": OptimizedLoRAConfig.get_available_legal_tasks()
            }
            
            # Проверяем конфигурацию
            warnings = OptimizedLoRAConfig.validate_config(config)
            if warnings:
                config["warnings"] = warnings
            
            return {
                "success": True,
                "config": config,
                "description": f"Оптимизированная конфигурация для {model_size} модели, задача: {task_type}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендации: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _estimate_training_time(config: Dict[str, Any], dataset_size: int) -> str:
        """Оценка времени обучения"""
        epochs = config.get("num_train_epochs", 3)
        batch_size = config.get("per_device_train_batch_size", 1)
        grad_accum = config.get("gradient_accumulation_steps", 4)
        
        effective_batch_size = batch_size * grad_accum
        steps_per_epoch = dataset_size // effective_batch_size
        total_steps = steps_per_epoch * epochs
        
        # Примерная оценка: 1-2 секунды на шаг для LoRA
        estimated_seconds = total_steps * 1.5
        
        if estimated_seconds < 3600:
            return f"{int(estimated_seconds // 60)} минут"
        else:
            return f"{estimated_seconds / 3600:.1f} часов"
    
    @staticmethod
    def _estimate_memory_requirements(config: Dict[str, Any]) -> str:
        """Оценка требований к памяти"""
        lora_config = config.get("lora_config", {})
        r = lora_config.get("r", 16)
        batch_size = config.get("per_device_train_batch_size", 1)
        
        # Примерная оценка для 7B модели
        base_memory = 14  # GB для базовой модели
        lora_memory = (r / 16) * 2  # Дополнительная память для LoRA
        batch_memory = batch_size * 2  # Память для batch
        
        total_memory = base_memory + lora_memory + batch_memory
        
        return f"{total_memory:.1f} GB VRAM"
