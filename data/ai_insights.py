"""
STATDIUM — Match Preview Generator (template-based, no API key needed)
Generates natural-language match previews from live Elo + form data.
"""
import threading

_lock = threading.Lock()
_preview_cache = {}

def ai_enabled():
    return False  # No API key — template mode only

def generate_match_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct, match_id=None):
    if match_id and match_id in _preview_cache:
        return _preview_cache[match_id]
    text = _template_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct)
    if match_id:
        with _lock:
            _preview_cache[match_id] = text
    return text

def _template_preview(home, away, h_rank, a_rank, h_form, a_form, shock_pct):
    fav  = home if h_rank < a_rank else away
    dog  = away if h_rank < a_rank else home
    rank_gap = abs(h_rank - a_rank)
    h_pts = h_form.get("pts", 0); a_pts = a_form.get("pts", 0)
    h_gd  = h_form.get("gf", 0) - h_form.get("ga", 0)
    a_gd  = a_form.get("gf", 0) - a_form.get("ga", 0)

    if shock_pct > 65:
        return (f"🔥 High-voltage clash! {home} (#{h_rank}) vs {away} (#{a_rank}) — "
                f"both sides within {rank_gap} FIFA ranking spots. {home} carry "
                f"{h_pts}pts and GD {h_gd:+d}; {away} with {a_pts}pts and GD {a_gd:+d}. "
                f"Expect tactical intensity and goals at both ends. Shock Index: {shock_pct:.0f}%.")
    elif shock_pct > 40:
        return (f"⚡ {fav} enter as favourites (#{min(h_rank,a_rank)}) but {dog} (#{max(h_rank,a_rank)}) "
                f"have the quality to cause problems. Form: {home} {h_pts}pts · {away} {a_pts}pts. "
                f"A tight contest expected — {dog} will look to counter-attack. Shock Index: {shock_pct:.0f}%.")
    else:
        return (f"📋 {fav} (#{min(h_rank,a_rank)}) are heavy favourites over {dog} (#{max(h_rank,a_rank)}). "
                f"Ranking gap of {rank_gap} suggests a comfortable {fav} performance, "
                f"but the World Cup always delivers surprises. Shock Index: {shock_pct:.0f}%.")
