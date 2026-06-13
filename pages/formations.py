from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper
from data.fetcher import WC2026_GROUPS, get_flag, FIFA_RANKINGS

POSITIONS = {
    "4-3-3":   [[.5,.92],[.15,.75],[.38,.75],[.62,.75],[.85,.75],[.25,.52],[.5,.52],[.75,.52],[.2,.25],[.5,.18],[.8,.25]],
    "4-4-2":   [[.5,.92],[.15,.75],[.38,.75],[.62,.75],[.85,.75],[.15,.52],[.38,.52],[.62,.52],[.85,.52],[.35,.22],[.65,.22]],
    "4-2-3-1": [[.5,.92],[.15,.75],[.38,.75],[.62,.75],[.85,.75],[.33,.60],[.67,.60],[.18,.42],[.5,.38],[.82,.42],[.5,.18]],
    "3-5-2":   [[.5,.92],[.2,.78],[.5,.78],[.8,.78],[.08,.55],[.28,.52],[.5,.50],[.72,.52],[.92,.55],[.33,.22],[.67,.22]],
    "5-3-2":   [[.5,.92],[.08,.75],[.27,.75],[.5,.75],[.73,.75],[.92,.75],[.25,.52],[.5,.52],[.75,.52],[.35,.22],[.65,.22]],
}
TEAM_FORMS = {
    "Brazil":"4-3-3","France":"4-2-3-1","Argentina":"4-3-3","England":"4-3-3",
    "Spain":"4-3-3","Germany":"4-2-3-1","Portugal":"4-3-3","Netherlands":"4-3-3",
    "Belgium":"4-3-3","Japan":"4-2-3-1","USA":"4-3-3","Mexico":"4-3-3",
    "Croatia":"4-3-3","Uruguay":"4-3-3","Colombia":"4-2-3-1","Morocco":"4-3-3",
}

def get_team_color(team):
    for letter, teams in WC2026_GROUPS.items():
        if team in teams: return COLORS["group_colors"].get(letter, COLORS["accent"])
    return COLORS["accent"]

def build_pitch_html(home, away, h_form, a_form):
    hc = get_team_color(home); ac = get_team_color(away)
    hp = POSITIONS.get(h_form, POSITIONS["4-3-3"])
    ap = POSITIONS.get(a_form, POSITIONS["4-3-3"])
    W,H = 400,620; mx,my = 22,28; pw,ph = W-mx*2, H-my*2

    def px(f): return mx + f*pw
    def py(f): return my + f*ph

    ls = 'stroke="rgba(255,255,255,0.3)" stroke-width="1.4" fill="none"'
    parts = [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;border-radius:10px">',
        f'<defs><linearGradient id="pg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a5c1a"/><stop offset="50%" stop-color="#1f6e1f"/><stop offset="100%" stop-color="#1a5c1a"/></linearGradient>',
        f'<filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#pg)" rx="10"/>',
    ]
    # stripes
    for i in range(10):
        sy = my + i*ph/10
        if i%2==0: parts.append(f'<rect x="{mx}" y="{sy:.1f}" width="{pw}" height="{ph/10:.1f}" fill="rgba(255,255,255,0.025)"/>')
    # lines
    parts += [
        f'<rect x="{mx}" y="{my}" width="{pw}" height="{ph}" {ls}/>',
        f'<line x1="{mx}" y1="{py(.5):.1f}" x2="{mx+pw}" y2="{py(.5):.1f}" {ls}/>',
        f'<circle cx="{px(.5):.1f}" cy="{py(.5):.1f}" r="{pw*.12:.1f}" {ls}/>',
        f'<circle cx="{px(.5):.1f}" cy="{py(.5):.1f}" r="3" fill="rgba(255,255,255,0.5)"/>',
    ]
    # penalty areas
    paW,paH = pw*.50,ph*.13
    gbW,gbH = pw*.26,ph*.055
    parts += [
        f'<rect x="{px(.5)-paW/2:.1f}" y="{my:.1f}" width="{paW:.1f}" height="{paH:.1f}" {ls}/>',
        f'<rect x="{px(.5)-paW/2:.1f}" y="{my+ph-paH:.1f}" width="{paW:.1f}" height="{paH:.1f}" {ls}/>',
        f'<rect x="{px(.5)-gbW/2:.1f}" y="{my:.1f}" width="{gbW:.1f}" height="{gbH:.1f}" {ls}/>',
        f'<rect x="{px(.5)-gbW/2:.1f}" y="{my+ph-gbH:.1f}" width="{gbW:.1f}" height="{gbH:.1f}" {ls}/>',
        f'<circle cx="{px(.5):.1f}" cy="{my+ph*.11:.1f}" r="2.5" fill="rgba(255,255,255,0.5)"/>',
        f'<circle cx="{px(.5):.1f}" cy="{my+ph*.89:.1f}" r="2.5" fill="rgba(255,255,255,0.5)"/>',
        f'<path d="M {mx} {my+8} A 8 8 0 0 0 {mx+8} {my}" stroke="rgba(255,255,255,0.3)" stroke-width="1.4" fill="none"/>',
        f'<path d="M {mx+pw-8} {my} A 8 8 0 0 0 {mx+pw} {my+8}" stroke="rgba(255,255,255,0.3)" stroke-width="1.4" fill="none"/>',
        f'<path d="M {mx} {my+ph-8} A 8 8 0 0 0 {mx+8} {my+ph}" stroke="rgba(255,255,255,0.3)" stroke-width="1.4" fill="none"/>',
        f'<path d="M {mx+pw-8} {my+ph} A 8 8 0 0 0 {mx+pw} {my+ph-8}" stroke="rgba(255,255,255,0.3)" stroke-width="1.4" fill="none"/>',
    ]
    # players
    def draw(positions, color, flip):
        for i,pos in enumerate(positions):
            cx = px(pos[0]); cy = py(pos[1] if not flip else 1-pos[1])
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="14" fill="{color}" opacity="0.18"/>')
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="{color}" stroke="white" stroke-width="1.8" style="cursor:pointer" filter="url(#glow)"/>')
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" font-size="8" font-weight="700" fill="white" font-family="Inter,sans-serif" pointer-events="none">{i+1}</text>')
    draw(hp, hc, False)
    draw(ap, ac, True)
    # team labels
    parts += [
        f'<text x="{W/2:.0f}" y="{H-6}" text-anchor="middle" font-size="11" font-weight="700" fill="{hc}" font-family="Inter,sans-serif" opacity="0.9">{home} · {h_form}</text>',
        f'<text x="{W/2:.0f}" y="15" text-anchor="middle" font-size="11" font-weight="700" fill="{ac}" font-family="Inter,sans-serif" opacity="0.9">{away} · {a_form}</text>',
        '</svg>',
    ]
    return ''.join(parts)

def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])
    opts = [{"label":f"{get_flag(t)} {t}","value":t} for t in all_teams]
    form_opts = [{"label":f,"value":f} for f in ["4-3-3","4-4-2","4-2-3-1","3-5-2","5-3-2"]]
    return html.Div([page_wrapper([
        section_header("Formations & Shock Index","Interactive pitch · Upset danger · Group of Death",accent_color=COLORS["accent3"]),
        html.Div([
            html.Div([
                html.Div("Home Team",style={"fontSize":"11px","color":COLORS["accent"],"marginBottom":"6px","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.08em"}),
                dcc.Dropdown(id="home-team-select",options=opts,value="Brazil",clearable=False),
                html.Div("Formation",style={"fontSize":"11px","color":COLORS["text_secondary"],"marginTop":"12px","marginBottom":"6px","textTransform":"uppercase","letterSpacing":"0.08em"}),
                dcc.Dropdown(id="home-form-select",options=form_opts,value="4-3-3",clearable=False),
            ],style={"flex":"1","minWidth":"160px"}),
            html.Div("VS",style={"fontSize":"32px","fontWeight":"900","color":COLORS["text_secondary"],"alignSelf":"center","minWidth":"48px","textAlign":"center"}),
            html.Div([
                html.Div("Away Team",style={"fontSize":"11px","color":COLORS["accent2"],"marginBottom":"6px","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.08em"}),
                dcc.Dropdown(id="away-team-select",options=opts,value="France",clearable=False),
                html.Div("Formation",style={"fontSize":"11px","color":COLORS["text_secondary"],"marginTop":"12px","marginBottom":"6px","textTransform":"uppercase","letterSpacing":"0.08em"}),
                dcc.Dropdown(id="away-form-select",options=form_opts,value="4-2-3-1",clearable=False),
            ],style={"flex":"1","minWidth":"160px"}),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px","display":"flex","gap":"24px","flexWrap":"wrap","marginBottom":"24px","alignItems":"flex-start"}),
        html.Div([
            html.Div([html.Div(id="pitch-display")],
                     style={"flex":"1.2","minWidth":"300px","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"16px"}),
            html.Div([html.Div(id="shock-index-panel")],style={"flex":"1","minWidth":"260px"}),
        ],style={"display":"flex","gap":"24px","flexWrap":"wrap","marginBottom":"24px"}),
        html.Div([
            section_header("Group of Death Calculator","All 12 groups ranked by combined strength",accent_color=COLORS["live_red"]),
            html.Div(id="group-death-content"),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
    ])])

@app.callback(Output("pitch-display","children"),
              Input("home-team-select","value"),Input("away-team-select","value"),
              Input("home-form-select","value"),Input("away-form-select","value"))
def update_pitch(home,away,h_form,a_form):
    if not home or not away: return html.Div()
    svg = build_pitch_html(home,away,h_form,a_form)
    # Embed via iframe srcDoc — works in all Dash versions
    srcdoc = f"""<!DOCTYPE html><html><head>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#16161A;overflow:hidden}}</style>
</head><body>{svg}</body></html>"""
    return html.Div([
        html.Div([
            html.Span(f"{get_flag(home)} {home}",style={"fontSize":"13px","fontWeight":"700","color":get_team_color(home)}),
            html.Span(" vs ",style={"fontSize":"12px","color":COLORS["text_secondary"],"margin":"0 8px"}),
            html.Span(f"{get_flag(away)} {away}",style={"fontSize":"13px","fontWeight":"700","color":get_team_color(away)}),
        ],style={"textAlign":"center","marginBottom":"12px"}),
        html.Iframe(srcDoc=srcdoc,style={"width":"100%","height":"640px","border":"none","borderRadius":"10px","display":"block"}),
        html.Div("Numbers = shirt positions (1=GK)",style={"fontSize":"10px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"8px"}),
    ])

@app.callback(Output("shock-index-panel","children"),
              Input("home-team-select","value"),Input("away-team-select","value"))
def update_shock(home,away):
    if not home or not away: return html.Div()
    rh=FIFA_RANKINGS.get(home,60); ra=FIFA_RANKINGS.get(away,60)
    gap=abs(rh-ra)
    underdog=home if rh>ra else away
    shock=min(92,max(8,8+gap*1.8))
    if gap<=5: shock=max(20,35+(5-gap)*3)
    if shock<35: dc=COLORS["win_green"]; dl="Low Risk"; dd="Strong favourite expected to win"
    elif shock<60: dc="#FF9F0A"; dl="Medium Risk"; dd="Competitive — anything can happen"
    else: dc=COLORS["live_red"]; dl="⚡ UPSET ALERT"; dd="History loves an upset here"

    fig=go.Figure(go.Indicator(
        mode="gauge+number",value=shock,
        number=dict(suffix="%",font=dict(size=42,color=dc,family="Inter")),
        gauge=dict(axis=dict(range=[0,100],tickwidth=0,tickfont=dict(color=COLORS["text_secondary"],size=10)),
                   bar=dict(color=dc,thickness=0.25),bgcolor="rgba(0,0,0,0)",borderwidth=0,
                   steps=[dict(range=[0,35],color="rgba(48,209,88,0.1)"),
                          dict(range=[35,60],color="rgba(255,159,10,0.1)"),
                          dict(range=[60,100],color="rgba(255,59,48,0.1)")]),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color=COLORS["text_secondary"]),margin=dict(l=20,r=20,t=24,b=0),height=230)

    def sbar(team,rank,color):
        pct=max(8,round((1-rank/90)*100))
        return html.Div([
            html.Div([
                html.Span(f"{get_flag(team)} {team}",style={"fontSize":"12px","color":COLORS["text_primary"],"fontWeight":"500"}),
                html.Span(f"FIFA #{rank}",style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            ],style={"display":"flex","justifyContent":"space-between","marginBottom":"5px"}),
            html.Div(html.Div(style={"width":f"{pct}%","height":"100%","backgroundColor":color,"borderRadius":"4px","transition":"width 0.9s cubic-bezier(0.22,1,0.36,1)"}),
                     style={"backgroundColor":COLORS["bg_card2"],"borderRadius":"4px","height":"8px","marginBottom":"12px"}),
        ])

    return html.Div([
        html.Div([
            html.Div([html.Span("⚡ SHOCK INDEX",style={"fontSize":"11px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.1em"})],style={"marginBottom":"4px"}),
            html.Div(f"{get_flag(underdog)} {underdog} upset probability",style={"fontSize":"13px","color":COLORS["text_primary"],"marginBottom":"4px"}),
            dcc.Graph(figure=fig,config={"displayModeBar":False}),
            html.Div([
                html.Div(dl,style={"fontSize":"16px","fontWeight":"800","color":dc,"textAlign":"center"}),
                html.Div(dd,style={"fontSize":"12px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"4px"}),
            ],style={"marginTop":"4px"}),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {dc}55","borderTop":f"3px solid {dc}","borderRadius":"12px","padding":"20px","marginBottom":"16px"}),
        html.Div([
            html.Div("Team Strength",style={"fontSize":"11px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"14px"}),
            sbar(home,rh,get_team_color(home)),
            sbar(away,ra,get_team_color(away)),
            html.Div([
                html.Div("FIFA Rank gap",style={"fontSize":"11px","color":COLORS["text_secondary"]}),
                html.Div(f"{gap} places",style={"fontSize":"18px","fontWeight":"800","color":dc}),
            ],style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginTop":"4px","paddingTop":"12px","borderTop":f"1px solid {COLORS['border']}"}),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
    ])

@app.callback(Output("group-death-content","children"),Input("away-team-select","value"))
def update_group_death(_):
    scored=[(l,t,sum(FIFA_RANKINGS.get(x,60) for x in t)/len(t)) for l,t in WC2026_GROUPS.items()]
    scored.sort(key=lambda x:x[2])
    items=[]
    for rank,(letter,teams,avg) in enumerate(scored,1):
        gc=COLORS["group_colors"].get(letter,COLORS["accent"])
        pct=max(10,min(100,round((80-avg)/70*100)))
        items.append(html.Div([
            html.Div([
                html.Span(f"#{rank}",style={"fontSize":"14px","fontWeight":"800","color":gc,"minWidth":"30px","display":"inline-block"}),
                html.Span(f"Group {letter}",style={"fontSize":"14px","fontWeight":"700","color":COLORS["text_primary"],"minWidth":"80px","display":"inline-block"}),
                html.Span("  ".join(f"{get_flag(t)} {t}" for t in teams),style={"fontSize":"11px","color":COLORS["text_secondary"],"flex":"1"}),
                html.Span(f"avg #{avg:.0f}",style={"fontSize":"11px","color":COLORS["text_secondary"],"minWidth":"60px","textAlign":"right"}),
                html.Span("☠ Death",style={"marginLeft":"10px","fontSize":"10px","fontWeight":"700","color":COLORS["live_red"],"backgroundColor":"rgba(255,59,48,0.12)","border":"1px solid rgba(255,59,48,0.3)","padding":"2px 7px","borderRadius":"5px"}) if rank<=3 else None,
            ],style={"display":"flex","alignItems":"center","gap":"8px","marginBottom":"6px","flexWrap":"wrap"}),
            html.Div(html.Div(style={"width":f"{pct}%","height":"100%","backgroundColor":gc,"borderRadius":"3px"}),
                     style={"backgroundColor":COLORS["bg_card2"],"borderRadius":"3px","height":"5px","marginBottom":"14px"}),
        ]))
    return html.Div(items)
