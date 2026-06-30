"""
STATDIUM — Confederation Wall & Elo Intelligence
Real Elo ratings from eloratings.net + confederation strength comparison
"""
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import get_flag_img, WC2026_GROUPS

CONF_NAMES = {
    "UEFA":"Europe (UEFA)", "CONMEBOL":"South America (CONMEBOL)",
    "CONCACAF":"North/Central America (CONCACAF)", "CAF":"Africa (CAF)",
    "AFC":"Asia (AFC)", "OFC":"Oceania (OFC)", "Other":"Other",
}
CONF_COLORS = {
    "UEFA":"#00E5A0","CONMEBOL":"#FF6B35","CONCACAF":"#7B61FF",
    "CAF":"#FFD700","AFC":"#00B4D8","OFC":"#FB8500","Other":"#8A8A9A",
}

GUIDE = page_guide("Elo Intelligence", [
    ("🌐", "Confederation strength chart compares average Elo ratings across UEFA, CONMEBOL, etc."),
    ("📊", "Elo wall shows all 48 teams sorted by current rating — updated after every match."),
    ("📈", "Elo rating changes after each result: upset wins gain more points than expected wins."),
], accent_color=COLORS["accent"])

def layout():
    return html.Div([
        dcc.Interval(id="conf-interval", interval=300000, n_intervals=0),
        page_wrapper([
            GUIDE,
            section_header("Elo Intelligence","Live ratings from eloratings.net · Confederation strength comparison",accent_color=COLORS["accent"]),
            html.Div(id="conf-content"),
        ]),
    ])


@app.callback(Output("conf-content","children"), Input("conf-interval","n_intervals"))
def update_confederations(_):
    from data.elo import get_all_wc_elos, get_confederation_stats

    all_elos = get_all_wc_elos()
    conf_stats = get_confederation_stats()

    # ── Confederation bar chart ──────────────────────────────────────
    confs = sorted(conf_stats.keys(), key=lambda c: conf_stats[c]["avg_elo"], reverse=True)
    fig_conf = go.Figure(go.Bar(
        x=[CONF_NAMES.get(c,c) for c in confs],
        y=[conf_stats[c]["avg_elo"] for c in confs],
        marker_color=[CONF_COLORS.get(c, COLORS["accent"]) for c in confs],
        marker_line_width=0,
        text=[f"{conf_stats[c]['avg_elo']}" for c in confs],
        textposition="inside",
        textfont=dict(size=12,color=COLORS["text_primary"]),
        customdata=[conf_stats[c]["count"] for c in confs],
        hovertemplate="<b>%{x}</b><br>Avg Elo: %{y}<br>%{customdata} teams<extra></extra>",
    ))
    fig_conf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=8,b=0), height=320, showlegend=False,
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=COLORS["text_secondary"])),
        yaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,
                  title=dict(text="Average Elo Rating",font=dict(size=11,color=COLORS["text_secondary"]))),
        bargap=0.35,
    )

    # ── Top 15 Elo ranking ────────────────────────────────────────────
    top15 = all_elos[:15]
    fig_top = go.Figure(go.Bar(
        y=[t["team"] for t in reversed(top15)],
        x=[t["elo"] for t in reversed(top15)],
        orientation="h",
        marker_color=[CONF_COLORS.get(t["confederation"], COLORS["accent"]) for t in reversed(top15)],
        marker_line_width=0,
        text=[t["elo"] for t in reversed(top15)],
        textposition="inside",
        textfont=dict(size=11,color=COLORS["text_primary"]),
    ))
    fig_top.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=40,t=8,b=0), height=440,
        xaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11,color=COLORS["text_primary"])),
        bargap=0.25,
    )

    # ── Confederation cards ───────────────────────────────────────────
    conf_cards = []
    for c in confs:
        d = conf_stats[c]
        color = CONF_COLORS.get(c, COLORS["accent"])
        conf_cards.append(html.Div([
            html.Div(CONF_NAMES.get(c,c), style={"fontSize":"13px","fontWeight":"700","color":color,"marginBottom":"8px"}),
            html.Div([
                html.Div([
                    html.Div(str(d["count"]), style={"fontSize":"22px","fontWeight":"800","color":COLORS["text_primary"]}),
                    html.Div("Teams", style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase"}),
                ], style={"textAlign":"center"}),
                html.Div([
                    html.Div(str(d["avg_elo"]), style={"fontSize":"22px","fontWeight":"800","color":color}),
                    html.Div("Avg Elo", style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase"}),
                ], style={"textAlign":"center"}),
                html.Div([
                    html.Div(str(d["max_elo"]), style={"fontSize":"22px","fontWeight":"800","color":COLORS["gold"]}),
                    html.Div("Best", style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase"}),
                ], style={"textAlign":"center"}),
            ], style={"display":"flex","gap":"16px","justifyContent":"space-around"}),
        ], className="glow-card", style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                  "borderLeft":f"3px solid {color}","borderRadius":"12px","padding":"16px","flex":"1","minWidth":"220px"}))

    # ── Full Elo table ─────────────────────────────────────────────────
    table_rows = []
    for i, t in enumerate(all_elos, 1):
        color = CONF_COLORS.get(t["confederation"], COLORS["text_secondary"])
        table_rows.append(html.Div([
            html.Span(f"#{i}", style={"width":"36px","fontSize":"12px","color":COLORS["text_secondary"]}),
            get_flag_img(t["team"], width=20),
            html.Span(t["team"], style={"flex":"1","fontSize":"13px","color":COLORS["text_primary"],"marginLeft":"8px"}),
            html.Span(t["confederation"], style={"fontSize":"10px","color":color,"backgroundColor":color+"22","padding":"2px 8px","borderRadius":"4px","marginRight":"12px"}),
            html.Span(str(t["elo"]), style={"fontSize":"14px","fontWeight":"700","color":COLORS["accent"],"minWidth":"50px","textAlign":"right"}),
        ], style={"display":"flex","alignItems":"center","padding":"7px 4px","borderBottom":f"1px solid {COLORS['border']}"}))

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Confederation Strength (Avg Elo)", style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                dcc.Graph(figure=fig_conf, config={"displayModeBar":False}),
            ], style={"flex":"1","minWidth":"320px","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px","marginBottom":"20px"}),
        ]),

        html.Div(conf_cards, style={"display":"flex","gap":"16px","flexWrap":"wrap","marginBottom":"24px"}),

        html.Div([
            html.Div([
                html.Div("Top 15 by Elo Rating", style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                dcc.Graph(figure=fig_top, config={"displayModeBar":False}),
            ], style={"flex":"1.2","minWidth":"320px","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),

            html.Div([
                html.Div("All 48 Teams — Full Elo Ranking", style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                html.Div(table_rows, style={"maxHeight":"440px","overflowY":"auto"}),
            ], style={"flex":"1","minWidth":"280px","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
        ], style={"display":"flex","gap":"20px","flexWrap":"wrap"}),

        html.Div("Elo ratings sourced live from eloratings.net · Updates automatically after every match result · Cached 1 hour",
                 style={"fontSize":"11px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"16px"}),
    ])
