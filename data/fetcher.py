"""
STATDIUM — Data Fetcher
Dual-source: openfootball (no key) + football-data.org (free key)
Graceful fallback, 60s cache, unified match object
"""

import requests
import json
import time
import threading
from datetime import datetime, timezone
import os

# ── Constants ──────────────────────────────────────────────────────────────
OPENFOOTBALL_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
FD_BASE = "https://api.football-data.org/v4"
FD_KEY = os.environ.get("FD_API_KEY", "8d70004cef9b423789f0cf45fc49861a")
FD_HEADERS = {"X-Auth-Token": FD_KEY} if FD_KEY else {}
WC_ID   = 2000   # football-data.org World Cup 2026 competition ID

CACHE_TTL = 60
_lock = threading.Lock()

_cache = {
    "matches":      [],
    "groups":       {},
    "scorers":      [],
    "last_updated": None,
    "source":       "none",
}

# ── REAL 2026 groups (from openfootball) ───────────────────────────────────
WC2026_GROUPS = {
    "A": ["Mexico",    "South Africa",         "South Korea",  "Czech Republic"],
    "B": ["Canada",    "Bosnia & Herzegovina", "Qatar",        "Switzerland"],
    "C": ["Brazil",    "Morocco",              "Scotland",     "Haiti"],
    "D": ["USA",       "Paraguay",             "Australia",    "Turkey"],
    "E": ["Germany",   "Ecuador",              "Ivory Coast",  "Curaçao"],
    "F": ["Japan",     "Netherlands",          "Sweden",       "Tunisia"],
    "G": ["Belgium",   "Egypt",                "Iran",         "New Zealand"],
    "H": ["Spain",     "Cape Verde",           "Saudi Arabia", "Uruguay"],
    "I": ["France",    "Senegal",              "Iraq",         "Norway"],
    "J": ["Argentina", "Algeria",              "Austria",      "Jordan"],
    "K": ["Portugal",  "Colombia",             "Uzbekistan",   "DR Congo"],
    "L": ["England",   "Croatia",              "Ghana",        "Panama"],
}

# ── FIFA Rankings (June 2026 approx) ───────────────────────────────────────
FIFA_RANKINGS = {
    "Argentina": 1,  "France": 2,    "England": 3,   "Belgium": 4,
    "Brazil": 5,     "Portugal": 6,  "Netherlands": 7, "Spain": 8,
    "Germany": 9,    "Morocco": 10,  "Japan": 11,    "USA": 13,
    "Mexico": 14,    "Croatia": 16,  "Uruguay": 17,  "Colombia": 18,
    "South Korea": 19, "Sweden": 22, "Turkey": 26,   "Ecuador": 27,
    "Serbia": 28,    "Norway": 29,   "Ukraine": 30,  "Tunisia": 32,
    "Slovakia": 33,  "Czech Republic": 34, "Paraguay": 35, "Ghana": 36,
    "Algeria": 37,   "South Africa": 38, "Iran": 39, "Uzbekistan": 40,
    "Iraq": 41,      "Saudi Arabia": 42, "Austria": 43, "Jordan": 44,
    "New Zealand": 45, "Cape Verde": 47, "Bosnia & Herzegovina": 48,
    "Scotland": 38,  "Haiti": 72,    "Ivory Coast": 52, "Curaçao": 86,
    "Switzerland": 20, "Qatar": 58,  "Australia": 23, "DR Congo": 61,
    "Senegal": 21,   "Canada": 44,   "Panama": 55,   "Egypt": 34,
}

# ── Flag emoji ─────────────────────────────────────────────────────────────
FLAG_MAP = {
    "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪",   "Bosnia & Herzegovina": "🇧🇦", "Brazil": "🇧🇷",
    "Canada": "🇨🇦",    "Cape Verde": "🇨🇻", "Colombia": "🇨🇴",
    "Croatia": "🇭🇷",   "Curaçao": "🇨🇼",   "Czech Republic": "🇨🇿",
    "DR Congo": "🇨🇩",  "Ecuador": "🇪🇨",   "Egypt": "🇪🇬",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿","France": "🇫🇷",    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",     "Haiti": "🇭🇹",     "Iran": "🇮🇷",
    "Iraq": "🇮🇶",      "Italy": "🇮🇹",     "Ivory Coast": "🇨🇮",
    "Jamaica": "🇯🇲",   "Japan": "🇯🇵",     "Jordan": "🇯🇴",
    "Mexico": "🇲🇽",    "Morocco": "🇲🇦",   "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿", "Norway": "🇳🇴",  "Panama": "🇵🇦",
    "Paraguay": "🇵🇾",  "Portugal": "🇵🇹",  "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸",
    "Sweden": "🇸🇪",   "Switzerland": "🇨🇭", "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",   "USA": "🇺🇸",        "Ukraine": "🇺🇦",
    "Uruguay": "🇺🇾",  "Uzbekistan": "🇺🇿",  "Algeria": "🇩🇿",
}

def get_flag(name):
    return FLAG_MAP.get(name, "🏳️")


# ── openfootball ────────────────────────────────────────────────────────────
def fetch_openfootball():
    try:
        r = requests.get(OPENFOOTBALL_URL, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[openfootball] error: {e}")
    return None


def parse_openfootball(data):
    if not data:
        return [], {}

    matches = []
    group_table = {}
    raw_matches = data.get("matches", [])
    today = datetime.now(timezone.utc).date()

    for m in raw_matches:
        date_str = m.get("date", "")
        t1 = m.get("team1", "")
        t2 = m.get("team2", "")
        score = m.get("score", {}) or {}
        ft = score.get("ft") if score else None
        group = m.get("group", m.get("round", ""))
        venue = m.get("ground", "")
        time_str = m.get("time", "")

        # Scores
        h_score, a_score = None, None
        if ft and len(ft) >= 2:
            try:
                h_score = int(ft[0])
                a_score = int(ft[1])
            except:
                pass

        # Status
        try:
            match_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if h_score is not None:
                status = "FINISHED"
            elif match_date == today:
                status = "LIVE"
            elif match_date < today:
                status = "FINISHED"  # past but no score = data lag
            else:
                status = "SCHEDULED"
        except:
            status = "SCHEDULED"

        match_obj = {
            "id":         f"{date_str}_{t1}_{t2}",
            "date":       date_str,
            "time":       time_str,
            "round":      m.get("round", ""),
            "group":      group,
            "home_team":  t1,
            "away_team":  t2,
            "home_score": h_score,
            "away_score": a_score,
            "status":     status,
            "home_flag":  get_flag(t1),
            "away_flag":  get_flag(t2),
            "venue":      venue,
        }
        matches.append(match_obj)

        # Update group table for finished matches with scores
        if status == "FINISHED" and h_score is not None:
            _update_group_table(group_table, group, t1, t2, h_score, a_score)

    return matches, group_table


def _update_group_table(table, group, team1, team2, g1, g2):
    if not group:
        return
    if group not in table:
        table[group] = {}
    for t in [team1, team2]:
        if t not in table[group]:
            table[group][t] = {
                "team": t, "p": 0, "w": 0, "d": 0,
                "l": 0, "gf": 0, "ga": 0, "pts": 0
            }
    t1d = table[group][team1]
    t2d = table[group][team2]
    t1d["p"] += 1; t2d["p"] += 1
    t1d["gf"] += g1; t1d["ga"] += g2
    t2d["gf"] += g2; t2d["ga"] += g1
    if g1 > g2:
        t1d["w"] += 1; t1d["pts"] += 3; t2d["l"] += 1
    elif g2 > g1:
        t2d["w"] += 1; t2d["pts"] += 3; t1d["l"] += 1
    else:
        t1d["d"] += 1; t1d["pts"] += 1
        t2d["d"] += 1; t2d["pts"] += 1


# ── football-data.org ──────────────────────────────────────────────────────
def fetch_fd_matches():
    if not FD_KEY:
        return []
    try:
        r = requests.get(f"{FD_BASE}/competitions/{WC_ID}/matches",
                         headers=FD_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception as e:
        print(f"[football-data] matches error: {e}")
    return []


def fetch_fd_scorers():
    if not FD_KEY:
        return []
    try:
        r = requests.get(f"{FD_BASE}/competitions/{WC_ID}/scorers?limit=20",
                         headers=FD_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("scorers", [])
    except Exception as e:
        print(f"[football-data] scorers error: {e}")
    return []


def merge_fd_into_matches(matches, fd_matches):
    if not fd_matches:
        return matches
    fd_lookup = {}
    for m in fd_matches:
        home = m.get("homeTeam", {}).get("name", "")
        away = m.get("awayTeam", {}).get("name", "")
        fd_lookup[f"{home}|{away}"] = m
    updated = []
    for m in matches:
        key = f"{m['home_team']}|{m['away_team']}"
        fd = fd_lookup.get(key)
        if fd:
            score = fd.get("score", {})
            ft = score.get("fullTime", {})
            hs = ft.get("home")
            as_ = ft.get("away")
            if hs is not None:
                m["home_score"] = hs
                m["away_score"] = as_
            fd_status = fd.get("status", "")
            if fd_status:
                m["status"] = fd_status
            m["minute"] = fd.get("minute")
        updated.append(m)
    return updated


# ── Main refresh ───────────────────────────────────────────────────────────
def refresh_data():
    global _cache
    print(f"[STATDIUM] Refreshing at {datetime.now().strftime('%H:%M:%S')}...")
    raw = fetch_openfootball()
    matches, groups = parse_openfootball(raw)
    fd_matches = fetch_fd_matches()
    if fd_matches:
        matches = merge_fd_into_matches(matches, fd_matches)
    scorers = fetch_fd_scorers()
    with _lock:
        _cache["matches"]      = matches
        _cache["groups"]       = groups
        _cache["scorers"]      = scorers
        _cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        _cache["source"]       = "openfootball" + ("+fd" if fd_matches else "")
    print(f"[STATDIUM] Done — {len(matches)} matches, source={_cache['source']}")


def get_cache():
    with _lock:
        return dict(_cache)

def get_matches(status=None, group=None):
    data = get_cache()
    ms = data["matches"]
    if status:
        ms = [m for m in ms if m["status"] == status]
    if group:
        ms = [m for m in ms if group.lower() in str(m.get("group","")).lower()]
    return ms

def get_today_matches():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [m for m in get_cache()["matches"] if m.get("date","") == today]

def get_recent_matches(n=10):
    finished = [m for m in get_cache()["matches"] if m["status"] == "FINISHED"]
    return sorted(finished, key=lambda x: x["date"], reverse=True)[:n]

def get_upcoming_matches(n=10):
    scheduled = [m for m in get_cache()["matches"] if m["status"] == "SCHEDULED"]
    return sorted(scheduled, key=lambda x: x["date"])[:n]


# Initial load
refresh_data()
