# 🏗️ ARQUITECTURA Y RECOMENDACIONES FINALES

**Fecha**: 28 de Enero de 2026  
**Objetivo**: Guía de arquitectura para integración óptima

---

## 🎯 ARQUITECTURA RECOMENDADA

### Nivel 1: Arquitectura Simple (Para empezar)

```
┌─────────────────────────────────────────────────────────────┐
│                    TU APLICACIÓN                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              OddsAggregatorService                          │
│  (Combina múltiples APIs en una interfaz unificada)        │
└─────────────────────────────────────────────────────────────┘
                ↙            ↓            ↘
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │SofaScore │   │TheSports │   │   ESPN   │
        │  (Odds)  │   │   DB     │   │(Backup)  │
        └──────────┘   └──────────┘   └──────────┘
```

**Implementación Simple**:
```python
class OddsAggregatorService:
    def get_events_with_odds(self, sport):
        # Intenta SofaScore primero
        try:
            return SofaScoreService.get_events_with_odds(sport)
        except:
            # Fallback a TheSportsDB
            return TheSportsDBService.get_league_events(sport, league_name)
```

---

### Nivel 2: Arquitectura Robusta (Con caché y fallback)

```
┌─────────────────────────────────────────────────────────────┐
│                    TU APLICACIÓN                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              OddsService (Interfaz unificada)               │
│  ├─ get_events(sport)                                      │
│  ├─ get_events_with_odds(sport)                            │
│  └─ cache management                                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
    ┌────────┐         ┌────────┐         ┌────────┐
    │ Cache  │         │ Retry  │         │Circuit │
    │(Redis) │         │Logic   │         │Breaker │
    └────────┘         └────────┘         └────────┘
        ↓                  ↓                  ↓
┌──────────────────────────────────────────────────────────┐
│              API Aggregator (Multi-fuente)               │
└──────────────────────────────────────────────────────────┘
        ↙            ↓             ↘
    ┌───────┐    ┌───────┐    ┌───────┐
    │Sofa   │    │Sports │    │ ESPN  │
    │Score  │    │  DB   │    │       │
    └───────┘    └───────┘    └───────┘
```

**Implementación Robusta**:
```python
class RobustOddsService:
    def __init__(self, cache_ttl=300):
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.primary = SofaScoreService
        self.secondary = TheSportsDBService
        self.tertiary = ESPNService
    
    def get_events_with_odds(self, sport):
        # 1. Check cache
        cache_key = f"{sport}_events"
        if cache_key in self.cache and not self._is_expired(cache_key):
            return self.cache[cache_key]
        
        # 2. Try primary (SofaScore)
        try:
            data = self.primary.get_events_with_odds(sport)
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.warning(f"Primary failed for {sport}: {e}")
        
        # 3. Try secondary (TheSportsDB)
        try:
            data = self.secondary.get_league_events(sport, league)
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.warning(f"Secondary failed for {sport}: {e}")
        
        # 4. Try tertiary (ESPN)
        try:
            data = self.tertiary.get_events(sport)
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"All sources failed for {sport}: {e}")
            return {"error": "No data available"}
    
    def _set_cache(self, key, data):
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _is_expired(self, key):
        timestamp = self.cache[key]['timestamp']
        return (time.time() - timestamp) > self.cache_ttl
```

---

### Nivel 3: Arquitectura Enterprise (Con monitoring)

```
┌────────────────────────────────────────────────────────────┐
│                   TU APLICACIÓN                            │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│         Enterprise Odds Service                            │
│  ├─ Unified API                                           │
│  ├─ Health checks                                         │
│  ├─ Metrics & Logging                                     │
│  └─ Auto-scaling logic                                    │
└────────────────────────────────────────────────────────────┘
                ↙         ↓         ↘
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Cache   │ │ Database │ │ Queue    │
        │ (Redis)  │ │ (Postgres)│ │ (RabbitMQ)
        └──────────┘ └──────────┘ └──────────┘
                ↓         ↓         ↓
┌────────────────────────────────────────────────────────────┐
│           Load Balancer & Circuit Breaker                  │
│  - Metrics collection                                     │
│  - Health monitoring                                      │
│  - Auto-retry with backoff                                │
└────────────────────────────────────────────────────────────┘
        ↙            ↓             ↘
    ┌───────┐    ┌───────┐    ┌───────┐
    │Sofa   │    │Sports │    │ ESPN  │
    │Score  │    │  DB   │    │       │
    └───────┘    └───────┘    └───────┘
                
        ↙            ↓             ↘
    ┌────────────────────────────────────────┐
    │      Monitoring & Alerting              │
    │  - Prometheus metrics                  │
    │  - Grafana dashboards                  │
    │  - PagerDuty alerts                    │
    └────────────────────────────────────────┘
```

---

## 🛠️ CONFIGURACIÓN RECOMENDADA POR CASO

### Caso 1: MVP / Prototipo (Hoy)
```
Arquitectura: Level 1 (Simple)
APIs: SofaScore + TheSportsDB
Cache: None (al principio)
Database: None
Time to market: 30 minutos
Costo: $0
```

### Caso 2: Aplicación Pequeña (Semana 1)
```
Arquitectura: Level 2 (Robusta)
APIs: SofaScore + TheSportsDB + ESPN
Cache: In-memory con TTL
Database: Opcional (para historiales)
Time to market: 2-3 horas
Costo: $0
```

### Caso 3: Aplicación Mediana (Mes 1)
```
Arquitectura: Level 2/3 (Robusta+)
APIs: SofaScore + TheSportsDB + ESPN + The Odds API ($39/mes)
Cache: Redis
Database: PostgreSQL (historiales)
Monitoring: Prometheus + Grafana
Time to market: 1 semana
Costo: $39/mes
```

### Caso 4: Aplicación Enterprise (Escalada)
```
Arquitectura: Level 3 (Enterprise)
APIs: Multi-source con fallback
Cache: Redis Cluster
Database: PostgreSQL + TimescaleDB
Queue: RabbitMQ o Kafka
Monitoring: Full stack (Prometheus, ELK, PagerDuty)
Time to market: 2-3 semanas
Costo: $100-500/mes (infraestructura)
```

---

## 🔄 PATRÓN: Circuit Breaker

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Fallback mode
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Uso
cb = CircuitBreaker()

def get_odds_safe(sport):
    try:
        return cb.call(SofaScoreService.get_events_with_odds, sport)
    except:
        return TheSportsDBService.get_league_events(sport, league_name)
```

---

## 📊 ESTRATEGIA DE CACHÉ

### Opción 1: TTL Simple (Recomendado para MVP)
```python
class SimpleCacheService:
    def __init__(self):
        self.cache = {}
    
    def get_with_cache(self, key, fetch_func, ttl=300):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < ttl:
                return data  # Return cached
        
        # Fetch new data
        data = fetch_func()
        self.cache[key] = (data, time.time())
        return data
```

**Tiempo de caché recomendado**:
```
Eventos en vivo: 30-60 segundos
Odds: 60-120 segundos
Standings: 5-10 minutos
Información estática: 1 hora
```

### Opción 2: Redis Cluster (Para escala)
```python
import redis

class RedisCacheService:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379)
    
    def get_with_cache(self, key, fetch_func, ttl=300):
        # Try cache
        cached = self.client.get(key)
        if cached:
            return json.loads(cached)
        
        # Fetch new
        data = fetch_func()
        self.client.setex(key, ttl, json.dumps(data))
        return data
```

---

## ⚡ RATE LIMITING STRATEGY

### Sin Rate Limit en APIs (Caso Normal)
```python
class SimpleRateLimiter:
    def __init__(self, min_delay_ms=100):
        self.min_delay = min_delay_ms / 1000
        self.last_call = 0
    
    def wait_if_needed(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_call = time.time()

limiter = SimpleRateLimiter(min_delay_ms=100)

def get_events_rate_limited(sport):
    limiter.wait_if_needed()
    return SofaScoreService.get_events_with_odds(sport)
```

### Con Rate Limit Distribuido (Para escala)
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls per minute
def api_call():
    return SofaScoreService.get_events_with_odds('football')
```

---

## 🚀 DEPLOYMENT PATTERNS

### Pattern 1: Simple (Single Server)
```
┌──────────────────┐
│  Single Server   │
│  ├─ FastAPI app  │
│  ├─ Cache (RAM)  │
│  └─ Logs         │
└──────────────────┘
         ↓
    ┌─────────────┐
    │  APIs       │
    │  (External) │
    └─────────────┘
```

### Pattern 2: Scalable (Load Balanced)
```
┌────────────────────┐
│   Load Balancer    │
│   (nginx/haproxy)  │
└─────────┬──────────┘
      ↙   ↓   ↘
  ┌─────┐ ┌─────┐ ┌─────┐
  │ App1│ │ App2│ │ App3│
  └──┬──┘ └──┬──┘ └──┬──┘
     └───────┼───────┘
            ↓
       ┌──────────┐
       │ Redis    │
       │ Cache    │
       └──────────┘
```

### Pattern 3: Enterprise (Microservices)
```
┌───────────────────────────────────┐
│   API Gateway                     │
│   (Kong/Ambassador)               │
└────────────┬──────────────────────┘
         ↙   ↓   ↘
    ┌──────┬──────┬──────┐
    ↓      ↓      ↓      ↓
┌────────────────────────────────┐
│  Microservices                 │
│  ├─ Odds Service               │
│  ├─ Events Service             │
│  ├─ Cache Service              │
│  └─ Monitoring Service         │
└────────────────────────────────┘
         ↓     ↓     ↓
    ┌───────────────────────┐
    │ Data Layer            │
    │ ├─ PostgreSQL         │
    │ ├─ Redis              │
    │ └─ TimescaleDB        │
    └───────────────────────┘
```

---

## 📋 IMPLEMENTACIÓN STEP-BY-STEP

### Paso 1: Setup Inicial (15 min)
```bash
# 1. Crear directorio de servicios
mkdir -p api/services/odds

# 2. Copiar servicios
cp FREE_ODDS_APIS_IMPLEMENTATION.md api/services/odds/

# 3. Instalar dependencias
pip install requests python-dotenv

# 4. Crear .env
cat > .env << EOF
SOFASCORE_ENABLED=true
THESPORTSDB_ENABLED=true
ESPN_ENABLED=true
API_REQUEST_DELAY=100
EOF
```

### Paso 2: Integración (30 min)
```python
# File: api/services/odds/__init__.py
from api.services.odds.sofascore_service import SofaScoreService
from api.services.odds.thesportsdb_service import TheSportsDBService
from api.services.odds.espn_service import ESPNService
from api.services.odds.unified_service import UnifiedOddsService

__all__ = [
    'SofaScoreService',
    'TheSportsDBService',
    'ESPNService',
    'UnifiedOddsService'
]
```

### Paso 3: Endpoints FastAPI (15 min)
```python
# File: api/routers/odds.py
from fastapi import APIRouter, HTTPException
from api.services.odds import UnifiedOddsService

router = APIRouter(prefix="/api/odds", tags=["odds"])

@router.get("/sports/all")
async def get_all_sports():
    """Get all sports with odds"""
    try:
        service = UnifiedOddsService()
        return service.get_all_sports_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Agregar a tu main.py
# from api.routers import odds
# app.include_router(odds.router)
```

### Paso 4: Testing (15 min)
```python
# File: tests/test_odds_apis.py
def test_sofascore_soccer():
    from api.services.odds import SofaScoreService
    data = SofaScoreService.get_events_today('football')
    assert 'events' in data
    assert isinstance(data['events'], list)

def test_thesportsdb_football():
    from api.services.odds import TheSportsDBService
    data = TheSportsDBService.get_league_events('soccer', 'premier_league')
    assert 'results' in data or 'events' in data

def test_all_12_sports():
    from api.services.odds import UnifiedOddsService
    service = UnifiedOddsService()
    overview = service.get_all_sports_overview()
    assert 'soccer' in overview
    assert 'tennis' in overview
    # ... test all 12
```

### Paso 5: Deployment (Variado)
```bash
# Local development
python -m uvicorn api.main:app --reload

# Docker
docker build -t odds-api .
docker run -p 8000:8000 odds-api

# Cloud (Render, Heroku, etc)
# Simplemente deploy tu app - APIs gratuitas no requieren config
```

---

## 📈 MÉTRICAS A MONITOREAR

```python
class OddsMetrics:
    # Request metrics
    requests_total = Counter('odds_requests_total', 'Total requests')
    request_duration = Histogram('odds_request_duration_seconds', 'Request duration')
    request_errors = Counter('odds_request_errors_total', 'Request errors')
    
    # Cache metrics
    cache_hits = Counter('odds_cache_hits_total', 'Cache hits')
    cache_misses = Counter('odds_cache_misses_total', 'Cache misses')
    
    # API health
    sofascore_health = Gauge('odds_sofascore_health', 'SofaScore health')
    thesportsdb_health = Gauge('odds_thesportsdb_health', 'TheSportsDB health')
    espn_health = Gauge('odds_espn_health', 'ESPN health')
```

---

## 🎯 TIMELINE RECOMENDADO

### Semana 1: MVP
- Día 1: Setup + integración básica (2 horas)
- Día 2-3: Testing y ajustes (4 horas)
- Día 4-5: Deployment (2 horas)
- **Total**: 8 horas de trabajo

### Semana 2-3: Optimización
- Agregar caché (4 horas)
- Agregar monitoring (4 horas)
- Optimizar queries (4 horas)
- **Total**: 12 horas de trabajo

### Semana 4: Escalado
- Database integration (8 horas)
- Queue system (8 horas)
- Full monitoring stack (8 horas)
- **Total**: 24 horas de trabajo

---

## ✅ CHECKLIST PRE-DEPLOYMENT

- [ ] Todas las APIs testeadas manualmente
- [ ] Los 12 deportes responden correctamente
- [ ] Caché funcionando
- [ ] Circuit breaker implementado
- [ ] Rate limiting activo
- [ ] Logs configurados
- [ ] Errores manejados gracefully
- [ ] Documentación completa
- [ ] Tests automatizados verdes
- [ ] Health checks implementados
- [ ] Monitoring configurado
- [ ] Alertas configuradas
- [ ] Backup plan documentado

---

**Última actualización**: 28 de Enero de 2026
