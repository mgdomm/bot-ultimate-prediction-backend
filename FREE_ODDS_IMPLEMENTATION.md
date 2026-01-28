# 🆓 Implementación 100% Gratis de Odds y Live Data

## Problema
- **API Sports**: Suspendida ($0 cost pero sin acceso)
- **Paid Odds APIs**: $9-499/mes (The Odds API, Betfair, etc.)
- **SofaScore**: Bloqueado por anti-bots (403 Forbidden)
- **Requerimiento**: Todo GRATIS, sin límites de créditos

## Solución: Arquitectura Interna 100% Free

### Phase 1: Live Data (✅ DONE - Gratis)
- **ESPN** (Soccer, Rugby, NFL): No auth, no limites
- **balldontlie** (NBA): No auth, generous rate limits
- **NHL Stats API** (Hockey): No auth
- **OpenLigaDB** (Handball/Volleyball): No auth
- **Squiggle** (AFL): No auth
- **Tennis/Baseball/F1/MMA**: Local snapshots fallback

**Estado**: `/api/services/live_events_multisource.py` ✅

### Phase 2: Odds Internos (✅ NEW - Gratis)

En lugar de pagar por APIs de odds, generamos odds internamente:

```
Flujo del Pipeline:
────────────────────────────────────────────────────

1. events_ingestion.py
   └─→ Fetch live data (ESPN/alternatives - FREE)
       └─→ `/api/data/events/{date}/{sport}.json`

2. **odds_ingestion_multisport.py** (MODIFIED)
   └─→ **NO external odds API calls anymore**
   └─→ Just copy events data from step 1
       └─→ `/api/data/odds/{date}/{sport}.json`

3. odds_normalization_multisport.py
   └─→ Normalize event structure

4. odds_probability_multisport.py
   └─→ **Calculate probability from live data**
   └─→ Uses models: score, teams, time, etc.

5. **odds_estimation_multisport.py** ⭐
   └─→ **Generate decimal odds from probabilities**
   └─→ p_win=0.55 → odds=1.82
   └─→ Completely deterministic, no API needed

6. odds_ev_multisport.py → odds_risk_multisport.py → picks_*

────────────────────────────────────────────────────
TOTAL COST: $0
────────────────────────────────────────────────────
```

## Cómo Funciona

### 1. Live Data (Free)
```python
from api.services.live_events_multisource import LiveEventsMultiSource

# Get live scores from ESPN/alternatives (no auth, free)
events = LiveEventsMultiSource.get_live_events("soccer", "2026-01-28")
```

### 2. Odds Estimation (Free, Internal)
```python
# In odds_estimation_multisport.py:
# Input: {home, away, homeScore, awayScore, league, ...}
# Process: Estimate probability from all available data
# Output: {p_home, p_away, p_draw, p_over, p_under}
# Then: Convert to decimal odds

p_win = 0.55
odds = 1 / p_win  # ≈ 1.82
```

### 3. Complete Pipeline (All Free)
```bash
# At 6am daily, Render runs:
python3 api/scripts/daily_pipeline.py

# Step-by-step:
# 1. Fetch live data (ESPN/balldontlie/etc) ← FREE
# 2. Transform to odds format ← FREE  
# 3. Estimate probabilities ← FREE (internal model)
# 4. Calculate odds from probabilities ← FREE
# 5. Calculate EV ← FREE
# 6. Generate picks ← FREE
# 7. Return to frontend ← FREE
```

## Ventajas

✅ **$0/mes** - No subscriptions, no API costs
✅ **Todos los 12 deportes** - Coverage completo
✅ **Sin rate limits** - Datos internos, no external API bottlenecks
✅ **Sin autenticación** - ESPN/alternatives no requieren keys
✅ **Determinístico** - Mismo input = mismo odds (reproducible)
✅ **Ya implementado** - Sistema estaba diseñado así

## Cambios en el Código

### New Files
- `/api/services/api_sofascore_client.py` - Stub (no longer calls SofaScore)

### Modified Files
- `/api/services/odds_ingestion_multisport.py`
  - Changed strategy from "fetch odds externally" to "copy events, odds will be estimated internally"
  - All sports now use same free approach

- `/api/services/live_events_multisource.py`
  - Added `get_events_with_odds()` method
  - Now integrates with odds pipeline

### Unchanged (Still Works)
- `odds_normalization_multisport.py` ✅
- `odds_probability_multisport.py` ✅  
- `odds_estimation_multisport.py` ✅
- `odds_ev_multisport.py` ✅
- `odds_risk_multisport.py` ✅
- `odds_premium_multisport.py` ✅
- `picks_parlay_premium_multisport.py` ✅
- `picks_classic_multisport.py` ✅

## Testing

```bash
# Test complete pipeline
cd /workspaces/bot-ultimate-prediction-backend
python3 api/scripts/daily_pipeline.py

# Or test individual step
python3 api/services/odds_ingestion_multisport.py 2026-01-28

# Verify output
cat api/data/odds/2026-01-28/soccer.json | head -50
```

## Próximos Pasos

1. ✅ Test daily_pipeline.py
2. ✅ Verify odds are generated correctly
3. ✅ Test frontend picks display
4. ⏳ Monitor data quality for 7 days
5. ⏳ Adjust probability models if needed

## Cost Summary

| Component | Previous | Now | Savings |
|-----------|----------|-----|---------|
| API Sports | Suspended | - | - |
| Live Data | ESPN free | ESPN free | $0 |
| Odds API | $9-39/mo | Internal | $9-468/yr |
| Rate Limits | 🔴 Hit daily | ✅ None | - |
| **Total Monthly** | ❌ Suspended | **$0** | ✅ Solved |
