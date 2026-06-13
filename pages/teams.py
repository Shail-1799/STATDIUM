from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper, stat_pill
from data.fetcher import WC2026_GROUPS, get_flag, get_cache, FIFA_RANKINGS

def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    opts = [{"label":f"{get_flag(t)} {t}","value":t} for t in all_teams]
    return html.Div([
        page_wrapper([
            section_header("Team Explorer","Head-to-head comparison · Radar · Form guide",
                           accent_color=COLORS["accent3"]),
            html.Div([
                html.Div([
                    html.Div("Team A",style={"fontSize":"11px","color":COLORS["accent"],"marginBottom":"6px","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.08em"}),
                    dcc.Dropdown(id="team-a", options=opts, value="Brazil", clearable=False),
                ], style={"flex":"1"}),
                html.Div("VS",style={"fontSize":"28px","fontWeight":"800","color":COLORS["text_secondary"],
                                     "alignSelf":"flex-end","paddingBottom":"4px","minWidth":"40px","textAlign":"center"}),
                html.Div([
                    html.Div("Team B",style={"fontSize":"11px","color":COLORS["accent2"],"marginBottom":"6px","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.08em"}),
                    dcc.Dropdown(id="team-b", options=opts, value="France", clearable=False),
                ], style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","alignItems":"flex-end",
                      "backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                      "borderRadius":"12px","padding":"20px","marginBottom":"24px"}),
            html.Div(id="team-comparison-content"),
        ]),
    ])

def _get_team_stats(team, group_table):
    for grp in group_table.values():
        if team in grp:
            t = grp[team]
            return {"pts":t.get("pts",0),"w":t.get("w",0),"d":t.get("d",0),"l":t.get("l",0),
                    "gf":t.get("gf",0),"ga":t.get("ga",0),"gd":t.get("gf",0)-t.get("ga",0),"p":t.get("p",0)}
    return {"pts":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"gd":0,"p":0}

def _get_group(team):
    for letter, teams in WC2026_GROUPS.items():
        if team in teams: return letter
    return "?"

@app.callback(Output("team-comparison-content","children"),
              Input("team-a","value"), Input("team-b","value"))
def update_comparison(team_a, team_b):
    if not team_a or not team_b:
        return html.Div()
    group_table = get_cache().get("groups",{})
    sa = _get_team_stats(team_a, group_table)
    sb = _get_team_stats(team_b, group_table)
    ra = FIFA_RANKINGS.get(team_a, 60)
    rb = FIFA_RANKINGS.get(team_b, 60)
    ga = _get_group(team_a)
    gb = _get_group(team_b)

    categories = ["FIFA Rank (inv)","Points","Goals For","Goal Diff","Wins","Defense"]
    def rvals(stats, rank):
        return [max(0,(100-rank)/100*10), min(10,stats["pts"]),
                min(10,stats["gf"]), min(10,max(0,stats["gd"]+5)),
                min(10,stats["w"]*3), min(10,max(0,(stats["p"]-stats["ga"])*2))]

    va = rvals(sa, ra); vb = rvals(sb, rb)
    fig_radar = go.Figure()
    for vals, name, color in [(va,team_a,COLORS["accent"]),(vb,team_b,COLORS["accent2"])]:
        fig_radar.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=categories+[categories[0]],
            fill="toself", name=name,
            line=dict(color=color,width=2), fillcolor="rgba(0,229,160,0.2)" if color==COLORS["accent"] else "rgba(123,97,255,0.2)",
        ))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True,range=[0,10],gridcolor=COLORS["border"],
                                   linecolor=COLORS["border"],tickfont=dict(size=9,color=COLORS["text_secondary"])),
                   angularaxis=dict(gridcolor=COLORS["border"],linecolor=COLORS["border"],
                                    tickfont=dict(size=10,color=COLORS["text_secondary"]))),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=40,r=40,t=40,b=40), height=380,
        legend=dict(font=dict(size=12,color=COLORS["text_primary"]),bgcolor="rgba(0,0,0,0)"),
    )

    stat_keys = ["pts","w","gf","ga"]
    stat_names = ["Points","Wins","Goals For","Goals Against"]
    fig_bars = go.Figure()
    for stats, name, color in [(sa,team_a,COLORS["accent"]),(sb,team_b,COLORS["accent2"])]:
        fig_bars.add_bar(name=name, x=stat_names, y=[stats[k] for k in stat_keys],
                         marker_color=color, marker_line_width=0,
                         text=[stats[k] for k in stat_keys], textposition="outside",
                         textfont=dict(size=12,color=color))
    fig_bars.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        barmode="group", font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0,r=0,t=8,b=0), height=260,
        legend=dict(font=dict(size=12,color=COLORS["text_primary"]),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.12),
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=12,color=COLORS["text_primary"])),
        yaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,showticklabels=False),
        bargap=0.15,bargroupgap=0.05,
    )

    def team_card(team, stats, rank, group, color):
        return html.Div([
            html.Div(get_flag(team),style={"fontSize":"52px","textAlign":"center","marginBottom":"8px"}),
            html.Div(team,style={"fontSize":"20px","fontWeight":"700","color":COLORS["text_primary"],"textAlign":"center","marginBottom":"4px"}),
            html.Div([
                html.Span(f"Group {group}",style={"fontSize":"11px","fontWeight":"700","color":color,"backgroundColor":color+"20","padding":"2px 8px","borderRadius":"4px","marginRight":"8px"}),
                html.Span(f"FIFA #{rank}",style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            ], style={"textAlign":"center","marginBottom":"16px"}),
            html.Div([
                stat_pill("Points",stats["pts"],color=color),
                stat_pill("Played",stats["p"]),
                stat_pill("W-D-L",f"{stats['w']}-{stats['d']}-{stats['l']}"),
                stat_pill("GD",f"{'+' if stats['gd']>=0 else ''}{stats['gd']}",
                          color=COLORS["win_green"] if stats["gd"]>0 else (COLORS["loss_red"] if stats["gd"]<0 else COLORS["text_secondary"])),
            ], style={"display":"flex","gap":"8px","flexWrap":"wrap","justifyContent":"center"}),
        ], style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {color}44",
                  "borderTop":f"3px solid {color}","borderRadius":"12px","padding":"20px","flex":"1","minWidth":"200px"})

    return html.Div([
        html.Div([
            team_card(team_a,sa,ra,ga,COLORS["accent"]),
            html.Div("⚔️",style={"fontSize":"24px","alignSelf":"center","color":COLORS["text_secondary"],"minWidth":"30px","textAlign":"center"}),
            team_card(team_b,sb,rb,gb,COLORS["accent2"]),
        ], style={"display":"flex","gap":"12px","marginBottom":"24px","flexWrap":"wrap"}),
        html.Div([
            html.Div([
                html.Div("Performance radar",style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                dcc.Graph(figure=fig_radar, config={"displayModeBar":False}),
            ], style={"flex":"1","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
            html.Div([
                html.Div("Head-to-head stats",style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                dcc.Graph(figure=fig_bars, config={"displayModeBar":False}),
            ], style={"flex":"1","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
        ], style={"display":"flex","gap":"20px","flexWrap":"wrap"}),
    ])
