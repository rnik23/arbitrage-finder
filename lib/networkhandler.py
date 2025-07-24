import requests
import os
from dotenv import load_dotenv, find_dotenv
from colorama import Fore, Back, Style

load_dotenv(find_dotenv('.env.local'))

class OddsAPIHandler:
    """
    Handles fetching odds data from the Odds API with robust error handling and bookmaker filtering.
    """
    def __init__(self, sport, regions='us', markets='h2h,totals', odds_format='decimal', date_format='iso', api_key=None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.sport = sport
        self.regions = regions
        self.markets = markets
        self.odds_format = odds_format
        self.date_format = date_format

    def fetch_from_api(self, max_retries=3, timeout=10, bookmaker_filter=None):
        """
        Fetch odds from the Odds API, retrying on failure and filtering bookmakers if specified.
        Returns a list of valid events with odds data.
        """
        print(Fore.YELLOW + f'Getting the {self.sport} odds from API...' + Style.RESET_ALL)
        url = f'https://api.the-odds-api.com/v4/sports/{self.sport}/odds'
        params = {
            'api_key': self.api_key,
            'regions': self.regions,
            'markets': self.markets,
            'oddsFormat': self.odds_format,
            'dateFormat': self.date_format,
        }
        odds_json = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    odds_json = response.json()
                    print(Fore.GREEN + f'Received {len(odds_json)} events from Odds API.' + Style.RESET_ALL)
                    print(f'Remaining requests: {response.headers.get("x-requests-remaining")}, Used: {response.headers.get("x-requests-used")}')
                    break
                else:
                    print(Back.RED + f'Attempt {attempt}: API error {response.status_code}: {response.text}' + Style.RESET_ALL)
            except requests.RequestException as e:
                print(Back.RED + f'Attempt {attempt}: Network error: {e}' + Style.RESET_ALL)
        if odds_json is None:
            raise RuntimeError('Failed to fetch odds from API after multiple attempts.')
        valid_events = []
        for event in odds_json:
            bookmakers = event.get('bookmakers', [])
            if not bookmakers:
                print(Back.RED + f"Event missing bookmakers: {event.get('id', 'unknown')}" + Style.RESET_ALL)
                continue
            if bookmaker_filter:
                bookmakers = [b for b in bookmakers if b['title'] in bookmaker_filter]
                event['bookmakers'] = bookmakers
            if bookmakers:
                valid_events.append(event)
        if not valid_events:
            print(Back.RED + 'No valid events with bookmakers found.' + Style.RESET_ALL)
        return valid_events

    def print_quota(self):
        """
        Print the current API quota usage.
        """
        url = 'https://api.the-odds-api.com/v4/sports'
        params = {'api_key': self.api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Remaining requests: {response.headers.get("x-requests-remaining")}, Used: {response.headers.get("x-requests-used")}')
        else:
            print(Back.RED + f'Failed to get quota: {response.status_code} {response.text}' + Style.RESET_ALL)
    
class APIHandler:

    def __init__(self):
        self.auth_token = self.get_auth_token()

    @staticmethod
    def get_auth_token():
        url = "https://arbfiner.uk.auth0.com/oauth/token"

        payload = {
            "client_id": os.getenv('CLIENT_ID'),
            "client_secret": os.getenv('CLIENT_SECRET'),
            "audience": "https://arbitrage-finder",
            "grant_type": "client_credentials"
        }

        headers = {
            'content-type': "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(Back.RED + f'Failed to get auth token: status_code {response.status_code}, response body {response.text}' + Style.RESET_ALL)
            return None
        else:
            return response.json()['access_token']

    def post_odds_to_database(self, bet_json):

        endpoint = os.getenv('API_ENDPOINT')

        header = {
            'Authorization': f'Bearer {self.auth_token}'
        }

        response = requests.post(endpoint, json=bet_json, headers=header)

        if response.status_code not in [200, 201]:
            print(Back.RED + f'Failed to post odds to database: status_code {response.status_code}, response body {response.json()["message"]}' + Style.RESET_ALL)
            return None
        else:
            print(Fore.GREEN + 'Odds posted to database!' + Style.RESET_ALL)
            return response.json()["data"]["_id"]
    
class DiscordHandler:

    def __init__(self) -> None:
        self.DISCORD_WEBWHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

    @staticmethod
    def _send_post_request(bot_name: str, message_body: str, webhook_url: str) -> requests.Response:

        if webhook_url == "":
            raise EnvironmentError(
                "No webhook URL found. Set the Discord Webhook URL before deploying. "
                "Learn more about Discord webhooks here: "
                "https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks"
            )
        
        return requests.post(
            url=webhook_url,
            json={
                'username': bot_name,
                'content': message_body
            }
        )

    def send_bet_to_discord(self, bet: dict, bet_id: str) -> None :
        number = bet.get('discord_number', '')
        sport = bet['sport']
        time = bet.get('est_time', bet['time'])
        home_team = bet['home_team']
        away_team = bet['away_team']
        if bet['type'] == 'h2h':
            stakes = {'home': bet['home_stake'], 'away': bet['away_stake']}
            message = f"""
{number}) ## 💎 New Head 2 Head Opportunity 💎

**Sport:** {sport}
**Match:** {home_team} (Home) vs {away_team} (Away) at {time}
**Teams:**
    Home: {home_team}
    Away: {away_team}
**Time:**
    EST: {bet.get('est_time', time)}
    Local: {bet.get('local_time', time)}
    Status: {bet.get('game_status', '')}
**Stakes:**
    *Home:* Stake £{stakes['home']['stake']} with {stakes['home']['bookmaker']} @ {stakes['home']['price']} (American: {stakes['home'].get('american_odds', 'N/A')})
    *Away:* Stake £{stakes['away']['stake']} with {stakes['away']['bookmaker']} @ {stakes['away']['price']} (American: {stakes['away'].get('american_odds', 'N/A')})

for a return of {bet['roi']}%
""".strip()
        elif bet['type'] == 'totals':
            stakes = {'over': bet['over_stake'], 'under': bet['under_stake']}
            message = f"""
{number}) ## 💎 New Totals Opportunity 💎

**Sport:** {sport}
**Match:** {home_team} (Home) vs {away_team} (Away) at {time}
**Teams:**
    Home: {home_team}
    Away: {away_team}
**Time:**
    EST: {bet.get('est_time', time)}
    Local: {bet.get('local_time', time)}
    Status: {bet.get('game_status', '')}
**Stakes:**
    *Over {stakes['over']['point']}:* Stake £{stakes['over']['stake']} with {stakes['over']['bookmaker']} @ {stakes['over']['price']} (American: {stakes['over'].get('american_odds', 'N/A')})
    *Under {stakes['under']['point']}:* Stake £{stakes['under']['stake']} with {stakes['under']['bookmaker']} @ {stakes['under']['price']} (American: {stakes['under'].get('american_odds', 'N/A')})

for a return of {bet['roi']}%
""".strip()
        else:
            stakes = {}
            message = f"""
{number}) ## 💎 New Laybet Opportunity 💎

**Sport:** {sport}
**Match:** {home_team} vs {away_team} at {time}
**Stakes:** """
            if 'home_stake' in bet:
                stakes['home'] = bet['home_stake']
                message += f""" 
            *Home:*     Back Stake £100 with {stakes['home']['back_bookmaker']} @ {stakes['home']['back_price']}
                        Lay Stake £{stakes['home']['lay_stake']} with {stakes['home']['lay_bookmaker']} @ {stakes['home']['lay_price']}
                        for a profit of £{stakes['home']['profit']}"""
            elif 'away_stake' in bet:
                stakes['away'] = bet['away_stake']
                message += f""" 
            *Away:*     Back Stake £100 with {stakes['away']['back_bookmaker']} @ {stakes['away']['back_price']}
                        Lay Stake £{stakes['away']['lay_stake']} with {stakes['away']['lay_bookmaker']} @ {stakes['away']['lay_price']}
                        for a profit of £{stakes['away']['profit']}"""
            elif 'draw_stake' in bet:
                stakes['draw']= bet['draw_stake']
                message += f""" 
            *Draw:*     Back Stake £100 with {stakes['draw']['back_bookmaker']} @ {stakes['draw']['back_price']}
                        Lay Stake £{stakes['draw']['lay_stake']} with {stakes['draw']['lay_bookmaker']} @ {stakes['draw']['lay_price']}
                        for a profit of £{stakes['draw']['profit']}"""

            message.strip()

        try:
            # [START v2SendToDiscord]
            response = self._send_post_request(
                "Arb Bot", message, self.DISCORD_WEBWHOOK_URL
            )
            if response.ok:
                print(f"Posted bet @{bet_id} to Discord.")
            else:
                response.raise_for_status()
            # [END v2SendToDiscord]
        except (EnvironmentError, requests.HTTPError) as error:
            print(f"Unable to post fatal Arb bet @{bet_id} to Discord.", error)