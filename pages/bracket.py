from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper
from data.fetcher import WC2026_GROUPS, get_flag

def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    team_opts = [{"label": f"{get_flag(t)} {t}", "value": t} for t in all_teams]
    return html.Div([
        dcc.Store(id="sim-results-store"),
        page_wrapper([
            section_header("Bracket Simulator","10,000 Monte Carlo simulations — live win probabilities",
                           accent_color=COLORS["accent2"]),
            html.Div([
                html.Div([
                    html.Div("Simulations", style={"fontSize":"11px","color":COLORS["text_secondary"],
                             "marginBottom":"6px","textTransform":"uppercase","letterSpacing":"0.08em"}),
                    dcc.Slider(id="sim-count", min=1000, max=10000, step=1000, value=5000,
                               marks={i:{"label":f"{i//1000}k","style":{"color":COLORS["text_secondary"],"fontSize":"11px"}}
                                      for i in range(1000,11000,1000)},
                               tooltip={"placement":"top"}),
                ], style={"flex":"2","minWidth":"200px"}),
                html.Div([
                    html.Div("Focus team", style={"fontSize":"11px","color":COLORS["text_secondary"],
                             "marginBottom":"6px","textTransform":"uppercase","letterSpacing":"0.08em"}),
                    dcc.Dropdown(id="focus-team", options=team_opts, value="Argentina", clearable=False),
                ], style={"flex":"1","minWidth":"160px"}),
                html.Div([
                    html.Button("⚡ Run Simulation", id="run-sim-btn", style={
                        "backgroundColor":COLORS["accent"],"color":"#000","border":"none",
                        "borderRadius":"10px","padding":"12px 28px","fontSize":"14px",
                        "fontWeight":"700","cursor":"pointer","width":"100%",
                        "marginTop":"22px","letterSpacing":"0.02em",
                    }),
                ], style={"flex":"1","minWidth":"160px"}),
            ], style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                      "borderRadius":"12px","padding":"20px","display":"flex","gap":"24px",
                      "flexWrap":"wrap","marginBottom":"24px"}),
            dcc.Loading(id="sim-loading", type="circle", color=COLORS["accent"],
                        children=html.Div(id="sim-results-panel")),
            html.Div(id="path-to-glory", style={"marginTop":"24px"}),
        ]),
    ])

@app.callback(
    Output("sim-results-store","data"),
    Output("sim-results-panel","children"),
    Input("run-sim-btn","n_clicks"),
    State("sim-count","value"),
    prevent_initial_call=True,
)
def run_simulation(n_clicks, n_sims):
    if not n_clicks:
        return {}, html.Div()
    from utils.monte_carlo import run_simulation as _run
    results = _run(n_sims or 5000)
    top_teams = sorted(results.items(), key=lambda x: x[1]["winner"], reverse=True)[:16]
    stages = ["r32","qf","sf","final","winner"]
    stage_labels = ["Round of 32","Quarter-finals","Semi-finals","Final","Champion"]

    team_names = [f"{get_flag(t)} {t}" for t,_ in top_teams]
    z_data     = [[v[s] for s in stages] for _,v in top_teams]

    fig_heat = go.Figure(go.Heatmap(
        z=z_data, x=stage_labels, y=team_names,
        colorscale=[[0.0,"#1E1E24"],[0.3,"rgba(123,97,255,0.3)"],[0.6,"rgba(255,107,53,0.7)"],[1.0,"#00E5A0"]],
        text=[[f"{v:.1f}%" for v in row] for row in z_data],
        texttemplate="%{text}", textfont=dict(size=11,color=COLORS["text_primary"]),
        showscale=True,
        colorbar=dict(title=dict(text="%",font=dict(color=COLORS["text_secondary"])),
                      tickfont=dict(color=COLORS["text_secondary"]),bgcolor="rgba(0,0,0,0)"),
        hovertemplate="<b>%{y}</b><br>%{x}: <b>%{z:.1f}%</b><extra></extra>",
    ))
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"],size=12),
        margin=dict(l=0,r=60,t=12,b=0), height=520,
        xaxis=dict(tickfont=dict(size=11,color=COLORS["text_secondary"]),side="top"),
        yaxis=dict(tickfont=dict(size=11,color=COLORS["text_primary"]),autorange="reversed"),
    )

    champ = sorted(top_teams, key=lambda x: x[1]["winner"], reverse=True)
    bar_colors = [COLORS["gold"] if i==0 else COLORS["accent"] if i<=2 else COLORS["accent2"]
                  for i in range(len(champ))]
    fig_champ = go.Figure(go.Bar(
        y=[f"{get_flag(t)} {t}" for t,_ in champ],
        x=[v["winner"] for _,v in champ],
        orientation="h", marker_color=bar_colors, marker_line_width=0,
        text=[f"{v['winner']:.1f}%" for _,v in champ],
        textposition="inside", textfont=dict(size=11,color=COLORS["text_primary"]),
        hovertemplate="<b>%{y}</b><br>Win probability: <b>%{x:.1f}%</b><extra></extra>",
    ))
    fig_champ.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0,r=60,t=8,b=0), height=420,
        xaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,
                   ticksuffix="%",tickfont=dict(size=10,color=COLORS["text_secondary"])),
        yaxis=dict(tickfont=dict(size=12,color=COLORS["text_primary"]),autorange="reversed"),
        bargap=0.3,
    )
    return (
        results,
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Championship probability",style={"fontSize":"13px","fontWeight":"600","color":COLORS["text_secondary"],"marginBottom":"8px","textTransform":"uppercase","letterSpacing":"0.06em"}),
                    dcc.Graph(figure=fig_champ, config={"displayModeBar":False}),
                ], style={"flex":"1","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
                html.Div([
                    html.Div("Stage-by-stage probability heatmap",style={"fontSize":"13px","fontWeight":"600","color":COLORS["text_secondary"],"marginBottom":"8px","textTransform":"uppercase","letterSpacing":"0.06em"}),
                    dcc.Graph(figure=fig_heat, config={"displayModeBar":False}),
                ], style={"flex":"1.5","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
            ], style={"display":"flex","gap":"20px","flexWrap":"wrap"}),
            html.Div(f"Based on {n_sims:,} Monte Carlo simulations · Strength = 60% FIFA ranking + 40% group form",
                     style={"fontSize":"11px","color":COLORS["text_secondary"],"marginTop":"12px","textAlign":"center"}),
        ])
    )

@app.callback(
    Output("path-to-glory","children"),
    Input("sim-results-store","data"),
    State("focus-team","value"),
    prevent_initial_call=True,
)
def update_path(results, team):
    if not results or not team:
        return html.Div()
    td = results.get(team, {})
    if not td:
        return html.Div()
    stages = ["r32","qf","sf","final","winner"]
    labels = ["Round of 32","Quarter-finals","Semi-finals","Final","🏆 Champion"]
    probs  = [td.get(s,0) for s in stages]
    stage_colors = [COLORS["text_secondary"],COLORS["accent2"],COLORS["accent3"],COLORS["gold"],COLORS["accent"]]

    fig = go.Figure(go.Funnel(
        y=labels, x=probs,
        textinfo="value+percent initial",
        textfont=dict(size=13,color=COLORS["text_primary"]),
        marker=dict(color=stage_colors, line=dict(width=0)),
        connector=dict(line=dict(color=COLORS["border"],width=1,dash="dot"),fillcolor=COLORS["bg_card2"]),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0,r=0,t=8,b=0), height=320, showlegend=False,
        yaxis=dict(tickfont=dict(size=12,color=COLORS["text_primary"])),
        xaxis=dict(ticksuffix="%",tickfont=dict(size=11,color=COLORS["text_secondary"]),
                   showgrid=True,gridcolor=COLORS["border"]),
    )
    strength = td.get("strength",0)
    bar_items = []
    for i, label in enumerate(labels):
        bar_items.append(html.Div([
            html.Div(label,style={"fontSize":"12px","color":COLORS["text_secondary"],"marginBottom":"4px"}),
            html.Div(html.Div(style={"height":"6px","width":f"{min(100,probs[i])}%",
                                     "backgroundColor":stage_colors[i],"borderRadius":"3px"}),
                     style={"backgroundColor":COLORS["bg_card2"],"borderRadius":"3px","height":"6px","marginBottom":"2px"}),
            html.Div(f"{probs[i]:.1f}%",style={"fontSize":"12px","color":COLORS["accent"],"textAlign":"right"}),
        ], style={"marginBottom":"14px"}))

    return html.Div([
        section_header(f"Path to Glory — {get_flag(team)} {team}",
                       f"Strength index: {strength:.0f}/100", accent_color=COLORS["gold"]),
        html.Div([
            html.Div([
                dcc.Graph(figure=fig, config={"displayModeBar":False}),
            ], style={"flex":"1.5","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                      "borderLeft":f"3px solid {COLORS['gold']}","borderRadius":"12px","padding":"20px"}),
            html.Div([
                html.Div(get_flag(team),style={"fontSize":"64px","textAlign":"center","marginBottom":"12px"}),
                html.Div(team,style={"fontSize":"20px","fontWeight":"700","color":COLORS["text_primary"],"textAlign":"center","marginBottom":"20px"}),
            ] + bar_items,
            style={"flex":"1","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"24px"}),
        ], style={"display":"flex","gap":"20px","flexWrap":"wrap"}),
    ])
