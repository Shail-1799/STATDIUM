"""
STATDIUM — Monte Carlo Bracket Simulator
10,000 simulations → win probabilities per team per round
"""

import numpy as np
from data.fetcher import get_cache, WC2026_GROUPS, FIFA_RANKINGS, get_flag


def get_team_strength(team, group_table=None):
    rank = FIFA_RANKINGS.get(team, 65)
    rank_score = max(0.0, 1.0 - (rank - 1) / 90.0)
    form_score = 0.0
    if group_table:
        for grp_teams in group_table.values():
            if team in grp_teams:
                t = grp_teams[team]
                pts = t.get("pts", 0)
                gd  = t.get("gf", 0) - t.get("ga", 0)
                form_score = min(1.0, (pts / 9.0) * 0.7 + max(0, gd / 10.0) * 0.3)
                break
    return 0.6 * rank_score + 0.4 * form_score


def win_prob(sa, sb):
    return 1.0 / (1.0 + 10 ** ((sb - sa) * 5))


def simulate_match(team_a, team_b, strength_map):
    sa = strength_map.get(team_a, 0.3)
    sb = strength_map.get(team_b, 0.3)
    return team_a if np.random.random() < win_prob(sa, sb) else team_b


def simulate_group(teams, strength_map):
    points = {t: 0 for t in teams}
    gd     = {t: 0 for t in teams}
    fixtures = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    for a, b in fixtures:
        sa = strength_map.get(a, 0.3)
        sb = strength_map.get(b, 0.3)
        pa = win_prob(sa, sb)
        r = np.random.random()
        win_threshold = pa * 0.65
        lose_threshold = 1 - (1 - pa) * 0.65
        if r < win_threshold:
            points[a] += 3
            goals = np.random.randint(1, 4)
            gd[a] += goals; gd[b] -= goals
        elif r > lose_threshold:
            points[b] += 3
            goals = np.random.randint(1, 4)
            gd[b] += goals; gd[a] -= goals
        else:
            points[a] += 1; points[b] += 1
    ranked = sorted(teams, key=lambda t: (points[t], gd[t]), reverse=True)
    return ranked[:2], ranked[2] if len(ranked) > 2 else None


def run_simulation(n_sims=5000):
    cache = get_cache()
    group_table = cache.get("groups", {})
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]
    strength_map = {t: get_team_strength(t, group_table) for t in all_teams}

    stages = ["r32", "qf", "sf", "final", "winner"]
    tally  = {t: {s: 0 for s in stages} for t in all_teams}

    rng = np.random.default_rng(seed=None)

    for _ in range(n_sims):
        group_winners  = {}
        group_runners  = {}
        third_places   = []

        for letter, teams in WC2026_GROUPS.items():
            top2, third = simulate_group(teams, strength_map)
            group_winners[letter] = top2[0]
            group_runners[letter] = top2[1]
            if third:
                third_places.append(third)

        # Best 8 of 12 third-place teams (by strength as proxy)
        third_sorted = sorted(third_places, key=lambda t: strength_map.get(t, 0), reverse=True)
        wild_cards = third_sorted[:8]

        r32_teams = list(group_winners.values()) + list(group_runners.values()) + wild_cards

        for t in r32_teams:
            if t in tally:
                tally[t]["r32"] += 1

        # Knockout bracket
        bracket = r32_teams[:32]
        rng.shuffle(bracket)

        current = bracket[:]
        for stage in ["qf", "sf", "final", "winner"]:
            if len(current) < 2:
                break
            next_round = []
            for i in range(0, len(current) - 1, 2):
                w = simulate_match(current[i], current[i+1], strength_map)
                next_round.append(w)
                if w in tally:
                    tally[w][stage] += 1
            current = next_round

    results = {}
    for team in all_teams:
        results[team] = {
            s: round(tally[team][s] / n_sims * 100, 1)
            for s in stages
        }
        results[team]["strength"] = round(strength_map.get(team, 0) * 100, 1)

    return results


def get_qualification_status(group_letter, teams, group_table):
    """
    Returns sorted team status list for qualification scenario text:
    [{"team":..., "flag":..., "pts":..., "gd":..., "p":...}, ...] sorted by pts/gd
    """
    from data.fetcher import get_flag
    group_key = f"Group {group_letter}"
    table_data = group_table.get(group_key, {})

    status = []
    for t in teams:
        if t in table_data:
            d = table_data[t]
            status.append({
                "team": t, "flag": get_flag(t),
                "pts": d.get("pts", 0),
                "gd": d.get("gf", 0) - d.get("ga", 0),
                "p": d.get("p", 0),
            })
        else:
            status.append({"team": t, "flag": get_flag(t), "pts": 0, "gd": 0, "p": 0})

    status.sort(key=lambda x: (x["pts"], x["gd"]), reverse=True)
    return status


def get_progression_sankey_data(n_sims=3000):
    """
    Build Sankey diagram data: how teams flow through tournament stages.
    Returns (labels, source_indices, target_indices, values, colors)
    """
    from data.fetcher import get_cache, WC2026_GROUPS, get_flag

    cache = get_cache()
    group_table = cache.get("groups", {})
    all_teams = [t for teams in WC2026_GROUPS.values() for t in teams]
    strength_map = {t: get_team_strength(t, group_table) for t in all_teams}

    stages = ["Group Stage", "Round of 32", "Quarter-finals", "Semi-finals", "Final", "Champion"]

    # Tally flows between consecutive stages
    flow_counts = {}  # (team, from_stage, to_stage) -> count
    elim_counts = {}  # (stage, "Eliminated") -> count of teams eliminated at that stage

    for _ in range(n_sims):
        group_winners, group_runners, third_places = {}, {}, []
        for letter, teams in WC2026_GROUPS.items():
            top2, third = simulate_group(teams, strength_map)
            group_winners[letter] = top2[0]
            group_runners[letter] = top2[1]
            if third: third_places.append(third)

        third_sorted = sorted(third_places, key=lambda t: strength_map.get(t, 0), reverse=True)
        wild_cards = third_sorted[:8]
        r32 = list(group_winners.values()) + list(group_runners.values()) + wild_cards

        current = r32[:32]
        np.random.shuffle(current)

        all_teams_set = set(all_teams)
        eliminated_in_groups = all_teams_set - set(current)
        for t in eliminated_in_groups:
            elim_counts[("Group Stage", "Eliminated")] = elim_counts.get(("Group Stage","Eliminated"), 0) + 1

        stage_names = ["Round of 32", "Quarter-finals", "Semi-finals", "Final"]
        for stage_idx, stage in enumerate(stage_names):
            if len(current) < 2:
                break
            next_round = []
            for i in range(0, len(current)-1, 2):
                winner = simulate_match(current[i], current[i+1], strength_map)
                loser = current[i] if winner == current[i+1] else current[i+1]
                next_round.append(winner)
                elim_counts[(stage, "Eliminated")] = elim_counts.get((stage,"Eliminated"), 0) + 1
            current = next_round
        if current:
            elim_counts[("Final", "Champion")] = elim_counts.get(("Final","Champion"), 0) + 1

    # Build simplified Sankey: Group Stage -> R32 -> QF -> SF -> Final -> Champion, plus Eliminated branches
    labels = ["Group Stage", "Round of 32", "Quarter-finals", "Semi-finals", "Final", "Champion", "Eliminated"]
    label_idx = {l: i for i, l in enumerate(labels)}

    n_teams = 48
    r32_count = 32
    qf_count = 16
    sf_count = 8
    final_count = 4
    champ_count = 1

    sources, targets, values, colors = [], [], [], []

    # Group Stage -> R32 / Eliminated
    sources += [label_idx["Group Stage"], label_idx["Group Stage"]]
    targets += [label_idx["Round of 32"], label_idx["Eliminated"]]
    values  += [r32_count, n_teams - r32_count]
    colors  += ["rgba(0,229,160,0.4)", "rgba(255,69,58,0.25)"]

    # R32 -> QF / Eliminated
    sources += [label_idx["Round of 32"], label_idx["Round of 32"]]
    targets += [label_idx["Quarter-finals"], label_idx["Eliminated"]]
    values  += [qf_count, r32_count - qf_count]
    colors  += ["rgba(0,229,160,0.4)", "rgba(255,69,58,0.25)"]

    # QF -> SF / Eliminated
    sources += [label_idx["Quarter-finals"], label_idx["Quarter-finals"]]
    targets += [label_idx["Semi-finals"], label_idx["Eliminated"]]
    values  += [sf_count, qf_count - sf_count]
    colors  += ["rgba(123,97,255,0.4)", "rgba(255,69,58,0.25)"]

    # SF -> Final / Eliminated
    sources += [label_idx["Semi-finals"], label_idx["Semi-finals"]]
    targets += [label_idx["Final"], label_idx["Eliminated"]]
    values  += [final_count, sf_count - final_count]
    colors  += ["rgba(255,107,53,0.4)", "rgba(255,69,58,0.25)"]

    # Final -> Champion / Eliminated (runner-up)
    sources += [label_idx["Final"], label_idx["Final"]]
    targets += [label_idx["Champion"], label_idx["Eliminated"]]
    values  += [champ_count, final_count - champ_count]
    colors  += ["rgba(255,215,0,0.5)", "rgba(255,69,58,0.25)"]

    return labels, sources, targets, values, colors
