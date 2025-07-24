import requests
import pytest
import json

# Fetch odds from DraftKings API for a specific event
# Replace <EVENT_ID> and <API_URL> as needed
DRAFTKINGS_API_URL = 'https://sportsbook.draftkings.com//sites/US-SB/api/v5/event/<EVENT_ID>'  # TODO: update with real event ID

# Fetch odds from DraftKings API

def get_draftkings_odds(event_id):
    url = DRAFTKINGS_API_URL.replace('<EVENT_ID>', str(event_id))
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    odds = {}
    # Example: parse markets and outcomes (site-specific)
    for market in data.get('event', {}).get('markets', []):
        market_key = market.get('key')
        odds[market_key] = {}
        for outcome in market.get('outcomes', []):
            odds[market_key][outcome['name']] = outcome['price']
    return odds

# Extract odds from your API event JSON

def get_api_odds(api_event, bookmaker='DraftKings'):
    for b in api_event['bookmakers']:
        if b['title'] == bookmaker:
            api_odds = {}
            for market in b['markets']:
                market_key = market['key']
                api_odds[market_key] = {}
                for outcome in market['outcomes']:
                    api_odds[market_key][outcome['name']] = outcome['price']
            return api_odds
    return {}

# Main test function

def test_odds_consistency():
    # Load API event from a saved file
    with open('testdata/api_event.json') as f:
        api_event = json.load(f)
    # Use the event ID from the API event
    event_id = api_event.get('id')
    draftkings_odds = get_draftkings_odds(event_id)
    api_odds = get_api_odds(api_event)
    for market in api_odds:
        assert market in draftkings_odds, f"Market {market} missing in DraftKings API data"
        for outcome in api_odds[market]:
            assert outcome in draftkings_odds[market], f"Outcome {outcome} missing in market {market}"
            assert api_odds[market][outcome] == draftkings_odds[market][outcome], (
                f"Odds mismatch for {market} - {outcome}: API={api_odds[market][outcome]}, DraftKings={draftkings_odds[market][outcome]}"
            )
