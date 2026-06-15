"""
STATDIUM — Stadiums & Weather + 3D Globe
Free APIs: Open-Meteo (weather, no key) + REST Countries (no key)
"""
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper
from data.fetcher import WC2026_GROUPS, get_flag, FIFA_RANKINGS, get_cache
from data.enrichment import WC2026_STADIUMS, fetch_stadium_weather, get_weather_label, ISO2_MAP

def layout():
    return html.Div([
        dcc.Interval(id="stadiums-interval", interval=1800000, n_intervals=0),  # 30 min
        page_wrapper([
            section_header("Stadiums & Match Day Conditions",
                           "Live weather at all 16 host venues · 3D tournament globe",
                           accent_color=COLORS["accent2"]),
            html.Div(id="globe-container", style={"marginBottom":"24px"}),
            html.Div(id="stadiums-grid"),
        ]),
    ])


@app.callback(Output("globe-container","children"), Input("stadiums-interval","n_intervals"))
def update_globe(_):
    """3D orthographic globe showing all 48 nations + stadium locations"""
    cache = get_cache()
    group_table = cache.get("groups", {})
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]

    # Country markers (approx capital coords for visualization)
    fig = go.Figure()

    # Stadium markers
    stadium_lats = [c[0] for c in WC2026_STADIUMS.values()]
    stadium_lons = [c[1] for c in WC2026_STADIUMS.values()]
    stadium_names = list(WC2026_STADIUMS.keys())

    fig.add_trace(go.Scattergeo(
        lon=stadium_lons, lat=stadium_lats,
        mode="markers",
        marker=dict(size=10, color=COLORS["accent"], symbol="circle",
                    line=dict(width=2, color="white"), opacity=0.9),
        text=[s.split("(")[0].strip() for s in stadium_names],
        hovertemplate="<b>⚽ %{text}</b><extra></extra>",
        name="Host Stadiums",
    ))

    fig.update_geos(
        projection_type="orthographic",
        showland=True, landcolor=COLORS["bg_card2"],
        showocean=True, oceancolor=COLORS["bg_primary"],
        showcountries=True, countrycolor=COLORS["border"],
        showcoastlines=True, coastlinecolor=COLORS["border"],
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        projection_rotation=dict(lon=-95, lat=25, roll=0),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=0,b=0),
        height=420,
        font=dict(color=COLORS["text_secondary"]),
        showlegend=False,
    )

    return html.Div([
        html.Div("🌍 Tournament Globe — Host Stadiums (drag to rotate)",
                 style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase",
                       "letterSpacing":"0.06em","marginBottom":"8px"}),
        dcc.Graph(figure=fig, config={"displayModeBar":False,"scrollZoom":True}),
    ], className="glow-card", style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"12px","padding":"20px"})


@app.callback(Output("stadiums-grid","children"), Input("stadiums-interval","n_intervals"))
def update_stadiums(_):
    cards = []
    for stadium, (lat, lon) in WC2026_STADIUMS.items():
        city = stadium.split("(")[-1].replace(")","").strip()
        venue_name = stadium.split("(")[0].strip()

        weather = fetch_stadium_weather(stadium)
        if weather:
            cw = weather.get("current_weather", {})
            temp = cw.get("temperature")
            wcode = cw.get("weathercode")
            wind = cw.get("windspeed")
            label = get_weather_label(wcode)

            daily = weather.get("daily", {})
            forecast_html = []
            if daily.get("time"):
                for i in range(min(3, len(daily["time"]))):
                    tmax = daily["temperature_2m_max"][i]
                    tmin = daily["temperature_2m_min"][i]
                    pcode = daily["weathercode"][i]
                    rain = daily.get("precipitation_probability_max",[0,0,0])[i]
                    date = daily["time"][i]
                    forecast_html.append(html.Div([
                        html.Span(date[5:], style={"fontSize":"10px","color":COLORS["text_secondary"],"minWidth":"36px"}),
                        html.Span(get_weather_label(pcode).split(" ")[0], style={"fontSize":"14px"}),
                        html.Span(f"{tmin:.0f}°–{tmax:.0f}°C", style={"fontSize":"11px","color":COLORS["text_primary"],"minWidth":"60px"}),
                        html.Span(f"💧{rain:.0f}%", style={"fontSize":"10px","color":COLORS["accent2"]}),
                    ], style={"display":"flex","alignItems":"center","gap":"8px","padding":"4px 0"}))

            weather_block = html.Div([
                html.Div([
                    html.Span(label.split(" ")[0], style={"fontSize":"32px"}),
                    html.Div([
                        html.Div(f"{temp:.0f}°C", style={"fontSize":"20px","fontWeight":"700","color":COLORS["text_primary"]}),
                        html.Div(label.split(" ",1)[1] if " " in label else label, style={"fontSize":"11px","color":COLORS["text_secondary"]}),
                    ]),
                    html.Div(f"💨 {wind:.0f} km/h", style={"fontSize":"11px","color":COLORS["text_secondary"],"marginLeft":"auto"}),
                ], style={"display":"flex","alignItems":"center","gap":"10px","marginBottom":"8px"}),
                html.Div(forecast_html, style={"borderTop":f"1px solid {COLORS['border']}","paddingTop":"6px"}),
            ])
        else:
            weather_block = html.Div("Weather data unavailable",
                                     style={"fontSize":"11px","color":COLORS["text_secondary"],"padding":"8px 0"})

        cards.append(html.Div([
            html.Div([
                html.Div(venue_name, style={"fontSize":"14px","fontWeight":"700","color":COLORS["text_primary"]}),
                html.Div(city, style={"fontSize":"11px","color":COLORS["accent"]}),
            ], style={"marginBottom":"10px"}),
            weather_block,
        ], className="glow-card", style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                  "borderRadius":"12px","padding":"16px","flex":"1","minWidth":"220px"}))

    return html.Div([
        section_header("Host Venues","Current conditions + 3-day forecast",accent_color=COLORS["accent3"]),
        html.Div(cards, className="resp-grid-3", style={"display":"flex","gap":"16px","flexWrap":"wrap"}),
    ])
