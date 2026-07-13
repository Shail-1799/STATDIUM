from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import (
    page_guide,
    COLORS,
    section_header,
    match_scorecard,
    stat_pill,
    page_wrapper,
    goal_ticker,
    get_flag_img,
)
from data.fetcher import (
    get_today_matches,
    get_recent_matches,
    get_upcoming_matches,
    get_cache,
    get_matches,
    WC2026_GROUPS,
    FIFA_RANKINGS,
    get_flag,
    ensure_fresh,
)
from datetime import datetime, timezone
from collections import defaultdict


def _hero():
    """Cinematic landing hero — renders with live data on callback, static shell here."""
    return html.Div(
        [
            # Eyebrow
            html.Div(
                "🏆  FIFA WORLD CUP 2026  ·  USA · CANADA · MEXICO",
                className="hero-eyebrow",
            ),
            # Big title
            html.Div(
                [
                    html.Span("STAT", style={"color": "var(--text-primary)"}),
                    html.Span("DIUM", style={"color": "var(--accent)"}),
                ],
                className="hero-title",
            ),
            html.Div(
                "Live analytics · Elo intelligence · Match simulations · Historical data",
                className="hero-sub",
            ),
            # Live stat strip (populated by callback)
            html.Div(id="hero-stat-strip"),
        ],
        className="hero-wrap",
    )


GUIDE = page_guide(
    "Live Dashboard",
    [
        (
            "⚡",
            "Auto-refreshes every 20 seconds — all data is live from openfootball + football-data.org.",
        ),
        (
            "⭐",
            "Go to Teams page to follow a team — their next match pins to the top of this page.",
        ),
        (
            "📅",
            "Match cards are grouped by date. Hover a card to tilt it; click for full match details.",
        ),
        (
            "📊",
            "The stats bar (top) shows total matches, goals, live count and average goals per match.",
        ),
        (
            "📈",
            "Goals Timeline (bottom) shows goals scored per day with a rolling average line.",
        ),
    ],
    accent_color=COLORS["accent"],
)


def layout():
    return html.Div(
        [
            dcc.Interval(id="live-interval", interval=20000, n_intervals=0),
            html.Div(id="goal-ticker-bar"),
            _hero(),
            page_wrapper(
                [
                    GUIDE,
                    html.Div(id="favorite-tracker", style={"marginBottom": "16px"}),
                    html.Div(id="live-stats-bar", style={"marginBottom": "24px"}),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="today-matches"),
                                    html.Div(
                                        id="recent-matches", style={"marginTop": "24px"}
                                    ),
                                ],
                                style={"flex": "1.2", "minWidth": "300px"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="upcoming-matches"),
                                    # html.Div(
                                    #     id="matches-timeline",
                                    #     style={"marginTop": "24px"},
                                    # ),
                                ],
                                style={"flex": "1", "minWidth": "280px"},
                            ),
                        ],
                        style={"display": "flex", "gap": "24px", "flexWrap": "wrap"},
                    ),
                    html.Div(
                        id="matches-timeline",
                        style={"marginTop": "24px"},
                    ),
                    html.Div(id="full-match-timeline", style={"marginTop": "32px"}),
                ]
            ),
        ]
    )


@app.callback(
    Output("favorite-tracker", "children"),
    Input("favorite-team-store", "data"),
    Input("live-interval", "n_intervals"),
)
def update_favorite_tracker(fav_data, _):
    fav = (fav_data or {}).get("team")
    if not fav:
        return html.Div()

    all_matches = get_cache()["matches"]
    team_matches = [
        m for m in all_matches if m["home_team"] == fav or m["away_team"] == fav
    ]
    if not team_matches:
        return html.Div()

    next_match = None
    for m in team_matches:
        if m["status"] in ("LIVE", "SCHEDULED"):
            next_match = m
            break
    if not next_match:
        finished = [m for m in team_matches if m["status"] == "FINISHED"]
        next_match = (
            sorted(finished, key=lambda x: x["date"], reverse=True)[0]
            if finished
            else None
        )
    if not next_match:
        return html.Div()

    return html.Div(
        [
            html.Div(
                [
                    html.Span("⭐ ", style={"fontSize": "14px"}),
                    html.Span(
                        f"Following {get_flag(fav)} {fav}",
                        style={
                            "fontSize": "12px",
                            "fontWeight": "700",
                            "color": COLORS["gold"],
                        },
                    ),
                    html.Span(
                        (
                            " — next up:"
                            if next_match["status"] != "FINISHED"
                            else " — last result:"
                        ),
                        style={
                            "fontSize": "12px",
                            "color": COLORS["text_secondary"],
                            "marginLeft": "6px",
                        },
                    ),
                ],
                style={"marginBottom": "8px"},
            ),
            match_scorecard(next_match),
        ],
        className="glow-card",
        style={
            "backgroundColor": "rgba(255,215,0,0.05)",
            "border": f"1px solid {COLORS['gold']}33",
            "borderRadius": "12px",
            "padding": "16px",
        },
    )


@app.callback(
    Output("goal-ticker-bar", "children"), Input("live-interval", "n_intervals")
)
def update_ticker(_):
    ensure_fresh()
    matches = get_cache()["matches"]
    return goal_ticker(matches)


@app.callback(
    Output("hero-stat-strip", "children"), Input("live-interval", "n_intervals")
)
def update_hero_strip(_):
    ensure_fresh()
    cache = get_cache()
    matches = cache["matches"]
    finished = [m for m in matches if m["status"] == "FINISHED"]
    live_now = [m for m in matches if m["status"] == "LIVE"]
    goals = sum(
        (m.get("home_score") or 0) + (m.get("away_score") or 0) for m in finished
    )
    scorers = cache.get("scorers", [])
    top = scorers[0]["name"] if scorers else "—"
    top_g = scorers[0]["goals"] if scorers else 0

    def stat(val, lbl):
        return html.Div(
            [
                html.Span(
                    str(val),
                    className="hero-stat-val countup-num",
                    **{"data-target": str(val)} if str(val).isdigit() else {},
                ),
                html.Span(lbl, className="hero-stat-lbl"),
            ],
            className="hero-stat",
        )

    return html.Div(
        [
            stat(len(matches), "MATCHES"),
            stat(len(finished), "PLAYED"),
            stat(len(live_now) or 0, "LIVE NOW"),
            stat(goals, "GOALS"),
            stat(f"{round(goals/max(1,len(finished)),2)}", "AVG/MATCH"),
            html.Div(
                [
                    html.Span(
                        f"{top_g}⚽",
                        className="hero-stat-val",
                        style={"fontSize": "16px", "lineHeight": "1.2"},
                    ),
                    html.Span(
                        top[:18] + "…" if len(top) > 18 else top,
                        style={
                            "fontSize": "9px",
                            "color": "var(--text-secondary)",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.08em",
                            "display": "block",
                            "marginTop": "3px",
                        },
                    ),
                    html.Span("TOP SCORER", className="hero-stat-lbl"),
                ],
                className="hero-stat",
            ),
        ],
        className="hero-stat-strip",
    )


@app.callback(
    Output("live-stats-bar", "children"), Input("live-interval", "n_intervals")
)
def update_stats_bar(_):
    ensure_fresh()
    cache = get_cache()
    matches = cache["matches"]
    finished = [m for m in matches if m["status"] == "FINISHED"]
    live_now = [m for m in matches if m["status"] == "LIVE"]
    scheduled = [m for m in matches if m["status"] == "SCHEDULED"]
    total_goals = sum(
        (m.get("home_score") or 0) + (m.get("away_score") or 0) for m in finished
    )
    avg_goals = round(total_goals / max(1, len(finished)), 2)
    lu = cache.get("last_updated", "–")
    try:
        lu = datetime.fromisoformat(lu).strftime("%H:%M UTC")
    except:
        pass

    return html.Div(
        [
            stat_pill("Total Matches", len(matches)),
            stat_pill("Played", len(finished)),
            stat_pill(
                "Live Now",
                len(live_now),
                color=COLORS["live_red"] if live_now else None,
            ),
            stat_pill("Upcoming", len(scheduled)),
            stat_pill("Total Goals", total_goals),
            stat_pill("Avg Goals/Match", avg_goals),
            html.Div(
                [
                    html.Div(
                        "Last sync",
                        style={
                            "fontSize": "10px",
                            "color": COLORS["text_secondary"],
                            "textTransform": "uppercase",
                            "letterSpacing": "0.08em",
                        },
                    ),
                    html.Div(lu, style={"fontSize": "13px", "color": COLORS["accent"]}),
                ],
                className="stat-pill",
            ),
        ],
        className="stat-pills-row",
    )


@app.callback(
    Output("today-matches", "children"), Input("live-interval", "n_intervals")
)
def update_today(_):
    ensure_fresh()
    live_now = get_matches(status="LIVE")
    today = get_today_matches()
    seen = {m["id"] for m in live_now}
    all_today = live_now + [m for m in today if m["id"] not in seen]
    if not all_today:
        # No fixtures today — skip this section entirely rather than
        # re-rendering "Recent Results" here too (that already has its own
        # dedicated section right below, so showing it twice was the bug).
        return html.Div(
            [
                section_header("Today's Matches", "No matches scheduled today"),
                html.Div(
                    [
                        html.Div(
                            "⚽",
                            style={
                                "fontSize": "36px",
                                "textAlign": "center",
                                "marginBottom": "8px",
                                "opacity": "0.6",
                            },
                        ),
                        html.Div(
                            "No matches today — check Recent Results or Coming Up",
                            style={
                                "fontSize": "13px",
                                "color": COLORS["text_secondary"],
                                "textAlign": "center",
                            },
                        ),
                    ],
                    style={"padding": "24px 20px"},
                ),
            ]
        )
    return _grouped_matches(
        all_today,
        "Today's Matches",
        f"{len(all_today)} match{'es' if len(all_today)!=1 else ''} today",
    )


def _grouped_matches(matches, title, subtitle, reverse_dates=False):
    """Group matches by date with styled date headers."""
    by_date = defaultdict(list)
    for m in matches:
        by_date[m.get("date", "")].append(m)

    date_keys = sorted(by_date.keys(), reverse=reverse_dates)
    date_groups = []
    for date_key in date_keys:
        day_matches = by_date[date_key]
        try:
            label = (
                datetime.strptime(date_key, "%Y-%m-%d").strftime("%A, %B %d").upper()
            )
        except:
            label = date_key.upper()

        date_groups.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "•",
                                style={
                                    "color": COLORS["accent"],
                                    "fontSize": "16px",
                                    "fontWeight": "900",
                                    "marginRight": "8px",
                                },
                            ),
                            html.Span(label, className="match-date-label"),
                            html.Span(
                                f"{len(day_matches)} match{'es' if len(day_matches)!=1 else ''}",
                                className="match-date-count",
                            ),
                        ],
                        className="match-date-header",
                    ),
                    html.Div(
                        [match_scorecard(m) for m in day_matches],
                        className="match-date-grid",
                    ),
                ],
                className="match-date-group",
            )
        )

    return html.Div([section_header(title, subtitle)] + date_groups)


def _grouped_matches_desc(matches, title, subtitle):
    """Same as _grouped_matches but newest date first (for Recent Results)."""
    return _grouped_matches(matches, title, subtitle, reverse_dates=True)


@app.callback(
    Output("recent-matches", "children"), Input("live-interval", "n_intervals")
)
def update_recent(_):
    ensure_fresh()
    from datetime import datetime, timezone, timedelta

    all_recent = get_recent_matches(50)
    if not all_recent:
        return html.Div()
    # Keep only matches from the last 3 days — no fallback to older matches,
    # since silently showing e.g. a 10-day-old result under a "Last 3 days"
    # label is exactly the kind of mislabeling that caused confusion before.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
    recent = [m for m in all_recent if m.get("date", "") >= cutoff]
    if not recent:
        return html.Div(
            [
                section_header("Recent Results", "Last 3 days of results"),
                html.Div(
                    "No completed matches in the last 3 days",
                    style={"color": COLORS["text_secondary"], "padding": "20px"},
                ),
            ]
        )
    return _grouped_matches_desc(recent, "Recent Results", "Last 3 days of results")


@app.callback(
    Output("upcoming-matches", "children"), Input("live-interval", "n_intervals")
)
def update_upcoming(_):
    ensure_fresh()
    upcoming = get_upcoming_matches(8)
    if not upcoming:
        return html.Div(
            [
                section_header(
                    "Coming Up", "Next fixtures", accent_color=COLORS["accent2"]
                ),
                html.Div(
                    "All matches completed",
                    style={"color": COLORS["text_secondary"], "padding": "20px"},
                ),
            ]
        )

    cards = []
    for i, m in enumerate(upcoming):
        cards.append(match_scorecard(m))
        if i == 0:
            cards.append(_build_ai_preview(m))
    return html.Div(
        [section_header("Coming Up", "Next fixtures", accent_color=COLORS["accent2"])]
        + cards
    )


def _build_ai_preview(match):
    from data.ai_insights import generate_match_preview, ai_enabled
    from data.fetcher import FIFA_RANKINGS, get_cache

    home, away = match["home_team"], match["away_team"]
    h_rank = FIFA_RANKINGS.get(home, 60)
    a_rank = FIFA_RANKINGS.get(away, 60)
    gap = abs(h_rank - a_rank)
    shock = min(92, max(8, 8 + gap * 1.8))
    if gap <= 5:
        shock = max(20, 35 + (5 - gap) * 3)

    group_table = get_cache().get("groups", {})

    def form(team):
        for g in group_table.values():
            if team in g:
                return g[team]
        return {"pts": 0, "gf": 0, "ga": 0}

    text = generate_match_preview(
        home, away, h_rank, a_rank, form(home), form(away), shock, match_id=match["id"]
    )
    badge = "🤖 AI Preview" if ai_enabled() else "📋 Preview"

    return html.Div(
        [
            html.Div(
                badge,
                style={
                    "fontSize": "10px",
                    "fontWeight": "700",
                    "color": COLORS["accent2"],
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                    "marginBottom": "6px",
                },
            ),
            html.Div(
                text,
                style={
                    "fontSize": "13px",
                    "color": COLORS["text_secondary"],
                    "lineHeight": "1.6",
                },
            ),
        ],
        className="glow-card",
        style={
            "backgroundColor": COLORS["bg_card2"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "10px",
            "padding": "14px 16px",
            "marginBottom": "16px",
            "marginTop": "-4px",
        },
    )


@app.callback(
    Output("matches-timeline", "children"), Input("live-interval", "n_intervals")
)
def update_timeline(_):
    ensure_fresh()
    daily_goals = defaultdict(int)
    daily_matches = defaultdict(int)
    for m in get_cache()["matches"]:
        if m["status"] == "FINISHED":
            daily_goals[m.get("date", "")[:10]] += (m.get("home_score") or 0) + (
                m.get("away_score") or 0
            )
            daily_matches[m.get("date", "")[:10]] += 1
    dates = sorted(daily_goals.keys())
    if not dates:
        return html.Div()
    goals_list = [daily_goals[d] for d in dates]
    avg_list = [round(daily_goals[d] / max(1, daily_matches[d]), 1) for d in dates]
    fig = go.Figure()
    fig.add_bar(
        x=dates,
        y=goals_list,
        name="Total Goals",
        marker_color=COLORS["accent"],
        marker_line_width=0,
        opacity=0.85,
    )
    fig.add_scatter(
        x=dates,
        y=avg_list,
        name="Avg/match",
        mode="lines+markers",
        line=dict(color=COLORS["accent3"], width=2),
        marker=dict(size=6, color=COLORS["accent3"]),
        yaxis="y2",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"], size=11),
        margin=dict(l=0, r=0, t=8, b=0),
        height=300,
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.15,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=9, color=COLORS["text_secondary"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            zeroline=False,
            tickfont=dict(size=9),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=9, color=COLORS["accent3"]),
        ),
        bargap=0.3,
    )
    return html.Div(
        [
            section_header(
                "Goals Timeline", "Per match day", accent_color=COLORS["accent3"]
            ),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ]
    )


@app.callback(
    Output("full-match-timeline", "children"), Input("live-interval", "n_intervals")
)
def update_full_timeline(_):
    """Horizontal scrollable match timeline grouped by date"""
    ensure_fresh()
    matches = get_cache()["matches"]
    by_date = defaultdict(list)
    for m in matches:
        by_date[m.get("date", "unknown")].append(m)
    dates = sorted(by_date.keys(), reverse=True)  # show ALL dates, no artificial cap
    if not dates:
        return html.Div()
    dates = [
        d for d in dates if d < datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ]  # only past dates for completed matches
    date_cols = []
    for d in dates:
        day_matches = by_date[d]
        try:
            label = datetime.strptime(d, "%Y-%m-%d").strftime("%b %d")
        except:
            label = d
        finished_count = sum(1 for m in day_matches if m["status"] == "FINISHED")
        date_cols.append(
            html.Div(
                [
                    html.Div(
                        label,
                        style={
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "color": COLORS["accent"],
                            "textAlign": "center",
                            "marginBottom": "8px",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.06em",
                        },
                    ),
                    html.Div(
                        f"{finished_count}/{len(day_matches)}",
                        style={
                            "fontSize": "10px",
                            "color": COLORS["text_secondary"],
                            "textAlign": "center",
                            "marginBottom": "10px",
                        },
                    ),
                ]
                + [
                    html.Div(
                        [
                            html.Span(
                                get_flag_img(m["home_team"], width=16),
                                style={"fontSize": "14px"},
                            ),
                            html.Span(m["home_flag"], style={"fontSize": "14px"}),
                            html.Span(
                                (
                                    f" {m.get('home_score','')}–{m.get('away_score','')}"
                                    if m["status"] == "FINISHED"
                                    else " vs"
                                ),
                                style={
                                    "fontSize": "11px",
                                    "fontWeight": "600",
                                    "color": COLORS["text_primary"],
                                    "margin": "0 4px",
                                },
                            ),
                            html.Span(m["away_flag"], style={"fontSize": "14px"}),
                            html.Span(
                                get_flag_img(m["away_team"], width=16),
                                style={"fontSize": "14px"},
                            ),
                        ],
                        className="timeline-match",
                    )
                    for m in day_matches
                ],
                style={"minWidth": "150px"},
            )
        )

    return html.Div(
        [
            section_header(
                "Match Timeline",
                "Completed fixtures — scroll →",
                accent_color=COLORS["accent2"],
            ),
            html.Div(
                date_cols,
                className="timeline-scroll",
                style={
                    "display": "flex",
                    "gap": "12px",
                    "overflowX": "auto",
                    "paddingBottom": "12px",
                },
            ),
        ],
        style={
            "backgroundColor": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "padding": "20px",
        },
    )
