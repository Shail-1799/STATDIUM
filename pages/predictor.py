"""
STATDIUM — Match Predictor
Pick winners of upcoming matches. Track your accuracy as results come in.
100% client-side via dcc.Store (localStorage). No API needed.
"""
from dash import html, dcc, Input, Output, State
import dash
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper, page_guide
from data.fetcher import get_cache, get_flag, get_flag_img, get_crest_img

GUIDE = page_guide("Match Predictor", [
    ("🎯", "Pick the winner (or draw) for any upcoming or live match — tap a team button to lock in your prediction."),
    ("✅", "Once the match finishes, your pick turns green (correct) or red (wrong) automatically."),
    ("📊", "Your running accuracy score is shown at the top — how do you compare to the Elo model?"),
    ("💾", "Picks are saved locally in your browser — they persist across sessions on this device."),
    ("🔄", "You can change a pick any time before the match finishes."),
], accent_color=COLORS["accent3"])


def layout():
    return html.Div([
        dcc.Interval(id="pred-interval", interval=60000, n_intervals=0),
        dcc.Store(id="pred-picks", storage_type="local", data={}),
        page_wrapper([
            GUIDE,
            section_header("🎯 Match Predictor",
                           "Pick winners · Track your accuracy · Beat the Elo model",
                           accent_color=COLORS["accent3"]),
            html.Div(id="pred-scoreboard", style={"marginBottom":"24px"}),
            html.Div(id="pred-matches"),
        ]),
    ])


@app.callback(
    Output("pred-scoreboard", "children"),
    Input("pred-picks", "data"),
    Input("pred-interval", "n_intervals"),
)
def update_scoreboard(picks, _):
    picks = picks or {}
    cache = get_cache()
    matches = cache.get("matches", [])
    finished = {m["id"]: m for m in matches if m["status"] == "FINISHED"}

    correct = wrong = pending = 0
    for mid, pick in picks.items():
        m = finished.get(mid)
        if not m:
            pending += 1
            continue
        hs, as_ = m.get("home_score", 0) or 0, m.get("away_score", 0) or 0
        actual = m["home_team"] if hs > as_ else (m["away_team"] if as_ > hs else "draw")
        if pick == actual: correct += 1
        else: wrong += 1

    total_graded = correct + wrong
    acc = round(correct / total_graded * 100) if total_graded else 0
    acc_color = COLORS["accent"] if acc >= 60 else (COLORS["gold"] if acc >= 40 else COLORS["loss_red"])

    # Elo model baseline (~58% accuracy for favourites)
    elo_baseline = 58

    return html.Div([
        html.Div([
            html.Div([
                html.Div(f"{acc}%", style={"fontSize":"36px","fontWeight":"900",
                                            "fontFamily":"var(--font-display)","color":acc_color}),
                html.Div("YOUR ACCURACY", style={"fontSize":"10px","color":COLORS["text_secondary"],
                                                   "textTransform":"uppercase","letterSpacing":"0.1em","marginTop":"2px"}),
            ], style={"textAlign":"center","flex":"1"}),

            html.Div(style={"width":"1px","background":COLORS["border"],"margin":"0 8px"}),

            html.Div([
                html.Div(str(correct), style={"fontSize":"28px","fontWeight":"900",
                                               "fontFamily":"var(--font-display)","color":COLORS["accent"]}),
                html.Div("CORRECT", style={"fontSize":"10px","color":COLORS["text_secondary"],
                                            "textTransform":"uppercase","letterSpacing":"0.1em"}),
            ], style={"textAlign":"center","flex":"1"}),

            html.Div([
                html.Div(str(wrong), style={"fontSize":"28px","fontWeight":"900",
                                             "fontFamily":"var(--font-display)","color":COLORS["loss_red"]}),
                html.Div("WRONG", style={"fontSize":"10px","color":COLORS["text_secondary"],
                                          "textTransform":"uppercase","letterSpacing":"0.1em"}),
            ], style={"textAlign":"center","flex":"1"}),

            html.Div([
                html.Div(str(pending), style={"fontSize":"28px","fontWeight":"900",
                                               "fontFamily":"var(--font-display)","color":COLORS["text_secondary"]}),
                html.Div("PENDING", style={"fontSize":"10px","color":COLORS["text_secondary"],
                                            "textTransform":"uppercase","letterSpacing":"0.1em"}),
            ], style={"textAlign":"center","flex":"1"}),

            html.Div(style={"width":"1px","background":COLORS["border"],"margin":"0 8px"}),

            html.Div([
                html.Div(f"{elo_baseline}%", style={"fontSize":"28px","fontWeight":"900",
                                                      "fontFamily":"var(--font-display)","color":COLORS["accent2"]}),
                html.Div("ELO BASELINE", style={"fontSize":"10px","color":COLORS["text_secondary"],
                                                  "textTransform":"uppercase","letterSpacing":"0.1em"}),
                html.Div("beat this →" if acc < elo_baseline else "you beat it! 🎉",
                         style={"fontSize":"10px","color":COLORS["accent2"] if acc < elo_baseline else COLORS["gold"],
                                "marginTop":"2px"}),
            ], style={"textAlign":"center","flex":"1"}),

        ], style={"display":"flex","alignItems":"center","gap":"8px",
                  "background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
                  "borderRadius":"12px","padding":"20px 24px"}),

        # Accuracy progress bar
        html.Div([
            html.Div(style={
                "width":f"{acc}%","height":"100%","borderRadius":"3px 0 0 3px",
                "background":acc_color,"transition":"width 0.8s ease",
            }),
            html.Div(style={
                "width":f"{max(0, elo_baseline-acc)}%","height":"100%",
                "background":COLORS["accent2"],"opacity":"0.3",
            }) if acc < elo_baseline else html.Div(),
        ], style={"display":"flex","height":"6px","background":COLORS["bg_card2"],
                  "borderRadius":"3px","marginTop":"10px","overflow":"hidden"}),
        html.Div(f"Elo baseline: {elo_baseline}% · {'You are ahead! 🏆' if acc >= elo_baseline else f'{elo_baseline-acc}% to beat the model'}",
                 style={"fontSize":"11px","color":COLORS["text_secondary"],"marginTop":"5px"}),
    ])


@app.callback(
    Output("pred-matches", "children"),
    Input("pred-picks", "data"),
    Input("pred-interval", "n_intervals"),
)
def render_match_cards(picks, _):
    picks = picks or {}
    cache = get_cache()
    matches = cache.get("matches", [])

    # Show: all live + scheduled (upcoming) + last 10 finished that have picks
    live_sched = [m for m in matches if m["status"] in ("LIVE", "SCHEDULED", "TIMED")]
    finished_with_picks = [m for m in matches
                           if m["status"] == "FINISHED" and m["id"] in picks][-10:]

    sections = []

    if live_sched:
        sections.append(html.Div([
            html.Div([
                html.Span("🔮", style={"fontSize":"14px"}),
                html.Span(" MAKE YOUR PICKS", style={"fontSize":"11px","fontWeight":"800",
                           "color":COLORS["accent3"],"letterSpacing":"0.1em","marginLeft":"6px"}),
                html.Span(f"  {len(live_sched)} matches",
                          style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            ], style={"display":"flex","alignItems":"center","padding":"6px 0",
                      "borderBottom":f"1px solid {COLORS['border']}","marginBottom":"12px"}),
            html.Div([
                _pick_card(m, picks.get(m["id"]), graded=False)
                for m in live_sched[:30]
            ], style={"display":"grid",
                      "gridTemplateColumns":"repeat(auto-fill,minmax(300px,1fr))",
                      "gap":"12px"}),
        ], style={"marginBottom":"32px"}))

    if finished_with_picks:
        sections.append(html.Div([
            html.Div([
                html.Span("📋", style={"fontSize":"14px"}),
                html.Span(" RESULTS", style={"fontSize":"11px","fontWeight":"800",
                           "color":COLORS["text_secondary"],"letterSpacing":"0.1em","marginLeft":"6px"}),
            ], style={"display":"flex","alignItems":"center","padding":"6px 0",
                      "borderBottom":f"1px solid {COLORS['border']}","marginBottom":"12px"}),
            html.Div([
                _pick_card(m, picks.get(m["id"]), graded=True)
                for m in finished_with_picks
            ], style={"display":"grid",
                      "gridTemplateColumns":"repeat(auto-fill,minmax(300px,1fr))",
                      "gap":"12px"}),
        ]))

    if not sections:
        return html.Div([
            html.Div("🎯", style={"fontSize":"48px","textAlign":"center","marginBottom":"12px"}),
            html.Div("No matches to predict right now",
                     style={"fontSize":"16px","fontWeight":"700","color":COLORS["text_primary"],"textAlign":"center"}),
            html.Div("Check back when upcoming matches are scheduled",
                     style={"fontSize":"13px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"6px"}),
        ], style={"padding":"60px 20px"})

    return html.Div(sections)


def _pick_card(match, current_pick, graded=False):
    mid   = match["id"]
    home  = match.get("home_team","")
    away  = match.get("away_team","")
    is_live = match["status"] == "LIVE"
    gl    = str(match.get("group","")).replace("Group","").strip()
    gc    = COLORS["group_colors"].get(gl, COLORS["accent"])

    result_indicator = None
    card_border = COLORS["border"]
    card_bg     = COLORS["bg_card"]

    if graded and current_pick:
        hs, as_ = match.get("home_score",0) or 0, match.get("away_score",0) or 0
        actual  = home if hs > as_ else (away if as_ > hs else "draw")
        is_correct = current_pick == actual
        card_border = COLORS["accent"] if is_correct else COLORS["loss_red"]
        card_bg     = "rgba(0,229,160,0.05)" if is_correct else "rgba(255,69,58,0.05)"
        result_indicator = html.Div(
            "✅ Correct!" if is_correct else f"❌ Wrong — was {get_flag(actual)} {actual}",
            style={"fontSize":"11px","fontWeight":"700",
                   "color":COLORS["accent"] if is_correct else COLORS["loss_red"],
                   "marginTop":"8px","textAlign":"center"}
        )

    def pick_btn(label, value, flag_team):
        is_selected = current_pick == value
        if is_selected:
            btn_style = {"background":f"rgba(0,229,160,0.15)","border":f"2px solid {COLORS['accent']}",
                         "color":COLORS["accent"],"fontWeight":"800"}
        else:
            btn_style = {"background":COLORS["bg_card2"],"border":f"1px solid {COLORS['border']}",
                         "color":COLORS["text_secondary"],"fontWeight":"500"}
        return html.Button(
            [get_flag(flag_team) + " " + label] if label != "Draw" else ["🤝 Draw"],
            id={"type":"pred-btn","match":mid,"pick":value},
            n_clicks=0,
            disabled=graded,
            style={
                **btn_style,
                "borderRadius":"8px","padding":"7px 10px","fontSize":"11px",
                "cursor":"default" if graded else "pointer","flex":"1",
                "fontFamily":"var(--font-body)","transition":"all 0.15s ease",
            }
        )

    score_str = ""
    if match["status"] == "FINISHED":
        score_str = f"{match.get('home_score',0)}–{match.get('away_score',0)}"

    return html.Div([
        # Header
        html.Div([
            html.Span(match.get("group",""), style={"fontSize":"10px","fontWeight":"700",
                      "color":gc,"textTransform":"uppercase","letterSpacing":"0.1em",
                      "fontFamily":"var(--font-display)"}),
            html.Span(
                html.Span([html.Span(className="live-dot"), "LIVE"], style={"display":"flex","alignItems":"center","gap":"3px","fontSize":"10px","fontWeight":"700","color":COLORS["live_red"]})
                if is_live else
                html.Span(score_str or match.get("date",""),
                          style={"fontSize":"10px","color":COLORS["text_secondary"]}),
            ),
        ], style={"display":"flex","justifyContent":"space-between","marginBottom":"12px"}),

        # Teams
        html.Div([
            html.Div([
                get_crest_img(home, width=28),
                html.Div(home, style={"fontSize":"12px","fontWeight":"700","marginTop":"4px",
                                       "color":COLORS["text_primary"],"textAlign":"center",
                                       "fontFamily":"var(--font-display)","maxWidth":"80px"}),
            ], style={"display":"flex","flexDirection":"column","alignItems":"center","gap":"0","flex":"1"}),
            html.Div("VS", style={"fontSize":"14px","fontWeight":"900","color":COLORS["text_dim"],
                                   "fontFamily":"var(--font-display)","alignSelf":"center"}),
            html.Div([
                get_crest_img(away, width=28),
                html.Div(away, style={"fontSize":"12px","fontWeight":"700","marginTop":"4px",
                                       "color":COLORS["text_primary"],"textAlign":"center",
                                       "fontFamily":"var(--font-display)","maxWidth":"80px"}),
            ], style={"display":"flex","flexDirection":"column","alignItems":"center","gap":"0","flex":"1"}),
        ], style={"display":"flex","alignItems":"center","marginBottom":"12px"}),

        # Pick buttons
        html.Div([
            pick_btn(home[:12], home, home),
            pick_btn("Draw", "draw", ""),
            pick_btn(away[:12], away, away),
        ], style={"display":"flex","gap":"6px"}),

        result_indicator or html.Div(),

    ], style={
        "background":card_bg,
        "border":f"1px solid {card_border}",
        "borderRadius":"12px","padding":"14px",
        "transition":"all 0.2s ease",
    })


# Callback: clicking a pick button updates the store
@app.callback(
    Output("pred-picks","data"),
    Input({"type":"pred-btn","match":dash.ALL,"pick":dash.ALL},"n_clicks"),
    State("pred-picks","data"),
    prevent_initial_call=True,
)
def save_pick(all_clicks, current_picks):
    ctx   = dash.callback_context
    if not ctx.triggered: return current_picks or {}
    picks = dict(current_picks or {})
    prop  = ctx.triggered[0]["prop_id"]
    if not prop or prop == ".": return picks
    try:
        import json
        id_part = prop.split(".n_clicks")[0]
        id_dict = json.loads(id_part)
        mid  = id_dict["match"]
        pick = id_dict["pick"]
        # Toggle off if same pick clicked again
        if picks.get(mid) == pick:
            del picks[mid]
        else:
            picks[mid] = pick
    except Exception:
        pass
    return picks
