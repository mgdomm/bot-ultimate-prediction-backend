# 🧪 TEST MANUAL: Ejemplos de Curl para Probar las APIs

**Propósito**: Copiar y pegar estos comandos para verificar que las APIs funcionan

---

## 1️⃣ THE ODDS API (Necesitas registrarte primero)

### Paso 1: Obtén tu API Key
```
1. Ve a https://www.the-odds-api.com/register
2. Completa el formulario (2 minutos)
3. Revisa tu email y confirma
4. Copia la API Key de tu dashboard
5. Reemplaza YOUR_API_KEY en los ejemplos abajo
```

### Test 1: Verificar que funciona

```bash
# Reemplaza YOUR_API_KEY con tu key real
API_KEY="YOUR_API_KEY"

curl "https://api.the-odds-api.com/v4/sports?api_key=$API_KEY"

# Response esperado: JSON con lista de deportes disponibles
```

### Test 2: Obtener odds de Soccer (EPL) - h2h + spreads + totals

```bash
API_KEY="YOUR_API_KEY"

curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=$API_KEY&regions=us&markets=h2h,spreads,totals&oddsFormat=decimal"

# Response: JSON con eventos y odds
```

**Explicación de parámetros:**
```
- api_key: Tu API Key
- regions: 'us' (USA), 'uk' (UK), 'au' (Australia)
- markets: 
  * h2h = Head-to-Head (Moneyline)
  * spreads = Handicaps/Point spreads
  * totals = Over/Under
- oddsFormat: 'decimal' (ej: 1.95) o 'american' (ej: -110)
```

### Test 3: Obtener solo SPREADS

```bash
API_KEY="YOUR_API_KEY"

curl "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?api_key=$API_KEY&regions=us&markets=spreads&oddsFormat=decimal"

# Response: Odds solo con spreads (point spreads)
```

### Test 4: Obtener solo TOTALS (Over/Under)

```bash
API_KEY="YOUR_API_KEY"

curl "https://api.the-odds-api.com/v4/sports/basketball_nba/odds?api_key=$API_KEY&regions=us&markets=totals&oddsFormat=decimal"

# Response: Odds solo con Over/Under
```

### Test 5: Todos los deportes soportados

```bash
API_KEY="YOUR_API_KEY"

# Soccer
curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'

# NFL
curl "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?api_key=$API_KEY&regions=us&markets=spreads" | jq '.[] | {home_team, away_team}'

# NBA
curl "https://api.the-odds-api.com/v4/sports/basketball_nba/odds?api_key=$API_KEY&regions=us&markets=totals" | jq '.[] | {home_team, away_team}'

# MLB
curl "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'

# NHL
curl "https://api.the-odds-api.com/v4/sports/hockey_nhl/odds?api_key=$API_KEY&regions=us&markets=spreads" | jq '.[] | {home_team, away_team}'

# Tennis ATP
curl "https://api.the-odds-api.com/v4/sports/tennis_atp/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'

# Rugby
curl "https://api.the-odds-api.com/v4/sports/rugby_union/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'

# AFL
curl "https://api.the-odds-api.com/v4/sports/aussie_rules_afl/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'

# F1
curl "https://api.the-odds-api.com/v4/sports/formula1/odds?api_key=$API_KEY&regions=us&markets=h2h" | jq '.[] | {home_team, away_team}'
```

### Test 6: Ver estructura completa de una respuesta

```bash
API_KEY="YOUR_API_KEY"

curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=$API_KEY&regions=us&markets=h2h,spreads,totals" | jq '.[0]'

# Muestra 1 evento completo con estructura
```

### Respuesta típica esperada:

```json
{
  "id": "13908e0d8c2f1a3...",
  "sport_key": "soccer_epl",
  "sport_title": "EPL",
  "commence_time": "2026-01-29T15:00Z",
  "home_team": "Manchester City",
  "away_team": "Liverpool",
  "bookmakers": [
    {
      "key": "draftkings",
      "title": "DraftKings",
      "last_update": "2026-01-29T20:00:00Z",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {
              "name": "Manchester City",
              "price": 1.95
            },
            {
              "name": "Draw",
              "price": 3.5
            },
            {
              "name": "Liverpool",
              "price": 2.1
            }
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {
              "name": "Manchester City",
              "price": 2.05,
              "point": -1.5
            },
            {
              "name": "Liverpool",
              "price": 1.77,
              "point": 1.5
            }
          ]
        },
        {
          "key": "totals",
          "outcomes": [
            {
              "name": "Over",
              "price": 2.0,
              "point": 2.5
            },
            {
              "name": "Under",
              "price": 1.87,
              "point": 2.5
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 2️⃣ SOFASCORE API (Sin registrarse)

### Test 1: Obtener eventos de hoy (Soccer)

```bash
curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events[] | {id, homeTeam: .homeTeam.name, awayTeam: .awayTeam.name}'

# Response: Lista de eventos de hoy
```

### Test 2: Obtener eventos de todos los deportes

```bash
# Football/Soccer
curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events | length'

# Basketball
curl "https://www.sofascore.com/api/v1/sport/basketball/events/today" | jq '.events | length'

# Tennis
curl "https://www.sofascore.com/api/v1/sport/tennis/events/today" | jq '.events | length'

# Hockey
curl "https://www.sofascore.com/api/v1/sport/hockey/events/today" | jq '.events | length'

# Baseball
curl "https://www.sofascore.com/api/v1/sport/baseball/events/today" | jq '.events | length'

# American Football
curl "https://www.sofascore.com/api/v1/sport/american-football/events/today" | jq '.events | length'

# Rugby
curl "https://www.sofascore.com/api/v1/sport/rugby/events/today" | jq '.events | length'

# MMA
curl "https://www.sofascore.com/api/v1/sport/mma/events/today" | jq '.events | length'

# Volleyball
curl "https://www.sofascore.com/api/v1/sport/volleyball/events/today" | jq '.events | length'

# Handball
curl "https://www.sofascore.com/api/v1/sport/handball/events/today" | jq '.events | length'

# Formula 1
curl "https://www.sofascore.com/api/v1/sport/formula-1/events/today" | jq '.events | length'

# Australian Football
curl "https://www.sofascore.com/api/v1/sport/australian-football/events/today" | jq '.events | length'
```

### Test 3: Obtener odds de un evento específico

```bash
# Primero, obtén el ID del evento
EVENT_ID=$(curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq -r '.events[0].id')

echo "Event ID: $EVENT_ID"

# Luego obtén los odds
curl "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds" | jq '.markets[0]'

# Muestra el primer mercado disponible
```

### Test 4: Ver todos los mercados disponibles

```bash
EVENT_ID=$(curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq -r '.events[0].id')

curl "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds" | jq '.markets[] | {marketName, marketKey, groupCount: (.groups | length)}'

# Muestra nombre y tipo de cada mercado
```

### Test 5: Ver odds específicos (h2h, spreads, totals)

```bash
EVENT_ID=$(curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq -r '.events[0].id')

# h2h (Moneyline)
echo "=== H2H ==="
curl "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds" | jq '.markets[] | select(.marketKey == "h2h") | .groups[0].odds[] | {name, odd}'

# Spreads
echo -e "\n=== Spreads ==="
curl "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds" | jq '.markets[] | select(.marketKey == "spreads") | .groups[0].odds[] | {name, odd, point}'

# Totals
echo -e "\n=== Totals ==="
curl "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds" | jq '.markets[] | select(.marketKey == "totals") | .groups[0].odds[] | {name, odd, point}'
```

### Respuesta típica esperada:

```json
{
  "markets": [
    {
      "marketName": "Full Time Result",
      "marketKey": "h2h",
      "marketId": 1,
      "groups": [
        {
          "groupId": 1,
          "groupName": null,
          "odds": [
            {
              "id": 123456789,
              "name": "Manchester City",
              "odd": 1.95,
              "bookmaker": {
                "id": 1,
                "name": "Bet365",
                "priority": 1
              },
              "fractionalKey": "19/20"
            },
            {
              "id": 123456790,
              "name": "Draw",
              "odd": 3.5,
              "bookmaker": {
                "id": 1,
                "name": "Bet365",
                "priority": 1
              }
            },
            {
              "id": 123456791,
              "name": "Liverpool",
              "odd": 2.1,
              "bookmaker": {
                "id": 1,
                "name": "Bet365",
                "priority": 1
              }
            }
          ]
        }
      ]
    },
    {
      "marketName": "Goals Over Under",
      "marketKey": "totals",
      "groups": [
        {
          "odds": [
            {
              "name": "Over 2.5",
              "odd": 2.0,
              "point": 2.5
            },
            {
              "name": "Under 2.5",
              "odd": 1.87,
              "point": 2.5
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 3️⃣ ESPN API (Sin registrarse)

### Test 1: Obtener eventos de Soccer

```bash
curl "https://site.api.espn.com/us/site/v2/sports/soccer" | jq '.leagues[0].name'

# Muestra info de soccer
```

### Test 2: Obtener todos los sports disponibles

```bash
curl "https://site.api.espn.com/us/site/v2/sports" | jq '.sports[] | {name, abbreviation}'
```

### Test 3: Obtener eventos actuales de NFL

```bash
curl "https://site.api.espn.com/us/site/v2/sports/football/nfl/summary" | jq '.story[] | {headline, lastModified}'
```

---

## 4️⃣ COMPARACIÓN: Respuesta de cada API

### Script para comparar

```bash
#!/bin/bash

echo "================================"
echo "API COMPARISON TEST"
echo "================================"

# The Odds API (necesita API Key)
echo -e "\n1. THE ODDS API (Soccer)"
API_KEY="YOUR_API_KEY"
curl -s "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=$API_KEY&regions=us&markets=h2h,spreads,totals" | \
  jq '.[] | {home: .home_team, away: .away_team, bookmakers: (.bookmakers | length)}' | head -10

# SofaScore
echo -e "\n2. SOFASCORE (Football/Soccer)"
curl -s "https://www.sofascore.com/api/v1/sport/football/events/today" | \
  jq '.events[] | {home: .homeTeam.name, away: .awayTeam.name}' | head -10

# ESPN
echo -e "\n3. ESPN (Soccer Summary)"
curl -s "https://site.api.espn.com/us/site/v2/sports/soccer" | \
  jq '.leagues[0] | {name, numberOfEvents}'
```

---

## ✅ CHECKLIST: Después de Probar

- [ ] The Odds API: Logré registrarme y obtuve API Key
- [ ] The Odds API: Hice al menos 1 request exitoso
- [ ] SofaScore: Obtuve lista de eventos de hoy
- [ ] SofaScore: Obtuve odds de un evento
- [ ] Comparé h2h vs spreads vs totals en al menos 2 APIs
- [ ] Probé al menos 3 deportes diferentes
- [ ] Guardé los scripts que funcionaron para referencia

---

## 🐛 TROUBLESHOOTING

### "jq: command not found"
```bash
# Instalar jq
sudo apt-get install jq

# O usar python en lugar de jq
curl "..." | python3 -m json.tool
```

### "curl: (7) Failed to connect"
```bash
# Verificar conexión de internet
ping google.com

# O especificar timeout más largo
curl --max-time 30 "..."
```

### "Invalid API Key" (The Odds API)
```bash
# Verificar que copiaste bien la key
# Ir a https://www.the-odds-api.com/dashboard
# Copiar de nuevo sin espacios
```

### "No events returned"
```bash
# Puede ser que no haya eventos hoy
# Intenta con otro deporte o revisará mañana
curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events | length'
```

---

## 🎯 PRÓXIMO PASO

Una vez que confirmes que las APIs funcionan:

1. **Para usar The Odds API en código:**
   - Ver archivo: `FREE_ODDS_IMPLEMENTATION_GUIDE.md` sección 1
   
2. **Para usar SofaScore en código:**
   - Ver archivo: `FREE_ODDS_IMPLEMENTATION_GUIDE.md` sección 2
   
3. **Para stack completo:**
   - Ver archivo: `FREE_ODDS_IMPLEMENTATION_GUIDE.md` sección 4

