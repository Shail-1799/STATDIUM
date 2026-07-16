<div align="center">

# ⚽ STATDIUM
### FIFA World Cup 2026 — Live Analytics Platform

**Built for the [Plotly Community App Challenge 2026](https://community.plotly.com/t/plotly-2026-world-cup-app-challenge)**

[![Live App](https://img.shields.io/badge/🔴%20Live%20App-statdium.onrender.com-00E5A0?style=for-the-badge)](https://statdium-fifa-world-cup-2026.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-Shail--1799%2FSTATDIUM-181717?style=for-the-badge&logo=github)](https://github.com/Shail-1799/STATDIUM)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-4.x-00B4D8?style=flat&logo=plotly&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-7B61FF?style=flat)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat)
![License](https://img.shields.io/badge/License-MIT-00E5A0?style=flat)

*A broadcast-grade football analytics platform — live scores, Elo intelligence,
Monte Carlo simulations, historical deep-dives, match predictions and interactive
scenarios. 14 pages. 100% free data sources. Zero paywalls.*

</div>

---

## 🎬 See It In Action

> *[→ Open the live app](https://statdium-fifa-world-cup-2026.onrender.com)*
> (Allow ~30s for Render cold start on first load)

---

## ✨ What Makes This Different

Most World Cup dashboards show a score and a table. STATDIUM goes further:

| Feature | What it does | Why it's different |
|---|---|---|
| *Elo Win Probability* | Live head-to-head win % from Elo formula | Not just FIFA ranking — actual mathematical probability |
| *Monte Carlo Bracket* | 10,000 tournament simulations on demand | Shows probability distributions, not single predictions |
| *What If Scenario Builder* | Override any score → group standings recompute live | Fully interactive — no other submission has this |
| *Match Predictor* | Pick winners, track accuracy vs Elo model baseline | Personal engagement that brings users back |
| *Tactical DNA Fingerprints* | Unique SVG data-art per team from live stats | Data as visual art — generative, not templated |
| *Historical Heatmap* | Every WC result 1930–2022 in one chart | 92 years of football in a single interactive view |
| *Fan Pulse Map* | World choropleth coloured by team pulse score | Emotion as a data layer on the globe |
| *GDP vs Football Power* | World Bank data + Elo in bubble scatter | Answers the question money can't buy |
| *Stadium Clock Wall* | 16 host cities, live local time + weather | Practical utility, beautifully presented |

---

## 📱 Keyboard Shortcuts

A genuine differentiator — navigate the entire app without touching the mouse:

| Key | Page | Key | Page |
|---|---|---|---|
| G | Live Dashboard | K | Leaderboards |
| B | Bracket | I | Insights |
| T | Teams | H | History |
| P | Predictor | W | What If |
| F | Formations | S | Simulator |
| ? | Help modal | ESC | Close modal |

---

## 📊 14 Pages — Full Feature List

### 📡 Live & Real-time
*/ — Live Dashboard*
Auto-refreshing hero with animated stat strip. Grouped match cards by date with live/FT badges. Favourite team tracker pinned to top. Goals timeline chart. Full scrollable match timeline across all 104 fixtures.

*/groups — Group Stage*
All 12 groups with colour-coded standings (🟢 qualifying / 🔴 elimination zones). W=green · D=gold · L=red per column. Monte Carlo qualification probability bars. Scenario text per group.

*/leaderboards — Leaderboards*
Golden Boot race with player photos + animated progress bars. Top Assists tab. Yellow & Red Cards tabs. All derived from live match data — updates every 60 seconds.

### 🧠 Analytics
*/bracket — Monte Carlo Bracket*
Run 10,000 tournament simulations on demand. Championship probability heatmap (Plotly choropleth). Sankey diagram showing team flow through rounds. Path to Glory funnel per team.

*/teams — Team Explorer*
Select any two teams. Grouped bar chart (Wins/Draws/Losses/GF/GA). 6-axis performance radar (0–100 scale). Elo win probability bar. Live quick stats comparison. Follow system — pin a team to your Live dashboard.

*/insights — Global Insights*
World choropleth map coloured by goals/wins. Goals by group bar chart. Upset tracker with Shock Index. Wall of Champions — every WC winner since 1930 with equal-sized cards.

*/history — Historical Deep-Dive*
WC performance heatmap: every team × every year from 1930–2022, colour-coded by result. All-time H2H records between any two nations with win/draw/loss bars.

### 🔮 Interactive
*/predictor — Match Predictor*
Pick home/draw/away for every match. Picks saved to localStorage — persist across sessions. Cards flip green/red as results come in. Running accuracy vs Elo model baseline (58%).

*/scenario — What If Builder*
Override any match score with custom inputs. All 12 group standings recompute instantly. Changed groups marked with ↺ badge and orange border. Reset to actual standings in one click.

*/simulator — Tournament Simulator*
Animate a full bracket round-by-round on click. Each run is independently random — natural Monte Carlo variance. GDP vs Football Power bubble scatter underneath.

*/tactical-dna — Tactical DNA*
Unique geometric SVG fingerprint per team generated from live stats. Fan Pulse world map — countries coloured by weighted performance score.

### 🏟️ Match Centre
*/formations — Formations & Shock Index*
Horizontal pitch SVG with formation overlay. Shock Index gauge (Elo + Poisson). Group of Death ranker by combined Elo.

*/stadiums — Stadiums & Clock Wall*
All 16 host venues. Live local time (pytz timezones). Open-Meteo temperature + weather icon. Next match at each venue. Google Maps link per stadium. Updates every 30 seconds.

---

## 🏗️ Architecture


statdium/
├── app.py                   # Entry point · router · APScheduler (60s refresh)
├── app_instance.py          # Shared Dash app + full OG meta tags
├── assets/
│   ├── statdium.css         # Design system — Barlow Condensed + Inter · CSS variables
│   ├── statdium.js          # Particles · sidebar · modal · keyboard shortcuts
│   └── og_thumbnail.svg     # 1200×630 Open Graph image
├── components/
│   └── ui.py                # sidebar() · match_scorecard() · standings_row()
│                            # stat_pill() · goal_ticker() · page_guide()
├── data/
│   ├── fetcher.py           # openfootball + FD API merge · caching · status logic
│   ├── elo.py               # eloratings.net scraper · Poisson model
│   ├── enrichment.py        # Open-Meteo weather
│   ├── ai_insights.py       # Template match previews (no API key needed)
│   ├── media_links.py       # FIFA+ · YouTube search · Google Maps
│   └── rapidapi_football.py # RapidAPI — lineups · events · match stats
├── pages/                   # All page files — one per route
└── utils/
    └── monte_carlo.py       # run_simulation() — Elo-powered bracket engine


### Data Flow

openfootball (GitHub raw JSON)     →  base match data + scorers
         +
football-data.org (FD API)         →  live status overlay + team crests + photos
         +
eloratings.net                     →  live Elo ratings → win probability
         +
Open-Meteo                         →  stadium weather
         ↓
APScheduler (every 60s)            →  refresh_data() → in-memory cache
         ↓
Dash callbacks (dcc.Interval)      →  page components read from cache


---

## 🆓 Data Sources — 100% Free

| Source | What | Key needed |
|---|---|---|
| *openfootball/worldcup.json* | Fixtures, scores, goal scorers | ❌ None |
| *football-data.org v4* | Live scores, team crests, scorer photos | ✅ Free signup |
| *eloratings.net* | Live Elo ratings (updates after every match) | ❌ None |
| *flagcdn.com* | Country flag images at multiple sizes | ❌ None |
| *Open-Meteo* | Stadium weather — temperature, conditions | ❌ None |
| *World Bank (embedded)* | GDP per country for economic analysis | ❌ None |

---

## 🚀 Run Locally in Under 2 Minutes

bash
# 1. Clone
git clone https://github.com/Shail-1799/STATDIUM
cd STATDIUM

# 2. Install
pip install -r requirements.txt

# 3. (Optional but recommended) Set free API keys
export FD_API_KEY=your_key_from_football-data.org

# 4. Run
python app.py


*Open http://localhost:8050* — the app works without API keys (degrades gracefully to openfootball data + Elo only).

Get your *free* football-data.org key at [football-data.org/client/register](https://www.football-data.org/client/register) — takes 2 minutes, no credit card.

---

## ☁️ Deploy to Render

1. Push to GitHub
2. New Web Service → connect repo
3. *Build:* pip install -r requirements.txt
4. *Start:* gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120
5. *Environment variables:*


FD_API_KEY      = your_football_data_key


---

## 🎨 Design System

*Fonts:* [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) for headings, scores and display numbers + [Inter](https://fonts.google.com/specimen/Inter) for body — the same font pairing used by broadcast sports graphics.

*Palette:* Dark broadcast aesthetic.
- #07070C — base background
- #00E5A0 — primary accent (green)
- #7B61FF — secondary accent (purple)
- #FFD700 — gold (leaders, champions)
- #FF3B30 — live red

*Responsive:* Sidebar collapses to 72px icon rail on tablet, hidden off-canvas drawer on mobile. Works on any screen size.

*Animations:* Particle network background · card tilt on hover · number countup on load · skeleton loaders · animated progress bars · cinematic bracket reveal.

---

## 🧮 Methodology (Brief)

*Elo Win Probability:*
P(A wins) = 1 / (1 + 10^((Elo_B − Elo_A) / 400))
Ratings from eloratings.net, updated live after every match.

*Monte Carlo Simulation:*
10,000 full tournament runs. Each match outcome drawn randomly weighted by Elo probability. Championship % = wins / 10,000.

*Shock Index:*
Combines Elo win probability with Poisson goal model. Higher = bigger potential upset.

*Fan Pulse Score:*
Pulse = (Points × 10) + (max(0, GD) × 5) + (Goals × 2)

Full methodology with worked examples → [About page](https://statdium-fifa-world-cup-2026.onrender.com/about)

---

## 🏆 Built for Plotly Community Challenge

> *"A goldmine of football intelligence — live scores to 92-year heatmaps,
> Monte Carlo simulations to personal match predictions,
> all in one dark, fast, broadcast-quality Dash app."*

*Plotly features used:* Choropleth maps · Scatterpolar radar · Sankey diagrams · Grouped bar charts · Scatter plots · Heatmaps · Line + bar combo charts · Funnel charts · Custom SVG iframes · dcc.Store (localStorage) · Pattern-matching callbacks · APScheduler integration

---

<div align="center">

**[🔴 Live App](https://statdium-fifa-world-cup-2026.onrender.com) · [💻 GitHub](https://github.com/Shail-1799/STATDIUM)**

Made with ❤️ · Powered by [Plotly Dash](https://dash.plotly.com) · 100% Free Data

</div>
