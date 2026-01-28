# 🛠️ IMPLEMENTACIÓN PRÁCTICA: Servicios de Odds Deportivas Gratuitas

**Fecha**: 28 de Enero de 2026  
**Objetivo**: Código listo para producción con APIs gratuitas

---

## 1. TheSportsDB Service (Eventos Generales)

**Archivo**: `api/services/thesportsdb_service.py`

```python
"""
TheSportsDB Service - Eventos Deportivos Gratuitos
Cobertura: Soccer, Rugby, NFL, Basketball, Hockey, Handball, Volleyball, AFL, Tennis, Baseball, F1, MMA
Costo: $0
Autenticación: No
Rate Limit: Generoso (sin documentación restrictiva)
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TheSportsDBService:
    """Service para eventos deportivos de TheSportsDB"""
    
    BASE_URL = "https://www.thesportsdb.com/api/v1/json/1"
    
    # League IDs mapping
    LEAGUE_IDS = {
        'soccer': {
            'premier_league': 133602,
            'bundesliga': 133603,
            'la_liga': 133604,
            'serie_a': 133605,
            'ligue_1': 133606,
            'mls': 133607,
            'champions_league': 133608,
        },
        'american_football': {
            'nfl': 133602,
        },
        'basketball': {
            'nba': 133600,
            'euroleague': 133601,
        },
        'hockey': {
            'nhl': 133655,
            'khl': 133654,
        },
        'tennis': {
            'grand_slam': 133678,
            'atp': 133679,
            'wta': 133680,
        },
        'baseball': {
            'mlb': 133602,
        },
        'rugby': {
            'six_nations': 133662,
            'rugby_championship': 133663,
        },
        'volleyball': {
            'world_cup': 133690,
        },
        'handball': {
            'champions_league': 133700,
        },
        'mma': {
            'ufc': 133650,
        },
        'afl': {
            'australian_league': 133645,
        },
        'formula_1': {
            'f1': 133629,
        }
    }
    
    @staticmethod
    def get_last_events(league_id: int) -> Dict:
        """
        Obtiene los últimos eventos de una liga
        
        Args:
            league_id: ID de la liga
            
        Returns:
            Diccionario con eventos
        """
        try:
            url = f"{TheSportsDBService.BASE_URL}/eventslast.php"
            params = {'id': league_id}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved {len(data.get('results', []))} events from league {league_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting events from TheSportsDB: {e}")
            return {'results': []}
    
    @staticmethod
    def get_events_by_date(league_id: int, date: str) -> Dict:
        """
        Obtiene eventos por fecha (YYYY-MM-DD)
        
        Args:
            league_id: ID de la liga
            date: Fecha en formato YYYY-MM-DD
            
        Returns:
            Diccionario con eventos
        """
        try:
            url = f"{TheSportsDBService.BASE_URL}/eventsday.php"
            params = {'id': league_id, 'd': date}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved events for {date} from league {league_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting events by date: {e}")
            return {'results': []}
    
    @staticmethod
    def get_future_events(league_id: int) -> Dict:
        """
        Obtiene próximos eventos
        
        Args:
            league_id: ID de la liga
            
        Returns:
            Diccionario con eventos futuros
        """
        try:
            url = f"{TheSportsDBService.BASE_URL}/eventslast.php"
            params = {'id': league_id}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting future events: {e}")
            return {'results': []}
    
    @staticmethod
    def get_league_events(sport: str, league: str) -> Dict:
        """
        Obtiene eventos para un deporte/liga específica
        
        Args:
            sport: Tipo de deporte (e.g., 'soccer', 'basketball')
            league: Nombre de la liga
            
        Returns:
            Diccionario con eventos
        """
        if sport not in TheSportsDBService.LEAGUE_IDS:
            logger.warning(f"Sport {sport} not found in LEAGUE_IDS")
            return {'results': []}
        
        if league not in TheSportsDBService.LEAGUE_IDS[sport]:
            logger.warning(f"League {league} not found for sport {sport}")
            return {'results': []}
        
        league_id = TheSportsDBService.LEAGUE_IDS[sport][league]
        return TheSportsDBService.get_last_events(league_id)

# Ejemplo de uso:
if __name__ == "__main__":
    # Soccer - Premier League
    pl_events = TheSportsDBService.get_league_events('soccer', 'premier_league')
    print(f"Premier League: {len(pl_events.get('results', []))} events")
    
    # NFL
    nfl_events = TheSportsDBService.get_league_events('american_football', 'nfl')
    print(f"NFL: {len(nfl_events.get('results', []))} events")
    
    # NBA
    nba_events = TheSportsDBService.get_league_events('basketball', 'nba')
    print(f"NBA: {len(nba_events.get('results', []))} events")
    
    # Tennis ATP
    atp_events = TheSportsDBService.get_league_events('tennis', 'atp')
    print(f"ATP: {len(atp_events.get('results', []))} events")
    
    # Baseball MLB
    mlb_events = TheSportsDBService.get_league_events('baseball', 'mlb')
    print(f"MLB: {len(mlb_events.get('results', []))} events")
```

---

## 2. SofaScore Service (Con Odds)

**Archivo**: `api/services/sofascore_service.py`

```python
"""
SofaScore Service - Eventos con Odds en Vivo
Cobertura: Soccer, Tennis, Basketball, Hockey, Baseball, MMA, Rugby, American Football, Volleyball, Handball, F1
Costo: $0
Autenticación: No
Rate Limit: Generoso
"""

import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SofaScoreService:
    """Service para obtener eventos y odds de SofaScore"""
    
    BASE_URL = "https://www.sofascore.com/api/v1"
    
    SPORT_SLUGS = {
        'soccer': 'football',
        'football': 'football',
        'tennis': 'tennis',
        'basketball': 'basketball',
        'nba': 'basketball',
        'hockey': 'hockey',
        'nhl': 'hockey',
        'baseball': 'baseball',
        'mlb': 'baseball',
        'mma': 'mma',
        'ufc': 'mma',
        'american_football': 'american-football',
        'nfl': 'american-football',
        'volleyball': 'volleyball',
        'rugby': 'rugby',
        'formula_1': 'formula-1',
        'f1': 'formula-1',
        'handball': 'handball',
        'afl': 'australian-football',
    }
    
    @staticmethod
    def get_events_today(sport: str) -> Dict:
        """
        Obtiene eventos de hoy para un deporte
        
        Args:
            sport: Tipo de deporte (soccer, tennis, basketball, etc.)
            
        Returns:
            Diccionario con eventos de hoy
        """
        try:
            sport_slug = SofaScoreService.SPORT_SLUGS.get(sport.lower(), sport)
            url = f"{SofaScoreService.BASE_URL}/sport/{sport_slug}/events/today"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            event_count = len(data.get('events', []))
            logger.info(f"Retrieved {event_count} {sport} events for today")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting events for {sport}: {e}")
            return {'events': []}
    
    @staticmethod
    def get_event_odds(event_id: int) -> Dict:
        """
        Obtiene odds para un evento específico
        
        Args:
            event_id: ID del evento
            
        Returns:
            Diccionario con odds disponibles
        """
        try:
            url = f"{SofaScoreService.BASE_URL}/event/{event_id}/odds"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved odds for event {event_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting odds for event {event_id}: {e}")
            return {'markets': []}
    
    @staticmethod
    def get_events_with_odds(sport: str) -> List[Dict]:
        """
        Obtiene eventos de hoy con sus odds disponibles
        
        Args:
            sport: Tipo de deporte
            
        Returns:
            Lista de eventos con odds
        """
        try:
            events_response = SofaScoreService.get_events_today(sport)
            events = events_response.get('events', [])
            
            results = []
            for event in events[:10]:  # Limitar a 10 para no sobrecargar
                event_id = event.get('id')
                odds_data = SofaScoreService.get_event_odds(event_id)
                
                results.append({
                    'event': event,
                    'odds': odds_data.get('markets', [])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting events with odds: {e}")
            return []
    
    @staticmethod
    def get_tournament_events(tournament_id: int, season_id: int) -> Dict:
        """
        Obtiene eventos de un torneo específico en una temporada
        
        Args:
            tournament_id: ID del torneo
            season_id: ID de la temporada
            
        Returns:
            Diccionario con eventos
        """
        try:
            url = f"{SofaScoreService.BASE_URL}/tournament/{tournament_id}/season/{season_id}/events/today"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting tournament events: {e}")
            return {'events': []}
    
    @staticmethod
    def get_team_events(team_id: int) -> Dict:
        """
        Obtiene eventos de un equipo específico
        
        Args:
            team_id: ID del equipo
            
        Returns:
            Diccionario con eventos del equipo
        """
        try:
            url = f"{SofaScoreService.BASE_URL}/team/{team_id}/events/last"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting team events: {e}")
            return {'events': []}
    
    @staticmethod
    def parse_odds_markets(odds_data: Dict) -> List[Dict]:
        """
        Parsea mercados de odds en formato consistente
        
        Args:
            odds_data: Datos de odds del API
            
        Returns:
            Lista de mercados parseados
        """
        markets = []
        for market in odds_data.get('markets', []):
            parsed_market = {
                'name': market.get('marketName'),
                'type': market.get('marketType'),
                'groups': []
            }
            
            for group in market.get('groups', []):
                parsed_group = {
                    'type': group.get('type'),
                    'odds': []
                }
                
                for odd in group.get('odds', []):
                    parsed_group['odds'].append({
                        'name': odd.get('name'),
                        'value': float(odd.get('odd', 0)),
                    })
                
                parsed_market['groups'].append(parsed_group)
            
            markets.append(parsed_market)
        
        return markets

# Ejemplo de uso:
if __name__ == "__main__":
    # Soccer eventos de hoy
    soccer = SofaScoreService.get_events_today('soccer')
    print(f"Soccer today: {len(soccer.get('events', []))} matches")
    
    # Tennis eventos de hoy con odds
    tennis = SofaScoreService.get_events_with_odds('tennis')
    print(f"Tennis today: {len(tennis)} matches with odds")
    
    # Basketball
    basketball = SofaScoreService.get_events_today('basketball')
    print(f"Basketball today: {len(basketball.get('events', []))} matches")
    
    # MMA
    mma = SofaScoreService.get_events_today('mma')
    print(f"MMA today: {len(mma.get('events', []))} matches")
```

---

## 3. ESPN Service (Scores + Datos)

**Archivo**: `api/services/espn_service.py`

```python
"""
ESPN Service - Scores y Datos de Deportes
Cobertura: Soccer, Baseball, Football, Basketball, Hockey, Tennis, etc.
Costo: $0
Autenticación: No
"""

import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ESPNService:
    """Service para obtener datos de ESPN"""
    
    BASE_URL = "https://site.api.espn.com/us/site/v2/sports"
    
    @staticmethod
    def get_soccer_events() -> Dict:
        """Obtiene eventos de Soccer/Football"""
        try:
            url = f"{ESPNService.BASE_URL}/soccer"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting soccer events: {e}")
            return {'events': []}
    
    @staticmethod
    def get_mlb_scores() -> Dict:
        """Obtiene scores de MLB"""
        try:
            url = f"{ESPNService.BASE_URL}/baseball/mlb"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting MLB scores: {e}")
            return {'events': []}
    
    @staticmethod
    def get_nfl_scores() -> Dict:
        """Obtiene scores de NFL"""
        try:
            url = f"{ESPNService.BASE_URL}/football/nfl"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting NFL scores: {e}")
            return {'events': []}
    
    @staticmethod
    def get_nba_scores() -> Dict:
        """Obtiene scores de NBA"""
        try:
            url = f"{ESPNService.BASE_URL}/basketball/nba"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting NBA scores: {e}")
            return {'events': []}
    
    @staticmethod
    def get_nhl_scores() -> Dict:
        """Obtiene scores de NHL"""
        try:
            url = f"{ESPNService.BASE_URL}/hockey/nhl"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting NHL scores: {e}")
            return {'events': []}
    
    @staticmethod
    def get_tennis_atp() -> Dict:
        """Obtiene eventos de ATP"""
        try:
            url = f"{ESPNService.BASE_URL}/tennis/atp"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting ATP events: {e}")
            return {'events': []}
    
    @staticmethod
    def get_tennis_wta() -> Dict:
        """Obtiene eventos de WTA"""
        try:
            url = f"{ESPNService.BASE_URL}/tennis/wta"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting WTA events: {e}")
            return {'events': []}
    
    @staticmethod
    def get_standings(sport: str, league: str = None) -> Dict:
        """
        Obtiene standings/clasificaciones
        
        Args:
            sport: Tipo de deporte (baseball, football, basketball, hockey)
            league: Liga específica si aplica (mlb, nfl, nba, nhl)
            
        Returns:
            Diccionario con standings
        """
        try:
            if league:
                url = f"{ESPNService.BASE_URL}/{sport}/{league}/standings"
            else:
                url = f"{ESPNService.BASE_URL}/{sport}/standings"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting standings: {e}")
            return {'groups': []}

# Ejemplo de uso:
if __name__ == "__main__":
    # MLB Scores
    mlb = ESPNService.get_mlb_scores()
    print(f"MLB: {len(mlb.get('events', []))} matches")
    
    # NFL Scores
    nfl = ESPNService.get_nfl_scores()
    print(f"NFL: {len(nfl.get('events', []))} matches")
    
    # NBA Scores
    nba = ESPNService.get_nba_scores()
    print(f"NBA: {len(nba.get('events', []))} matches")
    
    # Tennis
    atp = ESPNService.get_tennis_atp()
    print(f"ATP: {len(atp.get('events', []))} matches")
```

---

## 4. Servicio Unificado (Multi-Fuente)

**Archivo**: `api/services/unified_odds_service.py`

```python
"""
Unified Odds Service - Integra múltiples fuentes gratuitas
Proporciona interfaz consistente para acceder a odds de múltiples deportes
"""

import logging
from typing import Dict, List, Optional
from api.services.thesportsdb_service import TheSportsDBService
from api.services.sofascore_service import SofaScoreService
from api.services.espn_service import ESPNService

logger = logging.getLogger(__name__)

class UnifiedOddsService:
    """Servicio unificado para odds deportivas de múltiples fuentes gratuitas"""
    
    @staticmethod
    def get_soccer_events_with_odds() -> Dict:
        """
        Obtiene eventos de soccer de múltiples fuentes
        Combinando TheSportsDB, SofaScore y ESPN
        """
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
            'timestamp': None
        }
        
        try:
            # SofaScore (con odds)
            sofascore_data = SofaScoreService.get_events_with_odds('soccer')
            result['from_sofascore'] = sofascore_data
        except Exception as e:
            logger.error(f"Error getting soccer from SofaScore: {e}")
        
        try:
            # ESPN
            espn_data = ESPNService.get_soccer_events()
            result['from_espn'] = espn_data
        except Exception as e:
            logger.error(f"Error getting soccer from ESPN: {e}")
        
        try:
            # TheSportsDB
            thesportsdb_data = TheSportsDBService.get_league_events('soccer', 'premier_league')
            result['from_thesportsdb'] = thesportsdb_data
        except Exception as e:
            logger.error(f"Error getting soccer from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_baseball_events_with_odds() -> Dict:
        """Obtiene eventos de baseball de múltiples fuentes"""
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
        }
        
        try:
            result['from_sofascore'] = SofaScoreService.get_events_with_odds('baseball')
        except Exception as e:
            logger.error(f"Error getting baseball from SofaScore: {e}")
        
        try:
            result['from_espn'] = ESPNService.get_mlb_scores()
        except Exception as e:
            logger.error(f"Error getting baseball from ESPN: {e}")
        
        try:
            result['from_thesportsdb'] = TheSportsDBService.get_league_events('baseball', 'mlb')
        except Exception as e:
            logger.error(f"Error getting baseball from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_tennis_events_with_odds() -> Dict:
        """Obtiene eventos de tennis de múltiples fuentes"""
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
        }
        
        try:
            result['from_sofascore'] = SofaScoreService.get_events_with_odds('tennis')
        except Exception as e:
            logger.error(f"Error getting tennis from SofaScore: {e}")
        
        try:
            # ATP y WTA
            result['from_espn'] = {
                'atp': ESPNService.get_tennis_atp(),
                'wta': ESPNService.get_tennis_wta()
            }
        except Exception as e:
            logger.error(f"Error getting tennis from ESPN: {e}")
        
        try:
            result['from_thesportsdb'] = TheSportsDBService.get_league_events('tennis', 'atp')
        except Exception as e:
            logger.error(f"Error getting tennis from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_nfl_events_with_odds() -> Dict:
        """Obtiene eventos de NFL de múltiples fuentes"""
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
        }
        
        try:
            result['from_sofascore'] = SofaScoreService.get_events_with_odds('american_football')
        except Exception as e:
            logger.error(f"Error getting NFL from SofaScore: {e}")
        
        try:
            result['from_espn'] = ESPNService.get_nfl_scores()
        except Exception as e:
            logger.error(f"Error getting NFL from ESPN: {e}")
        
        try:
            result['from_thesportsdb'] = TheSportsDBService.get_league_events('american_football', 'nfl')
        except Exception as e:
            logger.error(f"Error getting NFL from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_nba_events_with_odds() -> Dict:
        """Obtiene eventos de NBA de múltiples fuentes"""
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
        }
        
        try:
            result['from_sofascore'] = SofaScoreService.get_events_with_odds('basketball')
        except Exception as e:
            logger.error(f"Error getting NBA from SofaScore: {e}")
        
        try:
            result['from_espn'] = ESPNService.get_nba_scores()
        except Exception as e:
            logger.error(f"Error getting NBA from ESPN: {e}")
        
        try:
            result['from_thesportsdb'] = TheSportsDBService.get_league_events('basketball', 'nba')
        except Exception as e:
            logger.error(f"Error getting NBA from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_hockey_events_with_odds() -> Dict:
        """Obtiene eventos de Hockey de múltiples fuentes"""
        result = {
            'from_sofascore': [],
            'from_espn': [],
            'from_thesportsdb': [],
        }
        
        try:
            result['from_sofascore'] = SofaScoreService.get_events_with_odds('hockey')
        except Exception as e:
            logger.error(f"Error getting Hockey from SofaScore: {e}")
        
        try:
            result['from_espn'] = ESPNService.get_nhl_scores()
        except Exception as e:
            logger.error(f"Error getting Hockey from ESPN: {e}")
        
        try:
            result['from_thesportsdb'] = TheSportsDBService.get_league_events('hockey', 'nhl')
        except Exception as e:
            logger.error(f"Error getting Hockey from TheSportsDB: {e}")
        
        return result
    
    @staticmethod
    def get_all_sports_overview() -> Dict:
        """
        Obtiene resumen de todos los deportes de múltiples fuentes
        """
        return {
            'soccer': UnifiedOddsService.get_soccer_events_with_odds(),
            'baseball': UnifiedOddsService.get_baseball_events_with_odds(),
            'tennis': UnifiedOddsService.get_tennis_events_with_odds(),
            'nfl': UnifiedOddsService.get_nfl_events_with_odds(),
            'nba': UnifiedOddsService.get_nba_events_with_odds(),
            'hockey': UnifiedOddsService.get_hockey_events_with_odds(),
        }

# Ejemplo de uso:
if __name__ == "__main__":
    service = UnifiedOddsService()
    
    # Obtener overview completo
    overview = service.get_all_sports_overview()
    print("Overview de todos los deportes:")
    for sport, data in overview.items():
        print(f"\n{sport.upper()}:")
        print(f"  - SofaScore: {len(data['from_sofascore'])} eventos")
        print(f"  - ESPN: {len(str(data['from_espn']))} caracteres de datos")
        print(f"  - TheSportsDB: {len(str(data['from_thesportsdb']))} caracteres de datos")
```

---

## 5. Instalación y Configuración

### Archivo: `.env` (Variables de entorno)

```bash
# APIs Gratuitas - No requieren API Keys
# Pero algunos pueden usarlos opcionalmente

# TheSportsDB (No requiere, opcional)
THESPORTSDB_ENABLED=true

# SofaScore (No requiere API key)
SOFASCORE_ENABLED=true

# ESPN (No requiere API key)
ESPN_ENABLED=true

# The Odds API (Requiere API key para tier gratis)
# Registrarse en: https://the-odds-api.com/
THE_ODDS_API_KEY=optional
THE_ODDS_API_ENABLED=false  # Usar solo si tienes API key

# Rate limiting (ms entre requests)
API_REQUEST_DELAY=100
```

### Archivo: `requirements.txt`

```
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## 6. Ejemplo de Endpoint FastAPI

**Archivo**: `api/main.py` (Agregar estos endpoints)

```python
from fastapi import APIRouter, HTTPException
from api.services.unified_odds_service import UnifiedOddsService

router = APIRouter(prefix="/api/odds", tags=["odds"])

@router.get("/sports/all")
async def get_all_sports_odds():
    """
    Obtiene overview de todos los deportes con odds de múltiples fuentes gratuitas
    """
    try:
        data = UnifiedOddsService.get_all_sports_overview()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/soccer")
async def get_soccer_odds():
    """Obtiene odds de soccer"""
    try:
        data = UnifiedOddsService.get_soccer_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/baseball")
async def get_baseball_odds():
    """Obtiene odds de baseball"""
    try:
        data = UnifiedOddsService.get_baseball_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tennis")
async def get_tennis_odds():
    """Obtiene odds de tennis"""
    try:
        data = UnifiedOddsService.get_tennis_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nfl")
async def get_nfl_odds():
    """Obtiene odds de NFL"""
    try:
        data = UnifiedOddsService.get_nfl_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nba")
async def get_nba_odds():
    """Obtiene odds de NBA"""
    try:
        data = UnifiedOddsService.get_nba_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hockey")
async def get_hockey_odds():
    """Obtiene odds de Hockey"""
    try:
        data = UnifiedOddsService.get_hockey_events_with_odds()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

**Última actualización**: 28 de Enero de 2026
