"""Cron задача для автопубликации (Vercel Cron Jobs)"""
import os
import sys
import json
import logging
import asyncio
import nest_asyncio
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# Применяем nest_asyncio
nest_asyncio.apply()

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import get_channels, save_post_history, update_channel, get_post_history, get_recent_posts
from core.ai_generator import get_generator
from core.telegram_client import get_telegram_client
from core.content_analyzer import get_analyzer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Флаг инициализации
_initialized = False

def ensure_initialized():
    """Ленивая инициализация БД"""
    global _initialized
    if not _initialized:
        try:
            from core import init_db
            init_db()
            logger.info("✅ База данных инициализирована")
            _initialized = True
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации БД: {e}")

async def auto_publish():
    """Автопубликация постов"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    published = []
    errors = []
    
    try:
        generator = get_generator()
        telegram = get_telegram_client()
        analyzer = get_analyzer()
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        return {
            'time': current_time,
            'published': [],
            'errors': [f"Ошибка инициализации: {str(e)}"]
        }
    
    channels = get_channels()
    logger.info(f"Проверка автопубликации в {current_time}, каналов: {len(channels)}")
    
    for channel in channels:
        if not channel.get('enabled'):
            logger.debug(f"Канал {channel.get('name')} выключен")
            continue
        
        times = channel.get('times', [])
        if current_time not in times:
            logger.debug(f"Канал {channel.get('name')}: время {current_time} не в расписании {times}")
            continue
        
        try:
            # Получение истории постов канала
            post_history = get_post_history(channel['id'], limit=50)
            recent_posts = get_recent_posts(channel['id'], days=7)
            
            # Анализ контента канала
            channel_stats = analyzer.analyze_channel_content(post_history)
            logger.info(f"Статистика канала {channel['name']}: {channel_stats['unique_posts']}/{channel_stats['total_posts']} уникальных постов")
            
            # Генерация поста с учетом анализа
            base_prompt = channel.get('prompt', 'Напиши интересный пост')
            theme = channel.get('theme')
            
            # Улучшаем промпт для уникальности
            enhanced_prompt = analyzer.generate_unique_prompt(base_prompt, channel_stats, recent_posts)
            
            logger.info(f"Генерация уникального поста для {channel['name']}")
            
            # Попытки генерации уникального поста
            max_attempts = 3
            post = None
            
            for attempt in range(max_attempts):
                post = generator.generate_post(enhanced_prompt, theme)
                
                if not post:
                    logger.error(f"Попытка {attempt + 1}: Не удалось сгенерировать пост")
                    continue
                
                # Проверка на дубликаты
                is_duplicate, similar_post = analyzer.is_duplicate(post, recent_posts)
                
                if not is_duplicate:
                    logger.info(f"✅ Сгенерирован уникальный пост (попытка {attempt + 1})")
                    break
                else:
                    logger.warning(f"⚠️ Попытка {attempt + 1}: Пост слишком похож на предыдущий")
                    enhanced_prompt += f"\n\nПОПЫТКА {attempt + 2}: Создай СОВЕРШЕННО ДРУГОЙ пост, не похожий на предыдущие!"
                    post = None
            
            if not post:
                error_msg = f"Не удалось сгенерировать уникальный пост для {channel['name']} за {max_attempts} попыток"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
            
            # Публикация
            logger.info(f"Публикация в {channel['name']}")
            success = await telegram.send_post(channel['id'], post)
            
            if success:
                save_post_history(channel['id'], post, 'published')
                update_channel(channel['id'], {'last_post_at': now.isoformat()})
                published.append(channel['name'])
                logger.info(f"✅ Опубликовано в {channel['name']}")
            else:
                save_post_history(channel['id'], post, 'failed')
                error_msg = f"Ошибка публикации в {channel['name']}"
                logger.error(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Ошибка для канала {channel.get('name', 'Unknown')}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    result = {
        'time': current_time,
        'published': published,
        'errors': errors,
        'total_channels': len(channels)
    }
    logger.info(f"Результат автопубликации: {result}")
    return result

class handler(BaseHTTPRequestHandler):
    """Vercel cron handler (WSGI-style)"""
    
    def do_GET(self):
        """Обработка cron задачи"""
        try:
            # Инициализация при первом запросе
            ensure_initialized()
            
            # Создаем новый event loop для каждого запроса
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(auto_publish())
            finally:
                loop.close()
            
            # Отправка ответа
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка cron: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            error_response = json.dumps({'error': str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8'))

