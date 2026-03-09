# ⚡ Быстрый старт

## 🚀 Деплой за 3 минуты

### Шаг 1: Подготовка (30 сек)
```bash
cd -telegram.Posting_Bot-AI
git add .
git commit -m "Ready for production"
git push
```

### Шаг 2: Vercel (1 мин)
1. Откройте [vercel.com](https://vercel.com)
2. New Project → Import Git Repository
3. Добавьте переменные окружения:
```
TELEGRAM_BOT_TOKEN=8588815355:AAEnHeBcsGJqwDWpRVfj5gMf3AMSIRWkqPg
GROQ_API_KEY=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
ADMIN_USER_ID=8264612178
DATABASE_URL=postgresql://postgres:kSdgEMv1Quw5pMAl@db.osunsmmvrglimqtmjixs.supabase.co:5432/postgres
```
4. Deploy!

⚠️ **ВАЖНО:** После добавления переменных сделайте REDEPLOY!

### Шаг 3: Webhook (30 сек)
```bash
python setup_webhook.py https://your-vercel-url.vercel.app
```

### Шаг 4: Проверка (1 мин)
1. Откройте @egoist_private_bot
2. Отправьте `/start`
3. Нажмите "➕ Добавить канал"
4. Добавьте @black_histor

## ✅ Готово!

Бот работает 24/7 на Vercel с автопубликацией!

## 📱 Использование

### Добавление канала:
1. "➕ Добавить канал"
2. Введите название: `Black History`
3. Введите ID: `@black_histor`
4. Введите тематику: `История`

### Настройка автопубликации:
1. Выберите канал
2. "⚙️ Настройки"
3. "✏️ Изменить промпт": `Напиши интересный исторический факт. 150-200 слов.`
4. "⏰ Изменить время": `09:00,15:00,21:00`
5. "🔢 Постов в день": `3`
6. "🎛️ Включить"

### Генерация поста:
1. Выберите канал
2. "🎨 Генерировать пост"
3. Проверьте уникальность
4. "🚀 Опубликовать"

### Анализ канала:
1. Выберите канал
2. "📊 Анализ канала"
3. Смотрите статистику

## 🔍 Проверка работы

### Webhook:
```bash
curl "https://api.telegram.org/bot8588815355:AAEnHeBcsGJqwDWpRVfj5gMf3AMSIRWkqPg/getWebhookInfo"
```

Должно быть:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-project.vercel.app/api/webhook",
    "pending_update_count": 0
  }
}
```

### Cron:
```bash
curl https://your-project.vercel.app/api/cron
```

### Логи:
```bash
vercel logs --follow
```

## 🆘 Проблемы?

### Ошибка 404:
- Проверьте переменные окружения в Vercel
- Сделайте redeploy
- Переустановите webhook

### Бот не отвечает:
- Проверьте webhook: должен быть установлен
- Проверьте логи в Vercel Dashboard
- Убедитесь, что вы админ (ID: 8264612178)

### Не генерируются посты:
- Проверьте GROQ_API_KEY
- Проверьте логи генерации
- Попробуйте другой промпт

### Автопубликация не работает:
- Проверьте расписание канала
- Убедитесь, что канал включен
- Проверьте cron в Vercel Dashboard

## 📚 Документация

- `README.md` - Полная документация
- `DEPLOY_READY.md` - Детальная инструкция по деплою
- `FEATURES.md` - Список всех функций
- `FIX_404.md` - Решение проблемы 404
- `FINAL_CHECKLIST.md` - Финальный чеклист

## 🎉 Готово!

Наслаждайтесь автоматической публикацией! 🚀
