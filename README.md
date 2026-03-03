cat > README.md << 'EOF'
# NCAAB Betting Model (MGMT 69000 Final)

A daily NCAA Men’s Basketball betting board generator using:
- Current season game results (auto-refreshed)
- Team rating engine (Elo + NET blend)
- Monte Carlo simulation for spread/total projections
- Daily “best bets” ranked by edge vs sportsbook lines

## Quick Start

### 1) Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python validation/validation_checks.py
