"""Модуль для генерации постов с помощью AI"""
import os
import logging
from typing import Optional
from groq import Groq

logger = logging.getLogger(__name__)

class AIGenerator:
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY не установлен")
        self.client = Groq(api_key=api_key)
    
    def generate_post(self, prompt: str, theme: str = None) -> Optional[str]:
        """Генерация поста"""
        try:
            full_prompt = prompt
            if theme:
                full_prompt = f"Тематика: {theme}\n\n{prompt}"
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            post = response.choices[0].message.content.strip()
            logger.info("Пост успешно сгенерирован")
            return post
            
        except Exception as e:
            logger.error(f"Ошибка генерации поста: {e}")
            return None

# Глобальный экземпляр
_generator = None

def get_generator() -> AIGenerator:
    """Получение экземпляра генератора"""
    global _generator
    if _generator is None:
        _generator = AIGenerator()
    return _generator
