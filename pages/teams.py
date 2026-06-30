"""
STATDIUM — Team Explorer
Head-to-head comparison, radar, hype cards, follow/unfollow.
Follow state stored in dcc.Store (localStorage). Single always-present toggle button.
"""

from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper, stat_pill
from data.fetcher import WC2026_GROUPS, get_flag, get_cache, FIFA_RANKINGS, get_flag_img
from data.elo import get_elo_with_fallback

GUIDE = page_guide(
    "Team Explorer",
    [
        ("👥", "Select two teams from the dropdowns to compare them head-to-head."),
        ("📊", "Bar chart shows Wins, Draws, Losses, Goals For/Against side by side."),
        (
            "🕸️",
            "Radar chart maps 6 performance dimensions on a 0–100 scale — bigger shape = stronger team.",
        ),
        (
            "⚖️",
            "Win probability bar is calculated from live Elo ratings using the standard Elo formula.",
        ),
        (
            "⭐",
            "Click 'Follow' to pin Team A to your Live dashboard for quick tracking.",
        ),
    ],
    accent_color=COLORS["accent3"],
)


def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    opts = [{"label": f"{get_flag(t)} {t}", "value": t} for t in all_teams]

    return html.Div(
        [
            page_wrapper(
                [
                    GUIDE,
                    section_header(
                        "Team Explorer",
                        "Head-to-head comparison · Radar · Form guide",
                        accent_color=COLORS["accent3"],
                    ),
                    # Team selector row
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Team A",
                                        style={
                                            "fontSize": "11px",
                                            "color": COLORS["accent"],
                                            "marginBottom": "6px",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.08em",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="team-a",
                                        options=opts,
                                        value="Brazil",
                                        clearable=False,
                                    ),
                                ],
                                style={"flex": "1"},
                            ),
                            html.Div(
                                "VS",
                                style={
                                    "fontSize": "28px",
                                    "fontWeight": "800",
                                    "color": COLORS["text_secondary"],
                                    "alignSelf": "flex-end",
                                    "paddingBottom": "4px",
                                    "minWidth": "40px",
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        "Team B",
                                        style={
                                            "fontSize": "11px",
                                            "color": COLORS["accent2"],
                                            "marginBottom": "6px",
                                            "fontWeight": "700",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.08em",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="team-b",
                                        options=opts,
                                        value="France",
                                        clearable=False,
                                    ),
                                ],
                                style={"flex": "1"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "12px",
                            "alignItems": "flex-end",
                            "backgroundColor": COLORS["bg_card"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "20px",
                            "marginBottom": "16px",
                            "flexWrap": "wrap",
                        },
                    ),
                    # Follow banner — always rendered, reacts to store
                    html.Div(id="follow-banner"),
                    html.Div(id="team-comparison-content"),
                ]
            ),
        ]
    )


# ── Follow banner: shows current favourite + toggle button ─────────────────
@app.callback(
    Output("follow-banner", "children"),
    Input("favorite-team-store", "data"),
    Input("team-a", "value"),
)
def render_follow_banner(fav_data, team_a):
    fav = (fav_data or {}).get("team")
    is_following = fav == team_a

    if is_following:
        banner_style = {
            "display": "flex",
            "alignItems": "center",
            "gap": "12px",
            "padding": "10px 16px",
            "marginBottom": "16px",
            "backgroundColor": "rgba(255,215,0,0.08)",
            "border": f"1px solid {COLORS['gold']}44",
            "borderRadius": "10px",
        }
        return html.Div(
            [
                html.Span("⭐", style={"fontSize": "16px"}),
                get_flag_img(fav, width=22),
                html.Span(
                    f"Following {fav}",
                    style={
                        "fontWeight": "700",
                        "color": COLORS["gold"],
                        "fontSize": "13px",
                    },
                ),
                html.Button(
                    "✕ Unfollow",
                    id="follow-toggle-btn",
                    n_clicks=0,
                    style={
                        "marginLeft": "auto",
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "backgroundColor": "transparent",
                        "border": f"1px solid {COLORS['border']}",
                        "color": COLORS["text_secondary"],
                        "borderRadius": "7px",
                        "padding": "5px 12px",
                        "cursor": "pointer",
                    },
                ),
            ],
            style=banner_style,
        )
    else:
        following_someone_else = fav and fav != team_a
        note = f"(currently following {fav})" if following_someone_else else ""
        return html.Div(
            [
                html.Span("⭐", style={"fontSize": "16px"}),
                html.Span(
                    f"Follow {team_a} to track them on the Live page",
                    style={"fontSize": "12px", "color": COLORS["text_secondary"]},
                ),
                html.Span(
                    note,
                    style={
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"],
                        "opacity": "0.6",
                    },
                ),
                html.Button(
                    f"⭐ Follow {team_a}",
                    id="follow-toggle-btn",
                    n_clicks=0,
                    style={
                        "marginLeft": "auto",
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "backgroundColor": "rgba(255,215,0,0.1)",
                        "border": f"1px solid {COLORS['gold']}66",
                        "color": COLORS["gold"],
                        "borderRadius": "7px",
                        "padding": "5px 14px",
                        "cursor": "pointer",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "10px",
                "flexWrap": "wrap",
                "padding": "10px 16px",
                "marginBottom": "16px",
                "backgroundColor": COLORS["bg_card2"],
                "border": f"1px solid {COLORS['border']}",
                "borderRadius": "10px",
            },
        )


# ── Single toggle callback ─────────────────────────────────────────────────
@app.callback(
    Output("favorite-team-store", "data"),
    Input("follow-toggle-btn", "n_clicks"),
    State("team-a", "value"),
    State("favorite-team-store", "data"),
    prevent_initial_call=True,
)
def toggle_follow(n_clicks, team_a, current):
    fav = (current or {}).get("team")
    # If already following team_a → unfollow; else follow
    if fav == team_a:
        return {}
    return {"team": team_a}


# ── Comparison ─────────────────────────────────────────────────────────────
@app.callback(
    Output("team-comparison-content", "children"),
    Input("team-a", "value"),
    Input("team-b", "value"),
)
def update_comparison(team_a, team_b):
    if not team_a or not team_b:
        return html.Div()

    cache = get_cache()
    group_table = cache.get("groups", {})

    sa = _get_team_stats(team_a, group_table)
    sb = _get_team_stats(team_b, group_table)

    ea = get_elo_with_fallback(team_a)
    eb = get_elo_with_fallback(team_b)
    ra = FIFA_RANKINGS.get(team_a, 60)
    rb = FIFA_RANKINGS.get(team_b, 60)

    ca = "#00E5A0"
    cb = "#7B61FF"

    # Win probability
    prob_a = round(1 / (1 + 10 ** ((eb - ea) / 400)) * 100)
    prob_b = 100 - prob_a

    # ── Radar ──
    categories = [
        "Goals For",
        "Wins",
        "Points",
        "Win Rate %",
        "Clean Sheets",
        "Goal Diff",
    ]

    def rvals(s, elo):
        p = max(s["p"], 1)
        return [
            min(100, s["gf"] * 14),
            min(100, s["w"] * 34),
            min(100, s["pts"] * 11),
            round(s["w"] / p * 100),
            min(100, max(0, (p - s["ga"]) / p * 100)),
            min(100, max(0, (s["gd"] + 9) * 6)),
        ]

    va, vb = rvals(sa, ea), rvals(sb, eb)

    def hex_rgba(h, a=0.25):
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{a})"

    fig_radar = go.Figure()
    for vals, name, color in [(va, team_a, ca), (vb, team_b, cb)]:
        fig_radar.add_trace(
            go.Scatterpolar(
                r=vals + [vals[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=name,
                line=dict(color=color, width=2.5),
                fillcolor=hex_rgba(color, 0.2),
            )
        )
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor=COLORS["border"],
                linecolor=COLORS["border"],
                tickfont=dict(size=9, color=COLORS["text_secondary"]),
                tickvals=[0, 25, 50, 75, 100],
            ),
            angularaxis=dict(
                gridcolor=COLORS["border"],
                linecolor=COLORS["border"],
                tickfont=dict(size=11, color=COLORS["text_primary"]),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(
            text="<b>Performance Comparison</b>",
            font=dict(size=14, color=COLORS["text_primary"]),
            x=0.5,
            xanchor="center",
        ),
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=50, r=50, t=50, b=40),
        height=360,
        legend=dict(
            font=dict(size=12, color=COLORS["text_primary"]),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            x=0.5,
            y=-0.2,
            xanchor="center",
        ),
    )

    # ── Bar chart ──
    stat_keys = ["w", "d", "l", "gf", "ga"]
    stat_names = ["Wins", "Draws", "Losses", "Goals For", "Goals Ag."]
    fig_bars = go.Figure()
    for s, name, color in [(sa, team_a, ca), (sb, team_b, cb)]:
        fig_bars.add_bar(
            name=name,
            x=stat_names,
            y=[s[k] for k in stat_keys],
            marker_color=color,
            marker_line_width=0,
            opacity=0.9,
            text=[str(s[k]) for k in stat_keys],
            textposition="inside",
            textfont=dict(size=11),
        )
    fig_bars.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        title=dict(
            text=f"<b>{team_a.upper()} vs {team_b.upper()}</b>",
            font=dict(size=15, color=COLORS["text_primary"]),
            x=0.5,
            xanchor="center",
        ),
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0, r=0, t=50, b=0),
        height=360,
        legend=dict(
            font=dict(size=12, color=COLORS["text_primary"]),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            x=0.5,
            y=-0.2,
            xanchor="center",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=12, color=COLORS["text_primary"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            zeroline=False,
            showticklabels=True,
            tickfont=dict(size=10, color=COLORS["text_secondary"]),
        ),
        bargap=0.2,
        bargroupgap=0.04,
    )

    chart_card = lambda fig: html.Div(
        [
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ],
        style={
            "background": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "padding": "16px",
            "flex": "1",
            "minWidth": "280px",
        },
    )

    # ── Win probability bar ──
    prob_bar = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        f"{get_flag(team_a)} {team_a}",
                        style={"fontSize": "13px", "fontWeight": "700", "color": ca},
                    ),
                    html.Div(
                        f"{prob_a}%",
                        style={"fontSize": "22px", "fontWeight": "900", "color": ca},
                    ),
                ]
            ),
            html.Div(
                [
                    html.Div(
                        style={
                            "width": f"{prob_a}%",
                            "height": "100%",
                            "background": ca,
                            "borderRadius": "4px 0 0 4px",
                            "transition": "width 0.8s ease",
                        }
                    ),
                    html.Div(
                        style={
                            "width": f"{prob_b}%",
                            "height": "100%",
                            "background": cb,
                            "borderRadius": "0 4px 4px 0",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "height": "10px",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                    "margin": "8px 0",
                },
            ),
            html.Div(
                [
                    html.Div(
                        f"{prob_b}%",
                        style={
                            "fontSize": "22px",
                            "fontWeight": "900",
                            "color": cb,
                            "textAlign": "right",
                        },
                    ),
                    html.Div(
                        f"{get_flag(team_b)} {team_b}",
                        style={
                            "fontSize": "13px",
                            "fontWeight": "700",
                            "color": cb,
                            "textAlign": "right",
                        },
                    ),
                ]
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0",
            "background": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "padding": "16px 20px",
            "marginBottom": "20px",
        },
    )

    # ── Quick stats comparison ──
    def cmp_row(label, va, vb):
        better_a = va > vb
        better_b = vb > va
        return html.Div(
            [
                html.Span(
                    str(va),
                    style={
                        "fontWeight": "800" if better_a else "400",
                        "color": ca if better_a else COLORS["text_secondary"],
                        "fontSize": "14px",
                        "width": "40px",
                        "textAlign": "right",
                    },
                ),
                html.Span(
                    label,
                    style={
                        "flex": "1",
                        "textAlign": "center",
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"],
                        "textTransform": "uppercase",
                        "letterSpacing": "0.06em",
                    },
                ),
                html.Span(
                    str(vb),
                    style={
                        "fontWeight": "800" if better_b else "400",
                        "color": cb if better_b else COLORS["text_secondary"],
                        "fontSize": "14px",
                        "width": "40px",
                        "textAlign": "left",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
                "padding": "7px 0",
                "borderBottom": f"1px solid {COLORS['border']}",
            },
        )

    stats_cmp = (
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            get_flag_img(team_a, width=32),
                            style={"textAlign": "center"},
                        ),
                        html.Div(
                            team_a,
                            style={
                                "fontSize": "12px",
                                "fontWeight": "700",
                                "color": ca,
                                "textAlign": "center",
                                "marginTop": "4px",
                            },
                        ),
                    ],
                    style={"flex": "1"},
                ),
                html.Div(style={"flex": "2"}),
                html.Div(
                    [
                        html.Div(
                            get_flag_img(team_b, width=32),
                            style={"textAlign": "center"},
                        ),
                        html.Div(
                            team_b,
                            style={
                                "fontSize": "12px",
                                "fontWeight": "700",
                                "color": cb,
                                "textAlign": "center",
                                "marginTop": "4px",
                            },
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ]
            + [],
            style={"display": "flex", "marginBottom": "12px"},
        ),
    )

    quick_stats = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                get_flag_img(team_a, width=28),
                                style={"textAlign": "center"},
                            ),
                            html.Div(
                                team_a,
                                style={
                                    "fontSize": "11px",
                                    "color": ca,
                                    "fontWeight": "700",
                                    "textAlign": "center",
                                    "marginTop": "3px",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(style={"flex": "2"}),
                    html.Div(
                        [
                            html.Div(
                                get_flag_img(team_b, width=28),
                                style={"textAlign": "center"},
                            ),
                            html.Div(
                                team_b,
                                style={
                                    "fontSize": "11px",
                                    "color": cb,
                                    "fontWeight": "700",
                                    "textAlign": "center",
                                    "marginTop": "3px",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                ],
                style={"display": "flex", "marginBottom": "10px"},
            ),
            cmp_row("Elo Rating", ea, eb),
            cmp_row(
                "FIFA Rank ↑ lower is better", rb, ra
            ),  # inverted: lower rank number = better
            cmp_row("Points", sa["pts"], sb["pts"]),
            cmp_row("Wins", sa["w"], sb["w"]),
            cmp_row("Goals For", sa["gf"], sb["gf"]),
            cmp_row("Goal Diff", sa["gd"], sb["gd"]),
        ],
        style={
            "background": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "padding": "16px 20px",
            "flex": "1",
            "minWidth": "240px",
        },
    )

    return html.Div(
        [
            section_header(
                "Head-to-Head",
                "Elo win probability + stats",
                accent_color=COLORS["accent3"],
            ),
            prob_bar,
            html.Div(
                [
                    chart_card(fig_bars),
                    quick_stats,
                    chart_card(fig_radar),
                ],
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
            ),
        ]
    )


def _get_team_stats(team, group_table):
    for grp in group_table.values():
        if team in grp:
            t = grp[team]
            return {
                "pts": t.get("pts", 0),
                "w": t.get("w", 0),
                "d": t.get("d", 0),
                "l": t.get("l", 0),
                "gf": t.get("gf", 0),
                "ga": t.get("ga", 0),
                "gd": t.get("gf", 0) - t.get("ga", 0),
                "p": t.get("p", 0),
            }
    return {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "p": 0}
