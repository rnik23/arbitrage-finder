# Main orchestration script
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from odds_workflow import OddsWorkflow
from arbitrage_workflow import ArbitrageWorkflow
from upload_workflow import UploadWorkflow
from csv_export import CSVExport
import json
from colorama import Fore, Back, Style

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find arbitrage opportunities for a specific sport.")
    parser.add_argument('--sport', type=str, required=True, help='Sport key (e.g., soccer_usa_mls, basketball_nba)')
    parser.add_argument('--show-metadata', action='store_true', help='Show metadata for odds API calls')
    parser.add_argument('--game-status', type=str, choices=['live', 'future', 'all'], default='all', help='Filter arbitrage for live, future, or all games')
    args = parser.parse_args()

    print(Back.MAGENTA + "       Welcome to the Arbitrage Finder!       " + Style.RESET_ALL)
    print(Fore.MAGENTA + f"This program will find arbitrage opportunities for {args.sport}." + Style.RESET_ALL +"\n")

    odds_workflow = OddsWorkflow(sport=args.sport)
    odds_workflow.fetch_and_format_odds(show_metadata=args.show_metadata)
    print(Back.GREEN + Fore.BLACK + "Formatting complete!" + Style.RESET_ALL + "\n")

    with open('data/all_odds.json', 'r') as infile:
        database = json.load(infile)

    arbitrage_workflow = ArbitrageWorkflow(database)
    bets = arbitrage_workflow.find_arbitrage()
    print(Back.GREEN + Fore.BLACK + "Searching complete!" + Style.RESET_ALL + "\n")

    # Filter bets based on game status with debug output
    from datetime import datetime, timezone
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

    upload_workflow = UploadWorkflow()
    upload_workflow.upload_bets(filtered_bets)
    print(Back.GREEN + Fore.BLACK + "Upload complete!" + Style.RESET_ALL + "\n")

    print(Fore.YELLOW + "Exporting arbitrage opportunities to CSV..." + Style.RESET_ALL)
    CSVExport.export_to_csv(filtered_bets)
