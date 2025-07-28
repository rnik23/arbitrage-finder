# Enhanced main script with database integration

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from odds_workflow import OddsWorkflow
from arbitrage_workflow import ArbitrageWorkflow
from upload_workflow import UploadWorkflow
from csv_export import CSVExport
from lib.database import ArbitrageDatabase
import json
from colorama import Fore, Back, Style
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description="Find arbitrage opportunities for a specific sport.")
    parser.add_argument('--sport', type=str, required=True, help='Sport key (e.g., soccer_usa_mls, basketball_nba)')
    parser.add_argument('--show-metadata', action='store_true', help='Show metadata for odds API calls')
    parser.add_argument('--game-status', type=str, choices=['live', 'future', 'all'], default='all', help='Filter arbitrage for live, future, or all games')
    parser.add_argument('--include-bookmakers', type=str, nargs='+', help='Only include these bookmakers (e.g., --include-bookmakers "DraftKings" "FanDuel")')
    parser.add_argument('--exclude-bookmakers', type=str, nargs='+', help='Exclude these bookmakers (e.g., --exclude-bookmakers "Bovada" "MyBookie.ag")')
    parser.add_argument('--save-to-db', action='store_true', help='Save results to PostgreSQL database')
    args = parser.parse_args()

    print(Back.MAGENTA + "       Welcome to the Arbitrage Finder!       " + Style.RESET_ALL)
    print(Fore.MAGENTA + f"This program will find arbitrage opportunities for {args.sport}." + Style.RESET_ALL +"\n")

    # Initialize database if needed
    db = None
    run_id = None
    if args.save_to_db:
        try:
            db = ArbitrageDatabase()
            bookmakers = args.include_bookmakers or (args.exclude_bookmakers and ['all_except_excluded']) or ['default']
            run_id = db.create_run(args.sport, bookmakers=bookmakers, game_status=args.game_status)
            print(f"📊 Database run created with ID: {run_id}")
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
            print("Continuing without database storage...")

    # Clear odds and metadata files before each run
    with open('data/odds/all_odds.json', 'w') as f:
        f.write('')
    with open('data/metadata/arbitrage_run_metadata.txt', 'w') as f:
        f.write('')

    # Fetch odds
    odds_workflow = OddsWorkflow(
        sport=args.sport, 
        include_bookmakers=args.include_bookmakers,
        exclude_bookmakers=args.exclude_bookmakers
    )
    odds_data = odds_workflow.fetch_and_format_odds(show_metadata=args.show_metadata)
    print(Back.GREEN + Fore.BLACK + "Formatting complete!" + Style.RESET_ALL + "\n")

    # Update database with events count
    if db and run_id:
        try:
            events_count = len(odds_data) if odds_data else 0
            # Note: You'll need to capture API usage from odds_workflow
            db.update_run_stats(run_id, arbitrages_found=0)  # Will update later
            if odds_data:
                db.save_odds_snapshot(run_id, odds_data)
            print(f"📊 Saved {events_count} events to database")
        except Exception as e:
            print(f"⚠️ Database update failed: {e}")

    # Load formatted odds data
    with open('data/all_odds.json', 'r') as infile:
        database = json.load(infile)

    # Find arbitrage opportunities
    arbitrage_workflow = ArbitrageWorkflow(database)
    bets = arbitrage_workflow.find_arbitrage()
    print(Back.GREEN + Fore.BLACK + "Searching complete!" + Style.RESET_ALL + "\n")

    # Filter bets based on game status with debug output
    filtered_bets = []
    now_utc = datetime.now(timezone.utc)
    for bet in bets:
        time_val = bet.get('time', None)
        print(f"DEBUG: bet id={bet.get('id', 'N/A')}, time_val={time_val}")
        if time_val:
            try:
                # If time_val is a float or int, treat as UNIX timestamp
                if isinstance(time_val, (float, int)):
                    dt_utc = datetime.fromtimestamp(time_val, tz=timezone.utc)
                else:
                    dt_utc = datetime.fromisoformat(str(time_val).replace('Z', '+00:00'))
                print(f"DEBUG: Parsed dt_utc={dt_utc}, now_utc={now_utc}")
                time_diff = (dt_utc - now_utc).total_seconds()
                print(f"DEBUG: time_diff={time_diff}")
                if args.game_status == 'future' and time_diff > 0:
                    filtered_bets.append(bet)
                elif args.game_status == 'live' and time_diff <= 0:
                    filtered_bets.append(bet)
                elif args.game_status == 'all':
                    filtered_bets.append(bet)
            except Exception as e:
                print(f"DEBUG: Failed to parse time for bet id={bet.get('id', 'N/A')}, error={e}")
                if args.game_status == 'all':
                    filtered_bets.append(bet)
        else:
            print(f"DEBUG: No time found for bet id={bet.get('id', 'N/A')}")
            if args.game_status == 'all':
                filtered_bets.append(bet)

    # Save arbitrage opportunities to database
    if db and run_id and filtered_bets:
        try:
            for bet in filtered_bets:
                arb_id = db.save_arbitrage_opportunity(run_id, bet)
                db.save_arbitrage_stakes(arb_id, bet)
            db.update_run_stats(run_id, arbitrages_found=len(filtered_bets))
            print(f"📊 Saved {len(filtered_bets)} arbitrage opportunities to database")
        except Exception as e:
            print(f"⚠️ Failed to save arbitrage opportunities: {e}")

    # Upload and notify
    upload_workflow = UploadWorkflow()
    upload_workflow.upload_bets(filtered_bets)
    print(Back.GREEN + Fore.BLACK + "Upload complete!" + Style.RESET_ALL + "\n")

    print(Fore.YELLOW + "Exporting arbitrage opportunities to CSV..." + Style.RESET_ALL)
    CSVExport.export_to_csv(filtered_bets)

    # Print summary
    print(f"\n🎯 Run Summary:")
    print(f"   Sport: {args.sport}")
    print(f"   Events analyzed: {len(odds_data) if odds_data else 0}")
    print(f"   Arbitrage opportunities found: {len(filtered_bets)}")
    if db and run_id:
        print(f"   Database run ID: {run_id}")

if __name__ == "__main__":
    main()
