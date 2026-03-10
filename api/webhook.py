"""Webhook обработчик для Telegram бота на Vercel"""
import os
import sys
import json
import logging
import asyncio
import nest_asyncio
from http.server import BaseHTTPRequestHandler

# Применяем nest_asyncio для работы с вложенными event loops
nest_asyncio.apply()

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
            logger.error("TELEGRAM_BOT_TOKEN не установлен")
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

class handler(BaseHTTPRequestHandler):
    """Vercel Python handler (WSGI-style)"""
    
    def do_GET(self):
        """Обработка GET запросов (healthcheck)"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = json.dumps({
                'status': 'running',
                'service': 'Telegram Bot Webhook',
                'version': '1.0'
            })
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Ошибка GET: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
    
    def do_POST(self):
        """Обработка POST запросов от Telegram"""
        try:
            # Получаем приложение (ленивая инициализация)
            app = get_application()
            
            # Читаем тело запроса
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Bad Request: Empty body')
                return
            
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode('utf-8'))
            
            logger.info(f"Получен update: {update_data.get('update_id')}")
            
            # Создаем Update объект
            update = Update.de_json(update_data, app.bot)
            
            # Обработка update асинхронно
            asyncio.run(app.process_update(update))
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
            logger.info("Update обработан успешно")
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bad Request: Invalid JSON')
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())

