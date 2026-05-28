# backend/test_lastfm.py
import httpx
import asyncio

API_KEY = "ea9dd4b577ea35abf494ae81874e2300"

async def test_lastfm():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.getinfo",
                "artist": "Radiohead",
                "api_key": API_KEY,  # ← ВАЖНО: именно "api_key", не "apikey"
                "format": "json"
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if "error" in data:
            print(f"❌ Last.fm error: {data.get('message')}")
        else:
            print(f"✅ Success! Artist: {data['artist']['name']}")
            print(f"   Tags: {[t['name'] for t in data['artist'].get('tags', {}).get('tag', [])[:3]]}")

if __name__ == "__main__":
    asyncio.run(test_lastfm())