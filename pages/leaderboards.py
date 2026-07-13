"""
STATDIUM — Leaderboards
Golden Boot: scrollable ranked rows with progress bars.
Cards removed (no free data source). Chart removed (redundant).
Assists/games shown when available from openfootball.
"""
from dash import html, dcc, Input, Output
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import get_cache, get_flag, get_flag_img

GUIDE = page_guide("Leaderboards", [
    ("🥇", "Golden Boot Race — ranked by goals scored. Medal colours: 🥇 gold · 🥈 silver · 🥉 bronze."),
    ("📊", "Progress bars show each player's goals relative to the tournament leader."),
    ("📸", "Player photos come from football-data.org (when available via FD_API_KEY)."),
    ("🔄", "Data refreshes every 60s — scorer list updates as goals are confirmed."),
], accent_color=COLORS["gold"])

def layout():
    return html.Div([
        dcc.Interval(id="leaderboards-interval", interval=60000, n_intervals=0),
        page_wrapper([
            GUIDE,
            section_header("Leaderboards",
                           "Golden Boot race · Top scorers from live match data",
                           accent_color=COLORS["gold"]),
            html.Div(id="leaderboards-content"),
        ]),
    ])


@app.callback(
    Output("leaderboards-content", "children"),
    Input("leaderboards-interval", "n_intervals"),
)
def update_leaderboard(_):
    cache = get_cache()
    scorers = cache.get("scorers", [])
    matches = cache.get("matches", [])
    played_count = len([m for m in matches if m["status"] == "FINISHED"])

    if not scorers:
        return dmc.LoadingOverlay(
            html.Div([
                html.Div("⚽", style={"fontSize":"48px","textAlign":"center","marginBottom":"12px","marginTop":"40px"}),
                html.Div("No scorer data yet — matches in progress",
                         style={"fontSize":"14px","color":COLORS["text_secondary"],"textAlign":"center"}),
            ])
        )

    return _build_golden_boot(scorers, played_count)

import requests
from dash import html

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php"


def get_player_photo(player_name, return_type="img", size=42):
    """
    Parameters
    ----------
    player_name : str
        e.g. "Lionel Messi", "Cristiano Ronaldo"

    return_type : str
        "url" -> returns image URL
        "img" -> returns html.Img
        "both" -> returns (url, html.Img)

    size : int
        Image size in pixels
    """

    try:
        params = {"p": player_name.replace(" ", "_")}
        r = requests.get(BASE_URL, params=params, timeout=5)
        r.raise_for_status()

        players = r.json().get("player")

        if not players:
            return None

        player = players[0]

        # Prefer transparent cutout
        photo = (
            player.get("strCutout")
            or player.get("strRender")
            or player.get("strThumb")
        )

        if not photo:
            return None

        if return_type == "url":
            return photo

        img = html.Img(
            src=photo,
            className="player-photo",
            style={
                "width": f"{size}px",
                "height": f"{size}px",
                "borderRadius": "50%",
                "objectFit": "cover"
            }
        )

        if return_type == "both":
            return photo, img

        return img

    except Exception:
        return None

        
def _build_golden_boot(scorers, played_count):
    rows = scorers[:20]
    max_goals = max((r.get("goals", 0) for r in rows), default=1)
    total_goals = sum(r.get("goals", 0) for r in rows)

    # Summary badges
    summary = html.Div([
        _stat_badge("🏅", "Top Scorer",       rows[0]["name"] if rows else "—"),
        _stat_badge("⚽", "Goals (Top 20)",   str(total_goals)),
        _stat_badge("🎮", "Matches Played",   str(played_count)),
        _stat_badge("📊", "Players Scoring",  str(len(rows))),
    ], style={"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"24px"})

    # Check if assists data exists at all
    has_assists = any(r.get("assists", 0) > 0 for r in rows)
    has_games   = any(r.get("games",   0) > 0 for r in rows)

    scorer_rows = []
    for i, r in enumerate(rows):
        goals   = r.get("goals",   0)
        assists = r.get("assists", 0)
        games   = r.get("games",   0)
        team    = r.get("team",    "")
        name    = r.get("name",    "")
        pct     = goals / max_goals * 100 if max_goals > 0 else 0

        if i == 0:
            row_cls  = "lb-scorer-row lb-gold"
            rank_el  = html.Div("🥇", className="lb-rank-badge",
                                 style={"background":"#FFD70020","color":"#FFD700","border":"1px solid #FFD70040","fontSize":"16px"})
            bar_color = COLORS["gold"]
        elif i == 1:
            row_cls  = "lb-scorer-row lb-silver"
            rank_el  = html.Div("🥈", className="lb-rank-badge",
                                 style={"background":"#C0C0C020","color":"#C0C0C0","border":"1px solid #C0C0C040","fontSize":"16px"})
            bar_color = "#C0C0C0"
        elif i == 2:
            row_cls  = "lb-scorer-row lb-bronze"
            rank_el  = html.Div("🥉", className="lb-rank-badge",
                                 style={"background":"#CD7F3220","color":"#CD7F32","border":"1px solid #CD7F3240","fontSize":"16px"})
            bar_color = "#CD7F32"
        else:
            row_cls   = "lb-scorer-row"
            rank_el   = html.Div(str(i + 1), className="lb-rank-badge")
            bar_color = COLORS["accent"]

        # Stats badges — only show what we actually have
        stat_chips = [
            html.Span(f"{goals} goal{'s' if goals != 1 else ''}",
                      className="lb-goals-badge"),
        ]
        if has_assists:
            stat_chips.append(
                html.Span(f"{assists} ast",
                          className="lb-assists-badge" if assists > 0 else "lb-games-badge")
            )
        if has_games:
            stat_chips.append(
                html.Span(f"{games} game{'s' if games != 1 else ''}",
                          className="lb-games-badge")
            )

        # Player photo (from FD API or HuggingFace fallback)
        # photo_url = r.get("photo","")
        photo_url = get_player_photo(name, "url")
        if photo_url:
            photo_el = html.Img(src=photo_url, className="player-photo",
                                style={"width":"42px","height":"42px"})
        else:
            photo_el = html.Div(get_flag(team), className="player-photo-fallback")

        scorer_rows.append(html.Div([
            rank_el,
            photo_el,
            html.Div(get_flag_img(team, width=22),
                     style={"flexShrink":"0","display":"flex","alignItems":"center"}),
            html.Div([
                html.Div(name, className="lb-player-name"),
                html.Div([get_flag(team),
                          html.Span(f" {team}", style={"color":COLORS["text_secondary"]})],
                         className="lb-player-team"),
            ], className="lb-player-info"),

            # Progress bar + stat chips
            html.Div([
                html.Div(stat_chips, className="lb-bar-stats"),
                html.Div(
                    html.Div(style={
                        "width": f"{pct}%", "height": "100%",
                        "borderRadius": "4px",
                        "background": f"linear-gradient(90deg, {bar_color}, {bar_color}aa)",
                        "transition": "width 1.2s cubic-bezier(0.22,1,0.36,1)",
                    }),
                    className="lb-progress-track"
                ),
            ], className="lb-bar-section"),
        ], className=row_cls))

    # Scrollable container — no duplicate bar chart
    return html.Div([
        summary,
        section_header("🏅 Golden Boot Race",
                       f"Top {len(rows)} scorers · {played_count} matches played",
                       accent_color=COLORS["gold"]),
        html.Div(
            scorer_rows,
            style={
                "maxHeight": "70vh",
                "overflowY": "auto",
                "paddingRight": "4px",
                # custom scrollbar handled by global CSS
            }
        ),
        html.Div(
            "Data: openfootball · Assists/games shown when available from match data",
            style={"fontSize":"11px","color":COLORS["text_secondary"],
                   "textAlign":"center","marginTop":"16px"}
        ),
    ])


def _stat_badge(icon, label, value):
    return html.Div([
        html.Div(icon,  style={"fontSize":"20px","marginBottom":"4px"}),
        html.Div(value, style={"fontSize":"16px","fontWeight":"800","color":COLORS["text_primary"]}),
        html.Div(label, style={"fontSize":"10px","color":COLORS["text_secondary"],
                               "textTransform":"uppercase","letterSpacing":"0.06em"}),
    ], style={"background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"10px","padding":"12px 16px","textAlign":"center",
              "minWidth":"100px","flex":"1"})
