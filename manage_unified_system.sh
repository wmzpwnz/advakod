#!/bin/bash
"""
Простой скрипт управления унифицированной системой кодексов
"""

SERVICE_NAME="unified_codex_system"
SERVICE_FILE="/root/advakod/unified_codex_system.service"
SYSTEMD_PATH="/etc/systemd/system/"

case "$1" in
    install)
        echo "🔧 Устанавливаем унифицированную систему кодексов..."
        
        # Копируем файл сервиса
        sudo cp $SERVICE_FILE $SYSTEMD_PATH$SERVICE_NAME.service
        
        # Перезагружаем systemd
        sudo systemctl daemon-reload
        
        # Включаем автозапуск
        sudo systemctl enable $SERVICE_NAME
        
        echo "✅ Система установлена и настроена на автозапуск"
        echo "📋 Для управления используйте:"
        echo "   sudo systemctl start $SERVICE_NAME    # Запустить"
        echo "   sudo systemctl stop $SERVICE_NAME     # Остановить"
        echo "   sudo systemctl status $SERVICE_NAME   # Статус"
        echo "   sudo systemctl restart $SERVICE_NAME  # Перезапустить"
        ;;
        
    start)
        echo "🚀 Запускаем унифицированную систему..."
        sudo systemctl start $SERVICE_NAME
        echo "✅ Система запущена"
        ;;
        
    stop)
        echo "🛑 Останавливаем систему..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Система остановлена"
        ;;
        
    restart)
        echo "🔄 Перезапускаем систему..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Система перезапущена"
        ;;
        
    status)
        echo "📊 Статус системы:"
        sudo systemctl status $SERVICE_NAME --no-pager
        echo ""
        echo "📋 Логи системы (последние 20 строк):"
        sudo journalctl -u $SERVICE_NAME --no-pager -n 20
        ;;
        
    logs)
        echo "📋 Логи системы (live):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
        
    check-files)
        echo "📊 Проверяем скачанные файлы..."
        if [ -d "/root/advakod/unified_codexes/codexes" ]; then
            file_count=$(ls -1 /root/advakod/unified_codexes/codexes/*.pdf 2>/dev/null | wc -l)
            echo "📄 Скачано PDF файлов: $file_count"
            echo "📁 Размер директории: $(du -sh /root/advakod/unified_codexes/codexes 2>/dev/null | cut -f1)"
            echo ""
            echo "📋 Список файлов:"
            ls -la /root/advakod/unified_codexes/codexes/*.pdf 2>/dev/null || echo "Файлы не найдены"
        else
            echo "❌ Директория скачивания не найдена"
        fi
        ;;
        
    manual-run)
        echo "🔄 Запускаем ручной цикл..."
        cd /root/advakod
        python3 unified_codex_system.py start
        ;;
        
    check-status)
        echo "📊 Проверяем статус системы..."
        cd /root/advakod
        python3 unified_codex_system.py status
        ;;
        
    uninstall)
        echo "🗑️ Удаляем систему..."
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl disable $SERVICE_NAME
        sudo rm $SYSTEMD_PATH$SERVICE_NAME.service
        sudo systemctl daemon-reload
        echo "✅ Система удалена"
        ;;
        
    *)
        echo "🚀 Унифицированная система скачивания и интеграции кодексов"
        echo "=" * 60
        echo ""
        echo "Использование: $0 {команда}"
        echo ""
        echo "Команды управления системой:"
        echo "  install       - Установить систему"
        echo "  start         - Запустить систему"
        echo "  stop          - Остановить систему"
        echo "  restart       - Перезапустить систему"
        echo "  status        - Показать статус системы"
        echo "  logs          - Показать логи системы"
        echo "  uninstall     - Удалить систему"
        echo ""
        echo "Команды проверки:"
        echo "  check-files   - Проверить скачанные файлы"
        echo "  manual-run    - Запустить ручной цикл"
        echo "  check-status  - Проверить статус системы"
        echo ""
        echo "Примеры:"
        echo "  $0 install    # Установить и настроить систему"
        echo "  $0 start      # Запустить систему"
        echo "  $0 status      # Проверить статус"
        echo "  $0 check-files # Посмотреть скачанные файлы"
        ;;
esac

