# test_classifier.py
from backend.app.utils.keyword_genre_classifier import classify_genre_by_keywords, get_confidence_score

test_cases = [
    ("Happy Indie Ukulele", "Seastock", "indie"),
    ("Driving Indie Rock", "Muza Production", "indie rock"),
    ("Smooth Jazz Cafe", "Jazz Collective", "jazz"),
    ("Epic Rock Anthem", "Rock Band", "rock"),
    ("Chill Lo-Fi Beats", "Study Music", "lo-fi"),
    ("Techno Night", "DJ Electro", "techno"),
    ("Bossa Nova Sunset", "Brazilian Trio", "bossa nova"),
    ("Random Song Title", "Unknown Artist", None),  # должно вернуть None
]

print("🧪 Тестирование классификатора жанров:\n")
for title, artist, expected in test_cases:
    result = classify_genre_by_keywords(title, artist)
    confidence = get_confidence_score(result, title, artist) if result else 0.0
    status = "✅" if result == expected else "❌"
    print(f"{status} '{title}' by {artist}")
    print(f"   Ожидал: {expected}, Получил: {result} (confidence: {confidence:.1f})\n")