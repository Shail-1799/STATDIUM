"""
STATDIUM — Data Fetcher
Sources: openfootball (no key) + football-data.org v4 (free key)
FD free tier: matches, standings, scorers, teams (with crest URLs)
"""
import requests, json, time, threading, os
from datetime import datetime, timezone

OPENFOOTBALL_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
FD_BASE    = "https://api.football-data.org/v4"
FD_KEY     = os.getenv("FD_API_KEY", "")
FD_HEADERS = {"X-Auth-Token": FD_KEY} if FD_KEY else {}
WC_ID      = 2000   # football-data.org WC 2026 competition ID

CACHE_TTL = 60
_lock = threading.Lock()
_cache = {
    "matches":[], "groups":{}, "scorers":[], "teams":{},
    "last_updated":None, "source":"none",
}

# ── WC 2026 Groups ─────────────────────────────────────────────────────────
WC2026_GROUPS = {
    "A":["Mexico","South Africa","South Korea","Czech Republic"],
    "B":["Canada","Bosnia & Herzegovina","Qatar","Switzerland"],
    "C":["Brazil","Morocco","Scotland","Haiti"],
    "D":["USA","Paraguay","Australia","Turkey"],
    "E":["Germany","Ecuador","Ivory Coast","Curaçao"],
    "F":["Japan","Netherlands","Sweden","Tunisia"],
    "G":["Belgium","Egypt","Iran","New Zealand"],
    "H":["Spain","Cape Verde","Saudi Arabia","Uruguay"],
    "I":["France","Senegal","Iraq","Norway"],
    "J":["Argentina","Algeria","Austria","Jordan"],
    "K":["Portugal","Colombia","Uzbekistan","DR Congo"],
    "L":["England","Croatia","Ghana","Panama"],
}

FIFA_RANKINGS = {
    "Argentina":1,"France":2,"England":3,"Belgium":4,"Brazil":5,
    "Portugal":6,"Netherlands":7,"Spain":8,"Germany":9,"Morocco":10,
    "Japan":11,"USA":13,"Mexico":14,"Croatia":16,"Uruguay":17,
    "Colombia":18,"South Korea":19,"Switzerland":20,"Senegal":21,
    "Sweden":22,"Australia":23,"Norway":29,"Ecuador":27,"Turkey":26,
    "Czech Republic":34,"Paraguay":35,"Ghana":36,"Algeria":37,
    "South Africa":38,"Scotland":38,"Iran":39,"Uzbekistan":40,
    "Iraq":41,"Saudi Arabia":42,"Austria":43,"Jordan":44,"Canada":44,
    "New Zealand":45,"Cape Verde":47,"Bosnia & Herzegovina":48,
    "Panama":55,"Qatar":58,"DR Congo":61,"Haiti":72,"Ivory Coast":52,
    "Curaçao":86,"Egypt":34,"Tunisia":32,
}

FLAG_MAP = {
    "Argentina":"🇦🇷","Australia":"🇦🇺","Austria":"🇦🇹","Belgium":"🇧🇪",
    "Bosnia & Herzegovina":"🇧🇦","Brazil":"🇧🇷","Canada":"🇨🇦","Cape Verde":"🇨🇻",
    "Colombia":"🇨🇴","Croatia":"🇭🇷","Curaçao":"🇨🇼","Czech Republic":"🇨🇿",
    "DR Congo":"🇨🇩","Ecuador":"🇪🇨","Egypt":"🇪🇬","England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France":"🇫🇷","Germany":"🇩🇪","Ghana":"🇬🇭","Haiti":"🇭🇹","Iran":"🇮🇷",
    "Iraq":"🇮🇶","Italy":"🇮🇹","Ivory Coast":"🇨🇮","Jamaica":"🇯🇲","Japan":"🇯🇵",
    "Jordan":"🇯🇴","Mexico":"🇲🇽","Morocco":"🇲🇦","Netherlands":"🇳🇱",
    "New Zealand":"🇳🇿","Norway":"🇳🇴","Panama":"🇵🇦","Paraguay":"🇵🇾",
    "Portugal":"🇵🇹","Qatar":"🇶🇦","Saudi Arabia":"🇸🇦","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Senegal":"🇸🇳","South Africa":"🇿🇦","South Korea":"🇰🇷","Spain":"🇪🇸",
    "Sweden":"🇸🇪","Switzerland":"🇨🇭","Tunisia":"🇹🇳","Turkey":"🇹🇷",
    "USA":"🇺🇸","Ukraine":"🇺🇦","Uruguay":"🇺🇾","Uzbekistan":"🇺🇿","Algeria":"🇩🇿",
}

ISO2_MAP = {
    "Argentina":"ar","Australia":"au","Austria":"at","Belgium":"be",
    "Bosnia & Herzegovina":"ba","Brazil":"br","Canada":"ca","Cape Verde":"cv",
    "Colombia":"co","Croatia":"hr","Curaçao":"cw","Czech Republic":"cz",
    "DR Congo":"cd","Ecuador":"ec","Egypt":"eg","England":"gb-eng",
    "France":"fr","Germany":"de","Ghana":"gh","Haiti":"ht","Iran":"ir",
    "Iraq":"iq","Italy":"it","Ivory Coast":"ci","Jamaica":"jm","Japan":"jp",
    "Jordan":"jo","Mexico":"mx","Morocco":"ma","Netherlands":"nl",
    "New Zealand":"nz","Norway":"no","Panama":"pa","Paraguay":"py",
    "Portugal":"pt","Qatar":"qa","Saudi Arabia":"sa","Scotland":"gb-sct",
    "Senegal":"sn","South Africa":"za","South Korea":"kr","Spain":"es",
    "Sweden":"se","Switzerland":"ch","Tunisia":"tn","Turkey":"tr",
    "USA":"us","Ukraine":"ua","Uruguay":"uy","Uzbekistan":"uz","Algeria":"dz",
}

def get_flag(name):       return FLAG_MAP.get(name,"🏳️")
def get_flag_url(name, width=40):
    code = ISO2_MAP.get(name)
    if not code: return None
    w = min([20,40,80,160,320], key=lambda x:abs(x-width))
    return f"https://flagcdn.com/w{w}/{code}.png"

def get_flag_img(name, width=40, style=None):
    from dash import html
    w = min([20,40,80,160,320], key=lambda x:abs(x-width))
    url = get_flag_url(name, width=w)
    s = {"width":f"{width}px","height":"auto","verticalAlign":"middle",
         "borderRadius":"2px","boxShadow":"0 1px 3px rgba(0,0,0,0.4)","display":"inline-block"}
    if style: s.update(style)
    if url: return html.Img(src=url, style=s, alt=name, title=name)
    return html.Span(get_flag(name), style={"fontSize":f"{int(width*0.8)}px"})

def get_crest_img(team_name, width=32, style=None):
    """Return team crest from FD API cache, fallback to flag."""
    from dash import html
    with _lock:
        crest_url = _cache.get("teams",{}).get(team_name)
    if crest_url:
        s = {"width":f"{width}px","height":f"{width}px","objectFit":"contain",
             "display":"inline-block","verticalAlign":"middle"}
        if style: s.update(style)
        return html.Img(src=crest_url, style=s, alt=team_name, title=team_name,
                        className="team-crest")
    return get_flag_img(team_name, width=width, style=style)

# ── openfootball ────────────────────────────────────────────────────────────
def fetch_openfootball():
    try:
        r = requests.get(OPENFOOTBALL_URL, timeout=10)
        if r.status_code == 200: return r.json()
    except Exception as e: print(f"[openfootball] {e}")
    return None

def parse_openfootball(data):
    if not data: return [], {}
    matches, group_table = [], {}
    today = datetime.now(timezone.utc).date()
    for m in data.get("matches",[]):
        date_str = m.get("date","")
        t1,t2 = m.get("team1",""), m.get("team2","")
        score = m.get("score",{}) or {}
        ft    = score.get("ft") if score else None
        group,venue,time_str = m.get("group",m.get("round","")), m.get("ground",""), m.get("time","")
        h_score=a_score=None
        if ft and len(ft)>=2:
            try: h_score=int(ft[0]); a_score=int(ft[1])
            except: pass
        try:
            md = datetime.strptime(date_str,"%Y-%m-%d").date()
            if h_score is not None:
                status = "FINISHED"
            elif md == today:
                # Today: check time — if no score yet, mark LIVE (FD will clarify)
                status = "LIVE"
            elif md < today:
                # Past date with no score: still mark FINISHED
                # FD will provide the actual score via merge
                status = "FINISHED"
            else:
                status = "SCHEDULED"
        except: status="SCHEDULED"
        matches.append({
            "id":f"{date_str}_{t1}_{t2}","date":date_str,"time":time_str,
            "round":m.get("round",""),"group":group,
            "home_team":t1,"away_team":t2,
            "home_score":h_score,"away_score":a_score,"status":status,
            "home_flag":get_flag(t1),"away_flag":get_flag(t2),
            "venue":venue,
            "goals1":m.get("goals1",[]) or [],"goals2":m.get("goals2",[]) or [],
        })
        if status=="FINISHED" and h_score is not None:
            _update_group_table(group_table, group, t1, t2, h_score, a_score)
    return matches, group_table

def build_scorers_from_matches(matches):
    scorer_map={}
    for m in matches:
        if m["status"]!="FINISHED": continue
        for g in m.get("goals1",[]):
            n=g.get("name","")
            if not n or "og" in n.lower(): continue
            if n not in scorer_map: scorer_map[n]={"name":n,"team":m["home_team"],"goals":0,"assists":0,"games":0}
            scorer_map[n]["goals"]+=1
        for g in m.get("goals2",[]):
            n=g.get("name","")
            if not n or "og" in n.lower(): continue
            if n not in scorer_map: scorer_map[n]={"name":n,"team":m["away_team"],"goals":0,"assists":0,"games":0}
            scorer_map[n]["goals"]+=1
    return sorted(scorer_map.values(), key=lambda x:x["goals"], reverse=True)

def _update_group_table(table, group, t1, t2, g1, g2):
    if not group: return
    if group not in table: table[group]={}
    for t in [t1,t2]:
        if t not in table[group]:
            table[group][t]={"team":t,"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0}
    a,b = table[group][t1], table[group][t2]
    a["p"]+=1; b["p"]+=1; a["gf"]+=g1; a["ga"]+=g2; b["gf"]+=g2; b["ga"]+=g1
    if g1>g2:   a["w"]+=1; a["pts"]+=3; b["l"]+=1
    elif g2>g1: b["w"]+=1; b["pts"]+=3; a["l"]+=1
    else:       a["d"]+=1; a["pts"]+=1; b["d"]+=1; b["pts"]+=1

# ── football-data.org ──────────────────────────────────────────────────────
def fetch_fd_matches():
    if not FD_KEY: return []
    try:
        r = requests.get(f"{FD_BASE}/competitions/{WC_ID}/matches",
                         headers=FD_HEADERS, timeout=10)
        if r.status_code==200: return r.json().get("matches",[])
    except Exception as e: print(f"[FD matches] {e}")
    return []

def fetch_fd_scorers():
    if not FD_KEY: return []
    try:
        r = requests.get(f"{FD_BASE}/competitions/{WC_ID}/scorers?limit=20",
                         headers=FD_HEADERS, timeout=10)
        if r.status_code==200: return r.json().get("scorers",[])
    except Exception as e: print(f"[FD scorers] {e}")
    return []

def fetch_fd_teams():
    """Fetch team crests from FD. Tries WC 2026 competition, falls back to team search."""
    if not FD_KEY: return {}
    all_our_teams = [t for grp in WC2026_GROUPS.values() for t in grp]
    crest_map = {}

    # Try competition endpoint (WC_ID=2000 for FIFA World Cup on FD)
    for comp_id in [2000, "WC"]:
        try:
            r = requests.get(f"{FD_BASE}/competitions/{comp_id}/teams",
                             headers=FD_HEADERS, timeout=10)
            if r.status_code == 200:
                teams = r.json().get("teams", [])
                for t in teams:
                    fd_name  = t.get("name","") or ""
                    fd_short = t.get("shortName","") or ""
                    fd_tla   = t.get("tla","") or ""
                    crest    = t.get("crest","") or t.get("crestUrl","") or ""
                    if not crest: continue
                    for our in all_our_teams:
                        our_l = our.lower()
                        if (our_l in fd_name.lower() or fd_name.lower() in our_l or
                            our_l in fd_short.lower() or fd_short.lower() in our_l):
                            crest_map[our] = crest
                            break
                if crest_map:
                    print(f"[FD teams] {len(crest_map)} crests from comp {comp_id}")
                    return crest_map
        except Exception as e:
            print(f"[FD teams comp {comp_id}] {e}")

    # Fallback: search each team individually (slow but reliable)
    print("[FD teams] Falling back to individual team search")
    for team_name in all_our_teams[:16]:  # limit to avoid rate limit
        try:
            r = requests.get(f"{FD_BASE}/teams?name={requests.utils.quote(team_name)}",
                             headers=FD_HEADERS, timeout=5)
            if r.status_code == 200:
                results = r.json().get("teams", [])
                for t in results:
                    crest = t.get("crest","") or t.get("crestUrl","")
                    if crest:
                        crest_map[team_name] = crest
                        break
        except Exception:
            pass

    print(f"[FD teams] Got {len(crest_map)} crests total")
    return crest_map

def parse_fd_scorers(fd_scorers):
    """Convert FD scorer format to our internal format."""
    result = []
    for s in fd_scorers:
        player = s.get("player",{}) or {}
        team   = s.get("team",{})   or {}
        name   = player.get("name","")
        if not name: continue
        # Map FD team name to our internal name
        fd_team = team.get("name","") or team.get("shortName","")
        our_team = _fd_team_to_ours(fd_team)
        result.append({
            "name":    name,
            "team":    our_team or fd_team,
            "goals":   s.get("goals",0) or 0,
            "assists": s.get("assists",0) or 0,
            "games":   s.get("playedMatches",0) or 0,
            "photo":   player.get("photo","") or "",
        })
    return result

def _fd_team_to_ours(fd_name):
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]
    fd_lower  = fd_name.lower()
    for our in all_teams:
        if our.lower() in fd_lower or fd_lower in our.lower():
            return our
    return fd_name

def merge_fd_into_matches(matches, fd_matches):
    """
    Merge FD data into openfootball matches.
    IMPORTANT: Never downgrade a FINISHED match to SCHEDULED/TIMED.
    openfootball has the scores; FD free tier is often delayed.
    Only use FD status to UPGRADE (e.g. SCHEDULED -> LIVE -> FINISHED).
    """
    if not fd_matches: return matches

    # Build FD lookup by team names (FD uses full names, may differ from openfootball)
    fd_lookup = {}
    for m in fd_matches:
        h = (m.get("homeTeam",{}) or {}).get("name","")
        a = (m.get("awayTeam",{}) or {}).get("name","")
        if h and a:
            fd_lookup[f"{h}|{a}"] = m

    STATUS_RANK = {"FINISHED":4, "IN_PLAY":3, "PAUSED":3, "LIVE":3,
                   "TIMED":1, "SCHEDULED":1, "POSTPONED":0}

    updated = []
    for m in matches:
        # Try exact match first, then fuzzy
        fd = fd_lookup.get(f"{m['home_team']}|{m['away_team']}")
        if not fd:
            # Fuzzy: check if any FD key matches our teams partially
            hl, al = m['home_team'].lower(), m['away_team'].lower()
            for key, fmatch in fd_lookup.items():
                kh, ka = key.split("|", 1)
                if ((hl[:4] in kh.lower() or kh.lower()[:4] in hl) and
                    (al[:4] in ka.lower() or ka.lower()[:4] in al)):
                    fd = fmatch
                    break

        if fd:
            fd_status = fd.get("status","") or ""
            our_status = m.get("status","SCHEDULED")

            # Only update score if FD has it
            score = fd.get("score",{}) or {}
            ft    = score.get("fullTime",{}) or {}
            hs, as_ = ft.get("home"), ft.get("away")
            if hs is not None and as_ is not None:
                m["home_score"] = hs
                m["away_score"] = as_

            # Only upgrade status, never downgrade a FINISHED match
            our_rank = STATUS_RANK.get(our_status, 0)
            fd_rank  = STATUS_RANK.get(fd_status, 0)
            if fd_rank > our_rank:
                m["status"] = fd_status
            # Map FD live statuses to our LIVE
            if fd_status in ("IN_PLAY","PAUSED"):
                m["status"] = "LIVE"
                m["minute"] = fd.get("minute")

        updated.append(m)
    return updated

# ── Main refresh ───────────────────────────────────────────────────────────
def refresh_data():
    global _cache
    print(f"[STATDIUM] Refreshing {datetime.now().strftime('%H:%M:%S')}…")
    raw            = fetch_openfootball()
    matches,groups = parse_openfootball(raw)
    fd_matches     = fetch_fd_matches()
    if fd_matches:  matches = merge_fd_into_matches(matches, fd_matches)
    fd_scorers_raw = fetch_fd_scorers()
    scorers        = parse_fd_scorers(fd_scorers_raw) if fd_scorers_raw else build_scorers_from_matches(matches)
    # Team crests (cached from last fetch; only re-fetch if empty)
    with _lock:
        existing_teams = _cache.get("teams",{})
    teams = existing_teams if existing_teams else fetch_fd_teams()
    with _lock:
        _cache.update({
            "matches":matches,"groups":groups,"scorers":scorers,"teams":teams,
            "last_updated":datetime.now(timezone.utc).isoformat(),
            "source":"openfootball"+("+fd" if fd_matches else ""),
        })
    print(f"[STATDIUM] {len(matches)} matches · {len(scorers)} scorers · {len(teams)} crests")

def get_cache():
    with _lock: return dict(_cache)

def get_matches(status=None, group=None):
    ms = get_cache()["matches"]
    if status: ms=[m for m in ms if m["status"]==status]
    if group:  ms=[m for m in ms if group.lower() in str(m.get("group","")).lower()]
    return ms

def get_today_matches():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [m for m in get_cache()["matches"] if m.get("date","")==today]

def get_recent_matches(n=20):
    """Return most recent finished matches, sorted newest first."""
    return sorted(
        [m for m in get_cache()["matches"] if m["status"] == "FINISHED"],
        key=lambda x: (x["date"], x.get("id","")),
        reverse=True
    )[:n]

def get_upcoming_matches(n=10):
    return sorted([m for m in get_cache()["matches"] if m["status"]=="SCHEDULED"],
                  key=lambda x:x["date"])[:n]

refresh_data()
