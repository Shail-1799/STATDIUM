from app_instance import app, server
from components.ui import COLORS, navbar
from data.fetcher import refresh_data
from pages import live, groups, bracket, teams, insights, formations, stadiums
from dash import html, dcc, Input, Output
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", seconds=60, id="data_refresh")
scheduler.start()

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="favorite-team-store", storage_type="local"),
        navbar(),
        html.Div(
            id="page-content",
            style={
                "minHeight": "calc(100vh - 108px)",
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
                                        "fontWeight": "900",
                                        "fontSize": "clamp(13px, 1.8vw, 16px)",
                                        "letterSpacing": "-0.03em",
                                    },
                                ),
                                html.Span(
                                    "DIUM",
                                    className="shiny-text",
                                    style={
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
    style={"backgroundColor": COLORS["bg_primary"], "minHeight": "100vh"},
)

@app.callback(Output("page-content","children"), Input("url","pathname"))
def route(pathname):
    return {
        "/":           live.layout,
        "/groups":     groups.layout,
        "/bracket":    bracket.layout,
        "/teams":      teams.layout,
        "/insights":   insights.layout,
        "/formations": formations.layout,
        "/stadiums":   stadiums.layout,
    }.get(pathname, live.layout)()

if __name__ == "__main__":
    app.run(debug=False)
