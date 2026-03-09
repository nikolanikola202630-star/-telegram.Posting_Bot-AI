"""Тест in-memory базы данных (без PostgreSQL)"""
import os
import sys

# Удаляем DATABASE_URL чтобы использовать in-memory
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

from core import init_db, add_channel, get_channels, get_channel, update_channel, delete_channel
from core import save_post_history, get_post_history, get_recent_posts

print("=" * 50)
print("🧪 ТЕСТ IN-MEMORY БАЗЫ ДАННЫХ")
print("=" * 50)

try:
    # Инициализация
    init_db()
    print("✅ База данных инициализирована (in-memory)")
    
    # Добавление канала
    success = add_channel("@test_channel", "Test Channel", theme="Тест", posts_per_day=3)
    if success:
        print("✅ Канал добавлен")
    else:
        print("❌ Ошибка добавления канала")
        sys.exit(1)
    
    # Получение канала
    channel = get_channel("@test_channel")
    if channel:
        print(f"✅ Канал получен: {channel['name']}")
        print(f"   - ID: {channel['id']}")
        print(f"   - Тематика: {channel['theme']}")
        print(f"   - Постов в день: {channel['posts_per_day']}")
        print(f"   - Время: {channel['times']}")
    else:
        print("❌ Канал не найден")
        sys.exit(1)
    
    # Обновление канала
    update_channel("@test_channel", {
        'prompt': 'Новый промпт для тестирования',
        'times': ['09:00', '15:00', '21:00'],
        'enabled': True
    })
    
    updated = get_channel("@test_channel")
    if updated['prompt'] == 'Новый промпт для тестирования':
        print("✅ Канал обновлен")
        print(f"   - Промпт: {updated['prompt'][:50]}...")
        print(f"   - Время: {updated['times']}")
    else:
        print("❌ Ошибка обновления")
        sys.exit(1)
    
    # Добавление еще каналов
    add_channel("@channel2", "Channel 2", theme="IT")
    add_channel("@channel3", "Channel 3", theme="Бизнес")
    
    # Получение всех каналов
    channels = get_channels()
    print(f"✅ Всего каналов: {len(channels)}")
    for ch in channels:
        status = "✅" if ch.get('enabled') else "❌"
        print(f"   {status} {ch['name']} | {ch['theme']}")
    
    # Сохранение истории постов
    save_post_history("@test_channel", "Первый тестовый пост", "published")
    save_post_history("@test_channel", "Второй тестовый пост", "published")
    save_post_history("@test_channel", "Третий тестовый пост", "published")
    print("✅ История постов сохранена (3 поста)")
    
    # Получение истории
    history = get_post_history("@test_channel", limit=10)
    print(f"✅ История получена: {len(history)} постов")
    for i, post in enumerate(history, 1):
        print(f"   {i}. {post['post_text'][:40]}...")
    
    # Получение последних постов
    recent = get_recent_posts("@test_channel", days=7)
    print(f"✅ Последние посты (7 дней): {len(recent)} постов")
    
    # Удаление канала
    delete_channel("@channel2")
    channels_after = get_channels()
    if len(channels_after) == len(channels) - 1:
        print("✅ Канал удален")
        print(f"   Осталось каналов: {len(channels_after)}")
    else:
        print("❌ Ошибка удаления")
        sys.exit(1)
    
    # Проверка включения/выключения
    update_channel("@test_channel", {'enabled': False})
    disabled = get_channel("@test_channel")
    if not disabled['enabled']:
        print("✅ Канал выключен")
    else:
        print("❌ Ошибка выключения")
        sys.exit(1)
    
    update_channel("@test_channel", {'enabled': True})
    enabled = get_channel("@test_channel")
    if enabled['enabled']:
        print("✅ Канал включен")
    else:
        print("❌ Ошибка включения")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 ВСЕ ТЕСТЫ IN-MEMORY БД ПРОЙДЕНЫ!")
    print("=" * 50)
    print("\n✅ In-memory база данных работает корректно")
    print("✅ Все CRUD операции функционируют")
    print("✅ История постов сохраняется")
    print("✅ Fallback механизм готов к работе")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
