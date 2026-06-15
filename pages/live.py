from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from app_instance import app
from components.ui import COLORS, section_header, match_scorecard, stat_pill, page_wrapper, goal_ticker
from data.fetcher import get_today_matches, get_recent_matches, get_upcoming_matches, get_cache, get_matches, WC2026_GROUPS, FIFA_RANKINGS, get_flag
from datetime import datetime, timezone
from collections import defaultdict

def layout():
    return html.Div([
        dcc.Interval(id="live-interval", interval=60000, n_intervals=0),
        html.Div(id="goal-ticker-bar"),
        page_wrapper([
            html.Div(id="favorite-tracker", style={"marginBottom":"16px"}),
            html.Div(id="live-stats-bar", style={"marginBottom":"24px"}),
            html.Div([
                html.Div([
                    html.Div(id="today-matches"),
                    html.Div(id="recent-matches", style={"marginTop":"24px"}),
                ], style={"flex":"1.2","minWidth":"300px"}),
                html.Div([
                    html.Div(id="upcoming-matches"),
                    html.Div(id="matches-timeline", style={"marginTop":"24px"}),
                ], style={"flex":"1","minWidth":"280px"}),
            ], style={"display":"flex","gap":"24px","flexWrap":"wrap"}),
            html.Div(id="full-match-timeline", style={"marginTop":"32px"}),
        ]),
    ])

@app.callback(Output("favorite-tracker","children"), Input("favorite-team-store","data"), Input("live-interval","n_intervals"))
def update_favorite_tracker(fav_data, _):
    fav = (fav_data or {}).get("team")
    if not fav:
        return html.Div()

    all_matches = get_cache()["matches"]
    team_matches = [m for m in all_matches if m["home_team"]==fav or m["away_team"]==fav]
    if not team_matches:
        return html.Div()

    # Find next scheduled or live match, else most recent finished
    next_match = None
    for m in team_matches:
        if m["status"] in ("LIVE","SCHEDULED"):
            next_match = m; break
    if not next_match:
        finished = [m for m in team_matches if m["status"]=="FINISHED"]
        next_match = sorted(finished, key=lambda x:x["date"], reverse=True)[0] if finished else None
    if not next_match:
        return html.Div()

    return html.Div([
        html.Div([
            html.Span("⭐ ", style={"fontSize":"14px"}),
            html.Span(f"Following {get_flag(fav)} {fav}", style={"fontSize":"12px","fontWeight":"700","color":COLORS["gold"]}),
            html.Span(" — next up:" if next_match["status"]!="FINISHED" else " — last result:",
                      style={"fontSize":"12px","color":COLORS["text_secondary"],"marginLeft":"6px"}),
        ], style={"marginBottom":"8px"}),
        match_scorecard(next_match),
    ], className="glow-card", style={"backgroundColor":"rgba(255,215,0,0.05)","border":f"1px solid {COLORS['gold']}33",
              "borderRadius":"12px","padding":"16px"})


@app.callback(Output("goal-ticker-bar","children"), Input("live-interval","n_intervals"))
def update_ticker(_):
    matches = get_cache()["matches"]
    return goal_ticker(matches)

@app.callback(Output("live-stats-bar","children"), Input("live-interval","n_intervals"))
def update_stats_bar(_):
    cache = get_cache()
    matches = cache["matches"]
    finished  = [m for m in matches if m["status"]=="FINISHED"]
    live_now  = [m for m in matches if m["status"]=="LIVE"]
    scheduled = [m for m in matches if m["status"]=="SCHEDULED"]
    total_goals = sum((m.get("home_score") or 0)+(m.get("away_score") or 0) for m in finished)
    avg_goals   = round(total_goals/max(1,len(finished)),2)
    lu = cache.get("last_updated","–")
    try: lu = datetime.fromisoformat(lu).strftime("%H:%M UTC")
    except: pass

    return html.Div([
        stat_pill("Total Matches", len(matches)),
        stat_pill("Played",        len(finished)),
        stat_pill("Live Now",      len(live_now), color=COLORS["live_red"] if live_now else None),
        stat_pill("Upcoming",      len(scheduled)),
        stat_pill("Total Goals",   total_goals),
        stat_pill("Avg Goals/Match", avg_goals),
        html.Div([
            html.Div("Last sync", style={"fontSize":"10px","color":COLORS["text_secondary"],"textTransform":"uppercase","letterSpacing":"0.08em"}),
            html.Div(lu, style={"fontSize":"13px","color":COLORS["accent"]}),
        ], className="stat-pill"),
    ], className="stat-pills-row", style={"display":"flex","gap":"12px","flexWrap":"wrap","alignItems":"stretch"})

@app.callback(Output("today-matches","children"), Input("live-interval","n_intervals"))
def update_today(_):
    live_now  = get_matches(status="LIVE")
    today     = get_today_matches()
    seen      = {m["id"] for m in live_now}
    all_today = live_now + [m for m in today if m["id"] not in seen]
    if not all_today:
        recent = get_recent_matches(5)
        cards  = [match_scorecard(m) for m in recent] if recent else [
            html.Div([
                html.Div("⚽", style={"fontSize":"48px","textAlign":"center","marginBottom":"12px"}),
                html.Div("Tournament underway!", style={"fontSize":"16px","fontWeight":"700","color":COLORS["text_primary"],"textAlign":"center"}),
                html.Div("First match: Mexico vs South Africa · Jun 11", style={"fontSize":"13px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"6px"}),
            ], style={"padding":"32px 20px"})
        ]
        return html.Div([section_header("Recent Results","Latest completed matches")] + cards)
    return html.Div([section_header("Today's Matches", f"{len(all_today)} match{'es' if len(all_today)!=1 else ''} today")]
                    + [match_scorecard(m) for m in all_today])

@app.callback(Output("recent-matches","children"), Input("live-interval","n_intervals"))
def update_recent(_):
    recent = get_recent_matches(6)
    if not recent: return html.Div()
    return html.Div([section_header("Recent Results","Last completed matches")]
                    + [match_scorecard(m) for m in recent])

@app.callback(Output("upcoming-matches","children"), Input("live-interval","n_intervals"))
def update_upcoming(_):
    upcoming = get_upcoming_matches(8)
    if not upcoming:
        return html.Div([section_header("Coming Up","Next fixtures",accent_color=COLORS["accent2"]),
                         html.Div("All matches completed", style={"color":COLORS["text_secondary"],"padding":"20px"})])

    cards = []
    for i, m in enumerate(upcoming):
        cards.append(match_scorecard(m))
        if i == 0:
            cards.append(_build_ai_preview(m))
    return html.Div([section_header("Coming Up","Next fixtures",accent_color=COLORS["accent2"])] + cards)


def _build_ai_preview(match):
    """Render AI/template preview for next match"""
    from data.ai_insights import generate_match_preview, ai_enabled
    from data.fetcher import FIFA_RANKINGS, get_cache
    home, away = match["home_team"], match["away_team"]
    h_rank = FIFA_RANKINGS.get(home, 60)
    a_rank = FIFA_RANKINGS.get(away, 60)
    gap = abs(h_rank - a_rank)
    shock = min(92, max(8, 8+gap*1.8))
    if gap <= 5: shock = max(20, 35+(5-gap)*3)

    group_table = get_cache().get("groups", {})
    def form(team):
        for g in group_table.values():
            if team in g: return g[team]
        return {"pts":0,"gf":0,"ga":0}

    text = generate_match_preview(home, away, h_rank, a_rank, form(home), form(away), shock, match_id=match["id"])
    badge = "🤖 AI Preview" if ai_enabled() else "📋 Preview"

    return html.Div([
        html.Div(badge, style={"fontSize":"10px","fontWeight":"700","color":COLORS["accent2"],
                               "textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"6px"}),
        html.Div(text, style={"fontSize":"13px","color":COLORS["text_secondary"],"lineHeight":"1.6"}),
    ], className="glow-card", style={"backgroundColor":COLORS["bg_card2"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"10px","padding":"14px 16px","marginBottom":"16px","marginTop":"-4px"})

@app.callback(Output("matches-timeline","children"), Input("live-interval","n_intervals"))
def update_timeline(_):
    daily_goals = defaultdict(int); daily_matches = defaultdict(int)
    for m in get_cache()["matches"]:
        if m["status"]=="FINISHED":
            daily_goals[m.get("date","")[:10]]   += (m.get("home_score") or 0)+(m.get("away_score") or 0)
            daily_matches[m.get("date","")[:10]] += 1
    dates = sorted(daily_goals.keys())
    if not dates: return html.Div()
    goals_list = [daily_goals[d] for d in dates]
    avg_list   = [round(daily_goals[d]/max(1,daily_matches[d]),1) for d in dates]
    fig = go.Figure()
    fig.add_bar(x=dates, y=goals_list, name="Total Goals", marker_color=COLORS["accent"], marker_line_width=0, opacity=0.85)
    fig.add_scatter(x=dates, y=avg_list, name="Avg/match", mode="lines+markers",
                    line=dict(color=COLORS["accent3"],width=2), marker=dict(size=6,color=COLORS["accent3"]), yaxis="y2")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"],size=11),
        margin=dict(l=0,r=0,t=8,b=0), height=220, showlegend=True,
        legend=dict(orientation="h",x=0,y=1.15,font=dict(size=10),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(size=9,color=COLORS["text_secondary"])),
        yaxis=dict(showgrid=True,gridcolor=COLORS["border"],zeroline=False,tickfont=dict(size=9)),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,zeroline=False,tickfont=dict(size=9,color=COLORS["accent3"])),
        bargap=0.3,
    )
    return html.Div([
        section_header("Goals Timeline","Per match day",accent_color=COLORS["accent3"]),
        dcc.Graph(figure=fig, config={"displayModeBar":False}),
    ])

@app.callback(Output("full-match-timeline","children"), Input("live-interval","n_intervals"))
def update_full_timeline(_):
    """Horizontal scrollable match timeline grouped by date"""
    matches = get_cache()["matches"]
    by_date = defaultdict(list)
    for m in matches:
        by_date[m.get("date","unknown")].append(m)
    dates = sorted(by_date.keys())[:20]  # first 20 days
    if not dates: return html.Div()

    date_cols = []
    for d in dates:
        day_matches = by_date[d]
        try:
            label = datetime.strptime(d, "%Y-%m-%d").strftime("%b %d")
        except:
            label = d
        finished_count = sum(1 for m in day_matches if m["status"]=="FINISHED")
        date_cols.append(html.Div([
            html.Div(label, style={"fontSize":"11px","fontWeight":"700","color":COLORS["accent"],"textAlign":"center","marginBottom":"8px","textTransform":"uppercase","letterSpacing":"0.06em"}),
            html.Div(f"{finished_count}/{len(day_matches)}", style={"fontSize":"10px","color":COLORS["text_secondary"],"textAlign":"center","marginBottom":"10px"}),
        ] + [
            html.Div([
                html.Span(m["home_flag"], style={"fontSize":"14px"}),
                html.Span(
                    f" {m.get('home_score','')}–{m.get('away_score','')}" if m["status"]=="FINISHED" else " vs",
                    style={"fontSize":"11px","fontWeight":"600","color":COLORS["text_primary"],"margin":"0 4px"}
                ),
                html.Span(m["away_flag"], style={"fontSize":"14px"}),
            ], className="timeline-match")
            for m in day_matches
        ], style={"minWidth":"130px"})
        )

    return html.Div([
        section_header("Match Timeline","All 104 fixtures — scroll →",accent_color=COLORS["accent2"]),
        html.Div(date_cols, className="timeline-scroll", style={
            "display":"flex","gap":"12px","overflowX":"auto","paddingBottom":"12px",
            "scrollbarWidth":"thin",
        }),
    ], style={"backgroundColor":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}","borderRadius":"12px","padding":"20px"})
