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
    get_flag_img,
)
from data.fetcher import (
    get_recent_matches,
    get_cache,
    WC2026_GROUPS,
    FIFA_RANKINGS,
    get_flag,
    normalize_round,
    ensure_fresh,
)
from datetime import datetime, timezone
from collections import defaultdict

# 2026 FIFA World Cup Champions — static source of truth. This is guaranteed
# correct regardless of any data-feed lag (the same lag issue that caused
# problems earlier in the tournament). Live match data below only ADDS
# supplementary detail (final score, runner-up) when available — it never
# gates or overrides this fact.
CHAMPION_TEAM = "Spain"

# Optionally pin specific match "id" values here (see each match's "id"
# field, formatted "date_hometeam_awayteam") to always feature them at the
# top of Top Moments regardless of the computed buzz score — for moments
# pure stats can't capture, like an iconic goal or a VAR controversy.
FEATURED_MATCH_IDS = []


# Scattered positions/delays for the twinkling sparkles on the champion
# card — hand-placed rather than randomized so they read as deliberate
# design, not noise.
_SPARKLE_SPOTS = [
    {"top": "10%", "left": "8%", "delay": "0s", "size": "16px"},
    {"top": "18%", "left": "88%", "delay": "0.35s", "size": "20px"},
    {"top": "62%", "left": "5%", "delay": "0.7s", "size": "14px"},
    {"top": "72%", "left": "92%", "delay": "1.0s", "size": "18px"},
    {"top": "8%", "left": "48%", "delay": "0.5s", "size": "13px"},
    {"top": "86%", "left": "44%", "delay": "0.85s", "size": "15px"},
    {"top": "42%", "left": "95%", "delay": "1.2s", "size": "12px"},
    {"top": "40%", "left": "3%", "delay": "0.2s", "size": "12px"},
]


def _sparkles():
    return [
        html.Span(
            "✨",
            className="champion-sparkle",
            style={
                "top": s["top"],
                "left": s["left"],
                "fontSize": s["size"],
                "animationDelay": s["delay"],
            },
        )
        for s in _SPARKLE_SPOTS
    ]


def _champion_banner():
    """
    Static champion fact (always correct) + a live-derived detail line
    (Final score, runner-up) when the real match data is available. If the
    data feed is stale or the Final match isn't found for any reason, the
    banner still renders correctly — it just skips the extra detail line.
    """
    detail = None
    try:
        matches = get_cache().get("matches", [])
        final_matches = [
            m for m in matches if normalize_round(m.get("round", "")) == "Final"
        ]
        if final_matches:
            fm = final_matches[0]
            if fm.get("status") == "FINISHED" and fm.get("home_score") is not None:
                hs, as_ = fm["home_score"], fm["away_score"]
                home, away = fm.get("home_team"), fm.get("away_team")
                winner = home if hs > as_ else away
                if winner == CHAMPION_TEAM:
                    runner_up = away if winner == home else home
                    score = f"{hs}–{as_}" if home == CHAMPION_TEAM else f"{as_}–{hs}"
                    detail = (
                        f"Beat {get_flag(runner_up)} {runner_up} {score} in the Final"
                    )
    except Exception:
        pass  # static banner below still renders regardless

    content = [
        html.Div("🏆", style={"fontSize": "56px", "textAlign": "center"}),
        html.Span(get_flag_img(CHAMPION_TEAM, width=48), style={"display": "block", "textAlign": "center"}),
        html.Div(
            f"{CHAMPION_TEAM}",
            style={
                "fontSize": "28px",
                "fontWeight": "900",
                "color": COLORS["gold"],
                "textAlign": "center",
                "marginTop": "8px",
            },
        ),
        html.Div(
            "2026 FIFA WORLD CUP CHAMPIONS",
            style={
                "fontSize": "12px",
                "fontWeight": "700",
                "color": COLORS["text_secondary"],
                "textAlign": "center",
                "letterSpacing": "0.1em",
                "marginTop": "4px",
            },
        ),
    ]
    if detail:
        content.append(
            html.Div(
                detail,
                style={
                    "fontSize": "13px",
                    "color": COLORS["text_secondary"],
                    "textAlign": "center",
                    "marginTop": "10px",
                },
            )
        )

    return html.Div(
        _sparkles()
        + [html.Div(content, style={"position": "relative", "zIndex": "3"})],
        className="champion-banner glow-card",
        style={
            "background": "rgba(255,215,0,0.08)",
            "border": f"2px solid {COLORS['gold']}66",
            "borderRadius": "16px",
            "padding": "28px 20px",
            "marginBottom": "20px",
        },
    )


def _hero():
    """Cinematic landing hero — renders with live data on callback, static shell here."""
    return html.Div(
        [
            # Eyebrow
            html.Div(
                "🏆  FIFA WORLD CUP 2026 · FINAL RESULTS  ·  USA · CANADA · MEXICO",
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
                "Final results · Top moments · Complete tournament history",
                className="hero-sub",
            ),
            # Live stat strip — moved above the champion card
            html.Div(id="hero-stat-strip"),
            _champion_banner(),
        ],
        className="hero-wrap",
    )


GUIDE = page_guide(
    "Final Results",
    [
        (
            "🏆",
            "Spain are the 2026 FIFA World Cup Champions — see the Final result above and the full tournament recap below.",
        ),
        (
            "🎬",
            "Top Moments highlights the tournament's most memorable matches — high-scoring games, big upsets, and knockout-stage drama.",
        ),
        (
            "📅",
            "Match cards are grouped by date. Hover a card to tilt it; click for full match details.",
        ),
        (
            "📊",
            "The stats bar (top) shows total matches, goals, and average goals per match across the whole tournament.",
        ),
        (
            "📈",
            "Goals Timeline and Match Timeline (bottom) cover every match day of the tournament, start to finish.",
        ),
    ],
    accent_color=COLORS["accent"],
)


PLOTLY_ANNOUNCEMENT_URL = "https://www.linkedin.com/posts/plotly_plotlycommunity-plotlydash-plotlychallenge-activity-7485000762293465088-GJsu"

def _winner_banner():
    """
    Site win announcement — deliberately impossible to miss: sticky to the
    top of the page as visitors scroll, high-contrast animated gradient,
    no dismiss button. A real, one-time achievement worth surfacing loudly.
    """
    return html.Div(
        [
            html.Span("🏆", style={"fontSize": "20px", "marginRight": "10px"}),
            html.Span(
                "WORLD RANK #1 — Plotly Dash App Challenge",
                style={"fontWeight": "900", "fontSize": "15px", "letterSpacing": "0.02em"},
            ),
            html.Span(" · ", style={"opacity": "0.6", "margin": "0 8px"}),
            html.Span(
                "STATDIUM ranked #1 worldwide",
                style={"fontWeight": "500", "fontSize": "13px"},
            ),
            html.A(
                "View the announcement →",
                href=PLOTLY_ANNOUNCEMENT_URL,
                target="_blank",
                style={"marginLeft": "14px", "fontWeight": "800", "fontSize": "13px",
                       "color": "#000", "textDecoration": "underline", "whiteSpace": "nowrap"},
            ),
        ],
        className="winner-banner",
    )


def layout():
    return html.Div(
        [
            dcc.Interval(id="live-interval", interval=20000, n_intervals=0),
            _winner_banner(),
            _hero(),
            page_wrapper(
                [
                    GUIDE,
                    html.Div(id="favorite-tracker", style={"marginBottom": "16px"}),
                    html.Div(id="live-stats-bar", style={"marginBottom": "24px"}),
                    html.Div(id="top-moments"),
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
    ensure_fresh()
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
    Output("hero-stat-strip", "children"), Input("live-interval", "n_intervals")
)
def update_hero_strip(_):
    ensure_fresh()
    cache = get_cache()
    matches = cache["matches"]
    finished = [m for m in matches if m["status"] == "FINISHED"]
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
                "Champion",
                f"{get_flag(CHAMPION_TEAM)} {CHAMPION_TEAM}",
                color=COLORS["gold"],
            ),
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


def _match_buzz_score(m):
    """
    Heuristic "how memorable was this match" score, built entirely from
    real match data — there's no social-media-buzz data source to draw
    from, so this is a transparent, explainable stand-in: high-scoring
    games, big upsets, and knockout-stage matches score higher. It's
    deliberately simple and inspectable, not a claim to know what fans
    online actually talked about most.
    """
    hs, as_ = m.get("home_score"), m.get("away_score")
    if hs is None or as_ is None:
        return -1
    goals = hs + as_
    home, away = m.get("home_team", ""), m.get("away_team", "")
    h_rank, a_rank = FIFA_RANKINGS.get(home, 60), FIFA_RANKINGS.get(away, 60)
    if hs > as_:
        winner_rank, loser_rank = h_rank, a_rank
    elif as_ > hs:
        winner_rank, loser_rank = a_rank, h_rank
    else:
        winner_rank = loser_rank = None
    upset_gap = max(0, winner_rank - loser_rank) if winner_rank is not None else 0
    round_weight = {"Final": 40, "SF": 28, "QF": 18, "R16": 10, "R32": 4}.get(
        normalize_round(m.get("round", "")) or "", 0
    )
    margin = abs(hs - as_)
    close_high_scoring_bonus = 8 if margin <= 1 and goals >= 3 else 0
    return goals * 4 + upset_gap * 1.5 + round_weight + close_high_scoring_bonus


def _top_moments(n=9):
    """Ranked list of the tournament's most memorable finished matches.
    FEATURED_MATCH_IDS (see top of file) always come first if set; the rest
    are ranked by _match_buzz_score."""
    matches = get_cache().get("matches", [])
    finished = [
        m
        for m in matches
        if m.get("status") == "FINISHED" and m.get("home_score") is not None
    ]
    featured = [m for m in finished if m.get("id") in FEATURED_MATCH_IDS]
    rest = [m for m in finished if m.get("id") not in FEATURED_MATCH_IDS]
    rest.sort(key=_match_buzz_score, reverse=True)
    return (featured + rest)[:n]


@app.callback(Output("top-moments", "children"), Input("live-interval", "n_intervals"))
def update_top_moments(_):
    ensure_fresh()
    moments = _top_moments(9)
    if not moments:
        return html.Div()

    cards = []
    for i, m in enumerate(moments, 1):
        badge = "🔥 " if i <= 3 else ""
        cards.append(
            html.Div(
                [
                    html.Div(
                        f"{badge}#{i}",
                        style={
                            "fontSize": "11px",
                            "fontWeight": "800",
                            "color": (
                                COLORS["gold"] if i <= 3 else COLORS["text_secondary"]
                            ),
                            "marginBottom": "4px",
                            "paddingLeft": "4px",
                        },
                    ),
                    match_scorecard(m),
                ]
            )
        )
    return html.Div(
        [
            section_header(
                "🎬 Top Moments",
                "The tournament's most memorable matches",
                accent_color=COLORS["gold"],
            ),
            html.Div(cards, className="match-date-grid"),
        ]
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
