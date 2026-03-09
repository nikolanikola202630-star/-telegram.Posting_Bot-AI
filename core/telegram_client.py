"""Модуль для работы с Telegram API"""
import os
import logging
from telegram import Bot

logger = logging.getLogger(__name__)

class TelegramClient:
    def __init__(self):
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        self.bot = Bot(token=token)
    
    async def send_post(self, channel_id: str, text: str) -> bool:
        """Отправка поста в канал"""
        try:
            await self.bot.send_message(chat_id=channel_id, text=text, parse_mode="Markdown")
            logger.info(f"Пост отправлен в {channel_id}")
            return True
        except Exception as e:
            logger.warning(f"Ошибка с Markdown: {e}")
            try:
                await self.bot.send_message(chat_id=channel_id, text=text)
                logger.info(f"Пост отправлен без Markdown в {channel_id}")
                return True
            except Exception as e2:
                logger.error(f"Ошибка отправки в {channel_id}: {e2}")
                return False
    
    async def set_webhook(self, url: str) -> bool:
        """Установка webhook"""
        try:
            await self.bot.set_webhook(url=url)
            logger.info(f"Webhook установлен: {url}")
            return True
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
            return False

# Глобальный экземпляр
_client = None

def get_telegram_client() -> TelegramClient:
    """Получение экземпляра клиента"""
    global _client
    if _client is None:
        _client = TelegramClient()
    return _client
