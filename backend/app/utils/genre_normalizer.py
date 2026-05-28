# backend/app/utils/genre_normalizer.py
from typing import List, Optional
import re

# Белый список: только музыкальные жанры
GENRE_WHITELIST = {
    # === Основные жанры ===
    "rock", "pop", "jazz", "classical", "electronic", "hip hop", "rap",
    "metal", "folk", "blues", "country", "reggae", "punk", "indie",
    "alternative", "r&b", "soul", "funk", "disco", "house", "techno",
    "trance", "dubstep", "ambient", "latin", "world", "soundtrack",
    
    # === Rock поджанры ===
    "alternative rock", "indie rock", "classic rock", "hard rock", "soft rock",
    "progressive rock", "psychedelic rock", "garage rock", "surf rock",
    "post-rock", "art rock", "glam rock", "punk rock", "pop rock",
    "folk rock", "country rock", "blues rock", "jazz rock", "funk rock",
    
    # === Metal поджанры ===
    "heavy metal", "death metal", "black metal", "thrash metal",
    "power metal", "doom metal", "progressive metal", "metalcore",
    "deathcore", "nu metal", "industrial metal", "symphonic metal",
    "folk metal", "melodic metal", "sludge metal", "stoner metal",
    
    # === Electronic поджанры ===
    "edm", "dance", "deep house", "tech house", "progressive house",
    "electro house", "minimal techno", "acid techno", "drum and bass",
    "jungle", "breakbeat", "trip hop", "downtempo", "chillout",
    "lo-fi", "synthwave", "vaporwave", "future bass", "trap",
    "hardstyle", "hardcore", "eurodance", "eurobeat", "italo disco",
    
    # === Hip-Hop/Rap поджанры ===
    "old school hip hop", "boom bap", "trap rap", "drill", "grime",
    "conscious rap", "gangsta rap", "mumble rap", "cloud rap",
    "jazz rap", "alternative hip hop", "experimental hip hop",
    
    # === Jazz поджанры ===
    "bebop", "cool jazz", "free jazz", "fusion", "smooth jazz",
    "acid jazz", "latin jazz", "avant-garde jazz", "swing",
    
    # === Classical поджанры ===
    "baroque", "romantic", "impressionist", "contemporary classical",
    "minimalism", "opera", "choral", "orchestral", "chamber music",
    
    # === Folk/World поджанры ===
    "celtic", "nordic folk", "balkan", "flamenco", "tango",
    "bossa nova", "samba", "afrobeat", "highlife", "rai",
    "qawwali", "fado", "klezmer", "bluegrass", "americana",
    
    # === Pop поджанры ===
    "synth-pop", "electropop", "indie pop", "dream pop", "shoegaze",
    "britpop", "k-pop", "j-pop", "c-pop", "latin pop", "europop",
    
    # === Experimental/Other ===
    "experimental", "avant-garde", "noise", "dark ambient",
    "post-punk", "new wave", "gothic", "industrial", "ebm",
    "ska", "reggaeton", "dancehall", "dub", "roots reggae",
    
    # === Инструментальные/настроения (только если явно музыкальные) ===
    "instrumental", "acoustic", "piano", "guitar", "orchestral",
    "cinematic", "epic", "meditation", "new age",
}

# Чёрный список: всё, что НЕ является жанром
GENRE_BLACKLIST = {
    # === Контекст прослушивания ===
    "seen live", "live", "concert", "festival", "tour",
    "my music", "my playlist", "favorites", "to listen", "wishlist",
    
    # === Настроения (слишком общие) ===
    "chill", "relaxing", "study", "workout", "party", "road trip",
    "happy", "sad", "energetic", "calm", "uplifting", "melancholic",
    "romantic", "aggressive", "peaceful", "dark", "light",
    
    # === Инструменты (не жанры) ===
    "guitar", "piano", "drums", "bass", "synthesizer", "vocals",
    "female vocalists", "male vocalists", "instrumental",
    
    # === Технические/производственные ===
    "cover", "remix", "acoustic version", "live version", "demo",
    "unplugged", "studio", "recording", "producer",
    
    # === Временные/эпохи ===
    "2010s", "2020s", "2000s", "90s", "80s", "70s", "60s",
    "vintage", "retro", "modern", "contemporary",
    
    # === Мусор/неинформативные ===
    "unknown", "misc", "other", "best", "awesome", "love", "hate",
    "good", "bad", "nice", "cool", "fire", "lit", "banger",
    "underrated", "overrated", "classic", "masterpiece",
    
    # === Языки/регионы (если не жанр) ===
    "english", "spanish", "french", "german", "russian",
    "japanese", "korean", "chinese",
}


def normalize_genre(raw_tags: List[str]) -> Optional[str]:
    """
    Принимает сырые теги из API → возвращает лучший жанр или None
    """
    if not raw_tags:
        return None
    
    # 1. Очистка и нормализация
    cleaned = []
    for tag in raw_tags:
        tag = tag.lower().strip()
        tag = re.sub(r"[^\w\s&-]", "", tag)  # убираем знаки препинания
        if tag and len(tag) > 1:  # пропускаем слишком короткие
            cleaned.append(tag)
    
    # 2. Фильтрация
    valid_genres = [
        t for t in cleaned
        if t in GENRE_WHITELIST and t not in GENRE_BLACKLIST
    ]
    
    if not valid_genres:
        return None
    
    # 3. Скоринг: считаем частоту упоминаний
    genre_scores = {g: 0 for g in valid_genres}
    for tag in cleaned:
        if tag in genre_scores:
            genre_scores[tag] += 1
    
    # Возвращаем жанр с максимальным "весом"
    return max(genre_scores, key=genre_scores.get)