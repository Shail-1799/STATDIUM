"""
STATDIUM — Media & External Links
Watch Live → FIFA+ (official free streaming)
Watch Highlights → YouTube search (working URL format)
"""
from urllib.parse import quote

FIFA_PLUS_LIVE = "https://www.fifaplus.com/en/live"
FOX_LIVE = "https://www.fox.com/soccer/fifa-world-cup"

def get_watch_live_url(home_team=None, away_team=None):
    """Direct link to FIFA+ live hub — official free global streamer."""
    return FOX_LIVE

def get_watch_highlights_search_url(home_team, away_team, match_date=None):
    """YouTube search for highlights — uses standard search URL (not channel-specific)."""
    query = quote(f"{home_team} vs {away_team} highlights FIFA World Cup 2026")
    return f"https://www.youtube.com/results?search_query={query}"

def get_highlights_embed_search(home_team, away_team):
    query = quote(f"{home_team} vs {away_team} highlights FIFA World Cup 2026")
    return f"https://www.youtube.com/results?search_query={query}"

def get_stadium_maps_embed_url(lat, lon, zoom=15):
    return f"https://maps.google.com/maps?q={lat},{lon}&z={zoom}&output=embed"

def get_stadium_maps_link(lat, lon, stadium_name=""):
    query = quote(stadium_name) if stadium_name else f"{lat},{lon}"
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
