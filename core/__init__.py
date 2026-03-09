"""Core модули бота"""
import os

# Выбор базы данных в зависимости от наличия DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Используем PostgreSQL
    from .database_pg import (
        init_db, get_channels, get_channel, add_channel, 
        update_channel, delete_channel, save_post_history,
        get_config, set_config, get_post_history, get_recent_posts
    )
else:
    # Используем in-memory
    from .database import (
        init_db, get_channels, get_channel, add_channel, 
        update_channel, delete_channel, save_post_history,
        get_config, set_config, get_post_history, get_recent_posts
    )

from .ai_generator import get_generator
from .telegram_client import get_telegram_client
from .content_analyzer import get_analyzer

__all__ = [
    'init_db', 'get_channels', 'get_channel', 'add_channel',
    'update_channel', 'delete_channel', 'save_post_history',
    'get_config', 'set_config', 'get_post_history', 'get_recent_posts',
    'get_generator', 'get_telegram_client', 'get_analyzer'
]
