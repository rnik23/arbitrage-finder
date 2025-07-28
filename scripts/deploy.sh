#!/bin/bash

# Production deployment script for Arbitrage Finder

echo "🚀 Deploying Arbitrage Finder Production Environment..."

# Create environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# Odds API Configuration
ODDS_API_KEY=your_odds_api_key_here

# Discord Configuration
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Database Configuration
POSTGRES_PASSWORD=secure_database_password_here
DATABASE_URL=postgresql://arb_user:secure_database_password_here@postgres:5432/arbitrage_db

# Optional: Auth0 Configuration (if using API uploads)
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
API_ENDPOINT=your_api_endpoint_here
EOF
    echo "⚠️ Please update .env.local with your actual API keys and credentials!"
    exit 1
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🗄️ Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🎯 Running database migrations..."
docker-compose exec postgres psql -U arb_user -d arbitrage_db -c "SELECT version();"

echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Deployment complete!"
echo ""
echo "📋 Service Status:"
docker-compose ps

echo ""
echo "📊 Database Status:"
docker-compose exec postgres psql -U arb_user -d arbitrage_db -c "SELECT COUNT(*) as total_runs FROM arbitrage_runs;"

echo ""
echo "🔧 Useful Commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Database shell: docker-compose exec postgres psql -U arb_user -d arbitrage_db"
echo "  Run manual scan: docker-compose run arbitrage-finder python src/main_production.py --sport baseball_mlb --save-to-db"
