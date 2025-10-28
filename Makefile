# АДВАКОД - ИИ-Юрист для РФ
# Makefile для удобного запуска

.PHONY: help start backend frontend stop clean install

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Запустить все сервисы
	@echo "🚀 Запускаю все сервисы..."
	@make backend &
	@make frontend

backend: ## Запустить бэкенд
	@echo "🚀 Запускаю бэкенд..."
	@cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

frontend: ## Запустить фронтенд
	@echo "🚀 Запускаю фронтенд..."
	@cd frontend && npm start

stop: ## Остановить все сервисы
	@echo "🛑 Останавливаю все сервисы..."
	@pkill -f uvicorn || true
	@pkill -f "npm start" || true

clean: ## Очистить временные файлы
	@echo "🧹 Очищаю временные файлы..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete

install: ## Установить все зависимости
	@echo "📦 Устанавливаю зависимости..."
	@cd frontend && npm install
	@cd backend && pip install -r requirements.txt
