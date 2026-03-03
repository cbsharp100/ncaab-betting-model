🏀 NCAA Basketball Betting Model
MGMT 69000 – Final Project

Author: Charles Sharp

📌 Project Overview

This project is a fully automated NCAA Men’s Basketball betting board generator that produces daily spread and total projections using:

Current season game results (auto-refreshed)

Elo rating system

NCAA NET rankings (blended as prior)

Monte Carlo simulation (1000+ simulations per game)

Edge calculation vs sportsbook lines

Automated CSV + Excel output

CI validation pipeline

The goal is to build a reproducible, validated financial modeling system that identifies market inefficiencies in sportsbook lines.

🧠 System Architecture
Raw Data
  ├── Season Game Results
  ├── NCAA NET Rankings
  └── Sportsbook Odds CSV
          ↓
Team Rating Engine
  ├── Elo Updates
  ├── NET Prior Blending
          ↓
Home Court Adjustment
          ↓
Monte Carlo Simulation
          ↓
Model Spread / Total
          ↓
Edge Calculation
          ↓
Daily Ranked Betting Board (CSV + Excel)
📊 Rating Methodology
1️⃣ Elo Model

Elo ratings update after every game:

𝐸
𝑛
𝑒
𝑤
=
𝐸
𝑜
𝑙
𝑑
+
𝐾
⋅
(
𝑅
𝑒
𝑠
𝑢
𝑙
𝑡
−
𝐸
𝑥
𝑝
𝑒
𝑐
𝑡
𝑒
𝑑
)
E
new
	​

=E
old
	​

+K⋅(Result−Expected)

Expected win probability:

𝑃
=
1
1
+
10
−
𝑑
/
400
P=
1+10
−d/400
1
	​


Where:

d = Elo difference between teams

K = update factor

2️⃣ NET Blended Prior

To stabilize early-season noise, NET rankings are converted into an Elo-like prior:

𝐸
𝑓
𝑖
𝑛
𝑎
𝑙
=
𝑤
⋅
𝐸
𝑒
𝑙
𝑜
+
(
1
−
𝑤
)
⋅
𝐸
𝑛
𝑒
𝑡
E
final
	​

=w⋅E
elo
	​

+(1−w)⋅E
net
	​


Where:

𝑤
=
𝑔
𝑎
𝑚
𝑒
𝑠
_
𝑝
𝑙
𝑎
𝑦
𝑒
𝑑
𝑔
𝑎
𝑚
𝑒
𝑠
_
𝑝
𝑙
𝑎
𝑦
𝑒
𝑑
+
10
w=
games_played+10
games_played
	​


As games increase, the model trusts Elo more than the NET prior.

🎲 Monte Carlo Simulation

Each matchup runs 1000 simulations.

For each simulation:

Estimate scoring distribution

Generate predicted margin

Generate predicted total

Outputs:

Model Spread

Model Total

Win Probability

Projected Scores

📈 Edge Calculation

Spread Edge:

spread_edge = model_spread_home - book_spread_home

Total Edge:

total_edge = model_total - book_total

Positive absolute edge indicates model disagreement with market.

Games are ranked by:

best_edge_abs = max(abs(spread_edge), abs(total_edge))
🚀 Quick Start
1️⃣ Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
2️⃣ Run Full Daily Pipeline
make board DAY=2026-02-28 SIMS=1000

This runs:

NET ranking refresh

Season game refresh

Elo rating rebuild

NET blending

Monte Carlo simulations

Full board export

3️⃣ Manual Run
python -m src.picks_day 2026-02-28 1000
📁 Output Files

Daily board saved to:

data/outputs/board_YYYY-MM-DD.csv
data/outputs/board_YYYY-MM-DD.xlsx
✅ Validation

Before simulation, data integrity is validated:

python validation/validation_checks.py

Validation checks:

Odds file contains required columns

Rating file contains Elo outputs

No null final ratings

At least one game simulated

CI automatically runs validation on every push.

🔁 CI/CD

GitHub Actions automatically:

Installs dependencies

Runs validation checks

Confirms pipeline integrity

CI workflow file:

.github/workflows/ci.yml
🤖 AI Disclosure

AI tools (ChatGPT) were used for:

Debugging merge logic

Improving name normalization

Designing CI workflow

Structuring README documentation

Refining Monte Carlo logic

Error diagnosis during pipeline build

All logic was reviewed, validated, and modified manually.

Full AI interaction log included in:

AI_LOG.md
⚠️ Limitations

Does not incorporate injury adjustments

Does not model line movement

Assumes static scoring distribution

No bankroll management strategy implemented

Team name matching requires normalization logic

🔮 Future Improvements

Backtesting vs historical spreads

Calibration analysis

Kelly Criterion bankroll sizing

Closing Line Value tracking

Tempo-adjusted efficiency modeling

Live odds API integration

📊 Example Output (Board Sample)
Home Team	Away Team	Model Spread	Book Spread	Spread Edge
Duke	Virginia	-7.2	-10.5	+3.3
Houston	Colorado	-16.7	-19.5	+2.8

Full results available in Excel export.
