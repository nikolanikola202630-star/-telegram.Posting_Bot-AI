import os
import time
import nest_asyncio
import sqlite3
import schedule
import json
from dotenv import load_dotenv
from groq import Groq
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters


nest_asyncio.apply()

# Функции для работы с БД
def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    # Глобальные настройки
    cursor.execute('''CREATE TABLE IF NOT EXISTS configs (
                        key TEXT PRIMARY KEY, 
                        value TEXT)''')
    # Каналы Telegram
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_channel_id TEXT,
                        name TEXT,
                        enabled BOOLEAN DEFAULT 1,
                        posts_per_day INTEGER DEFAULT 1,
                        times_json TEXT,  -- JSON array of times ["09:00", "15:00"]
                        prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_post_at TIMESTAMP)''')
    # История постов
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id INTEGER,
                        platform TEXT,  -- 'telegram' or 'threads'
                        post_text TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'published') -- published, failed, etc.
    ''')
    conn.commit()
    conn.close()

def load_default_prompt():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM configs WHERE key = 'default_prompt'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Напиши интересный пост для Telegram канала. Пост должен быть вдохновляющим."

def save_default_prompt(prompt):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configs (key, value) VALUES ('default_prompt', ?)", (prompt,))
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels")
    channels = cursor.fetchall()
    conn.close()
    return channels

def get_channel(channel_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels WHERE telegram_channel_id = ?", (channel_id,))
    channel = cursor.fetchone()
    conn.close()
    return channel

def add_channel(telegram_channel_id, name, posts_per_day=1, times_json='["12:00"]', prompt=None):
    if not prompt:
        prompt = load_default_prompt()
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO channels 
                     (telegram_channel_id, name, posts_per_day, times_json, prompt) 
                     VALUES (?, ?, ?, ?, ?)""", 
                   (telegram_channel_id, name, posts_per_day, times_json, prompt))
    conn.commit()
    conn.close()

def update_channel(channel_id, updates):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    cursor.execute(f"UPDATE channels SET {set_clause} WHERE telegram_channel_id = ?", 
                   list(updates.values()) + [channel_id])
    conn.commit()
    conn.close()

def save_post_history(channel_id, platform, post_text, status='published'):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts_history (channel_id, platform, post_text, status) VALUES (?, ?, ?, ?)", 
                   (channel_id, platform, post_text, status))
    conn.commit()
    conn.close()

# Глобальное состояние
user_states = {}  # user_id -> {'state': 'select_channel', 'data': {}}
generated_posts = {}  # user_id -> {'telegram': post_text, 'threads': post_text}

# Главная клавиатура
MAIN_KEYBOARD = ReplyKeyboardMarkup([["📱 Telegram каналы"], ["📷 Threads генерация"]], resize_keyboard=True)

# Загрузка переменных окружения
load_dotenv()

# Получение переменных
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_PROMPT = os.getenv("POST_PROMPT")
POST_FREQUENCY = int(os.getenv("POST_FREQUENCY", 1))
POST_TIME = os.getenv("POST_TIME", "12:00")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

# Проверка наличия необходимых переменных
if not all([TELEGRAM_BOT_TOKEN, GROQ_API_KEY, CHANNEL_ID, POST_PROMPT, ADMIN_USER_ID]):
    print("Ошибка: Не все переменные окружения установлены. Проверьте .env файл.")
    exit(1)

try:
    ADMIN_USER_ID = int(ADMIN_USER_ID)
except ValueError:
    print("ADMIN_USER_ID должно быть числом. Получите его через @userinfobot.")
    exit(1)

# Инициализация БД
init_db()
POST_PROMPT = load_default_prompt()  # Загружаем сохраненный промпт

# Инициализация клиентов
groq_client = Groq(api_key=GROQ_API_KEY)
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Глобальные переменные
generated_post = None
changing_prompt = False

def is_admin(user_id):
    return user_id == ADMIN_USER_ID

def generate_post(prompt):
    """Генерация поста через GroqCloud"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Другие модели: llama3-8b-8192, llama-3.1-70b-versatile
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка генерации поста: {e}")
        import traceback
        traceback.print_exc()
        return None

async def send_post_to_telegram(post):
    """Отправка поста в Telegram канал"""
    try:
        await telegram_bot.send_message(chat_id=CHANNEL_ID, text=post, parse_mode="Markdown")
        print("Пост успешно опубликован в Telegram!")
        return True
    except Exception as e:
        print(f"Ошибка отправки поста с Markdown: {e}")
        try:
            # Попытка без parse_mode
            await telegram_bot.send_message(chat_id=CHANNEL_ID, text=post)
            return True
        except Exception as e2:
            print(f"Ошибка отправки поста в Telegram: {e2}")
            return False

async def send_main_menu(query):
    """Главное меню бота"""
    keyboard = [
        [InlineKeyboardButton("📱 Telegram каналы", callback_data='telegram_main')],
        [InlineKeyboardButton("📷 Threads генерация", callback_data='threads_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('🔧 Управление постами - выберите платформу:', reply_markup=reply_markup)

async def send_telegram_menu(query):
    """Меню Telegram"""
    channels = get_channels()
    keyboard = []
    for ch in channels:
        status = "✅" if ch[3] else "❌"  # enabled
        keyboard.append([InlineKeyboardButton(f"{status} {ch[2]} (@{ch[1]})", callback_data=f'telegram_channel_{ch[1]}')])
    keyboard.append([InlineKeyboardButton("➕ Добавить канал", callback_data='telegram_add_channel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('📱 Выберите канал или добавьте новый:', reply_markup=reply_markup)

async def send_post_to_telegram_channel(post, channel_id):
    """Отправка поста в Telegram канал по ID"""
    try:
        await telegram_bot.send_message(chat_id=channel_id, text=post, parse_mode="Markdown")
        print(f"Пост успешно опубликован в {channel_id}!")
        return True
    except Exception as e:
        print(f"Ошибка отправки поста в {channel_id}: {e}")
        try:
            # Попытка без parse_mode
            await telegram_bot.send_message(chat_id=channel_id, text=post)
            return True
        except Exception as e2:
            print(f"Ошибка отправки поста в {channel_id}: {e2}")
            return False

async def send_telegram_menu_message(update: Update):
    """Меню Telegram для message update"""
    channels = get_channels()
    keyboard = []
    for ch in channels:
        status = "✅" if ch[3] else "❌"  # enabled
        keyboard.append([InlineKeyboardButton(f"{status} {ch[2]} (@{ch[1]})", callback_data=f'telegram_channel_{ch[1]}')])
    keyboard.append([InlineKeyboardButton("➕ Добавить канал", callback_data='telegram_add_channel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('📱 Выберите канал или добавьте новый:', reply_markup=reply_markup)

async def send_threads_menu(update_or_query):
    """Меню Threads"""
    keyboard = [
        [InlineKeyboardButton("🎨 Сгенерировать пост", callback_data='threads_generate')],
        [InlineKeyboardButton("✏️ Изменить промт", callback_data='threads_change_prompt')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_obj = update_or_query.message
    if isinstance(update_or_query, CallbackQuery):
        await message_obj.edit_text('📷 Генерация постов для Threads:', reply_markup=reply_markup)
    else:
        await message_obj.reply_text('📷 Генерация постов для Threads:', reply_markup=reply_markup)

async def handle_text(update: Update, context):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    if not is_admin(user.id):
        return

    global changing_prompt

    # Handle main keyboard buttons
    if update.message.text == "📱 Telegram каналы":
        await send_telegram_menu_message(update)
        return
    elif update.message.text == "📷 Threads генерация":
        await send_threads_menu(update)
        return

    state = user_states.get(user.id, {})
    if state.get('state') == 'changing_prompt':
        new_prompt = update.message.text
        if state['platform'] == 'telegram':
            POST_PROMPT = new_prompt
            save_default_prompt(new_prompt)
            await update.message.reply_text(f"Промт для {state['platform']} обновлен: {new_prompt}")
        elif state['platform'] == 'telegram_channel':
            channel_id_db = state.get('channel_id_db')
            if channel_id_db:
                channels = get_channels()
                channel = next((c for c in channels if c[0] == channel_id_db), None)
                if channel:
                    update_channel(channel[1], {'prompt': new_prompt})
                    await update.message.reply_text(f"Промт для канала {channel[2]} обновлен!")
                else:
                    await update.message.reply_text("Канал не найден.")
        elif state['platform'] == 'threads':
            # Save threads prompt
            conn = sqlite3.connect('bot.db')
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO configs (key, value) VALUES ('threads_prompt', ?)", (new_prompt,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"Промт для {state['platform']} обновлен: {new_prompt}")
        user_states[user.id] = {}
        # Return to menu
        if state['platform'] in ('telegram', 'telegram_channel'):
            await send_telegram_menu_message(update)
        elif state['platform'] == 'threads':
            await send_threads_menu(update)
    elif state.get('state') == 'changing_time':
        # Parse times
        times_input = update.message.text.strip()
        times_list = [t.strip() for t in times_input.split(',') if t.strip()]
        # Validate format HH:MM
        valid_times = []
        for t in times_list:
            if ':' in t and len(t.split(':')) == 2:
                h, m = t.split(':')
                try:
                    h, m = int(h), int(m)
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        valid_times.append(f"{h:02d}:{m:02d}")
                except:
                    pass
        if valid_times:
            channel_id_db = state.get('channel_id_db')
            if channel_id_db:
                channels = get_channels()
                channel = next((c for c in channels if c[0] == channel_id_db), None)
                if channel:
                    update_channel(channel[1], {'times_json': json.dumps(valid_times)})
                    await update.message.reply_text(f"Время публикаций для канала {channel[2]} установлено: {', '.join(valid_times)}")
                else:
                    await update.message.reply_text("Канал не найден.")
        else:
            await update.message.reply_text("Неверный формат времени. Введи через запятую HH:MM,HH:MM")
        user_states[user.id] = {}
        await send_telegram_menu_message(update)
    elif state.get('state') == 'changing_posts':
        try:
            posts_count = int(update.message.text.strip())
            if 1 <= posts_count <= 24:
                channel_id_db = state.get('channel_id_db')
                if channel_id_db:
                    channels = get_channels()
                    channel = next((c for c in channels if c[0] == channel_id_db), None)
                    if channel:
                        update_channel(channel[1], {'posts_per_day': posts_count})
                        await update.message.reply_text(f"Количество постов для канала {channel[2]} установлено: {posts_count}")
                    else:
                        await update.message.reply_text("Канал не найден.")
                user_states[user.id] = {}
                await send_telegram_menu_message(update)
            else:
                await update.message.reply_text("Количество должно быть от 1 до 24.")
        except ValueError:
            await update.message.reply_text("Неверное число. Введи целое число от 1 до 24.")
    elif state.get('state') == 'add_channel_name':
        user_states[user.id]['new_channel_name'] = update.message.text
        user_states[user.id]['state'] = 'add_channel_id'
        await update.message.reply_text("Теперь введите ID канала (например, -1001234567890):")
    elif state.get('state') == 'add_channel_id':
        channel_id = update.message.text
        add_channel(channel_id, user_states[user.id]['new_channel_name'])
        user_states[user.id] = {}
        await update.message.reply_text("Канал добавлен! ✅")
        await send_telegram_menu(update)

async def start(update: Update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("У вас нет доступа к админ панели.")
        return
    await update.message.reply_text("Добро пожаловать! Используйте кнопки внизу:", reply_markup=MAIN_KEYBOARD)

async def button(update: Update, context):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if not is_admin(user.id):
        await query.edit_message_text(text="У вас нет доступа.")
        return

    # Initialize user data
    if user.id not in generated_posts:
        generated_posts[user.id] = {}
    if user.id not in user_states:
        user_states[user.id] = {}

    if query.data == 'telegram_main':
        await send_telegram_menu(query)
    elif query.data == 'threads_main':
        await send_threads_menu(query)
    elif query.data == 'back_main':
        await send_main_menu(query)
    elif query.data.startswith('telegram_channel_'):
        channel_id = query.data.split('telegram_channel_')[1]
        channel = get_channel(channel_id)
        if channel:
            # Send channel management menu
            keyboard = [
                [InlineKeyboardButton("🎨 Генерировать пост", callback_data=f'channel_generate_{channel[0]}')],
                [InlineKeyboardButton("🚀 Опубликовать пост", callback_data=f'channel_publish_{channel[0]}')],
                [InlineKeyboardButton("⚙️ Настройки", callback_data=f'channel_settings_{channel[0]}')],
                [InlineKeyboardButton("⬅️ Назад", callback_data='telegram_main')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            status = "✅ Вкл" if channel[3] else "❌ Выкл"
            await query.edit_message_text(text=f"📱 Канал {channel[2]} ({channel[1]})\nСтатус: {status}\nПостов в день: {channel[4]}\nВремя: {json.loads(channel[5]) if channel[5] else []}", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="Канал не найден.")
    elif query.data == 'telegram_add_channel':
        user_states[user.id] = {'state': 'add_channel_name', 'data': {}}
        await query.edit_message_text(text="Введите название нового канала:")
    elif query.data == 'threads_generate':
        threads_prompt = "Напиши короткий и креативный пост для Threads (Instagram). Сделай его модным и фото-дружественным."  # default
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configs WHERE key = 'threads_prompt'")
        row = cursor.fetchone()
        if row:
            threads_prompt = row[0]
        conn.close()
        
        post = generate_post(threads_prompt)
        if post:
            generated_posts[user.id]['threads'] = post
            keyboard = [
                [InlineKeyboardButton("⚡ Скопировать", callback_data='threads_copy') if post else []],
                [InlineKeyboardButton("⬅️ Назад", callback_data='threads_main')],
            ]
            # Filter empty buttons
            keyboard = [btn for btn in keyboard if btn]
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await query.edit_message_text(text=f"📷 Пост для Threads:\n\n{post}\n\nГотово для публикации!", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="Не удалось сгенерировать пост для Threads.")
    elif query.data == 'threads_copy':
        if 'threads' in generated_posts.get(user.id, {}):
            post_text = generated_posts[user.id]['threads']
            await query.edit_message_text(text=f"Ваш пост:\n\n{post_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='threads_main')]]))
        else:
            await query.edit_message_text(text="Нет сгенерированного поста. Сначала сгенерируйте.")
    elif query.data == 'threads_change_prompt':
        user_states[user.id] = {'state': 'changing_prompt', 'platform': 'threads'}
        await query.edit_message_text(text="Отправьте новый промт для Threads в виде текста:")
    elif query.data.startswith('channel_generate_'):
        channel_id_db = int(query.data.split('channel_generate_')[1])
        # Get channel prompt
        all_ch = get_channels()
        channel = next((c for c in all_ch if c[0] == channel_id_db), None)
        if channel:
            prompt = channel[6]  # prompt column
            post = generate_post(prompt)
            if post:
                generated_posts[user.id]['telegram'] = post
                await query.edit_message_text(text=f"📱 Пост для канала {channel[2]}:\n\n{post}\n\nТеперь можно опубликовать.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'telegram_channel_{channel[1]}')]]))
            else:
                await query.edit_message_text(text="Не удалось сгенерировать пост.")
    elif query.data.startswith('channel_publish_'):
        channel_id_db = int(query.data.split('channel_publish_')[1])
        if 'telegram' in generated_posts.get(user.id, {}):
            post = generated_posts[user.id]['telegram']
            all_ch = get_channels()
            channel = next((c for c in all_ch if c[0] == channel_id_db), None)
            if channel:
                success = await send_post_to_telegram_channel(post, channel[1])
                updates = {'last_post_at': int(time.time())}
                if success:
                    await query.edit_message_text(text=f"📱 Пост опубликован в {channel[2]}! ✅")
                    save_post_history(channel_id_db, 'telegram', post, 'published')
                else:
                    updates['last_post_at'] = None
                    await query.edit_message_text(text="Ошибка публикации в канал.")
                update_channel(channel[1], updates)
            else:
                await query.edit_message_text(text="Канал не найден.")
        else:
            await query.edit_message_text(text="Сначала сгенерируйте пост.")
    elif query.data.startswith('channel_settings_'):
        channel_id_db = int(query.data.split('channel_settings_')[1])
        all_ch = get_channels()
        channel = next((c for c in all_ch if c[0] == channel_id_db), None)
        if channel:
            settings_keyboard = [
                [InlineKeyboardButton("✏️ Промт канала", callback_data=f'settings_prompt_{channel_id_db}')],
                [InlineKeyboardButton(f"⏰ Время (текущий: {channel[5]})", callback_data=f'settings_time_{channel_id_db}')],
                [InlineKeyboardButton(f"🔢 Постов в день ({channel[4]})", callback_data=f'settings_posts_{channel_id_db}')],
                [InlineKeyboardButton("🎛️ Автопостинг " + ("✅ Вкл" if channel[3] else "❌ Выкл"), callback_data=f'settings_auto_{channel_id_db}')],
                [InlineKeyboardButton("⬅️ Назад", callback_data=f'telegram_channel_{channel[1]}')]]
            await query.edit_message_text(text=f"Настройки канала {channel[2]}", reply_markup=InlineKeyboardMarkup(settings_keyboard))
        else:
            await query.edit_message_text(text="Канал не найден.")
    elif query.data.startswith('settings_prompt_'):
        channel_id_db = int(query.data.split('settings_prompt_')[1])
        user_states[user.id] = {'state': 'changing_prompt', 'platform': 'telegram_channel', 'channel_id_db': channel_id_db}
        await query.edit_message_text(text="Отправьте новый промт для канала:")
    elif query.data.startswith('settings_time_'):
        channel_id_db = int(query.data.split('settings_time_')[1])
        user_states[user.id] = {'state': 'changing_time', 'channel_id_db': channel_id_db}
        await query.edit_message_text(text="Введи время публикаций через запятую (HH:MM,HH:MM):")
    elif query.data.startswith('settings_posts_'):
        channel_id_db = int(query.data.split('settings_posts_')[1])
        user_states[user.id] = {'state': 'changing_posts', 'channel_id_db': channel_id_db}
        await query.edit_message_text(text="Введи количество постов в день (1-24):")
    elif query.data.startswith('settings_auto_'):
        channel_id_db = int(query.data.split('settings_auto_')[1])
        all_ch = get_channels()
        channel = next((c for c in all_ch if c[0] == channel_id_db), None)
        if channel:
            new_enabled = 0 if channel[3] else 1
            update_channel(channel[1], {'enabled': new_enabled})
            await query.edit_message_text(text=f"Автопостинг {'включен' if new_enabled else 'отключен'} для канала {channel[2]}!")
        else:
            await query.edit_message_text(text="Канал не найден.")
    # Add more handlers for settings, etc.
    else:
        await query.edit_message_text(text="Неизвестная команда.")

async def auto_publish():
    """Автоматическая публикация постов"""
    global POST_PROMPT
    print("Выполнение автопубликации...")
    post = generate_post(POST_PROMPT)
    if post:
        success = await send_post_to_telegram(post)
        print(f"Автопубликация завершена: {'успешно' if success else 'ошибка'}")
    else:
        print("Не удалось сгенерировать пост для автопубликации")

async def scheduler_loop():
    """Цикл для scheduler"""
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

async def main():
    """Запуск бота"""
    print("Запуск бота для управления генерацией и публикацией постов...")

    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button))

    # Настройка автопубликации
    print(f"Автопубликация запланирована на {POST_TIME} по местному времени ежедневно")
    schedule.every().day.at(POST_TIME).do(lambda: asyncio.create_task(auto_publish()))
    asyncio.create_task(scheduler_loop())

    # Запуск polling
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
