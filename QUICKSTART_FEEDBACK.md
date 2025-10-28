# ⚡ Быстрый старт: Система обратной связи

## 🚀 Запуск за 3 минуты

### Шаг 1: Автоматическое развертывание
```bash
./deploy_feedback_system.sh
```

### Шаг 2: Запуск серверов
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm start
```

### Шаг 3: Назначить модераторов
1. Откройте админ-панель: http://localhost:3000/admin
2. Перейдите в "Управление ролями"
3. Назначьте роль `moderator` пользователям

## ✅ Готово!

- **Пользователи**: Видят кнопки 👍 👎 после ответов ИИ
- **Модераторы**: Доступ к `/moderation`
- **Админы**: Доступ к `/moderation-dashboard`

## 📚 Документация

- `FEEDBACK_SYSTEM_README.md` - Полное руководство
- `FINAL_REPORT_FEEDBACK_SYSTEM.md` - Детальный отчет

## 👨‍💻 Разработчик

**Багбеков Азиз** | Компания "Аврамир" | [A2codex.com](https://a2codex.com)
