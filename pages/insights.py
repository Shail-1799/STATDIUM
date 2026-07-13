from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper, get_flag_img
from data.fetcher import get_cache, WC2026_GROUPS, get_flag, FIFA_RANKINGS, normalize_round

ISO3_MAP = {
    "Argentina":"ARG","Australia":"AUS","Austria":"AUT","Belgium":"BEL",
    "Bosnia & Herzegovina":"BIH","Brazil":"BRA","Canada":"CAN","Cape Verde":"CPV",
    "Colombia":"COL","Croatia":"HRV","Curaçao":"CUW","Czech Republic":"CZE",
    "DR Congo":"COD","Ecuador":"ECU","Egypt":"EGY","England":"GBR",
    "France":"FRA","Germany":"DEU","Ghana":"GHA","Haiti":"HTI","Iran":"IRN",
    "Iraq":"IRQ","Ivory Coast":"CIV","Japan":"JPN","Jordan":"JOR",
    "Mexico":"MEX","Morocco":"MAR","Netherlands":"NLD","New Zealand":"NZL",
    "Norway":"NOR","Panama":"PAN","Paraguay":"PRY","Portugal":"PRT","Qatar":"QAT",
    "Saudi Arabia":"SAU","Scotland":"GBR","Senegal":"SEN","South Africa":"ZAF",
    "South Korea":"KOR","Spain":"ESP","Sweden":"SWE","Switzerland":"CHE",
    "Tunisia":"TUN","Turkey":"TUR","USA":"USA","Ukraine":"UKR","Uruguay":"URY",
    "Uzbekistan":"UZB","Algeria":"DZA",
}

WC_WINNERS = [
    ("1930","🇺🇾","Uruguay"),("1934","🇮🇹","Italy"),("1938","🇮🇹","Italy"),
    ("1950","🇺🇾","Uruguay"),("1954","🇩🇪","W. Germany"),("1958","🇧🇷","Brazil"),
    ("1962","🇧🇷","Brazil"),("1966","🏴󠁧󠁢󠁥󠁮󠁧󠁿","England"),("1970","🇧🇷","Brazil"),
    ("1974","🇩🇪","W. Germany"),("1978","🇦🇷","Argentina"),("1982","🇮🇹","Italy"),
    ("1986","🇦🇷","Argentina"),("1990","🇩🇪","W. Germany"),("1994","🇧🇷","Brazil"),
    ("1998","🇫🇷","France"),("2002","🇧🇷","Brazil"),("2006","🇮🇹","Italy"),
    ("2010","🇪🇸","Spain"),("2014","🇩🇪","Germany"),("2018","🇫🇷","France"),
    ("2022","🇦🇷","Argentina"),
]

GUIDE = page_guide("Insights", [
    ("🌍", "World map is coloured by total goals scored — hover a country to see their stats."),
    ("📊", "Goals by Group bar chart shows which groups have been the most entertaining."),
    ("⚡", "Upset Tracker shows matches where the lower-ranked Elo team won — the bigger the gap, the bigger the shock."),
    ("🏆", "Wall of Champions: every World Cup winner since 1930 — click a card to see the year."),
], accent_color=COLORS["accent2"])

def layout():
    return html.Div([
        dcc.Interval(id="insights-interval", interval=120000, n_intervals=0),
        page_wrapper([
            GUIDE,html.Div(id="insights-content")]),
    ])

@app.callback(Output("insights-content","children"), Input("insights-interval","n_intervals"))
def update_insights(_):
    cache       = get_cache()
    matches     = cache.get("matches",[])
    scorers     = cache.get("scorers",[])
    group_table = cache.get("groups",{})
    finished    = [m for m in matches if m["status"]=="FINISHED"]
    all_teams   = [t for teams in WC2026_GROUPS.values() for t in teams]

    # World map
    map_rows = []
    for team in all_teams:
        pts,gd,gf = 0,0,0
        rank = FIFA_RANKINGS.get(team,60)
        for grp_data in group_table.values():
            if team in grp_data:
                t=grp_data[team]; pts=t.get("pts",0); gf=t.get("gf",0); gd=gf-t.get("ga",0)
                break
        iso3 = ISO3_MAP.get(team,"")
        if iso3:
            map_rows.append({"team":team,"iso3":iso3,"pts":pts,"gd":gd,"gf":gf,"rank":rank})

    fig_map = go.Figure(go.Choropleth(
        locations=[r["iso3"] for r in map_rows],
        z=[r["pts"] for r in map_rows],
        text=[f"<b>{get_flag(r['team'])} {r['team']}</b><br>Points: {r['pts']}<br>GD: {'+' if r['gd']>=0 else ''}{r['gd']}<br>Goals: {r['gf']}<br>FIFA #{r['rank']}" for r in map_rows],
        hovertemplate="%{text}<extra></extra>",
        colorscale=[[0.0,"#1E1E24"],[0.3,"rgba(123,97,255,0.4)"],[0.7,"#7B61FF"],[1.0,"#00E5A0"]],
        zmin=0,zmax=9,showscale=True,
        colorbar=dict(title=dict(text="Pts",font=dict(color=COLORS["text_secondary"])),
                      tickfont=dict(color=COLORS["text_secondary"]),bgcolor="rgba(0,0,0,0)",len=0.6),
        marker_line_color=COLORS["border"],marker_line_width=0.5,
    ))
    fig_map.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)",showframe=False,showcoastlines=True,
                 coastlinecolor=COLORS["border"],showland=True,landcolor=COLORS["bg_card2"],
                 showocean=True,oceancolor=COLORS["bg_primary"],
                 showcountries=True,countrycolor=COLORS["border"],projection_type="natural earth"),
        margin=dict(l=0,r=0,t=0,b=0),height=400,font=dict(color=COLORS["text_secondary"]),
    )

    # Goals by group
    group_goals = {}
    for m in finished:
        grp = str(m.get("group","")).replace("Group ","").strip()
        if grp:
            group_goals[grp] = group_goals.get(grp,0)+(m.get("home_score") or 0)+(m.get("away_score") or 0)

    if group_goals:
        sg = sorted(group_goals.items())
        fig_goals = go.Figure(go.Bar(
            x=[f"Grp {g}" for g,_ in sg], y=[v for _,v in sg],
            marker_color=[COLORS["group_colors"].get(g,COLORS["accent"]) for g,_ in sg],
            marker_line_width=0, text=[v for _,v in sg], textposition="inside",
            textfont=dict(size=12,color=COLORS["text_primary"]),
        ))
        fig_goals.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=8,b=0),showlegend=False,
            xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=10,color=COLORS["text_secondary"])),
            yaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,showticklabels=False),
            bargap=0.3,
            height=360
        )
        goals_widget = dcc.Graph(figure=fig_goals,config={"displayModeBar":False})
    else:
        goals_widget = html.Div("Awaiting first goals ⚽",style={"color":COLORS["text_secondary"],"padding":"20px","textAlign":"center"})

    # Upsets
    upset_html = []
    upsets = []
    for m in finished:
        h,a = m.get("home_team",""),m.get("away_team","")
        hs,as_ = m.get("home_score"),m.get("away_score")
        if hs is None or as_ is None: continue
        rh=FIFA_RANKINGS.get(h,60); ra=FIFA_RANKINGS.get(a,60)
        if hs>as_ and rh>ra+10: upsets.append((h,a,f"{hs}–{as_}",rh-ra,get_flag(h),get_flag(a)))
        elif as_>hs and ra>rh+10: upsets.append((a,h,f"{as_}–{hs}",ra-rh,get_flag(a),get_flag(h)))
    upsets.sort(key=lambda x:x[3],reverse=True)
    for winner,loser,score,gap,fw,fl in upsets[:6]:
        upset_html.append(html.Div([
            html.Span(f"{fw} {winner}",style={"fontSize":"13px","color":COLORS["accent"],"fontWeight":"600"}),
            html.Span(f" {score} ",style={"fontSize":"13px","color":COLORS["text_primary"]}),
            html.Span(f"{fl} {loser}",style={"fontSize":"13px","color":COLORS["text_secondary"]}),
            html.Div(f"⚡ Rank gap: +{gap}",style={"fontSize":"10px","color":COLORS["accent3"]}),
        ],style={"padding":"8px 0","borderBottom":f"1px solid {COLORS['border']}"}))
    if not upset_html:
        upset_html=[html.Div("No upsets detected yet",style={"color":COLORS["text_secondary"],"fontSize":"13px","padding":"16px 0"})]

    # Top scorers
    scorer_html = []
    if scorers:
        for i,s in enumerate(scorers[:10],1):
            player = s.get("player",{}).get("name","") if isinstance(s.get("player"),dict) else s.get("name","–")
            team_raw = s.get("team","–")
            team = team_raw if isinstance(team_raw,str) else team_raw.get("shortName", team_raw.get("name","–"))
            goals  = s.get("numberOfGoals", s.get("goals",0))
            medal={1:"🥇",2:"🥈",3:"🥉"}.get(i,f"{i}.")
            scorer_html.append(html.Div([
                html.Span(medal,style={"width":"32px","fontSize":"14px","display":"inline-block"}),
                html.Span(player,style={"flex":"1","fontSize":"13px","color":COLORS["text_primary"]}),
                html.Span(f"{get_flag(team)} {team}",style={"fontSize":"12px","color":COLORS["text_secondary"],"minWidth":"80px"}),
                html.Span(f"⚽ {goals}",style={"fontSize":"13px","fontWeight":"700","color":COLORS["accent"],"minWidth":"40px","textAlign":"right"}),
            ],style={"display":"flex","alignItems":"center","gap":"8px","padding":"8px 12px",
                     "backgroundColor":COLORS["bg_card2"] if i%2==0 else "transparent","borderRadius":"6px","marginBottom":"2px"}))
    else:
        scorer_html=[html.Div("Set FD_API_KEY for live scorer data (free key — see README)",style={"color":COLORS["text_secondary"],"padding":"16px","fontSize":"13px"})]

    # Wall of Champions — equal-sized cards with flag, ISO code, full name, year
    # ISO2 short code for display
    ISO2_DISPLAY = {
        "Uruguay":"UY","Italy":"IT","W. Germany":"DE","Brazil":"BR",
        "England":"EN","West Germany":"DE","Argentina":"AR","Germany":"DE",
        "France":"FR","Spain":"ES",
    }

    # Only add a 2026 entry once the Final has ACTUALLY been played — never
    # fabricate a champion. This is derived live from real match data, so
    # the Wall of Champions completes itself automatically the moment the
    # Final finishes, with no manual code edit ever needed.
    wc_winners_display = list(WC_WINNERS)
    final_matches = [m for m in matches if normalize_round(m.get("round","")) == "Final"]
    if final_matches:
        fm = final_matches[0]
        if fm.get("status") == "FINISHED" and fm.get("home_score") is not None:
            hs, as_ = fm["home_score"], fm["away_score"]
            home, away = fm.get("home_team"), fm.get("away_team")
            if hs != as_:  # a Final tied on the data we have (pre-penalties) can't declare a winner
                champion_2026 = home if hs > as_ else away
                wc_winners_display.append(("2026", get_flag(champion_2026), champion_2026))

    latest_year = wc_winners_display[-1][0]

    champions_html = []
    for year, flag, team in wc_winners_display:
        short = ISO2_DISPLAY.get(team, team[:2].upper())
        # Highlight whichever year is actually the most recent — never
        # hardcoded, so this keeps working correctly through 2026 and every
        # World Cup after it too.
        is_current = year == latest_year
        border_style = f"1px solid rgba(255,215,0,0.6)" if is_current else f"1px solid rgba(255,215,0,0.15)"
        bg_style = "rgba(255,215,0,0.08)" if is_current else "var(--card-bg)"
        champions_html.append(html.Div([
            # html.Div(flag, className="champ-flag"),
            # html.Div(short, className="champ-iso"),
            html.Span(get_flag_img(team, width=20)),
            html.Div(team, className="champ-team"),
            html.Div(year, className="champ-year"),
        ], className="champion-pill",
           style={"border":border_style,"background":bg_style}))

    return html.Div([
        section_header("Global Insights","World map · Top scorers · Upsets · Wall of Champions",accent_color=COLORS["accent2"]),

        # Map
        html.Div([
            html.Div("Participating nations — shaded by group stage points",
                     style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
            dcc.Graph(figure=fig_map,config={"displayModeBar":False,"scrollZoom":True}),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px","marginBottom":"24px"}),

        # 3-col grid
        html.Div([
            html.Div([
                html.Div("Goals by group",style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"8px"}),
                goals_widget,
            ],style={"flex":"1.2","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),

            html.Div([html.Div("Top scorers",style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"12px"})]+scorer_html,
                     style={"flex":"1.2","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),

            html.Div([html.Div("⚡ Upset tracker",style={"fontSize":"12px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"12px"})]+upset_html,
                     style={"flex":"1","backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"}),
        ],className="insights-3col",style={"display":"flex","gap":"20px","flexWrap":"wrap","marginBottom":"24px"}),

        # Wall of Champions
        html.Div([
            section_header("Wall of Champions","Every FIFA World Cup winner since 1930",accent_color=COLORS["gold"]),
            html.Div(champions_html,className="champions-grid"),
        ],style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderLeft":f"3px solid {COLORS['gold']}","borderRadius":"12px","padding":"20px"}),
    ])
