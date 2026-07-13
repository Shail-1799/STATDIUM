from dash import html, dcc
from data.fetcher import get_flag_img, get_crest_img

COLORS = {
    "bg_primary":"#07070C","bg_card":"#111118","bg_card2":"#18181F","bg_card3":"#1E1E28",
    "accent":"#00E5A0","accent2":"#7B61FF","accent3":"#FF6B35",
    "gold":"#FFD700","text_primary":"#F2F2F7","text_secondary":"#8E8E9A",
    "text_dim":"#48484A","border":"#252530","live_red":"#FF3B30",
    "win_green":"#00E5A0","loss_red":"#FF453A","draw_gray":"#636366",
    "group_colors":{
        "A":"#00E5A0","B":"#7B61FF","C":"#FF6B35","D":"#FFD700",
        "E":"#00B4D8","F":"#FF6B9D","G":"#C77DFF","H":"#06D6A0",
        "I":"#FFB703","J":"#FB8500","K":"#E63946","L":"#457B9D",
    },
}

SIDEBAR_SECTIONS = [
    {"label":"OVERVIEW","items":[
        {"label":"Live","icon":"⚡","href":"/","id":"nav-live"},
        {"label":"Groups","icon":"📊","href":"/groups","id":"nav-groups"},
    ]},
    {"label":"ANALYTICS","items":[
        {"label":"Bracket","icon":"🏆","href":"/bracket","id":"nav-bracket"},
        {"label":"Teams","icon":"👥","href":"/teams","id":"nav-teams"},
        {"label":"Leaderboards","icon":"📈","href":"/leaderboards","id":"nav-leaderboards"},
        {"label":"Insights","icon":"🌍","href":"/insights","id":"nav-insights"},
        {"label":"History","icon":"📜","href":"/history","id":"nav-history"},
    ]},
    {"label":"INTERACTIVE","items":[
        {"label":"Predictor","icon":"🎯","href":"/predictor","id":"nav-predictor"},
        {"label":"What If","icon":"🔮","href":"/scenario","id":"nav-scenario"},
        {"label":"Simulator","icon":"🎬","href":"/simulator","id":"nav-simulator"},
        {"label":"Tactical DNA","icon":"🧬","href":"/tactical-dna","id":"nav-tactical-dna"},
    ]},
    {"label":"MATCH CENTRE","items":[
        {"label":"Formations","icon":"⚽","href":"/formations","id":"nav-formations"},
        {"label":"Stadiums & Clocks","icon":"🏟️","href":"/stadiums","id":"nav-stadiums"},
    ]},
    # {"label":"ELO INTELLIGENCE","items":[
    #     {"label":"Confederations","icon":"🌐","href":"/confederations","id":"nav-confederations"},
    # ]},
]

# ── STATDIUM SVG wordmark ──────────────────────────────────────────────────
WORDMARK_SVG = """<svg viewBox="0 0 140 28" xmlns="http://www.w3.org/2000/svg" style="height:22px;width:auto">
  <text x="0" y="22" font-family="Barlow Condensed,Inter,sans-serif" font-size="24"
        font-weight="900" letter-spacing="-0.5" fill="#F2F2F7">STAT</text>
  <text x="58" y="22" font-family="Barlow Condensed,Inter,sans-serif" font-size="24"
        font-weight="900" letter-spacing="-0.5" fill="#00E5A0">DIUM</text>
  <circle cx="134" cy="8" r="5" fill="none" stroke="#00E5A0" stroke-width="1.5"/>
  <line x1="131" y1="8" x2="137" y2="8" stroke="#00E5A0" stroke-width="1.2"/>
  <line x1="134" y1="5" x2="134" y2="11" stroke="#00E5A0" stroke-width="1.2"/>
</svg>"""

def page_wrapper(children):
    return html.Div(children, className="page-wrapper-inner",
                    style={"position":"relative","zIndex":"1"})

def section_header(title, subtitle=None, accent_color=None):
    color = accent_color or COLORS["accent"]
    return html.Div([
        html.Div(className="section-hdr-bar",
                 style={"backgroundColor":color,"width":"3px","height":"24px",
                        "borderRadius":"2px","marginRight":"12px","flexShrink":"0"}),
        html.Div([
            html.Div(title, className="section-hdr-title"),
            html.Div(subtitle, className="section-hdr-sub") if subtitle else None,
        ]),
    ], className="section-hdr")

def stat_pill(label, value, color=None):
    v = str(value)
    try: num = float(v) if v.replace(".","",1).lstrip("+-").isdigit() else None
    except: num = None
    return html.Div([
        html.Div(v,
                 className="stat-pill-value countup-num" if num is not None else "stat-pill-value",
                 **{"data-target":str(num)} if num is not None else {},
                 style={"color":color or COLORS["accent"]}),
        html.Div(label, className="stat-pill-label"),
    ], className="stat-pill glow-card")

def live_badge():
    return html.Span([html.Span(className="live-dot"),"LIVE"],
                     style={"backgroundColor":COLORS["live_red"],"color":"#fff",
                            "fontSize":"10px","fontWeight":"800","padding":"2px 8px",
                            "borderRadius":"4px","letterSpacing":"0.1em",
                            "display":"inline-flex","alignItems":"center",
                            "fontFamily":"var(--font-display)"})

def match_scorecard(match, show_actions=True):
    from data.fetcher import get_flag_img, get_crest_img
    from data.media_links import get_watch_live_url, get_watch_highlights_search_url

    status   = match.get("status","SCHEDULED")
    is_live  = status=="LIVE"
    is_fin   = status=="FINISHED"
    h        = match.get("home_score")
    a        = match.get("away_score")
    score_str = f"{h}  –  {a}" if (is_fin or is_live) and h is not None else "vs"
    gl       = str(match.get("group","")).replace("Group","").strip()
    gc       = COLORS["group_colors"].get(gl, COLORS["accent"])
    cls      = "match-card glow-card live-glow-card" if is_live else "match-card glow-card"
    home,away = match.get("home_team",""), match.get("away_team","")

    action_buttons = []
    if show_actions:
        if is_live:
            action_buttons.append(html.A(["Watch Live"],
                href=get_watch_live_url(home,away), target="_blank",
                className="match-action-btn match-action-live"))
        if is_fin:
            action_buttons.append(html.A(["Watch Highlights"],
                href=get_watch_highlights_search_url(home,away), target="_blank",
                className="match-action-btn match-action-highlights"))

    if is_live:   status_badge = live_badge()
    elif is_fin:  status_badge = html.Span("FT",style={"fontSize":"10px","fontWeight":"700","color":COLORS["text_secondary"],"background":COLORS["bg_card2"],"padding":"2px 7px","borderRadius":"4px"})
    else:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(f"{match.get('date','')}T{match.get('time','00:00') or '00:00'}:00".replace("Z",""))
            status_badge = html.Span(dt.strftime("%b %d · %H:%M UTC"),style={"fontSize":"10px","color":COLORS["text_secondary"]})
        except:
            status_badge = html.Span("SCHEDULED",style={"fontSize":"10px","color":COLORS["text_secondary"]})

    h_bold = a_bold = False
    if is_fin and h is not None and a is not None:
        h_bold,a_bold = h>a, a>h

    # Use crest if available, else flag
    def team_logo(team, sz=32):
        return get_crest_img(team, width=sz)

    return html.Div([
        html.Div([
            html.Span(match.get("group",""),style={"fontSize":"10px","fontWeight":"700","color":gc,"textTransform":"uppercase","letterSpacing":"0.1em","fontFamily":"var(--font-display)"}),
            html.Div([status_badge]+action_buttons,style={"display":"flex","alignItems":"center","gap":"8px"}),
        ],style={"display":"flex","alignItems":"center","justifyContent":"space-between","marginBottom":"12px"}),

        html.Div([
            html.Div([
                team_logo(home,32),
                html.Div(home,className="match-team-name",
                         style={"fontWeight":"800" if h_bold else "600","color":COLORS["text_primary"] if h_bold else COLORS["text_secondary"]}),
            ],style={"display":"flex","flexDirection":"column","alignItems":"center","gap":"0","minWidth":"84px"}),

            html.Div(score_str,className="match-score",
                     style={"color":COLORS["text_primary"] if (is_fin or is_live) else COLORS["text_secondary"]}),

            html.Div([
                team_logo(away,32),
                html.Div(away,className="match-team-name",
                         style={"fontWeight":"800" if a_bold else "600","color":COLORS["text_primary"] if a_bold else COLORS["text_secondary"]}),
            ],style={"display":"flex","flexDirection":"column","alignItems":"center","gap":"0","minWidth":"84px"}),
        ],style={"display":"flex","alignItems":"center","justifyContent":"center","gap":"12px"}),

        html.Div(match.get("venue",""),style={"fontSize":"10px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"8px"}),
    ], className=cls,
       id={"type":"match-card-click","id":match.get("id","")},
       n_clicks=0,
       **{"data-match-id": match.get("id","")},
       style={"cursor":"pointer"})


def standings_row(rank, team, flag, played, won, drawn, lost, gf, ga, pts, qualify=False, eliminate=False):
    gd = gf - ga

    # Rank badge — green circle for top 2, grey otherwise
    badge_bg    = "rgba(0,229,160,0.15)" if qualify else "rgba(255,255,255,0.05)"
    badge_color = COLORS["accent"] if qualify else COLORS["text_secondary"]
    rank_badge  = html.Div(str(rank), style={
        "width":"22px","height":"22px","borderRadius":"50%","flexShrink":"0",
        "background":badge_bg,"color":badge_color,
        "fontSize":"11px","fontWeight":"800","display":"flex",
        "alignItems":"center","justifyContent":"center",
        "fontFamily":"var(--font-display)",
    })

    # Flag image (real image, not emoji)
    flag_img = get_flag_img(team, width=20)

    # W/D/L colored individually
    def stat(v, color): return html.Span(str(v), style={
        "width":"28px","flexShrink":"0","fontSize":"12px","fontWeight":"700" if v else "400",
        "color":color if v else COLORS["text_dim"],"textAlign":"center",
    })

    row_cls = "standings-row"
    if qualify:    row_cls += " qualify"
    elif eliminate: row_cls += " eliminate"

    return html.Div([
        rank_badge,
        # Flag + team name inline on same row
        html.Div([
            flag_img,
            html.Span(team, style={
                "fontSize":"12px","fontWeight":"600","color":COLORS["text_primary"],
                "fontFamily":"var(--font-display)","overflow":"hidden",
                "textOverflow":"ellipsis","whiteSpace":"nowrap",
            }),
        ], style={"flex":"1","display":"flex","alignItems":"center","gap":"7px",
                  "paddingLeft":"6px","minWidth":"0"}),
        stat(played, COLORS["text_secondary"]),
        stat(won,    COLORS["win_green"]),
        stat(drawn,  COLORS["gold"]),
        stat(lost,   COLORS["loss_red"]),
        html.Span(f"{gf}:{ga}", style={
            "width":"44px","flexShrink":"0","fontSize":"11px",
            "color":COLORS["text_secondary"],"textAlign":"center",
        }),
        html.Span(f"{'+' if gd>=0 else ''}{gd}", style={
            "width":"30px","flexShrink":"0","fontSize":"11px","fontWeight":"700",
            "textAlign":"center",
            "color": COLORS["accent"] if gd>0 else (COLORS["loss_red"] if gd<0 else COLORS["text_dim"]),
        }),
        html.Span(str(pts), style={
            "width":"30px","flexShrink":"0","fontSize":"13px","fontWeight":"900",
            "textAlign":"center","fontFamily":"var(--font-display)",
            "color": COLORS["gold"] if qualify else COLORS["text_primary"],
        }),
    ], className=row_cls, style={"padding":"8px 10px"})


def goal_ticker(matches):
    items = []
    for m in matches:
        if m.get("status")=="FINISHED":
            hs,as_ = m.get("home_score",0) or 0, m.get("away_score",0) or 0
            items.append(html.Span([
                html.Span(get_flag_img(m['home_team'], width=20),style={"fontSize":"14px"}),
                html.Span(f" {m['home_team']} ",style={"color":COLORS["text_primary"],"fontWeight":"600"}),
                html.Span(f"{hs}–{as_}",className="ticker-score"),
                html.Span(f" {m['away_team']} ",style={"color":COLORS["text_primary"],"fontWeight":"600"}),
                html.Span(get_flag_img(m['away_team'], width=20),style={"fontSize":"14px"}),
            ],className="ticker-item"))
        elif m.get("status")=="LIVE":
            items.append(html.Span([
                html.Span(className="live-dot"),
                html.Span(f" {m['home_team']} vs {m['away_team']}",style={"color":COLORS["text_primary"],"fontWeight":"600"}),
            ],className="ticker-item"))
    if not items:
        items=[html.Span("⚽ FIFA World Cup 2026 — STATDIUM Live Analytics · 48 Teams · 104 Matches · 16 Stadiums",className="ticker-item")]
    return html.Div(
        [
            html.Div("MATCH CENTRE", className="ticker-label"),
            html.Div(items * 4, className="ticker-track"),
        ],
        className="ticker-wrap",
    )


def sidebar():
    section_blocks=[]
    for sec in SIDEBAR_SECTIONS:
        section_blocks.append(html.Div(sec["label"],className="sidebar-section-label"))
        for item in sec["items"]:
            section_blocks.append(
                dcc.Link([
                    html.Span(item["icon"],className="sidebar-icon"),
                    html.Span(item["label"],className="sidebar-label"),
                ],href=item["href"],id=item["id"],className="sidebar-link")
            )

    overlay = html.Div(id="sidebar-overlay")

    sidebar_el = html.Div(
        [
            html.Div(
                [
                    html.A(
                        html.Div(
                            [
                                # html.Span("⚽",style={"fontSize":"20px"}),
                                html.Img(
                                    src="/assets/logo.png",
                                    style={
                                        "height": "clamp(22px, 1.8vw, 26px)",
                                        "marginRight": "2px",
                                    },
                                ),
                                #
                                html.Div(
                                    [
                                        html.Span(
                                            "STAT",
                                            style={
                                                "fontFamily": "var(--font-display)",
                                                "fontWeight": "900",
                                                "fontSize": "20px",
                                                "color": "var(--text-primary)",
                                                "letterSpacing": "-0.02em",
                                            },
                                        ),
                                        html.Span(
                                            "DIUM",
                                            className="shiny-text",
                                            style={
                                                "fontFamily": "var(--font-display)",
                                                "fontWeight": "900",
                                                "fontSize": "20px",
                                                "color": "var(--accent)",
                                                "letterSpacing": "-0.02em",
                                            },
                                        ),
                                    ],
                                    className="sidebar-title",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "gap": "6px",
                            },
                        ),
                        href="/",
                        style={"textDecoration": "none"},
                    ),
                    html.Button(
                        "☰", id="sidebar-toggle-btn", className="sidebar-toggle-btn"
                    ),
                ],
                className="sidebar-header",
            ),
            html.Div(
                [
                    html.Span(className="live-dot"),
                    html.Span(
                        "FIFA World Cup 2026",
                        className="sidebar-label",
                        style={"fontSize": "11px", "color": COLORS["text_secondary"]},
                    ),
                ],
                className="sidebar-live-strip",
            ),
            html.Div(section_blocks, className="sidebar-nav"),
            # html.Div(id="sidebar-progress", className="sidebar-progress"),
        ],
        id="statdium-sidebar",
        className="statdium-sidebar",
    )

    mobile_topbar = html.Div([
        html.Button("☰",**{"data-mobile-toggle":"true"},
                    style={"background":"none","border":"none","color":COLORS["text_primary"],
                           "fontSize":"20px","cursor":"pointer","padding":"4px 8px","lineHeight":"1"}),
        # html.A([
        #     html.Span("⚽ ",style={"fontSize":"18px"}),
        #     html.Span("STAT",style={"fontFamily":"var(--font-display)","fontWeight":"900","color":COLORS["text_primary"]}),
        #     html.Span("DIUM",style={"fontFamily":"var(--font-display)","fontWeight":"900","color":COLORS["accent"]}),
        # ],href="/",style={"textDecoration":"none","display":"flex","alignItems":"center","fontSize":"18px","letterSpacing":"-0.02em"}),
    ],className="sidebar-mobile-topbar")

    return html.Div([overlay,sidebar_el,mobile_topbar])

def navbar(): return sidebar()


# ── PAGE GUIDE — collapsible "how to use this page" panel ─────────────────
def page_guide(title, bullets, accent_color=None):
    """
    Collapsible info panel shown at top of every page.
    title   : str   — short page name
    bullets : list  — list of (icon, text) tuples describing features / interactions
    """
    color = accent_color or COLORS["accent"]
    bullet_els = []
    for icon, text in bullets:
        bullet_els.append(html.Div([
            html.Span(icon, style={
                "fontSize":"16px","flexShrink":"0","width":"22px","textAlign":"center"
            }),
            html.Span(text, style={
                "fontSize":"12px","color":COLORS["text_secondary"],"lineHeight":"1.55"
            }),
        ], style={"display":"flex","alignItems":"flex-start","gap":"10px","padding":"4px 0"}))

    return html.Details([
        html.Summary([
            html.Span("ℹ️", style={"fontSize":"14px","marginRight":"8px"}),
            html.Span(f"Click to See How to use — {title}",
                      style={"fontSize":"12px","fontWeight":"700","color":color,
                             "textTransform":"uppercase","letterSpacing":"0.08em"}),
           
        ], style={"cursor":"pointer","listStyle":"none","display":"flex","alignItems":"center",
                  "padding":"10px 14px","outline":"none"}),
        html.Div(bullet_els, style={"padding":"4px 14px 12px 14px",
                                     "borderTop":f"1px solid {COLORS['border']}"}),
    ], style={
        "background":COLORS["bg_card2"],
        "border":f"1px solid {COLORS['border']}",
        "borderLeft":f"3px solid {color}",
        "borderRadius":"10px","marginBottom":"20px",
        "fontSize":"12px",
    })


def football_loader(text="Loading..."):
    """
    Reusable bouncing-football loading indicator — generic across every
    page. Pass it as the custom_spinner for any dcc.Loading that wraps a
    page's dynamic content:

        dcc.Loading(
            custom_spinner=football_loader("Loading leaderboards..."),
            children=html.Div(id="leaderboards-content"),
        )

    Works for both the "whole page on first load" case (wrap the page's
    top-level content Div) and "just this section while it refreshes"
    (wrap only the specific Div that a periodic Interval re-populates).
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Span("⚽", className="football-bounce"),
                    html.Div(className="football-bounce-shadow"),
                ],
                className="football-bounce-track",
            ),
            html.Div(text, className="football-loader-text"),
        ],
        className="football-loader-wrap",
    )
