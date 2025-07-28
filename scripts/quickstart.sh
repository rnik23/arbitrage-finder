#!/bin/bash

# Quick start deployment script for Arbitrage Finder

echo "🎯 Arbitrage Finder - Docker Quick Start"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📋 Creating .env file from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your actual API keys before continuing!"
        echo "   Required: ODDS_API_KEY (get from https://the-odds-api.com)"
        echo "   Optional: DISCORD_WEBHOOK_URL"
        echo ""
        read -p "Press Enter after updating .env file..."
    else
        echo "❌ .env.example file not found. Creating basic .env..."
        cat > .env << EOF
ODDS_API_KEY=your_odds_api_key_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
DB_HOST=postgres
DB_PORT=5432
DB_NAME=arbitrage_finder
DB_USER=arbitrage_user
DB_PASSWORD=arbitrage_password
EOF
        echo "⚠️  Please edit .env file with your actual API keys!"
        exit 1
    fi
fi

# Check if API key is set
if grep -q "your_odds_api_key_here" .env; then
    echo "⚠️  Warning: Please update ODDS_API_KEY in .env file with your actual API key"
    echo "   Get one free at: https://the-odds-api.com"
    read -p "Continue anyway for testing? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting deployment..."

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans -v

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🗄️  Starting PostgreSQL database..."
docker-compose up postgres -d

# Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
sleep 15

# Create database user with proper permissions
echo "👤 Setting up database user..."
docker-compose exec postgres psql -U postgres -d arbitrage_finder -c "
CREATE USER arbitrage_user WITH PASSWORD 'arbitrage_password';
GRANT ALL PRIVILEGES ON SCHEMA public TO arbitrage_user;
GRANT CREATE ON SCHEMA public TO arbitrage_user;
" 2>/dev/null || echo "User may already exist, continuing..."

# Initialize database schema
echo "🗄️  Initializing database schema..."
docker-compose run --rm arbitrage-finder python scripts/init_db.py

# Test database connection
echo "🧪 Testing database connection..."
if docker-compose run --rm arbitrage-finder python scripts/test_db.py > /dev/null 2>&1; then
    echo "✅ Database test successful!"
else
    echo "❌ Database test failed. Check logs with: docker-compose logs"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Quick Commands:"
echo "  # Test MLB scan:"
echo "  docker-compose run arbitrage-finder python src/main_production.py --sport baseball_mlb --save-to-db"
echo ""
echo "  # Start automated scheduler:"
echo "  ./scripts/scheduler.sh"
echo ""
echo "  # View logs:"
echo "  docker-compose logs -f"
echo ""
echo "  # Database shell:"
echo "  docker-compose exec postgres psql -U arbitrage_user -d arbitrage_finder"
echo ""
echo "  # Stop services:"
echo "  docker-compose down"
