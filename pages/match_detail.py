# pyrefly: ignore [missing-import]
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import random
import dash
from app_instance import app
from components.ui import COLORS, section_header, page_wrapper, live_badge
from data.fetcher import get_cache, FIFA_RANKINGS, get_flag
from data.enrichment import fetch_stadium_weather, get_match_venue_coords, STADIUM_CAPACITIES, fetch_country_profile
from data.ai_insights import generate_match_preview, generate_match_recap
from pages.formations import POSITIONS, TEAM_FORMS

# Predefined squads for major teams to show realistic player names
SQUADS = {
    "Argentina": ["E. Martinez", "C. Romero", "N. Otamendi", "N. Tagliafico", "N. Molina", "R. De Paul", "E. Fernandez", "A. Mac Allister", "L. Messi", "J. Alvarez", "A. Di Maria", "G. Lo Celso", "L. Paredes", "L. Martinez", "A. Garnacho"],
    "Brazil": ["Alisson", "Marquinhos", "Gabriel", "Danilo", "W. Arana", "B. Guimaraes", "J. Gomes", "L. Paqueta", "Vinicius Jr.", "Rodrygo", "Raphinha", "Endrick", "Casemiro", "E. Militao", "G. Martinelli"],
    "France": ["M. Maignan", "W. Saliba", "D. Upamecano", "T. Hernandez", "J. Kounde", "A. Tchouameni", "A. Rabiot", "A. Griezmann", "O. Dembele", "K. Mbappe", "M. Thuram", "O. Giroud", "K. Coman", "E. Camavinga", "R. Kolo Muani"],
    "England": ["J. Pickford", "J. Stones", "K. Walker", "M. Guehi", "K. Trippier", "D. Rice", "K. Mainoo", "J. Bellingham", "B. Saka", "P. Foden", "H. Kane", "C. Palmer", "O. Watkins", "A. Gordon", "T. Alexander-Arnold"],
    "Germany": ["M. Neuer", "A. Rudiger", "J. Tah", "J. Kimmich", "M. Mittelstadt", "T. Kroos", "R. Andrich", "J. Musiala", "I. Gundogan", "F. Wirtz", "K. Havertz", "N. Fullkrug", "L. Sane", "T. Muller", "N. Schlotterbeck"],
    "Spain": ["U. Simon", "A. Laporte", "R. Le Normand", "D. Carvajal", "M. Cucurella", "Rodri", "F. Ruiz", "Pedri", "L. Yamal", "N. Williams", "A. Morata", "D. Olmo", "F. Torres", "Joselu", "A. Grimaldo"],
    "Portugal": ["D. Costa", "R. Dias", "Pepe", "J. Cancelo", "N. Mendes", "J. Palhinha", "Vitinha", "B. Fernandes", "B. Silva", "R. Leao", "C. Ronaldo", "J. Felix", "D. Jota", "M. Nunes", "R. Neves"],
    "USA": ["M. Turner", "T. Ream", "C. Richards", "A. Robinson", "J. Scally", "W. McKennie", "T. Adams", "Y. Musah", "C. Pulisic", "F. Balogun", "T. Weah", "G. Reyna", "R. Pepi", "C. Carter-Vickers", "J. Cardoso"],
    "Mexico": ["G. Ochoa", "C. Montes", "J. Vasquez", "J. Sanchez", "G. Arteaga", "E. Alvarez", "L. Chavez", "O. Pineda", "S. Gimenez", "J. Quinones", "U. Antuna", "H. Martin", "A. Vega", "L. Romo", "E. Sanchez"],
    "South Africa": ["R. Williams", "K. Mudau", "M. Mvala", "G. Kekana", "A. Modiba", "T. Mokoena", "S. Sithole", "T. Zwane", "T. Morena", "P. Tau", "E. Makgopa", "Z. Lepasa", "M. Mayambela", "S. Monare", "S. Xulu"],
    "South Korea": ["Kim Seung-gyu", "Kim Min-jae", "Kim Young-gwon", "Kim Jin-su", "Seol Young-woo", "Hwang In-beom", "Park Yong-woo", "Lee Jae-sung", "Lee Kang-in", "Son Heung-min", "Hwang Hee-chan", "Cho Gue-sung", "Oh Hyeon-gyu", "Hong Hyun-seok", "Lee Ki-je"],
    "Canada": ["M. Crepeau", "K. Miller", "D. Bombito", "A. Johnston", "A. Davies", "I. Kone", "S. Eustaquio", "L. Millar", "J. David", "C. Larin", "T. Buchanan", "J. Shaffelburg", "J. Osorio", "R. Laryea", "A. Ahmed"],
    "Saudi Arabia": ["M. Al-Owais", "A. Al-Bulaihi", "A. Lajami", "H. Al-Tambakti", "Y. Al-Shahrani", "S. Abdulhamid", "M. Kanno", "F. Al-Ghamdi", "F. Al-Muwallad", "S. Al-Dawsari", "S. Al-Shehri", "F. Al-Buraikan", "A. Ghareeb", "A. Al-Hassan", "M. Al-Breik"],
    "Japan": ["Z. Suzuki", "K. Itakura", "S. Taniguchi", "R. Suga", "D. Maeda", "W. Endo", "H. Morita", "R. Doan", "T. Minamino", "K. Mitoma", "A. Ueda", "T. Kubo", "J. Ito", "K. Machida", "D. Kamada"],
    "Netherlands": ["B. Verbruggen", "V. van Dijk", "S. de Vrij", "N. Ake", "D. Dumfries", "J. Schouten", "T. Reijnders", "X. Simons", "J. Frimpong", "C. Gakpo", "M. Depay", "W. Weghorst", "D. Malen", "M. de Ligt", "R. Gravenberch"],
    "Italy": ["G. Donnarumma", "A. Bastoni", "R. Calafiori", "G. Di Lorenzo", "F. Dimarco", "N. Barella", "Jorginho", "D. Frattesi", "F. Chiesa", "G. Scamacca", "L. Pellegrini", "M. Retegui", "G. Raspadori", "M. Darmian", "A. Buongiorno"],
    "Uruguay": ["S. Rochet", "R. Araujo", "J. Gimenez", "M. Olivera", "G. Varela", "F. Valverde", "M. Ugarte", "R. Bentancur", "F. Pellistri", "D. Nunez", "M. Araujo", "L. Suarez", "N. De la Cruz", "S. Caceres", "N. Nandez"],
    "Morocco": ["Y. Bounou", "R. Saiss", "N. Aguerd", "A. Hakimi", "N. Mazraoui", "S. Amrabat", "A. Ounahi", "S. Amallah", "H. Ziyech", "S. Boufal", "Y. En-Nesyri", "B. Diaz", "A. El Kaabi", "A. Adli", "Y. Abdelhamid"],
    "Croatia": ["D. Livakovic", "J. Gvardiol", "J. Sutalo", "J. Stanisic", "B. Sosa", "L. Modric", "M. Kovacic", "M. Brozovic", "M. Pasalic", "A. Kramaric", "I. Perisic", "B. Petkovic", "L. Majer", "A. Budimir", "M. Erlic"],
    "Belgium": ["K. Casteels", "J. Vertonghen", "W. Faes", "T. Castagne", "A. Theate", "A. Onana", "O. Mangala", "K. De Bruyne", "J. Doku", "L. Trossard", "R. Lukaku", "J. Bakayoko", "L. Openda", "Y. Carrasco", "C. De Ketelaere"],
}

FORMATION_LABELS = {
    "4-3-3": ["GK", "LB", "LCB", "RCB", "RB", "LCM", "CM", "RCM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "LCB", "RCB", "RB", "LM", "LCM", "RCM", "RM", "LST", "RST"],
    "4-2-3-1": ["GK", "LB", "LCB", "RCB", "RB", "LDM", "RDM", "LM", "AM", "RM", "ST"],
    "3-5-2": ["GK", "LCB", "CB", "RCB", "LWB", "LCM", "CM", "RCM", "RWB", "LST", "RST"],
    "5-3-2": ["GK", "LWB", "LCB", "CB", "RCB", "RWB", "LCM", "CM", "RCM", "LST", "RST"],
}

def get_team_preferred_formation(team_name, match_id):
    """Fetch the formation the team played (or will play) the match in"""
    if team_name in TEAM_FORMS:
        return TEAM_FORMS[team_name]
    # Deterministic fallback based on team and match
    rng = random.Random(f"formation_{team_name}_{match_id}")
    return rng.choice(["4-3-3", "4-4-2", "4-2-3-1"])

def get_formation_coords(formation_name, team_side):
    """Map the vertical pitch coordinates to the horizontal layout coordinates"""
    raw_coords = POSITIONS.get(formation_name, POSITIONS["4-3-3"])
    coords = []
    for x_raw, y_raw in raw_coords:
        # Translate to horizontal layout (x=GK to FW, y=LB to RB)
        x_pos = 6.0 + (1.0 - y_raw) * 40.0
        
        if team_side == "home":
            y_pos = x_raw * 100.0
        else:
            x_pos = 100.0 - x_pos
            y_pos = (1.0 - x_raw) * 100.0
            
        coords.append((x_pos, y_pos))
    return coords

def get_squad(country_name, match_id, formation="4-3-3"):
    """Deterministically generate starting XI and subs for a country based on match seed and formation"""
    rng = random.Random(f"squad_{country_name}_{match_id}")
    if country_name in SQUADS:
        names = list(SQUADS[country_name])
    else:
        # Generate plausible names
        common_surnames = ["Gomez", "Silva", "Santos", "Smith", "Johnson", "Müller", "Weber", "Dupont", "Martin", "Rossi", "Bianchi", "Ivanov", "Petrov", "Kim", "Lee", "Ali", "Hassan", "Mensah", "Osei", "Tanaka", "Sato", "Hwang", "Al-Farsi", "Al-Sudairy", "O'Connor", "Murphy"]
        names = []
        for i in range(15):
            init = chr(rng.randint(65, 90))
            sur = rng.choice(common_surnames)
            names.append(f"{init}. {sur}")
            
    starters_names = names[:11]
    subs = names[11:]
    
    # Map starting players to positions of the formation
    labels = FORMATION_LABELS.get(formation, FORMATION_LABELS["4-3-3"])
    
    starters = {}
    for idx, p_name in enumerate(starters_names):
        role = labels[idx] if idx < len(labels) else "SUB"
        starters[p_name] = role
        
    return starters, subs

def simulate_events(match):
    """Deterministically simulate match events (goals, cards, subs) seeded by match ID"""
    rng = random.Random(f"events_{match['id']}")
    home = match["home_team"]
    away = match["away_team"]
    h_score = match.get("home_score", 0) or 0
    a_score = match.get("away_score", 0) or 0
    
    h_form = get_team_preferred_formation(home, match["id"])
    a_form = get_team_preferred_formation(away, match["id"])
    home_starters, home_subs = get_squad(home, match["id"], h_form)
    away_starters, away_subs = get_squad(away, match["id"], a_form)
    
    home_outfield = [p for p, pos in home_starters.items() if pos != "GK"]
    away_outfield = [p for p, pos in away_starters.items() if pos != "GK"]
    
    events = []
    
    # Goals
    for _ in range(h_score):
        scorer = rng.choice(home_outfield)
        minute = rng.randint(1, 90)
        assist = rng.choice([p for p in home_outfield if p != scorer] + [None])
        events.append({
            "type": "goal",
            "team": "home",
            "player": scorer,
            "minute": minute,
            "detail": f"Assist: {assist}" if assist else "Unassisted"
        })
        
    for _ in range(a_score):
        scorer = rng.choice(away_outfield)
        minute = rng.randint(1, 90)
        assist = rng.choice([p for p in away_outfield if p != scorer] + [None])
        events.append({
            "type": "goal",
            "team": "away",
            "player": scorer,
            "minute": minute,
            "detail": f"Assist: {assist}" if assist else "Unassisted"
        })
        
    # Yellow Cards
    num_yellows = rng.randint(1, 4)
    for _ in range(num_yellows):
        team = rng.choice(["home", "away"])
        outfield = home_outfield if team == "home" else away_outfield
        player = rng.choice(outfield)
        minute = rng.randint(5, 90)
        events.append({
            "type": "yellow_card",
            "team": team,
            "player": player,
            "minute": minute,
            "detail": "Foul"
        })
        
    # Red Cards (rare)
    if rng.random() < 0.08:
        team = rng.choice(["home", "away"])
        outfield = home_outfield if team == "home" else away_outfield
        player = rng.choice(outfield)
        minute = rng.randint(45, 90)
        events.append({
            "type": "red_card",
            "team": team,
            "player": player,
            "minute": minute,
            "detail": "Violent Conduct"
        })
        
    # Substitutions
    for team in ["home", "away"]:
        outfield = home_outfield if team == "home" else away_outfield
        subs = home_subs if team == "home" else away_subs
        for i in range(min(2, len(subs))):
            player_out = rng.choice(outfield)
            player_in = subs[i]
            minute = rng.randint(55, 88)
            events.append({
                "type": "substitution",
                "team": team,
                "player": f"{player_in} (IN) / {player_out} (OUT)",
                "minute": minute,
                "detail": "Tactical"
            })
            
    return sorted(events, key=lambda x: x["minute"])

def simulate_stats(match):
    """Deterministically simulate match statistics seeded by match ID"""
    rng = random.Random(f"stats_{match['id']}")
    h_score = match.get("home_score", 0) or 0
    a_score = match.get("away_score", 0) or 0
    
    possession_home = rng.randint(40, 60)
    if h_score > a_score:
        possession_home = rng.randint(45, 65)
    elif a_score > h_score:
        possession_home = rng.randint(35, 55)
    possession_away = 100 - possession_home
    
    shots_home = rng.randint(6, 18) + h_score
    shots_away = rng.randint(6, 18) + a_score
    
    sot_home = min(shots_home, rng.randint(1, 5) + h_score)
    sot_away = min(shots_away, rng.randint(1, 5) + a_score)
    
    fouls_home = rng.randint(8, 16)
    fouls_away = rng.randint(8, 16)
    
    corners_home = rng.randint(2, 9)
    corners_away = rng.randint(2, 9)
    
    offsides_home = rng.randint(0, 4)
    offsides_away = rng.randint(0, 4)
    
    saves_home = max(0, sot_away - a_score)
    saves_away = max(0, sot_home - h_score)
    
    pass_home = rng.randint(75, 90)
    pass_away = rng.randint(75, 90)
    
    return {
        "Possession": (possession_home, possession_away, "%"),
        "Shots": (shots_home, shots_away, ""),
        "Shots on Target": (sot_home, sot_away, ""),
        "Pass Accuracy": (pass_home, pass_away, "%"),
        "Fouls": (fouls_home, fouls_away, ""),
        "Corners": (corners_home, corners_away, ""),
        "Offsides": (offsides_home, offsides_away, ""),
        "Saves": (saves_home, saves_away, ""),
    }

def get_match_by_id(match_id):
    """Look up a match from the central cache"""
    matches = get_cache().get("matches", [])
    for m in matches:
        if m["id"] == match_id:
            return m
    return None

def stat_row(label, home_val, away_val, suffix=""):
    total = home_val + away_val if (home_val + away_val) > 0 else 1
    home_pct = (home_val / total) * 100
    away_pct = (away_val / total) * 100
    
    return html.Div([
        html.Div([
            html.Span(f"{home_val}{suffix}", style={"fontWeight":"700", "color": COLORS["accent"]}),
            html.Span(label, style={"color": COLORS["text_secondary"], "fontSize":"12px", "fontWeight":"500"}),
            html.Span(f"{away_val}{suffix}", style={"fontWeight":"700", "color": COLORS["accent2"]}),
        ], style={"display":"flex", "justifyContent":"space-between", "marginBottom":"6px"}),
        html.Div([
            html.Div(style={"width": f"{home_pct}%", "height":"100%", "background": f"linear-gradient(90deg, {COLORS['accent']}99, {COLORS['accent']})", "borderRadius":"3px 0 0 3px"}),
            html.Div(style={"width": f"{away_pct}%", "height":"100%", "background": f"linear-gradient(90deg, {COLORS['accent2']}, {COLORS['accent2']}99)", "borderRadius":"0 3px 3px 0"}),
        ], style={"height":"6px", "background":"#1E1E24", "borderRadius":"3px", "display":"flex", "overflow":"hidden", "marginBottom":"16px"}),
    ])

def render_tab_view(tab_name, match):
    home = match["home_team"]
    away = match["away_team"]
    status = match.get("status", "SCHEDULED")
    
    if tab_name == "overview":
        if status in ("FINISHED", "LIVE"):
            events = simulate_events(match)
            
            # Events Vertical Timeline
            timeline_items = []
            for ev in events:
                is_home = ev["team"] == "home"
                icon = "⚽" if ev["type"] == "goal" else ("🟨" if ev["type"] == "yellow_card" else ("🟥" if ev["type"] == "red_card" else "🔄"))
                
                left_content = html.Div([
                    html.Div(ev["player"], style={"fontWeight":"600", "color": COLORS["text_primary"], "fontSize":"13px"}),
                    html.Div(ev["detail"], style={"color": COLORS["text_secondary"], "fontSize":"11px"}),
                ], style={"textAlign":"right"}) if is_home else html.Div()
                
                right_content = html.Div([
                    html.Div(ev["player"], style={"fontWeight":"600", "color": COLORS["text_primary"], "fontSize":"13px"}),
                    html.Div(ev["detail"], style={"color": COLORS["text_secondary"], "fontSize":"11px"}),
                ], style={"textAlign":"left"}) if not is_home else html.Div()
                
                timeline_items.append(html.Div([
                    html.Div(left_content, style={"flex":"1", "paddingRight":"16px"}),
                    html.Div([
                        html.Div(f"{ev['minute']}'", style={"fontSize":"11px", "fontWeight":"700", "color": COLORS["accent3"], "marginBottom":"2px"}),
                        html.Div(icon, style={"fontSize":"16px"}),
                    ], style={"display":"flex", "flexDirection":"column", "alignItems":"center", "minWidth":"48px", "zIndex":"2"}),
                    html.Div(right_content, style={"flex":"1", "paddingLeft":"16px"}),
                ], style={"display":"flex", "alignItems":"center", "marginBottom":"20px", "position":"relative"}))
            
            timeline_view = html.Div([
                html.Div(style={"position":"absolute", "top":"0", "bottom":"0", "left":"50%", "width":"2px", "backgroundColor": COLORS["border"], "transform":"translateX(-50%)", "zIndex":"1"}),
                html.Div(timeline_items)
            ], style={"position":"relative", "padding":"20px 0"})
            
            # AI Recap
            recap_text = generate_match_recap(home, away, match.get("home_score", 0), match.get("away_score", 0))
            
            return html.Div([
                section_header("Match Timeline", "Chronological flow of key events (simulated)"),
                html.Div(timeline_view, className="glow-card", style={"padding":"24px", "backgroundColor": COLORS["bg_card"], "marginBottom":"24px"}),
                
                section_header("AI Recap", "Natural language summary"),
                html.Div([
                    html.Div("🤖 AI Commentary", style={"fontSize":"10px","fontWeight":"700","color":COLORS["accent2"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"6px"}),
                    html.Div(recap_text, style={"fontSize":"13px","color":COLORS["text_secondary"],"lineHeight":"1.6"}),
                    html.Div("Note: Detailed timelines and statistics are generated to represent realistic match patterns.", style={"fontSize":"10px", "color": COLORS["text_secondary"], "marginTop":"12px", "fontStyle":"italic"})
                ], className="glow-card", style={"backgroundColor": COLORS["bg_card2"], "padding":"16px 20px"})
            ])
        else:
            # Scheduled Match Preview & Predictions
            h_rank = FIFA_RANKINGS.get(home, 60)
            a_rank = FIFA_RANKINGS.get(away, 60)
            gap = abs(h_rank - a_rank)
            
            # Predict Win Probabilities
            home_prob = max(10, min(80, 38 + (a_rank - h_rank) * 1.2))
            away_prob = max(10, min(80, 38 + (h_rank - a_rank) * 1.2))
            draw_prob = round(100 - home_prob - away_prob)
            home_prob = round(home_prob)
            away_prob = round(away_prob)
            
            # Predict text
            preview_text = generate_match_preview(home, away, h_rank, a_rank, None, None, gap * 2.5, match_id=match["id"])
            
            return html.Div([
                section_header("Match Preview", "Predictions & Analysis"),
                html.Div([
                    html.Div("📋 Pre-match Report", style={"fontSize":"10px","fontWeight":"700","color":COLORS["accent2"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"8px"}),
                    html.Div(preview_text, style={"fontSize":"13px","color":COLORS["text_secondary"],"lineHeight":"1.6", "marginBottom":"20px"}),
                    
                    html.Div("Win Probabilities", style={"fontSize":"12px", "fontWeight":"700", "color": COLORS["text_primary"], "marginBottom":"10px"}),
                    html.Div([
                        html.Div(f"{home_prob}% {home} Win", style={"width":f"{home_prob}%", "height":"100%", "backgroundColor": COLORS["accent"], "color":"#000", "fontSize":"11px", "fontWeight":"800", "display":"flex", "alignItems":"center", "justifyContent":"center", "whiteSpace":"nowrap"}),
                        html.Div(f"{draw_prob}% Draw", style={"width":f"{draw_prob}%", "height":"100%", "backgroundColor": COLORS["draw_gray"], "color":"#fff", "fontSize":"11px", "fontWeight":"700", "display":"flex", "alignItems":"center", "justifyContent":"center", "whiteSpace":"nowrap"}),
                        html.Div(f"{away_prob}% {away} Win", style={"width":f"{away_prob}%", "height":"100%", "backgroundColor": COLORS["accent2"], "color":"#fff", "fontSize":"11px", "fontWeight":"800", "display":"flex", "alignItems":"center", "justifyContent":"center", "whiteSpace":"nowrap"}),
                    ], style={"height":"26px", "borderRadius":"6px", "display":"flex", "overflow":"hidden", "boxShadow":"0 4px 12px rgba(0,0,0,0.3)"}),
                    
                    html.Div([
                        html.Div([
                            html.Span("FIFA Rank: ", style={"color":COLORS["text_secondary"]}),
                            html.Span(f"#{h_rank}", style={"fontWeight":"700", "color":COLORS["accent"]})
                        ], style={"fontSize":"12px"}),
                        html.Div([
                            html.Span("FIFA Rank: ", style={"color":COLORS["text_secondary"]}),
                            html.Span(f"#{a_rank}", style={"fontWeight":"700", "color":COLORS["accent2"]})
                        ], style={"fontSize":"12px"}),
                    ], style={"display":"flex", "justifyContent":"space-between", "marginTop":"12px"})
                ], className="glow-card", style={"padding":"20px", "backgroundColor": COLORS["bg_card"], "marginBottom":"24px"})
            ])
            
    elif tab_name == "stats":
        stats = simulate_stats(match)
        stat_rows = []
        for label, (home_val, away_val, suffix) in stats.items():
            stat_rows.append(stat_row(label, home_val, away_val, suffix))
            
        label_text = "Match Statistics" if status != "SCHEDULED" else "Expected Statistics (Simulated)"
        sub_text = "Comparative metrics based on match data" if status != "SCHEDULED" else "Simulated metrics based on team strength"
        
        return html.Div([
            section_header(label_text, sub_text),
            html.Div(stat_rows, className="glow-card", style={"padding":"24px", "backgroundColor": COLORS["bg_card"]})
        ])
        
    elif tab_name == "lineups":
        h_form = get_team_preferred_formation(home, match["id"])
        a_form = get_team_preferred_formation(away, match["id"])
        
        home_starters, home_subs = get_squad(home, match["id"], h_form)
        away_starters, away_subs = get_squad(away, match["id"], a_form)
        
        home_coords = get_formation_coords(h_form, "home")
        away_coords = get_formation_coords(a_form, "away")
        
        # Helper to assign coords to starting players
        home_starter_list = list(home_starters.items())
        home_rendered_players = []
        for idx, (player_name, pos_role) in enumerate(home_starter_list[:11]):
            x, y = home_coords[idx]
            last_name = player_name.split(". ")[-1] if ". " in player_name else player_name.split(" ")[-1]
            
            home_rendered_players.append(html.Div([
                html.Div(str(idx + 1 if idx > 0 else 1), style={
                    "width":"22px", "height":"22px", "borderRadius":"50%", 
                    "backgroundColor": COLORS["accent"], "color": "#000", 
                    "display":"flex", "alignItems":"center", "justifyContent":"center",
                    "fontSize":"11px", "fontWeight":"800", "boxShadow":"0 2px 6px rgba(0,229,160,0.4)"
                }),
                html.Div(last_name, style={
                    "fontSize":"10px", "fontWeight":"700", "color": "#fff",
                    "marginTop":"3px", "textShadow":"0 1px 3px rgba(0,0,0,0.8)", "textAlign":"center",
                    "maxWidth":"70px", "whiteSpace":"nowrap", "overflow":"hidden", "textOverflow":"ellipsis"
                })
            ], style={"position":"absolute", "left": f"{x}%", "top": f"{y}%", "transform": "translate(-50%, -50%)", "display":"flex", "flexDirection":"column", "alignItems":"center"}))
            
        away_starter_list = list(away_starters.items())
        away_rendered_players = []
        for idx, (player_name, pos_role) in enumerate(away_starter_list[:11]):
            x, y = away_coords[idx]
            last_name = player_name.split(". ")[-1] if ". " in player_name else player_name.split(" ")[-1]
            
            away_rendered_players.append(html.Div([
                html.Div(str(idx + 1 if idx > 0 else 1), style={
                    "width":"22px", "height":"22px", "borderRadius":"50%", 
                    "backgroundColor": COLORS["accent2"], "color": "#fff", 
                    "display":"flex", "alignItems":"center", "justifyContent":"center",
                    "fontSize":"11px", "fontWeight":"800", "boxShadow":"0 2px 6px rgba(123,97,255,0.4)"
                }),
                html.Div(last_name, style={
                    "fontSize":"10px", "fontWeight":"700", "color": "#fff",
                    "marginTop":"3px", "textShadow":"0 1px 3px rgba(0,0,0,0.8)", "textAlign":"center",
                    "maxWidth":"70px", "whiteSpace":"nowrap", "overflow":"hidden", "textOverflow":"ellipsis"
                })
            ], style={"position":"absolute", "left": f"{x}%", "top": f"{y}%", "transform": "translate(-50%, -50%)", "display":"flex", "flexDirection":"column", "alignItems":"center"}))
            
        # Draw tactical pitch markings
        pitch_markings = [
            # Center Circle
            html.Div(style={"position":"absolute", "top":"50%", "left":"50%", "transform":"translate(-50%, -50%)", "width":"90px", "height":"90px", "borderRadius":"50%", "border":"1.5px solid rgba(255,255,255,0.18)"}),
            # Center Spot
            html.Div(style={"position":"absolute", "top":"50%", "left":"50%", "transform":"translate(-50%, -50%)", "width":"6px", "height":"6px", "borderRadius":"50%", "backgroundColor":"rgba(255,255,255,0.3)"}),
            # Center Line
            html.Div(style={"position":"absolute", "top":"0", "bottom":"0", "left":"50%", "width":"1.5px", "backgroundColor":"rgba(255,255,255,0.18)"}),
            # Penalty Box Left
            html.Div(style={"position":"absolute", "top":"20%", "bottom":"20%", "left":"0", "width":"55px", "border":"1.5px solid rgba(255,255,255,0.18)", "borderLeft":"none"}),
            # Goal Area Left
            html.Div(style={"position":"absolute", "top":"35%", "bottom":"35%", "left":"0", "width":"18px", "border":"1.5px solid rgba(255,255,255,0.18)", "borderLeft":"none"}),
            # Penalty Box Right
            html.Div(style={"position":"absolute", "top":"20%", "bottom":"20%", "right":"0", "width":"55px", "border":"1.5px solid rgba(255,255,255,0.18)", "borderRight":"none"}),
            # Goal Area Right
            html.Div(style={"position":"absolute", "top":"35%", "bottom":"35%", "right":"0", "width":"18px", "border":"1.5px solid rgba(255,255,255,0.18)", "borderRight":"none"}),
        ]
        
        pitch_view = html.Div(
            pitch_markings + home_rendered_players + away_rendered_players,
            className="tactical-pitch",
            style={
                "position":"relative", 
                "height":"380px", 
                "background":"linear-gradient(135deg, #163C2E 0%, #0D2C20 100%)", 
                "borderRadius":"16px", 
                "border":f"1px solid {COLORS['border']}", 
                "overflow":"hidden", 
                "marginBottom":"24px",
                "boxShadow":"inset 0 0 40px rgba(0,0,0,0.6)"
            }
        )
        
        # Lineup details column
        home_starters_elements = [html.Div(f"{pos}: {name}", style={"fontSize":"13px", "color": COLORS["text_primary"], "marginBottom":"4px"}) for name, pos in home_starters.items()]
        away_starters_elements = [html.Div(f"{pos}: {name}", style={"fontSize":"13px", "color": COLORS["text_primary"], "marginBottom":"4px"}) for name, pos in away_starters.items()]
        
        home_subs_elements = [html.Div(f"SUB: {name}", style={"fontSize":"12px", "color": COLORS["text_secondary"], "marginBottom":"3px"}) for name in home_subs]
        away_subs_elements = [html.Div(f"SUB: {name}", style={"fontSize":"12px", "color": COLORS["text_secondary"], "marginBottom":"3px"}) for name in away_subs]
        
        return html.Div([
            section_header("Tactical Lineups", f"{home} ({h_form})  vs  {away} ({a_form})"),
            pitch_view,
            html.Div([
                html.Div([
                    html.Div(f"{get_flag(home)} {home} Squad ({h_form})", style={"fontWeight":"800", "color": COLORS["accent"], "marginBottom":"12px", "fontSize":"15px"}),
                    html.Div(home_starters_elements, style={"marginBottom":"16px"}),
                    html.Div("Substitutes", style={"fontWeight":"700", "color": COLORS["text_secondary"], "marginBottom":"8px", "fontSize":"12px"}),
                    html.Div(home_subs_elements)
                ], className="glow-card", style={"flex":"1", "padding":"20px", "backgroundColor": COLORS["bg_card"]}),
                
                html.Div([
                    html.Div(f"{get_flag(away)} {away} Squad ({a_form})", style={"fontWeight":"800", "color": COLORS["accent2"], "marginBottom":"12px", "fontSize":"15px"}),
                    html.Div(away_starters_elements, style={"marginBottom":"16px"}),
                    html.Div("Substitutes", style={"fontWeight":"700", "color": COLORS["text_secondary"], "marginBottom":"8px", "fontSize":"12px"}),
                    html.Div(away_subs_elements)
                ], className="glow-card", style={"flex":"1", "padding":"20px", "backgroundColor": COLORS["bg_card"]}),
            ], style={"display":"flex", "gap":"20px", "flexWrap":"wrap"})
        ])
        
    elif tab_name == "venue":
        # Venue Details & Weather
        venue = match.get("venue","")
        coords_info = get_match_venue_coords(venue)
        stadium_name = coords_info[0] if coords_info else venue
        capacity = STADIUM_CAPACITIES.get(stadium_name, "N/A")
        
        weather_card_children = [
            html.Div("Weather & Venue Info", style={"fontSize":"10px","fontWeight":"700","color":COLORS["accent"],"textTransform":"uppercase","letterSpacing":"0.08em","marginBottom":"10px"}),
            html.Div([
                html.Div([
                    html.Div("Stadium Capacity", style={"fontSize":"11px", "color": COLORS["text_secondary"]}),
                    html.Div(f"{capacity:,}" if isinstance(capacity, int) else str(capacity), style={"fontSize":"20px", "fontWeight":"800", "color": COLORS["text_primary"]})
                ], style={"flex":"1"}),
                html.Div([
                    html.Div("Venue", style={"fontSize":"11px", "color": COLORS["text_secondary"]}),
                    html.Div(stadium_name, style={"fontSize":"14px", "fontWeight":"700", "color": COLORS["text_primary"]})
                ], style={"flex":"1.5"})
            ], style={"display":"flex", "gap":"16px", "marginBottom":"16px"})
        ]
        
        # Load weather forecast
        weather_data = fetch_stadium_weather(stadium_name) if stadium_name else None
        if weather_data and "current_weather" in weather_data:
            cw = weather_data["current_weather"]
            temp = cw.get("temperature", "—")
            code = cw.get("weathercode", 0)
            from data.enrichment import get_weather_label
            cond = get_weather_label(code)
            
            weather_card_children.append(
                html.Div([
                    html.Div("Current Local Weather", style={"fontSize":"12px", "fontWeight":"700", "color": COLORS["accent3"], "marginBottom":"6px"}),
                    html.Div([
                        html.Span(f"{temp}°C", style={"fontSize":"24px", "fontWeight":"900", "color": COLORS["text_primary"], "marginRight":"12px"}),
                        html.Span(cond, style={"fontSize":"13px", "color": COLORS["text_secondary"]})
                    ], style={"display":"flex", "alignItems":"center"})
                ], style={"borderTop": f"1px solid {COLORS['border']}", "paddingTop":"12px"})
            )
        else:
            weather_card_children.append(
                html.Div("Weather forecast currently unavailable", style={"fontSize":"12px", "color": COLORS["text_secondary"], "fontStyle":"italic", "borderTop": f"1px solid {COLORS['border']}", "paddingTop":"12px"})
            )
            
        # Country comparison profiles
        profile_a = fetch_country_profile(home)
        profile_b = fetch_country_profile(away)
        
        def render_country_card(team, prof):
            if not prof:
                return html.Div([
                    html.Div(f"{get_flag(team)} {team}", style={"fontWeight":"800", "fontSize":"15px", "color": COLORS["text_primary"], "marginBottom":"12px"}),
                    html.Div("Profile data unavailable", style={"fontStyle":"italic", "color": COLORS["text_secondary"]})
                ], className="glow-card", style={"flex":"1", "padding":"20px", "backgroundColor": COLORS["bg_card"]})
                
            pop = prof.get("population", 0)
            pop_str = f"{pop:,}" if pop > 0 else "N/A"
            cap = prof.get("capital", "N/A")
            region = prof.get("region", "N/A")
            subreg = prof.get("subregion", "N/A")
            langs = ", ".join(prof.get("languages", [])) or "N/A"
            flag_svg = prof.get("flag_svg")
            
            return html.Div([
                html.Div([
                    html.Div([
                        html.Div(f"{get_flag(team)} {team}", style={"fontWeight":"800", "fontSize":"16px", "color": COLORS["text_primary"]}),
                        html.Div(f"Capital: {cap}", style={"fontSize":"12px", "color": COLORS["text_secondary"]}),
                    ]),
                    html.Img(src=flag_svg, style={"width":"40px", "height":"26px", "borderRadius":"4px", "objectFit":"cover", "border":"1px solid rgba(255,255,255,0.1)"}) if flag_svg else None
                ], style={"display":"flex", "justifyContent":"space-between", "alignItems":"flex-start", "marginBottom":"16px", "borderBottom":f"1px solid {COLORS['border']}", "paddingBottom":"12px"}),
                
                html.Div([
                    html.Div([
                        html.Div("Population", style={"fontSize":"10px", "color": COLORS["text_secondary"], "textTransform":"uppercase"}),
                        html.Div(pop_str, style={"fontSize":"14px", "fontWeight":"700", "color": COLORS["text_primary"]})
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Region", style={"fontSize":"10px", "color": COLORS["text_secondary"], "textTransform":"uppercase"}),
                        html.Div(f"{region} ({subreg})", style={"fontSize":"13px", "fontWeight":"700", "color": COLORS["text_primary"]})
                    ], style={"flex":"1.2"}),
                ], style={"display":"flex", "gap":"12px", "marginBottom":"12px"}),
                
                html.Div([
                    html.Div("Languages", style={"fontSize":"10px", "color": COLORS["text_secondary"], "textTransform":"uppercase"}),
                    html.Div(langs, style={"fontSize":"12px", "fontWeight":"500", "color": COLORS["text_primary"]})
                ])
            ], className="glow-card", style={"flex":"1", "padding":"20px", "backgroundColor": COLORS["bg_card"]})
            
        return html.Div([
            section_header("Match Environment", "Stadium and country facts"),
            html.Div(weather_card_children, className="glow-card", style={"padding":"20px", "backgroundColor": COLORS["bg_card2"], "marginBottom":"24px"}),
            html.Div([
                render_country_card(home, profile_a),
                render_country_card(away, profile_b)
            ], style={"display":"flex", "gap":"20px", "flexWrap":"wrap"})
        ])

def layout(match_id):
    match = get_match_by_id(match_id)
    
    if not match:
        return html.Div([
            page_wrapper([
                html.Div([
                    html.Div("⚠️", style={"fontSize":"48px", "marginBottom":"16px"}),
                    html.Div("Match Not Found", style={"fontSize":"20px", "fontWeight":"800", "color": COLORS["text_primary"], "marginBottom":"8px"}),
                    html.Div("The match ID requested does not match any fixture in our records.", style={"color": COLORS["text_secondary"], "marginBottom":"20px"}),
                    dcc.Link("Return to Dashboard", href="/", className="shiny-text", style={"textDecoration":"none", "fontWeight":"700"})
                ], className="glow-card", style={"padding":"40px", "textAlign":"center", "maxWidth":"500px", "margin":"60px auto"})
            ])
        ])
        
    home = match["home_team"]
    away = match["away_team"]
    status = match.get("status", "SCHEDULED")
    is_live = status == "LIVE"
    is_fin = status == "FINISHED"
    
    score_display = html.Div("vs", style={"fontSize":"16px", "color": COLORS["text_secondary"]})
    if is_fin or is_live:
        score_display = html.Div([
            html.Div(f"{match.get('home_score')}  –  {match.get('away_score')}", style={"fontSize":"clamp(24px, 6vw, 36px)", "fontWeight":"900", "fontVariantNumeric":"tabular-nums", "color": COLORS["live_red"] if is_live else COLORS["text_primary"]})
        ])
        
    badge_color = COLORS["live_red"] if is_live else (COLORS["win_green"] if is_fin else COLORS["text_secondary"])
    status_badge = live_badge() if is_live else html.Span(status, style={
        "backgroundColor": badge_color + "22",
        "border": f"1px solid {badge_color}44",
        "color": badge_color,
        "fontSize": "10px", "fontWeight": "700", "padding": "2px 8px", "borderRadius": "4px"
    })
    
    return html.Div([
        page_wrapper([
            # Navigation row
            html.Div([
                dcc.Link("← Back to Dashboard", href="/", style={
                    "textDecoration":"none", "color": COLORS["accent"], "fontWeight":"600",
                    "fontSize":"13px", "display":"inline-flex", "alignItems":"center", "gap":"6px",
                    "transition":"all 0.2s ease"
                }, className="back-link")
            ], style={"marginBottom":"18px"}),
            
            # Header Match Card Banner
            html.Div([
                html.Div([
                    status_badge,
                    html.Span(match.get("group", ""), style={"fontSize":"11px", "fontWeight":"700", "color": COLORS["accent3"], "textTransform":"uppercase", "letterSpacing":"0.1em"})
                ], style={"display":"flex", "justifyContent":"space-between", "alignItems":"center", "width":"100%", "marginBottom":"20px"}),
                
                html.Div([
                    # Home Team
                    html.Div([
                        html.Div(match.get("home_flag", ""), style={"fontSize":"clamp(32px, 8vw, 54px)", "marginBottom":"8px"}),
                        html.Div(home, style={"fontSize":"clamp(14px, 3.5vw, 20px)", "fontWeight":"800", "color": COLORS["text_primary"], "textAlign":"center", "lineHeight":"1.2"})
                    ], style={"flex":"1", "display":"flex", "flexDirection":"column", "alignItems":"center"}),
                    
                    # Score Center
                    html.Div([
                        score_display,
                        html.Div(match.get("time", ""), style={"fontSize":"11px", "color": COLORS["text_secondary"], "marginTop":"8px", "fontWeight":"500"}),
                    ], style={"minWidth":"120px", "textAlign":"center", "display":"flex", "flexDirection":"column", "alignItems":"center", "justifyContent":"center"}),
                    
                    # Away Team
                    html.Div([
                        html.Div(match.get("away_flag", ""), style={"fontSize":"clamp(32px, 8vw, 54px)", "marginBottom":"8px"}),
                        html.Div(away, style={"fontSize":"clamp(14px, 3.5vw, 20px)", "fontWeight":"800", "color": COLORS["text_primary"], "textAlign":"center", "lineHeight":"1.2"})
                    ], style={"flex":"1", "display":"flex", "flexDirection":"column", "alignItems":"center"}),
                ], style={"display":"flex", "alignItems":"center", "justifyContent":"space-between", "width":"100%"}),
                
                html.Div([
                    html.Span(f"📅 {match.get('date','')}", style={"fontSize":"12px", "color": COLORS["text_secondary"]}),
                    html.Span(" · ", style={"color": COLORS["border"], "margin":"0 8px"}),
                    html.Span(f"📍 {match.get('venue','')}", style={"fontSize":"12px", "color": COLORS["text_secondary"]})
                ], style={"marginTop":"20px", "borderTop": f"1px solid {COLORS['border']}", "paddingTop":"14px", "width":"100%", "textAlign":"center"})
            ], className="glow-card", style={"padding":"28px", "backgroundColor": COLORS["bg_card"], "marginBottom":"24px", "display":"flex", "flexDirection":"column", "alignItems":"center"}),
            
            # Tab Selector
            html.Div([
                html.Button("Overview", id="overview-btn", className="tab-btn active", style={"flex":"1", "padding":"12px", "cursor":"pointer"}),
                html.Button("Stats", id="stats-btn", className="tab-btn", style={"flex":"1", "padding":"12px", "cursor":"pointer"}),
                html.Button("Lineups", id="lineups-btn", className="tab-btn", style={"flex":"1", "padding":"12px", "cursor":"pointer"}),
                html.Button("Venue & Countries", id="venue-btn", className="tab-btn", style={"flex":"1", "padding":"12px", "cursor":"pointer"}),
            ], style={"display":"flex", "backgroundColor": COLORS["bg_card2"], "borderRadius":"10px", "border":f"1px solid {COLORS['border']}", "padding":"4px", "marginBottom":"24px", "gap":"4px"}),
            
            # Active Tab Content
            html.Div(id="match-detail-tab-content")
        ])
    ])

@app.callback(
    [Output("match-detail-tab-content", "children"),
     Output("overview-btn", "className"),
     Output("stats-btn", "className"),
     Output("lineups-btn", "className"),
     Output("venue-btn", "className")],
    [Input("overview-btn", "n_clicks"),
     Input("stats-btn", "n_clicks"),
     Input("lineups-btn", "n_clicks"),
     Input("venue-btn", "n_clicks")],
    [State("url", "pathname")]
)
def render_tab_content(overview, stats, lineups, venue, pathname):
    ctx = dash.callback_context
    
    base_cls = "tab-btn"
    active_cls = "tab-btn active"
    
    overview_cls = active_cls
    stats_cls = base_cls
    lineups_cls = base_cls
    venue_cls = base_cls
    
    active_tab = "overview"
    if ctx.triggered:
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "stats-btn":
            active_tab = "stats"
            overview_cls, stats_cls, lineups_cls, venue_cls = base_cls, active_cls, base_cls, base_cls
        elif trigger_id == "lineups-btn":
            active_tab = "lineups"
            overview_cls, stats_cls, lineups_cls, venue_cls = base_cls, base_cls, active_cls, base_cls
        elif trigger_id == "venue-btn":
            active_tab = "venue"
            overview_cls, stats_cls, lineups_cls, venue_cls = base_cls, base_cls, base_cls, active_cls
            
    match = get_match_by_id(pathname.split("/")[-1]) if pathname and pathname.startswith("/match/") else None
    if not match:
        return html.Div("Match not found."), overview_cls, stats_cls, lineups_cls, venue_cls
        
    content = render_tab_view(active_tab, match)
    return content, overview_cls, stats_cls, lineups_cls, venue_cls
