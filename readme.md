### README: Telegram Bot with AI Assistant (YandexGPT / GigaChat)

---

⚠ Описание<br>
Этот проект представляет собой Telegram-бота, который использует российские языковые модели (YandexGPT или GigaChat от Sber) для генерации ответов на сообщения пользователей. Бот поддерживает переключение между провайдерами, историю диалога и команды управления.

🛠 Требования<br>
Операционная система: Linux (Ubuntu/Debian рекомендовано) или Windows (для тестирования)<br>
Python: версия 3.11 (рекомендовано)<br>
Менеджер пакетов: pip<br>
Доступ в интернет для обращения к API Telegram и AI-провайдеров
---

🚀 Установка и настройка
1. Клонирование репозитория или копирование проекта на сервер
2. Создание виртуального окружения<br>
На Linux/macOS:<br>
python3.11 -m venv .venv<br>
source .venv/bin/activate

3. Установка зависимостей<br>
pip install -r requirements.txt
4. Настройка переменных окружения<br>
Создайте файл .env в корневой папке проекта и заполните его по образцу ниже.
    Пример .env:


    TELEGRAM_BOT_TOKEN=ваш_токен_бота
    YANDEX_API_KEY=ваш_API_ключ_яндекса
    YANDEX_FOLDER_ID=ваш_ID_каталога_в_облаке
    YANDEX_MODEL=yandexgpt-lite   # или yandexgpt, yandexgpt-pro
    GIGACHAT_API_KEY=ваш_API_ключ_гигачата
    GIGACHAT_MODEL=GigaChat:latest

Важно: Никогда не публикуйте файл .env в открытом доступе. Добавьте его в .gitignore.

🔑 Получение ключей API<br>
Telegram Bot Token<br>
В официальном боте @BotFather в Telegram.

YandexGPT<br>
Зарегистрируйтесь в Yandex Cloud.<br>
Создайте каталог (folder) и сервисный аккаунт.<br>
Получите API-ключ для сервисного аккаунта.<br>
Folder ID можно посмотреть в карточке каталога.<br>
Выберите модель: yandexgpt-lite (быстрая), yandexgpt (стандартная) или yandexgpt-pro (мощная).

GigaChat<br>
Зарегистрируйтесь на разработчика Sber.<br>
Получите API ключ

---
🏃 Запуск бота<br>
Локальный запуск (для тестирования)<br>
python main.py<br>
Бот начнёт опрашивать Telegram и отвечать на сообщения.

Запуск через systemd (Linux-сервер)<br>
Чтобы бот работал постоянно и автоматически перезапускался после сбоев, настройте systemd-сервис.

Создание юнит-файла
Создайте файл /etc/systemd/system/ai_bot.service с содержимым:

[Unit]<br>
Description=AI Telegram Bot Service<br>
After=network.target<br>

[Service]<br>
User=root<br>
Group=root<br>
WorkingDirectory=/opt/ai_bot<br>
ExecStart=/opt/ai_bot/.venv/bin/python3 /opt/ai_bot/main.py<br>
Restart=always<br>
RestartSec=10<br>

[Install]<br>
WantedBy=multi-user.target<br>
Убедитесь, что пути соответствуют вашему проекту.

✅ Активация сервиса <br>
sudo systemctl daemon-reload<br>
sudo systemctl enable ai_bot   # автозапуск при загрузке<br>
sudo systemctl start ai_bot     # запустить сейчас<br>
sudo systemctl status ai_bot    # проверить состояние<br>
🛑 Управление сервисом<br>
Остановка: sudo systemctl stop ai_bot<br>
Запуск: sudo systemctl start ai_bot<br>
Перезапуск: sudo systemctl restart ai_bot<br>
Отключение автозапуска: sudo systemctl disable ai_bot
Просмотр логов: sudo journalctl -u ai_bot -f

---
⚠️ Возможные проблемы и решения
1. Конфликт при запуске (ошибка Conflict)<br>
Симптом: В логах telegram.error.Conflict: terminated by other getUpdates request.<br>
Решение: Убедитесь, что нет другого запущенного экземпляра бота (проверьте через ps aux | grep python и убейте лишние процессы).<br>
Также можно выполнить сброс вебхука: <br>
curl -X POST "https://api.telegram.org/bot<ТОКЕН>/deleteWebhook"
2. Ошибка импорта Filters из telegram.ext<br>
Причина: Несовместимая версия python-telegram-bot (используется 13.x, а установлена 20.x).
Решение: Установите версию 13.7
3. Ошибка DLL load failed при импорте numpy (Windows)
Решение: Установите Microsoft Visual C++ Redistributable (скачать с официального сайта) и перезагрузите компьютер.
5. Бот не отвечает, хотя запущен<br>
Проверьте:<br>
Правильность токена в .env.<br>
Наличие активного интернета на сервере.<br>
Логи сервиса (journalctl -u ai_bot).

---
📞 Поддержка<br>
Если у вас возникли вопросы или проблемы, свяжитесь с разработчиком: @avsolon
---
© 2026 | Версия 1.0