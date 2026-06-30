"""
STATDIUM — What If Scenario Builder (Feature #2)
Override any match score, see group standings update live.
Pure Dash + existing Elo engine. No external API needed.
"""
from dash import html, dcc, Input, Output, State
import dash
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper, standings_row
from data.fetcher import get_cache, WC2026_GROUPS, get_flag, get_flag_img
from collections import defaultdict

GUIDE = page_guide("What If Scenario Builder", [
    ("🔮", "Select any match from the dropdown, set a custom score using the number inputs."),
    ("⚡", "Click 'Apply Scenario' — all 12 group standings instantly recompute with your override."),
    ("↺", "Groups that changed from your scenario are marked with a ↺ badge and orange border."),
    ("🔄", "Click 'Reset All' to go back to actual standings."),
    ("💡", "Try: set Germany 7–0 Curaçao and watch Group E standings shift."),
], accent_color=COLORS["accent3"])

def layout():
    cache = get_cache()
    matches = cache.get("matches", [])
    # Only show group stage (non-knockout) upcoming/scheduled matches + recent ones
    group_matches = [m for m in matches if m.get("group") and m.get("status") in ("SCHEDULED","TIMED","FINISHED")][:30]

    opts = []
    for m in group_matches:
        label = f"{m['home_flag']} {m['home_team']} vs {m['away_team']} {m['away_flag']} [{m.get('group','')}]"
        if m["status"] == "FINISHED":
            label += f" (FT: {m.get('home_score',0)}-{m.get('away_score',0)})"
        opts.append({"label": label, "value": m["id"]})

    return html.Div([
        page_wrapper([
            GUIDE,
            section_header("🔮 What If Scenario Builder",
                           "Override any match score and see group standings update instantly",
                           accent_color=COLORS["accent3"]),

            html.Div([
                # Left: match selector + score override
                html.Div([
                    html.Div("Select a Match", style={"fontSize":"11px","fontWeight":"700",
                             "color":COLORS["text_secondary"],"textTransform":"uppercase",
                             "letterSpacing":"0.08em","marginBottom":"8px"}),
                    dcc.Dropdown(id="scenario-match", options=opts,
                                 value=opts[0]["value"] if opts else None,
                                 placeholder="Choose a match…",
                                 style={"marginBottom":"16px"}),

                    html.Div(id="scenario-score-panel"),

                    html.Button("⚡ Apply Scenario", id="scenario-apply", n_clicks=0,
                                style={"width":"100%","background":"linear-gradient(135deg,#FF6B35,#FFD700)",
                                       "border":"none","borderRadius":"10px","color":"#000",
                                       "fontWeight":"800","fontSize":"14px","padding":"12px",
                                       "cursor":"pointer","marginTop":"12px"}),

                    html.Button("↺ Reset All", id="scenario-reset", n_clicks=0,
                                style={"width":"100%","background":"transparent",
                                       "border":f"1px solid {COLORS['border']}",
                                       "borderRadius":"10px","color":COLORS["text_secondary"],
                                       "fontSize":"13px","padding":"10px",
                                       "cursor":"pointer","marginTop":"8px"}),

                    dcc.Store(id="scenario-overrides", data={}),
                    html.Div(id="scenario-applied-list", style={"marginTop":"16px"}),
                ], style={"flex":"1","minWidth":"280px","background":COLORS["bg_card"],
                          "border":f"1px solid {COLORS['border']}","borderRadius":"14px","padding":"20px"}),

                # Right: live standings
                html.Div([
                    html.Div(id="scenario-standings"),
                ], style={"flex":"1.5","minWidth":"320px"}),
            ], style={"display":"flex","gap":"20px","flexWrap":"wrap"}),
        ]),
    ])


@app.callback(
    Output("scenario-score-panel","children"),
    Input("scenario-match","value"),
)
def show_score_panel(match_id):
    if not match_id: return html.Div()
    cache = get_cache()
    match = next((m for m in cache.get("matches",[]) if m["id"]==match_id), None)
    if not match: return html.Div()

    home = match.get("home_team",""); away = match.get("away_team","")
    cur_h = match.get("home_score") or 0
    cur_a = match.get("away_score") or 0

    return html.Div([
        html.Div([
            html.Div([
                get_flag_img(home, width=40),
                html.Div(home, style={"fontWeight":"700","fontSize":"14px","marginTop":"6px",
                                      "color":COLORS["text_primary"],"textAlign":"center"}),
            ], style={"textAlign":"center","flex":"1"}),

            html.Div([
                dcc.Input(id="scenario-home-score", type="number", value=cur_h,
                          min=0, max=20,
                          style={"width":"60px","textAlign":"center","fontSize":"28px","fontWeight":"800",
                                 "background":COLORS["bg_card2"],"border":f"1px solid {COLORS['border']}",
                                 "borderRadius":"8px","padding":"8px","color":COLORS["text_primary"]}),
                html.Span("–", style={"fontSize":"24px","color":COLORS["text_secondary"],"padding":"0 8px"}),
                dcc.Input(id="scenario-away-score", type="number", value=cur_a,
                          min=0, max=20,
                          style={"width":"60px","textAlign":"center","fontSize":"28px","fontWeight":"800",
                                 "background":COLORS["bg_card2"],"border":f"1px solid {COLORS['border']}",
                                 "borderRadius":"8px","padding":"8px","color":COLORS["text_primary"]}),
            ], style={"display":"flex","alignItems":"center","flex":"0 0 auto"}),

            html.Div([
                get_flag_img(away, width=40),
                html.Div(away, style={"fontWeight":"700","fontSize":"14px","marginTop":"6px",
                                      "color":COLORS["text_primary"],"textAlign":"center"}),
            ], style={"textAlign":"center","flex":"1"}),
        ], style={"display":"flex","alignItems":"center","justifyContent":"space-between","gap":"8px"}),

        html.Div(f"Group {match.get('group','')} · {match.get('date','')}",
                 style={"fontSize":"11px","color":COLORS["text_secondary"],"textAlign":"center","marginTop":"10px"}),
    ])


@app.callback(
    Output("scenario-overrides","data"),
    Output("scenario-applied-list","children"),
    Input("scenario-apply","n_clicks"),
    Input("scenario-reset","n_clicks"),
    State("scenario-match","value"),
    State("scenario-home-score","value"),
    State("scenario-away-score","value"),
    State("scenario-overrides","data"),
    prevent_initial_call=True,
)
def apply_scenario(apply_clicks, reset_clicks, match_id, home_score, away_score, overrides):
    ctx = dash.callback_context
    if not ctx.triggered: return overrides, html.Div()

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "scenario-reset":
        return {}, html.Div("All overrides cleared.", style={"fontSize":"12px","color":COLORS["text_secondary"]})

    if not match_id: return overrides, html.Div()
    overrides = dict(overrides or {})
    overrides[match_id] = {"home_score": int(home_score or 0), "away_score": int(away_score or 0)}

    cache = get_cache()
    applied_items = []
    for mid, scores in overrides.items():
        m = next((x for x in cache.get("matches",[]) if x["id"]==mid), None)
        if m:
            applied_items.append(html.Div(
                f"{m['home_flag']} {m['home_team']} {scores['home_score']}–{scores['away_score']} {m['away_team']} {m['away_flag']}",
                style={"fontSize":"12px","color":COLORS["accent"],"padding":"4px 8px",
                       "background":"rgba(0,229,160,0.08)","borderRadius":"6px","marginBottom":"4px"}
            ))

    badge = html.Div([
        html.Div(f"✅ {len(overrides)} scenario{'s' if len(overrides)!=1 else ''} applied",
                 style={"fontSize":"11px","fontWeight":"700","color":COLORS["accent"],"marginBottom":"6px"}),
        html.Div(applied_items),
    ])
    return overrides, badge


@app.callback(
    Output("scenario-standings","children"),
    Input("scenario-overrides","data"),
    Input("scenario-apply","n_clicks"),
    Input("scenario-reset","n_clicks"),
)
def update_scenario_standings(overrides, *_):
    cache = get_cache()
    matches = cache.get("matches", [])
    overrides = overrides or {}

    # Build scenario matches list
    scenario_matches = []
    for m in matches:
        if m["id"] in overrides and m.get("group"):
            sm = dict(m)
            sm["home_score"] = overrides[m["id"]]["home_score"]
            sm["away_score"] = overrides[m["id"]]["away_score"]
            sm["status"] = "FINISHED"
            scenario_matches.append(sm)
        else:
            scenario_matches.append(m)

    # Recompute group standings
    group_stats = {g: {t: {"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0}
                        for t in teams}
                   for g, teams in WC2026_GROUPS.items()}

    for m in scenario_matches:
        if m.get("status") != "FINISHED": continue
        gl = str(m.get("group","")).replace("Group","").strip()
        if not gl or gl not in group_stats: continue
        h, a = m.get("home_team",""), m.get("away_team","")
        hs, as_ = m.get("home_score",0) or 0, m.get("away_score",0) or 0
        if h not in group_stats[gl] or a not in group_stats[gl]: continue

        group_stats[gl][h]["p"] += 1; group_stats[gl][a]["p"] += 1
        group_stats[gl][h]["gf"] += hs; group_stats[gl][h]["ga"] += as_
        group_stats[gl][a]["gf"] += as_; group_stats[gl][a]["ga"] += hs

        if hs > as_:
            group_stats[gl][h]["w"] += 1; group_stats[gl][h]["pts"] += 3
            group_stats[gl][a]["l"] += 1
        elif hs == as_:
            group_stats[gl][h]["d"] += 1; group_stats[gl][h]["pts"] += 1
            group_stats[gl][a]["d"] += 1; group_stats[gl][a]["pts"] += 1
        else:
            group_stats[gl][a]["w"] += 1; group_stats[gl][a]["pts"] += 3
            group_stats[gl][h]["l"] += 1

    changed_groups = set()
    orig_groups = cache.get("groups", {})
    for gl in group_stats:
        for t in group_stats[gl]:
            if group_stats[gl][t] != orig_groups.get(gl, {}).get(t, {}):
                changed_groups.add(gl)

    blocks = []
    has_overrides = len(overrides) > 0

    if has_overrides:
        blocks.append(html.Div([
            html.Span("⚡ Scenario Active", style={"color":COLORS["accent3"],"fontWeight":"700","fontSize":"12px"}),
            html.Span(f" — {len(overrides)} match{'es' if len(overrides)!=1 else ''} overridden",
                      style={"color":COLORS["text_secondary"],"fontSize":"12px"}),
        ], style={"background":"rgba(255,107,53,0.1)","border":"1px solid rgba(255,107,53,0.3)",
                  "borderRadius":"8px","padding":"8px 14px","marginBottom":"16px"}))

    for gl in sorted(group_stats.keys()):
        teams_sorted = sorted(group_stats[gl].items(),
                              key=lambda x: (-x[1]["pts"], -(x[1]["gf"]-x[1]["ga"]), -x[1]["gf"]))
        changed = gl in changed_groups and has_overrides

        header_style = {"fontSize":"11px","fontWeight":"800","color":COLORS["accent3"] if changed else COLORS["accent"],
                        "textTransform":"uppercase","letterSpacing":"0.1em","marginBottom":"6px",
                        "display":"flex","alignItems":"center","gap":"6px"}
        rows = [html.Div([
            html.Span("GROUP " + gl, style=header_style),
            html.Span("CHANGED ↺", style={"fontSize":"10px","color":COLORS["accent3"],"fontWeight":"700"}) if changed else None,
        ])]
        # column header
        rows.append(html.Div([
            html.Span("",style={"flex":"1","fontSize":"10px","color":COLORS["text_secondary"]}),
            *[html.Span(h, style={"width":"24px","fontSize":"9px","color":COLORS["text_secondary"],"textAlign":"center","flexShrink":"0"})
              for h in ["P","W","D","L","GF","GA","GD","PTS"]],
        ], style={"display":"flex","padding":"0 12px","marginBottom":"2px"}))

        for rank, (team, s) in enumerate(teams_sorted, 1):
            gd = s["gf"] - s["ga"]
            is_qual = rank <= 2
            rows.append(html.Div([
                html.Span(str(rank), style={"width":"16px","fontSize":"11px","color":COLORS["text_secondary"],"flexShrink":"0"}),
                html.Span(get_flag(team), style={"fontSize":"14px","marginLeft":"2px","flexShrink":"0"}),
                html.Span(team, style={"flex":"1","fontSize":"12px","fontWeight":"600","paddingLeft":"6px",
                                       "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap",
                                       "color":COLORS["text_primary"]}),
                *[html.Span(str(v), style={"width":"24px","fontSize":"11px","color":COLORS["text_secondary"],"textAlign":"center","flexShrink":"0"})
                  for v in [s["p"],s["w"],s["d"],s["l"],s["gf"],s["ga"]]],
                html.Span(f"{'+' if gd>=0 else ''}{gd}",
                          style={"width":"24px","fontSize":"11px","textAlign":"center","flexShrink":"0",
                                 "color":COLORS["accent"] if gd>0 else (COLORS["loss_red"] if gd<0 else COLORS["text_secondary"]),
                                 "fontWeight":"600"}),
                html.Span(str(s["pts"]),
                          style={"width":"24px","fontSize":"12px","fontWeight":"800","textAlign":"center",
                                 "flexShrink":"0","color":COLORS["gold"] if is_qual else COLORS["text_primary"]}),
            ], style={"display":"flex","alignItems":"center","padding":"6px 12px","borderRadius":"6px","marginBottom":"2px",
                      "background":"rgba(0,229,160,0.06)" if is_qual else "transparent",
                      "border":"1px solid rgba(0,229,160,0.12)" if is_qual else "1px solid transparent"}))

        blocks.append(html.Div(rows, style={
            "background":COLORS["bg_card"],
            "border":f"2px solid {COLORS['accent3']}44" if changed and has_overrides else f"1px solid {COLORS['border']}",
            "borderRadius":"12px","padding":"14px","marginBottom":"12px",
        }))

    return html.Div([
        section_header("Scenario Standings",
                       "Groups marked ↺ changed from your overrides",
                       accent_color=COLORS["accent3"]),
        html.Div(blocks, style={"columns":"2","columnGap":"16px","breakInside":"avoid"}),
    ])
