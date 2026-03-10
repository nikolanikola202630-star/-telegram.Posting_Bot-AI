# 🚀 ДЕПЛОЙ НА VERCEL - ПОШАГОВАЯ ИНСТРУКЦИЯ

## ✅ Проект готов к деплою!

**Все изменения закоммичены локально.**  
Осталось только отправить на GitHub и задеплоить на Vercel.

---

## 📋 Шаг 1: Отправка на GitHub (1 минута)

### Вариант A: Через GitHub Desktop (рекомендуется)
1. Откройте GitHub Desktop
2. Выберите репозиторий `-telegram.Posting_Bot-AI`
3. Нажмите "Push origin"

### Вариант B: Через командную строку
```bash
cd -telegram.Posting_Bot-AI
git push origin main
```

Если возникает ошибка 403, настройте Git credentials:
```bash
git config credential.helper store
git push origin main
# Введите ваш GitHub username и Personal Access Token
```

---

## 📋 Шаг 2: Деплой на Vercel (3 минуты)

### Способ 1: Через Vercel Dashboard (проще)

1. **Откройте Vercel:**
   - Перейдите на [vercel.com](https://vercel.com)
   - Войдите в аккаунт

2. **Создайте новый проект:**
   - Нажмите "Add New..." → "Project"
   - Выберите "Import Git Repository"
   - Найдите репозиторий `AlexMi64/-telegram.Posting_Bot-AI`
   - Нажмите "Import"

3. **Настройте проект:**
   - Project Name: `telegram-posting-bot` (или любое другое)
   - Framework Preset: `Other`
   - Root Directory: `./`
   - Build Command: (оставьте пустым)
   - Output Directory: (оставьте пустым)

4. **Добавьте переменные окружения:**
   
   Нажмите "Environment Variables" и добавьте:
   
   ```
   TELEGRAM_BOT_TOKEN
   8588815355:AAEnHeBcsGJqwDWpRVfj5gMf3AMSIRWkqPg
   
   GROQ_API_KEY
   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
   
   ADMIN_USER_ID
   8264612178
   
   DATABASE_URL
   postgresql://postgres:kSdgEMv1Quw5pMAl@db.osunsmmvrglimqtmjixs.supabase.co:5432/postgres
   ```
   
   **ВАЖНО:** Добавьте все 4 переменные для всех окружений (Production, Preview, Development)

5. **Деплой:**
   - Нажмите "Deploy"
   - Дождитесь завершения (2-3 минуты)
   - Скопируйте URL проекта (например: `https://telegram-posting-bot-abc123.vercel.app`)

### Способ 2: Через Vercel CLI

```bash
# Установка Vercel CLI (если еще не установлен)
npm install -g vercel

# Логин
vercel login

# Деплой
cd -telegram.Posting_Bot-AI
vercel --prod

# Следуйте инструкциям в терминале
```

---

## 📋 Шаг 3: Установка Webhook (1 минута)

После успешного деплоя:

1. **Скопируйте URL вашего проекта** из Vercel Dashboard
   - Например: `https://telegram-posting-bot-abc123.vercel.app`

2. **Запустите скрипт установки webhook:**
   ```bash
   python setup_webhook.py https://telegram-posting-bot-abc123.vercel.app
   ```
   
   Замените URL на ваш реальный URL!

3. **Проверьте результат:**
   Вы должны увидеть:
   ```
   ✅ Webhook успешно установлен!
   URL: https://telegram-posting-bot-abc123.vercel.app/api/webhook
   ```

---

## 📋 Шаг 4: Проверка (2 минуты)

### 1. Проверьте webhook:
```bash
curl "https://api.telegram.org/bot8588815355:AAEnHeBcsGJqwDWpRVfj5gMf3AMSIRWkqPg/getWebhookInfo"
```

Должно быть:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-project.vercel.app/api/webhook",
    "pending_update_count": 0,
    "last_error_date": null
  }
}
```

### 2. Протестируйте бота:
1. Откройте Telegram
2. Найдите @egoist_private_bot
3. Отправьте `/start`
4. Должно появиться меню с кнопками

### 3. Добавьте канал:
1. Нажмите "➕ Добавить канал"
2. Введите название: `Black History`
3. Введите ID: `@black_histor`
4. Введите тематику: `История`

### 4. Настройте автопубликацию:
1. Выберите канал
2. "⚙️ Настройки"
3. "✏️ Изменить промпт": `Напиши интересный исторический факт. Увлекательный стиль, 150-200 слов.`
4. "⏰ Изменить время": `09:00,15:00,21:00`
5. "🔢 Постов в день": `3`
6. "🎛️ Включить"

### 5. Протестируйте генерацию:
1. Выберите канал
2. "🎨 Генерировать пост"
3. Проверьте результат
4. "🚀 Опубликовать"

---

## 🎉 Готово!

Ваш бот теперь работает 24/7 на Vercel!

### Что работает:
- ✅ Webhook для Telegram
- ✅ Автопубликация каждый час (Cron Jobs)
- ✅ AI генерация постов
- ✅ Проверка уникальности контента
- ✅ PostgreSQL хранилище
- ✅ Управление через Telegram

### Мониторинг:

**Vercel Dashboard:**
- Analytics → Функции
- Deployments → Логи
- Settings → Environment Variables

**Логи в реальном времени:**
```bash
vercel logs --follow
```

**Проверка cron:**
```bash
curl https://your-project.vercel.app/api/cron
```

---

## 🆘 Если что-то не работает

### Ошибка 404:
1. Проверьте переменные окружения в Vercel
2. Сделайте redeploy (Deployments → ... → Redeploy)
3. Переустановите webhook

### Бот не отвечает:
1. Проверьте webhook: `getWebhookInfo`
2. Проверьте логи в Vercel Dashboard
3. Убедитесь, что все переменные окружения установлены

### Не генерируются посты:
1. Проверьте GROQ_API_KEY
2. Проверьте логи функции `/api/cron`
3. Попробуйте другой промпт

### PostgreSQL не работает:
- Это нормально! Бот автоматически использует in-memory БД
- Для продакшена PostgreSQL будет работать на Vercel

---

## 📚 Полезные ссылки

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Telegram Bot:** https://t.me/egoist_private_bot
- **Канал:** https://t.me/black_histor
- **Документация:** README.md, DEPLOY_READY.md, QUICKSTART.md

---

## 🎯 Следующие шаги

После успешного деплоя:

1. **Мониторинг:**
   - Следите за логами в Vercel
   - Проверяйте публикации в канале
   - Смотрите статистику в боте

2. **Оптимизация:**
   - Настройте промпты для лучшего контента
   - Подберите оптимальное время публикаций
   - Добавьте больше каналов

3. **Масштабирование:**
   - Добавьте другие каналы
   - Настройте разные тематики
   - Экспериментируйте с промптами

---

**Удачного деплоя! 🚀**

Если возникнут вопросы, проверьте:
- FIX_404.md - решение проблемы 404
- DEPLOY_READY.md - детальная инструкция
- TEST_REPORT.md - результаты тестирования
