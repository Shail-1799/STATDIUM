import random
from dash import html, dcc, Input, Output, State
from app_instance import app
from components.ui import page_guide, COLORS, section_header, page_wrapper
from data.fetcher import WC2026_GROUPS, get_flag, get_cache
from pages.history import WC_HISTORY, RESULT_LABEL, _team_2026_result

GUIDE = page_guide(
    "World Cup Trivia",
    [
        (
            "🧠",
            "Every question is generated live from the same historical dataset that powers the History page — nothing here is pre-written or hardcoded.",
        ),
        (
            "⚽",
            "Includes questions about the CURRENT tournament, using its live furthest-stage-reached data — these update automatically as the tournament progresses.",
        ),
        (
            "🏆",
            "Track your running score as you go. Hit 'New Question' any time to keep going.",
        ),
    ],
    accent_color=COLORS["gold"],
)

STAGE_TAGS = ["GS", "R16", "QF", "SF", "F", "W"]


def _year_to_champion():
    mapping = {}
    for team, hist in WC_HISTORY.items():
        for year, result in hist.items():
            if result == "W":
                mapping[year] = team
    return mapping


def _label(tag):
    return RESULT_LABEL.get(tag, tag)


def _distractor_teams(exclude, pool, n=3):
    candidates = [t for t in pool if t != exclude]
    return random.sample(candidates, min(n, len(candidates)))


def _distractor_tags(exclude, n=3):
    candidates = [t for t in STAGE_TAGS if t != exclude]
    return random.sample(candidates, min(n, len(candidates)))


def generate_question():
    """
    Builds one multiple-choice question, picking randomly from four question
    types. Everything is derived live from WC_HISTORY (and, for the current
    tournament, from the same live furthest-stage-reached logic the History
    page itself uses) — there's no separate hand-written question bank to
    keep in sync or let go stale.
    """
    all_historical_teams = list(WC_HISTORY.keys())
    year_champs = _year_to_champion()
    current_teams = sorted({t for teams in WC2026_GROUPS.values() for t in teams})

    question_types = ["who_won", "how_many_titles", "best_result"]
    if current_teams:
        question_types.append("current_2026")

    qtype = random.choice(question_types)

    if qtype == "who_won" and year_champs:
        year = random.choice(list(year_champs.keys()))
        correct = year_champs[year]
        distractors = _distractor_teams(correct, all_historical_teams)
        options = distractors + [correct]
        random.shuffle(options)
        return {
            "prompt": f"Which team won the {year} FIFA World Cup?",
            "options": options,
            "correct": correct,
            "display": lambda t: f"{get_flag(t)} {t}",
        }

    if qtype == "how_many_titles" and all_historical_teams:
        team = random.choice(all_historical_teams)
        count = sum(1 for v in WC_HISTORY[team].values() if v == "W")
        nearby = {max(0, count - 1), count, count + 1, count + 2}
        nearby.discard(count)
        options = [str(count)] + [str(n) for n in list(nearby)[:3]]
        options = list(dict.fromkeys(options))  # dedupe, keep order
        while len(options) < 4:
            options.append(str(max(0, count + len(options))))
        random.shuffle(options)
        return {
            "prompt": f"How many World Cups has {get_flag(team)} {team} won?",
            "options": options,
            "correct": str(count),
            "display": lambda t: t,
        }

    if qtype == "best_result":
        candidates = [
            (t, y, r)
            for t, hist in WC_HISTORY.items()
            for y, r in hist.items()
            if r in STAGE_TAGS
        ]
        if candidates:
            team, year, correct = random.choice(candidates)
            distractors = _distractor_tags(correct)
            options = distractors + [correct]
            random.shuffle(options)
            return {
                "prompt": f"What was {get_flag(team)} {team}'s furthest stage at the {year} World Cup?",
                "options": options,
                "correct": correct,
                "display": _label,
            }

    if qtype == "current_2026" and current_teams:
        matches = get_cache().get("matches", [])
        team = random.choice(current_teams)
        correct = _team_2026_result(team, matches)
        distractors = _distractor_tags(correct)
        options = distractors + [correct]
        random.shuffle(options)
        return {
            "prompt": f"How far has {get_flag(team)} {team} gone in the 2026 World Cup so far?",
            "options": options,
            "correct": correct,
            "display": _label,
        }

    # Fallback — should be unreachable given the guards above, but never
    # leave the quiz with nothing to show.
    return {
        "prompt": "Which team has won the most World Cup titles?",
        "options": ["Brazil", "Germany", "Argentina", "Italy"],
        "correct": "Brazil",
        "display": lambda t: t,
    }


def layout():
    return html.Div(
        [
            page_wrapper(
                [
                    GUIDE,
                    section_header(
                        "🧠 World Cup Trivia",
                        "Test your knowledge — every question generated live from real tournament data",
                        accent_color=COLORS["gold"],
                    ),
                    dcc.Store(id="trivia-question-store", data=None),
                    dcc.Store(id="trivia-score-store", data={"correct": 0, "total": 0}),
                    html.Div(
                        [
                            html.Div(
                                id="trivia-score-display",
                                style={
                                    "fontSize": "14px",
                                    "fontWeight": "700",
                                    "color": COLORS["gold"],
                                    "marginBottom": "16px",
                                },
                            ),
                            html.Div(
                                id="trivia-question-display",
                                style={
                                    "fontSize": "17px",
                                    "fontWeight": "700",
                                    "color": COLORS["text_primary"],
                                    "marginBottom": "16px",
                                    "lineHeight": "1.5",
                                },
                            ),
                            dcc.RadioItems(
                                id="trivia-options",
                                options=[],
                                value=None,
                                labelStyle={
                                    "display": "block",
                                    "padding": "10px 14px",
                                    "marginBottom": "8px",
                                    "backgroundColor": (
                                        COLORS["bg_card2"]
                                        if "bg_card2" in COLORS
                                        else COLORS["bg_card"]
                                    ),
                                    "borderRadius": "8px",
                                    "cursor": "pointer",
                                    "fontSize": "14px",
                                },
                            ),
                            html.Div(
                                id="trivia-feedback",
                                style={
                                    "marginTop": "12px",
                                    "fontSize": "14px",
                                    "fontWeight": "700",
                                },
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Submit Answer",
                                        id="trivia-submit-btn",
                                        n_clicks=0,
                                        style={
                                            "background": COLORS["accent"],
                                            "border": "none",
                                            "borderRadius": "10px",
                                            "color": "#000",
                                            "fontWeight": "800",
                                            "fontSize": "14px",
                                            "padding": "12px 24px",
                                            "cursor": "pointer",
                                            "marginRight": "12px",
                                        },
                                    ),
                                    html.Button(
                                        "New Question ▶",
                                        id="trivia-next-btn",
                                        n_clicks=0,
                                        style={
                                            "background": "transparent",
                                            "border": f"1px solid {COLORS['border']}",
                                            "borderRadius": "10px",
                                            "color": COLORS["text_secondary"],
                                            "fontSize": "14px",
                                            "padding": "12px 24px",
                                            "cursor": "pointer",
                                        },
                                    ),
                                ],
                                style={"marginTop": "20px"},
                            ),
                        ],
                        style={
                            "backgroundColor": COLORS["bg_card"],
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "14px",
                            "padding": "28px",
                            "maxWidth": "640px",
                        },
                    ),
                ]
            ),
        ]
    )


@app.callback(
    Output("trivia-question-store", "data"),
    Output("trivia-question-display", "children"),
    Output("trivia-options", "options"),
    Output("trivia-options", "value"),
    Output("trivia-feedback", "children"),
    Input("trivia-next-btn", "n_clicks"),
)
def new_question(_):
    q = generate_question()
    display_fn = q["display"]
    return (
        {"correct": q["correct"]},
        q["prompt"],
        [{"label": display_fn(opt), "value": opt} for opt in q["options"]],
        None,
        "",
    )


@app.callback(
    Output("trivia-feedback", "children", allow_duplicate=True),
    Output("trivia-score-store", "data"),
    Output("trivia-score-display", "children"),
    Input("trivia-submit-btn", "n_clicks"),
    State("trivia-options", "value"),
    State("trivia-question-store", "data"),
    State("trivia-score-store", "data"),
    prevent_initial_call=True,
)
def check_answer(_, selected, question_data, score):
    score = score or {"correct": 0, "total": 0}
    if not question_data or selected is None:
        return "Pick an answer first!", score, _score_text(score)

    correct = question_data["correct"]
    score = dict(score)
    score["total"] += 1
    if selected == correct:
        score["correct"] += 1
        feedback = html.Span("✅ Correct!", style={"color": COLORS["accent"]})
    else:
        feedback = html.Span(
            f"❌ Not quite — the answer was {RESULT_LABEL.get(correct, correct)}",
            style={"color": COLORS.get("live_red", "#FF4D4D")},
        )
    return feedback, score, _score_text(score)


def _score_text(score):
    total = score.get("total", 0)
    correct = score.get("correct", 0)
    pct = round(correct / total * 100) if total else 0
    return f"Score: {correct}/{total} ({pct}%)" if total else "Score: 0/0"


@app.callback(
    Output("trivia-score-display", "children", allow_duplicate=True),
    Input("trivia-score-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def sync_score_display(score):
    return _score_text(score or {"correct": 0, "total": 0})
