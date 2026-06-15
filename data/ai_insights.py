"""
STATDIUM — AI Insights Module
Generates natural-language match previews, recaps, and qualification scenarios.
Uses Anthropic API if ANTHROPIC_API_KEY is set (free tier / pay-as-you-go available);
falls back to template-based generation if no key — app NEVER breaks without it.
"""
import os
import json
import threading
import time

_lock = threading.Lock()
_preview_cache = {}   # match_id -> {"text":..., "ts":...}
CACHE_TTL = 3600 * 6   # 6 hours — previews don't need to regenerate often

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

try:
    if ANTHROPIC_KEY:
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    else:
        _client = None
except Exception:
    _client = None


def _template_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct):
    """Fallback: rule-based preview, zero API cost, always works"""
    fav = home if h_rank < a_rank else away
    dog = away if h_rank < a_rank else home
    fav_rank = min(h_rank, a_rank)
    dog_rank = max(h_rank, a_rank)

    if shock_pct >= 60:
        tone = f"{dog} ({dog_rank}th) will need something special against {fav} ({fav_rank}th), but World Cup history is full of shocks — this is exactly the kind of fixture upsets are made of."
    elif shock_pct >= 35:
        tone = f"On paper {fav} ({fav_rank}th) hold the edge over {dog} ({dog_rank}th), but the gap is thin enough that anything could happen."
    else:
        tone = f"{fav} ({fav_rank}th) go in as clear favourites against {dog} ({dog_rank}th) — a routine result would be the expected outcome."

    form_note = ""
    if h_form and h_form.get("pts", 0) > 0:
        form_note = f" {home} head into this on {h_form['pts']} points with a goal difference of {h_form['gf']-h_form['ga']:+d}."

    return tone + form_note


def _template_qualification(group_letter, teams_status):
    """Rule-based qualification scenario text"""
    leader = teams_status[0]
    lines = [f"In Group {group_letter}, {leader['flag']} {leader['team']} currently top the table with {leader['pts']} points."]
    if len(teams_status) > 1:
        second = teams_status[1]
        gap = leader['pts'] - second['pts']
        if gap == 0:
            lines.append(f"{second['flag']} {second['team']} are level on points — goal difference could decide who tops the group.")
        else:
            lines.append(f"{second['flag']} {second['team']} sit {gap} point{'s' if gap!=1 else ''} behind in 2nd, the final automatic qualification spot.")
    if len(teams_status) > 2:
        third = teams_status[2]
        lines.append(f"{third['flag']} {third['team']} remain in contention for one of the 8 third-place wildcard spots.")
    return " ".join(lines)


def generate_match_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct, match_id=None):
    """Generate a 2-3 sentence match preview. Cached 6h. Falls back gracefully."""
    cache_key = match_id or f"{home}_{away}"
    now = time.time()
    with _lock:
        cached = _preview_cache.get(cache_key)
        if cached and now - cached["ts"] < CACHE_TTL:
            return cached["text"]

    # Try AI generation if client available
    if _client:
        try:
            prompt = (
                f"Write a punchy 2-sentence FIFA World Cup 2026 match preview for "
                f"{home} (FIFA rank #{h_rank}) vs {away} (FIFA rank #{a_rank}). "
                f"Upset probability is {shock_pct:.0f}%. "
                f"Be exciting but factual, no emojis, max 40 words."
            )
            resp = _client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=120,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            with _lock:
                _preview_cache[cache_key] = {"text": text, "ts": now}
            return text
        except Exception as e:
            print(f"[ai_insights] AI preview error: {e}")

    # Fallback: template
    text = _template_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct)
    with _lock:
        _preview_cache[cache_key] = {"text": text, "ts": now}
    return text


def generate_qualification_scenario(group_letter, teams_status):
    """Generate qualification scenario text. Template-based (no API needed)."""
    cache_key = f"qual_{group_letter}"
    now = time.time()
    with _lock:
        cached = _preview_cache.get(cache_key)
        if cached and now - cached["ts"] < CACHE_TTL:
            return cached["text"]

    text = _template_qualification(group_letter, teams_status)
    with _lock:
        _preview_cache[cache_key] = {"text": text, "ts": now}
    return text


def generate_match_recap(home, away, hs, as_, scorers_text=""):
    """Generate a post-match recap. AI if available, else template."""
    cache_key = f"recap_{home}_{away}_{hs}_{as_}"
    now = time.time()
    with _lock:
        cached = _preview_cache.get(cache_key)
        if cached and now - cached["ts"] < CACHE_TTL * 4:
            return cached["text"]

    if _client:
        try:
            prompt = (
                f"Write a 1-sentence FIFA World Cup 2026 result recap: "
                f"{home} {hs}-{as_} {away}. {scorers_text} "
                f"Be concise and factual, no emojis, max 25 words."
            )
            resp = _client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            with _lock:
                _preview_cache[cache_key] = {"text": text, "ts": now}
            return text
        except Exception as e:
            print(f"[ai_insights] AI recap error: {e}")

    # Template fallback
    if hs > as_:
        text = f"{home} beat {away} {hs}-{as_}."
    elif as_ > hs:
        text = f"{away} beat {home} {as_}-{hs}."
    else:
        text = f"{home} and {away} drew {hs}-{as_}."
    with _lock:
        _preview_cache[cache_key] = {"text": text, "ts": now}
    return text


def ai_enabled():
    return _client is not None
