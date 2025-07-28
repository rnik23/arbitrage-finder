# Sportsbook URL mappings for deep linking
SPORTSBOOK_URLS = {
    'DraftKings': {
        'base_url': 'https://sportsbook.draftkings.com',
        'sport_paths': {
            'baseball_mlb': '/leagues/baseball/mlb',
            'basketball_nba': '/leagues/basketball/nba',
            'basketball_wnba': '/leagues/basketball/wnba',
            'americanfootball_nfl': '/leagues/football/nfl',
            'icehockey_nhl': '/leagues/hockey/nhl',
            'soccer_usa_mls': '/leagues/soccer/mls'
        }
    },
    'FanDuel': {
        'base_url': 'https://sportsbook.fanduel.com',
        'sport_paths': {
            'baseball_mlb': '/baseball',
            'basketball_nba': '/basketball',
            'basketball_wnba': '/basketball/wnba',
            'americanfootball_nfl': '/football',
            'icehockey_nhl': '/hockey',
            'soccer_usa_mls': '/soccer'
        }
    },
    'BetMGM': {
        'base_url': 'https://sports.betmgm.com',
        'sport_paths': {
            'baseball_mlb': '/en/sports/baseball-23',
            'basketball_nba': '/en/sports/basketball-7',
            'basketball_wnba': '/en/sports/basketball-7',
            'americanfootball_nfl': '/en/sports/football-11',
            'icehockey_nhl': '/en/sports/ice-hockey-12',
            'soccer_usa_mls': '/en/sports/soccer-4'
        }
    },
    'Caesars': {
        'base_url': 'https://sportsbook.caesars.com',
        'sport_paths': {
            'baseball_mlb': '/us/sport/baseball',
            'basketball_nba': '/us/sport/basketball',
            'basketball_wnba': '/us/sport/basketball',
            'americanfootball_nfl': '/us/sport/american-football',
            'icehockey_nhl': '/us/sport/ice-hockey',
            'soccer_usa_mls': '/us/sport/soccer'
        }
    }
}

def generate_sportsbook_link(bookmaker, sport, home_team=None, away_team=None):
    """
    Generate a deep link to the sportsbook for the specific sport/game.
    Falls back to sport section if specific game link isn't available.
    """
    if bookmaker not in SPORTSBOOK_URLS:
        return None
    
    sportsbook = SPORTSBOOK_URLS[bookmaker]
    base_url = sportsbook['base_url']
    
    if sport in sportsbook['sport_paths']:
        sport_path = sportsbook['sport_paths'][sport]
        return f"{base_url}{sport_path}"
    
    # Fallback to base URL if sport not mapped
    return base_url

def add_betting_links_to_arb(arb_data):
    """
    Add betting links to arbitrage opportunity data.
    """
    sport = arb_data.get('sport')
    home_team = arb_data.get('home_team')
    away_team = arb_data.get('away_team')
    
    # Add links for each stake bookmaker
    for stake_type in ['home_stake', 'away_stake', 'draw_stake', 'over_stake', 'under_stake']:
        if stake_type in arb_data:
            bookmaker = arb_data[stake_type].get('bookmaker')
            if bookmaker:
                link = generate_sportsbook_link(bookmaker, sport, home_team, away_team)
                if link:
                    arb_data[stake_type]['betting_link'] = link
    
    return arb_data
