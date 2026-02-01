# 📊 MATRIZ FINAL: APIs de Odds Gratuitas - Comparativa Completa

**Última actualización**: 29 de Enero de 2026

---

## 🎯 TABLA PRINCIPAL: Todos los Criterios

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    APIS GRATUITAS CON MÚLTIPLES MERCADOS                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ API: The Odds API (FREE TIER) ──────────────────────────────────────────────┐
│                                                                               │
│  URL: https://www.the-odds-api.com/                                         │
│  Costo: $0 (500 requests/mes) | Pago: $9-499/mes                            │
│  Autenticación: Sí (API Key gratuita, registrarse en 2 min)                 │
│  Auth Complexity: Baja (solo copiar API key)                                 │
│                                                                               │
│  ✅ DISPONIBLE:                  │  ❌ NO DISPONIBLE:                       │
│  ├─ h2h/Moneyline             │  ├─ Player props                          │
│  ├─ Spreads/Handicap          │  ├─ Correct score                         │
│  ├─ Totals (Over/Under)       │  ├─ Quarter/Half bets                     │
│  ├─ Múltiples bookmakers      │  ├─ In-play betting                       │
│  └─ 9 deportes (ver tabla)    │  └─ Futures                               │
│                                                                               │
│  DEPORTES (9 de 12):             RATE LIMIT:                               │
│  ✅ Soccer (20+ ligas)           │ • 1 request/segundo                     │
│  ✅ NFL (American Football)      │ • 500 requests/mes                      │
│  ✅ NBA (Basketball)            │ • ~16 requests/día                      │
│  ✅ MLB (Baseball)              │ • ⚠️ MUY LIMITADO                       │
│  ✅ NHL (Hockey)                │                                          │
│  ✅ Rugby Union                 │ ESTABILIDAD:                            │
│  ✅ AFL (Australian Football)   │ ⭐⭐⭐⭐⭐ Oficial                      │
│  ✅ ATP/WTA (Tennis)            │                                          │
│  ✅ Formula 1                   │ DOCUMENTACIÓN:                          │
│  ❌ Handball                    │ ⭐⭐⭐⭐⭐ Excelente                    │
│  ❌ Volleyball                  │                                          │
│  ❌ MMA/UFC                     │ UPTIME:                                 │
│                                  │ ✅ 99.9%+                               │
│                                                                               │
│  BOOKMAKERS INCLUIDOS:                                                       │
│  └─ DraftKings, FanDuel, BetMGM, BetRivers, +20 más (varían por región)    │
│                                                                               │
│  CASOS DE USO IDEALES:                                                       │
│  ✅ Máxima confiabilidad                                                     │
│  ✅ Datos verificados de bookmakers                                          │
│  ✅ Integración en producción                                                │
│  ❌ Actualizaciones frecuentes                                               │
│  ❌ Alta concurrencia de requests                                            │
│                                                                               │
│  EJEMPLO DE USO:                                                             │
│  curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds\              │
│    ?api_key=YOUR_KEY&markets=h2h,spreads,totals&regions=us"                │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ API: SofaScore API ─────────────────────────────────────────────────────────┐
│                                                                               │
│  URL: https://www.sofascore.com/api/v1/                                     │
│  Costo: $0 (completamente gratis)                                            │
│  Autenticación: No requerida                                                 │
│  Auth Complexity: Nula (copiar URL, listo)                                   │
│                                                                               │
│  ✅ DISPONIBLE:                  │  ❌ NO DISPONIBLE:                       │
│  ├─ h2h/Moneyline             │  ├─ Player props (parcial)               │
│  ├─ Spreads/Handicap          │  ├─ Correct score (inconsistente)      │
│  ├─ Totals (Over/Under)       │  ├─ Futures                             │
│  ├─ Múltiples bookmakers      │  └─ In-play oficial                     │
│  └─ 12 deportes COMPLETOS ✅  │                                          │
│                                                                               │
│  DEPORTES (12 de 12) ✅:          RATE LIMIT:                               │
│  ✅ Soccer (todas las ligas)     │ • Sin documentación restrictiva         │
│  ✅ NFL                          │ • Típicamente: 1-2 req/segundo         │
│  ✅ NBA                          │ • ✅ ILIMITADO (prakticamente)         │
│  ✅ MLB                          │                                          │
│  ✅ NHL                          │ ESTABILIDAD:                            │
│  ✅ Rugby                        │ ⭐⭐⭐⭐ Muy buena (usado por          │
│  ✅ Handball                     │          miles de apps)                 │
│  ✅ Volleyball                   │                                          │
│  ✅ Tennis                       │ DOCUMENTACIÓN:                          │
│  ✅ MMA/UFC                      │ ⭐⭐⭐ Media (reverse-engineered)      │
│  ✅ Australian Football          │                                          │
│  ✅ Formula 1                    │ UPTIME:                                 │
│                                  │ ✅ 99.8%+ (empírico)                   │
│                                                                               │
│  BOOKMAKERS INCLUIDOS:                                                       │
│  └─ Bet365, William Hill, Pinnacle, Unibet, MarathonBet, +20 más           │
│                                                                               │
│  CASOS DE USO IDEALES:                                                       │
│  ✅ Cobertura de 12 deportes                                                 │
│  ✅ Sin límite de requests                                                   │
│  ✅ Prototipado rápido                                                       │
│  ✅ Máxima disponibilidad                                                    │
│  ❌ Máxima confiabilidad (API no oficial)                                    │
│  ❌ Soporte SLA garantizado                                                  │
│                                                                               │
│  EJEMPLO DE USO:                                                             │
│  curl "https://www.sofascore.com/api/v1/sport/football/events/today"       │
│                                                                               │
│  ENTONCES:                                                                    │
│  curl "https://www.sofascore.com/api/v1/event/{eventId}/odds"              │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ API: ESPN (Bonus - solo scores, no odds) ───────────────────────────────────┐
│                                                                               │
│  URL: https://site.api.espn.com/                                            │
│  Costo: $0                                                                    │
│  Autenticación: No                                                            │
│                                                                               │
│  ✅ DISPONIBLE:        │  ❌ NO DISPONIBLE:                                 │
│  ├─ Eventos/Scores   │  ├─ Cualquier odd/mercado                        │
│  ├─ Estadísticas     │  ├─ Información de apuestas                       │
│  └─ Standings        │  └─ Datos de predicción                           │
│                                                                               │
│  DEPORTES: 6 de 12 (Soccer, Baseball, NFL, Basketball, Hockey, Tennis)     │
│  RATE LIMIT: Muy generoso                                                    │
│  ESTABILIDAD: ⭐⭐⭐⭐⭐ Oficial ESPN                                       │
│                                                                               │
│  UTILIDAD:                                                                    │
│  Complementario a APIs de odds para scores EN VIVO                          │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ API: TheSportsDB (Bonus - solo eventos históricos) ────────────────────────┐
│                                                                               │
│  URL: https://www.thesportsdb.com/api/v1/json/1/                           │
│  Costo: $0                                                                    │
│  Autenticación: No                                                            │
│                                                                               │
│  ✅ DISPONIBLE:        │  ❌ NO DISPONIBLE:                                 │
│  ├─ Eventos/Scores   │  ├─ Cualquier odd/mercado                        │
│  ├─ Equipos          │  ├─ Datos en vivo                                 │
│  └─ Estadísticas     │  └─ Información actual                            │
│                                                                               │
│  DEPORTES: 12 de 12 ✅                                                       │
│  RATE LIMIT: Generoso                                                        │
│  ESTABILIDAD: ⭐⭐⭐⭐⭐                                                     │
│                                                                               │
│  UTILIDAD:                                                                    │
│  Datos históricos, equipos, estadísticas. No para apuestas.                │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔥 DECISIÓN RÁPIDA: Cuál Usar

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SI NECESITAS...                           → USA...                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Spreads + Totals + h2h (h2h + spreads    → The Odds API O SofaScore    │
│                                                                          │
│ Máxima confiabilidad                     → The Odds API                │
│                                                                          │
│ Máxima cobertura (12 deportes)           → SofaScore                   │
│                                                                          │
│ Sin registrarse (0 configuración)        → SofaScore                   │
│                                                                          │
│ Ilimitado de requests                    → SofaScore                   │
│                                                                          │
│ Datos verificados de bookmakers          → The Odds API                │
│                                                                          │
│ Stack completo (backup + verificación)   → SofaScore + The Odds API    │
│                                                                          │
│ Player props O Correct score completo    ❌ NO EXISTE GRATIS           │
│                                            (pagar $9+ al mes)           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 COBERTURA DE DEPORTES

```
┌──────────────────┬──────────────┬──────────────┬──────────┬─────────────┐
│ Deporte          │ The Odds API │ SofaScore    │ ESPN     │ TheSportsDB │
├──────────────────┼──────────────┼──────────────┼──────────┼─────────────┤
│ Soccer           │ ✅           │ ✅           │ ✅       │ ✅          │
│ NFL              │ ✅           │ ✅           │ ✅       │ ✅          │
│ NBA              │ ✅           │ ✅           │ ✅       │ ✅          │
│ MLB              │ ✅           │ ✅           │ ✅       │ ✅          │
│ NHL              │ ✅           │ ✅           │ ✅       │ ✅          │
│ Rugby            │ ✅           │ ✅           │ ❌       │ ✅          │
│ Tennis           │ ✅           │ ✅           │ ✅       │ ✅          │
│ AFL              │ ✅           │ ✅           │ ❌       │ ✅          │
│ F1               │ ✅           │ ✅           │ ❌       │ ✅          │
│ Handball         │ ❌           │ ✅           │ ❌       │ ✅          │
│ Volleyball       │ ❌           │ ✅           │ ❌       │ ✅          │
│ MMA/UFC          │ ❌           │ ✅           │ ❌       │ ✅          │
├──────────────────┼──────────────┼──────────────┼──────────┼─────────────┤
│ TOTAL            │ 9/12 ✅      │ 12/12 ✅✅   │ 6/12 ⚠️  │ 12/12 ✅✅   │
└──────────────────┴──────────────┴──────────────┴──────────┴─────────────┘
```

---

## 💰 ANÁLISIS DE COSTOS

### Escenario 1: "Solo quiero h2h y spreads, no muchas consultas"
```
The Odds API FREE (500 req/mes)
├─ Costo: $0
├─ Covers: 9 deportes
├─ Mercados: h2h ✅, spreads ✅, totals ✅
└─ Ideal para: Aplicaciones con bajo volumen
```

### Escenario 2: "Quiero máxima cobertura (12 deportes), ilimitado"
```
SofaScore
├─ Costo: $0
├─ Covers: 12 deportes
├─ Mercados: h2h ✅, spreads ✅, totals ✅
└─ Ideal para: High-volume applications, startups
```

### Escenario 3: "Quiero lo mejor de ambos mundos"
```
SofaScore (primary) + The Odds API (backup/verification)
├─ Costo: $0
├─ Covers: 12 deportes
├─ Mercados: h2h ✅, spreads ✅, totals ✅
├─ Rate limit: Ilimitado + 500/mes
└─ Ideal para: Producción crítica con redundancia
```

### Escenario 4: "Necesito player props o correct score exacto"
```
The Odds API PAID ($9-99/mes) O Sportradar ($1,000+/mes)
├─ Costo: $9+ al mes mínimo
├─ Covers: Más mercados
└─ Ideal para: Aplicaciones de apuestas profesionales
```

---

## ⚠️ LIMITACIONES POR TIPO DE DATO

```
┌────────────────────────────────────────────────────────────────────┐
│ TIPO DE DATO / MERCADO                          OPCIÓN GRATUITA    │
├────────────────────────────────────────────────────────────────────┤
│ h2h (Moneyline)                                 ✅ The Odds + SS   │
│ Spreads/Handicaps                               ✅ The Odds + SS   │
│ Totals (Over/Under)                             ✅ The Odds + SS   │
│ Parlay/Combination                              ✅ Parcialmente SS  │
│ Player Props                                     ❌ NO HAY           │
│ Correct Score Exacto                            ⚠️ SS (inconsist.) │
│ Quarter/Half Props                              ❌ NO HAY           │
│ Live In-Play Betting                            ✅ SS parcial       │
│ Futures (Win tournament, etc)                   ❌ NO HAY           │
│ Alternative Markets (Goal scorer, etc)          ⚠️ SS parcial       │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA

### Nivel 1: Prototipo Rápido (15 minutos)
```python
# SofaScore directo, sin configuración
import requests

response = requests.get(
    "https://www.sofascore.com/api/v1/sport/football/events/today"
)
events = response.json()['events']
```

### Nivel 2: Producción Confiable (1 hora)
```python
# The Odds API + SofaScore backup
# Ver: FREE_ODDS_IMPLEMENTATION_GUIDE.md
```

### Nivel 3: Enterprise Ready (4 horas)
```python
# Stack completo con retry logic, caching, fallback
# Ver: FREE_ODDS_IMPLEMENTATION_GUIDE.md sección 4
```

---

## 📞 SOPORTE Y DOCUMENTACIÓN

| API | Docs | Community | SLA |
|-----|------|-----------|-----|
| **The Odds API** | https://the-odds-api.com/docs | Email support | No SLA (free) |
| **SofaScore** | Reverse-engineered | Reddit/GitHub | No official |
| **ESPN** | site.api.espn.com | ESPN support | No SLA |
| **TheSportsDB** | thesportsdb.com/api | Community | No official |

---

## ✅ CHECKLIST: Antes de Implementar

- [ ] Decidí si necesito múltiples deportes (12) o puedo con 9
- [ ] Decidí si puedo vivir con 16 requests/día (The Odds API) o necesito ilimitado
- [ ] Decidí si me importa máxima confiabilidad (The Odds) vs máxima cobertura (SS)
- [ ] Leí la documentación específica de la API elegida
- [ ] Probé al menos un request manualmente (curl)
- [ ] Consideré usar SofaScore + The Odds API como backup

---

## 🎓 CONCLUSIÓN FINAL

✅ **EXISTEN opciones gratuitas con múltiples mercados (h2h + spreads + totals)**

**Mejor opción para la mayoría:** SofaScore (gratis, ilimitado, 12 deportes)

**Mejor opción para confiabilidad:** The Odds API (gratis, oficial, pero 16 req/día)

**Mejor opción para producción:** Ambas juntas (redundancia)

**Costo total:** $0 ✅

