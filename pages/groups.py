from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, standings_row, page_wrapper
from data.fetcher import get_cache, WC2026_GROUPS, get_flag, FIFA_RANKINGS
import numpy as np

def layout():
    return html.Div([
        dcc.Interval(id="groups-interval", interval=30000, n_intervals=0),
        page_wrapper([html.Div(id="groups-content")]),
    ])

def _qualify_probs(teams, table_data, n_sims=2000):
    """Monte Carlo: probability each team finishes top-2 or 3rd in their group"""
    from data.fetcher import FIFA_RANKINGS
    def strength(t):
        r = FIFA_RANKINGS.get(t, 60)
        return max(0.05, 1.0 - (r-1)/90.0)

    counts = {t:{"top2":0,"third":0} for t in teams}
    for _ in range(n_sims):
        pts = {t:0 for t in teams}; gd = {t:0 for t in teams}
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                a, b = teams[i], teams[j]
                sa, sb = strength(a), strength(b)
                pa = 1/(1+10**((sb-sa)*5))
                r = np.random.random()
                if r < pa*0.65:   pts[a]+=3; gd[a]+=np.random.randint(1,4); gd[b]-=np.random.randint(0,2)
                elif r > 1-(1-pa)*0.65: pts[b]+=3; gd[b]+=np.random.randint(1,4); gd[a]-=np.random.randint(0,2)
                else: pts[a]+=1; pts[b]+=1
        ranked = sorted(teams, key=lambda t:(pts[t],gd[t]), reverse=True)
        counts[ranked[0]]["top2"]+=1; counts[ranked[1]]["top2"]+=1
        counts[ranked[2]]["third"]+=1
    return {t:{"top2":round(v["top2"]/n_sims*100,0),"third":round(v["third"]/n_sims*100,0)} for t,v in counts.items()}

def _shock_index(team, opponent):
    """Upset risk score 0-100 based on rank gap"""
    r1 = FIFA_RANKINGS.get(team, 60)
    r2 = FIFA_RANKINGS.get(opponent, 60)
    gap = r2 - r1  # positive = opponent is lower ranked (expected to lose)
    if gap <= 0: return 50 - min(40, abs(gap)*1.5)
    return min(95, 50 + gap * 1.8)

def _get_scenario_text(letter, sorted_teams, group_table):
    """Generate qualification scenario text — AI if available, else template"""
    from data.ai_insights import generate_qualification_scenario
    from utils.monte_carlo import get_qualification_status
    teams_list = [t["team"] for t in sorted_teams]
    status = get_qualification_status(letter, teams_list, group_table)
    return generate_qualification_scenario(letter, status)


def _build_group_card(letter, teams, group_table):
    group_key   = f"Group {letter}"
    table_data  = group_table.get(group_key, {})
    group_color = COLORS["group_colors"].get(letter, COLORS["accent"])
    played      = sum(t.get("p",0) for t in table_data.values())//2 if table_data else 0

    if table_data:
        sorted_teams = sorted(table_data.values(), key=lambda t:(t["pts"],t.get("gf",0)-t.get("ga",0),t.get("gf",0)), reverse=True)
        present = {t["team"] for t in sorted_teams}
        for team in teams:
            if team not in present:
                sorted_teams.append({"team":team,"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0})
    else:
        sorted_teams = [{"team":t,"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0} for t in teams]

    # Qualification probabilities
    probs = _qualify_probs(teams, table_data, n_sims=800)

    # Average strength → Group of Death?
    avg_rank = sum(FIFA_RANKINGS.get(t,60) for t in teams)/len(teams)
    is_death = avg_rank < 20

    # Points bar
    fig = go.Figure(go.Bar(
        x=[t["team"][:3].upper() for t in sorted_teams],
        y=[t["pts"] for t in sorted_teams],
        marker_color=[group_color]*len(sorted_teams), marker_line_width=0,
        text=[t["pts"] for t in sorted_teams], textposition="inside",
        textfont=dict(size=11,color=COLORS["text_primary"]),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=12,b=0), height=110, showlegend=False,
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=COLORS["text_secondary"])),
        yaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,showticklabels=False),
        bargap=0.3,
    )

    # Standing rows
    header_cells = [("#","28px"),("Team","160px"),("P","36px"),("W","36px"),
                    ("D","36px"),("L","36px"),("G","52px"),("GD","40px"),("Pts","40px")]
    rows_html = [standings_row(rank,t["team"],get_flag(t["team"]),t["p"],t["w"],t["d"],t["l"],
                               t.get("gf",0),t.get("ga",0),t["pts"],highlight=(rank<=2))
                 for rank,t in enumerate(sorted_teams,1)]

    # Qualification probability bars
    qual_rows = []
    for t in sorted_teams:
        p_top2  = probs.get(t["team"],{}).get("top2",0)
        p_third = probs.get(t["team"],{}).get("third",0)
        p_total = min(100, p_top2 + p_third*0.67)  # ~67% of 3rd place teams qualify
        bar_color = COLORS["accent"] if p_top2>=50 else (COLORS["gold"] if p_third>=30 else COLORS["text_secondary"])
        qual_rows.append(html.Div([
            html.Div(f"{get_flag(t['team'])} {t['team'][:12]}", style={"fontSize":"11px","color":COLORS["text_primary"],"minWidth":"120px"}),
            html.Div([
                html.Div(style={"width":f"{p_total}%","backgroundColor":bar_color,"height":"100%","borderRadius":"4px","transition":"width 0.8s ease"}),
            ], className="qual-bar-wrap", style={"flex":"1","height":"6px","borderRadius":"4px"}),
            html.Div(f"{p_top2:.0f}%", style={"fontSize":"10px","color":bar_color,"minWidth":"32px","textAlign":"right"}),
        ], style={"display":"flex","alignItems":"center","gap":"8px","marginBottom":"5px"}))

    header_row = html.Div(
        [html.Span(label,style={"width":w,"minWidth":w,"fontSize":"10px","color":COLORS["text_secondary"],
                                "textTransform":"uppercase","letterSpacing":"0.08em",
                                "textAlign":"center" if label!="Team" else "left","display":"inline-block"})
         for label,w in header_cells],
        style={"padding":"4px 12px 8px","display":"flex"}
    )

    return html.Div(
        [html.Div([
            html.Span(f"Group {letter}",style={"fontSize":"16px","fontWeight":"700","color":group_color}),
            html.Div([
                html.Span(className="death-badge", children=["☠ Group of Death"],
                          style={"marginRight":"8px"}) if is_death else None,
                html.Span(f"{played}/6 played",style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            ],style={"display":"flex","alignItems":"center"}),
         ],style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "marginBottom":"12px","paddingBottom":"8px","borderBottom":f"1px solid {COLORS['border']}"}),
         html.Div([header_row] + rows_html, className="standings-scroll"),
        ] + [
        html.Div([
            html.Div(style={"height":"2px","background":f"linear-gradient(90deg,{group_color}80,transparent)","marginBottom":"6px"}),
            html.Span("↑ Top 2 advance · Best 8 third-place teams also qualify",style={"fontSize":"10px","color":COLORS["text_secondary"]}),
        ],style={"marginTop":"8px","marginBottom":"14px"}),
        html.Div("Qualification probability",style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"8px"}),
        ] + qual_rows + [
        html.Div([
            html.Div("Points",style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em","marginTop":"12px","marginBottom":"4px"}),
            dcc.Graph(figure=fig,config={"displayModeBar":False}),
        ]),
        ] + [
        html.Div([
            html.Div("📝 Scenario", style={"fontSize":"10px","color":COLORS["accent2"],"textTransform":"uppercase","letterSpacing":"0.08em","marginTop":"14px","marginBottom":"6px"}),
            html.Div(_get_scenario_text(letter, sorted_teams, group_table), style={"fontSize":"12px","color":COLORS["text_secondary"],"lineHeight":"1.5"}),
        ]),
        ],
        style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
               "borderLeft":f"3px solid {group_color}","borderRadius":"12px","padding":"20px"}
    )

@app.callback(Output("groups-content","children"), Input("groups-interval","n_intervals"))
def update_groups(_):
    group_table = get_cache().get("groups",{})
    letters = list(WC2026_GROUPS.keys())
    rows = []
    for i in range(0,len(letters),2):
        pair = [html.Div(_build_group_card(l,WC2026_GROUPS[l],group_table),
                         className="stagger-item",
                         style={"flex":"1","minWidth":"340px"})
                for l in letters[i:i+2]]
        rows.append(html.Div(pair,className="group-pair stagger-container",style={"display":"flex","gap":"20px","marginBottom":"20px","flexWrap":"wrap"}))
    return html.Div([section_header("Group Stage","12 groups · 48 teams · Qualification probabilities live")] + rows)
