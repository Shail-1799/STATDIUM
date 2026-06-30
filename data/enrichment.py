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

# ── Stadium capacities ────────────────────────────────────────────────────
STADIUM_CAPACITIES = {
    "MetLife Stadium (New York/New Jersey)":      82500,
    "AT&T Stadium (Dallas)":                      80000,
    "SoFi Stadium (Los Angeles)":                 70240,
    "Mercedes-Benz Stadium (Atlanta)":            71000,
    "Hard Rock Stadium (Miami)":                  64767,
    "Lincoln Financial Field (Philadelphia)":     69328,
    "Levi's Stadium (San Francisco Bay Area)":    68500,
    "NRG Stadium (Houston)":                      72220,
    "Arrowhead Stadium (Kansas City)":            76416,
    "Gillette Stadium (Boston)":                  65878,
    "Lumen Field (Seattle)":                      68740,
    "BMO Field (Toronto)":                        30000,
    "BC Place (Vancouver)":                       54500,
    "Estadio Azteca (Mexico City)":               87523,
    "Estadio Akron (Guadalajara)":                49850,
    "Estadio BBVA (Monterrey)":                   53500,
}

# ── Stadium host countries ─────────────────────────────────────────────────
STADIUM_COUNTRIES = {
    "MetLife Stadium (New York/New Jersey)":      "🇺🇸",
    "AT&T Stadium (Dallas)":                      "🇺🇸",
    "SoFi Stadium (Los Angeles)":                 "🇺🇸",
    "Mercedes-Benz Stadium (Atlanta)":            "🇺🇸",
    "Hard Rock Stadium (Miami)":                  "🇺🇸",
    "Lincoln Financial Field (Philadelphia)":     "🇺🇸",
    "Levi's Stadium (San Francisco Bay Area)":    "🇺🇸",
    "NRG Stadium (Houston)":                      "🇺🇸",
    "Arrowhead Stadium (Kansas City)":            "🇺🇸",
    "Gillette Stadium (Boston)":                  "🇺🇸",
    "Lumen Field (Seattle)":                      "🇺🇸",
    "BMO Field (Toronto)":                        "🇨🇦",
    "BC Place (Vancouver)":                       "🇨🇦",
    "Estadio Azteca (Mexico City)":               "🇲🇽",
    "Estadio Akron (Guadalajara)":                "🇲🇽",
    "Estadio BBVA (Monterrey)":                   "🇲🇽",
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
