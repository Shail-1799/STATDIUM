"""Shared Dash app instance — imported by both app.py and all pages"""
import dash

OG_TITLE       = "STATDIUM ⚽ — FIFA World Cup 2026 Analytics"
OG_DESCRIPTION = ("Live scores · Elo intelligence · Monte Carlo bracket · "
                  "Historical heatmaps · What-If scenarios · 14 pages of free football data")
OG_URL         = "https://statdium.onrender.com"
OG_IMAGE       = f"{OG_URL}/assets/og_thumbnail.png"

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="STATDIUM ⚽ World Cup 2026",
    update_title=None,
    meta_tags=[
        {"name": "viewport",      "content": "width=device-width, initial-scale=1"},
        {"name": "description",   "content": OG_DESCRIPTION},
        {"name": "theme-color",   "content": "#07070C"},
        # Open Graph
        {"property": "og:type",        "content": "website"},
        {"property": "og:url",         "content": OG_URL},
        {"property": "og:title",       "content": OG_TITLE},
        {"property": "og:description", "content": OG_DESCRIPTION},
        {"property": "og:image",       "content": OG_IMAGE},
        {"property": "og:image:width", "content": "1200"},
        {"property": "og:image:height","content": "630"},
        # Twitter card
        {"name": "twitter:card",        "content": "summary_large_image"},
        {"name": "twitter:title",       "content": OG_TITLE},
        {"name": "twitter:description", "content": OG_DESCRIPTION},
        {"name": "twitter:image",       "content": OG_IMAGE},
    ],
)
server = app.server
