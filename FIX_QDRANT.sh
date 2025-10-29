#!/bin/bash

# Исправление проблемы с размерностью векторов в Qdrant
echo "🔧 Исправление Qdrant - проблема с размерностью векторов"

# Остановка Qdrant
docker stop advakod_qdrant

# Удаление старой коллекции
echo "🗑️ Удаление старой коллекции с неправильной размерностью..."
curl -X DELETE "http://localhost:6333/collections/legal_documents"

# Создание новой коллекции с правильной размерностью
echo "🆕 Создание новой коллекции с правильной размерностью..."
curl -X PUT "http://localhost:6333/collections/legal_documents" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

# Перезапуск Qdrant
echo "🔄 Перезапуск Qdrant..."
docker start advakod_qdrant

echo "✅ Qdrant исправлен!"
