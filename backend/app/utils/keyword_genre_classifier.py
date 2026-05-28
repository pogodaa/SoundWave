# backend/app/utils/keyword_genre_classifier.py
from typing import Optional, List, Dict
import re

# 🔑 Словарь жанров → ключевые слова для поиска в названии/описании
GENRE_KEYWORDS: Dict[str, List[str]] = {
    # === Rock ===
    "rock": ["rock", "hard rock", "soft rock", "rock anthem", "rock ballad"],
    "indie rock": ["indie rock", "indie-rock", "independent rock"],
    "alternative rock": ["alt rock", "alternative rock", "alt-rock"],
    "punk rock": ["punk rock", "punk-rock", "pop punk", "pop-punk"],
    "progressive rock": ["prog rock", "progressive rock", "prog-rock"],
    "psychedelic rock": ["psychedelic rock", "psych rock", "psychedelia"],
    
    # === Pop ===
    "pop": ["pop", "pop song", "pop hit", "dance pop"],
    "indie pop": ["indie pop", "indie-pop", "bedroom pop"],
    "synth-pop": ["synth pop", "synth-pop", "electropop"],
    "k-pop": ["k-pop", "kpop", "korean pop"],
    "j-pop": ["j-pop", "jpop", "japanese pop"],
    
    # === Electronic ===
    "electronic": ["electronic", "electronica", "edm", "electro"],
    "house": ["house", "deep house", "tech house", "progressive house"],
    "techno": ["techno", "minimal techno", "acid techno"],
    "trance": ["trance", "progressive trance", "uplifting trance"],
    "dubstep": ["dubstep", "brostep", "riddim"],
    "drum and bass": ["drum and bass", "drum'n'bass", "dnb", "jungle"],
    "ambient": ["ambient", "ambient electronic", "dark ambient"],
    "lo-fi": ["lo-fi", "lofi", "chill beats", "study beats"],
    "synthwave": ["synthwave", "retrowave", "outrun", "vaporwave"],
    
    # === Hip-Hop/Rap ===
    "hip hop": ["hip hop", "hip-hop", "rap", "hiphop"],
    "trap": ["trap", "trap rap", "trap music"],
    "old school hip hop": ["old school", "boom bap", "90s hip hop"],
    "conscious rap": ["conscious", "political rap", "lyrical"],
    
    # === Jazz ===
    "jazz": ["jazz", "jazz fusion", "smooth jazz", "contemporary jazz"],
    "bebop": ["bebop", "bop"],
    "swing": ["swing", "big band", "swing jazz"],
    "bossa nova": ["bossa nova", "bossa-nova", "brazilian jazz"],
    
    # === Classical ===
    "classical": ["classical", "classical music", "orchestral"],
    "piano": ["piano solo", "piano piece", "piano composition"],
    "baroque": ["baroque", "bach", "handel", "vivaldi"],
    
    # === Folk/World ===
    "folk": ["folk", "folk music", "acoustic folk", "indie folk"],
    "country": ["country", "country music", "americana", "bluegrass"],
    "reggae": ["reggae", "roots reggae", "dub reggae"],
    "latin": ["latin", "latin music", "salsa", "tango", "flamenco"],
    "world": ["world music", "world", "ethnic", "tribal"],
    
    # === Metal ===
    "metal": ["metal", "heavy metal", "metal music"],
    "death metal": ["death metal", "deathmetal"],
    "black metal": ["black metal", "blackmetal"],
    "power metal": ["power metal", "powermetal"],
    
    # === Other ===
    "blues": ["blues", "blues rock", "electric blues"],
    "soul": ["soul", "neo-soul", "souls"],
    "funk": ["funk", "funk rock", "p-funk"],
    "disco": ["disco", "nu-disco", "disco house"],
    "soundtrack": ["soundtrack", "ost", "film score", "movie theme"],
    "instrumental": ["instrumental", "no vocals", "instrumental version"],
    "acoustic": ["acoustic", "unplugged", "acoustic version"],
}

# 🗑 Слова-исключения (чтобы не срабатывало ложно)
EXCLUSION_KEYWORDS = {
    "cover", "remix", "version", "live", "demo", "unplugged",
    "instrumental", "karaoke", "radio edit", "extended mix",
    "feat", "featuring", "ft", "vs", "mix", "mashup"
}

def classify_genre_by_keywords(
    title: Optional[str],
    artist: Optional[str] = None,
    description: Optional[str] = None
) -> Optional[str]:
    """
    Простой классификатор жанра по ключевым словам.
    
    Приоритет: точное совпадение фразы > совпадение слова > ничего
    
    Возвращает:
        - Жанр из GENRE_KEYWORDS если найдено совпадение
        - None если ничего не подошло
    """
    if not title:
        return None
    
    # Объединяем все текстовые поля для поиска
    search_text = " ".join(filter(None, [title, artist, description])).lower()
    
    # Очищаем от спецсимволов, но оставляем дефисы для составных жанров
    search_text = re.sub(r"[^\w\s\-&']", " ", search_text)
    
    # Словарь для подсчёта «веса» каждого жанра
    genre_scores: Dict[str, int] = {}
    
    # Проверяем каждый жанр и его ключевые слова
    for genre, keywords in GENRE_KEYWORDS.items():
        for keyword in keywords:
            # Точное совпадение фразы даёт +3 балла
            if keyword in search_text:
                genre_scores[genre] = genre_scores.get(genre, 0) + 3
            # Совпадение отдельных слов из фразы даёт +1 балл
            elif any(word in search_text for word in keyword.split()):
                genre_scores[genre] = genre_scores.get(genre, 0) + 1
    
    # Проверяем исключения: если есть исключающее слово — снижаем вес жанра
    for exclusion in EXCLUSION_KEYWORDS:
        if exclusion in search_text:
            # Снижаем вес всех жанров, но не обнуляем полностью
            for genre in genre_scores:
                genre_scores[genre] = max(0, genre_scores[genre] - 1)
    
    # Возвращаем жанр с максимальным весом (если вес > 0)
    if genre_scores:
        best_genre = max(genre_scores, key=genre_scores.get)
        if genre_scores[best_genre] > 0:
            return best_genre
    
    return None


def get_confidence_score(genre: Optional[str], title: str, artist: Optional[str] = None) -> float:
    """
    Возвращает «уверенность» классификатора (0.0–1.0).
    Полезно для логирования и отладки.
    """
    if not genre:
        return 0.0
    
    search_text = " ".join(filter(None, [title, artist])).lower()
    search_text = re.sub(r"[^\w\s\-&']", " ", search_text)
    
    keywords = GENRE_KEYWORDS.get(genre, [])
    
    # Считаем, сколько ключевых слов найдено
    matches = sum(1 for kw in keywords if kw in search_text)
    
    # Нормализуем: 3+ совпадения = 1.0, 1-2 = 0.5, 0 = 0.0
    if matches >= 3:
        return 1.0
    elif matches >= 1:
        return 0.5
    return 0.0