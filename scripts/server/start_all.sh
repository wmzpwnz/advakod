#!/bin/bash

echo "🚀 Starting ADVAKOD - ИИ-Юрист для РФ"
echo "======================================"

# Проверка .env файлов
if [ ! -f "backend/.env" ]; then
  echo "❌ backend/.env not found!"
  echo "Please create backend/.env file with configuration."
  exit 1
fi

if [ ! -f "frontend/.env" ]; then
  echo "❌ frontend/.env not found!"
  echo "Please create frontend/.env file with configuration."
  exit 1
fi

# Запуск backend
echo ""
echo "🔧 Starting Backend on http://localhost:8000..."
cd backend

# Активация виртуального окружения
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "venv_new/bin/activate" ]; then
  source venv_new/bin/activate
else
  echo "⚠️  Virtual environment not found. Creating..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
fi

# Запуск backend в фоне
python main.py > ../backend_runtime.log 2>&1 &
BACKEND_PID=$!
cd ..

# Ждем запуска backend
echo "⏳ Waiting for backend to start..."
sleep 5

# Проверка запуска backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Backend started successfully!"
else
  echo "⚠️  Backend may still be starting up..."
fi

# Запуск frontend
echo ""
echo "🎨 Starting Frontend on http://localhost:3000..."
cd frontend

# Установка зависимостей если нужно
if [ ! -d "node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  npm install
fi

# Запуск frontend в фоне
PORT=3000 npm start > ../frontend_runtime.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "✅ System started successfully!"
echo "======================================"
echo ""
echo "📊 Process IDs:"
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend:      http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Health:       http://localhost:8000/health"
echo "   Readiness:    http://localhost:8000/ready"
echo "   Metrics:      http://localhost:8000/metrics"
echo ""
echo "📝 Logs:"
echo "   Backend:      tail -f backend_runtime.log"
echo "   Frontend:     tail -f frontend_runtime.log"
echo ""
echo "🛑 To stop all services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or use: ./stop_all.sh"
echo ""
echo "======================================"
echo "Press Ctrl+C to stop monitoring..."
echo "======================================"

# Функция для остановки всех сервисов
cleanup() {
  echo ""
  echo "🛑 Stopping all services..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "✅ All services stopped"
  exit 0
}

# Ловим сигнал завершения
trap cleanup SIGINT SIGTERM

# Мониторинг процессов
while true; do
  sleep 5
  
  # Проверка backend
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend stopped unexpectedly!"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
  fi
  
  # Проверка frontend
  if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend stopped unexpectedly!"
    kill $BACKEND_PID 2>/dev/null
    exit 1
  fi
done

