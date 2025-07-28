import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime
from typing import List, Dict, Any

class ArbitrageDatabase:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            # Fallback to individual components
            host = os.getenv('DB_HOST', 'postgres')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'arbitrage_finder')
            user = os.getenv('DB_USER', 'arbitrage_user')
            password = os.getenv('DB_PASSWORD', 'arbitrage_password')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def get_connection(self):
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def create_run(self, sport: str, events_count: int = 0, bookmakers: List[str] = None, 
                   game_status: str = 'all') -> int:
        """Create a new arbitrage run record and return the run ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO arbitrage_runs (sport, events_count, bookmakers_included, game_status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (sport, events_count, bookmakers or [], game_status))
                return cur.fetchone()['id']
    
    def update_run_stats(self, run_id: int, arbitrages_found: int, 
                        api_requests_used: int = None, api_requests_remaining: int = None):
        """Update run statistics."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE arbitrage_runs 
                    SET arbitrages_found = %s, api_requests_used = %s, api_requests_remaining = %s
                    WHERE id = %s
                """, (arbitrages_found, api_requests_used, api_requests_remaining, run_id))
    
    def save_arbitrage_opportunity(self, run_id: int, arb_data: Dict[str, Any]) -> int:
        """Save an arbitrage opportunity and return the arbitrage ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Convert timestamp if it's a float (UNIX timestamp)
                event_time = arb_data.get('time')
                if isinstance(event_time, (int, float)):
                    event_time = datetime.fromtimestamp(event_time)
                
                cur.execute("""
                    INSERT INTO arbitrage_opportunities 
                    (run_id, event_id, sport, market_type, home_team, away_team, event_time, roi_percentage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    run_id, arb_data.get('id'), arb_data.get('sport'), arb_data.get('type'),
                    arb_data.get('home_team'), arb_data.get('away_team'), event_time, arb_data.get('roi')
                ))
                return cur.fetchone()['id']
    
    def save_arbitrage_stakes(self, arbitrage_id: int, arb_data: Dict[str, Any]):
        """Save the stakes for an arbitrage opportunity."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                stake_types = ['home_stake', 'away_stake', 'draw_stake', 'over_stake', 'under_stake']
                
                for stake_type in stake_types:
                    if stake_type in arb_data:
                        stake_data = arb_data[stake_type]
                        cur.execute("""
                            INSERT INTO arbitrage_stakes 
                            (arbitrage_id, stake_type, bookmaker, price, american_odds, stake_amount, betting_link, point_spread)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            arbitrage_id, stake_type.replace('_stake', ''), stake_data.get('bookmaker'),
                            stake_data.get('price'), stake_data.get('american_odds'), stake_data.get('stake'),
                            stake_data.get('betting_link'), stake_data.get('point')
                        ))
    
    def save_odds_snapshot(self, run_id: int, odds_data: List[Dict[str, Any]]):
        """Save odds data for historical analysis."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for event in odds_data:
                    for bookmaker in event.get('bookmakers', []):
                        for market in bookmaker.get('markets', []):
                            for outcome in market.get('outcomes', []):
                                cur.execute("""
                                    INSERT INTO odds_snapshots 
                                    (run_id, event_id, sport, bookmaker, market_type, outcome_name, price)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    run_id, event.get('id'), event.get('sport_key'),
                                    bookmaker.get('title'), market.get('key'), 
                                    outcome.get('name'), outcome.get('price')
                                ))
    
    def get_recent_arbitrages(self, sport: str = None, hours: int = 24) -> List[Dict]:
        """Get recent arbitrage opportunities."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT * FROM arbitrage_summary 
                    WHERE run_timestamp >= NOW() - INTERVAL '%s hours'
                """
                params = [hours]
                
                if sport:
                    query += " AND sport = %s"
                    params.append(sport)
                
                query += " ORDER BY run_timestamp DESC"
                
                cur.execute(query, params)
                return cur.fetchall()
    
    def get_run_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics for recent runs."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        sport,
                        COUNT(*) as total_runs,
                        SUM(arbitrages_found) as total_arbitrages,
                        AVG(arbitrages_found) as avg_arbitrages_per_run,
                        SUM(events_count) as total_events_analyzed
                    FROM arbitrage_runs 
                    WHERE run_timestamp >= NOW() - INTERVAL '%s days'
                    GROUP BY sport
                    ORDER BY total_arbitrages DESC
                """, (days,))
                return cur.fetchall()
