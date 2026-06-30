<div align="center">

# ⚽ STATDIUM
### FIFA World Cup 2026 — Live Analytics Platform

**Built for the [Plotly Community App Challenge](https://community.plotly.com/t/plotly-2026-world-cup-app-challenge) · June 2026**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-4.x-00B4D8?style=flat&logo=plotly&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-7B61FF?style=flat&logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00E5A0?style=flat)

---

*A broadcast-grade football analytics app — live scores, Elo intelligence, Monte Carlo simulations, historical deep-dives and interactive scenarios. 100% free data sources. Zero paywalls.*

</div>

---

## ✨ Features

### 📡 Live & Real-time
| Feature | Description |
|---|---|
| **Live Scores** | Auto-refresh every 60s — openfootball + football-data.org overlay |
| **Live Ticker** | Scrolling scoreboard of all finished and live matches |
| **Favourite Team Tracker** | Follow any team, see their next match pinned on the dashboard |
| **Goals Timeline** | Day-by-day goals chart with avg per match trend line |

### 📊 Analytics
| Feature | Description |
|---|---|
| **12 Group Tables** | Live standings with qualification (🟢) and elimination (🔴) zones |
| **Golden Boot Race** | Ranked progress bars with player photos · goals · assists |
| **Monte Carlo Bracket** | 10,000 simulations — championship probability heatmap + Sankey |
| **Team H2H Comparison** | Grouped bar chart + 7-axis radar + Elo win probability bar |
| **World Choropleth** | Goals, wins, upsets painted on the world map |

### 🧠 Intelligence
| Feature | Description |
|---|---|
| **Tactical DNA** | Unique geometric SVG fingerprint per team from live stats |
| **Fan Pulse Map** | World emotion choropleth — team performance as a sentiment layer |
| **GDP vs Football** | Does money buy World Cup success? World Bank data bubble scatter |
| **Shock Index** | Elo + Poisson model upset probability for every upcoming match |

### 🔮 Interactive
| Feature | Description |
|---|---|
| **What If Scenario Builder** | Override any score → see group standings instantly recompute |
| **Tournament Simulator** | Click to animate a full bracket round-by-round |
| **Historical Heatmap** | Every team's WC journey 1930–2022, colour-coded by result |
| **All-time H2H** | Win/draw/loss records between any two nations |

### 🏟️ Venues
| Feature | Description |
|---|---|
| **Stadium Clock Wall** | All 16 host cities — local time, live temperature, next match |
| **Weather Cards** | Open-Meteo live data per stadium |
| **Google Maps Links** | One click to each stadium location |

---

## 🏗️ Architecture

```
statdium/
├── app.py                  # Entry point, router, APScheduler (60s refresh)
├── app_instance.py         # Shared Dash app object
├── assets/
│   ├── statdium.css        # Full design system — Barlow Condensed + Inter
│   └── statdium.js         # Particles, tilt, countup, sidebar toggle
├── components/
│   └── ui.py               # sidebar(), match_scorecard(), stat_pill(), standings_row()
├── data/
│   ├── fetcher.py          # openfootball + FD API + team crests + scorers
│   ├── elo.py              # eloratings.net scraper + Poisson model
│   ├── enrichment.py       # Open-Meteo weather, hype themes
│   ├── ai_insights.py      # Template match previews
│   └── media_links.py      # FIFA+, YouTube search, Google Maps
├── pages/                  # 14 pages — one file each
│   ├── live.py             # Hero + live scores + ticker + timeline
│   ├── groups.py           # 12 groups + qual probability bars
│   ├── bracket.py          # Monte Carlo + heatmap + Sankey + Path to Glory
│   ├── teams.py            # H2H radar + follow system
│   ├── leaderboards.py     # Golden Boot progress bars + player photos
│   ├── insights.py         # Choropleth + upsets + Wall of Champions
│   ├── formations.py       # Pitch SVG + Shock Index + Group of Death
│   ├── stadiums.py         # Clock wall + weather (merged)
│   ├── history.py          # WC heatmap 1930–2022 + H2H history
│   ├── scenario.py         # What If scenario builder
│   ├── tactical_dna.py     # DNA fingerprints + Fan Pulse map
│   ├── animated_bracket.py # Bracket simulator + GDP chart
│   └── animated_bracket.py # ... and more
└── utils/
    └── monte_carlo.py      # Elo-powered tournament simulation engine
```

---

## 🆓 Data Sources

| Source | What | Key needed? |
|---|---|---|
| **openfootball/worldcup.json** | Fixtures, scores, goal scorers | ❌ None |
| **football-data.org** | Live scores, scorers + goals, team crests | ✅ Free key |
| **eloratings.net** | Live Elo ratings (updates after every match) | ❌ None |
| **flagcdn.com** | Real flag images (20/40/80/160/320px) | ❌ None |
| **Open-Meteo** | Stadium weather — temperature, conditions | ❌ None |
| **World Bank (embedded)** | GDP per country for economic analysis | ❌ None |

---

## 🚀 Run Locally

```bash
git clone https://github.com/Shail-1799/statdium
cd statdium
pip install -r requirements.txt

# Optional but recommended:
export FD_API_KEY=your_key_from_football-data.org

python app.py
# → http://localhost:8050
```

Get your **free** football-data.org key at [football-data.org/client/register](https://www.football-data.org/client/register) — takes 2 minutes.

---

## ☁️ Deploy to Render

1. Push to GitHub
2. New Web Service → connect repo
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. **Environment variables:**
   - `FD_API_KEY` → your football-data.org free key

---

## 🎨 Design

- **Fonts:** [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) (headings/scores) + [Inter](https://fonts.google.com/specimen/Inter) (body) — same font family used by broadcast sports apps
- **Palette:** Dark broadcast aesthetic — `#07070C` base, `#00E5A0` accent
- **Animations:** Particle network, card tilt, number countup, skeleton loaders
- **Responsive:** Sidebar collapses on desktop · slide-in drawer on mobile

---

## 🏆 Built for Plotly Community Challenge

> *"A goldmine of football intelligence — from live scores to 92-year historical heatmaps, all in one dark, fast, broadcast-quality app."*

Made with ❤️ and ⚽ · Powered by [Dash](https://dash.plotly.com) + [Plotly](https://plotly.com)
