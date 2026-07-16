from dash import html, dcc, Input, Output
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import get_cache

GUIDE = page_guide(
    "About",
    [
        (
            "📡",
            "Where every number on this site comes from — data sources, refresh timing, and the exact rules used to decide LIVE vs FINISHED.",
        ),
        (
            "📈",
            "How the Elo model and Monte Carlo simulations actually work — no black boxes.",
        ),
        (
            "⚠️",
            "Known limitations, stated plainly — a source of truth should show its assumptions, not just its numbers.",
        ),
    ],
    accent_color=COLORS["accent3"],
)


def _row(label, value):
    return html.Div(
        [
            html.Div(
                label,
                style={
                    "fontSize": "11px",
                    "fontWeight": "700",
                    "color": COLORS["text_secondary"],
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "minWidth": "160px",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "13px",
                    "color": COLORS["text_primary"],
                    "lineHeight": "1.6",
                    "flex": "1",
                },
            ),
        ],
        style={
            "display": "flex",
            "gap": "16px",
            "padding": "10px 0",
            "borderBottom": f"1px solid {COLORS['border']}",
            "flexWrap": "wrap",
        },
    )


def _section(title, children, accent=None):
    return html.Div(
        [
            section_header(title, "", accent_color=accent or COLORS["accent3"]),
            html.Div(children, style={"marginTop": "4px"}),
        ],
        style={
            "backgroundColor": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "padding": "20px",
            "marginBottom": "20px",
        },
    )


def layout():
    return html.Div(
        [
            dcc.Interval(id="about-interval", interval=30000, n_intervals=0),
            page_wrapper(
                [
                    GUIDE,
                    section_header(
                        "About STATDIUM",
                        "How the data, predictions, and simulations actually work",
                        accent_color=COLORS["accent3"],
                    ),
                    _section(
                        "📡 Data sources & refresh timing",
                        [
                            _row(
                                "Fixtures & results",
                                "openfootball/worldcup.json — a community-maintained schedule feed. This is the schedule backbone; it's hand-updated, so a just-finished result can occasionally lag a few minutes to hours behind real life.",
                            ),
                            _row(
                                "Live scores overlay",
                                "football-data.org's live matches endpoint, when FD_API_KEY is configured. Normally accurate within minutes of the real result — this is the primary source for anything time-sensitive.",
                            ),
                            _row(
                                "Scorers & team crests",
                                "football-data.org, refreshed less frequently than match scores to stay within the free-tier rate limit (10 requests/minute).",
                            ),
                            _row(
                                "Elo ratings",
                                "eloratings.net — an independent, long-running football Elo rating system, not affiliated with FIFA rankings.",
                            ),
                            _row(
                                "Stadium weather",
                                "Open-Meteo, live per-venue forecast.",
                            ),
                            _row(
                                "Lineups / match events / stats",
                                "RapidAPI (free-tier football data), when RAPIDAPI_KEY is configured.",
                            ),
                            _row(
                                "GDP figures",
                                "World Bank, 2023 USD billions — embedded as a static snapshot, not live-refreshed.",
                            ),
                            _row(
                                "Refresh cadence",
                                "A background job refreshes match data on an interval, and every page's own display also checks staleness on each load/poll and self-refreshes if the cache is older than ~20 seconds — so data freshness doesn't depend solely on a background thread staying alive between visits.",
                            ),
                            html.Div(
                                id="about-live-status", style={"marginTop": "12px"}
                            ),
                        ],
                    ),
                    _section(
                        "🟢 How LIVE / FINISHED status is decided",
                        [
                            html.P(
                                "One rule, deliberately simple: if a real final score exists in the data, the match is FINISHED. If it doesn't, it's SCHEDULED. Nothing is inferred from the clock, the date, or how much time has \"probably\" passed — a match is never guessed into FINISHED or LIVE based on elapsed time alone.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                            html.P(
                                "LIVE is only ever set when football-data.org itself reports a match as IN_PLAY or PAUSED — a real external signal, not a local assumption. And once football-data.org or the schedule feed reports a status, it can only ever upgrade (SCHEDULED → LIVE → FINISHED), never downgrade — so a delayed or stale API response can't accidentally undo a confirmed result.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        "📈 Elo ratings & win probability",
                        [
                            html.P(
                                "Every team's Elo rating is pulled from eloratings.net. To turn two ratings into a win probability, we use the standard Elo logistic formula:",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                            html.Div(
                                "P(A beats B) = 1 / (1 + 10^((Elo_B − Elo_A) / 400))",
                                style={
                                    "fontFamily": "monospace",
                                    "fontSize": "13px",
                                    "color": COLORS["gold"],
                                    "backgroundColor": (
                                        COLORS["bg_card2"]
                                        if "bg_card2" in COLORS
                                        else COLORS["bg_card"]
                                    ),
                                    "padding": "12px 16px",
                                    "borderRadius": "8px",
                                    "margin": "8px 0",
                                },
                            ),
                            html.P(
                                "This is the exact same formula chess Elo ratings use — a 400-point Elo gap corresponds to roughly a 10:1 favorite. It powers the win/loss outcome in the bracket simulator below.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_secondary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        '🎲 Bracket simulator — how "Simulate Tournament" actually works',
                        [
                            html.P(
                                "The simulator does not replay the whole tournament from scratch. It builds the knockout bracket from the ACTUAL current state: any match that's already been played uses its real result — locked in, never re-randomized. Only fixtures that genuinely haven't happened yet get Elo-based simulation.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                            html.P(
                                'In practice, this means "Simulate Tournament" answers "who wins from here" — not "what if we replayed everything." The deeper into the knockout stage the real tournament gets, the more of the bracket is real results and the less is simulated.',
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_secondary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        "📊 Group-stage qualification probability",
                        [
                            html.P(
                                "While a group is still in progress, the qualification-probability bars are generated by simulating that group's remaining round-robin matches thousands of times, using each team's FIFA ranking converted into a win-strength score (higher-ranked teams are more likely to win a simulated match, with a built-in chance of a draw). The percentage shown is simply how often a team finished top-2 (or 3rd) across those simulations.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                            html.P(
                                "This is an estimate from a simplified model, not a guarantee — it doesn't know about injuries, tactics, or form, only FIFA ranking. The moment a group actually finishes all 6 matches, these probability bars are replaced entirely by the real, decided result — we don't keep showing a \"73% chance\" for something that's already 100% certain.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_secondary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        "⚡ Shock Index (upset risk)",
                        [
                            html.P(
                                "A simple 0–100 score based purely on the FIFA ranking gap between two teams — the bigger the gap in the underdog's favor, the higher the score. It's a rough, explainable heuristic for \"how surprising would an upset be here,\" not a probability model.",
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        "📜 History heatmap — what the tags mean",
                        [
                            html.P(
                                'Every tag (GS, R16, QF, SF, F, W) means "furthest stage reached", not "won that specific match." A team tagged QF made the quarter-final, whether they won or lost it — same convention historians use. The current tournament\'s column updates live and resolves to the real final result the moment it\'s actually decided; nothing is filled in early.',
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                            html.P(
                                '1942 and 1946 are intentionally excluded from the year range — no World Cup was held either year (WWII), so those years are correctly omitted rather than mislabeled "Did Not Qualify."',
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_secondary"],
                                    "lineHeight": "1.7",
                                },
                            ),
                        ],
                    ),
                    _section(
                        "⚠️ Known limitations — stated plainly",
                        [
                            html.Ul(
                                [
                                    html.Li(
                                        "No penalty-shootout data: a knockout match tied after 90/120 minutes and decided on penalties still shows as a draw in win/loss stats — we don't have shootout results in the underlying data.",
                                        style={"marginBottom": "8px"},
                                    ),
                                    html.Li(
                                        "The schedule feed is community-maintained and hand-updated — a just-finished result can occasionally lag behind real life until football-data.org's live overlay catches up, or the schedule feed itself is updated.",
                                        style={"marginBottom": "8px"},
                                    ),
                                    html.Li(
                                        "GDP figures are a static 2023 World Bank snapshot, not live-refreshed.",
                                        style={"marginBottom": "8px"},
                                    ),
                                    html.Li(
                                        "Group-stage qualification probabilities are a simplified FIFA-ranking-based estimate, not a full form/injury/tactics model.",
                                        style={"marginBottom": "8px"},
                                    ),
                                ],
                                style={
                                    "fontSize": "13px",
                                    "color": COLORS["text_primary"],
                                    "lineHeight": "1.8",
                                    "paddingLeft": "20px",
                                },
                            ),
                        ],
                    ),
                ]
            ),
        ]
    )


@app.callback(
    Output("about-live-status", "children"), Input("about-interval", "n_intervals")
)
def update_live_status(_):
    cache = get_cache()
    last_updated = cache.get("last_updated")
    source = cache.get("source", "unknown")
    matches = cache.get("matches", [])
    return html.Div(
        [
            html.Span("● ", style={"color": COLORS["accent"]}),
            html.Span(
                f"Cache last refreshed: {last_updated or 'not yet run'} · source: {source} · {len(matches)} matches loaded",
                style={"fontSize": "11px", "color": COLORS["text_secondary"]},
            ),
        ]
    )
