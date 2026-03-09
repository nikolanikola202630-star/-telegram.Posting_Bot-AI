"""Модуль для работы с PostgreSQL (Supabase)"""
import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Получение подключения к БД"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise

def init_db():
    """Инициализация базы данных"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Таблица конфигураций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица каналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                posts_per_day INTEGER DEFAULT 1,
                times JSONB DEFAULT '["12:00"]'::jsonb,
                prompt TEXT,
                theme TEXT DEFAULT 'Общая тематика',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_post_at TIMESTAMP
            )
        ''')
        
        # Таблица истории постов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts_history (
                id SERIAL PRIMARY KEY,
                channel_id TEXT REFERENCES channels(id) ON DELETE CASCADE,
                post_text TEXT NOT NULL,
                status TEXT DEFAULT 'published',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для оптимизации
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_posts_channel_id ON posts_history(channel_id);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts_history(created_at DESC);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channels_enabled ON channels(enabled);
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL база данных инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise

def get_channels() -> List[Dict]:
    """Получение всех каналов"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channels ORDER BY created_at DESC")
        channels = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Преобразуем JSONB в list
        for channel in channels:
            if isinstance(channel['times'], str):
                channel['times'] = json.loads(channel['times'])
        
        return channels
        
    except Exception as e:
        logger.error(f"Ошибка получения каналов: {e}")
        return []

def get_channel(channel_id: str) -> Optional[Dict]:
    """Получение канала по ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channels WHERE id = %s", (channel_id,))
        channel = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if channel and isinstance(channel['times'], str):
            channel['times'] = json.loads(channel['times'])
        
        return channel
        
    except Exception as e:
        logger.error(f"Ошибка получения канала: {e}")
        return None

def add_channel(telegram_channel_id: str, name: str, posts_per_day: int = 1, 
                times: List[str] = None, prompt: str = None, theme: str = None) -> bool:
    """Добавление нового канала"""
    try:
        if times is None:
            times = ["12:00"]
        
        if prompt is None:
            prompt = "Напиши интересный пост для Telegram канала."
        
        if theme is None:
            theme = "Общая тематика"
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO channels (id, name, posts_per_day, times, prompt, theme)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', (telegram_channel_id, name, posts_per_day, json.dumps(times), prompt, theme))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        
        if success:
            logger.info(f"✅ Канал {name} добавлен")
        else:
            logger.warning(f"⚠️ Канал {telegram_channel_id} уже существует")
        
        return success
        
    except Exception as e:
        logger.error(f"Ошибка добавления канала: {e}")
        return False

def update_channel(channel_id: str, updates: Dict) -> bool:
    """Обновление настроек канала"""
    try:
        if not updates:
            return False
        
        # Преобразуем times в JSON если есть
        if 'times' in updates and isinstance(updates['times'], list):
            updates['times'] = json.dumps(updates['times'])
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Формируем SET clause
        set_parts = []
        values = []
        for key, value in updates.items():
            if key == 'times':
                set_parts.append(f"{key} = %s::jsonb")
            else:
                set_parts.append(f"{key} = %s")
            values.append(value)
        
        values.append(channel_id)
        
        query = f"UPDATE channels SET {', '.join(set_parts)} WHERE id = %s"
        cursor.execute(query, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        
        if success:
            logger.info(f"✅ Канал {channel_id} обновлен")
        
        return success
        
    except Exception as e:
        logger.error(f"Ошибка обновления канала: {e}")
        return False

def delete_channel(channel_id: str) -> bool:
    """Удаление канала"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM channels WHERE id = %s", (channel_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        
        if success:
            logger.info(f"✅ Канал {channel_id} удален")
        
        return success
        
    except Exception as e:
        logger.error(f"Ошибка удаления канала: {e}")
        return False

def save_post_history(channel_id: str, post_text: str, status: str = 'published'):
    """Сохранение истории постов"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts_history (channel_id, post_text, status)
            VALUES (%s, %s, %s)
        ''', (channel_id, post_text, status))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ История поста сохранена для {channel_id}")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")

def get_post_history(channel_id: str, limit: int = 50) -> List[Dict]:
    """Получение истории постов канала"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM posts_history
            WHERE channel_id = %s AND status = 'published'
            ORDER BY created_at DESC
            LIMIT %s
        ''', (channel_id, limit))
        
        posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Преобразуем в нужный формат
        result = []
        for post in posts:
            result.append({
                'channel_id': post['channel_id'],
                'post_text': post['post_text'],
                'status': post['status'],
                'timestamp': post['created_at'].isoformat() if post['created_at'] else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return []

def get_recent_posts(channel_id: str, days: int = 7) -> List[str]:
    """Получение текстов последних постов за N дней"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT post_text FROM posts_history
            WHERE channel_id = %s 
            AND status = 'published'
            AND created_at >= %s
            ORDER BY created_at DESC
        ''', (channel_id, cutoff_date))
        
        posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [post['post_text'] for post in posts]
        
    except Exception as e:
        logger.error(f"Ошибка получения последних постов: {e}")
        return []

def get_config(key: str, default: str = None) -> Optional[str]:
    """Получение конфигурации"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM configs WHERE key = %s", (key,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result['value'] if result else default
        
    except Exception as e:
        logger.error(f"Ошибка получения конфига: {e}")
        return default

def set_config(key: str, value: str):
    """Сохранение конфигурации"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO configs (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        ''', (key, value))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Конфиг {key} сохранен")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения конфига: {e}")
