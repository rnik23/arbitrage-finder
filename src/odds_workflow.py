# Handles odds fetching and formatting

from lib.networkhandler import OddsAPIHandler
from lib.betting_odds_database import BettingOddsDatabase
import os
import json
import pytz
from datetime import datetime

class OddsWorkflow:
    def __init__(self, sport='basketball_nba', include_bookmakers=None, exclude_bookmakers=None):
        self.odds_api = OddsAPIHandler(sport)
        
        # Handle bookmaker filtering logic
        if include_bookmakers:
            # Include-only mode: only analyze specified bookmakers
            self.database = BettingOddsDatabase(include_bookmakers=set(include_bookmakers))
        elif exclude_bookmakers:
            # Exclude mode: analyze all except specified bookmakers
            self.database = BettingOddsDatabase(ignore_bookmakers=set(exclude_bookmakers))
        else:
            # Default: exclude Bovada only
            self.database = BettingOddsDatabase(ignore_bookmakers={'Bovada'})
        
        self.sport = sport

    @staticmethod
    def decimal_to_american(decimal_odds):
        if decimal_odds >= 2:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"

    def fetch_and_format_odds(self, show_metadata=False):
        print("DEBUG: Starting odds fetch and format workflow...")
        # Fetch odds for the specified sport and save to odds folder
        odds_data = self.odds_api.fetch_from_api()
        print(f"DEBUG: Odds data fetched, events count: {len(odds_data)}")
        odds_file = f'odds/{self.sport}.json'
        with open(odds_file, 'w') as output:
            json.dump(odds_data, output)
        print(f"DEBUG: Odds data written to {odds_file}")
        # Format the newly created odds file
        self.database.formatJSON(odds_file)
        print(f"DEBUG: Odds data formatted by BettingOddsDatabase")
        with open('data/all_odds.json', 'w') as outfile:
            json.dump(self.database.database, outfile, indent=4)
        print("DEBUG: Formatted odds written to data/all_odds.json")
        if show_metadata:
            metadata_file = f'data/{self.sport}_metadata.txt'
            est = pytz.timezone('US/Eastern')
            with open(metadata_file, 'w') as meta_out:
                for event in odds_data:
                    teams = f"{event.get('home_team', 'N/A')} vs {event.get('away_team', 'N/A')}"
                    # Convert ISO time to EST
                    start_time = event.get('commence_time', None)
                    if start_time:
                        try:
                            dt_utc = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            dt_est = dt_utc.astimezone(est)
                            est_time_str = dt_est.strftime('%Y-%m-%d %I:%M %p EST')
                        except Exception:
                            est_time_str = start_time
                    else:
                        est_time_str = 'N/A'
                    meta_out.write(f"Event: {teams} at {est_time_str}\n")
                    print(f"Event: {teams} at {est_time_str}")
                    for bookmaker in event.get('bookmakers', []):
                        meta_out.write(f"  Sportsbook: {bookmaker['title']}\n")
                        print(f"  Sportsbook: {bookmaker['title']}")
                        for market in bookmaker.get('markets', []):
                            meta_out.write(f"    Market: {market['key']}\n")
                            print(f"    Market: {market['key']}")
                            for outcome in market.get('outcomes', []):
                                american_odds = self.decimal_to_american(outcome['price'])
                                meta_out.write(f"      Outcome: {outcome['name']}, Odds: {outcome['price']} (American: {american_odds})\n")
                                print(f"      Outcome: {outcome['name']}, Odds: {outcome['price']} (American: {american_odds})")
                    meta_out.write("\n")
                    print()
