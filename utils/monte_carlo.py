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
