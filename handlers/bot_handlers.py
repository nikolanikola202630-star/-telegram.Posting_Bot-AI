"""Обработчики команд и кнопок Telegram бота"""
import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from core import (
    get_channels, get_channel, add_channel, update_channel, 
    delete_channel, save_post_history, get_post_history, get_recent_posts
)
from core.ai_generator import get_generator
from core.telegram_client import get_telegram_client
from core.content_analyzer import get_analyzer

logger = logging.getLogger(__name__)

# Состояния пользователей
user_states = {}
generated_posts = {}

# Проверка админа
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

# Клавиатуры
MAIN_KEYBOARD = ReplyKeyboardMarkup([["📱 Мои каналы"], ["➕ Добавить канал"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа")
        return
    
    await update.message.reply_text(
        "👋 Добро пожаловать в бот управления постами!\n\n"
        "Используйте кнопки ниже для управления каналами.",
        reply_markup=MAIN_KEYBOARD
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    if not is_admin(user.id):
        return
    
    text = update.message.text
    
    # Главное меню
    if text == "📱 Мои каналы":
        await show_channels_list(update)
        return
    elif text == "➕ Добавить канал":
        user_states[user.id] = {'state': 'add_channel_name'}
        await update.message.reply_text("Введите название канала:")
        return
    
    # Обработка состояний
    state = user_states.get(user.id, {})
    
    if state.get('state') == 'add_channel_name':
        user_states[user.id]['name'] = text
        user_states[user.id]['state'] = 'add_channel_id'
        await update.message.reply_text("Введите ID канала (например, @channel или -1001234567890):")
        
    elif state.get('state') == 'add_channel_id':
        user_states[user.id]['id'] = text
        user_states[user.id]['state'] = 'add_channel_theme'
        await update.message.reply_text("Введите тематику канала (например: IT, Бизнес, Мотивация):")
        
    elif state.get('state') == 'add_channel_theme':
        name = user_states[user.id]['name']
        channel_id = user_states[user.id]['id']
        theme = text
        
        success = add_channel(channel_id, name, theme=theme)
        user_states[user.id] = {}
        
        if success:
            await update.message.reply_text(f"✅ Канал '{name}' добавлен!\nТематика: {theme}")
        else:
            await update.message.reply_text("❌ Ошибка добавления (возможно, канал уже существует)")
        
        await show_channels_list(update)
        
    elif state.get('state') == 'edit_prompt':
        channel_id = state['channel_id']
        update_channel(channel_id, {'prompt': text})
        user_states[user.id] = {}
        await update.message.reply_text("✅ Промпт обновлен!")
        await show_channel_settings(update, channel_id)
        
    elif state.get('state') == 'edit_theme':
        channel_id = state['channel_id']
        update_channel(channel_id, {'theme': text})
        user_states[user.id] = {}
        await update.message.reply_text("✅ Тематика обновлена!")
        await show_channel_settings(update, channel_id)
        
    elif state.get('state') == 'edit_times':
        channel_id = state['channel_id']
        times_list = [t.strip() for t in text.split(',')]
        valid_times = []
        
        for t in times_list:
            if ':' in t:
                try:
                    h, m = t.split(':')
                    h, m = int(h), int(m)
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        valid_times.append(f"{h:02d}:{m:02d}")
                except:
                    pass
        
        if valid_times:
            update_channel(channel_id, {'times': valid_times})
            user_states[user.id] = {}
            await update.message.reply_text(f"✅ Время установлено: {', '.join(valid_times)}")
            await show_channel_settings(update, channel_id)
        else:
            await update.message.reply_text("❌ Неверный формат. Используйте HH:MM,HH:MM")
            
    elif state.get('state') == 'edit_posts_count':
        channel_id = state['channel_id']
        try:
            count = int(text)
            if 1 <= count <= 24:
                update_channel(channel_id, {'posts_per_day': count})
                user_states[user.id] = {}
                await update.message.reply_text(f"✅ Количество постов: {count}")
                await show_channel_settings(update, channel_id)
            else:
                await update.message.reply_text("❌ Число должно быть от 1 до 24")
        except:
            await update.message.reply_text("❌ Введите число")

async def show_channels_list(update: Update):
    """Показать список каналов"""
    channels = get_channels()
    
    if not channels:
        keyboard = [[InlineKeyboardButton("➕ Добавить первый канал", callback_data='add_channel')]]
        await update.message.reply_text(
            "📱 У вас пока нет каналов",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    keyboard = []
    for ch in channels:
        status = "✅" if ch.get('enabled') else "❌"
        theme = ch.get('theme', 'Общая')
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {ch['name']} | {theme}",
                callback_data=f"channel_{ch['id']}"
            )
        ])
    
    await update.message.reply_text(
        f"📱 Ваши каналы ({len(channels)}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_channel_settings(update, channel_id: str):
    """Показать настройки канала"""
    channel = get_channel(channel_id)
    if not channel:
        message_text = "❌ Канал не найден"
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message_text)
        elif hasattr(update, 'message'):
            await update.message.reply_text(message_text)
        return
    
    times = ', '.join(channel.get('times', ['12:00']))
    status = "✅ Включен" if channel.get('enabled') else "❌ Выключен"
    
    text = (
        f"📱 {channel['name']}\n"
        f"ID: {channel['id']}\n"
        f"Тематика: {channel.get('theme', 'Общая')}\n"
        f"Статус: {status}\n"
        f"Постов в день: {channel.get('posts_per_day', 1)}\n"
        f"Время: {times}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎨 Генерировать пост", callback_data=f"gen_{channel_id}")],
        [InlineKeyboardButton("📊 Анализ канала", callback_data=f"analyze_{channel_id}")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data=f"settings_{channel_id}")],
        [InlineKeyboardButton("🗑️ Удалить канал", callback_data=f"delete_{channel_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_list")]
    ]
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    if not is_admin(user.id):
        await query.edit_message_text("❌ У вас нет доступа")
        return
    
    data = query.data
    
    if data == "back_list":
        channels = get_channels()
        keyboard = []
        for ch in channels:
            status = "✅" if ch.get('enabled') else "❌"
            theme = ch.get('theme', 'Общая')
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {ch['name']} | {theme}",
                    callback_data=f"channel_{ch['id']}"
                )
            ])
        await query.edit_message_text(
            f"📱 Ваши каналы ({len(channels)}):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data.startswith("channel_"):
        channel_id = data.replace("channel_", "")
        await show_channel_settings(update, channel_id)
        
    elif data.startswith("gen_"):
        channel_id = data.replace("gen_", "")
        channel = get_channel(channel_id)
        
        if channel:
            # Получаем историю и анализируем
            post_history = get_post_history(channel_id, limit=50)
            recent_posts = get_recent_posts(channel_id, days=7)
            
            analyzer = get_analyzer()
            generator = get_generator()
            
            # Анализ для улучшения промпта
            channel_stats = analyzer.analyze_channel_content(post_history)
            base_prompt = channel.get('prompt')
            theme = channel.get('theme')
            
            # Улучшаем промпт
            enhanced_prompt = analyzer.generate_unique_prompt(base_prompt, channel_stats, recent_posts)
            
            await query.edit_message_text("⏳ Генерирую уникальный пост...")
            
            # Попытки генерации
            max_attempts = 3
            post = None
            
            for attempt in range(max_attempts):
                post = generator.generate_post(enhanced_prompt, theme)
                
                if not post:
                    continue
                
                # Проверка на дубликаты
                is_duplicate, _ = analyzer.is_duplicate(post, recent_posts)
                
                if not is_duplicate:
                    break
                else:
                    enhanced_prompt += f"\n\nПОПЫТКА {attempt + 2}: Создай СОВЕРШЕННО ДРУГОЙ пост!"
                    post = None
            
            if post:
                generated_posts[user.id] = {'channel_id': channel_id, 'post': post}
                
                # Проверяем уникальность
                is_dup, _ = analyzer.is_duplicate(post, recent_posts)
                uniqueness = "✅ Уникальный" if not is_dup else "⚠️ Возможно похож"
                
                keyboard = [
                    [InlineKeyboardButton("🚀 Опубликовать", callback_data=f"publish_{channel_id}")],
                    [InlineKeyboardButton("🔄 Сгенерировать еще", callback_data=f"gen_{channel_id}")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data=f"channel_{channel_id}")]
                ]
                await query.edit_message_text(
                    f"📝 Сгенерированный пост ({uniqueness}):\n\n{post}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text("❌ Не удалось сгенерировать уникальный пост. Попробуйте еще раз.")
                
    elif data.startswith("analyze_"):
        channel_id = data.replace("analyze_", "")
        channel = get_channel(channel_id)
        
        if channel:
            # Получаем историю постов
            post_history = get_post_history(channel_id, limit=100)
            
            if not post_history:
                await query.edit_message_text(
                    f"📊 Анализ канала {channel['name']}\n\n"
                    "Пока нет опубликованных постов для анализа.\n"
                    "Опубликуйте несколько постов, чтобы увидеть статистику.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f"channel_{channel_id}")]])
                )
                return
            
            # Анализируем контент
            analyzer = get_analyzer()
            stats = analyzer.analyze_channel_content(post_history)
            
            # Формируем отчет
            report = f"📊 Анализ канала {channel['name']}\n\n"
            report += f"📝 Всего постов: {stats['total_posts']}\n"
            report += f"✨ Уникальных: {stats['unique_posts']}\n"
            report += f"📈 Уникальность: {(1 - stats['duplicate_rate']) * 100:.1f}%\n"
            report += f"📏 Средняя длина: {stats['avg_post_length']} символов\n\n"
            
            if stats['common_keywords']:
                report += f"🔑 Частые темы:\n"
                for i, keyword in enumerate(stats['common_keywords'][:5], 1):
                    report += f"{i}. {keyword}\n"
            
            report += f"\n💡 Рекомендация: "
            if stats['duplicate_rate'] > 0.3:
                report += "Высокий процент повторений. Попробуйте разнообразить темы постов."
            elif stats['duplicate_rate'] > 0.1:
                report += "Умеренное разнообразие. Можно добавить больше уникальных тем."
            else:
                report += "Отличное разнообразие контента! Продолжайте в том же духе."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data=f"analyze_{channel_id}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data=f"channel_{channel_id}")]
            ]
            
            await query.edit_message_text(report, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("publish_"):
        channel_id = data.replace("publish_", "")
        post_data = generated_posts.get(user.id)
        
        if post_data and post_data['channel_id'] == channel_id:
            telegram = get_telegram_client()
            success = await telegram.send_post(channel_id, post_data['post'])
            
            if success:
                save_post_history(channel_id, post_data['post'], 'published')
                await query.edit_message_text("✅ Пост опубликован!")
            else:
                save_post_history(channel_id, post_data['post'], 'failed')
                await query.edit_message_text("❌ Ошибка публикации")
        else:
            await query.edit_message_text("❌ Сначала сгенерируйте пост")
            
    elif data.startswith("settings_"):
        channel_id = data.replace("settings_", "")
        channel = get_channel(channel_id)
        
        if channel:
            keyboard = [
                [InlineKeyboardButton("✏️ Изменить промпт", callback_data=f"edit_prompt_{channel_id}")],
                [InlineKeyboardButton("🎨 Изменить тематику", callback_data=f"edit_theme_{channel_id}")],
                [InlineKeyboardButton("⏰ Изменить время", callback_data=f"edit_times_{channel_id}")],
                [InlineKeyboardButton("🔢 Постов в день", callback_data=f"edit_posts_{channel_id}")],
                [InlineKeyboardButton(
                    "🎛️ " + ("Выключить" if channel.get('enabled') else "Включить"),
                    callback_data=f"toggle_{channel_id}"
                )],
                [InlineKeyboardButton("⬅️ Назад", callback_data=f"channel_{channel_id}")]
            ]
            await query.edit_message_text(
                f"⚙️ Настройки канала {channel['name']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    elif data.startswith("edit_prompt_"):
        channel_id = data.replace("edit_prompt_", "")
        user_states[user.id] = {'state': 'edit_prompt', 'channel_id': channel_id}
        await query.edit_message_text("Введите новый промпт для генерации постов:")
        
    elif data.startswith("edit_theme_"):
        channel_id = data.replace("edit_theme_", "")
        user_states[user.id] = {'state': 'edit_theme', 'channel_id': channel_id}
        await query.edit_message_text("Введите новую тематику:")
        
    elif data.startswith("edit_times_"):
        channel_id = data.replace("edit_times_", "")
        user_states[user.id] = {'state': 'edit_times', 'channel_id': channel_id}
        await query.edit_message_text("Введите время публикаций через запятую (HH:MM,HH:MM):")
        
    elif data.startswith("edit_posts_"):
        channel_id = data.replace("edit_posts_", "")
        user_states[user.id] = {'state': 'edit_posts_count', 'channel_id': channel_id}
        await query.edit_message_text("Введите количество постов в день (1-24):")
        
    elif data.startswith("toggle_"):
        channel_id = data.replace("toggle_", "")
        channel = get_channel(channel_id)
        
        if channel:
            new_status = not channel.get('enabled')
            update_channel(channel_id, {'enabled': new_status})
            await query.answer(f"✅ Канал {'включен' if new_status else 'выключен'}")
            await show_channel_settings(update, channel_id)
            
    elif data.startswith("delete_"):
        channel_id = data.replace("delete_", "")
        channel = get_channel(channel_id)
        
        if channel:
            keyboard = [
                [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{channel_id}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"channel_{channel_id}")]
            ]
            await query.edit_message_text(
                f"⚠️ Удалить канал '{channel['name']}'?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    elif data.startswith("confirm_delete_"):
        channel_id = data.replace("confirm_delete_", "")
        delete_channel(channel_id)
        await query.edit_message_text("✅ Канал удален")
