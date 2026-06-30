"""
STATDIUM — Elo Intelligence Engine
Source: eloratings.net/World.tsv (free, no key, updates after every match)
Provides: live Elo ratings, Elo-based win probabilities, Poisson hybrid model,
          Elo history per team, confederation analysis
"""

import requests
import io
import time
import threading
import math
from datetime import datetime, timezone

_lock  = threading.Lock()
_cache = {"ratings": {}, "last_updated": None}
CACHE_TTL = 3600  # 1 hour

# TSV columns (reverse-engineered from eloratings.net/scripts/ratings.js)
TSV_URL  = "https://www.eloratings.net/World.tsv"
HIST_URL = "https://www.eloratings.net/{team}.tsv"  # per-team history

# Elo → confederation mapping
CONFEDERATION_MAP = {
    "Argentina":"CONMEBOL","Australia":"AFC","Austria":"UEFA","Belgium":"UEFA",
    "Bosnia & Herzegovina":"UEFA","Brazil":"CONMEBOL","Canada":"CONCACAF",
    "Cape Verde":"CAF","Colombia":"CONMEBOL","Croatia":"UEFA","Curaçao":"CONCACAF",
    "Czech Republic":"UEFA","DR Congo":"CAF","Ecuador":"CONMEBOL","Egypt":"CAF",
    "England":"UEFA","France":"UEFA","Germany":"UEFA","Ghana":"CAF","Haiti":"CONCACAF",
    "Iran":"AFC","Iraq":"AFC","Ivory Coast":"CAF","Japan":"AFC","Jordan":"AFC",
    "Mexico":"CONCACAF","Morocco":"CAF","Netherlands":"UEFA","New Zealand":"OFC",
    "Norway":"UEFA","Panama":"CONCACAF","Paraguay":"CONMEBOL","Portugal":"UEFA",
    "Qatar":"AFC","Saudi Arabia":"AFC","Scotland":"UEFA","Senegal":"CAF",
    "South Africa":"CAF","South Korea":"AFC","Spain":"UEFA","Sweden":"UEFA",
    "Switzerland":"UEFA","Tunisia":"CAF","Turkey":"UEFA","USA":"CONCACAF",
    "Ukraine":"UEFA","Uruguay":"CONMEBOL","Uzbekistan":"AFC","Algeria":"CAF",
}

# eloratings.net uses slightly different team names — map ours to theirs
ELOR_NAME_MAP = {
    "USA":          "United States",
    "South Korea":  "Korea Republic",
    "Ivory Coast":  "Côte d'Ivoire",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "DR Congo":     "DR Congo",
    "Czech Republic":"Czech Republic",
    "Curaçao":      "Curaçao",
}


def _parse_tsv(raw_text):
    """Parse eloratings World.tsv → dict of team_name: {rank, rating, ...}"""
    ratings = {}
    for line in raw_text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue
        try:
            rank   = int(parts[0])
            name   = parts[1].strip()
            rating = int(parts[2])
            # parts[3] = matches played, parts[4..] = delta columns (variable)
            ratings[name] = {"rank": rank, "rating": rating}
        except (ValueError, IndexError):
            continue
    return ratings


def fetch_elo_ratings():
    """Fetch live Elo ratings from eloratings.net/World.tsv"""
    global _cache
    now = time.time()
    with _lock:
        if _cache["last_updated"] and now - _cache["last_updated"] < CACHE_TTL:
            return _cache["ratings"]

    try:
        r = requests.get(TSV_URL, timeout=10, headers={"User-Agent": "STATDIUM/1.0"})
        if r.status_code == 200:
            ratings = _parse_tsv(r.text)
            with _lock:
                _cache["ratings"] = ratings
                _cache["last_updated"] = now
            print(f"[Elo] Fetched {len(ratings)} ratings")
            return ratings
        else:
            print(f"[Elo] TSV returned {r.status_code}")
    except Exception as e:
        print(f"[Elo] fetch error: {e}")

    with _lock:
        return _cache.get("ratings", {})


def get_elo(team_name):
    """Get Elo rating for a team (handles name mapping). Returns None if not found."""
    ratings = fetch_elo_ratings()
    mapped = ELOR_NAME_MAP.get(team_name, team_name)
    data = ratings.get(mapped) or ratings.get(team_name)
    return data["rating"] if data else None


def get_elo_rank(team_name):
    ratings = fetch_elo_ratings()
    mapped = ELOR_NAME_MAP.get(team_name, team_name)
    data = ratings.get(mapped) or ratings.get(team_name)
    return data["rank"] if data else None


def elo_win_probability(elo_a, elo_b):
    """
    Standard Elo win probability formula (used by eloratings.net)
    dr = elo_b - elo_a; P(A wins) = 1 / (1 + 10^(dr/400))
    For football, scale factor = 400 (same as chess)
    """
    if not elo_a or not elo_b:
        return 0.5, 0.25, 0.25  # equal
    dr = elo_b - elo_a
    p_a_wins = 1.0 / (1.0 + 10 ** (dr / 400.0))
    # Approximate draw probability using WC historical base rates
    # WC group stage: ~23% draws historically; adjust by closeness
    closeness = 1 - abs(p_a_wins - 0.5) * 2  # 0=big gap, 1=perfectly even
    p_draw = 0.20 + 0.08 * closeness           # 20-28% range
    p_b_wins = 1 - p_a_wins - p_draw
    return round(p_a_wins, 3), round(p_draw, 3), round(max(0, p_b_wins), 3)


def poisson_match_probs(elo_a, elo_b, avg_goals_per_team=1.35):
    """
    Hybrid Elo + Poisson model.
    Uses Elo strength ratio to set expected goals, then Poisson distribution
    to compute full scoreline probability matrix and match outcome probs.
    Returns: {
        'home_win': p, 'draw': p, 'away_win': p,
        'expected_home': λ, 'expected_away': λ,
        'score_matrix': dict of (h,a)->prob for scores 0-4
    }
    """
    import math

    if not elo_a or not elo_b:
        elo_a = elo_b = 1750

    # Elo ratio → expected goals scaling
    # Stronger team scores slightly more than average; weaker team scores less
    # λ_home = base * exp((elo_a - elo_b) / 600)
    scale = (elo_a - elo_b) / 600.0
    lam_h = avg_goals_per_team * math.exp(scale)
    lam_a = avg_goals_per_team * math.exp(-scale)

    # Clamp to realistic range
    lam_h = max(0.3, min(3.5, lam_h))
    lam_a = max(0.3, min(3.5, lam_a))

    def poisson_pmf(k, lam):
        return (lam ** k) * math.exp(-lam) / math.factorial(k)

    home_win = draw = away_win = 0.0
    score_matrix = {}
    for h in range(7):
        for a in range(7):
            p = poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)
            score_matrix[(h, a)] = round(p, 4)
            if h > a:   home_win += p
            elif h == a: draw    += p
            else:        away_win += p

    return {
        "home_win":      round(home_win, 3),
        "draw":          round(draw, 3),
        "away_win":      round(away_win, 3),
        "expected_home": round(lam_h, 2),
        "expected_away": round(lam_a, 2),
        "score_matrix":  score_matrix,
    }


def get_all_wc_elos():
    """Return Elo data for all 48 WC teams, sorted by rating desc."""
    from data.fetcher import WC2026_GROUPS
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]
    result = []
    for team in all_teams:
        rating = get_elo(team)
        rank   = get_elo_rank(team)
        conf   = CONFEDERATION_MAP.get(team, "Other")
        result.append({
            "team":          team,
            "elo":           rating or 1600,
            "elo_rank":      rank or 999,
            "confederation": conf,
        })
    result.sort(key=lambda x: x["elo"], reverse=True)
    return result


def get_confederation_stats():
    """Avg Elo + team count per confederation for the 48 WC teams."""
    teams = get_all_wc_elos()
    conf_data = {}
    for t in teams:
        c = t["confederation"]
        if c not in conf_data:
            conf_data[c] = {"teams": [], "elos": []}
        conf_data[c]["teams"].append(t["team"])
        conf_data[c]["elos"].append(t["elo"])
    result = {}
    for c, d in conf_data.items():
        elos = d["elos"]
        result[c] = {
            "count":   len(elos),
            "avg_elo": round(sum(elos) / len(elos)) if elos else 0,
            "max_elo": max(elos) if elos else 0,
            "min_elo": min(elos) if elos else 0,
            "teams":   d["teams"],
        }
    return result


# Initial fetch on import
try:
    fetch_elo_ratings()
except:
    pass

# ── Fallback Elo ratings (June 2026, from eloratings.net Top 20 + WC teams) ─
FALLBACK_ELO = {
    "Spain":2171,"Argentina":2113,"France":2063,"England":2042,
    "Colombia":1998,"Brazil":1979,"Portugal":1976,"Netherlands":1959,
    "Croatia":1933,"Ecuador":1933,"Norway":1922,"Germany":1910,
    "Switzerland":1897,"Uruguay":1890,"Turkey":1880,"Japan":1879,
    "Senegal":1869,"Belgium":1849,"Morocco":1843,"USA":1838,
    "Mexico":1816,"South Korea":1805,"Australia":1794,"Denmark":1864,
    "Scotland":1782,"Canada":1770,"South Africa":1740,"Czech Republic":1748,
    "Algeria":1744,"Panama":1695,"Egypt":1732,"Paraguay":1720,
    "Ghana":1698,"Iran":1712,"Qatar":1652,"Saudi Arabia":1640,
    "Ivory Coast":1743,"Uzbekistan":1660,"DR Congo":1635,"Haiti":1582,
    "Jordan":1610,"Cape Verde":1638,"New Zealand":1635,"Curaçao":1570,
    "Bosnia & Herzegovina":1727,"Norway":1922,"Austria":1780,
    "Tunisia":1735,"Sweden":1820,"Iraq":1620,
}

def get_elo_with_fallback(team_name):
    """Get Elo, falling back to hardcoded values if API unavailable."""
    live = get_elo(team_name)
    if live:
        return live
    mapped = ELOR_NAME_MAP.get(team_name, team_name)
    return FALLBACK_ELO.get(mapped) or FALLBACK_ELO.get(team_name) or 1650
