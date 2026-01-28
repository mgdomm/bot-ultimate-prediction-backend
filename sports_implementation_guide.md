# Practical Implementation Guide: Tennis & MLB APIs

## QUICK START: Copy-Paste Examples

### Installation Requirements
```bash
# Core libraries
pip install requests beautifulsoup4 selenium lxml

# Optional for advanced analysis
pip install pybaseball pandas numpy

# For the Odds API wrapper
pip install odds-api-wrapper
```

---

## MLB: QUICK START (5 minutes)

### Example 1: Get Today's Games
```python
import requests
from datetime import datetime

def get_todays_mlb_games():
    """Fetch all MLB games for today"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule"
    params = {'date': today}
    
    response = requests.get(url, params=params)
    games = response.json()
    
    print(f"\n📊 MLB Games for {today}\n")
    print("-" * 70)
    
    for game in games:
        away = game['teams']['away']['team']['name']
        home = game['teams']['home']['team']['name']
        status = game['status']['detailedState']
        game_id = game['gamePk']
        
        print(f"🏟️  {away:20} @ {home:20} | Status: {status}")
    
    return games

# Run it
games = get_todays_mlb_games()
```

---

### Example 2: Get Live Game Stats
```python
import requests
import json

def get_live_game_data(game_id):
    """Get detailed live data for a specific game"""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/linescore"
    
    response = requests.get(url)
    data = response.json()
    
    game = data.get('game', {})
    print(f"\n🎮 Live Game Data (ID: {game_id})")
    print("-" * 70)
    print(f"Status: {game.get('status', 'Unknown')}")
    print(f"Inning: {data.get('currentInning', 'N/A')}")
    print(f"Outs: {data.get('outs', 'N/A')}")
    
    # Score by inning
    teams = data.get('teams', {})
    away_runs = teams.get('away', {}).get('runs', 0)
    home_runs = teams.get('home', {}).get('runs', 0)
    print(f"\nScore: {away_runs} - {home_runs}")
    
    return data

# Usage: get_live_game_data(694145)  # Example game ID
```

---

### Example 3: Get Player Stats
```python
import requests

def get_player_stats(player_id):
    """Fetch detailed statistics for a specific player"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    
    response = requests.get(url)
    data = response.json()
    person = data.get('people', [{}])[0]
    
    print(f"\n👤 Player Stats: {person.get('fullName', 'Unknown')}")
    print("-" * 70)
    print(f"Position: {person.get('primaryPosition', {}).get('name', 'N/A')}")
    print(f"Jersey #: {person.get('primaryNumber', 'N/A')}")
    print(f"Bat/Throw: {person.get('batSide', {}).get('code', 'N/A')}/{person.get('pitchHand', {}).get('code', 'N/A')}")
    
    return data

# Mike Trout's ID is 545361
# Usage: get_player_stats(545361)
```

---

### Example 4: Standings & Rankings
```python
import requests

def get_mlb_standings(season=2025):
    """Fetch current league standings"""
    url = f"https://statsapi.mlb.com/api/v1/standings"
    params = {'leagueId': '103,104', 'season': season}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    records = data.get('records', [])
    
    for division in records:
        print(f"\n🏆 {division['division']['name']}")
        print("-" * 60)
        
        for team_record in division['teamRecords']:
            team = team_record['team']['name']
            wins = team_record['wins']
            losses = team_record['losses']
            gb = team_record.get('gamesBack', '—')
            
            print(f"{team:20} | W: {wins:2} L: {losses:2} | GB: {gb}")
    
    return data

# Usage: get_mlb_standings(2025)
```

---

## TENNIS: QUICK START

### Example 1: Get ATP Matches via ESPN
```python
import requests
import json

def get_atp_matches():
    """Fetch current ATP matches from ESPN"""
    url = "https://site.api.espn.com/us/site/v2/sports/tennis/atp"
    
    response = requests.get(url)
    data = response.json()
    
    events = data.get('events', [])
    
    print(f"\n🎾 ATP Matches ({len(events)} total)")
    print("-" * 70)
    
    for event in events[:10]:  # Show first 10
        competitors = event.get('competitors', [])
        if len(competitors) >= 2:
            player1 = competitors[0].get('displayName', 'Unknown')
            player2 = competitors[1].get('displayName', 'Unknown')
            status = event.get('status', 'Unknown')
            
            print(f"🏆 {player1:25} vs {player2:25} | {status}")
    
    return events

# Usage: get_atp_matches()
```

---

### Example 2: Get WTA Matches
```python
import requests

def get_wta_matches():
    """Fetch current WTA matches"""
    url = "https://site.api.espn.com/us/site/v2/sports/tennis/wta"
    
    response = requests.get(url)
    data = response.json()
    
    events = data.get('events', [])
    
    print(f"\n👩‍🦰 WTA Matches ({len(events)} total)")
    print("-" * 70)
    
    for event in events[:10]:
        competitors = event.get('competitors', [])
        if len(competitors) >= 2:
            player1 = competitors[0].get('displayName', 'Unknown')
            player2 = competitors[1].get('displayName', 'Unknown')
            
            # Rankings (if available)
            rank1 = competitors[0].get('seed', 'NR')
            rank2 = competitors[1].get('seed', 'NR')
            
            print(f"({rank1}) {player1:23} vs ({rank2}) {player2:23}")
    
    return events

# Usage: get_wta_matches()
```

---

### Example 3: Tennis Scores with Scraping (Advanced)
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_live_tennis_scores():
    """Scrape live tennis scores from a public source"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.tennis-explorer.com/live/")
        
        # Wait for matches to load (JS rendered)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "match"))
        )
        
        matches = driver.find_elements(By.CLASS_NAME, "match")
        
        print(f"\n🎾 Live Tennis Scores ({len(matches)} matches)")
        print("-" * 70)
        
        for match in matches[:10]:  # Get first 10
            try:
                match_text = match.text
                if match_text:
                    # Parse the match data
                    lines = match_text.split('\n')
                    for line in lines[:5]:  # Show first 5 lines per match
                        print(f"  {line}")
                    print("  " + "-" * 60)
            except:
                pass
        
        time.sleep(2)  # Be respectful with scraping
        
    finally:
        driver.quit()

# Usage: scrape_live_tennis_scores()
```

---

## BETTING ODDS: QUICK START

### Example 1: Get Tennis Odds (The Odds API)
```python
import requests
from typing import List, Dict

class OddsAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_sports(self) -> List:
        """Get available sports"""
        url = f"{self.base_url}/sports"
        params = {'api_key': self.api_key}
        
        response = requests.get(url, params=params)
        return response.json()
    
    def get_tennis_odds(self, league='tennis_atp') -> Dict:
        """Get tennis odds for ATP or WTA"""
        url = f"{self.base_url}/sports/{league}/odds"
        params = {
            'api_key': self.api_key,
            'regions': 'us',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        response = requests.get(url, params=params)
        odds = response.json()
        
        print(f"\n📊 {league.upper()} Odds")
        print("-" * 70)
        
        for match in odds[:5]:  # Show first 5 matches
            away = match.get('away_team', 'Unknown')
            home = match.get('home_team', 'Unknown')
            
            print(f"\n{away} vs {home}")
            print(f"Bookmakers: {len(match.get('bookmakers', []))}")
            
            for bookmaker in match.get('bookmakers', [])[:2]:  # Show 2 bookmakers
                title = bookmaker.get('title', 'Unknown')
                print(f"  {title}:")
                
                for market in bookmaker.get('markets', []):
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        name = outcome.get('name', 'Unknown')
                        price = outcome.get('price', 'N/A')
                        print(f"    {name}: {price}")
        
        return odds
    
    def get_mlb_odds(self) -> Dict:
        """Get MLB betting odds"""
        url = f"{self.base_url}/sports/baseball_mlb/odds"
        params = {
            'api_key': self.api_key,
            'regions': 'us',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        response = requests.get(url, params=params)
        return response.json()

# Usage
client = OddsAPIClient(api_key='YOUR_API_KEY')
tennis_atp_odds = client.get_tennis_odds('tennis_atp')
mlb_odds = client.get_mlb_odds()
```

---

### Example 2: Compare Odds Across Bookmakers
```python
import requests
from typing import List

def find_best_odds(api_key: str, sport: str = 'baseball_mlb') -> None:
    """Find best odds across multiple bookmakers"""
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        'api_key': api_key,
        'regions': 'us',
        'markets': 'h2h'
    }
    
    response = requests.get(url, params=params)
    games = response.json()
    
    print(f"\n💰 Best Odds for {sport}")
    print("=" * 80)
    
    for game in games[:3]:  # Show first 3 games
        away = game.get('away_team', 'Unknown')
        home = game.get('home_team', 'Unknown')
        
        print(f"\n{away} @ {home}")
        print("-" * 80)
        
        best_away = 0
        best_home = 0
        best_away_book = ""
        best_home_book = ""
        
        for bookmaker in game.get('bookmakers', []):
            title = bookmaker.get('title', '')
            
            for market in bookmaker.get('markets', []):
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == away:
                        if outcome['price'] > best_away:
                            best_away = outcome['price']
                            best_away_book = title
                    elif outcome['name'] == home:
                        if outcome['price'] > best_home:
                            best_home = outcome['price']
                            best_home_book = title
        
        print(f"Best {away}: {best_away:.2f} @ {best_away_book}")
        print(f"Best {home}: {best_home:.2f} @ {best_home_book}")

# Usage: find_best_odds('YOUR_API_KEY')
```

---

## ADVANCED: COMBINED DATA PIPELINE

### Complete Integration Example
```python
import requests
import json
from datetime import datetime
from typing import Dict, List

class UnifiedSportsFeed:
    """Unified feed for MLB, Tennis, and Betting Odds"""
    
    def __init__(self, odds_api_key: str):
        self.odds_api_key = odds_api_key
        self.mlb_base = "https://statsapi.mlb.com/api/v1"
        self.odds_base = "https://api.the-odds-api.com/v4"
    
    def get_combined_feed(self) -> Dict:
        """Get combined data for MLB and Tennis with odds"""
        feed = {
            'timestamp': datetime.now().isoformat(),
            'mlb': {
                'games': self._get_mlb_games(),
                'odds': self._get_mlb_odds()
            },
            'tennis': {
                'atp': self._get_atp_matches(),
                'wta': self._get_wta_matches(),
                'odds': self._get_tennis_odds()
            }
        }
        return feed
    
    def _get_mlb_games(self) -> List:
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{self.mlb_base}/schedule"
        params = {'date': today}
        
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else []
    
    def _get_mlb_odds(self) -> List:
        url = f"{self.odds_base}/sports/baseball_mlb/odds"
        params = {
            'api_key': self.odds_api_key,
            'regions': 'us',
            'markets': 'h2h'
        }
        
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else []
    
    def _get_atp_matches(self) -> List:
        url = "https://site.api.espn.com/us/site/v2/sports/tennis/atp"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else {}
    
    def _get_wta_matches(self) -> List:
        url = "https://site.api.espn.com/us/site/v2/sports/tennis/wta"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else {}
    
    def _get_tennis_odds(self) -> Dict:
        url = f"{self.odds_base}/sports/tennis_atp/odds"
        params = {
            'api_key': self.odds_api_key,
            'regions': 'us',
            'markets': 'h2h'
        }
        
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else {}
    
    def save_feed(self, filename: str = 'sports_feed.json'):
        """Save the combined feed to a JSON file"""
        feed = self.get_combined_feed()
        with open(filename, 'w') as f:
            json.dump(feed, f, indent=2)
        print(f"✅ Feed saved to {filename}")

# Usage
feed = UnifiedSportsFeed(api_key='YOUR_API_KEY')
combined_data = feed.get_combined_feed()
feed.save_feed('sports_data.json')
print(json.dumps(combined_data, indent=2)[:500] + "...")
```

---

## MONITORING & CACHING

### Caching Implementation
```python
import requests
from datetime import datetime, timedelta
import json
import os

class CachedSportsFetcher:
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = cache_dir
        self.cache_ttl = 300  # 5 minutes
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _is_cache_valid(self, key: str) -> bool:
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return False
        
        age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(cache_path)
        )
        return age < timedelta(seconds=self.cache_ttl)
    
    def fetch(self, url: str, params: dict = None, cache_key: str = None) -> dict:
        """Fetch with caching"""
        # Try cache first
        if cache_key and self._is_cache_valid(cache_key):
            with open(self._get_cache_path(cache_key), 'r') as f:
                return json.load(f)
        
        # Fetch fresh data
        response = requests.get(url, params=params)
        data = response.json() if response.status_code == 200 else {}
        
        # Save to cache
        if cache_key:
            with open(self._get_cache_path(cache_key), 'w') as f:
                json.dump(data, f)
        
        return data

# Usage
fetcher = CachedSportsFetcher()
mlb_data = fetcher.fetch(
    url="https://statsapi.mlb.com/api/v1/schedule",
    params={'date': '2025-06-15'},
    cache_key='mlb_schedule_2025-06-15'
)
```

---

## TROUBLESHOOTING

### Common Issues & Solutions

#### 1. Rate Limiting
```python
import time
import requests

def fetch_with_retry(url, max_retries=3, backoff=2):
    """Fetch with exponential backoff for rate limiting"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 429:  # Too Many Requests
                wait_time = backoff ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            return response
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(backoff ** attempt)
    
    return None
```

#### 2. Handle Missing Data
```python
def safe_get(dictionary, keys, default=None):
    """Safely navigate nested dictionaries"""
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
    return result if result is not None else default

# Usage
game_data = {'game': {'status': {'abstractGameState': 'Live'}}}
status = safe_get(game_data, ['game', 'status', 'abstractGameState'], 'Unknown')
```

---

## Summary Table

| API | Sport | Auth | Free | Rate Limit | Freshness |
|-----|-------|------|------|------------|-----------|
| MLB Stats | Baseball | No | Yes | ~1/s | Real-time |
| ESPN | Tennis/Baseball | No | Yes | ~1/s | Real-time |
| Odds API | All | Key | 500/mo | 1/s | 1-5 min |
| PyBaseball | Baseball | No | Yes | N/A | Daily |
| TheSpread | Odds | No | Limited | N/A | Real-time |

