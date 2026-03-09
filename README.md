# 🤖 Telegram Posting Bot - AI Powered

Интеллектуальный Telegram бот для автоматической генерации и публикации постов с использованием AI (Groq/Llama) и анализом уникальности контента.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone)

## ✅ Статус: ГОТОВ К ДЕПЛОЮ

**Последнее тестирование:** 5/6 тестов пройдено (83.3%)
- ✅ Переменные окружения
- ✅ AI генератор (Groq)
- ✅ Telegram клиент
- ✅ Анализатор контента
- ✅ Обработчики бота
- ⚠️ PostgreSQL (работает только на Vercel)

---

## ✨ Возможности

- 📱 **Множественные каналы** - Управление неограниченным количеством каналов
- 🤖 **AI генерация** - Качественный контент через Groq/Llama
- 🔍 **Анализ уникальности** - Автоматическая проверка на дубликаты
- ⏰ **Автопубликация** - Гибкое расписание для каждого канала
- 📊 **Аналитика** - Статистика и анализ контента канала
- 🗄️ **PostgreSQL** - Постоянное хранилище данных (опционально)
- 🚀 **Serverless** - Готов к деплою на Vercel

---

## 🏗️ Архитектура

```
├── api/
│   ├── webhook.py      # Webhook для Telegram
│   └── cron.py         # Автопубликация (Cron Jobs)
├── core/
│   ├── database.py     # In-memory хранилище
│   ├── database_pg.py  # PostgreSQL хранилище
│   ├── ai_generator.py # Groq AI генерация
│   ├── telegram_client.py # Telegram API
│   └── content_analyzer.py # Анализ уникальности
├── handlers/
│   └── bot_handlers.py # Обработчики команд
├── .env                # Конфигурация
├── vercel.json         # Конфиг Vercel
└── requirements.txt    # Зависимости
```

---

## 🚀 Быстрый старт

### 1. Получение токенов

#### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/BotFather)
2. Создайте бота: `/newbot`
3. Скопируйте токен

#### Groq API Key
1. Зарегистрируйтесь на [console.groq.com](https://console.groq.com)
2. Создайте API ключ (бесплатно)

#### Admin User ID
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Получите ваш User ID

### 2. Локальное тестирование (опционально)

```bash
# Клонируйте репозиторий
git clone <your-repo>
cd -telegram.Posting_Bot-AI

# Установите зависимости
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
# Заполните .env своими данными

# Запустите тест
python test_full.py

# Запустите бота локально
python local_test.py
```

### 3. Деплой на Vercel

#### Через GitHub (рекомендуется):

```bash
# 1. Создайте репозиторий на GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/repo.git
git push -u origin main

# 2. Импортируйте в Vercel
# - Перейдите на vercel.com
# - New Project → Import Git Repository
# - Добавьте переменные окружения:
#   TELEGRAM_BOT_TOKEN
#   GROQ_API_KEY
#   ADMIN_USER_ID
#   DATABASE_URL (опционально)
# - Deploy!

# 3. Установите webhook
python setup_webhook.py https://your-project.vercel.app
```

#### Через Vercel CLI:

```bash
# Установите CLI
npm install -g vercel

# Войдите
vercel login

# Деплой
vercel --prod

# Добавьте переменные окружения
vercel env add TELEGRAM_BOT_TOKEN
vercel env add GROQ_API_KEY
vercel env add ADMIN_USER_ID

# Редеплой
vercel --prod

# Установите webhook
python setup_webhook.py https://your-project.vercel.app
```

---

## 📖 Использование

### Команды бота

- `/start` - Запуск бота

### Управление каналами

1. **Добавление канала**
   - Нажмите "➕ Добавить канал"
   - Введите название
   - Введите ID канала (@channel или -1001234567890)
   - Введите тематику

2. **Настройка канала**
   - Выберите канал из списка
   - "⚙️ Настройки"
   - Настройте:
     - ✏️ Промпт для AI
     - 🎨 Тематику
     - ⏰ Время публикаций (09:00,15:00,21:00)
     - 🔢 Количество постов в день
     - 🎛️ Включить/выключить автопостинг

3. **Генерация и публикация**
   - Выберите канал
   - "🎨 Генерировать пост"
   - Проверьте уникальность
   - "🚀 Опубликовать"

4. **Анализ канала**
   - Выберите канал
   - "📊 Анализ канала"
   - Просмотрите статистику

---

## 🔍 Анализ уникальности

Бот автоматически:
- Проверяет новые посты на схожесть с предыдущими (порог 70%)
- Анализирует последние 50 постов
- Делает до 3 попыток создать уникальный контент
- Улучшает промпт с учетом истории канала

### Пример анализа:

```
📊 Анализ канала Black History

📝 Всего постов: 25
✨ Уникальных: 22
📈 Уникальность: 88.0%
📏 Средняя длина: 187 символов

🔑 Частые темы:
1. история
2. факты
3. события
4. личности
5. даты

💡 Рекомендация: Отличное разнообразие контента!
```

---

## �️ PostgreSQL (опционально)

Для постоянного хранилища данных:

```bash
# 1. Создайте БД на Supabase/Neon/Vercel Postgres

# 2. Добавьте DATABASE_URL в .env
DATABASE_URL=postgresql://user:password@host:5432/database

# 3. Деплой
vercel --prod
```

Бот автоматически создаст все таблицы при первом запуске.

Подробнее: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

---

## 💡 Примеры промптов

### Исторический канал
```
Напиши интересный исторический факт.
Используй увлекательный стиль, добавь эмодзи.
Длина: 150-200 слов.
```

### Мотивационный канал
```
Создай вдохновляющий пост о достижении целей.
Используй метафоры и позитивный тон.
```

### IT канал
```
Напиши краткую IT-новость.
Профессиональный стиль, 150 слов.
```

---

## 🔧 Конфигурация

### Переменные окружения

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather | ✅ |
| `GROQ_API_KEY` | API ключ Groq | ✅ |
| `ADMIN_USER_ID` | ID администратора | ✅ |
| `DATABASE_URL` | PostgreSQL URL | ⚪ |

### Vercel Cron Jobs

Автопубликация настроена в `vercel.json`:
```json
{
  "crons": [{
    "path": "/api/cron",
    "schedule": "0 * * * *"  // Каждый час
  }]
}
```

---

## 🧪 Тестирование

```bash
# Полный тест всех модулей
python test_full.py

# Тест PostgreSQL
python test_postgres.py

# Локальный запуск
python local_test.py
```

---

## 📊 Мониторинг

### Логи Vercel
```bash
vercel logs --follow
```

### Проверка webhook
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### Проверка cron
```bash
curl https://your-project.vercel.app/api/cron
```

---

## 🐛 Troubleshooting

### Бот не отвечает
1. Проверьте webhook: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
2. Проверьте логи: `vercel logs`
3. Переустановите webhook: `python setup_webhook.py delete && python setup_webhook.py <URL>`

### Не работает автопубликация
1. Проверьте Cron Jobs в Vercel Dashboard
2. Убедитесь, что каналы включены (✅)
3. Проверьте время в настройках

### Ошибки генерации
1. Проверьте Groq API ключ
2. Проверьте лимиты на console.groq.com

---

## 📚 Документация

- [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md) - Чеклист деплоя
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - Настройка PostgreSQL
- [FEATURES.md](FEATURES.md) - Описание функций
- [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) - Анализ проекта

---

## 💰 Стоимость

### Бесплатный тариф
- **Vercel:** Free tier (достаточно для старта)
- **Groq:** Free tier (щедрые лимиты)
- **Telegram:** Бесплатно
- **Итого:** $0/месяц

### Продакшн (рекомендуемый)
- **Vercel Pro:** $20/месяц
- **PostgreSQL:** $0-20/месяц
- **Groq API:** $0-50/месяц
- **Итого:** $20-90/месяц

---

## 🔐 Безопасность

- ✅ Токены в переменных окружения
- ✅ Проверка прав администратора
- ✅ .env в .gitignore
- ✅ HTTPS webhook
- ✅ PostgreSQL с SSL

---

## 🤝 Вклад

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 Лицензия

MIT License - используйте свободно для личных и коммерческих проектов.

---

## 🎉 Готово!

Ваш бот готов к работе. Добавляйте каналы, настраивайте промпты и наслаждайтесь автоматической публикацией уникального контента!

**Удачи! 🚀**
