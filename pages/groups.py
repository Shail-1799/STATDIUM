from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import page_guide, COLORS, section_header, standings_row, page_wrapper
from data.fetcher import get_cache, WC2026_GROUPS, get_flag, FIFA_RANKINGS
import numpy as np

GUIDE = page_guide("Groups", [
    ("📊", "All 12 groups shown with live standings — updates every 30 seconds as matches finish."),
    ("🟢", "Green left border = qualifying position (top 2 advance to Round of 32)."),
    ("🔴", "Red left border = elimination zone (bottom 2 when all group matches played)."),
    ("📈", "While the group is still in progress: qualification-chance bars from live Monte Carlo simulation."),
    ("✅", "Once a group finishes all 6 matches: probability bars are replaced by the final Advanced/Eliminated result — no more guessing once it's decided."),
], accent_color=COLORS["accent"])

def layout():
    return html.Div([
        dcc.Interval(id="groups-interval", interval=30000, n_intervals=0),
        page_wrapper([
            GUIDE,html.Div(id="groups-content")]),
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
    """Generate qualification scenario text from live standings."""
    if not sorted_teams:
        return f"Group {letter} standings updating…"
    leader = sorted_teams[0]["team"]
    second = sorted_teams[1]["team"] if len(sorted_teams) > 1 else "TBD"
    third  = sorted_teams[2]["team"] if len(sorted_teams) > 2 else "TBD"
    l_pts  = sorted_teams[0].get("pts", 0)
    s_pts  = sorted_teams[1].get("pts", 0) if len(sorted_teams) > 1 else 0
    gap    = l_pts - s_pts
    if gap >= 4:
        return (f"🟢 {leader} look set to top Group {letter} with a {gap}-point cushion. "
                f"{second} hold the runners-up spot — {third} need a result to stay alive.")
    elif gap <= 1:
        return (f"🔥 Group {letter} is wide open! {leader} and {second} are level or separated by {gap} pt. "
                f"Every match decides who advances — {third} still have a mathematical shot.")
    else:
        return (f"⚡ {leader} lead Group {letter} by {gap} pts. {second} occupy the qualification spot "
                f"but {third} are breathing down their necks — must-win matches ahead.")


def _get_final_scenario_text(letter, sorted_teams, qualified_teams):
    """Group is fully finished — state what actually happened, not what
    might happen. No probabilities, no 'must-win', it's already decided."""
    advanced = [t["team"] for t in sorted_teams if t["team"] in qualified_teams]
    if not advanced:
        return f"Group {letter} — final standings locked in."
    if len(advanced) == 1:
        adv_text = advanced[0]
    elif len(advanced) == 2:
        adv_text = f"{advanced[0]} and {advanced[1]}"
    else:
        adv_text = ", ".join(advanced[:-1]) + f", and {advanced[-1]}"
    return f"✅ Group {letter} complete — {adv_text} advanced to the knockout stage."


def _build_group_card(letter, teams, group_table, all_complete=False, qualified_teams=None):
    qualified_teams = qualified_teams or set()
    group_key   = f"Group {letter}"
    table_data  = group_table.get(group_key, {})
    group_color = COLORS["group_colors"].get(letter, COLORS["accent"])
    played      = sum(t.get("p",0) for t in table_data.values())//2 if table_data else 0
    # Gate on the GLOBAL all_complete flag, not this group's own played
    # count: a group finishing its 6 matches early can't correctly declare
    # its 3rd-place team eliminated until every other group has ALSO
    # finished — otherwise the best-8-thirds comparison isn't fair yet.
    group_done  = all_complete

    if table_data:
        sorted_teams = sorted(table_data.values(), key=lambda t:(t["pts"],t.get("gf",0)-t.get("ga",0),t.get("gf",0)), reverse=True)
        present = {t["team"] for t in sorted_teams}
        for team in teams:
            if team not in present:
                sorted_teams.append({"team":team,"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0})
    else:
        sorted_teams = [{"team":t,"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0} for t in teams]

    # Qualification probabilities — only meaningful while the group is
    # actually still in progress. Once it's finished, running a Monte Carlo
    # sim to estimate the "chance" of something that's already 100% decided
    # is exactly the kind of stale-relevance issue worth never showing again.
    probs = {} if group_done else _qualify_probs(teams, table_data, n_sims=800)

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

    rows_html = [
        standings_row(
            rank,
            t["team"],
            get_flag(t["team"]),
            t["p"],
            t["w"],
            t["d"],
            t["l"],
            t.get("gf", 0),
            t.get("ga", 0),
            t["pts"],
            qualify=(t["team"] in qualified_teams) if group_done else (rank <= 2),
        )
        for rank, t in enumerate(sorted_teams, 1)
    ]

    # Qualification status — probability bars while in progress, a plain
    # factual Advanced/Eliminated readout once the group is actually done.
    # No more percentages for something that's already 100% decided.
    if group_done:
        qual_rows = []
        for t in sorted_teams:
            advanced = t["team"] in qualified_teams
            qual_rows.append(html.Div([
                html.Div(f"{get_flag(t['team'])} {t['team'][:14]}", style={"fontSize":"11px","color":COLORS["text_primary"],"minWidth":"140px"}),
                html.Div("✅ Advanced" if advanced else "Eliminated",
                         style={"fontSize":"11px","fontWeight":"700",
                                "color": COLORS["accent"] if advanced else COLORS["text_secondary"]}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"6px"}))
    else:
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

    # Header — mirrors standings_row flex layout exactly
    
    header_row = html.Div(
        [
            html.Span(
                "", style={"width": "28px", "flexShrink": "0"}
            ),  # rank badge spacer
            html.Span(
                "TEAM",
                style={
                    "flex": "1",
                    "fontSize": "9px",
                    "fontWeight": "700",
                    "color": COLORS["text_dim"],
                    "textTransform": "uppercase",
                    "letterSpacing": "0.1em",
                    "paddingLeft": "6px",
                },
            ),
            *[
                html.Span(
                    lbl,
                    style={
                        "width": "28px",
                        "flexShrink": "0",
                        "fontSize": "9px",
                        "fontWeight": "700",
                        "color": COLORS["text_dim"],
                        "textAlign": "center",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.1em",
                    },
                )
                for lbl in ["P", "W", "D", "L"]
            ],
            html.Span(
                "GF:GA",
                style={
                    "width": "44px",
                    "flexShrink": "0",
                    "fontSize": "9px",
                    "fontWeight": "700",
                    "color": COLORS["text_dim"],
                    "textAlign": "center",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                },
            ),
            html.Span(
                "GD",
                style={
                    "width": "30px",
                    "flexShrink": "0",
                    "fontSize": "9px",
                    "fontWeight": "700",
                    "color": COLORS["text_dim"],
                    "textAlign": "center",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.1em",
                },
            ),
            html.Span(
                "PTS",
                style={
                    "width": "30px",
                    "flexShrink": "0",
                    "fontSize": "9px",
                    "fontWeight": "700",
                    "color": COLORS["text_dim"],
                    "textAlign": "center",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.1em",
                },
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "padding": "4px 10px 8px",
            "borderBottom": f"1px solid {COLORS['border']}",
            "marginBottom": "2px",
        },
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
        html.Div("Final Result" if group_done else "Qualification probability",style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"8px"}),
        ] + qual_rows + [
        html.Div([
            html.Div("Points",style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em","marginTop":"12px","marginBottom":"4px"}),
            dcc.Graph(figure=fig,config={"displayModeBar":False}),
        ]),
        ] + [
        html.Div([
            html.Div("📝 Scenario" if not group_done else "✅ Result", style={"fontSize":"10px","color":COLORS["accent2"],"textTransform":"uppercase","letterSpacing":"0.08em","marginTop":"14px","marginBottom":"6px"}),
            html.Div(
                _get_final_scenario_text(letter, sorted_teams, qualified_teams) if group_done
                else _get_scenario_text(letter, sorted_teams, group_table),
                style={"fontSize":"12px","color":COLORS["text_secondary"],"lineHeight":"1.5"}),
        ]),
        ],
        style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
               "borderLeft":f"3px solid {group_color}","borderRadius":"12px","padding":"20px"}
    )

@app.callback(Output("groups-content","children"), Input("groups-interval","n_intervals"))
def update_groups(_):
    group_table = get_cache().get("groups",{})
    letters = list(WC2026_GROUPS.keys())

    # Determine real qualification state — top 2 per group are locked in
    # the moment their group finishes; the best-8-third-place rule can only
    # be resolved once EVERY group has finished (otherwise you'd be
    # comparing a group that's played 6/6 against one that's only played
    # 3/6, which isn't a fair "best of" comparison yet).
    all_complete = True
    qualified_teams = set()
    third_place_candidates = []
    for letter in letters:
        table_data = group_table.get(f"Group {letter}", {})
        teams = WC2026_GROUPS[letter]
        played = sum(t.get("p", 0) for t in table_data.values()) // 2 if table_data else 0
        if played < 6:
            all_complete = False
        sorted_teams = sorted(table_data.values(), key=lambda t: (t["pts"], t.get("gf", 0) - t.get("ga", 0), t.get("gf", 0)), reverse=True) if table_data else []
        present = {t["team"] for t in sorted_teams}
        for team in teams:
            if team not in present:
                sorted_teams.append({"team": team, "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0})
        if len(sorted_teams) >= 2:
            qualified_teams.add(sorted_teams[0]["team"])
            qualified_teams.add(sorted_teams[1]["team"])
        if len(sorted_teams) >= 3:
            third_place_candidates.append(sorted_teams[2])

    if all_complete and third_place_candidates:
        best_thirds = sorted(
            third_place_candidates,
            key=lambda t: (t.get("pts", 0), t.get("gf", 0) - t.get("ga", 0), t.get("gf", 0)),
            reverse=True,
        )
        for t in best_thirds[:8]:
            qualified_teams.add(t["team"])

    rows = []
    for i in range(0,len(letters),2):
        pair = [html.Div(_build_group_card(l, WC2026_GROUPS[l], group_table, all_complete, qualified_teams),
                         style={"flex":"1","minWidth":"340px"})
                for l in letters[i:i+2]]
        rows.append(html.Div(pair,className="group-pair",style={"display":"flex","gap":"20px","marginBottom":"20px","flexWrap":"wrap"}))
    return html.Div([section_header("Group Stage","12 groups · 48 teams · Qualification probabilities live")] + rows)
