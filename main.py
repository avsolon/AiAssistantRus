from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import requests
import logging
import time
import os
from dotenv import load_dotenv
import uuid
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Формат записи логов
    level=logging.INFO  # Уровень логирования
)
logger = logging.getLogger(__name__)

class RussianAI:
    def __init__(self):
        # Получение провайдера по умолчанию из переменных окружения
        self.provider = os.getenv("DEFAULT_PROVIDER", "yandexgpt")
        # Инициализация истории диалога как пустого списка
        self.conversation_history = []
        # Настройка выбранного провайдера
        self.set_provider(self.provider)

    def set_provider(self, provider: str):
        self.provider = provider.lower() # переводим название провайдера в нижний регистр
        self.conversation_history = []

        if self.provider == "yandexgpt":
            # получение ключа, id каталога и модели
            self.api_key = os.getenv("YANDEX_API_KEY")
            self.folder_id = os.getenv("YANDEX_FOLDER_ID")
            self.model = os.getenv("YANDEX_MODEL", "yandexgpt-lite")
            # URL API YandexGPT
            self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            # Проверка наличия обязательных ключей
            if not self.api_key or not self.folder_id:
                # Запись ошибки в лог
                logger.error("Не заданы YANDEX_API_KEY и YANDEX_FOLDER_ID")
                return False  # Возврат статуса ошибки
        elif self.provider == "gigachat":
            self.api_key = os.getenv("GIGACHAT_API_KEY")
            self.model = os.getenv("GIGACHAT_MODEL", "GigaChat:latest")
            self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            self.base_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            if not self.api_key:
                logger.error("Не задан GIGACHAT_API_KEY")
                return False
        else:
            logger.error(f"Неизвестный провайдер {provider}")
            return False

        logger.info(f"Используется провайдер: {self.provider.upper()} ({self.model})")
        return True

    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    def generate_response(self, user_input: str):
        self.add_message("user", user_input)
        try:
            # Выбор соответствующего метода API в зависимости от провайдера
            if self.provider == "yandexgpt":
                return self._yandex_request()
            elif self.provider == "gigachat":
                return self._gigachat_request()
        except Exception as e:
            return f"🚨 Ошибка API ({self.provider}): {str(e)}"

    def _yandex_request(self):
        headers = {
            "Authorization": f"Api-Key {self.api_key}",  # API-ключ для аутентификации
            "Content-Type": "application/json",  # Тип содержимого
            "x-folder-id": self.folder_id  # Идентификатор каталога
        }
        yandex_messages = []
        for msg in self.conversation_history:
            yandex_messages.append({
                "role": msg["role"],
                "text": msg["content"] # Yandex использует "text" вместо "content"
            })
         # Формирование тела запроса
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions":{
                "stream": False,  # Режим без потоковой передачи
                "temperature": 0.7,  # Креативность ответов
                "maxTokens": 2000  # Максимальное количество токенов в ответе
            },
            "messages": yandex_messages  # История диалога
        }
        try:
            response = requests.post(
                self.base_url,  # URL API
                headers=headers,  # Заголовки
                json=payload,  # Тело запроса в формате JSON
                timeout=30  # Таймаут запроса
            )
            # Проверка статуса ответа
            if response.status_code != 200:
                # Логирование ошибки при ненормальном статусе
                logger.error(f"Ошибка {response.status_code}: {response.text}")
                return f"Ошибка API: {response.text}"
            data = response.json()
            ai_reply = data["result"]["alternatives"][0]["message"]["text"]
            self.add_message("assistant", ai_reply)
            return ai_reply # возврат ответа
        except Exception as e:
            return f"Ошибка соединения: {str(e)}"

    def _gigachat_request(self):
        try:
            auth_headers = {
                "Authorization": f"Basic {self.api_key}",  # ключ уже в base64
                "Content-Type": "application/x-www-form-urlencoded",
                "RqUID": str(uuid.uuid4()),
                "Accept": "application/json"
            }
            auth_data = {
                "scope": "GIGACHAT_API_PERS"
            }
            auth_response = requests.post(
                self.auth_url,
                headers=auth_headers,
                data=auth_data,
                timeout=30,
                verify=False  # обязательно для порта 9443
            )
            if auth_response.status_code != 200:
                logger.error(
                    f"Ошибка аутентификации GigaChat: статус {auth_response.status_code}, ответ: {auth_response.text}")
                return "Ошибка аутентификации GigaChat"

            auth_data = auth_response.json()
            access_token = auth_data["access_token"]

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            # Формирование тела запроса
            payload = {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            response = requests.post(
                self.base_url,  # URL API
                headers=headers,  # Заголовки
                json=payload,  # Тело запроса в формате JSON
                timeout=30,  # Таймаут запроса
                verify = False
            )
            if response.status_code != 200:
                # Логирование ошибки при ненормальном статусе
                logger.error(f"Ошибка {response.status_code}: {response.text}")
                return f"Ошибка API: {response.text}"

            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]
            self.add_message("assistant", ai_reply)
            return ai_reply
        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка GIGACHAT: {e}")
            return f"Ошибка соединения: {str(e)}"
        except Exception as e:
            logger.error(f"Неизвестная ошибка GIGACHAT: {e}", exc_info=True)
            return f"Ошибка: {str(e)}"

    def clear_history(self):
        self.conversation_history = []
        logger.info("История диалога очищена")
        return True

ai_assistant = RussianAI()

def start(update: Update, context: CallbackContext) -> None:
    help_text = (
        "🤖 Привет! Я российский AI-ассистент. Могу ответить на ваши вопросы с помощью:\n"
        f"• YandexGPT ({ai_assistant.model if ai_assistant.provider == 'yandexgpt' else 'доступен через /yandex'})\n"
        f"• GigaChat ({ai_assistant.model if ai_assistant.provider == 'gigachat' else 'доступен через /gigachat'})\n\n"
        f"• доступные команды: \n"
        "/yandex - использовать YandexGPT\n"
        "/gigachat - использовать GigaChat\n"
        "/clear - очистить историю диалога\n\n"
        "Просто отправьте мне сообщение с вопросом"
    )
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/gigachat")],
        [KeyboardButton("/clear")]
    ]
    update.message.reply_text(
        text=help_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    )

def switch_to_yandex(update: Update, context: CallbackContext) -> None:
    if ai_assistant.set_provider("yandexgpt"):
        update.message.reply_text(
            f"✅ Переключено на YandexGPT ({ai_assistant.model})",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось переключиться на YandexGPT")

def switch_to_gigachat(update: Update, context: CallbackContext) -> None:
    if ai_assistant.set_provider("gigachat"):
        update.message.reply_text(
            f"✅ переключено на GigaChat ({ai_assistant.model})",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось переключиться на GigaChat")


def clear_history(update, context):
    if ai_assistant.clear_history():
        update.message.reply_text(
            f"🗑️ История диалога очищена!",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось очистить историю")

def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    if user_input.startswith("/"):
        return
    context.bot.send_chat_action(
        chat_id = update.effective_chat.id, # id текущего чата
        action="typing" # анимация печати
    )
    start_time = time.time()
    try:
        response = ai_assistant.generate_response(user_input)
        elapsed_time = time.time() - start_time
        formatted_response = (
            f"🤖 {ai_assistant.provider.upper()} отвечает:\n\n"
            f"{response}\n\n"
            f"⏱ Время генерации: {elapsed_time:.2f} сек"
        )
        update.message.reply_text(
            text=formatted_response,
            reply_markup=create_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {str(e)}")
        update.message.reply_text(
            "🚨 Произошла ошибка при генерации ответа. Попробуйте позже.",
            reply_markup=create_keyboard()
        )

def create_keyboard():
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/gigachat")],
        [KeyboardButton("/clear")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def main():
    if not os.getenv("YANDEX_API_KEY") and not os.getenv("GIGACHAT_API_KEY"):
        logger.error("Не найдены API-ключи! Проверьте .env файл")
        print("❌ ОШИБКА: Не найден ни один API ключ в .env файле!")
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("Не задан TELEGRAM_BOT_TOKEN в .env файле!")
        print("❌ ОШИБКА: Не задан TELEGRAM_BOT_TOKEN в .env файле!")
        return
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('yandex', switch_to_yandex))
    dispatcher.add_handler(CommandHandler('gigachat', switch_to_gigachat))
    dispatcher.add_handler(CommandHandler('clear', clear_history))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    logger.info("🤖 Российский AI-ассистент запущен и готов к работе!")
    print("Бот успешно запущен. Используйте /start в Telegram для начала работы.")
    updater.idle()

if __name__ == "__main__":
    main()
