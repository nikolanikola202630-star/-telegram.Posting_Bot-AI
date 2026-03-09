"""Тестирование всех функций бота"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Проверка переменных окружения
def test_env_variables():
    """Тест 1: Проверка переменных окружения"""
    print("\n=== Тест 1: Переменные окружения ===")
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY', 'ADMIN_USER_ID']
    optional_vars = ['DATABASE_URL']
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен")
        else:
            print(f"❌ {var}: НЕ установлен")
            all_ok = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен (PostgreSQL)")
        else:
            print(f"⚠️  {var}: не установлен (будет использован in-memory)")
    
    return all_ok

# Тест базы данных
def test_database():
    """Тест 2: База данных"""
    print("\n=== Тест 2: База данных ===")
    
    try:
        from core import init_db, add_channel, get_channels, get_channel, update_channel, delete_channel
        
        # Инициализация
        init_db()
        print("✅ База данных инициализирована")
        
        # Добавление тестового канала
        test_id = "@test_channel_12345"
        success = add_channel(test_id, "Test Channel", theme="Тест")
        if success:
            print("✅ Канал добавлен")
        else:
            print("⚠️  Канал уже существует")
        
        # Получение канала
        channel = get_channel(test_id)
        if channel:
            print(f"✅ Канал получен: {channel['name']}")
        else:
            print("❌ Ошибка получения канала")
            return False
        
        # Обновление канала
        update_channel(test_id, {'prompt': 'Test prompt'})
        updated = get_channel(test_id)
        if updated and updated['prompt'] == 'Test prompt':
            print("✅ Канал обновлен")
        else:
            print("❌ Ошибка обновления канала")
            return False
        
        # Получение всех каналов
        channels = get_channels()
        print(f"✅ Всего каналов: {len(channels)}")
        
        # Удаление тестового канала
        delete_channel(test_id)
        print("✅ Тестовый канал удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

# Тест AI генератора
def test_ai_generator():
    """Тест 3: AI генератор"""
    print("\n=== Тест 3: AI генератор ===")
    
    try:
        from core.ai_generator import get_generator
        
        generator = get_generator()
        print("✅ Генератор инициализирован")
        
        # Генерация тестового поста
        post = generator.generate_post("Напиши короткий тестовый пост в одно предложение", "Тест")
        
        if post:
            print(f"✅ Пост сгенерирован ({len(post)} символов)")
            print(f"   Превью: {post[:100]}...")
            return True
        else:
            print("❌ Ошибка генерации поста")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка генератора: {e}")
        return False

# Тест Telegram клиента
async def test_telegram_client():
    """Тест 4: Telegram клиент"""
    print("\n=== Тест 4: Telegram клиент ===")
    
    try:
        from core.telegram_client import get_telegram_client
        
        client = get_telegram_client()
        print("✅ Telegram клиент инициализирован")
        
        # Проверка бота
        bot_info = await client.bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

# Тест анализатора контента
def test_content_analyzer():
    """Тест 5: Анализатор контента"""
    print("\n=== Тест 5: Анализатор контента ===")
    
    try:
        from core.content_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        print("✅ Анализатор инициализирован")
        
        # Тест схожести
        text1 = "Это тестовый пост о программировании"
        text2 = "Это тестовый пост о программировании"
        text3 = "Совершенно другой текст про кулинарию"
        
        similarity1 = analyzer.calculate_similarity(text1, text2)
        similarity2 = analyzer.calculate_similarity(text1, text3)
        
        print(f"✅ Схожесть идентичных текстов: {similarity1:.2%}")
        print(f"✅ Схожесть разных текстов: {similarity2:.2%}")
        
        # Тест проверки дубликатов
        is_dup, _ = analyzer.is_duplicate(text1, [text2])
        if is_dup:
            print("✅ Дубликат обнаружен корректно")
        else:
            print("❌ Дубликат не обнаружен")
            return False
        
        is_dup2, _ = analyzer.is_duplicate(text3, [text1, text2])
        if not is_dup2:
            print("✅ Уникальный текст определен корректно")
        else:
            print("❌ Ложное срабатывание дубликата")
            return False
        
        # Тест извлечения ключевых слов
        keywords = analyzer.get_unique_keywords(text1)
        print(f"✅ Извлечено ключевых слов: {len(keywords)}")
        
        # Тест анализа канала
        test_posts = [
            {'post_text': 'Первый пост о программировании', 'timestamp': '2024-01-01'},
            {'post_text': 'Второй пост о разработке', 'timestamp': '2024-01-02'},
            {'post_text': 'Третий пост о кодинге', 'timestamp': '2024-01-03'}
        ]
        
        stats = analyzer.analyze_channel_content(test_posts)
        print(f"✅ Анализ канала: {stats['total_posts']} постов, {stats['unique_posts']} уникальных")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализатора: {e}")
        return False

# Тест обработчиков бота
def test_bot_handlers():
    """Тест 6: Обработчики бота"""
    print("\n=== Тест 6: Обработчики бота ===")
    
    try:
        from handlers import bot_handlers
        
        # Проверка наличия всех функций
        required_functions = ['start', 'button', 'handle_text', 'show_channels_list', 'show_channel_settings']
        
        for func_name in required_functions:
            if hasattr(bot_handlers, func_name):
                print(f"✅ Функция {func_name} найдена")
            else:
                print(f"❌ Функция {func_name} не найдена")
                return False
        
        # Проверка админа
        admin_id = int(os.getenv('ADMIN_USER_ID', 0))
        if bot_handlers.is_admin(admin_id):
            print(f"✅ Проверка админа работает (ID: {admin_id})")
        else:
            print("❌ Ошибка проверки админа")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработчиков: {e}")
        return False

# Главная функция
async def main():
    """Запуск всех тестов"""
    print("=" * 50)
    print("🧪 ТЕСТИРОВАНИЕ TELEGRAM БОТА")
    print("=" * 50)
    
    results = []
    
    # Тест 1: Переменные окружения
    results.append(("Переменные окружения", test_env_variables()))
    
    # Тест 2: База данных
    results.append(("База данных", test_database()))
    
    # Тест 3: AI генератор
    results.append(("AI генератор", test_ai_generator()))
    
    # Тест 4: Telegram клиент
    results.append(("Telegram клиент", await test_telegram_client()))
    
    # Тест 5: Анализатор контента
    results.append(("Анализатор контента", test_content_analyzer()))
    
    # Тест 6: Обработчики бота
    results.append(("Обработчики бота", test_bot_handlers()))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 50)
    print(f"Пройдено: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 50)
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот готов к работе.")
        return 0
    else:
        print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ ({total - passed} ошибок)")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
