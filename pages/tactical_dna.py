"""
STATDIUM — Tactical DNA Fingerprint (Feature #4) + Fan Pulse (Feature #3)
Unique SVG data-art fingerprint per team + emotion world map.
"""
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import math, json
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import get_cache, WC2026_GROUPS, FIFA_RANKINGS, get_flag, get_flag_img
from data.elo import get_elo_with_fallback

# Team color palette — unique color per team
TEAM_PALETTE = {
    "Brazil":"#009C3B","Argentina":"#74ACDF","France":"#002395","Germany":"#000000",
    "England":"#CF081F","Spain":"#c60b1e","Netherlands":"#FF6600","Portugal":"#006600",
    "Belgium":"#EF3340","USA":"#002868","Mexico":"#006847","Canada":"#FF0000",
    "Japan":"#BC002D","Morocco":"#006233","Croatia":"#FF0000","Uruguay":"#75AADB",
    "Colombia":"#FCD116","South Korea":"#003478","Switzerland":"#FF0000",
    "Norway":"#EF2B2D","Australia":"#00843D","Ecuador":"#FFD100","Senegal":"#00853F",
    "Iran":"#239F40","Ghana":"#006B3F","Tunisia":"#E70013","Sweden":"#006AA7",
    "Austria":"#ED2939","Turkey":"#E30A17","Egypt":"#CE1126","Iraq":"#007A3D",
    "Denmark":"#C60C30","Scotland":"#003DA5","Wales":"#C8102E","Serbia":"#C6363C",
    "Poland":"#DC143C","Ukraine":"#005BBB","Saudi Arabia":"#006C35","Qatar":"#8D1B3D",
    "Paraguay":"#D52B1E","Bolivia":"#D52B1E","Algeria":"#006233","Jordan":"#007A3D",
    "Haiti":"#00209F","Ivory Coast":"#F77F00","DR Congo":"#007FFF","Uzbekistan":"#1EB53A",
    "New Zealand":"#00247D","Cape Verde":"#003893","Curaçao":"#002B7F","Bosnia & Herzegovina":"#002395",
    "South Africa":"#007A4D","Czech Republic":"#D7141A","Panama":"#DA121A",
}

def _team_color(team):
    c = TEAM_PALETTE.get(team, COLORS["accent"])
    if c == "#000000": c = "#444444"
    return c

def _dna_svg(team, stats, elo):
    """Generate a unique geometric SVG fingerprint from team stats."""
    W, H = 200, 200
    cx, cy = 100, 100

    # Map stats to visual parameters
    p = max(stats.get("p", 1), 1)
    win_rate = stats.get("w", 0) / p
    attack = min(1.0, stats.get("gf", 0) / 8)
    defense = 1.0 - min(1.0, stats.get("ga", 0) / 8)
    pts_norm = min(1.0, stats.get("pts", 0) / 9)
    elo_norm = min(1.0, max(0, (elo - 1400) / 600))

    color = _team_color(team)
    r_hex = int(color.lstrip('#')[0:2], 16) if color.startswith('#') and len(color)==7 else 0
    g_hex = int(color.lstrip('#')[2:4], 16) if color.startswith('#') and len(color)==7 else 229
    b_hex = int(color.lstrip('#')[4:6], 16) if color.startswith('#') and len(color)==7 else 160

    # Outer ring — elo strength
    r_outer = 30 + elo_norm * 55
    # Inner polygon — win_rate
    r_inner = 15 + win_rate * 35
    # Attack spikes count
    n_spikes = max(3, min(12, int(attack * 10) + 3))
    # Defense arc width
    arc_w = 4 + defense * 6

    paths = []
    # Outer glow circle
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="rgba({r_hex},{g_hex},{b_hex},0.08)" stroke="rgba({r_hex},{g_hex},{b_hex},0.25)" stroke-width="1.5"/>')

    # Star/polygon from win_rate
    star_pts = []
    for i in range(n_spikes * 2):
        angle = math.pi * i / n_spikes - math.pi / 2
        r = r_inner if i % 2 == 0 else r_inner * 0.45
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        star_pts.append(f"{x:.1f},{y:.1f}")
    paths.append(f'<polygon points="{" ".join(star_pts)}" fill="rgba({r_hex},{g_hex},{b_hex},0.35)" stroke="rgba({r_hex},{g_hex},{b_hex},0.8)" stroke-width="1.5"/>')

    # Attack energy lines
    for i in range(n_spikes):
        angle = math.pi * 2 * i / n_spikes - math.pi / 2
        x1 = cx + r_inner * 0.3 * math.cos(angle)
        y1 = cy + r_inner * 0.3 * math.sin(angle)
        x2 = cx + (r_outer * 0.85) * math.cos(angle)
        y2 = cy + (r_outer * 0.85) * math.sin(angle)
        paths.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba({r_hex},{g_hex},{b_hex},0.4)" stroke-width="{arc_w * 0.4:.1f}" stroke-linecap="round"/>')

    # Center dot — current points
    r_center = 4 + pts_norm * 12
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r_center}" fill="rgba({r_hex},{g_hex},{b_hex},0.9)"/>')
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r_center * 0.4:.1f}" fill="white" opacity="0.6"/>')

    svg = f"""<svg
        viewBox="0 0 {W} {H}"
        xmlns="http://www.w3.org/2000/svg"
        width="100%"
        height="100%"
        style="overflow:hidden;"
    >
    <defs>
        <filter id="glow-{team.replace(" ","_")}">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
        </filter>
    </defs>
    <g filter="url(#glow-{team.replace(" ","_")})">
        {"".join(paths)}
    </g>
    </svg>"""
    return svg


GUIDE = page_guide("Tactical DNA", [
    ("🧬", "Each geometric fingerprint is generated from live stats: Elo strength, win rate, goals, defense."),
    ("🔵", "Bigger outer ring = higher Elo. More star points = higher attack rate. Brighter centre = more points."),
    ("🌍", "Fan Pulse Map: countries coloured by a composite 'pulse' score — brighter = team is thriving."),
    ("➕", "Add or remove teams from the selector to compare up to 8 fingerprints side by side."),
], accent_color=COLORS["accent2"])

def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    opts = [{"label": f"{get_flag(t)} {t}", "value": t} for t in all_teams]

    return html.Div([
        page_wrapper([
            GUIDE,
            section_header("🧬 Tactical DNA",
                           "Unique geometric fingerprint per team — generated from live stats + Elo",
                           accent_color=COLORS["accent2"]),

            # Team selector
            html.Div([
                html.Div("Select Teams to Compare (up to 8):", style={
                    "fontSize":"11px","fontWeight":"700","color":COLORS["text_secondary"],
                    "textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"8px"}),
                dcc.Dropdown(id="dna-teams", options=opts, multi=True,
                             value=["Brazil","Argentina","France","Germany","England","Spain"],
                             placeholder="Add teams…"),
            ], style={"background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                      "borderRadius":"12px","padding":"16px 20px","marginBottom":"20px"}),

            html.Div(id="dna-grid"),

            html.Div(style={"marginTop":"32px"}),

            # Fan Pulse section
            section_header("💚 Fan Pulse Map",
                           "World sentiment — team performance painted on the globe",
                           accent_color=COLORS["live_red"]),
            html.Div(id="fan-pulse-map"),
        ]),
    ])


def _team_full_stats(team, matches):
    """
    Aggregate a team's complete record — group stage AND every knockout
    round played so far — directly from finished matches. group_table alone
    only ever holds group-stage numbers, so any team still alive in the
    knockout rounds would otherwise show a fingerprint/stat card frozen at
    whatever it looked like after 3 group games, silently ignoring every
    knockout result since. One known, honest limitation: our match data
    doesn't carry penalty-shootout detail, so a knockout tie that was
    decided on penalties still counts as a "draw" here rather than a win/loss.
    """
    stats = {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
        h, a = m.get("home_team"), m.get("away_team")
        if team not in (h, a):
            continue
        hs, as_ = m.get("home_score"), m.get("away_score")
        if hs is None or as_ is None:
            continue
        is_home = team == h
        gf, ga = (hs, as_) if is_home else (as_, hs)
        stats["p"] += 1
        stats["gf"] += gf
        stats["ga"] += ga
        if gf > ga:
            stats["w"] += 1
            stats["pts"] += 3
        elif gf == ga:
            stats["d"] += 1
            stats["pts"] += 1
        else:
            stats["l"] += 1
    return stats


@app.callback(Output("dna-grid","children"), Input("dna-teams","value"))
def update_dna(selected_teams):
    if not selected_teams: return html.Div("Select teams above", style={"color":COLORS["text_secondary"],"padding":"20px"})
    selected_teams = selected_teams[:8]

    cache = get_cache()
    matches = cache.get("matches", [])

    cards = []
    for team in selected_teams:
        stats = _team_full_stats(team, matches)

        elo = get_elo_with_fallback(team)
        rank = FIFA_RANKINGS.get(team, 60)
        svg = _dna_svg(team, stats, elo)
        color = _team_color(team)

        cards.append(
            html.Div(
                [
                    # DNA SVG
                    html.Div(
                        html.Iframe(
                            srcDoc=svg,
                            style={
                                "width": "100%",
                                "height": "100%",
                                "border": "none",
                                "overflow": "hidden",
                            },
                        ),
                        style={"width": "140px", "height": "150px", "margin": "0 auto"},
                    ),
                    # Team info
                    html.Span(
                        get_flag_img(team, width=20),
                        style={
                            "justifyContent": "center",
                            "display": "flex",
                            "marginTop": "4px",
                        },
                    ),
                    html.Div(
                        team,
                        style={
                            "fontSize": "14px",
                            "fontWeight": "800",
                            "textAlign": "center",
                            "color": COLORS["text_primary"],
                            "marginTop": "8px",
                        },
                    ),
                    html.Div(
                        f"Elo {elo} · #{rank}",
                        style={
                            "fontSize": "11px",
                            "color": COLORS["text_secondary"],
                            "textAlign": "center",
                            "marginTop": "2px",
                        },
                    ),
                    # Mini stats
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        str(stats["pts"]),
                                        style={
                                            "fontSize": "18px",
                                            "fontWeight": "800",
                                            "color": color,
                                        },
                                    ),
                                    html.Div(
                                        "PTS",
                                        style={
                                            "fontSize": "9px",
                                            "color": COLORS["text_secondary"],
                                        },
                                    ),
                                ],
                                style={"textAlign": "center", "flex": "1"},
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        f"{stats['w']}-{stats['d']}-{stats['l']}",
                                        style={
                                            "fontSize": "12px",
                                            "fontWeight": "700",
                                            "color": COLORS["text_primary"],
                                        },
                                    ),
                                    html.Div(
                                        "W-D-L",
                                        style={
                                            "fontSize": "9px",
                                            "color": COLORS["text_secondary"],
                                        },
                                    ),
                                ],
                                style={"textAlign": "center", "flex": "1"},
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        f"{stats['gf']}-{stats['ga']}",
                                        style={
                                            "fontSize": "12px",
                                            "fontWeight": "700",
                                            "color": COLORS["text_primary"],
                                        },
                                    ),
                                    html.Div(
                                        "GF-GA",
                                        style={
                                            "fontSize": "9px",
                                            "color": COLORS["text_secondary"],
                                        },
                                    ),
                                ],
                                style={"textAlign": "center", "flex": "1"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "4px",
                            "marginTop": "10px",
                            "paddingTop": "10px",
                            "borderTop": f"1px solid {COLORS['border']}",
                        },
                    ),
                ],
                style={
                    "background": COLORS["bg_card"],
                    "border": f"2px solid {color}44",
                    "borderTop": f"3px solid {color}",
                    "borderRadius": "14px",
                    "padding": "16px",
                    "transition": "all 0.2s ease",
                },
                className="glow-card tilt-card",
            )
        )

    return html.Div(cards, style={"display":"grid","gridTemplateColumns":"repeat(auto-fill,minmax(200px,1fr))","gap":"16px"})


@app.callback(Output("fan-pulse-map","children"), Input("dna-teams","value"))
def update_fan_pulse(_):
    """World choropleth colored by team performance score — the 'emotion' layer."""
    cache = get_cache()
    matches = cache.get("matches",[])
    finished = [m for m in matches if m["status"]=="FINISHED"]

    ISO3_MAP = {
        "Argentina":"ARG","Australia":"AUS","Austria":"AUT","Belgium":"BEL",
        "Bosnia & Herzegovina":"BIH","Brazil":"BRA","Canada":"CAN","Cape Verde":"CPV",
        "Colombia":"COL","Croatia":"HRV","Curaçao":"CUW","Czech Republic":"CZE",
        "DR Congo":"COD","Ecuador":"ECU","Egypt":"EGY","England":"GBR",
        "France":"FRA","Germany":"DEU","Ghana":"GHA","Haiti":"HTI","Iran":"IRN",
        "Iraq":"IRQ","Ivory Coast":"CIV","Japan":"JPN","Jordan":"JOR",
        "Mexico":"MEX","Morocco":"MAR","Netherlands":"NLD","New Zealand":"NZL",
        "Norway":"NOR","Panama":"PAN","Paraguay":"PRY","Portugal":"PRT","Qatar":"QAT",
        "Saudi Arabia":"SAU","Scotland":"GBR","Senegal":"SEN","South Africa":"ZAF",
        "South Korea":"KOR","Spain":"ESP","Sweden":"SWE","Switzerland":"CHE",
        "Tunisia":"TUN","Turkey":"TUR","USA":"USA","Ukraine":"UKR","Uruguay":"URY",
        "Uzbekistan":"UZB","Algeria":"DZA",
    }

    rows = []
    for grp, teams in WC2026_GROUPS.items():
        for team in teams:
            iso3 = ISO3_MAP.get(team,"")
            if not iso3: continue
            stats = _team_full_stats(team, matches)
            pts = stats.get("pts",0)
            gf  = stats.get("gf",0)
            ga  = stats.get("ga",0)
            gd  = gf - ga
            # Pulse score: weighted — minimum 1 so non-playing teams aren't invisible
            pulse = max(1, pts * 10 + max(0,gd) * 5 + gf * 2)
            # Last result mood
            team_matches = [m for m in finished if m.get("home_team")==team or m.get("away_team")==team]
            if team_matches:
                last = team_matches[-1]
                hs, as_ = last.get("home_score",0) or 0, last.get("away_score",0) or 0
                if last.get("home_team")==team: mood = "W" if hs>as_ else ("D" if hs==as_ else "L")
                else: mood = "W" if as_>hs else ("D" if as_==hs else "L")
            else:
                mood = "—"
            rows.append({"team":team,"iso3":iso3,"pulse":pulse,"pts":pts,"gd":gd,"mood":mood,"flag":get_flag(team)})

    if not rows:
        return html.Div("No match data yet", style={"color":COLORS["text_secondary"],"padding":"20px"})

    fig = go.Figure(go.Choropleth(
        locations=[r["iso3"] for r in rows],
        z=[r["pulse"] for r in rows],
        text=[f"<b>{r['flag']} {r['team']}</b><br>Pulse: {r['pulse']}<br>Points: {r['pts']}<br>GD: {'+' if r['gd']>=0 else ''}{r['gd']}<br>Last: {r['mood']}" for r in rows],
        hovertemplate="%{text}<extra></extra>",
        colorscale=[
            [0.0,"#1a0a2e"],[0.2,"#2d1b69"],[0.4,"#7B61FF"],
            [0.6,"#00B4D8"],[0.8,"#00E5A0"],[1.0,"#FFD700"]
        ],
        zmin=1, zmax=max(r["pulse"] for r in rows) if rows else 100,
        showscale=True,
        colorbar=dict(title=dict(text="Fan Pulse",font=dict(color=COLORS["text_secondary"])),
                      tickfont=dict(color=COLORS["text_secondary"]),bgcolor="rgba(0,0,0,0)",len=0.6),
        marker_line_color=COLORS["border"], marker_line_width=0.5,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)",showframe=False,showcoastlines=True,
                 coastlinecolor=COLORS["border"],showland=True,landcolor="#1a1a22",
                 showocean=True,oceancolor=COLORS["bg_primary"],
                 showcountries=True,countrycolor=COLORS["border"],
                 projection_type="natural earth"),
        margin=dict(l=0,r=0,t=0,b=0), height=420,
        font=dict(color=COLORS["text_secondary"]),
    )
    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar":False,"scrollZoom":True}),
        html.Div("Pulse score = Points×10 + Goal Difference×5 + Goals×2 · Darker = struggling, brighter = thriving",
                 style={"fontSize":"11px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"8px"}),
    ], style={"background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"14px","padding":"20px"})
