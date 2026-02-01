# 🛠️ GUÍA PRÁCTICA: Implementar APIs de Odds Gratis con Múltiples Mercados

**Fecha**: 29 de Enero de 2026  
**Objetivo**: Código listo para producción

---

## 1️⃣ THE ODDS API - OPCIÓN MÁS CONFIABLE

### Paso 1: Registrarse (2 minutos)

```bash
# Ir a https://www.the-odds-api.com/register
# Completar formulario
# Confirmar email
# Copiar API Key
```

### Paso 2: Guardar en .env

```bash
echo "ODDS_API_KEY=your_key_here" >> .env
```

### Paso 3: Cliente Python

```python
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime

class TheOddsAPIClient:
    """
    Cliente para The Odds API
    FREE: 500 requests/mes, h2h + spreads + totals
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    SPORT_MAPPING = {
        'soccer': 'soccer_epl',  # O cambia por otra liga
        'nfl': 'americanfootball_nfl',
        'nba': 'basketball_nba',
        'mlb': 'baseball_mlb',
        'nhl': 'hockey_nhl',
        'tennis': 'tennis_atp',  # O tennis_wta
        'rugby': 'rugby_union',
        'afl': 'aussie_rules_afl',
        'f1': 'formula1',
    }
    
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        if not self.api_key:
            raise ValueError("ODDS_API_KEY no configurada")
        self.request_count = 0
        self.request_limit = 500  # Per month
    
    def get_odds(self, sport: str, markets: str = 'h2h,spreads,totals') -> Dict:
        """
        Obtiene odds para un deporte
        
        Args:
            sport: 'soccer', 'nfl', 'nba', 'mlb', 'nhl', 'tennis', 'rugby', 'afl', 'f1'
            markets: 'h2h' | 'spreads' | 'totals' (separado por comas)
        
        Returns:
            Dict con eventos y odds
        """
        if self.request_count >= self.request_limit:
            return {
                'status': 'error',
                'message': 'API request limit exceeded (500/month)',
                'request_count': self.request_count
            }
        
        sport_key = self.SPORT_MAPPING.get(sport.lower())
        if not sport_key:
            return {'status': 'error', 'message': f'Sport {sport} not supported'}
        
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/odds"
            params = {
                'api_key': self.api_key,
                'regions': 'us',  # Cambia a 'uk', 'au' según necesidad
                'markets': markets,
                'oddsFormat': 'decimal'  # O 'american'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            self.request_count += 1
            data = response.json()
            
            return {
                'status': 'success',
                'sport': sport,
                'markets': markets.split(','),
                'events_count': len(data),
                'events': self._normalize_events(data),
                'request_count': self.request_count,
                'remaining_requests': self.request_limit - self.request_count
            }
        
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': str(e)}
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict]:
        """Normaliza respuesta a formato consistente"""
        normalized = []
        
        for event in events[:5]:  # Limita a 5 eventos por economía de requests
            try:
                home = event.get('home_team', 'Unknown')
                away = event.get('away_team', 'Unknown')
                time = event.get('commence_time', '')
                
                event_data = {
                    'id': event.get('id'),
                    'home': home,
                    'away': away,
                    'time': time,
                    'markets': {}
                }
                
                # Procesar odds
                if 'bookmakers' in event:
                    for bookmaker in event['bookmakers'][:3]:  # Top 3 bookmakers
                        book_name = bookmaker.get('title', 'Unknown')
                        book_odds = bookmaker.get('markets', [])
                        
                        for market in book_odds:
                            market_key = market.get('key', 'unknown')
                            
                            if market_key not in event_data['markets']:
                                event_data['markets'][market_key] = {}
                            
                            if book_name not in event_data['markets'][market_key]:
                                event_data['markets'][market_key][book_name] = []
                            
                            for outcome in market.get('outcomes', []):
                                event_data['markets'][market_key][book_name].append({
                                    'name': outcome.get('name'),
                                    'odds': outcome.get('price'),
                                    'point': outcome.get('point', None)
                                })
                
                normalized.append(event_data)
            
            except Exception as e:
                print(f"Error normalizing event: {e}")
                continue
        
        return normalized
    
    def get_best_odds(self, sport: str, market: str = 'h2h') -> Dict:
        """
        Obtiene solo los mejores odds por mercado
        
        Args:
            sport: Deporte
            market: 'h2h', 'spreads', o 'totals'
        """
        data = self.get_odds(sport, markets=market)
        
        if data['status'] != 'success':
            return data
        
        best_odds = []
        
        for event in data['events']:
            event_result = {
                'home': event['home'],
                'away': event['away'],
                'time': event['time'],
                'best_odds': {}
            }
            
            if market in event['markets']:
                all_bookmakers = event['markets'][market]
                
                for outcome_idx in range(len(list(all_bookmakers.values())[0]) if all_bookmakers else 0):
                    best_price = 0
                    best_book = None
                    outcome_name = None
                    
                    for book_name, outcomes in all_bookmakers.items():
                        if outcome_idx < len(outcomes):
                            outcome = outcomes[outcome_idx]
                            if outcome['odds'] > best_price:
                                best_price = outcome['odds']
                                best_book = book_name
                                outcome_name = outcome['name']
                    
                    if outcome_name and best_book:
                        event_result['best_odds'][outcome_name] = {
                            'odds': best_price,
                            'bookmaker': best_book
                        }
            
            best_odds.append(event_result)
        
        return {
            'status': 'success',
            'sport': sport,
            'market': market,
            'events': best_odds,
            'request_count': data['request_count'],
            'remaining_requests': data['remaining_requests']
        }

# Uso
if __name__ == '__main__':
    client = TheOddsAPIClient()
    
    # Obtener todos los odds (h2h + spreads + totals)
    soccer_odds = client.get_odds('soccer')
    print(f"Soccer events: {soccer_odds['events_count']}")
    print(f"Remaining requests: {soccer_odds['remaining_requests']}\n")
    
    # Obtener solo mejores odds para spreads
    nfl_spreads = client.get_best_odds('nfl', market='spreads')
    print(f"NFL Spreads (Best):")
    for event in nfl_spreads['events']:
        print(f"  {event['home']} vs {event['away']}")
        for outcome, odds_info in event['best_odds'].items():
            print(f"    {outcome}: {odds_info['odds']} ({odds_info['bookmaker']})")
```

---

## 2️⃣ SOFASCORE API - OPCIÓN ILIMITADA

### Ventaja: Sin registrarse, sin límites

```python
import requests
from typing import Dict, List, Optional
from datetime import datetime

class SofaScoreClient:
    """
    Cliente SofaScore
    FREE: Sin límites, sin autenticación
    MERCADOS: h2h, spreads, totals, parciales
    """
    
    BASE_URL = "https://www.sofascore.com/api/v1"
    
    SPORT_SLUGS = {
        'soccer': 'football',
        'basketball': 'basketball',
        'tennis': 'tennis',
        'hockey': 'hockey',
        'baseball': 'baseball',
        'rugby': 'rugby',
        'nfl': 'american-football',
        'mma': 'mma',
        'volleyball': 'volleyball',
        'handball': 'handball',
        'afl': 'australian-football',
        'f1': 'formula-1',
    }
    
    @staticmethod
    def get_today_events(sport: str) -> Dict:
        """Obtiene eventos de hoy"""
        sport_slug = SofaScoreClient.SPORT_SLUGS.get(sport.lower())
        if not sport_slug:
            return {'status': 'error', 'message': f'Sport {sport} not supported'}
        
        try:
            url = f"{SofaScoreClient.BASE_URL}/sport/{sport_slug}/events/today"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            return {
                'status': 'success',
                'sport': sport,
                'count': len(events),
                'events': SofaScoreClient._normalize_events(events)
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def get_event_odds(event_id: int) -> Dict:
        """Obtiene odds de un evento específico"""
        try:
            url = f"{SofaScoreClient.BASE_URL}/event/{event_id}/odds"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            markets = data.get('markets', [])
            
            return {
                'status': 'success',
                'event_id': event_id,
                'markets_count': len(markets),
                'markets': SofaScoreClient._normalize_odds(markets)
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _normalize_events(events: List[Dict]) -> List[Dict]:
        """Normaliza eventos"""
        normalized = []
        
        for event in events:
            try:
                home = event.get('homeTeam', {}).get('name', 'Unknown')
                away = event.get('awayTeam', {}).get('name', 'Unknown')
                status = event.get('status', {}).get('description', 'Unknown')
                
                normalized.append({
                    'id': event.get('id'),
                    'home': home,
                    'away': away,
                    'status': status,
                    'time': event.get('startTimestamp'),
                })
            except:
                continue
        
        return normalized
    
    @staticmethod
    def _normalize_odds(markets: List[Dict]) -> List[Dict]:
        """Normaliza odds"""
        normalized = []
        
        for market in markets:
            try:
                market_data = {
                    'name': market.get('marketName', 'Unknown'),
                    'key': market.get('marketKey', 'unknown'),
                    'bookmakers': {}
                }
                
                groups = market.get('groups', [])
                for group in groups:
                    for odd in group.get('odds', []):
                        bookmaker = odd.get('bookmaker', {}).get('name', 'Unknown')
                        
                        if bookmaker not in market_data['bookmakers']:
                            market_data['bookmakers'][bookmaker] = []
                        
                        market_data['bookmakers'][bookmaker].append({
                            'name': odd.get('name'),
                            'odds': odd.get('odd'),
                            'point': odd.get('point', None)
                        })
                
                normalized.append(market_data)
            except:
                continue
        
        return normalized

# Uso
if __name__ == '__main__':
    # Obtener eventos de hoy (soccer)
    soccer = SofaScoreClient.get_today_events('soccer')
    print(f"Soccer events today: {soccer['count']}")
    
    if soccer['events']:
        # Obtener odds del primer evento
        first_event = soccer['events'][0]
        event_id = first_event['id']
        odds = SofaScoreClient.get_event_odds(event_id)
        
        print(f"\nEvent: {first_event['home']} vs {first_event['away']}")
        print(f"Available markets: {odds['markets_count']}")
        
        for market in odds['markets']:
            print(f"\n  Market: {market['name']}")
            for bookmaker, outcomes in market['bookmakers'].items():
                print(f"    {bookmaker}:")
                for outcome in outcomes[:2]:  # First 2 outcomes
                    print(f"      - {outcome['name']}: {outcome['odds']}")
```

---

## 3️⃣ COMPARATIVA: Cuál Usar en Cada Caso

### Caso 1: "Necesito odds CONFIABLES de bookmakers reales"
```python
→ The Odds API FREE
✅ Datos verificados
✅ Oficial
⚠️ Limitado a 16 requests/día
```

### Caso 2: "Necesito cobertura de TODOS los deportes"
```python
→ SofaScore
✅ 12 deportes
✅ Sin límites
⚠️ API no oficial
```

### Caso 3: "Necesito máxima confiabilidad + respaldo"
```python
→ The Odds API (principal) + SofaScore (backup)
✅ Best of both worlds
⚠️ Código más complejo
```

### Caso 4: "Necesito múltiples mercados (spreads, totals)"
```python
→ SofaScore (ilimitado)
→ The Odds API (limitado pero oficial)
✅ Ambas soportan spreads + totals
❌ Nada soporta props o correct score
```

---

## 4️⃣ SCRIPT DE COMBINACIÓN - STACK COMPLETO

```python
"""
Stack Completo: Odds + Eventos + Mercados Múltiples (100% Gratis)
Usa:
- The Odds API para verificación de odds
- SofaScore como principal (ilimitado)
- ESPN para scores en vivo
"""

import requests
import os
from typing import Dict, List
from datetime import datetime

class CompleteFreeOddsStack:
    """Stack completo de odds gratis con múltiples mercados"""
    
    def __init__(self):
        self.odds_api_key = os.getenv('ODDS_API_KEY')
        self.sofascore_base = "https://www.sofascore.com/api/v1"
        self.odds_api_base = "https://api.the-odds-api.com/v4"
        self.espn_base = "https://site.api.espn.com/us/site/v2/sports"
        self.request_count = 0
    
    def get_complete_odds(self, sport: str) -> Dict:
        """
        Obtiene odds completos: SofaScore + The Odds API + ESPN scores
        """
        result = {
            'sport': sport,
            'timestamp': datetime.utcnow().isoformat(),
            'sofascore': {},
            'odds_api': {},
            'espn_scores': {},
            'combined_events': []
        }
        
        # 1. Obtener de SofaScore (sin límites)
        result['sofascore'] = self._get_sofascore_odds(sport)
        
        # 2. Obtener de The Odds API (para verificación)
        if self.odds_api_key:
            result['odds_api'] = self._get_odds_api_odds(sport)
        
        # 3. Obtener scores de ESPN
        result['espn_scores'] = self._get_espn_scores(sport)
        
        # 4. Combinar en una vista única
        result['combined_events'] = self._combine_sources(result)
        
        return result
    
    def _get_sofascore_odds(self, sport: str) -> Dict:
        """SofaScore - ilimitado"""
        try:
            sport_map = {
                'soccer': 'football',
                'nfl': 'american-football',
                'nba': 'basketball',
                'mlb': 'baseball',
                'nhl': 'hockey',
            }
            
            sport_slug = sport_map.get(sport.lower(), sport.lower())
            url = f"{self.sofascore_base}/sport/{sport_slug}/events/today"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            events = response.json().get('events', [])
            
            return {
                'status': 'success',
                'count': len(events),
                'events': [
                    {
                        'id': e['id'],
                        'home': e.get('homeTeam', {}).get('name'),
                        'away': e.get('awayTeam', {}).get('name'),
                    }
                    for e in events[:5]
                ]
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_odds_api_odds(self, sport: str) -> Dict:
        """The Odds API - limitado pero confiable"""
        try:
            sport_map = {
                'soccer': 'soccer_epl',
                'nfl': 'americanfootball_nfl',
                'nba': 'basketball_nba',
                'mlb': 'baseball_mlb',
                'nhl': 'hockey_nhl',
            }
            
            sport_key = sport_map.get(sport.lower())
            if not sport_key:
                return {'status': 'error', 'message': f'{sport} not mapped'}
            
            url = f"{self.odds_api_base}/sports/{sport_key}/odds"
            params = {
                'api_key': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'decimal'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            self.request_count += 1
            events = response.json()
            
            return {
                'status': 'success',
                'count': len(events),
                'request_count': self.request_count,
                'remaining': 500 - self.request_count,
                'events': [
                    {
                        'home': e.get('home_team'),
                        'away': e.get('away_team'),
                    }
                    for e in events[:3]
                ]
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_espn_scores(self, sport: str) -> Dict:
        """ESPN - scores en vivo"""
        try:
            url_map = {
                'soccer': f"{self.espn_base}/soccer",
                'nfl': f"{self.espn_base}/football/nfl",
                'nba': f"{self.espn_base}/basketball/nba",
                'mlb': f"{self.espn_base}/baseball/mlb",
                'nhl': f"{self.espn_base}/hockey/nhl",
            }
            
            url = url_map.get(sport.lower())
            if not url:
                return {'status': 'error', 'message': f'{sport} not available'}
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return {'status': 'success', 'url': url}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _combine_sources(self, data: Dict) -> List[Dict]:
        """Combina datos de múltiples fuentes"""
        combined = []
        
        sofascore_events = data['sofascore'].get('events', [])
        odds_api_events = data['odds_api'].get('events', [])
        
        # Combina por nombre de equipos
        for ss_event in sofascore_events[:5]:
            combined_event = {
                'home': ss_event['home'],
                'away': ss_event['away'],
                'sofascore_id': ss_event['id'],
                'verified_odds': None
            }
            
            # Busca en The Odds API para verificación
            for oa_event in odds_api_events:
                if (oa_event['home'] == ss_event['home'] and 
                    oa_event['away'] == ss_event['away']):
                    combined_event['verified_odds'] = 'Available'
            
            combined.append(combined_event)
        
        return combined

# Uso final
if __name__ == '__main__':
    stack = CompleteFreeOddsStack()
    
    for sport in ['soccer', 'nfl', 'nba', 'mlb', 'nhl']:
        print(f"\n{'='*50}")
        print(f"SPORT: {sport.upper()}")
        print('='*50)
        
        result = stack.get_complete_odds(sport)
        
        print(f"SofaScore: {result['sofascore'].get('count', 0)} events")
        print(f"The Odds API: {result['odds_api'].get('count', 0)} events")
        print(f"The Odds API remaining: {result['odds_api'].get('remaining', 'N/A')} requests")
        
        print(f"\nCombined view ({len(result['combined_events'])} events):")
        for event in result['combined_events'][:3]:
            status = "✅" if event['verified_odds'] else "⚠️"
            print(f"  {status} {event['home']} vs {event['away']}")
```

---

## 📝 RESUMEN RÁPIDO

| Necesidad | Solución | Código |
|-----------|----------|--------|
| Odds confiables | `TheOddsAPIClient` | Ver sección 1 |
| Ilimitado | `SofaScoreClient` | Ver sección 2 |
| Todo combinado | `CompleteFreeOddsStack` | Ver sección 4 |
| Solo spreads/totals | SofaScore | Gratuito |
| Props/Correct Score | NINGUNA (pagar) | N/A |

**Costo Total:** $0 ✅

