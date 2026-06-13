from app_instance import app, server
from components.ui import COLORS, navbar
from data.fetcher import refresh_data
from pages import live, groups, bracket, teams, insights, formations
from dash import html, dcc, Input, Output
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", seconds=60, id="data_refresh")
scheduler.start()

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    navbar(),
    html.Div(id="page-content", style={"minHeight":"calc(100vh - 108px)","position":"relative","zIndex":"1"}),
    html.Div([
        html.Div([
            html.Span("STATDIUM ⚽", style={"fontWeight":"800","color":COLORS["accent"]}),
            html.Span("  ·  FIFA World Cup 2026 Analytics", style={"color":COLORS["text_secondary"],"fontSize":"12px"}),
            html.Span("  ·  openfootball + football-data.org", style={"color":COLORS["text_secondary"],"fontSize":"11px"}),
        ], style={"maxWidth":"1400px","margin":"0 auto","padding":"0 24px","display":"flex","alignItems":"center","gap":"4px"}),
    ], style={"backgroundColor":COLORS["bg_card"],"borderTop":f"1px solid {COLORS['border']}","height":"48px","display":"flex","alignItems":"center","marginTop":"48px","position":"relative","zIndex":"1"}),
], style={"backgroundColor":COLORS["bg_primary"],"minHeight":"100vh"})

@app.callback(Output("page-content","children"), Input("url","pathname"))
def route(pathname):
    return {
        "/":           live.layout,
        "/groups":     groups.layout,
        "/bracket":    bracket.layout,
        "/teams":      teams.layout,
        "/insights":   insights.layout,
        "/formations": formations.layout,
    }.get(pathname, live.layout)()

if __name__ == "__main__":
    app.run(debug=False)
