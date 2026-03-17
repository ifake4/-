import telebot
from telebot import types
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ПОЛУЧАЕМ ТОКЕН ИЗ ПЕРЕМЕННОЙ ОКРУЖЕНИЯ (ВАЖНО!)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("КРИТИЧЕСКАЯ ОШИБКА: Токен не найден в переменных окружения!")
    logger.error("Добавьте TELEGRAM_TOKEN в Environment Variables на Render")
    # Для локального тестирования можно раскомментировать:
    # TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN_HERE'
else:
    logger.info(f"Токен загружен, длина: {len(TELEGRAM_TOKEN)}")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== ПОЛНАЯ БАЗА ЗНАНИЙ (50 ВОПРОСОВ) ==========
# (весь ваш код с вопросами остается здесь)
sections = [
    {
        "id": 1,
        "name": "📝 Прием на работу и оформление",
        "icon": "📝",
        "questions": [
            {
                "id": 101,
                "question": "В течение какого срока я должен подписать трудовой договор, если меня уже допустили до работы?",
                "answer": "Если вы фактически приступили к работе с ведома или по поручению работодателя, трудовой договор должен быть оформлен в письменной форме не позднее **3 рабочих дней** со дня фактического допущения к работе (ст. 67 ТК РФ)."
            },
            # ... остальные вопросы (я не стал копировать все для краткости, 
            # но вы должны оставить ВСЕ ваши вопросы из предыдущей версии)
        ]
    },
    # ... остальные разделы
]

# ========== КОНЕЦ БАЗЫ ЗНАНИЙ ==========

# Вспомогательные функции
def get_main_keyboard():
    """Создание главной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = []
    
    for section in sections:
        buttons.append(types.KeyboardButton(section["name"]))
    
    buttons.extend([
        types.KeyboardButton("📌 О проекте"),
        types.KeyboardButton("🔍 Поиск"),
        types.KeyboardButton("📞 Контакты")
    ])
    
    keyboard.add(*buttons)
    return keyboard

def get_sections_keyboard():
    """Клавиатура для выбора раздела"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for section in sections:
        keyboard.add(
            types.InlineKeyboardButton(
                section["name"], 
                callback_data=f"section_{section['id']}"
            )
        )
    
    keyboard.add(
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

def get_questions_keyboard(section_id: int, page: int = 0):
    """Клавиатура для вопросов раздела с пагинацией"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    section = next(
        (s for s in sections if s["id"] == section_id), 
        None
    )
    
    if not section:
        return keyboard
    
    questions = section.get("questions", [])
    
    if not questions:
        keyboard.add(
            types.InlineKeyboardButton("🔙 К разделам", callback_data="back_to_sections")
        )
        return keyboard
    
    questions_per_page = 5
    total_pages = (len(questions) + questions_per_page - 1) // questions_per_page
    
    start_idx = page * questions_per_page
    end_idx = min(start_idx + questions_per_page, len(questions))
    
    for i in range(start_idx, end_idx):
        q = questions[i]
        short_q = q["question"][:40] + "..." if len(q["question"]) > 40 else q["question"]
        keyboard.add(
            types.InlineKeyboardButton(
                f"{i+1}. {short_q}",
                callback_data=f"question_{q['id']}"
            )
        )
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            types.InlineKeyboardButton("◀️ Назад", callback_data=f"page_{section_id}_{page-1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            types.InlineKeyboardButton("Вперед ▶️", callback_data=f"page_{section_id}_{page+1}")
        )
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.add(
        types.InlineKeyboardButton("🔙 К разделам", callback_data="back_to_sections"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard

# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    welcome_text = f"""
👋 Здравствуйте, {user_name}!

Добро пожаловать в **Мини-базу знаний по трудовому праву** 📚

**Что вы найдете здесь:**
• 📝 Прием на работу и оформление
• ⏰ Рабочее время и отпуска
• 💰 Оплата труда и гарантии
• 🛡️ Дисциплина и защита прав
• 📋 Увольнение и выплаты

> ⚖️ *Информация носит справочный характер.*

Выберите интересующий раздел в меню ниже 👇
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "📌 О проекте")
def about_project(message):
    about_text = """
📌 **О проекте**

**Мини-база знаний по трудовому праву**

В базе знаний:
• **50+ ответов** на типовые вопросы
• 5 тематических разделов
• Ссылки на статьи ТК РФ

> ⚠️ *Бот носит информационный характер.*
    """
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def search_prompt(message):
    bot.send_message(
        message.chat.id,
        "🔍 **Поиск по вопросам**\n\nВведите ключевое слово:",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, search_questions)

def search_questions(message):
    query = message.text.lower()
    results = []
    
    for section in sections:
        for question in section.get("questions", []):
            if query in question["question"].lower() or query in question["answer"].lower():
                results.append((section["name"], question))
    
    if not results:
        bot.send_message(
            message.chat.id,
            f"😕 По запросу '{message.text}' ничего не найдено.",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = f"🔍 Найдено результатов: {len(results)}\n\n"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for i, (section_name, question) in enumerate(results[:10]):
        short_q = question["question"][:30] + "..." if len(question["question"]) > 30 else question["question"]
        keyboard.add(
            types.InlineKeyboardButton(
                f"{i+1}. [{section_name}] {short_q}",
                callback_data=f"question_{question['id']}"
            )
        )
    
    keyboard.add(
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "📞 Контакты")
def contacts(message):
    contacts_text = """
📞 **Контакты**

По вопросам работы бота:
📧 Email: support@trudpravo.ru

**Полезные ресурсы:**
• Онлайнинспекция.рф
• КонсультантПлюс
    """
    bot.send_message(message.chat.id, contacts_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_sections(message):
    text = message.text
    
    for section in sections:
        if text == section["name"]:
            show_section(message.chat.id, section["id"])
            return
    
    bot.send_message(
        message.chat.id,
        "Пожалуйста, выберите раздел из меню ниже 👇",
        reply_markup=get_main_keyboard()
    )

def show_section(chat_id: int, section_id: int, page: int = 0):
    section = next(
        (s for s in sections if s["id"] == section_id), 
        None
    )
    
    if not section:
        bot.send_message(chat_id, "Раздел не найден")
        return
    
    questions = section.get("questions", [])
    total_questions = len(questions)
    
    if total_questions == 0:
        bot.send_message(
            chat_id,
            f"{section['icon']} **{section['name']}**\n\nВ этом разделе пока нет вопросов.",
            parse_mode='Markdown',
            reply_markup=get_sections_keyboard()
        )
        return
    
    text = f"{section['icon']} **{section['name']}**\n"
    text += f"Всего вопросов: {total_questions}\n\n"
    text += "Выберите интересующий вопрос 👇"
    
    bot.send_message(
        chat_id,
        text,
        parse_mode='Markdown',
        reply_markup=get_questions_keyboard(section_id, page)
    )

# Обработчики callback
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        if call.data == "main_menu":
            bot.delete_message(chat_id, message_id)
            bot.send_message(
                chat_id,
                "🏠 Главное меню\nВыберите раздел:",
                reply_markup=get_main_keyboard()
            )
            
        elif call.data == "back_to_sections":
            bot.edit_message_text(
                "📚 Выберите раздел:",
                chat_id,
                message_id,
                reply_markup=get_sections_keyboard()
            )
            
        elif call.data.startswith("section_"):
            section_id = int(call.data.split("_")[1])
            show_section(chat_id, section_id)
            
        elif call.data.startswith("page_"):
            parts = call.data.split("_")
            section_id = int(parts[1])
            page = int(parts[2])
            
            section = next((s for s in sections if s["id"] == section_id), None)
            if section:
                text = f"{section['icon']} **{section['name']}**\nВыберите вопрос:"
                bot.edit_message_text(
                    text,
                    chat_id,
                    message_id,
                    parse_mode='Markdown',
                    reply_markup=get_questions_keyboard(section_id, page)
                )
                
        elif call.data.startswith("question_"):
            question_id = int(call.data.split("_")[1])
            
            found = False
            for section in sections:
                for question in section.get("questions", []):
                    if question["id"] == question_id:
                        found = True
                        answer_text = f"❓ **{question['question']}**\n\n📌 **Ответ:**\n{question['answer']}"
                        
                        answer_text += "\n\n---\n_Данная информация носит справочный характер._"
                        
                        section_id = section["id"]
                        
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(
                            types.InlineKeyboardButton("🔙 К списку вопросов", callback_data=f"section_{section_id}"),
                            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
                        )
                        
                        bot.edit_message_text(
                            answer_text,
                            chat_id,
                            message_id,
                            parse_mode='Markdown',
                            reply_markup=keyboard
                        )
                        break
                if found:
                    break
                
    except Exception as e:
        logger.error(f"Ошибка в callback: {e}")

# Класс для обработки health checks
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running')
    
    def log_message(self, format, *args):
        # Отключаем логирование запросов
        pass

def run_webserver():
    """Запуск веб-сервера для health checks"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"🌐 Веб-сервер запущен на порту {port}")
    server.serve_forever()

def run_bot():
    """Запуск бота"""
    logger.info("🤖 Бот запускается...")
    
    # Подсчитываем количество вопросов
    total_questions = 0
    for section in sections:
        total_questions += len(section.get("questions", []))
    logger.info(f"📊 Всего вопросов в базе: {total_questions}")
    
    # Проверяем токен
    if not TELEGRAM_TOKEN:
        logger.error("❌ Токен не найден! Бот не может запуститься.")
        return
    
    try:
        logger.info("✅ Бот успешно запущен и готов к работе!")
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"❌ Ошибка в polling: {e}")
        time.sleep(5)  # Пауза перед перезапуском

# Запуск
if __name__ == "__main__":
    logger.info("🚀 Запуск приложения...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем веб-сервер в основном потоке
    run_webserver()