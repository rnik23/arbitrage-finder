# Python Arbitrage Betting Finder 🎯

This arbitrage betting finder searches major sports events using [The Odds API](https://the-odds-api.com) to fetch odds and find arbitrage opportunities across all bookmakers.

## ✨ Features

- **🔍 Multi-sport support**: MLB, NBA, WNBA, NFL, NHL, MLS and more
- **📊 Real-time odds**: Fetches live odds from major sportsbooks
- **💎 Arbitrage detection**: Intelligent algorithms to find profitable opportunities
- **🔗 Direct betting links**: One-click links to place bets on each sportsbook
- **📨 Discord notifications**: Real-time alerts with betting details
- **🗄️ PostgreSQL integration**: Historical data storage and analytics
- **🐳 Docker deployment**: Production-ready containerized setup
- **⏰ Automated scheduling**: Run scans at custom intervals

## 🚀 Docker Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Odds API key from [The Odds API](https://the-odds-api.com)
- Discord webhook URL (optional)

### 1. Clone and Setup
```bash
git clone <your-repo>
cd arbitrage-finder

# Create environment file
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file with your credentials:
```env
# Required: Get your free API key from https://the-odds-api.com
ODDS_API_KEY=your_odds_api_key_here

# Optional: Discord webhook for notifications
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Database (auto-configured for Docker)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=arbitrage_finder
DB_USER=arbitrage_user
DB_PASSWORD=arbitrage_password
```

### 3. Deploy with Docker
```bash
# Start the complete stack (PostgreSQL + Application)
docker-compose up -d

# Initialize the database schema
docker-compose run arbitrage-finder python scripts/init_db.py

# Test the setup
docker-compose run arbitrage-finder python scripts/test_db.py
```

### 4. Run Arbitrage Scans
```bash
# Scan MLB with specific bookmakers
docker-compose run arbitrage-finder python src/main_production.py \
  --sport baseball_mlb \
  --save-to-db \
  --include-bookmakers "DraftKings" "FanDuel" "BetMGM"

# Scan WNBA for future games only
docker-compose run arbitrage-finder python src/main_production.py \
  --sport basketball_wnba \
  --game-status future \
  --save-to-db
```

### 5. Start Automated Scheduling
```bash
# Option 1: Simple scheduler
./scripts/scheduler.sh

# Option 2: Cron-based (runs in background)
docker-compose up scheduler -d
```

## 📊 Available Sports
- `baseball_mlb` - Major League Baseball
- `basketball_nba` - National Basketball Association  
- `basketball_wnba` - Women's National Basketball Association
- `americanfootball_nfl` - National Football League
- `icehockey_nhl` - National Hockey League
- `soccer_usa_mls` - Major League Soccer

## 🎯 Command Line Options
```bash
python src/main_production.py [OPTIONS]

Options:
  --sport SPORT              Sport to analyze (required)
  --game-status {live,future,all}  Filter by game timing (default: all)
  --include-bookmakers LIST  Only use specific bookmakers
  --exclude-bookmakers LIST  Exclude specific bookmakers  
  --save-to-db              Save results to PostgreSQL
  --show-metadata           Show additional run metadata
```

## 🔧 Management Commands
```bash
# View logs
docker-compose logs -f

# Database shell
docker-compose exec postgres psql -U arbitrage_user -d arbitrage_finder

# Stop all services
docker-compose down

# Reset everything (⚠️ deletes data)
docker-compose down -v
```

## 📈 Monitoring & Analytics
Access your PostgreSQL database to analyze:
- Historical arbitrage opportunities
- Bookmaker performance
- ROI trends over time
- API usage statistics

Example queries:
```sql
-- Recent arbitrage opportunities
SELECT * FROM arbitrage_summary WHERE run_timestamp >= NOW() - INTERVAL '24 hours';

-- Best performing sports
SELECT sport, AVG(roi_percentage) as avg_roi 
FROM arbitrage_opportunities 
GROUP BY sport ORDER BY avg_roi DESC;
```

## 🛠️ Development Setup

For local development without Docker:
```bash
# Install dependencies
pip install -r requirements/requirements.txt

# Set up local PostgreSQL (optional)
# Or use Docker for database only:
docker-compose up postgres -d

# Run locally
python src/main.py --sport baseball_mlb --include-bookmakers "DraftKings" "FanDuel"
```

## 📝 How It Works

1. **Fetch Odds**: Retrieves current odds from The Odds API
2. **Filter Data**: Applies your bookmaker and game status preferences  
3. **Find Arbitrage**: Uses mathematical algorithms to identify profitable opportunities
4. **Calculate Stakes**: Determines optimal bet amounts for guaranteed profit
5. **Generate Links**: Creates direct links to place bets on each sportsbook
6. **Notify & Store**: Sends Discord alerts and saves to database
7. **Repeat**: Runs on your chosen schedule for continuous monitoring

## 🤝 Contributing
- Fork the repository
- Create a feature branch
- Submit a pull request

## 📄 License
See LICENSE file for details.

---
**⚠️ Disclaimer**: Use responsibly and in accordance with local laws and sportsbook terms of service.
