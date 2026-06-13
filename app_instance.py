"""Shared Dash app instance — imported by both app.py and all pages"""
import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="STATDIUM ⚽ World Cup 2026",
    update_title=None,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "STATDIUM — FIFA World Cup 2026 live analytics"},
    ],
)
server = app.server
