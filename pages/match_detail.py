"""
STATDIUM — Match Detail Modal
Centre overlay. Close via ✕ button or clicking backdrop.
Uses a separate close-store to avoid ID conflicts.
"""
from dash import html, dcc, Input, Output, State
import json, dash
from app_instance import app
from components.ui import COLORS
from data.fetcher import get_cache, get_flag, get_flag_img, get_crest_img, FIFA_RANKINGS
from data.elo import get_elo_with_fallback

def modal_shell():
    """Always-present modal shell. One dcc.Store drives open/close."""
    return html.Div([
        # Backdrop — pure div, no n_clicks (handled by JS in statdium.js)
        html.Div(id="match-modal-backdrop", style={
            "display":"none","position":"fixed","inset":"0",
            "background":"rgba(0,0,0,0.82)","backdropFilter":"blur(5px)",
            "zIndex":"2000","cursor":"pointer",
        }),
        # Centre card
        html.Div([
            html.Div(id="match-modal-body"),
        ], id="match-modal-drawer", style={
            "display":"none","position":"fixed",
            "top":"50%","left":"50%","transform":"translate(-50%,-50%)",
            "width":"min(560px,95vw)","maxHeight":"90vh","overflowY":"auto",
            "background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
            "borderRadius":"18px","zIndex":"2001","padding":"0",
            "boxShadow":"0 32px 80px rgba(0,0,0,0.7)",
        }),
        # Two stores: one for which match to show, one to signal close
        dcc.Store(id="match-modal-id",    data=None),
        dcc.Store(id="match-modal-close", data=0),
    ])


@app.callback(
    Output("match-modal-backdrop","style"),
    Output("match-modal-drawer","style"),
    Output("match-modal-body","children"),
    Output("match-modal-id","data"),          # reset to None on close
    Input("match-modal-id","data"),
    Input("match-modal-close","data"),
    prevent_initial_call=True,
)
def toggle_modal(match_id, close_signal):
    CLOSED_BACKDROP = {
        "display":"none","position":"fixed","inset":"0",
        "background":"rgba(0,0,0,0.82)","backdropFilter":"blur(5px)",
        "zIndex":"2000","cursor":"pointer",
    }
    CLOSED_DRAWER = {
        "display":"none","position":"fixed",
        "top":"50%","left":"50%","transform":"translate(-50%,-50%)",
        "width":"min(560px,95vw)","maxHeight":"90vh","overflowY":"auto",
        "background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
        "borderRadius":"18px","zIndex":"2001","padding":"0",
        "boxShadow":"0 32px 80px rgba(0,0,0,0.7)",
    }
    OPEN_BACKDROP = {**CLOSED_BACKDROP, "display":"block"}
    OPEN_DRAWER   = {**CLOSED_DRAWER,   "display":"block"}

    ctx     = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    # Close signal fired (from JS setting the store) or no match
    if "match-modal-close" in trigger or not match_id:
        return CLOSED_BACKDROP, CLOSED_DRAWER, html.Div(), None

    cache  = get_cache()
    match  = next((m for m in cache.get("matches",[]) if m["id"] == match_id), None)
    if not match:
        return CLOSED_BACKDROP, CLOSED_DRAWER, html.Div(), None

    return OPEN_BACKDROP, OPEN_DRAWER, _build_modal_body(match, cache), match_id


@app.callback(
    Output("match-modal-id","data", allow_duplicate=True),
    Input({"type":"match-card-click","id":dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_modal_from_card(all_clicks):
    ctx = dash.callback_context
    if not ctx.triggered: return dash.no_update
    triggered = ctx.triggered[0]
    if not triggered["value"]: return dash.no_update
    try:
        id_dict = json.loads(triggered["prop_id"].split(".n_clicks")[0])
        mid = id_dict.get("id","")
        return mid if mid else dash.no_update
    except Exception:
        return dash.no_update


def _build_modal_body(m, cache):
    from data.media_links import get_watch_live_url, get_watch_highlights_search_url

    home, away = m.get("home_team",""), m.get("away_team","")
    hs, as_    = m.get("home_score") or 0, m.get("away_score") or 0
    status     = m.get("status","")
    is_fin     = status == "FINISHED"
    is_live    = status == "LIVE"
    ea, eb     = get_elo_with_fallback(home), get_elo_with_fallback(away)
    prob_a     = round(1 / (1 + 10**((eb-ea)/400)) * 100)
    prob_b     = 100 - prob_a
    gl         = str(m.get("group","")).replace("Group","").strip()
    gc         = COLORS["group_colors"].get(gl, COLORS["accent"])

    scorers_home = [g.get("name","") for g in (m.get("goals1") or []) if g.get("name")]
    scorers_away = [g.get("name","") for g in (m.get("goals2") or []) if g.get("name")]

    # Header with ✕ close — uses JS to set match-modal-close store
    header = html.Div([
        html.Div([
            html.Span(m.get("group",""), style={
                "fontSize":"11px","fontWeight":"800","color":gc,
                "textTransform":"uppercase","letterSpacing":"0.12em",
                "fontFamily":"var(--font-display)",
            }),
            html.Span(" · " + m.get("date",""),
                      style={"fontSize":"11px","color":COLORS["text_secondary"]}),
        ]),
        html.Button("✕", id="modal-close-btn-inner", n_clicks=0, style={
            "background":"rgba(255,255,255,0.07)","border":"none",
            "color":COLORS["text_secondary"],"fontSize":"16px",
            "width":"32px","height":"32px","borderRadius":"50%",
            "cursor":"pointer","display":"flex","alignItems":"center",
            "justifyContent":"center","lineHeight":"1",
        }),
    ], style={
        "display":"flex","justifyContent":"space-between","alignItems":"center",
        "padding":"16px 20px","borderBottom":f"1px solid {COLORS['border']}",
    })

    def team_col(team, goals):
        return html.Div([
            get_crest_img(team, width=52),
            html.Div(team, style={
                "fontFamily":"var(--font-display)","fontSize":"16px","fontWeight":"800",
                "color":COLORS["text_primary"],"marginTop":"8px","textAlign":"center",
            }),
            html.Div(f"#{FIFA_RANKINGS.get(team,'?')} FIFA",
                     style={"fontSize":"10px","color":COLORS["text_secondary"],"textAlign":"center"}),
            html.Div([
                html.Div(f"⚽ {g}",
                         style={"fontSize":"11px","color":COLORS["text_secondary"],"padding":"2px 0"})
                for g in goals
            ], style={"marginTop":"6px","minHeight":"18px"}),
        ], style={"flex":"1","display":"flex","flexDirection":"column","alignItems":"center"})

    score_row = html.Div([
        team_col(home, scorers_home),
        html.Div([
            html.Div(f"{hs}–{as_}" if (is_fin or is_live) else "vs", style={
                "fontFamily":"var(--font-display)","fontSize":"52px","fontWeight":"900",
                "color":COLORS["text_primary"],"lineHeight":"1","textAlign":"center",
            }),
            html.Div(
                "FT" if is_fin else ("🔴 LIVE" if is_live else "SCHEDULED"),
                style={"fontSize":"11px","fontWeight":"700","textAlign":"center",
                       "marginTop":"4px",
                       "color":COLORS["live_red"] if is_live else COLORS["text_secondary"]},
            ),
        ], style={"flexShrink":"0","padding":"0 12px","alignSelf":"center"}),
        team_col(away, scorers_away),
    ], style={"display":"flex","alignItems":"flex-start","padding":"20px"})

    prob_bar = html.Div([
        html.Div("Elo Win Probability", style={
            "fontSize":"9px","fontWeight":"700","color":COLORS["text_secondary"],
            "textTransform":"uppercase","letterSpacing":"0.1em","marginBottom":"8px",
        }),
        html.Div([
            html.Div(style={"width":f"{prob_a}%","background":COLORS["accent"],
                            "height":"8px","borderRadius":"3px 0 0 3px"}),
            html.Div(style={"width":f"{prob_b}%","background":COLORS["accent2"],
                            "height":"8px","borderRadius":"0 3px 3px 0"}),
        ], style={"display":"flex","borderRadius":"3px","overflow":"hidden","marginBottom":"6px"}),
        html.Div([
            html.Span(f"{home[:16]} {prob_a}%",
                      style={"color":COLORS["accent"],"fontSize":"11px","fontWeight":"700"}),
            html.Span(f"{prob_b}% {away[:16]}",
                      style={"color":COLORS["accent2"],"fontSize":"11px","fontWeight":"700"}),
        ], style={"display":"flex","justifyContent":"space-between"}),
    ], style={"padding":"14px 20px","borderTop":f"1px solid {COLORS['border']}"})

    details = html.Div([
        html.Div([
            html.Span(str(ea), style={"fontFamily":"var(--font-display)","fontSize":"20px",
                                      "fontWeight":"900","color":COLORS["accent"]}),
            html.Span(" Elo", style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            html.Div(home[:18], style={"fontSize":"10px","color":COLORS["text_secondary"]}),
        ], style={"flex":"1"}),
        html.Div("⚡", style={"fontSize":"18px","alignSelf":"center","padding":"0 12px"}),
        html.Div([
            html.Span(str(eb), style={"fontFamily":"var(--font-display)","fontSize":"20px",
                                      "fontWeight":"900","color":COLORS["accent2"]}),
            html.Span(" Elo", style={"fontSize":"11px","color":COLORS["text_secondary"]}),
            html.Div(away[:18], style={"fontSize":"10px","color":COLORS["text_secondary"]}),
        ], style={"flex":"1","textAlign":"right"}),
    ], style={"display":"flex","padding":"12px 20px",
              "borderTop":f"1px solid {COLORS['border']}","alignItems":"center"})

    venue = html.Div([
        html.Span("🏟️ ", style={"fontSize":"13px"}),
        html.Span(m.get("venue","Unknown venue"),
                  style={"fontSize":"12px","color":COLORS["text_secondary"]}),
    ], style={"padding":"10px 20px","borderTop":f"1px solid {COLORS['border']}"})

    actions = html.Div(
        [x for x in [
            html.A("📺 Watch Live", href=get_watch_live_url(home,away), target="_blank",
                   className="match-action-btn match-action-live") if is_live else None,
            html.A("🎬 Highlights", href=get_watch_highlights_search_url(home,away),
                   target="_blank",
                   className="match-action-btn match-action-highlights") if is_fin else None,
        ] if x],
        style={"display":"flex","gap":"8px","padding":"14px 20px",
               "borderTop":f"1px solid {COLORS['border']}"}
    )

    return html.Div([header, score_row, prob_bar, details, venue, actions])


# Dash callback: ✕ button click → increment close store → triggers toggle_modal
@app.callback(
    Output("match-modal-close","data"),
    Input("modal-close-btn","n_clicks"),
    Input("modal-close-btn-inner","n_clicks"),
    State("match-modal-close","data"),
    prevent_initial_call=True,
)
def close_via_button(n1, n2, current):
    if not n1 and not n2: return dash.no_update
    return (current or 0) + 1
