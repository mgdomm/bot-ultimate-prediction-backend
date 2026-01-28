# 🔗 ENDPOINTS COMPLETOS: Guía de Referencia Rápida

**Fecha**: 28 de Enero de 2026  
**Objetivo**: Referencia rápida de todos los endpoints para los 12 deportes

---

## 📍 SofaScore API (Recomendado - Con Odds)

### URL Base
```
https://www.sofascore.com/api/v1
```

### Endpoints por Deporte

#### **1. ⚽ SOCCER / FOOTBALL**
```
Obtener eventos de hoy:
GET /sport/football/events/today

Obtener odds de evento:
GET /event/{eventId}/odds

Obtener información de torneos:
GET /tournament/{tournamentId}/season/{seasonId}/events/today

Ejemplo completo:
curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events[0]'
```

#### **2. 🏉 RUGBY**
```
Obtener eventos de hoy:
GET /sport/rugby/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/rugby/events/today"
```

#### **3. 🏈 NFL (AMERICAN FOOTBALL)**
```
Obtener eventos de hoy:
GET /sport/american-football/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/american-football/events/today"
```

#### **4. 🏀 BASKETBALL**
```
Obtener eventos de hoy:
GET /sport/basketball/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/basketball/events/today"
```

#### **5. 🏒 HOCKEY**
```
Obtener eventos de hoy:
GET /sport/hockey/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/hockey/events/today"
```

#### **6. 🤾 HANDBALL**
```
Obtener eventos de hoy:
GET /sport/handball/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/handball/events/today"
```

#### **7. 🏐 VOLLEYBALL**
```
Obtener eventos de hoy:
GET /sport/volleyball/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/volleyball/events/today"
```

#### **8. 🏈 AFL (AUSTRALIAN FOOTBALL)**
```
Obtener eventos de hoy:
GET /sport/australian-football/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/australian-football/events/today"
```

#### **9. 🎾 TENNIS**
```
Obtener eventos de hoy:
GET /sport/tennis/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/tennis/events/today"
```

#### **10. ⚾ BASEBALL**
```
Obtener eventos de hoy:
GET /sport/baseball/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/baseball/events/today"
```

#### **11. 🏎️ FORMULA 1**
```
Obtener eventos de hoy:
GET /sport/formula-1/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/formula-1/events/today"
```

#### **12. 🥊 MMA / UFC**
```
Obtener eventos de hoy:
GET /sport/mma/events/today

Obtener odds:
GET /event/{eventId}/odds

Ejemplo:
curl "https://www.sofascore.com/api/v1/sport/mma/events/today"
```

---

## 📍 TheSportsDB API (Complementaria - Sin Odds)

### URL Base
```
https://www.thesportsdb.com/api/v1/json/1
```

### League IDs por Deporte

```json
{
  "soccer": {
    "premier_league": 133602,
    "bundesliga": 133603,
    "la_liga": 133604,
    "serie_a": 133605,
    "ligue_1": 133606,
    "mls": 133607,
    "champions_league": 133608
  },
  "american_football": {
    "nfl": 133602
  },
  "basketball": {
    "nba": 133600,
    "euroleague": 133601
  },
  "hockey": {
    "nhl": 133655,
    "khl": 133654
  },
  "tennis": {
    "grand_slam": 133678,
    "atp": 133679,
    "wta": 133680
  },
  "baseball": {
    "mlb": 133602
  },
  "rugby": {
    "six_nations": 133662,
    "rugby_championship": 133663
  },
  "volleyball": {
    "world_cup": 133690
  },
  "handball": {
    "champions_league": 133700
  },
  "mma": {
    "ufc": 133650
  },
  "afl": {
    "australian_league": 133645
  },
  "formula_1": {
    "f1": 133629
  }
}
```

### Endpoints

```
Obtener últimos eventos de liga:
GET /eventslast.php?id={league_id}

Obtener eventos por fecha:
GET /eventsday.php?id={league_id}&d=YYYY-MM-DD

Obtener información de evento:
GET /eventinfo.php?id={event_id}

Obtener equipos de liga:
GET /eventteam.php?id={team_id}
```

### Ejemplos Completos

#### **1. ⚽ SOCCER**
```bash
# Premier League últimos eventos
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133602"

# Eventos por fecha
curl "https://www.thesportsdb.com/api/v1/json/1/eventsday.php?id=133602&d=2026-01-28"

# La Liga
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133604"
```

#### **2. 🎾 TENNIS**
```bash
# ATP
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133679"

# WTA
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133680"

# Grand Slams
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133678"
```

#### **3. ⚾ BASEBALL**
```bash
# MLB
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133602"
```

#### **4. 🏈 NFL**
```bash
# NFL
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133602"
```

#### **5. 🏀 BASKETBALL**
```bash
# NBA
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133600"
```

#### **6. 🏒 HOCKEY**
```bash
# NHL
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133655"
```

#### **7. 🏉 RUGBY**
```bash
# Six Nations
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133662"
```

#### **8. 🤾 HANDBALL**
```bash
# Champions League
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133700"
```

#### **9. 🏐 VOLLEYBALL**
```bash
# World Cup
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133690"
```

#### **10. 🏈 AFL**
```bash
# Australian League
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133645"
```

#### **11. 🏎️ FORMULA 1**
```bash
# F1
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133629"
```

#### **12. 🥊 MMA**
```bash
# UFC
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133650"
```

---

## 📍 ESPN API (Complementaria - Scores)

### URL Base
```
https://site.api.espn.com/us/site/v2/sports
```

### Endpoints por Deporte

#### **1. ⚾ BASEBALL (MLB)**
```bash
# Scores
curl "https://site.api.espn.com/us/site/v2/sports/baseball/mlb"

# Standings
curl "https://site.api.espn.com/us/site/v2/sports/baseball/mlb/standings"
```

#### **2. 🏈 FOOTBALL (NFL)**
```bash
# Scores
curl "https://site.api.espn.com/us/site/v2/sports/football/nfl"

# Standings
curl "https://site.api.espn.com/us/site/v2/sports/football/nfl/standings"
```

#### **3. 🏀 BASKETBALL (NBA)**
```bash
# Scores
curl "https://site.api.espn.com/us/site/v2/sports/basketball/nba"

# Standings
curl "https://site.api.espn.com/us/site/v2/sports/basketball/nba/standings"
```

#### **4. 🏒 HOCKEY (NHL)**
```bash
# Scores
curl "https://site.api.espn.com/us/site/v2/sports/hockey/nhl"

# Standings
curl "https://site.api.espn.com/us/site/v2/sports/hockey/nhl/standings"
```

#### **5. 🎾 TENNIS (ATP)**
```bash
# ATP matches
curl "https://site.api.espn.com/us/site/v2/sports/tennis/atp"
```

#### **6. 🎾 TENNIS (WTA)**
```bash
# WTA matches
curl "https://site.api.espn.com/us/site/v2/sports/tennis/wta"
```

#### **7. ⚽ SOCCER**
```bash
# Soccer events
curl "https://site.api.espn.com/us/site/v2/sports/soccer"
```

---

## 🔄 PATRONES DE USO

### Patrón 1: Get All Events Today
```python
import requests

def get_all_sports_today():
    sports = [
        ('football', 'soccer'),
        ('tennis', 'tennis'),
        ('basketball', 'basketball'),
        ('hockey', 'hockey'),
        ('baseball', 'baseball'),
        ('american-football', 'nfl'),
        ('rugby', 'rugby'),
        ('handball', 'handball'),
        ('volleyball', 'volleyball'),
        ('australian-football', 'afl'),
        ('formula-1', 'f1'),
        ('mma', 'mma'),
    ]
    
    base_url = "https://www.sofascore.com/api/v1"
    
    for sport_slug, sport_name in sports:
        try:
            url = f"{base_url}/sport/{sport_slug}/events/today"
            response = requests.get(url, timeout=10)
            events = response.json().get('events', [])
            print(f"{sport_name.upper()}: {len(events)} eventos")
        except Exception as e:
            print(f"{sport_name.upper()}: Error - {e}")

get_all_sports_today()
```

### Patrón 2: Get Odds for Top Events
```python
import requests

def get_top_odds_all_sports():
    sports = ['football', 'tennis', 'basketball', 'hockey', 'baseball']
    base_url = "https://www.sofascore.com/api/v1"
    
    for sport in sports:
        try:
            # Get events
            events_url = f"{base_url}/sport/{sport}/events/today"
            events_response = requests.get(events_url, timeout=10)
            events = events_response.json().get('events', [])
            
            # Get odds for top 3 events
            for event in events[:3]:
                event_id = event['id']
                odds_url = f"{base_url}/event/{event_id}/odds"
                odds_response = requests.get(odds_url, timeout=10)
                
                print(f"\n{sport.upper()} - {event.get('slug', 'N/A')}")
                markets = odds_response.json().get('markets', [])
                print(f"  Markets: {len(markets)}")
                
        except Exception as e:
            print(f"{sport}: Error - {e}")

get_top_odds_all_sports()
```

### Patrón 3: Refresh Specific Sports
```python
import requests
import time

def refresh_sports_every_hour(sports=['football', 'basketball', 'baseball']):
    base_url = "https://www.sofascore.com/api/v1"
    
    while True:
        for sport in sports:
            try:
                url = f"{base_url}/sport/{sport}/events/today"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                # Process data here
                print(f"[{time.strftime('%H:%M:%S')}] {sport}: {len(data.get('events', []))} eventos")
                
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] {sport}: Error - {e}")
        
        # Wait 1 hour
        time.sleep(3600)

# Descommentar para ejecutar
# refresh_sports_every_hour()
```

---

## 📋 TESTING RÁPIDO

### Test Todos los Deportes (SofaScore)
```bash
#!/bin/bash

BASE="https://www.sofascore.com/api/v1"

echo "Testing todos los deportes SofaScore..."

sports=("football" "tennis" "basketball" "hockey" "baseball" "american-football" "rugby" "handball" "volleyball" "australian-football" "formula-1" "mma")

for sport in "${sports[@]}"
do
    count=$(curl -s "$BASE/sport/$sport/events/today" | jq '.events | length' 2>/dev/null || echo "ERROR")
    echo "$sport: $count eventos"
done
```

### Test Todos los Deportes (TheSportsDB)
```bash
#!/bin/bash

BASE="https://www.thesportsdb.com/api/v1/json/1"

echo "Testing todos los deportes TheSportsDB..."

declare -A ids=(
    ["Soccer"]=133602
    ["Tennis ATP"]=133679
    ["Tennis WTA"]=133680
    ["NFL"]=133602
    ["NBA"]=133600
    ["NHL"]=133655
    ["MLB"]=133602
    ["Rugby"]=133662
    ["Handball"]=133700
    ["Volleyball"]=133690
    ["AFL"]=133645
    ["Formula1"]=133629
    ["MMA"]=133650
)

for sport in "${!ids[@]}"
do
    count=$(curl -s "$BASE/eventslast.php?id=${ids[$sport]}" | jq '.results | length' 2>/dev/null || echo "ERROR")
    echo "$sport: $count eventos"
done
```

---

## 🎯 REFERENCIA RÁPIDA POR DEPORTE

### Soccer ⚽
```
SofaScore: /sport/football/events/today
TheSportsDB: /eventslast.php?id=133602
ESPN: /sports/soccer
```

### Rugby 🏉
```
SofaScore: /sport/rugby/events/today
TheSportsDB: /eventslast.php?id=133662
ESPN: No disponible
```

### NFL 🏈
```
SofaScore: /sport/american-football/events/today
TheSportsDB: /eventslast.php?id=133602
ESPN: /sports/football/nfl
```

### Basketball 🏀
```
SofaScore: /sport/basketball/events/today
TheSportsDB: /eventslast.php?id=133600
ESPN: /sports/basketball/nba
```

### Hockey 🏒
```
SofaScore: /sport/hockey/events/today
TheSportsDB: /eventslast.php?id=133655
ESPN: /sports/hockey/nhl
```

### Handball 🤾
```
SofaScore: /sport/handball/events/today
TheSportsDB: /eventslast.php?id=133700
ESPN: No disponible
```

### Volleyball 🏐
```
SofaScore: /sport/volleyball/events/today
TheSportsDB: /eventslast.php?id=133690
ESPN: No disponible
```

### AFL 🏈
```
SofaScore: /sport/australian-football/events/today
TheSportsDB: /eventslast.php?id=133645
ESPN: No disponible
```

### Tennis 🎾
```
SofaScore: /sport/tennis/events/today
TheSportsDB ATP: /eventslast.php?id=133679
TheSportsDB WTA: /eventslast.php?id=133680
ESPN ATP: /sports/tennis/atp
ESPN WTA: /sports/tennis/wta
```

### Baseball ⚾
```
SofaScore: /sport/baseball/events/today
TheSportsDB: /eventslast.php?id=133602
ESPN: /sports/baseball/mlb
```

### Formula 1 🏎️
```
SofaScore: /sport/formula-1/events/today
TheSportsDB: /eventslast.php?id=133629
ESPN: No disponible
```

### MMA 🥊
```
SofaScore: /sport/mma/events/today
TheSportsDB: /eventslast.php?id=133650
ESPN: No disponible
```

---

## ⚡ PERFORMANCE TIPS

1. **Cache Results**: Cachea resultados por 5-15 minutos
2. **Parallel Requests**: Realiza requests en paralelo para múltiples deportes
3. **Rate Limiting**: Implementa backoff exponencial
4. **Fallback**: Si SofaScore falla, usa TheSportsDB
5. **Batch Updates**: No actualices todos los deportes cada 30 segundos

---

**Última actualización**: 28 de Enero de 2026
