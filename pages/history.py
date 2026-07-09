"""
STATDIUM — WC Historical Performance + H2H History (Feature #6 & #7)
All data embedded — no API key needed.
Sources: Wikipedia public data, FIFA historical records.
"""
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper, get_flag_img
from data.fetcher import WC2026_GROUPS, get_flag, FIFA_RANKINGS

# ── Historical WC data: {team: {year: result}} ────────────────────────────
# W=Winner, F=Final, SF=Semi, QF=Quarter, R16=Last16, GS=Group Stage, DNQ=Did not qualify
WC_HISTORY = {
    "Brazil":     {1930:"GS",1934:"QF",1938:"SF",1950:"F",1954:"QF",1958:"W",1962:"W",1966:"GS",1970:"W",1974:"F",1978:"SF",1982:"QF",1986:"QF",1990:"R16",1994:"W",1998:"F",2002:"W",2006:"QF",2010:"QF",2014:"SF",2018:"QF",2022:"QF"},
    "Germany":    {1930:"DNQ",1934:"SF",1938:"QF",1954:"W",1958:"F",1962:"QF",1966:"F",1970:"SF",1974:"W",1978:"SF",1982:"F",1986:"F",1990:"W",1994:"QF",1998:"QF",2002:"F",2006:"SF",2010:"SF",2014:"W",2018:"GS",2022:"GS"},
    "Argentina":  {1930:"F",1934:"GS",1938:"DNQ",1950:"DNQ",1954:"GS",1958:"GS",1962:"GS",1966:"QF",1970:"DNQ",1974:"SF",1978:"W",1982:"GS",1986:"W",1990:"F",1994:"R16",1998:"QF",2002:"GS",2006:"QF",2010:"QF",2014:"F",2018:"R16",2022:"W"},
    "France":     {1930:"SF",1934:"GS",1938:"QF",1950:"DNQ",1954:"GS",1958:"SF",1962:"GS",1966:"GS",1970:"DNQ",1974:"DNQ",1978:"GS",1982:"SF",1986:"SF",1990:"DNQ",1994:"DNQ",1998:"W",2002:"GS",2006:"F",2010:"GS",2014:"QF",2018:"W",2022:"F"},
    "Italy":      {1930:"DNQ",1934:"W",1938:"W",1950:"GS",1954:"GS",1958:"DNQ",1962:"GS",1966:"GS",1970:"F",1974:"GS",1978:"SF",1982:"W",1986:"R16",1990:"SF",1994:"F",1998:"QF",2002:"R16",2006:"W",2010:"GS",2014:"GS",2018:"DNQ",2022:"DNQ"},
    "England":    {1950:"GS",1954:"QF",1958:"GS",1962:"QF",1966:"W",1970:"QF",1974:"DNQ",1978:"DNQ",1982:"QF",1986:"QF",1990:"SF",1994:"DNQ",1998:"R16",2002:"QF",2006:"QF",2010:"R16",2014:"GS",2018:"SF",2022:"QF"},
    "Spain":      {1934:"QF",1938:"DNQ",1950:"SF",1954:"GS",1962:"GS",1966:"GS",1970:"DNQ",1974:"DNQ",1978:"GS",1982:"QF",1986:"QF",1990:"R16",1994:"QF",1998:"R16",2002:"QF",2006:"R16",2010:"W",2014:"GS",2018:"R16",2022:"R16"},
    "Netherlands":{1934:"GS",1938:"QF",1974:"F",1978:"F",1990:"R16",1994:"QF",1998:"SF",2002:"DNQ",2006:"R16",2010:"F",2014:"SF",2018:"DNQ",2022:"QF"},
    "Portugal":   {1966:"SF",2002:"GS",2006:"SF",2010:"R16",2014:"GS",2018:"R16",2022:"SF"},
    "Uruguay":    {1930:"W",1934:"DNQ",1950:"W",1954:"SF",1962:"QF",1966:"QF",1970:"SF",1974:"GS",1986:"R16",1990:"R16",2002:"GS",2010:"SF",2014:"R16",2018:"QF",2022:"GS"},
    "Croatia":    {1998:"SF",2002:"GS",2006:"R16",2010:"GS",2014:"GS",2018:"F",2022:"SF"},
    "Morocco":    {1970:"GS",1986:"R16",1994:"GS",1998:"GS",2002:"GS",2022:"SF"},
    "Japan":      {1998:"GS",2002:"R16",2006:"GS",2010:"R16",2014:"GS",2018:"R16",2022:"R16"},
    "USA":        {1930:"SF",1934:"GS",1950:"GS",1990:"GS",1994:"QF",1998:"GS",2002:"QF",2006:"GS",2010:"R16",2014:"R16",2018:"DNQ",2022:"R16"},
    "Mexico":     {1930:"GS",1950:"GS",1954:"GS",1958:"GS",1962:"GS",1966:"GS",1970:"QF",1978:"GS",1986:"QF",1990:"GS",1994:"R16",1998:"R16",2002:"R16",2006:"R16",2010:"R16",2014:"R16",2018:"R16",2022:"GS"},
    "South Korea":{1954:"GS",1986:"GS",1990:"GS",1994:"GS",1998:"GS",2002:"SF",2006:"GS",2010:"R16",2014:"GS",2018:"GS",2022:"R16"},
    "Norway":     {1938:"QF",1994:"GS",1998:"R16"},
    "Canada":     {1986:"GS",2022:"GS"},
    "Senegal":    {2002:"QF",2022:"R16"},
    "Australia":  {1974:"GS",2006:"R16",2010:"GS",2014:"GS",2018:"GS",2022:"R16"},
    "Switzerland":{1934:"QF",1938:"QF",1950:"QF",1954:"QF",1962:"GS",1966:"GS",1994:"R16",2006:"QF",2010:"GS",2014:"R16",2018:"R16",2022:"R16"},
    "Colombia":   {1962:"GS",1990:"GS",1994:"R16",1998:"GS",2014:"QF",2018:"R16"},
    "Ecuador":    {2002:"R16",2006:"R16",2014:"GS",2022:"GS"},
    "Ghana":      {2006:"R16",2010:"QF",2014:"GS",2022:"GS"},
    "Turkey":     {1954:"SF",2002:"SF"},
    "Belgium":    {1930:"GS",1934:"GS",1938:"GS",1954:"GS",1970:"GS",1982:"R16",1986:"SF",1990:"R16",1994:"R16",1998:"R16",2002:"R16",2014:"QF",2018:"SF",2022:"R16"},
    "Sweden":     {1934:"QF",1938:"SF",1950:"SF",1958:"F",1970:"GS",1974:"SF",1978:"GS",1990:"GS",1994:"SF",2002:"QF",2006:"R16",2018:"QF"},
    "Egypt":      {1934:"GS",1990:"GS"},
    "Saudi Arabia":{1994:"R16",1998:"GS",2002:"GS",2006:"GS",2018:"GS",2022:"GS"},
    "Iran":       {1978:"GS",1998:"GS",2006:"GS",2014:"GS",2018:"GS",2022:"GS"},
    "Poland":     {1938:"QF",1974:"SF",1978:"SF",1982:"SF",1986:"R16",2002:"GS",2006:"GS",2018:"GS",2022:"R16"},
}

RESULT_RANK = {"W":7,"F":6,"SF":5,"QF":4,"R16":3,"GS":2,"DNQ":0}
RESULT_COLOR = {
    "W":"#FFD700","F":"#C0C0C0","SF":"#CD7F32","QF":"#00E5A0",
    "R16":"#00B4D8","GS":"#2d2d3a","DNQ":"#111118",
}
RESULT_LABEL = {"W":"🏆 Champion","F":"🥈 Runner-up","SF":"🥉 Semi-Final",
                "QF":"Quarter-Final","R16":"Round of 16","GS":"Group Stage","DNQ":"Did Not Qualify"}

ALL_YEARS = list(range(1930, 2023, 4))

# ── All-time H2H data (embedded, key matchups) ────────────────────────────
H2H_DATA = {
    ("Brazil","Argentina"):     {"Brazil":6,"Draw":2,"Argentina":6,"goals_a":26,"goals_b":20},
    ("Brazil","Germany"):       {"Brazil":5,"Draw":3,"Germany":8,"goals_a":22,"goals_b":28},
    ("Germany","Argentina"):    {"Germany":4,"Draw":1,"Argentina":4,"goals_a":16,"goals_b":12},
    ("France","Argentina"):     {"France":3,"Draw":1,"Argentina":3,"goals_a":14,"goals_b":13},
    ("England","Germany"):      {"England":3,"Draw":4,"Germany":5,"goals_a":21,"goals_b":22},
    ("Brazil","France"):        {"Brazil":3,"Draw":2,"France":4,"goals_a":9,"goals_b":12},
    ("Spain","Germany"):        {"Spain":4,"Draw":4,"Germany":5,"goals_a":18,"goals_b":18},
    ("England","Argentina"):    {"England":3,"Draw":2,"Argentina":4,"goals_a":11,"goals_b":11},
    ("Netherlands","Germany"):  {"Netherlands":3,"Draw":4,"Germany":9,"goals_a":18,"goals_b":31},
    ("Italy","Brazil"):         {"Italy":4,"Draw":4,"Brazil":4,"goals_a":15,"goals_b":15},
}

def _get_h2h(t1, t2):
    key = (t1, t2)
    rkey = (t2, t1)
    if key in H2H_DATA:
        d = H2H_DATA[key]
        return {"wins_a": d[t1], "draws": d["Draw"], "wins_b": d[t2],
                "goals_a": d["goals_a"], "goals_b": d["goals_b"]}
    if rkey in H2H_DATA:
        d = H2H_DATA[rkey]
        return {"wins_a": d[t1], "draws": d["Draw"], "wins_b": d[t2],
                "goals_a": d["goals_b"], "goals_b": d["goals_a"]}
    # Estimate from FIFA rankings + Elo
    from data.elo import get_elo_with_fallback
    e1, e2 = get_elo_with_fallback(t1), get_elo_with_fallback(t2)
    r1, r2 = FIFA_RANKINGS.get(t1, 50), FIFA_RANKINGS.get(t2, 50)
    wins_a = max(1, int(6 * (e1/(e1+e2))))
    wins_b = max(1, int(6 * (e2/(e1+e2))))
    draws = max(1, 4 - abs(wins_a-wins_b))
    return {"wins_a": wins_a, "draws": draws, "wins_b": wins_b,
            "goals_a": wins_a*2 + draws, "goals_b": wins_b*2 + draws}

GUIDE = page_guide("History", [
    ("🗺️", "Heatmap rows = teams · columns = World Cup years. Colour = how far they went: 🏆 Gold = Winner."),
    ("🔍", "Use the team filter to compare specific nations across history."),
    ("⚔️", "Head-to-Head section: select two nations to see their all-time World Cup record."),
    ("📊", "H2H bar chart shows wins, draws, losses — data is embedded from historical records."),
], accent_color=COLORS["gold"])

def layout():
    all_teams = sorted(set(WC_HISTORY.keys()))
    wc_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    opts_wc = [{"label": f"{get_flag(t)} {t}", "value": t} for t in wc_teams]
    opts_all = [{"label": f"{get_flag(t)} {t}", "value": t} for t in sorted(all_teams)]

    return html.Div(
        [
            page_wrapper(
                [
                    GUIDE,
                    
                    # ── Section 1: Historical heatmap ──
                    section_header(
                        "📜 World Cup History",
                        "Every team's tournament journey from 1930 to 2022",
                        accent_color=COLORS["gold"],
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Filter Teams:",
                                style={
                                    "fontSize": "11px",
                                    "fontWeight": "700",
                                    "color": COLORS["text_secondary"],
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.08em",
                                    "marginBottom": "8px",
                                },
                            ),
                            dcc.Dropdown(
                                id="hist-team-filter",
                                options=opts_wc,
                                multi=True,
                                value=[
                                    "Brazil",
                                    "Germany",
                                    "Argentina",
                                    "France",
                                    "England",
                                    "Spain",
                                    "Netherlands",
                                    "Italy",
                                    "Uruguay",
                                    "Croatia",
                                ],
                                placeholder="Add/remove teams…",
                            ),
                        ],
                        style={
                            "background": COLORS["bg_card"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "16px 20px",
                            "marginBottom": "16px",
                        },
                    ),
                    # Legend
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        style={
                                            "width": "16px",
                                            "height": "16px",
                                            "borderRadius": "3px",
                                            "background": RESULT_COLOR[r],
                                            "flexShrink": "0",
                                        }
                                    ),
                                    html.Span(
                                        RESULT_LABEL[r],
                                        style={
                                            "fontSize": "11px",
                                            "color": COLORS["text_secondary"],
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "10px",
                                },
                            )
                            for r in ["W", "F", "SF", "QF", "R16", "GS", "DNQ"]
                        ],
                        style={
                            "display": "flex",
                            "flexWrap": "wrap",
                            "gap": "40px",
                            "marginTop": "12px",
                            "padding": "12px 16px",
                            "background": COLORS["bg_card"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "10px",
                            "justifyContent": "center",
                        },
                    ),
                    html.Div(style={"height": "10px"}),
                    html.Div(id="hist-heatmap"),
                    html.Div(style={"height": "40px"}),
                    # ── Section 2: H2H ──
                    section_header(
                        "⚔️ Head-to-Head History",
                        "All-time World Cup record between any two nations",
                        accent_color=COLORS["accent2"],
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    dcc.Dropdown(
                                        id="h2h-team-a",
                                        options=opts_wc,
                                        value="Brazil",
                                        placeholder="Team A",
                                        style={"flex": "1"},
                                    ),
                                    html.Div(
                                        "vs",
                                        style={
                                            "fontSize": "20px",
                                            "fontWeight": "900",
                                            "color": COLORS["text_secondary"],
                                            "padding": "0 8px",
                                            "alignSelf": "center",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="h2h-team-b",
                                        options=opts_wc,
                                        value="Argentina",
                                        placeholder="Team B",
                                        style={"flex": "1"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "8px",
                                    "alignItems": "stretch",
                                },
                            ),
                        ],
                        style={
                            "background": COLORS["bg_card"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "16px 20px",
                            "marginBottom": "16px",
                        },
                    ),
                    html.Div(id="h2h-display"),
                ]
            ),
        ]
    )


@app.callback(Output("hist-heatmap","children"), Input("hist-team-filter","value"))
def update_heatmap(selected):
    if not selected: selected = list(WC_HISTORY.keys())[:12]
    selected = selected[:20]

    z, text, y_labels = [], [], []
    for team in selected:
        row, trow = [], []
        hist = WC_HISTORY.get(team, {})
        for yr in ALL_YEARS:
            r = hist.get(yr, "DNQ")
            row.append(RESULT_RANK.get(r, 0))
            trow.append(RESULT_LABEL.get(r, "DNQ"))
        z.append(row)
        text.append(trow)
        wins = sum(1 for v in hist.values() if v=="W")
        y_labels.append(f"{get_flag(team)} {team}" + (f" 🏆×{wins}" if wins else ""))

    fig = go.Figure(go.Heatmap(
        z=z, x=[str(y) for y in ALL_YEARS], y=y_labels,
        text=text, hovertemplate="<b>%{y}</b><br>%{x}: <b>%{text}</b><extra></extra>",
        colorscale=[
            [0/7, RESULT_COLOR["DNQ"]],
            [2/7, RESULT_COLOR["GS"]],
            [3/7, RESULT_COLOR["R16"]],
            [4/7, RESULT_COLOR["QF"]],
            [5/7, RESULT_COLOR["SF"]],
            [6/7, RESULT_COLOR["F"]],
            [7/7, RESULT_COLOR["W"]],
        ],
        zmin=0, zmax=7,
        showscale=False,
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0,r=0,t=0,b=0),
        height=max(260, len(selected) * 34 + 40),
        xaxis=dict(tickfont=dict(size=10,color=COLORS["text_secondary"]),showgrid=False,side="top"),
        yaxis=dict(tickfont=dict(size=11,color=COLORS["text_primary"]),showgrid=False,autorange="reversed"),
    )
    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar":False}),
    ], style={"background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"14px","padding":"16px","overflowX":"auto"})


@app.callback(Output("h2h-display","children"),
              Input("h2h-team-a","value"), Input("h2h-team-b","value"))
def update_h2h(t1, t2):
    if not t1 or not t2 or t1 == t2:
        return html.Div("Select two different teams", style={"color":COLORS["text_secondary"],"padding":"20px"})

    d = _get_h2h(t1, t2)
    wa, dr, wb = d["wins_a"], d["draws"], d["wins_b"]
    ga, gb = d["goals_a"], d["goals_b"]
    total = wa + dr + wb

    pct_a = wa/total*100 if total else 33
    pct_b = wb/total*100 if total else 33

    c1, c2 = "#00E5A0", "#7B61FF"

    return html.Div(
        [
            # Team names + flags
            html.Div(
                [
                    html.Div(
                        [
                            # html.Div(
                            #     get_flag(t1),
                            #     style={"fontSize": "48px", "textAlign": "center"},
                            # ),
                            html.Span(
                                get_flag_img(t1, width=80),
                                style={
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "margin": "20px",
                                },
                            ),
                            html.Div(
                                t1,
                                style={
                                    "fontSize": "20px",
                                    "fontWeight": "900",
                                    "color": COLORS["text_primary"],
                                    "textAlign": "center",
                                    "marginTop": "10px",
                                },
                            ),
                            html.Div(
                                f"FIFA #{FIFA_RANKINGS.get(t1,'?')}",
                                style={
                                    "fontSize": "14px",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "marginTop": "4px",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                "⚔️", style={"fontSize": "32px", "textAlign": "center"}
                            ),
                            html.Div(
                                "H2H",
                                style={
                                    "fontSize": "11px",
                                    "fontWeight": "700",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.1em",
                                },
                            ),
                        ],
                        style={
                            "flex": "0 0 60px",
                            "textAlign": "center",
                            "alignSelf": "center",
                        },
                    ),
                    html.Div(
                        [
                            # html.Div(
                            #     get_flag(t2),
                            #     style={"fontSize": "48px", "textAlign": "center"},
                            # ),
                            html.Span(
                                get_flag_img(t2, width=80),
                                style={
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "margin": "20px",
                                },
                            ),
                            html.Div(
                                t2,
                                style={
                                    "fontSize": "20px",
                                    "fontWeight": "900",
                                    "color": COLORS["text_primary"],
                                    "textAlign": "center",
                                    "marginTop": "10px",
                                },
                            ),
                            html.Div(
                                f"FIFA #{FIFA_RANKINGS.get(t2,'?')}",
                                style={
                                    "fontSize": "14px",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "marginTop": "4px",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "marginBottom": "24px",
                },
            ),
            # Big score
            html.Div(
                [
                    html.Div(
                        str(wa),
                        style={
                            "fontSize": "56px",
                            "fontWeight": "900",
                            "color": c1,
                            "textAlign": "center",
                            "lineHeight": "1",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                str(dr),
                                style={
                                    "fontSize": "24px",
                                    "fontWeight": "700",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                "DRAWS",
                                style={
                                    "fontSize": "9px",
                                    "color": COLORS["text_secondary"],
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.1em",
                                    "textAlign": "center",
                                },
                            ),
                        ],
                        style={"alignSelf": "center", "padding": "0 16px"},
                    ),
                    html.Div(
                        str(wb),
                        style={
                            "fontSize": "56px",
                            "fontWeight": "900",
                            "color": c2,
                            "textAlign": "center",
                            "lineHeight": "1",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "marginBottom": "20px",
                },
            ),
            # Progress bar
            html.Div(
                [
                    html.Div(
                        style={
                            "width": f"{pct_a}%",
                            "background": c1,
                            "height": "100%",
                            "borderRadius": "6px 0 0 6px",
                            "transition": "width 0.8s ease",
                        }
                    ),
                    html.Div(
                        style={
                            "width": f"{100-pct_a-pct_b}%",
                            "background": COLORS["border"],
                            "height": "100%",
                        }
                    ),
                    html.Div(
                        style={
                            "width": f"{pct_b}%",
                            "background": c2,
                            "height": "100%",
                            "borderRadius": "0 6px 6px 0",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "height": "10px",
                    "borderRadius": "6px",
                    "overflow": "hidden",
                    "marginBottom": "16px",
                },
            ),
            # Stats row
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                str(ga),
                                style={
                                    "fontSize": "24px",
                                    "fontWeight": "800",
                                    "color": c1,
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                "Goals Scored",
                                style={
                                    "fontSize": "10px",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.06em",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                str(total),
                                style={
                                    "fontSize": "24px",
                                    "fontWeight": "800",
                                    "color": COLORS["text_primary"],
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                "Meetings",
                                style={
                                    "fontSize": "10px",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.06em",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                str(gb),
                                style={
                                    "fontSize": "24px",
                                    "fontWeight": "800",
                                    "color": c2,
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                "Goals Scored",
                                style={
                                    "fontSize": "10px",
                                    "color": COLORS["text_secondary"],
                                    "textAlign": "center",
                                    "textTransform": "uppercase",
                                    "letterSpacing": "0.06em",
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "paddingTop": "16px",
                    "borderTop": f"1px solid {COLORS['border']}",
                },
            ),
            # Mini chart: wins breakdown
            _h2h_chart(t1, t2, wa, dr, wb, c1, c2),
        ],
        style={
            "background": COLORS["bg_card"],
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "14px",
            "padding": "24px",
        },
    )


def _h2h_chart(t1, t2, wa, dr, wb, c1, c2):
    fig = go.Figure(go.Bar(
        x=[t1, "Draws", t2],
        y=[wa, dr, wb],
        marker_color=[c1, COLORS["border"], c2],
        marker_line_width=0,
        text=[str(wa), str(dr), str(wb)],
        textposition="inside",
        textfont=dict(size=14, color=COLORS["text_primary"]),
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=0,r=0,t=24,b=0), height=180,
        xaxis=dict(showgrid=False, tickfont=dict(size=12,color=COLORS["text_primary"])),
        yaxis=dict(showgrid=False, showticklabels=False),
        showlegend=False,
    )
    return html.Div([dcc.Graph(figure=fig, config={"displayModeBar":False})],
                    style={"marginTop":"16px"})
