#!/usr/bin/env python3
"""Скрипт для установки webhook на Vercel"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def setup_webhook(vercel_url: str):
    """Установка webhook"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return False
    
    if not vercel_url:
        print("❌ Укажите URL Vercel")
        return False
    
    # Убираем trailing slash
    vercel_url = vercel_url.rstrip('/')
    webhook_url = f"{vercel_url}/api/webhook"
    
    try:
        bot = Bot(token=token)
        
        # Устанавливаем webhook
        await bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook установлен: {webhook_url}")
        
        # Проверяем webhook
        info = await bot.get_webhook_info()
        print(f"\n📊 Информация о webhook:")
        print(f"   URL: {info.url}")
        print(f"   Pending updates: {info.pending_update_count}")
        
        if info.last_error_message:
            print(f"   ⚠️ Последняя ошибка: {info.last_error_message}")
        else:
            print(f"   ✅ Ошибок нет")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def delete_webhook():
    """Удаление webhook"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return False
    
    try:
        bot = Bot(token=token)
        await bot.delete_webhook()
        print("✅ Webhook удален")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("🔧 Настройка Webhook для Telegram бота")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nИспользование:")
        print("  python setup_webhook.py <vercel-url>")
        print("  python setup_webhook.py delete")
        print("\nПример:")
        print("  python setup_webhook.py https://your-bot.vercel.app")
        print("  python setup_webhook.py delete")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "delete":
        asyncio.run(delete_webhook())
    else:
        asyncio.run(setup_webhook(command))

if __name__ == "__main__":
    main()
