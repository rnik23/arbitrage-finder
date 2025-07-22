# Handles database and Discord uploading

from lib.networkhandler import APIHandler, DiscordHandler
import json
import csv
import pytz
from datetime import datetime, timezone

class UploadWorkflow:
    def __init__(self):
        self.discord = DiscordHandler()

    def upload_bets(self, bets):
        csv_file_path = 'odds/arbitrage_bets.csv'
        metadata_file = 'data/arbitrage_metadata.txt'
        # Use user's local timezone
        import tzlocal
        local_tz = tzlocal.get_localzone()
        est = pytz.timezone('US/Eastern')
        now_utc = datetime.now(timezone.utc)
        # Overwrite metadata file each run
        with open(metadata_file, 'w') as meta_out:
            for bet in bets:
                # Format timestamp
                time_str = bet.get('time', 'N/A')
                try:
                    dt_utc = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    dt_est = dt_utc.astimezone(est)
                    dt_local = dt_utc.astimezone(local_tz)
                    est_time_str = dt_est.strftime('%Y-%m-%d %I:%M %p EST')
                    local_time_str = dt_local.strftime('%Y-%m-%d %I:%M %p %Z')
                    time_diff = (dt_utc - now_utc).total_seconds()
                    if time_diff > 0:
                        hours = int(time_diff // 3600)
                        minutes = int((time_diff % 3600) // 60)
                        status = f"Starts in {hours}h {minutes}m"
                    else:
                        status = "LIVE or started"
                except Exception:
                    est_time_str = time_str
                    local_time_str = time_str
                    status = "Unknown"
                meta_out.write(f"Event: {bet.get('home_team', 'N/A')} vs {bet.get('away_team', 'N/A')}\n")
                meta_out.write(f"  EST: {est_time_str}\n  Local: {local_time_str}\n  Status: {status}\n")
                meta_out.write(f"  Type: {bet.get('type', 'N/A')}\n")
                for stake_type in ['home_stake', 'away_stake', 'draw_stake', 'over_stake', 'under_stake']:
                    if stake_type in bet:
                        price = bet[stake_type].get('price', None)
                        american_odds = UploadWorkflow.decimal_to_american(price) if price else 'N/A'
                        meta_out.write(f"    {stake_type}: Bookmaker: {bet[stake_type].get('bookmaker', 'N/A')}, Price: {price} (American: {american_odds}), Stake: {bet[stake_type].get('stake', 'N/A')}\n")
                meta_out.write("\n")
        if bets:
            keys = set()
            for bet in bets:
                keys.update(bet.keys())
            keys = list(keys)
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=keys)
                writer.writeheader()
                writer.writerows(bets)
            print(f"Arbitrage bets saved to {csv_file_path}")
            # Optionally send to Discord
            for idx, bet in enumerate(bets, start=1):
                # Format timestamp for Discord
                time_str = bet.get('time', 'N/A')
                try:
                    dt_utc = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    dt_est = dt_utc.astimezone(est)
                    dt_local = dt_utc.astimezone(local_tz)
                    est_time_str = dt_est.strftime('%Y-%m-%d %I:%M %p EST')
                    local_time_str = dt_local.strftime('%Y-%m-%d %I:%M %p %Z')
                    time_diff = (dt_utc - now_utc).total_seconds()
                    if time_diff > 0:
                        hours = int(time_diff // 3600)
                        minutes = int((time_diff % 3600) // 60)
                        status = f"Starts in {hours}h {minutes}m"
                    else:
                        status = "LIVE or started"
                except Exception:
                    est_time_str = time_str
                    local_time_str = time_str
                    status = "Unknown"
                # Format American odds for Discord
                for stake_type in ['home_stake', 'away_stake', 'draw_stake', 'over_stake', 'under_stake']:
                    if stake_type in bet:
                        price = bet[stake_type].get('price', None)
                        american_odds = UploadWorkflow.decimal_to_american(price) if price else 'N/A'
                        bet[stake_type]['american_odds'] = american_odds
                bet['est_time'] = est_time_str
                bet['local_time'] = local_time_str
                bet['game_status'] = status
                bet['discord_number'] = idx
                self.discord.send_bet_to_discord(bet, bet.get('id', 'csv'))
        else:
            print("No arbitrage opportunities found to export.")

    @staticmethod
    def decimal_to_american(decimal_odds):
        if decimal_odds is None:
            return 'N/A'
        if decimal_odds >= 2:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"
