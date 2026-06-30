from dash import html, dcc

COLORS = {
    "bg_primary":"#0A0A0F","bg_card":"#16161A","bg_card2":"#1E1E24",
    "accent":"#00E5A0","accent2":"#7B61FF","accent3":"#FF6B35",
    "gold":"#FFD700","text_primary":"#F0F0F5","text_secondary":"#8A8A9A",
    "border":"#2A2A38","live_red":"#FF3B30","win_green":"#30D158",
    "draw_gray":"#636366","loss_red":"#FF453A",
    "group_colors":{"A":"#00E5A0","B":"#7B61FF","C":"#FF6B35","D":"#FFD700",
                    "E":"#00B4D8","F":"#FF6B9D","G":"#C77DFF","H":"#06D6A0",
                    "I":"#FFB703","J":"#FB8500","K":"#E63946","L":"#457B9D"},
}

def page_wrapper(children):
    return html.Div(children, className="page-wrapper-inner",
                    style={"position":"relative","zIndex":"1"})

def section_header(title, subtitle=None, accent_color=None):
    color = accent_color or COLORS["accent"]
    return html.Div([
        html.Div(className="section-hdr-bar",
                 style={"backgroundColor":color,"width":"4px","height":"28px",
                        "borderRadius":"2px","marginRight":"12px","flexShrink":"0"}),
        html.Div([
            html.Div(title, className="section-hdr-title"),
            html.Div(subtitle, className="section-hdr-sub") if subtitle else None,
        ]),
    ], className="section-hdr")

def stat_pill(label, value, color=None):
    val_str = str(value)
    try:
        num = float(val_str) if val_str.replace(".","",1).lstrip("+-").isdigit() else None
    except: num = None
    return html.Div([
        html.Div(val_str,
                 className="stat-pill-value countup-num" if num is not None else "stat-pill-value",
                 **{"data-target": str(num)} if num is not None else {},
                 style={"color": color or COLORS["accent"]}),
        html.Div(label, className="stat-pill-label"),
    ], className="stat-pill glow-card")

def live_badge():
    return html.Span([html.Span(className="live-dot"), "LIVE"],
                     style={"backgroundColor":COLORS["live_red"],"color":"#fff",
                            "fontSize":"10px","fontWeight":"700","padding":"2px 8px",
                            "borderRadius":"4px","letterSpacing":"0.1em",
                            "display":"inline-flex","alignItems":"center"})

def match_scorecard(match):
    status = match.get("status","SCHEDULED")
    is_live = status=="LIVE"; is_fin = status=="FINISHED"
    h = match.get("home_score"); a = match.get("away_score")
    score_str = f"{h}  –  {a}" if (is_fin or is_live) and h is not None else "vs"
    gl = str(match.get("group","")).replace("Group ","").strip()
    gc = COLORS["group_colors"].get(gl, COLORS["accent"])
    cls = "match-card glow-card live-glow-card" if is_live else "match-card glow-card"
    
    card_content = html.Div([
        html.Div([
            html.Span(match.get("group",""),
                      style={"fontSize":"10px","fontWeight":"700","color":gc,
                             "textTransform":"uppercase","letterSpacing":"0.1em"}),
            live_badge() if is_live else html.Span(status, style={"fontSize":"10px","color":COLORS["text_secondary"]}),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"12px"}),
        html.Div([
            html.Div([
                html.Div(match.get("home_flag",""), style={"fontSize":"clamp(20px,5vw,28px)"}),
                html.Div(match.get("home_team",""),
                         style={"fontSize":"clamp(9px,2vw,11px)","fontWeight":"600",
                                "color":COLORS["text_primary"],"textAlign":"center",
                                "marginTop":"4px","maxWidth":"80px","wordBreak":"break-word"}),
            ], style={"textAlign":"center","flex":"1"}),
            html.Div(score_str,
                     style={"fontSize":"clamp(16px,4vw,22px)" if (is_fin or is_live) else "clamp(13px,3vw,16px)",
                            "fontWeight":"700","minWidth":"70px","textAlign":"center",
                            "fontVariantNumeric":"tabular-nums",
                            "color":COLORS["live_red"] if is_live else (COLORS["text_primary"] if is_fin else COLORS["text_secondary"])}),
            html.Div([
                html.Div(match.get("away_flag",""), style={"fontSize":"clamp(20px,5vw,28px)"}),
                html.Div(match.get("away_team",""),
                         style={"fontSize":"clamp(9px,2vw,11px)","fontWeight":"600",
                                "color":COLORS["text_primary"],"textAlign":"center",
                                "marginTop":"4px","maxWidth":"80px","wordBreak":"break-word"}),
            ], style={"textAlign":"center","flex":"1"}),
        ], style={"display":"flex","alignItems":"center","justifyContent":"space-between"}),
        html.Div([
            html.Span(match.get("date",""),
                      style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            html.Span(f" · {match.get('venue','')[:22]}" if match.get("venue") else "",
                      style={"fontSize":"11px","color":COLORS["text_secondary"]}),
        ], style={"marginTop":"10px","textAlign":"center"}),
    ], className=cls)

    return dcc.Link(
        card_content,
        href=f"/match/{match.get('id','')}",
        className="match-card-link"
    )


def standings_row(rank, team, flag, p, w, d, l, gf, ga, pts, highlight=False):
    gd = gf - ga
    cells = [
        (str(rank),"24px",COLORS["text_secondary"],"center"),
        (f"{flag} {team[:12]}","140px",COLORS["text_primary"],"left"),
        (str(p),"28px",COLORS["text_secondary"],"center"),
        (str(w),"28px",COLORS["win_green"],"center"),
        (str(d),"28px",COLORS["draw_gray"],"center"),
        (str(l),"28px",COLORS["loss_red"],"center"),
        (f"{gf}:{ga}","44px",COLORS["text_secondary"],"center"),
        (f"{'+' if gd>=0 else ''}{gd}","36px",
         COLORS["win_green"] if gd>0 else (COLORS["loss_red"] if gd<0 else COLORS["text_secondary"]),"center"),
        (str(pts),"32px",COLORS["accent"] if highlight else COLORS["text_primary"],"center"),
    ]
    return html.Div(
        [html.Span(t, style={"width":w,"minWidth":w,"color":c,"textAlign":a,
                             "fontSize":"12px","fontWeight":"500" if highlight else "400",
                             "display":"inline-block","flexShrink":"0"})
         for t,w,c,a in cells],
        className="standings-row highlight" if highlight else "standings-row",
        style={"backgroundColor":"rgba(0,229,160,0.06)" if highlight else "transparent",
               "overflowX":"hidden"}
    )

def goal_ticker(matches):
    items = []
    for m in matches:
        if m.get("status")=="FINISHED" and m.get("home_score") is not None:
            hs=m["home_score"]; as_=m["away_score"]
            items.append(html.Span([
                html.Span("⚽ ", className="ticker-goal"),
                html.Span(f"{m['home_flag']} {m['home_team']} ", style={"color":"#9A9AAA"}),
                html.Span(f"{hs}–{as_}", className="ticker-score"),
                html.Span(f" {m['away_flag']} {m['away_team']}", style={"color":"#9A9AAA"}),
            ], className="ticker-item"))
    if not items:
        items = [html.Span(
            "⚽  Tournament underway · Mexico 2–0 South Africa · South Korea 2–1 Czech Republic · USA 4–1 Paraguay · Stay tuned!",
            className="ticker-item")]
    return html.Div([
        html.Div("LIVE", className="ticker-label"),
        html.Div(items + items, className="ticker-track"),
    ], className="ticker-wrap")

def navbar():
    return html.Div(
        [
            html.Div(
                [
                    html.A(
                        [
                            html.Span(
                                "⚽ ",
                                style={
                                    "marginRight": "4px",
                                    "fontSize": "clamp(20px,4vw,25px)",
                                },
                            ),
                            html.Span(
                                " STAT",
                                style={
                                    "color": COLORS["text_primary"],
                                    "fontWeight": "900",
                                    "fontSize": "clamp(17px,4vw,22px)",
                                    "letterSpacing": "-0.03em",
                                },
                            ),
                            html.Span(
                                "DIUM",
                                className="shiny-text",
                                style={
                                    "fontWeight": "900",
                                    "fontSize": "clamp(17px,4vw,22px)",
                                    "letterSpacing": "-0.03em",
                                },
                            ),
                        ],
                        href="/",
                        style={
                            "textDecoration": "none",
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Link("Live", href="/", className="nav-link active"),
                            dcc.Link(
                                "Stadiums",
                                href="/stadiums",
                                className="nav-link hide-mobile",
                            ),
                            dcc.Link("Groups", href="/groups", className="nav-link"),
                            dcc.Link("Bracket", href="/bracket", className="nav-link"),
                            dcc.Link("Teams", href="/teams", className="nav-link"),
                            dcc.Link(
                                "Insights", href="/insights", className="nav-link"
                            ),
                            dcc.Link(
                                "Formations", href="/formations", className="nav-link"
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "2px",
                            "flexWrap": "nowrap",
                            "overflowX": "auto",
                        },
                    ),
                    html.Div(
                        [
                            html.Span(className="live-dot"),
                            html.Span(
                                id="typewriter-text",
                                **{"data-text": "FIFA World Cup 2026 · Live Analytics"},
                                style={
                                    "fontSize": "12px",
                                    "color": COLORS["text_secondary"],
                                    "whiteSpace": "nowrap",
                                },
                            ),
                            html.Span(
                                id="typewriter-cursor", className="typewriter-cursor"
                            ),
                        ],
                        className="typewriter-wrap hide-mobile",
                        style={"display": "flex", "alignItems": "center", "gap": "4px"},
                    ),
                ],
                className="navbar-inner",
                style={
                    "maxWidth": "1400px",
                    "margin": "0 auto",
                    "padding": "0 clamp(12px,3vw,24px)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "height": "60px",
                    "gap": "8px",
                },
            ),
        ],
        className="statdium-navbar",
    )
