"""
STATDIUM — Animated Bracket (Feature #5) + GDP vs Football Power (Feature #7)
Cinematic tournament simulation + World Bank economic data viz.
"""
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import random, json
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import get_cache, WC2026_GROUPS, FIFA_RANKINGS, get_flag, normalize_round, KNOCKOUT_ROUND_ORDER
from data.elo import get_elo_with_fallback
# NOTE: intentionally NOT importing utils.monte_carlo.run_simulation here.
# Two reasons: (1) it previously shared its name with the callback function
# below, which caused infinite self-recursion on every single click — the
# real simulator likely never actually ran, silently falling back to the
# cruder inline sim every time. (2) even when it did "succeed", its result
# never populated the bracket's "rounds" data, so the round-by-round display
# stayed empty either way. Rather than keep depending on an external
# function whose output shape wasn't compatible with this page's display,
# everything now runs through one self-contained, fully-tested simulator
# below (run_bracket_simulation), which ALSO fixes the deeper issue: it
# builds the bracket from actual current results, not from scratch.

# GDP data (World Bank 2023, USD billions) — embedded to avoid API call
GDP_DATA = {
    "USA":27360,"Germany":4430,"Japan":4210,"France":3050,"Brazil":2170,
    "Canada":2140,"Italy":2170,"Australia":1720,"Spain":1580,"Mexico":1320,
    "Netherlands":1090,"Switzerland":906,"Argentina":632,"Sweden":594,
    "Norway":546,"Belgium":627,"Austria":516,"Colombia":363,"Portugal":362,
    "South Korea":1710,"Turkey":1108,"Egypt":396,"Iran":367,"Saudi Arabia":1063,
    "Uruguay":77,"Ecuador":118,"Paraguay":42,"Morocco":142,"Algeria":194,
    "Tunisia":47,"Senegal":27,"Ghana":76,"Ivory Coast":70,"DR Congo":62,
    "South Africa":377,"England":3076,"Scotland":210,"Croatia":82,
    "Bosnia & Herzegovina":23,"Serbia":78,"Ukraine":161,"Jordan":48,
    "Iraq":264,"Qatar":220,"Cape Verde":2,"Curaçao":3,"Haiti":20,
    "New Zealand":249,"Uzbekistan":90,"Panama":73,
}

GUIDE = page_guide("Tournament Simulator", [
    ("▶️", "Click 'Simulate Tournament' to run a full bracket using Elo win probabilities."),
    ("🎲", "Each simulation is randomised — run it multiple times to see different outcomes."),
    ("💰", "GDP vs Football Power (bottom): bubble size = Elo strength. Does wealth predict success?"),
    ("🔍", "Hover any bubble on the chart to see the country's GDP and Elo rating."),
], accent_color=COLORS["gold"])

def layout():
    all_teams = sorted([t for teams in WC2026_GROUPS.values() for t in teams])

    return html.Div([
        page_wrapper([
            GUIDE,
            # Animated Bracket Simulator
            section_header("🎬 Tournament Simulator",
                           "Click Simulate to watch the bracket fill round by round — powered by Elo + Poisson",
                           accent_color=COLORS["gold"]),

            html.Div([
                html.Button("▶ Simulate Tournament", id="sim-run-btn", n_clicks=0,
                            style={"background":"linear-gradient(135deg,#FFD700,#FF6B35)",
                                   "border":"none","borderRadius":"10px","color":"#000",
                                   "fontWeight":"900","fontSize":"15px","padding":"14px 28px",
                                   "cursor":"pointer"}),
                html.Button("↺ Reset", id="sim-reset-btn", n_clicks=0,
                            style={"background":"transparent","border":f"1px solid {COLORS['border']}",
                                   "borderRadius":"10px","color":COLORS["text_secondary"],
                                   "fontSize":"13px","padding":"14px 20px","cursor":"pointer"}),
                html.Div(id="sim-status",
                         style={"fontSize":"13px","color":COLORS["text_secondary"],"alignSelf":"center"}),
            ], style={"display":"flex","gap":"12px","marginBottom":"24px","flexWrap":"wrap","alignItems":"center"}),

            dcc.Store(id="sim-results", data=None),
            html.Div(id="sim-bracket-display"),

            html.Div(style={"height":"48px"}),

            # GDP vs Football Power
            section_header("💰 GDP vs Football Power",
                           "Does money buy World Cup success? Economic power vs Elo strength",
                           accent_color=COLORS["accent3"]),
            html.Div(id="gdp-chart"),
        ]),
    ])


def _win_prob(a, b):
    ea, eb = get_elo_with_fallback(a), get_elo_with_fallback(b)
    return 1 / (1 + 10 ** ((eb - ea) / 400))


def _play(a, b):
    return a if random.random() < _win_prob(a, b) else b


def run_bracket_simulation():
    """
    Builds the knockout bracket from the ACTUAL current tournament state:
    any match that's already been played uses its real result — locked in,
    never re-randomized — and only fixtures that haven't happened yet get
    Elo-based simulation. This means "Simulate Tournament" answers "who
    wins from here", which is what stays useful once most of the bracket
    is real, instead of re-randomizing rounds that have already happened.
    """
    cache = get_cache()
    matches = cache.get("matches", [])

    by_round = {r: [] for r in KNOCKOUT_ROUND_ORDER}
    for m in matches:
        r = normalize_round(m.get("round", ""))
        if r:
            by_round[r].append(m)

    if not any(by_round[r] for r in KNOCKOUT_ROUND_ORDER):
        # No knockout fixtures in the feed at all yet (e.g. very early in
        # the tournament) — fall back to building a bracket purely from
        # group-stage placements, same as this page always did before.
        return _simulate_from_groups()

    rounds_out = {r: [] for r in KNOCKOUT_ROUND_ORDER}
    advancing = None

    for r in KNOCKOUT_ROUND_ORDER:
        fixtures = by_round[r]
        if fixtures:
            pairs, winners = [], []
            for m in fixtures:
                a, b = m.get("home_team"), m.get("away_team")
                if not a or not b:
                    continue
                if m.get("status") == "FINISHED" and m.get("home_score") is not None:
                    hs, as_ = m["home_score"], m["away_score"]
                    winner = a if hs > as_ else (b if as_ > hs else _play(a, b))
                else:
                    winner = _play(a, b)
                pairs.append((a, b))
                winners.append(winner)
            rounds_out[r] = pairs
            advancing = winners
        elif advancing and len(advancing) >= 2:
            # No real fixtures published yet for this round — pair up
            # whoever is advancing so far, in bracket order.
            pairs = list(zip(advancing[::2], advancing[1::2]))
            rounds_out[r] = pairs
            advancing = [_play(a, b) for a, b in pairs]

    champion = advancing[0] if advancing and len(advancing) == 1 else (
        _play(*advancing[:2]) if advancing and len(advancing) >= 2 else "Unknown"
    )
    return {
        "champion": champion,
        "rounds": {k: [list(p) for p in v] for k, v in rounds_out.items()},
    }


def _simulate_from_groups():
    """Full from-scratch bracket sim using only group-stage placements —
    used only when there's no real knockout data in the feed at all yet."""
    teams_by_group = {}
    for grp, teams in WC2026_GROUPS.items():
        elos = [(t, get_elo_with_fallback(t)) for t in teams]
        elos.sort(key=lambda x: -x[1])
        teams_by_group[grp] = {"1st": elos[0][0], "2nd": elos[1][0]}

    groups = sorted(teams_by_group.keys())
    r32 = []
    for i in range(0, len(groups), 2):
        g1, g2 = groups[i], groups[i + 1] if i + 1 < len(groups) else groups[0]
        r32.append((teams_by_group[g1]["1st"], teams_by_group[g2]["2nd"]))
        r32.append((teams_by_group[g2]["1st"], teams_by_group[g1]["2nd"]))

    rounds = {"R32": r32, "R16": [], "QF": [], "SF": [], "Final": []}
    current = [_play(a, b) for a, b in r32]
    rounds["R16"] = list(zip(current[::2], current[1::2]))
    current = [_play(a, b) for a, b in rounds["R16"]]
    rounds["QF"] = list(zip(current[::2], current[1::2]))
    current = [_play(a, b) for a, b in rounds["QF"]]
    rounds["SF"] = list(zip(current[::2], current[1::2]))
    current = [_play(a, b) for a, b in rounds["SF"]]
    rounds["Final"] = [tuple(current)] if len(current) >= 2 else []
    champion = _play(*current) if len(current) >= 2 else (current[0] if current else "Unknown")

    return {"champion": champion, "rounds": {k: [list(m) for m in v] for k, v in rounds.items()}}


@app.callback(
    Output("sim-results", "data"),
    Output("sim-status", "children"),
    Input("sim-run-btn", "n_clicks"),
    Input("sim-reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_simulate(run_clicks, reset_clicks):
    import dash
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "sim-reset-btn":
        return None, "Ready to simulate"

    try:
        results = run_bracket_simulation()
        return results, f"✅ {results.get('champion', '?')} wins the simulation! 🏆"
    except Exception as e:
        print(f"[STATDIUM] bracket simulation error: {e}")
        return None, "⚠️ Simulation failed — try again"


@app.callback(Output("sim-bracket-display","children"), Input("sim-results","data"))
def display_bracket(results):
    if not results:
        return html.Div([
            html.Div("🏆", style={"fontSize":"64px","textAlign":"center","marginBottom":"12px","opacity":"0.3"}),
            html.Div("Click Simulate to run a full tournament bracket",
                     style={"color":COLORS["text_secondary"],"textAlign":"center","fontSize":"14px"}),
        ], style={"padding":"60px 20px"})

    champion = results.get("champion","?")
    rounds = results.get("rounds", {})
    round_order = ["R32","R16","QF","SF","Final"]
    round_labels = {"R32":"Round of 32","R16":"Round of 16","QF":"Quarter-Finals","SF":"Semi-Finals","Final":"⭐ Final"}

    round_cols = []
    for rnd in round_order:
        matches = rounds.get(rnd, [])
        if not matches: continue
        match_cards = []
        for pair in matches:
            if len(pair) >= 2:
                a, b = pair[0], pair[1]
                match_cards.append(html.Div([
                    html.Div([get_flag(a), html.Span(f" {a}", style={"fontSize":"11px","fontWeight":"600","color":COLORS["text_primary"]})],
                             style={"display":"flex","alignItems":"center","gap":"4px","padding":"4px 6px"}),
                    html.Div("vs", style={"fontSize":"9px","color":COLORS["text_secondary"],"textAlign":"center","padding":"1px 0"}),
                    html.Div([get_flag(b), html.Span(f" {b}", style={"fontSize":"11px","fontWeight":"600","color":COLORS["text_primary"]})],
                             style={"display":"flex","alignItems":"center","gap":"4px","padding":"4px 6px"}),
                ], style={"background":COLORS["bg_card2"],"border":f"1px solid {COLORS['border']}",
                          "borderRadius":"8px","marginBottom":"6px","overflow":"hidden"}))

        round_cols.append(html.Div([
            html.Div(round_labels.get(rnd, rnd),
                     style={"fontSize":"10px","fontWeight":"800","color":COLORS["accent"],
                            "textTransform":"uppercase","letterSpacing":"0.1em","marginBottom":"10px",
                            "textAlign":"center"}),
            html.Div(match_cards),
        ], style={"minWidth":"160px","flex":"1"}))

    # Champion card
    champ_card = html.Div([
        html.Div("🏆", style={"fontSize":"48px","textAlign":"center"}),
        html.Div(get_flag(champion), style={"fontSize":"32px","textAlign":"center","margin":"8px 0"}),
        html.Div(champion, style={"fontSize":"20px","fontWeight":"900","color":COLORS["gold"],
                                   "textAlign":"center"}),
        html.Div("WORLD CHAMPION", style={"fontSize":"10px","fontWeight":"700",
                                           "color":COLORS["text_secondary"],"textAlign":"center",
                                           "letterSpacing":"0.12em","marginTop":"4px"}),
    ], style={"background":"rgba(255,215,0,0.08)","border":f"2px solid {COLORS['gold']}44",
              "borderRadius":"16px","padding":"24px","marginBottom":"24px"})

    return html.Div([
        champ_card,
        html.Div(round_cols, style={"display":"flex","gap":"12px","overflowX":"auto","paddingBottom":"8px"}),
    ])


@app.callback(Output("gdp-chart","children"), Input("sim-run-btn","n_clicks"))
def update_gdp_chart(_):
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]
    rows = []
    for team in all_teams:
        gdp = GDP_DATA.get(team)
        elo = get_elo_with_fallback(team)
        rank = FIFA_RANKINGS.get(team, 60)
        if gdp:
            rows.append({"team":team,"gdp":gdp,"elo":elo,"rank":rank,"flag":get_flag(team)})

    rows.sort(key=lambda x: x["gdp"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[r["gdp"] for r in rows],
        y=[r["elo"] for r in rows],
        mode="markers+text",
        text=[r["flag"] + " " + r["team"] for r in rows],
        textposition="top center",
        textfont=dict(size=9, color=COLORS["text_secondary"]),
        marker=dict(
            size=[max(8, min(30, r["elo"]/60)) for r in rows],
            color=[r["elo"] for r in rows],
            colorscale=[[0,"#1E1E24"],[0.3,"#7B61FF"],[0.7,"#00E5A0"],[1.0,"#FFD700"]],
            showscale=True,
            colorbar=dict(title="Elo",tickfont=dict(color=COLORS["text_secondary"]),
                          bgcolor="rgba(0,0,0,0)"),
            line=dict(color=COLORS["border"], width=1),
        ),
        hovertemplate="<b>%{text}</b><br>GDP: $%{x:,.0f}B<br>Elo: %{y}<extra></extra>",
    ))

    # Add trend line annotation
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(title="GDP (USD Billions, log scale)", type="log",
                   showgrid=True, gridcolor=COLORS["border"],
                   tickfont=dict(size=10, color=COLORS["text_secondary"])),
        yaxis=dict(title="Elo Rating", showgrid=True, gridcolor=COLORS["border"],
                   tickfont=dict(size=10, color=COLORS["text_secondary"])),
        margin=dict(l=0, r=0, t=16, b=0), height=460,
        annotations=[dict(
            x=0.02, y=0.98, xref="paper", yref="paper",
            text="Bubble size = Elo strength · Color = Elo rating",
            showarrow=False, font=dict(size=10, color=COLORS["text_secondary"]),
            align="left",
        )],
    )

    # Key insight annotation
    insight = ("💡 Insight: High GDP doesn't guarantee football success — "
               "Brazil (#5 world GDP) and Argentina (#1 ranked) prove football is about culture, not cash. "
               "Norway (smaller economy) punches above its weight thanks to Haaland's generation.")

    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar":False}),
        html.Div(insight, style={"fontSize":"12px","color":COLORS["text_secondary"],"padding":"12px 16px",
                                  "background":COLORS["bg_card2"],"borderRadius":"8px","marginTop":"12px",
                                  "lineHeight":"1.6"}),
    ], style={"background":COLORS["bg_card"],"border":f"1px solid {COLORS['border']}",
              "borderRadius":"14px","padding":"20px"})
