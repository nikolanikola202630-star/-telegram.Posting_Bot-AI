"""Скрипт для добавления переменных окружения в Vercel"""
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

# Переменные для добавления
env_vars = {
    'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
    'ADMIN_USER_ID': os.getenv('ADMIN_USER_ID'),
    'DATABASE_URL': os.getenv('DATABASE_URL')
}

print("=" * 60)
print("🔧 Добавление переменных окружения в Vercel")
print("=" * 60)

for key, value in env_vars.items():
    if not value:
        print(f"⚠️  {key}: не найден в .env")
        continue
    
    print(f"\n📝 Добавление {key}...")
    
    # Команда для добавления переменной
    cmd = f'echo "{value}" | vercel env add {key} production'
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            input=f"{value}\n"
        )
        
        if result.returncode == 0:
            print(f"✅ {key} добавлен")
        else:
            print(f"❌ Ошибка добавления {key}")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n" + "=" * 60)
print("✅ Готово! Теперь нужно сделать redeploy:")
print("   vercel --prod")
print("=" * 60)
