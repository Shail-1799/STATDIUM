"""
STATDIUM — Data Enrichment Module
Free, no-key sources: Open-Meteo (weather), REST Countries (country profiles)
All calls wrapped in try/except with caching — never breaks the app if a host is unreachable
"""
import requests
import threading
import time

_lock = threading.Lock()
_weather_cache = {}   # stadium_key -> {"data":..., "ts":...}
_country_cache = {}   # iso2 -> {"data":..., "ts":...}

WEATHER_TTL  = 1800   # 30 min
COUNTRY_TTL  = 86400  # 24 hr (country data never changes)

# ── World Cup 2026 host stadiums (lat/lon) ─────────────────────────────────
WC2026_STADIUMS = {
    "MetLife Stadium (New York/New Jersey)":      (40.8136, -74.0744),
    "AT&T Stadium (Dallas)":                       (32.7473, -97.0945),
    "SoFi Stadium (Los Angeles)":                  (33.9535, -118.3392),
    "Mercedes-Benz Stadium (Atlanta)":             (33.7554, -84.4008),
    "Hard Rock Stadium (Miami)":                   (25.9580, -80.2389),
    "Lincoln Financial Field (Philadelphia)":      (39.9008, -75.1675),
    "Levi's Stadium (San Francisco Bay Area)":     (37.4030, -121.9700),
    "NRG Stadium (Houston)":                       (29.6847, -95.4107),
    "Arrowhead Stadium (Kansas City)":             (39.0489, -94.4839),
    "Gillette Stadium (Boston)":                   (42.0909, -71.2643),
    "Lumen Field (Seattle)":                       (47.5952, -122.3316),
    "BMO Field (Toronto)":                         (43.6332, -79.4185),
    "BC Place (Vancouver)":                        (49.2768, -123.1119),
    "Estadio Azteca (Mexico City)":                (19.3029, -99.1505),
    "Estadio Akron (Guadalajara)":                 (20.6822, -103.4624),
    "Estadio BBVA (Monterrey)":                    (25.6694, -100.2436),
}

# ── ISO3166 alpha-2 codes for REST Countries ───────────────────────────────
ISO2_MAP = {
    "Argentina":"AR","Australia":"AU","Austria":"AT","Belgium":"BE",
    "Bosnia & Herzegovina":"BA","Brazil":"BR","Canada":"CA","Cape Verde":"CV",
    "Colombia":"CO","Croatia":"HR","Curaçao":"CW","Czech Republic":"CZ",
    "DR Congo":"CD","Ecuador":"EC","Egypt":"EG","England":"GB",
    "France":"FR","Germany":"DE","Ghana":"GH","Haiti":"HT","Iran":"IR",
    "Iraq":"IQ","Ivory Coast":"CI","Japan":"JP","Jordan":"JO",
    "Mexico":"MX","Morocco":"MA","Netherlands":"NL","New Zealand":"NZ",
    "Norway":"NO","Panama":"PA","Paraguay":"PY","Portugal":"PT","Qatar":"QA",
    "Saudi Arabia":"SA","Scotland":"GB","Senegal":"SN","South Africa":"ZA",
    "South Korea":"KR","Spain":"ES","Sweden":"SE","Switzerland":"CH",
    "Tunisia":"TN","Turkey":"TR","USA":"US","Ukraine":"UA","Uruguay":"UY",
    "Uzbekistan":"UZ","Algeria":"DZ",
}

WEATHER_CODES = {
    0:"☀️ Clear sky", 1:"🌤️ Mainly clear", 2:"⛅ Partly cloudy", 3:"☁️ Overcast",
    45:"🌫️ Fog", 48:"🌫️ Fog", 51:"🌦️ Light drizzle", 53:"🌦️ Drizzle",
    55:"🌧️ Dense drizzle", 61:"🌧️ Light rain", 63:"🌧️ Rain", 65:"🌧️ Heavy rain",
    71:"🌨️ Light snow", 73:"🌨️ Snow", 75:"🌨️ Heavy snow", 80:"🌦️ Rain showers",
    81:"🌧️ Rain showers", 82:"⛈️ Violent showers", 95:"⛈️ Thunderstorm",
    96:"⛈️ Thunderstorm + hail", 99:"⛈️ Severe thunderstorm",
}

def get_weather_label(code):
    return WEATHER_CODES.get(code, "🌡️ Unknown")


def fetch_stadium_weather(stadium_name):
    """Fetch current + 3-day forecast for a stadium. Cached 30 min."""
    now = time.time()
    with _lock:
        cached = _weather_cache.get(stadium_name)
        if cached and now - cached["ts"] < WEATHER_TTL:
            return cached["data"]

    coords = WC2026_STADIUMS.get(stadium_name)
    if not coords:
        return None

    lat, lon = coords
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current_weather": True,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=6,
        )
        if r.status_code == 200:
            data = r.json()
            with _lock:
                _weather_cache[stadium_name] = {"data": data, "ts": now}
            return data
    except Exception as e:
        print(f"[enrichment] weather error for {stadium_name}: {e}")
    return None


def fetch_country_profile(team_name):
    """Fetch REST Countries profile (population, region, flag svg, capital). Cached 24h."""
    iso2 = ISO2_MAP.get(team_name)
    if not iso2:
        return None

    now = time.time()
    with _lock:
        cached = _country_cache.get(iso2)
        if cached and now - cached["ts"] < COUNTRY_TTL:
            return cached["data"]

    try:
        r = requests.get(f"https://restcountries.com/v3.1/alpha/{iso2}", timeout=6)
        if r.status_code == 200:
            data = r.json()
            profile = data[0] if isinstance(data, list) else data
            result = {
                "name": profile.get("name", {}).get("common", team_name),
                "capital": (profile.get("capital") or ["—"])[0],
                "region": profile.get("region", "—"),
                "subregion": profile.get("subregion", "—"),
                "population": profile.get("population", 0),
                "flag_svg": profile.get("flags", {}).get("svg", ""),
                "maps": profile.get("maps", {}).get("googleMaps", ""),
                "languages": list((profile.get("languages") or {}).values()),
            }
            with _lock:
                _country_cache[iso2] = {"data": result, "ts": now}
            return result
    except Exception as e:
        print(f"[enrichment] country error for {team_name}: {e}")
    return None


def get_match_venue_coords(venue_name):
    """Fuzzy-match a venue string from openfootball to our stadium coords"""
    if not venue_name:
        return None
    venue_lower = venue_name.lower()
    for stadium, coords in WC2026_STADIUMS.items():
        # Match on city name fragment
        city_part = stadium.split("(")[-1].replace(")", "").lower()
        if city_part in venue_lower or venue_lower in stadium.lower():
            return stadium, coords
    return None


# ── Wikipedia free thumbnail API (no key) — team badge/photo ──────────────
WIKI_PAGE_MAP = {
    "Brazil":"Brazil_national_football_team","France":"France_national_football_team",
    "Argentina":"Argentina_national_football_team","England":"England_national_football_team",
    "Spain":"Spain_national_football_team","Germany":"Germany_national_football_team",
    "Portugal":"Portugal_national_football_team","Netherlands":"Netherlands_national_football_team",
    "Belgium":"Belgium_national_football_team","Morocco":"Morocco_national_football_team",
    "USA":"United_States_men's_national_soccer_team","Mexico":"Mexico_national_football_team",
    "Croatia":"Croatia_national_football_team","Uruguay":"Uruguay_national_football_team",
    "Colombia":"Colombia_national_football_team","Japan":"Japan_national_football_team",
    "South Korea":"South_Korea_national_football_team","Senegal":"Senegal_national_football_team",
    "Norway":"Norway_national_football_team","Switzerland":"Switzerland_national_football_team",
    "Canada":"Canada_men's_national_soccer_team","Ecuador":"Ecuador_national_football_team",
}
_wiki_cache = {}

def fetch_team_wiki_image(team_name):
    """Fetch team badge/photo thumbnail from Wikipedia REST API. Cached forever (static)."""
    if team_name in _wiki_cache:
        return _wiki_cache[team_name]
    page = WIKI_PAGE_MAP.get(team_name)
    if not page:
        return None
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{page}", timeout=6)
        if r.status_code == 200:
            data = r.json()
            thumb = data.get("thumbnail", {}).get("source")
            with _lock:
                _wiki_cache[team_name] = thumb
            return thumb
    except Exception as e:
        print(f"[enrichment] wiki image error for {team_name}: {e}")
    with _lock:
        _wiki_cache[team_name] = None
    return None


# ── "Hype Theme" concept — viral-style cultural angle per nation ──────────
# Inspired by the Norway "Vikings" theme going viral. Gives each team a
# punchy nickname + emoji motif + accent color for shareable team cards.
TEAM_HYPE_THEMES = {
    "Norway":        {"nickname":"THE VIKINGS",       "motif":"⚔️", "tagline":"Raiding the World Cup", "color":"#A91D1D"},
    "Brazil":        {"nickname":"THE SAMBA KINGS",   "motif":"⭐", "tagline":"Joga Bonito, always",    "color":"#FFD700"},
    "Argentina":     {"nickname":"LA ALBICELESTE",    "motif":"🐐", "tagline":"Three stars, one dream",  "color":"#75AADB"},
    "France":        {"nickname":"LES BLEUS",         "motif":"🐓", "tagline":"Allez les Bleus",         "color":"#0055A4"},
    "England":       {"nickname":"THE THREE LIONS",   "motif":"🦁", "tagline":"It's coming home?",       "color":"#CE1124"},
    "Germany":       {"nickname":"DIE MANNSCHAFT",    "motif":"🦅", "tagline":"Efficiency personified",  "color":"#000000"},
    "Spain":         {"nickname":"LA ROJA",           "motif":"🔥", "tagline":"Tiki-taka returns",        "color":"#C60B1E"},
    "Portugal":      {"nickname":"A SELEÇÃO",         "motif":"⚜️", "tagline":"One last dance",          "color":"#006600"},
    "Netherlands":   {"nickname":"THE ORANGE ARMY",   "motif":"🧡", "tagline":"Total Football lives",    "color":"#FF6600"},
    "Belgium":       {"nickname":"THE RED DEVILS",    "motif":"😈", "tagline":"Golden Generation 2.0",    "color":"#ED2939"},
    "Morocco":       {"nickname":"THE ATLAS LIONS",   "motif":"🦁", "tagline":"Africa's pride",           "color":"#C1272D"},
    "Croatia":       {"nickname":"THE CHECKERED ARMY","motif":"🏁", "tagline":"Small nation, big heart",  "color":"#FF0000"},
    "Japan":         {"nickname":"THE SAMURAI BLUE",  "motif":"⚔️", "tagline":"Disciplined and dangerous","color":"#000080"},
    "South Korea":   {"nickname":"THE TAEGEUK WARRIORS","motif":"🐯","tagline":"Speed and spirit",        "color":"#C60C30"},
    "USA":           {"nickname":"THE STARS & STRIPES","motif":"🦅","tagline":"Home soil, high hopes",    "color":"#002868"},
    "Mexico":        {"nickname":"EL TRI",            "motif":"🌵", "tagline":"Three's the charm at home","color":"#006847"},
    "Senegal":       {"nickname":"THE LIONS OF TERANGA","motif":"🦁","tagline":"Roaring through the draw","color":"#00853F"},
    "Uruguay":       {"nickname":"LA CELESTE",        "motif":"☀️", "tagline":"Punching above their weight","color":"#7FB3D5"},
    "Switzerland":   {"nickname":"DIE NATI",          "motif":"🏔️", "tagline":"Precision engineering",    "color":"#FF0000"},
    "Canada":        {"nickname":"LES ROUGES",        "motif":"🍁", "tagline":"North American breakout",  "color":"#FF0000"},
    "Colombia":      {"nickname":"LOS CAFETEROS",     "motif":"☕", "tagline":"Coffee-fueled chaos",       "color":"#FCD116"},
    "Ecuador":       {"nickname":"LA TRI",            "motif":"🌋", "tagline":"High altitude, high hopes","color":"#FFD100"},
}

def get_hype_theme(team_name):
    """Returns a viral-style theme dict for a team, or a generic default."""
    return TEAM_HYPE_THEMES.get(team_name, {
        "nickname": team_name.upper(), "motif": "⚽",
        "tagline": "Chasing the trophy", "color": "#00E5A0",
    })
