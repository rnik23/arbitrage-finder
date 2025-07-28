#!/usr/bin/env python3
"""
Test script for database integration without API calls
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.database import ArbitrageDatabase
import json
from datetime import datetime

def test_database():
    """Test database functionality with mock data"""
    try:
        print("🧪 Testing database integration...")
        
        # Initialize database
        db = ArbitrageDatabase()
        print("✅ Database connection successful!")
        
        # Create a test run
        run_id = db.create_run(
            sport='baseball_mlb', 
            events_count=5, 
            bookmakers=['DraftKings', 'FanDuel', 'BetMGM'],
            game_status='all'
        )
        print(f"📊 Created test run with ID: {run_id}")
        
        # Create mock arbitrage opportunity
        mock_arb = {
            'id': 'test_event_123',
            'sport': 'baseball_mlb',
            'type': 'h2h',
            'home_team': 'New York Yankees',
            'away_team': 'Boston Red Sox',
            'time': datetime.now().timestamp(),
            'roi': 5.2,
            'home_stake': {
                'bookmaker': 'DraftKings',
                'price': 2.1,
                'stake': 47.6,
                'american_odds': '+110',
                'betting_link': 'https://sportsbook.draftkings.com/leagues/baseball/mlb'
            },
            'away_stake': {
                'bookmaker': 'FanDuel',
                'price': 2.0,
                'stake': 52.4,
                'american_odds': '+100',
                'betting_link': 'https://sportsbook.fanduel.com/baseball'
            }
        }
        
        # Save arbitrage opportunity
        arb_id = db.save_arbitrage_opportunity(run_id, mock_arb)
        print(f"💎 Saved arbitrage opportunity with ID: {arb_id}")
        
        # Save stakes
        db.save_arbitrage_stakes(arb_id, mock_arb)
        print("📈 Saved arbitrage stakes")
        
        # Update run stats
        db.update_run_stats(run_id, arbitrages_found=1, api_requests_used=1, api_requests_remaining=999)
        print("📊 Updated run statistics")
        
        # Test queries
        recent_arbs = db.get_recent_arbitrages(sport='baseball_mlb', hours=1)
        print(f"🔍 Found {len(recent_arbs)} recent arbitrages")
        
        stats = db.get_run_statistics(days=1)
        print(f"📈 Run statistics: {stats}")
        
        print("🎉 Database integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    test_database()
