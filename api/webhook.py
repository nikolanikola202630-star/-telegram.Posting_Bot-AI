"""Webhook обработчик для Telegram бота на Vercel"""
import os
import sys
import json
import logging
import asyncio
from urllib.parse import parse_qs

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.bot_handlers import start, button, handle_text

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Инициализация приложения (ленивая)
application = None

def get_application():
    """Получение или создание приложения"""
    global application
    if application is None:
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        
        # Инициализация БД
        try:
            from core import init_db
            init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации БД: {e}")
        
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("✅ Приложение инициализировано")
    
    return application

def handler(event, context):
    """Vercel serverless function handler"""
    try:
        # Получаем приложение
        app = get_application()
        
        # Получаем метод и тело запроса
        http_method = event.get('httpMethod', event.get('method', 'GET'))
        
        # Обработка GET запроса (healthcheck)
        if http_method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'running',
                    'service': 'Telegram Bot Webhook',
                    'version': '1.0'
                })
            }
        
        # Обработка POST запроса (webhook)
        if http_method == 'POST':
            body = event.get('body', '')
            if event.get('isBase64Encoded'):
                import base64
                body = base64.b64decode(body).decode('utf-8')
            
            update_data = json.loads(body)
            
            # Создаем Update объект
            update = Update.de_json(update_data, app.bot)
            
            # Обработка update
            asyncio.run(app.process_update(update))
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/plain'},
                'body': 'OK'
            }
        
        return {
            'statusCode': 405,
            'body': 'Method Not Allowed'
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Error: {str(e)}'
        }
