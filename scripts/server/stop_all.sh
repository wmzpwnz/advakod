#!/bin/bash

echo "🛑 Stopping ADVAKOD - ИИ-Юрист для РФ"
echo "======================================"

# Останавливаем процессы на портах
echo "Stopping processes on ports 8000, 3000, 3001..."

# Backend (port 8000)
BACKEND_PID=$(lsof -ti:8000)
if [ -n "$BACKEND_PID" ]; then
  echo "Stopping backend (PID: $BACKEND_PID)..."
  kill -9 $BACKEND_PID 2>/dev/null
  echo "✅ Backend stopped"
else
  echo "ℹ️  No backend process found on port 8000"
fi

# Frontend (port 3000)
FRONTEND_PID=$(lsof -ti:3000)
if [ -n "$FRONTEND_PID" ]; then
  echo "Stopping frontend (PID: $FRONTEND_PID)..."
  kill -9 $FRONTEND_PID 2>/dev/null
  echo "✅ Frontend stopped"
else
  echo "ℹ️  No frontend process found on port 3000"
fi

# Frontend (port 3001 если есть)
FRONTEND_3001_PID=$(lsof -ti:3001)
if [ -n "$FRONTEND_3001_PID" ]; then
  echo "Stopping frontend on 3001 (PID: $FRONTEND_3001_PID)..."
  kill -9 $FRONTEND_3001_PID 2>/dev/null
  echo "✅ Frontend on 3001 stopped"
else
  echo "ℹ️  No frontend process found on port 3001"
fi

echo ""
echo "======================================"
echo "✅ All services stopped"
echo "======================================"

