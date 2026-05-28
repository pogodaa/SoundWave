# backend/app/utils/genre_from_name.py
from typing import Optional
import re

# 🔒 Тот же whitelist, что и в genre_normalizer.py
GENRE_WHITELIST = {
    "rock", "pop", "jazz", "classical", "electronic", "hip hop", "rap",
    "metal", "folk", "blues", "country", "reggae", "punk", "indie",
    "alternative", "r&b", "soul", "funk", "disco", "house", "techno",
    "trance", "dubstep", "ambient", "latin", "world", "soundtrack",
    "lo-fi", "synthwave", "post-rock", "shoegaze", "grunge", "drum and bass",
    "trap", "k-pop", "j-pop", "edm", "dance", "hardcore", "progressive",
    "psychedelic", "garage", "surf", "ska", "swing", "acoustic", "instrumental"
}

def extract_genre_from_name(track_title: str) -> Optional[str]:
    """
    Извлекает жанр из названия трека, если в нём есть ключевое слово из whitelist.
    
    Примеры:
        "Happy Indie Ukulele" → "indie"
        "Chill Jazz Piano" → "jazz"
        "Epic Rock Anthem" → "rock"
        "Some Random Song" → None
    """
    if not track_title:
        return None
    
    # Приводим к нижнему регистру и убираем лишние символы
    title_clean = re.sub(r"[^\w\s\-&]", " ", track_title.lower())
    words = title_clean.split()
    
    # Проверяем каждое слово и словосочетания (для "hip hop", "drum and bass")
    # Сначала проверяем составные жанры (2-3 слова)
    for i in range(len(words)):
        # Проверяем 3-словные жанры: "drum and bass"
        if i + 2 < len(words):
            phrase = " ".join(words[i:i+3])
            if phrase in GENRE_WHITELIST:
                return phrase
        # Проверяем 2-словные жанры: "hip hop", "post-rock"
        if i + 1 < len(words):
            phrase = " ".join(words[i:i+2])
            if phrase in GENRE_WHITELIST:
                return phrase
    
    # Проверяем отдельные слова
    for word in words:
        if word in GENRE_WHITELIST:
            return word
    
    return None