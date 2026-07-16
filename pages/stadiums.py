"""
STATDIUM — Stadiums + Clock Wall (merged)
16 host venues: weather, local time, capacity, next match, map link.
4-column grid layout.
"""
from dash import html, dcc, Input, Output
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper, get_flag_img
from data.fetcher import get_cache, get_flag
from data.media_links import get_stadium_maps_link

HOST_VENUES = [
    {"city":"New York/NJ",  "state":"NJ",   "stadium":"MetLife Stadium",        "country":"USA",    "flag":"🇺🇸","tz":"America/New_York",    "lat":40.8135, "lon":-74.0745,"capacity":82500},
    {"city":"Los Angeles",  "state":"CA",   "stadium":"SoFi Stadium",            "country":"USA",    "flag":"🇺🇸","tz":"America/Los_Angeles",  "lat":33.9535, "lon":-118.3392,"capacity":70240},
    {"city":"Dallas",       "state":"TX",   "stadium":"AT&T Stadium",            "country":"USA",    "flag":"🇺🇸","tz":"America/Chicago",      "lat":32.7480, "lon":-97.0927,"capacity":80000},
    {"city":"San Francisco","state":"CA",   "stadium":"Levi's Stadium",          "country":"USA",    "flag":"🇺🇸","tz":"America/Los_Angeles",  "lat":37.4033, "lon":-121.9694,"capacity":68500},
    {"city":"Miami",        "state":"FL",   "stadium":"Hard Rock Stadium",       "country":"USA",    "flag":"🇺🇸","tz":"America/New_York",    "lat":25.9580, "lon":-80.2389,"capacity":65326},
    {"city":"Seattle",      "state":"WA",   "stadium":"Lumen Field",             "country":"USA",    "flag":"🇺🇸","tz":"America/Los_Angeles",  "lat":47.5952, "lon":-122.3316,"capacity":68740},
    {"city":"Boston",       "state":"MA",   "stadium":"Gillette Stadium",        "country":"USA",    "flag":"🇺🇸","tz":"America/New_York",    "lat":42.0909, "lon":-71.2643,"capacity":65878},
    {"city":"Philadelphia", "state":"PA",   "stadium":"Lincoln Financial Field", "country":"USA",    "flag":"🇺🇸","tz":"America/New_York",    "lat":39.9008, "lon":-75.1675,"capacity":69328},
    {"city":"Kansas City",  "state":"MO",   "stadium":"Arrowhead Stadium",       "country":"USA",    "flag":"🇺🇸","tz":"America/Chicago",      "lat":39.0489, "lon":-94.4839,"capacity":73000},
    {"city":"Atlanta",      "state":"GA",   "stadium":"Mercedes-Benz Stadium",   "country":"USA",    "flag":"🇺🇸","tz":"America/New_York",    "lat":33.7554, "lon":-84.4010,"capacity":71000},
    {"city":"Houston",      "state":"TX",   "stadium":"NRG Stadium",             "country":"USA",    "flag":"🇺🇸","tz":"America/Chicago",      "lat":29.6847, "lon":-95.4107,"capacity":72220},
    {"city":"Vancouver",    "state":"BC",   "stadium":"BC Place",                "country":"Canada", "flag":"🇨🇦","tz":"America/Vancouver",    "lat":49.2767, "lon":-123.1115,"capacity":54500},
    {"city":"Toronto",      "state":"ON",   "stadium":"BMO Field",               "country":"Canada", "flag":"🇨🇦","tz":"America/Toronto",      "lat":43.6333, "lon":-79.4167,"capacity":30000},
    {"city":"Mexico City",  "state":"CDMX", "stadium":"Estadio Azteca",          "country":"Mexico", "flag":"🇲🇽","tz":"America/Mexico_City",  "lat":19.3028, "lon":-99.1508,"capacity":87523},
    {"city":"Guadalajara",  "state":"JAL",  "stadium":"Estadio Akron",           "country":"Mexico", "flag":"🇲🇽","tz":"America/Mexico_City",  "lat":20.6752, "lon":-103.4679,"capacity":49850},
    {"city":"Monterrey",    "state":"NL",   "stadium":"Estadio BBVA",            "country":"Mexico", "flag":"🇲🇽","tz":"America/Monterrey",    "lat":25.6695, "lon":-100.2427,"capacity":53500},
]

GUIDE = page_guide("Stadiums & Clock Wall", [
    ("🕐", "Each card shows the current local time at that stadium city — updates every 30 seconds."),
    ("🌡️", "Temperature and weather icon come from Open-Meteo live API."),
    ("⚽", "'Next match' shows the upcoming fixture at that venue (matched by city name)."),
    ("📍", "'Open in Maps' links directly to the stadium location on Google Maps."),
], accent_color=COLORS["accent"])

def layout():
    return html.Div([
        dcc.Interval(id="stadiums-interval", interval=30000, n_intervals=0),
        page_wrapper([
            GUIDE,
            section_header("🏟️ Stadiums & Clock Wall",
                           "16 host venues · Local time · Weather · Capacity · Next match",
                           accent_color=COLORS["accent"]),
            html.Div([
                html.Div("Clocks update every 30 seconds · Temperature from Open-Meteo",
                         style={"fontSize":"12px","color":COLORS["text_secondary"]}),
                html.Div(id="stadiums-last-update",
                         style={"fontSize":"11px","color":COLORS["accent"]}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "marginBottom":"20px","flexWrap":"wrap","gap":"8px"}),
            html.Div(id="stadiums-grid"),
        ]),
    ])


@app.callback(
    Output("stadiums-grid", "children"),
    Output("stadiums-last-update", "children"),
    Input("stadiums-interval", "n_intervals"),
)
def update_stadiums(_):
    from datetime import datetime
    import requests

    try:
        import pytz
        HAS_PYTZ = True
    except ImportError:
        HAS_PYTZ = False

    cache = get_cache()
    matches = cache.get("matches", [])
    upcoming = [m for m in matches if m.get("status") in ("SCHEDULED", "TIMED", "LIVE")]

    # Batch weather
    weather = {}
    try:
        lats = ",".join(str(v["lat"]) for v in HOST_VENUES)
        lons = ",".join(str(v["lon"]) for v in HOST_VENUES)
        url  = (f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lats}&longitude={lons}&current_weather=true&forecast_days=1")
        resp = requests.get(url, timeout=5)
        if resp.ok:
            data = resp.json()
            if isinstance(data, list):
                for i, d in enumerate(data):
                    cw = d.get("current_weather", {})
                    weather[i] = {"temp": cw.get("temperature"), "code": cw.get("weathercode", 0)}
    except Exception:
        pass

    def wicon(code):
        if code is None: return "🌤"
        if code == 0:    return "☀️"
        if code <= 2:    return "⛅"
        if code <= 48:   return "🌫"
        if code <= 67:   return "🌧"
        if code <= 77:   return "❄️"
        if code <= 82:   return "🌦"
        return "⛈"

    now_utc = datetime.utcnow()
    cards = []
    for i, v in enumerate(HOST_VENUES):
        w = weather.get(i, {})

        # Local time
        if HAS_PYTZ:
            try:
                import pytz
                tz = pytz.timezone(v["tz"])
                local = datetime.now(tz)
                local_time = local.strftime("%H:%M")
                local_date = local.strftime("%a %b %d")
            except Exception:
                local_time = "—"; local_date = ""
        else:
            local_time = "—"; local_date = ""

        # Next match at this venue
        next_str    = "No upcoming matches"
        next_detail = v["stadium"]
        is_live_v   = False
        for m in upcoming:
            venue_str = str(m.get("venue", ""))
            if v["city"].split("/")[0] in venue_str or v["stadium"][:8] in venue_str:
                if m["status"] == "LIVE":
                    next_str    = "🔴 LIVE NOW"
                    next_detail = [html.Span(get_flag_img(m["home_team"], width=20)), 
                                   f" {m['home_team']} vs {m['away_team']} ", 
                                   html.Span(get_flag_img(m["away_team"], width=20))]
                    is_live_v   = True
                else:
                    next_str    = f"Next Match: {m.get('date', '')}"
                    next_detail = [
                        html.Span(get_flag_img(m["home_team"], width=20)),
                        f" {m['home_team']} vs {m['away_team']} ",
                        html.Span(get_flag_img(m["away_team"], width=20)),
                    ]
                break

        maps_url = get_stadium_maps_link(v["lat"], v["lon"], v["stadium"])

        card = html.Div(
            [
                # Flag + city
                html.Div(
                    [
                        html.Span(
                            get_flag_img(v["country"], width=40)
                        ),
                        html.Div(
                            [
                                html.Div(
                                    v["city"],
                                    style={
                                        "fontSize": "16px",
                                        "fontWeight": "800",
                                        "color": COLORS["text_primary"],
                                    },
                                ),
                                html.Div(
                                    v["state"] + " · " + v["country"],
                                    style={
                                        "fontSize": "12px",
                                        "color": COLORS["text_secondary"],
                                    },
                                ),
                            ]
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "8px",
                        "marginBottom": "10px",
                    },
                ),
                # Clock
                html.Div(
                    local_time,
                    style={
                        "fontSize": "30px",
                        "fontWeight": "900",
                        "letterSpacing": "-0.03em",
                        "color": COLORS["live_red"] if is_live_v else COLORS["accent"],
                        "lineHeight": "1",
                        "marginBottom": "2px",
                        "fontVariantNumeric": "tabular-nums",
                    },
                ),
                html.Div(
                    local_date,
                    style={
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"],
                        "marginBottom": "10px",
                    },
                ),
                # Weather + capacity row
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    wicon(w.get("code")), style={"fontSize": "15px"}
                                ),
                                html.Span(
                                    (
                                        f" {w['temp']}°C"
                                        if w.get("temp") is not None
                                        else " —"
                                    ),
                                    style={
                                        "fontSize": "12px",
                                        "color": COLORS["text_primary"],
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center"},
                        ),
                        html.Div(
                            f"Cap {v['capacity']:,}",
                            style={
                                "fontSize": "10px",
                                "color": COLORS["text_secondary"],
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "borderBottom": f"1px solid {COLORS['border']}",
                        "paddingBottom": "10px",
                        "marginBottom": "10px",
                    },
                ),
                # Next match
                html.Div(
                    next_str,
                    style={
                        "fontSize": "10px",
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.06em",
                        "marginBottom": "2px",
                        "color": (
                            COLORS["live_red"]
                            if is_live_v
                            else COLORS["text_secondary"]
                        ),
                    },
                ),
                html.Div(
                    next_detail,
                    style={
                        "fontSize": "11px",
                        "color": COLORS["text_secondary"],
                        "lineHeight": "1.4",
                        "marginBottom": "10px",
                        "minHeight": "16px",
                    },
                ),
                # Maps link
                html.A(
                    "📍 Open in Maps",
                    href=maps_url,
                    target="_blank",
                    className="stadium-map-link",
                ),
            ],
            className="glow-card",
            style={
                "background": COLORS["bg_card"],
                "border": (
                    f"2px solid {COLORS['live_red']}44"
                    if is_live_v
                    else f"1px solid {COLORS['border']}"
                ),
                "borderTop": (
                    f"3px solid {COLORS['live_red']}"
                    if is_live_v
                    else f"3px solid {COLORS['accent']}"
                ),
                "borderRadius": "14px",
                "padding": "16px",
                "transition": "all 0.2s ease",
            },
        )
        cards.append(card)

    grid = html.Div(cards, style={
        "display":"grid",
        "gridTemplateColumns":"repeat(4, 1fr)",
        "gap":"14px",
    })
    return grid, f"Updated {now_utc.strftime('%H:%M')} UTC"
