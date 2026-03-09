"""Модуль для анализа контента канала и проверки уникальности"""
import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Анализатор контента для проверки уникальности постов"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Args:
            similarity_threshold: Порог схожести (0-1). Если схожесть выше - пост считается дубликатом
        """
        self.similarity_threshold = similarity_threshold
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести двух текстов"""
        if not text1 or not text2:
            return 0.0
        
        # Нормализация текстов
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Вычисление схожести
        return SequenceMatcher(None, text1, text2).ratio()
    
    def is_duplicate(self, new_post: str, existing_posts: List[str]) -> tuple[bool, Optional[str]]:
        """
        Проверка, является ли новый пост дубликатом
        
        Returns:
            (is_duplicate, similar_post): True если дубликат, и текст похожего поста
        """
        if not existing_posts:
            return False, None
        
        for existing_post in existing_posts:
            similarity = self.calculate_similarity(new_post, existing_post)
            
            if similarity >= self.similarity_threshold:
                logger.warning(f"Найден дубликат! Схожесть: {similarity:.2%}")
                return True, existing_post
        
        return False, None
    
    def get_unique_keywords(self, text: str) -> set:
        """Извлечение ключевых слов из текста"""
        # Простое извлечение слов (можно улучшить с помощью NLP)
        words = text.lower().split()
        # Фильтруем короткие слова и стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'как', 'что', 'это', 'не', 'а', 'но'}
        keywords = {word for word in words if len(word) > 3 and word not in stop_words}
        return keywords
    
    def analyze_channel_content(self, posts: List[Dict]) -> Dict:
        """
        Анализ контента канала
        
        Returns:
            Статистика по каналу
        """
        if not posts:
            return {
                'total_posts': 0,
                'unique_posts': 0,
                'duplicate_rate': 0.0,
                'common_keywords': [],
                'avg_post_length': 0
            }
        
        total_posts = len(posts)
        post_texts = [p.get('post_text', '') for p in posts]
        
        # Подсчет уникальных постов
        unique_count = 0
        checked = set()
        
        for i, text1 in enumerate(post_texts):
            if i in checked:
                continue
            
            is_unique = True
            for j, text2 in enumerate(post_texts[i+1:], start=i+1):
                if self.calculate_similarity(text1, text2) >= self.similarity_threshold:
                    checked.add(j)
                    is_unique = False
            
            if is_unique:
                unique_count += 1
        
        # Извлечение общих ключевых слов
        all_keywords = []
        for text in post_texts:
            all_keywords.extend(self.get_unique_keywords(text))
        
        # Подсчет частоты ключевых слов
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Топ-10 ключевых слов
        common_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Средняя длина поста
        avg_length = sum(len(text) for text in post_texts) / total_posts if total_posts > 0 else 0
        
        return {
            'total_posts': total_posts,
            'unique_posts': unique_count,
            'duplicate_rate': (total_posts - unique_count) / total_posts if total_posts > 0 else 0,
            'common_keywords': [kw for kw, _ in common_keywords],
            'avg_post_length': int(avg_length)
        }
    
    def generate_unique_prompt(self, base_prompt: str, channel_stats: Dict, recent_posts: List[str]) -> str:
        """
        Генерация промпта с учетом анализа канала для создания уникального контента
        
        Args:
            base_prompt: Базовый промпт пользователя
            channel_stats: Статистика канала
            recent_posts: Последние посты для избежания повторений
        
        Returns:
            Улучшенный промпт
        """
        enhanced_prompt = base_prompt
        
        # Добавляем инструкции по уникальности
        enhanced_prompt += "\n\nВАЖНО: Создай УНИКАЛЬНЫЙ контент, который НЕ повторяет следующие темы:"
        
        # Добавляем ключевые слова из последних постов
        if recent_posts:
            recent_keywords = set()
            for post in recent_posts[-5:]:  # Последние 5 постов
                recent_keywords.update(self.get_unique_keywords(post))
            
            if recent_keywords:
                enhanced_prompt += f"\nИзбегай повторения этих тем: {', '.join(list(recent_keywords)[:10])}"
        
        # Добавляем статистику
        if channel_stats.get('common_keywords'):
            enhanced_prompt += f"\nЧасто используемые темы в канале: {', '.join(channel_stats['common_keywords'][:5])}"
            enhanced_prompt += "\nПопробуй найти новый угол или аспект этих тем."
        
        enhanced_prompt += "\n\nСоздай свежий, оригинальный контент с новой перспективой!"
        
        return enhanced_prompt

# Глобальный экземпляр
_analyzer = None

def get_analyzer() -> ContentAnalyzer:
    """Получение экземпляра анализатора"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ContentAnalyzer(similarity_threshold=0.7)
    return _analyzer
