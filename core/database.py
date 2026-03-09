"""Модуль для работы с базой данных"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Используем in-memory хранилище для Vercel (можно заменить на PostgreSQL/Redis)
_channels_store = {}
_posts_history = []
_configs = {}

def init_db():
    """Инициализация базы данных"""
    logger.info("База данных инициализирована (in-memory)")

def get_channels() -> List[Dict]:
    """Получение всех каналов"""
    return list(_channels_store.values())

def get_channel(channel_id: str) -> Optional[Dict]:
    """Получение канала по ID"""
    return _channels_store.get(channel_id)

def add_channel(telegram_channel_id: str, name: str, posts_per_day: int = 1, 
                times: List[str] = None, prompt: str = None, theme: str = None) -> bool:
    """Добавление нового канала"""
    if telegram_channel_id in _channels_store:
        logger.warning(f"Канал {telegram_channel_id} уже существует")
        return False
    
    if times is None:
        times = ["12:00"]
    
    if prompt is None:
        prompt = "Напиши интересный пост для Telegram канала."
    
    _channels_store[telegram_channel_id] = {
        'id': telegram_channel_id,
        'name': name,
        'enabled': True,
        'posts_per_day': posts_per_day,
        'times': times,
        'prompt': prompt,
        'theme': theme or 'Общая тематика',
        'created_at': datetime.now().isoformat(),
        'last_post_at': None
    }
    
    logger.info(f"Канал {name} добавлен")
    return True

def update_channel(channel_id: str, updates: Dict) -> bool:
    """Обновление настроек канала"""
    if channel_id not in _channels_store:
        logger.error(f"Канал {channel_id} не найден")
        return False
    
    _channels_store[channel_id].update(updates)
    logger.info(f"Канал {channel_id} обновлен")
    return True

def delete_channel(channel_id: str) -> bool:
    """Удаление канала"""
    if channel_id in _channels_store:
        del _channels_store[channel_id]
        logger.info(f"Канал {channel_id} удален")
        return True
    return False

def save_post_history(channel_id: str, post_text: str, status: str = 'published'):
    """Сохранение истории постов"""
    _posts_history.append({
        'channel_id': channel_id,
        'post_text': post_text,
        'status': status,
        'timestamp': datetime.now().isoformat()
    })
    logger.info(f"История поста сохранена для {channel_id}")

def get_post_history(channel_id: str, limit: int = 50) -> List[Dict]:
    """Получение истории постов канала"""
    channel_posts = [
        post for post in _posts_history 
        if post['channel_id'] == channel_id and post['status'] == 'published'
    ]
    # Сортируем по времени (новые первые)
    channel_posts.sort(key=lambda x: x['timestamp'], reverse=True)
    return channel_posts[:limit]

def get_recent_posts(channel_id: str, days: int = 7) -> List[str]:
    """Получение текстов последних постов за N дней"""
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    recent = []
    for post in _posts_history:
        if post['channel_id'] == channel_id and post['status'] == 'published':
            post_date = datetime.fromisoformat(post['timestamp'])
            if post_date >= cutoff_date:
                recent.append(post['post_text'])
    
    return recent

def get_config(key: str, default: str = None) -> Optional[str]:
    """Получение конфигурации"""
    return _configs.get(key, default)

def set_config(key: str, value: str):
    """Сохранение конфигурации"""
    _configs[key] = value
    logger.info(f"Конфиг {key} сохранен")
