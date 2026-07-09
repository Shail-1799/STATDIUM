from app_instance import app, server
from components.ui import COLORS, sidebar
from data.fetcher import refresh_data, get_cache, refresh_matches
from pages import (live, groups, bracket, teams, insights, formations,
                   stadiums, leaderboards, confederations,
                   scenario, tactical_dna, animated_bracket, history,
                   predictor)
from pages.match_detail import modal_shell
from dash import html, dcc, Input, Output
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_matches, "interval", seconds=20, id="fast_refresh")
scheduler.add_job(refresh_data, "interval", seconds=120, id="full_refresh")
scheduler.start()

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="favorite-team-store", storage_type="local"),
        dcc.Interval(id="sidebar-progress-interval", interval=60000, n_intervals=0),
        # Always-present modal shell + permanent close button (outside modal body)
        modal_shell(),
        # modal-close-btn must always exist in DOM for Dash callback
        html.Button(id="modal-close-btn", n_clicks=0, style={"display": "none"}),
        sidebar(),
        html.Div(
            [
                html.Div(
                    id="page-content",
                    style={
                        "minHeight": "calc(100vh - 48px)",
                        "position": "relative",
                        "zIndex": "1",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.A(
                                    [
                                        html.Span(
                                            "⚽",
                                            style={
                                                "fontSize": "clamp(14px, 2vw, 18px)",
                                                "marginRight": "4px",
                                            },
                                        ),
                                        html.Span(
                                            "STAT",
                                            style={
                                                "color": COLORS["text_primary"],
                                                "fontFamily": "var(--font-display)",
                                                "fontWeight": "900",
                                                "fontSize": "clamp(13px, 1.8vw, 16px)",
                                                "letterSpacing": "-0.03em",
                                            },
                                        ),
                                        html.Span(
                                            "DIUM",
                                            className="shiny-text",
                                            style={
                                                "fontFamily": "var(--font-display)",
                                                "fontWeight": "900",
                                                "fontSize": "clamp(13px, 1.8vw, 16px)",
                                                "letterSpacing": "-0.03em",
                                            },
                                        ),
                                    ],
                                    href="/",
                                    style={
                                        "textDecoration": "none",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "whiteSpace": "nowrap",
                                    },
                                ),
                                html.Span(
                                    " © 2026 • Built with ❤️ by",
                                    style={
                                        "color": COLORS["text_primary"],
                                        "fontSize": "clamp(11px, 1.2vw, 14px)",
                                        "whiteSpace": "nowrap",
                                    },
                                ),
                                html.A(
                                    "Shail Shukla",
                                    href="https://www.linkedin.com/in/shail-shukla/",
                                    target="_blank",
                                    className="shiny-text",
                                    style={
                                        "fontFamily": "var(--font-display)",
                                        "fontWeight": "900",
                                        "fontSize": "clamp(11px, 1.2vw, 14px)",
                                        "textDecoration": "none",
                                        "whiteSpace": "nowrap",
                                    },
                                ),
                            ],
                            style={
                                "maxWidth": "1400px",
                                "width": "100%",
                                "margin": "0 auto",
                                "padding": "0 16px",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "flexWrap": "wrap",
                                "columnGap": "6px",
                                "rowGap": "2px",
                                "textAlign": "center",
                            },
                        ),
                    ],
                    style={
                        "backgroundColor": COLORS["bg_card"],
                        "borderTop": f"1px solid {COLORS['border']}",
                        "minHeight": "48px",
                        "padding": "10px 0",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginTop": "48px",
                        "position": "relative",
                        "zIndex": "1",
                    },
                ),
            ],
            id="statdium-main-content",
            className="statdium-main-content",
        ),
    ],
    style={"backgroundColor": COLORS["bg_primary"], "minHeight": "100vh"},
)


ROUTES = {
    "/": live.layout,
    "/live": live.layout,
    "/groups": groups.layout,
    "/bracket": bracket.layout,
    "/teams": teams.layout,
    "/insights": insights.layout,
    "/formations": formations.layout,
    "/stadiums": stadiums.layout,
    "/leaderboards": leaderboards.layout,
    # "/confederations": confederations.layout,
    "/scenario": scenario.layout,
    "/tactical-dna": tactical_dna.layout,
    "/simulator": animated_bracket.layout,
    "/history": history.layout,
    "/predictor": predictor.layout,
}

@app.callback(Output("page-content","children"), Input("url","pathname"))
def route(pathname):
    return ROUTES.get(pathname, live.layout)()


@app.callback(Output("sidebar-progress","children"),
              Input("sidebar-progress-interval","n_intervals"))
def update_sidebar_progress(_):
    cache  = get_cache()
    matches = cache.get("matches",[])
    total  = len(matches)
    played = len([m for m in matches if m["status"]=="FINISHED"])
    pct    = round(played/total*100) if total else 0
    return html.Div([
        html.Span("Tournament Progress", className="sidebar-label",
                  style={"fontSize":"10px","color":COLORS["text_secondary"],
                         "textTransform":"uppercase","letterSpacing":"0.06em"}),
        html.Div(
            html.Div(style={"width":f"{pct}%","height":"100%","backgroundColor":COLORS["accent"],
                            "borderRadius":"3px","transition":"width 0.8s ease"}),
            style={"backgroundColor":COLORS["bg_card2"],"borderRadius":"3px","height":"5px","margin":"6px 0"}
        ),
        html.Span(f"{played}/{total} matches · {pct}%", className="sidebar-label",
                  style={"fontSize":"10px","color":COLORS["accent"]}),
    ])


if __name__ == "__main__":
    app.run(debug=False)
