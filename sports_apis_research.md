# Comprehensive Sports APIs Research: Tennis & MLB

## TENNIS APIS & DATA SOURCES

### 1. **The Odds API** (https://www.odds-api.com/)
- **Status**: ✅ VIABLE
- **Authentication**: API Key (free tier available)
- **Free Tier**: 
  - 500 requests/month (free)
  - Sports included: Football, Basketball, Baseball, Ice Hockey, Tennis
  - Data: Live & upcoming odds only
- **Tennis Coverage**: 
  - ATP/WTA matches
  - Grand Slams
  - Betting lines from multiple bookmakers
- **Rate Limits**: 1 request/second on free tier
- **Data Freshness**: Real-time (updates every 1-5 minutes)
- **Pricing Paid**: $39/month (10k requests) or $99/month (unlimited)

**Code Example:**
```python
import requests

API_KEY = "YOUR_API_KEY"
url = "https://api.the-odds-api.com/v4/sports"

params = {
    'api_key': API_KEY
}

r = requests.get(url, params=params)
if r.status_code == 200:
    sports = r.json()
    print(f"Available sports: {sports}")
```

---

### 2. **ESPN Tennis Data**
- **Status**: ✅ VIABLE (via scraping or unofficial APIs)
- **Authentication**: None required
- **Coverage**:
  - Live scores for ATP, WTA
  - Match stats and player info
  - Tournament standings
- **Data Sources**:
  - https://www.espn.com/tennis/
  - ESPN mobile API (reverse-engineered)

**Available Endpoints:**
- `https://site.api.espn.com/us/site/v2/sports/tennis/atp` (ATP)
- `https://site.api.espn.com/us/site/v2/sports/tennis/wta` (WTA)

**Code Example:**
```python
import requests

def get_atp_matches():
    url = "https://site.api.espn.com/us/site/v2/sports/tennis/atp"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        # Extract matches from events
        events = data.get('events', [])
        for event in events:
            print(f"{event['name']}: {event['status']}")

get_atp_matches()
```

---

### 3. **Tennis Explorer/Tennis Live Tracker (Web Scraping)**
- **Status**: ⚠️ VIABLE WITH CAUTION
- **Authentication**: None
- **Coverage**: 
  - Live scores (ATP, WTA, Challengers)
  - Match details and statistics
  - Player rankings
- **Legal Status**: ToS may prohibit scraping; check before use
- **Data Freshness**: Real-time

**Popular Libraries:**
- BeautifulSoup + Selenium
- Scrapy

**Code Example:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def scrape_tennis_explorer():
    driver = webdriver.Chrome()
    driver.get("https://www.tennisexplorer.com/live/")
    time.sleep(3)  # Wait for JS to load
    
    matches = driver.find_elements(By.CLASS_NAME, "match")
    for match in matches:
        title = match.text
        print(f"Match: {title}")
    
    driver.quit()

scrape_tennis_explorer()
```

---

### 4. **GitHub: TennisScoresAPI**
- **Repository**: https://github.com/search?q=TennisScoresAPI
- **Status**: Custom/Community project
- **Features**: Live tennis scores
- **Authentication**: None/API Key
- **Data**: Tennis match data from various sources

---

### 5. **Flashscore/LiveScore** (Web Scraping)
- **Status**: ⚠️ VIABLE WITH CAUTION
- **Authentication**: None
- **Coverage**:
  - ATP, WTA, Grand Slams
  - Live scores
  - Match statistics
- **Legal Note**: Terms of Service may prohibit automated scraping

**GitHub Projects:**
- `Tennis-Website-Scraper` - Scrapes Tennis Explorer & Flashscore
- `flashscore_tennis_player_scraper`

**Rate Limiting Considerations**: 
- Heavy scraping may trigger IP blocks
- Recommended: 2-5 second delays between requests

---

### 6. **RapidAPI Sports APIs**
- **Platform**: https://rapidapi.com/
- **Available Options**:
  - Tennis Live Scores API
  - Tennis Data API
  - Sports Data APIs (multi-sport)
- **Pricing**: Freemium model
- **Free Tier**: Usually 100-500 requests/month
- **Rate Limits**: Varies (typically 1-10 requests/second)

**Example Tennis APIs on RapidAPI:**
- `Tennis Live Scores API` - Real-time scores
- `ATP/WTA Rankings API` - Player rankings

---

## MLB APIS & DATA SOURCES

### 1. **MLB Stats API** (Official - Free)
- **Status**: ✅ HIGHLY VIABLE
- **Authentication**: None required
- **Coverage**:
  - Live game scores
  - Play-by-play data
  - Player statistics
  - Team information
  - Game schedules
- **Data Freshness**: Real-time (updates every 30 seconds during games)
- **Rate Limits**: Friendly (no documented limits, ~1 request/second recommended)
- **Base URL**: `https://statsapi.mlb.com/api/v1/`

**Popular Endpoints:**
```
/game/{gameId} - Individual game data
/schedule - Games on a specific date
/teams - Team information
/people/{playerId} - Player statistics
/standings - League standings
/live/gridData - Live game data
```

**Code Example:**
```python
import requests
from datetime import datetime

def get_mlb_schedule(date_str="2026-01-28"):
    """Fetch MLB schedule for a specific date"""
    url = f"https://statsapi.mlb.com/api/v1/schedule"
    params = {'date': date_str}
    
    r = requests.get(url, params=params)
    if r.status_code == 200:
        games = r.json()
        for game in games:
            print(f"{game['teams']['away']['team']['name']} @ {game['teams']['home']['team']['name']}: {game['status']}")
    return r.json()

def get_live_game(game_id):
    """Get detailed live game data"""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/linescore"
    r = requests.get(url)
    return r.json()

# Example usage
schedule = get_mlb_schedule()
if schedule:
    for game in schedule[:1]:
        if game['gameType'] != 'S':  # Skip Spring Training
            live_data = get_live_game(game['gamePk'])
            print(json.dumps(live_data, indent=2))
```

---

### 2. **ESPN Baseball Data**
- **Status**: ✅ VIABLE
- **Authentication**: None
- **Coverage**:
  - Live scores
  - Team stats
  - Player statistics
  - League standings
- **Data Freshness**: Real-time
- **URL**: `https://www.espn.com/mlb/`

**Unofficial API Endpoints:**
```
https://site.api.espn.com/us/site/v2/sports/baseball/mlb
https://site.api.espn.com/us/site/v2/sports/baseball/mlb/teams
https://site.api.espn.com/us/site/v2/sports/baseball/mlb/standings
```

**Code Example:**
```python
import requests

def get_mlb_standings():
    url = "https://site.api.espn.com/us/site/v2/sports/baseball/mlb/standings"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        leagues = data.get('standings', [])
        for league in leagues:
            print(f"League: {league.get('name')}")
            for division in league.get('children', []):
                print(f"  {division['name']}")
```

---

### 3. **Odds-API for Baseball**
- **Status**: ✅ VIABLE
- **Authentication**: API Key
- **Coverage**: 
  - MLB betting odds
  - Live and upcoming games
  - Multiple bookmaker lines
- **Free Tier**: 500 requests/month
- **Rate Limits**: 1 request/second
- **Data Freshness**: Real-time (1-5 minutes)

**Code Example:**
```python
import requests

API_KEY = "YOUR_API_KEY"

def get_baseball_odds():
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'api_key': API_KEY,
        'regions': 'us',  # Multiple regions supported
        'markets': 'h2h',  # Head-to-head odds
        'oddsFormat': 'decimal'
    }
    
    r = requests.get(url, params=params)
    if r.status_code == 200:
        odds = r.json()
        for game in odds:
            print(f"{game['home_team']} vs {game['away_team']}")
            for bookmaker in game['bookmakers']:
                print(f"  {bookmaker['title']}: {bookmaker['markets'][0]['outcomes']}")
    return r.json()

get_baseball_odds()
```

---

### 4. **MLB.com Official API**
- **Status**: ⚠️ LIMITED
- **Authentication**: None for basic endpoints
- **Coverage**: 
  - Game data
  - Team info
  - Schedule
- **URL**: Direct from MLB.com (unofficial reverse-engineered)
- **Note**: May change without notice

---

### 5. **PyBaseball Library**
- **Repository**: https://github.com/jldbc/pybaseball
- **Status**: ✅ VIABLE
- **Authentication**: None (scrapes publicly available data)
- **Coverage**:
  - Historical statistics
  - Advanced metrics
  - Player data
  - Pitch data (PITCHf/x)
- **Data Freshness**: Daily updates
- **Installation**: `pip install pybaseball`

**Code Example:**
```python
from pybaseball import playerid_lookup, statcast, batting_stats

# Get player ID
playerid = playerid_lookup("Trout", "Mike")
print(playerid)

# Get advanced batting stats
batting = batting_stats(2025, qual=1)
print(batting.head())

# Get statcast data (pitch-by-pitch)
statcast_data = statcast(start_dt='2025-04-01', end_dt='2025-04-30')
print(statcast_data.head())
```

---

### 6. **RetroSheet Data**
- **Status**: ✅ VIABLE
- **URL**: https://www.retrosheet.org/
- **Coverage**:
  - Historical game data (100+ years)
  - Play-by-play data
  - Rosters
- **Authentication**: None
- **Format**: CSV, Text
- **Data Freshness**: Historical (updates seasonally)
- **Use Case**: Historical analysis, not real-time

---

### 7. **RapidAPI Baseball APIs**
- **Status**: ✅ VIABLE
- **Platform**: https://rapidapi.com/
- **Available Options**:
  - Baseball API
  - MLB Stats API
  - Baseball Data API
- **Pricing**: Freemium
- **Free Tier**: 100-500 requests/month typically
- **Rate Limits**: 1-10 requests/second

---

### 8. **GitHub: mlbstats**
- **Repository**: https://github.com/search?q=mlbstats
- **Status**: ✅ ACTIVE
- **Features**: Python wrapper for MLB Stats API
- **Authentication**: None
- **Installation**: `pip install mlbstats`

**Code Example:**
```python
from mlbstats import StatsAPI

api = StatsAPI()

# Get current day's schedule
schedule = api.get_schedule_by_date('2026-01-28')
print(schedule)

# Get game data
game_data = api.get_game(game_id='123456')
print(game_data)
```

---

## BETTING ODDS AGGREGATORS

### 1. **The Odds API** (⭐ Recommended)
- **Sports**: Tennis, Baseball, Football, Basketball, Hockey
- **Coverage**: 20+ sportsbooks
- **Free Tier**: 500 requests/month
- **Paid**: $39-$99/month
- **Rate Limits**: 1 request/second (free)
- **Updates**: 1-5 minutes

---

### 2. **TheSpread.io API**
- **Repository**: https://github.com/thespread/api
- **Status**: Community project
- **Coverage**: Vegas odds aggregation
- **Features**: Real-time odds from multiple books

---

### 3. **RapidAPI Sports Odds APIs**
- **Platform**: https://rapidapi.com/
- **Multiple Providers**:
  - BetsAPI
  - SportsOdds API
  - Live Odds API
- **Free Tier**: Limited requests
- **Data**: Multiple bookmakers

---

### 4. **BetRadar/Sportradar Alternative**
- **Note**: These are enterprise solutions ($$)
- **Free Alternative**: Combine multiple free APIs

---

## LEGAL & ETHICAL CONSIDERATIONS

### ✅ Legal Options:
- Official APIs (MLB Stats, ESPN, Odds-API)
- Public data sources with explicit permission
- Libraries like pybaseball (properly attributed)

### ⚠️ Gray Zone (Check ToS):
- Web scraping (ESPN, Tennis Explorer, Flashscore)
- Requires respectful rate limiting
- Must check Terms of Service

### ❌ Avoid:
- Bypassing authentication
- Extreme rate limiting (DDoS-like)
- Commercial use of copyrighted data

---

## RECOMMENDATION MATRIX

| Sport | Best Option | Secondary | Tertiary | Cost |
|-------|-----------|-----------|----------|------|
| **Tennis** | The Odds API + ESPN scraping | Flashscore scraping | RapidAPI Tennis APIs | $0-$39/mo |
| **MLB Scores** | MLB Stats API | ESPN API | PyBaseball | $0 |
| **MLB Odds** | The Odds API | RapidAPI | TheSpread.io | $0-$39/mo |
| **Historical Data** | PyBaseball | RetroSheet | Kaggle Datasets | $0 |

---

## IMPLEMENTATION ROADMAP

### Phase 1: Get Data (Low Cost)
1. **MLB Scores**: Use MLB Stats API (free, excellent)
2. **Tennis Scores**: Use ESPN scraping + The Odds API free tier
3. **Odds**: Use The Odds API (500 req/month free)

### Phase 2: Enhance (As Needed)
1. Upgrade Odds API to paid ($39/month) for more sports/requests
2. Add RapidAPI backups for tennis
3. Implement caching to reduce API calls

### Phase 3: Production (If Revenue)
1. Switch to enterprise solutions if needed
2. Negotiate better rates with major providers
3. Consider Sportradar/BetRadar for premium data

---

## CODE TEMPLATES

### Template 1: Unified Sports Score Fetcher
```python
import requests
from datetime import datetime
import json

class SportsDataFetcher:
    def __init__(self, odds_api_key):
        self.odds_api_key = odds_api_key
    
    def get_mlb_scores(self, date_str=None):
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        url = f"https://statsapi.mlb.com/api/v1/schedule"
        params = {'date': date_str}
        r = requests.get(url, params=params)
        return r.json() if r.status_code == 200 else None
    
    def get_tennis_odds(self, sport='tennis_atp'):
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {
            'api_key': self.odds_api_key,
            'regions': 'us',
            'markets': 'h2h'
        }
        r = requests.get(url, params=params)
        return r.json() if r.status_code == 200 else None
    
    def get_atp_matches(self):
        url = "https://site.api.espn.com/us/site/v2/sports/tennis/atp"
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None

# Usage
fetcher = SportsDataFetcher(api_key='YOUR_ODDS_API_KEY')
mlb_games = fetcher.get_mlb_scores()
tennis_odds = fetcher.get_tennis_odds()
atp_matches = fetcher.get_atp_matches()
```

### Template 2: Caching Strategy
```python
import requests
from datetime import datetime, timedelta
import json

class CachedSportsFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _is_cache_valid(self, key):
        if key not in self.cache:
            return False
        return datetime.now() - self.cache[key]['time'] < timedelta(seconds=self.cache_ttl)
    
    def fetch_with_cache(self, url, params=None, cache_key=None):
        if cache_key and self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        r = requests.get(url, params=params)
        data = r.json() if r.status_code == 200 else None
        
        if cache_key and data:
            self.cache[cache_key] = {'data': data, 'time': datetime.now()}
        
        return data

# Usage
fetcher = CachedSportsFetcher()
odds = fetcher.fetch_with_cache(
    url="https://api.the-odds-api.com/v4/sports/tennis_atp/odds",
    params={'api_key': 'YOUR_KEY'},
    cache_key='tennis_atp_odds'
)
```

---

## FINAL VERDICT

### ✅ RECOMMENDED STACK FOR PRODUCTION:
1. **MLB Scores**: MLB Stats API (free, no auth, reliable)
2. **Tennis & MLB Odds**: The Odds API (free tier 500 req/mo, $39/mo for unlimited)
3. **Backup/Enhancement**: RapidAPI APIs (freemium, backup)
4. **Historical Data**: PyBaseball (free, open-source)
5. **Live Data**: ESPN scraping (with responsible rate limiting)

### Total Monthly Cost: **$0-$39** (depending on scale)
### Viability: **VERY HIGH** ✅

