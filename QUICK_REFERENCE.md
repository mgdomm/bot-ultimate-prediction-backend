# QUICK REFERENCE GUIDE: Sports APIs

## 🚀 Get Started in 5 Minutes

### Step 1: Sign Up (2 min)
```
The Odds API (Free Tier):
→ Go to https://www.odds-api.com/register
→ Get your free API key (500 requests/month)
→ Copy to .env as ODDS_API_KEY
```

### Step 2: First API Call (1 min)
```bash
# Test MLB Stats API (no auth needed)
curl "https://statsapi.mlb.com/api/v1/schedule?date=$(date +%Y-%m-%d)"

# Test ESPN Tennis
curl "https://site.api.espn.com/us/site/v2/sports/tennis/atp"

# Test Odds API (replace YOUR_KEY)
curl "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds?api_key=YOUR_KEY&regions=us&markets=h2h"
```

### Step 3: Integrate (2 min)
Copy one of the service files from `SPORTS_APIS_INTEGRATION_EXAMPLES.md`

---

## 📋 API QUICK REFERENCE

### MLB Stats API (FREE, NO AUTH)
```
Base URL: https://statsapi.mlb.com/api/v1/

Endpoints:
  /schedule?date=YYYY-MM-DD         → Games for a date
  /game/{gameId}/linescore          → Live game score
  /game/{gameId}/boxscore           → Detailed box score
  /people/{playerId}                → Player stats
  /standings?leagueId=103,104        → League standings
  /teams                             → All teams info

Response Time: <100ms
Updates: Real-time (30s during games)
Rate Limit: Friendly (no documented limit)
```

### ESPN Tennis API (FREE, NO AUTH)
```
Base URLs:
  ATP: https://site.api.espn.com/us/site/v2/sports/tennis/atp
  WTA: https://site.api.espn.com/us/site/v2/sports/tennis/wta

Response Format: JSON
Response Time: <200ms
Rate Limit: ~1 request/second

Key Fields:
  .events[] → Array of matches
  .events[].competitors[] → Players
  .events[].status → Match status
```

### The Odds API (FREEMIUM)
```
Base URL: https://api.the-odds-api.com/v4/

Sports Keys:
  baseball_mlb
  tennis_atp
  tennis_wta

Endpoint: /sports/{sport}/odds
  ?api_key=KEY
  &regions=us,uk,au
  &markets=h2h,spreads,totals
  &oddsFormat=decimal,american

Response Time: <300ms
Rate Limit: 1 request/second (free tier)
Free Tier: 500 requests/month = ~17/day
Updates: 1-5 minutes
```

---

## 🔧 COMMON CODE PATTERNS

### Pattern 1: Get Data with Error Handling
```python
import requests

def fetch_with_retry(url, params=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    return None
```

### Pattern 2: Cache Data
```python
from datetime import datetime, timedelta

class SimpleCache:
    def __init__(self, ttl_seconds=300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
        return None
    
    def set(self, key, data):
        self.cache[key] = (data, datetime.now())

cache = SimpleCache()
```

### Pattern 3: Rate Limiting
```python
import time

class RateLimiter:
    def __init__(self, requests_per_second=1):
        self.min_interval = 1 / requests_per_second
        self.last_request = 0
    
    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

limiter = RateLimiter(requests_per_second=1)
limiter.wait()
# Make API call
```

---

## 📊 API COMPARISON MATRIX

| Feature | MLB Stats | ESPN | Odds API |
|---------|-----------|------|----------|
| **Auth Required** | No | No | Yes (API Key) |
| **Cost** | Free | Free | Free (500/mo) |
| **Response Time** | <100ms | <200ms | <300ms |
| **Update Frequency** | 30s-live | Real-time | 1-5 min |
| **Coverage** | MLB only | Multiple sports | 20+ sports |
| **Rate Limit** | Friendly | ~1/s | 1/s (free) |
| **Reliability** | 99.9% | 99% | 99%+ |

---

## 💾 STORAGE LOCATION IN YOUR PROJECT

```
bot-ultimate-prediction-backend/
├── api/
│   ├── services/
│   │   ├── mlb_stats_service.py      ← NEW
│   │   ├── tennis_service.py         ← NEW
│   │   ├── odds_service.py           ← NEW
│   │   └── sports_feed_service.py    ← NEW
│   ├── main.py                        ← UPDATE
│   └── data/
│       └── sports/                    ← NEW (optional, for caching)
├── SPORTS_APIS_EXECUTIVE_SUMMARY.md
├── SPORTS_APIS_INTEGRATION_EXAMPLES.md
└── sports_apis_research.md
```

---

## 🎯 COMMON TASKS

### Task 1: Get Today's MLB Games
```python
from api.services.mlb_stats_service import mlb_service

games = mlb_service.get_schedule()  # Uses today by default
for game in games:
    print(f"{game['teams']['away']['team']['name']} @ {game['teams']['home']['team']['name']}")
```

### Task 2: Get Current Tennis Matches
```python
from api.services.tennis_service import tennis_service

atp = tennis_service.get_active_matches('atp')
for match in atp:
    print(f"{match['player1']['name']} vs {match['player2']['name']}")
```

### Task 3: Get Best Betting Odds
```python
from api.services.odds_service import odds_service

best = odds_service.get_best_odds('baseball_mlb')
for game, odds in best.items():
    print(f"{game}: {odds['away']['price']} vs {odds['home']['price']}")
```

### Task 4: Get Combined Data
```python
from api.services.sports_feed_service import sports_feeder

feed = sports_feeder.get_combined_feed()
# Returns MLB games + odds + Tennis matches + odds
```

---

## ⚠️ TROUBLESHOOTING

### Issue: "401 Unauthorized" from Odds API
**Solution**: Check your API key is correct in `.env`
```python
import os
print(f"API Key present: {bool(os.getenv('ODDS_API_KEY'))}")
```

### Issue: Timeout errors
**Solution**: Increase timeout, use rate limiting
```python
requests.get(url, timeout=20)  # Increase from 10s
```

### Issue: Rate limit exceeded
**Solution**: Implement caching and rate limiting
```python
cache = SimpleCache(ttl_seconds=300)
# Check cache before API call
```

### Issue: ESPN API returns empty results
**Solution**: This is normal during off-season or late night
```python
# Check timestamp
from datetime import datetime
print(datetime.now())
```

---

## 📈 UPGRADE PATH

### Current (Free)
- MLB Stats API: Free
- ESPN APIs: Free
- Odds API: Free (500 req/month)
- **Total Cost**: $0/month

### Growth Phase 1 ($39/month)
- Upgrade Odds API to Starter (10K req/month)
- **Total Cost**: $39/month

### Growth Phase 2 ($99/month)
- Upgrade Odds API to Pro (Unlimited)
- **Total Cost**: $99/month

### Enterprise (Custom)
- Consider Sportradar/BetRadar for premium data
- **Total Cost**: $500-2000+/month

---

## 🔗 HELPFUL LINKS

**Official Documentation:**
- MLB Stats API: https://statsapi.mlb.com/docs/
- ESPN APIs: (unofficial) https://github.com/search?q=espn+api
- The Odds API: https://docs.odds-api.com/

**Free Tier Sign Up:**
- The Odds API: https://www.odds-api.com/register

**Python Libraries:**
- PyBaseball: `pip install pybaseball`
- Requests: `pip install requests`
- Redis (optional): `pip install redis`

**Testing Tools:**
- Postman: https://www.postman.com/
- curl: Built-in command-line tool
- Python Requests: Interactive REPL

---

## ✅ CHECKLIST: Start Implementation Today

- [ ] Sign up for The Odds API free tier
- [ ] Copy API key to .env
- [ ] Copy service files to api/services/
- [ ] Update api/main.py with new endpoints
- [ ] Test one endpoint with curl
- [ ] Add error handling
- [ ] Implement caching (optional)
- [ ] Deploy to production
- [ ] Monitor API usage
- [ ] Plan upgrade if needed

---

## 💡 TIPS & BEST PRACTICES

1. **Cache Aggressively**: 5-minute cache for odds, 30-second for live scores
2. **Monitor Quota**: Track Odds API usage with the free tier
3. **Use Timestamps**: Always include data freshness timestamps
4. **Error Handling**: Always implement fallbacks for API failures
5. **Rate Limiting**: Respect API limits with sleeps between requests
6. **Logging**: Log all API calls for debugging
7. **Testing**: Test with real data before deploying
8. **Documentation**: Keep API documentation updated

---

## 🎓 LEARNING RESOURCES

**Get Started with:**
1. Read: `SPORTS_APIS_EXECUTIVE_SUMMARY.md` (5 min)
2. Code: Copy service from `SPORTS_APIS_INTEGRATION_EXAMPLES.md` (10 min)
3. Test: Run endpoints locally (10 min)
4. Deploy: Push to production (5 min)

**Total Time: ~30 minutes to live production**

---

## 📞 SUPPORT

For detailed information, see:
- **Executive Summary**: Overview & recommendations
- **Research Guide**: Deep dive into each API
- **Implementation Guide**: Copy-paste code examples
- **Integration Examples**: Service layer code
- **Quick Reference**: This file

---

**Last Updated**: January 28, 2026  
**Status**: Ready for Implementation ✅

