"""
Оптимизированные гиперпараметры LoRA для юридических моделей
Исправляет M-01: оптимизация гиперпараметров LoRA на основе исследований и экспериментов
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelSize(Enum):
    """Размеры моделей"""
    SMALL = "small"      # <1B параметров
    MEDIUM = "medium"    # 1B-7B параметров  
    LARGE = "large"      # 7B-13B параметров
    EXTRA_LARGE = "xl"   # >13B параметров


class TaskComplexity(Enum):
    """Сложность задач"""
    SIMPLE = "simple"        # Классификация, простые QA
    MODERATE = "moderate"    # Средней сложности генерация
    COMPLEX = "complex"      # Сложная юридическая генерация


@dataclass
class LoRAHyperparameters:
    """Оптимизированные LoRA гиперпараметры"""
    
    # LoRA specific parameters
    r: int                                # Rank матриц
    lora_alpha: int                      # Scaling parameter
    lora_dropout: float                  # Dropout для LoRA слоев
    target_modules: List[str]            # Целевые модули для LoRA
    bias: str                            # Bias handling
    
    # Training parameters
    learning_rate: float                 # Learning rate
    num_train_epochs: int               # Количество эпох
    per_device_train_batch_size: int    # Batch size
    gradient_accumulation_steps: int    # Gradient accumulation
    warmup_ratio: float                 # Warmup ratio
    weight_decay: float                 # Weight decay
    max_grad_norm: float                # Gradient clipping
    
    # Optimization parameters
    optimizer: str                       # Оптимизатор
    lr_scheduler_type: str              # LR scheduler
    warmup_steps: int                   # Warmup steps
    
    # Memory and performance
    fp16: bool                          # FP16 precision
    bf16: bool                          # BF16 precision
    gradient_checkpointing: bool        # Gradient checkpointing
    dataloader_num_workers: int         # DataLoader workers
    
    # Regularization
    label_smoothing: float              # Label smoothing
    
    # Evaluation
    evaluation_strategy: str            # Evaluation strategy
    eval_steps: int                     # Evaluation frequency
    save_steps: int                     # Save frequency
    logging_steps: int                  # Logging frequency


class OptimizedLoRAConfig:
    """Класс для генерации оптимизированных LoRA конфигураций"""
    
    # Оптимизированные конфигурации для разных сценариев
    OPTIMIZED_CONFIGS = {
        # Конфигурация для небольших моделей (до 7B)
        ModelSize.MEDIUM: {
            TaskComplexity.SIMPLE: LoRAHyperparameters(
                r=8,
                lora_alpha=16,
                lora_dropout=0.05,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
                bias="none",
                learning_rate=3e-4,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=4,
                warmup_ratio=0.1,
                weight_decay=0.01,
                max_grad_norm=1.0,
                optimizer="adamw_torch",
                lr_scheduler_type="cosine",
                warmup_steps=100,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=2,
                label_smoothing=0.0,
                evaluation_strategy="steps",
                eval_steps=200,
                save_steps=500,
                logging_steps=10
            ),
            TaskComplexity.MODERATE: LoRAHyperparameters(
                r=16,
                lora_alpha=32,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                bias="none",
                learning_rate=2e-4,
                num_train_epochs=4,
                per_device_train_batch_size=2,
                gradient_accumulation_steps=8,
                warmup_ratio=0.15,
                weight_decay=0.01,
                max_grad_norm=1.0,
                optimizer="adamw_torch",
                lr_scheduler_type="cosine",
                warmup_steps=150,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=2,
                label_smoothing=0.05,
                evaluation_strategy="steps",
                eval_steps=250,
                save_steps=500,
                logging_steps=10
            ),
            TaskComplexity.COMPLEX: LoRAHyperparameters(
                r=32,
                lora_alpha=64,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                bias="lora_only",
                learning_rate=1e-4,
                num_train_epochs=5,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=16,
                warmup_ratio=0.2,
                weight_decay=0.015,
                max_grad_norm=0.5,
                optimizer="adamw_torch",
                lr_scheduler_type="cosine",
                warmup_steps=200,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=1,
                label_smoothing=0.1,
                evaluation_strategy="steps",
                eval_steps=300,
                save_steps=500,
                logging_steps=5
            )
        },
        
        # Конфигурация для больших моделей (7B+)
        ModelSize.LARGE: {
            TaskComplexity.SIMPLE: LoRAHyperparameters(
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "v_proj"],
                bias="none",
                learning_rate=2e-4,
                num_train_epochs=2,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=8,
                warmup_ratio=0.1,
                weight_decay=0.01,
                max_grad_norm=1.0,
                optimizer="adamw_8bit",
                lr_scheduler_type="cosine",
                warmup_steps=100,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=1,
                label_smoothing=0.0,
                evaluation_strategy="steps",
                eval_steps=200,
                save_steps=500,
                logging_steps=10
            ),
            TaskComplexity.MODERATE: LoRAHyperparameters(
                r=32,
                lora_alpha=64,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
                bias="none",
                learning_rate=1e-4,
                num_train_epochs=3,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=16,
                warmup_ratio=0.15,
                weight_decay=0.01,
                max_grad_norm=1.0,
                optimizer="adamw_8bit",
                lr_scheduler_type="cosine",
                warmup_steps=150,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=1,
                label_smoothing=0.05,
                evaluation_strategy="steps",
                eval_steps=250,
                save_steps=500,
                logging_steps=10
            ),
            TaskComplexity.COMPLEX: LoRAHyperparameters(
                r=64,
                lora_alpha=128,
                lora_dropout=0.15,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                bias="lora_only",
                learning_rate=5e-5,
                num_train_epochs=4,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=32,
                warmup_ratio=0.2,
                weight_decay=0.02,
                max_grad_norm=0.3,
                optimizer="adamw_8bit",
                lr_scheduler_type="cosine",
                warmup_steps=200,
                fp16=True,
                bf16=False,
                gradient_checkpointing=True,
                dataloader_num_workers=1,
                label_smoothing=0.1,
                evaluation_strategy="steps",
                eval_steps=300,
                save_steps=500,
                logging_steps=5
            )
        }
    }
    
    # Специализированные конфигурации для юридических задач
    LEGAL_TASK_CONFIGS = {
        "legal_classification": {
            "description": "Классификация правовых документов",
            "base_complexity": TaskComplexity.SIMPLE,
            "modifications": {
                "r": 12,
                "lora_alpha": 24,
                "learning_rate": 3e-4,
                "num_train_epochs": 4
            }
        },
        "legal_qa": {
            "description": "Вопросы-ответы по праву",
            "base_complexity": TaskComplexity.MODERATE,
            "modifications": {
                "r": 24,
                "lora_alpha": 48,
                "learning_rate": 1.5e-4,
                "label_smoothing": 0.05
            }
        },
        "legal_summarization": {
            "description": "Резюмирование правовых документов",
            "base_complexity": TaskComplexity.MODERATE,
            "modifications": {
                "r": 20,
                "lora_alpha": 40,
                "learning_rate": 2e-4,
                "weight_decay": 0.015
            }
        },
        "legal_generation": {
            "description": "Генерация правовых текстов",
            "base_complexity": TaskComplexity.COMPLEX,
            "modifications": {
                "r": 48,
                "lora_alpha": 96,
                "learning_rate": 8e-5,
                "num_train_epochs": 6,
                "label_smoothing": 0.1
            }
        },
        "contract_analysis": {
            "description": "Анализ договоров",
            "base_complexity": TaskComplexity.COMPLEX,
            "modifications": {
                "r": 40,
                "lora_alpha": 80,
                "learning_rate": 1e-4,
                "weight_decay": 0.02
            }
        }
    }
    
    @classmethod
    def get_optimized_config(
        cls,
        model_size: ModelSize = ModelSize.MEDIUM,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
        legal_task_type: Optional[str] = None,
        custom_modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Получить оптимизированную конфигурацию LoRA
        
        Args:
            model_size: Размер модели
            task_complexity: Сложность задачи
            legal_task_type: Тип юридической задачи
            custom_modifications: Пользовательские модификации
            
        Returns:
            Словарь с оптимизированными гиперпараметрами
        """
        
        # Получаем базовую конфигурацию
        base_config = cls.OPTIMIZED_CONFIGS[model_size][task_complexity]
        
        # Конвертируем в словарь
        config_dict = {
            "lora_config": {
                "r": base_config.r,
                "lora_alpha": base_config.lora_alpha,
                "lora_dropout": base_config.lora_dropout,
                "target_modules": base_config.target_modules,
                "bias": base_config.bias,
                "task_type": "CAUSAL_LM"
            },
            "learning_rate": base_config.learning_rate,
            "num_train_epochs": base_config.num_train_epochs,
            "per_device_train_batch_size": base_config.per_device_train_batch_size,
            "gradient_accumulation_steps": base_config.gradient_accumulation_steps,
            "warmup_ratio": base_config.warmup_ratio,
            "weight_decay": base_config.weight_decay,
            "max_grad_norm": base_config.max_grad_norm,
            "optim": base_config.optimizer,
            "lr_scheduler_type": base_config.lr_scheduler_type,
            "warmup_steps": base_config.warmup_steps,
            "fp16": base_config.fp16,
            "bf16": base_config.bf16,
            "gradient_checkpointing": base_config.gradient_checkpointing,
            "dataloader_num_workers": base_config.dataloader_num_workers,
            "label_smoothing": base_config.label_smoothing,
            "evaluation_strategy": base_config.evaluation_strategy,
            "eval_steps": base_config.eval_steps,
            "save_steps": base_config.save_steps,
            "logging_steps": base_config.logging_steps
        }
        
        # Применяем модификации для специфических юридических задач
        if legal_task_type and legal_task_type in cls.LEGAL_TASK_CONFIGS:
            task_config = cls.LEGAL_TASK_CONFIGS[legal_task_type]
            modifications = task_config["modifications"]
            
            for key, value in modifications.items():
                if key in ["r", "lora_alpha", "lora_dropout"]:
                    config_dict["lora_config"][key] = value
                else:
                    config_dict[key] = value
        
        # Применяем пользовательские модификации
        if custom_modifications:
            for key, value in custom_modifications.items():
                if key.startswith("lora_"):
                    lora_key = key.replace("lora_", "", 1)
                    if lora_key in config_dict["lora_config"]:
                        config_dict["lora_config"][lora_key] = value
                else:
                    config_dict[key] = value
        
        # Добавляем метаданные
        config_dict["_metadata"] = {
            "model_size": model_size.value,
            "task_complexity": task_complexity.value,
            "legal_task_type": legal_task_type,
            "optimized": True,
            "version": "1.0"
        }
        
        logger.info(f"Generated optimized LoRA config for {model_size.value} model, {task_complexity.value} task")
        
        return config_dict
    
    @classmethod
    def get_available_legal_tasks(cls) -> Dict[str, str]:
        """Получить список доступных юридических задач"""
        return {
            task_type: config["description"] 
            for task_type, config in cls.LEGAL_TASK_CONFIGS.items()
        }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Валидация конфигурации LoRA
        
        Returns:
            Список предупреждений/ошибок
        """
        warnings = []
        
        lora_config = config.get("lora_config", {})
        
        # Проверяем LoRA параметры
        r = lora_config.get("r", 0)
        alpha = lora_config.get("lora_alpha", 0)
        
        if r <= 0:
            warnings.append("LoRA rank (r) должен быть положительным")
        if r > 128:
            warnings.append("LoRA rank (r) слишком большой, может привести к overfitting")
        
        if alpha <= 0:
            warnings.append("LoRA alpha должен быть положительным")
        if alpha < r:
            warnings.append("LoRA alpha обычно должен быть >= r для стабильного обучения")
        
        # Проверяем learning rate
        lr = config.get("learning_rate", 0)
        if lr <= 0:
            warnings.append("Learning rate должен быть положительным")
        if lr > 1e-3:
            warnings.append("Learning rate может быть слишком большим для LoRA")
        
        # Проверяем batch size
        batch_size = config.get("per_device_train_batch_size", 0)
        grad_accum = config.get("gradient_accumulation_steps", 1)
        effective_batch_size = batch_size * grad_accum
        
        if effective_batch_size < 8:
            warnings.append("Эффективный batch size может быть слишком маленьким")
        if effective_batch_size > 128:
            warnings.append("Эффективный batch size может быть слишком большим")
        
        return warnings
    
    @classmethod
    def save_config(cls, config: Dict[str, Any], filepath: str) -> bool:
        """Сохранить конфигурацию в файл"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    @classmethod
    def load_config(cls, filepath: str) -> Optional[Dict[str, Any]]:
        """Загрузить конфигурацию из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Config loaded from {filepath}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None


# Пример использования
if __name__ == "__main__":
    # Создаем оптимизированную конфигурацию для генерации правовых текстов
    config = OptimizedLoRAConfig.get_optimized_config(
        model_size=ModelSize.MEDIUM,
        task_complexity=TaskComplexity.COMPLEX,
        legal_task_type="legal_generation"
    )
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Оптимизированная конфигурация LoRA:")
    logger.info(json.dumps(config, indent=2, ensure_ascii=False))
    
    # Проверяем конфигурацию
    warnings = OptimizedLoRAConfig.validate_config(config)
    if warnings:
        logger.warning("Предупреждения:")
        for warning in warnings:
            logger.warning(f"- {warning}")
    else:
        logger.info("Конфигурация валидна!")