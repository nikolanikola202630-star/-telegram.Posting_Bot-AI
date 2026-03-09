"""Локальный запуск бота для тестирования"""
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Для локального тестирования используем in-memory БД
# Удаляем DATABASE_URL ДО загрузки переменных окружения
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

# Загрузка переменных окружения
load_dotenv()

# Снова удаляем DATABASE_URL если он был загружен из .env
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск бота"""
    try:
        # Проверка переменных окружения
        required_vars = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY', 'ADMIN_USER_ID']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
            return 1
        
        logger.info("✅ Все переменные окружения установлены")
        logger.info("ℹ️  Используется in-memory БД для локального тестирования")
        
        # Инициализация базы данных
        from core import init_db
        init_db()
        logger.info("✅ База данных инициализирована (in-memory)")
        
        # Импорт компонентов
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
        from handlers.bot_handlers import start, button, handle_text
        
        # Создание приложения
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        application = Application.builder().token(token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("✅ Обработчики зарегистрированы")
        
        # Получение информации о боте
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Бот запущен: @{bot_info.username} ({bot_info.first_name})")
        logger.info(f"✅ ID бота: {bot_info.id}")
        
        admin_id = os.getenv('ADMIN_USER_ID')
        logger.info(f"✅ Админ ID: {admin_id}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🤖 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
        logger.info("=" * 60)
        logger.info(f"📱 Откройте Telegram: https://t.me/{bot_info.username}")
        logger.info("📝 Отправьте команду: /start")
        logger.info("⏹️  Для остановки нажмите Ctrl+C")
        logger.info("=" * 60 + "\n")
        
        # Запуск polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )
        
        # Ожидание остановки
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("\n⏹️  Остановка бота...")
        
        # Остановка
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        
        logger.info("✅ Бот остановлен")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Бот остановлен пользователем")
        return 0
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен")
        sys.exit(0)
