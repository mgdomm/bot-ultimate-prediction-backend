# 🎯 MATRIZ COMPARATIVA FINAL: APIs de Odds Deportivas GRATUITAS

**Fecha**: 28 de Enero de 2026  
**Criterio**: Solo APIs 100% GRATUITAS sin planes pagos obligatorios

---

## 📈 COMPARATIVA COMPLETA

### **TheSportsDB** ⭐⭐⭐⭐⭐
| Aspecto | Detalles |
|--------|----------|
| **Costo** | $0 - 100% Gratuito |
| **Autenticación** | ❌ No requiere |
| **Registro** | No necesario |
| **Rate Limit** | ✅ Generoso (sin documentación restrictiva) |
| **HTTPS** | ✅ Sí |
| **CORS** | ✅ Soportado |
| **Respuesta** | JSON |
| **Uptime** | Muy bueno |
| **Documentación** | Excelente |
| **Soporte** | Comunidad activa |

**Deportes Cubiertos**:
```
✅ Soccer/Football - Excelente cobertura mundial
✅ Rugby - Six Nations, Rugby Championship, etc.
✅ American Football (NFL) - Excelente
✅ Basketball (NBA, FIBA, EuroLeague) - Excelente
✅ Hockey (NHL, KHL) - Excelente
✅ Handball - Champions League, etc.
✅ Volleyball - World Cups, Leagues
✅ Australian Football (AFL) - Excelente
✅ Tennis (ATP, WTA, Grand Slams) - Excelente
✅ Baseball (MLB, Minor League) - Excelente
✅ Formula 1 - Excelente
✅ MMA/UFC - Excelente
```

**Endpoints Disponibles**:
```
/eventslast.php?id={league_id}       - Últimos eventos
/eventsday.php?id={league_id}&d=DATE  - Eventos por fecha
/eventsbet.php?id={league_id}         - Eventos con apuestas
/eventinfo.php?id={event_id}          - Detalle de evento
```

**Ejemplo de Respuesta**:
```json
{
  "results": [
    {
      "idEvent": "123456",
      "strEvent": "Manchester United vs Liverpool",
      "dateEvent": "2026-01-28",
      "strHomeTeam": "Manchester United",
      "strAwayTeam": "Liverpool",
      "intHomeScore": 2,
      "intAwayScore": 1,
      "strStatus": "Match Finished"
    }
  ]
}
```

**Ventajas**:
- ✅ Completamente gratis
- ✅ Sin autenticación
- ✅ Cobertura muy amplia (12 deportes)
- ✅ Datos históricos disponibles
- ✅ Actualizaciones regulares
- ✅ API estable

**Desventajas**:
- ❌ No incluye odds de apuestas (solo eventos)
- ❌ Actualizaciones pueden ser lentas en eventos en vivo
- ⚠️ Sin soporte oficial de SLA

---

### **SofaScore API** ⭐⭐⭐⭐⭐
| Aspecto | Detalles |
|--------|----------|
| **Costo** | $0 - 100% Gratuito |
| **Autenticación** | ❌ No requiere |
| **Registro** | No necesario |
| **Rate Limit** | ✅ Generoso |
| **HTTPS** | ✅ Sí |
| **CORS** | ✅ Soportado |
| **Respuesta** | JSON |
| **Uptime** | Excelente |
| **Documentación** | Buena (reverse-engineered) |
| **Soporte** | No oficial pero comunidad activa |

**Deportes Cubiertos**:
```
✅ Soccer/Football - Cobertura mundial completa
✅ Tennis (ATP, WTA, Grand Slams) - Excelente
✅ Basketball (NBA, FIBA, EuroLeague) - Excelente
✅ Hockey (NHL, KHL) - Bueno
✅ Baseball (MLB) - Bueno
✅ MMA/UFC - Bueno
✅ Rugby - Bueno
✅ American Football (NFL) - Bueno
✅ Volleyball - Disponible
✅ Formula 1 - Disponible
✅ Handball - Disponible
✅ Australian Football (AFL) - Disponible
```

**Endpoints Disponibles**:
```
/sport/{sport}/events/today           - Eventos de hoy
/event/{eventId}/odds                 - Odds de evento
/tournament/{tournamentId}/season/{seasonId}/events/today
/team/{teamId}/events/last            - Eventos del equipo
/player/{playerId}                    - Info del jugador
```

**Ejemplo de Respuesta - Eventos**:
```json
{
  "events": [
    {
      "id": 123456,
      "slug": "manchester-united-liverpool",
      "status": {
        "type": "finished",
        "description": "Finished"
      },
      "homeTeam": {
        "id": 1,
        "name": "Manchester United"
      },
      "awayTeam": {
        "id": 2,
        "name": "Liverpool"
      },
      "homeScore": {
        "current": 2
      },
      "awayScore": {
        "current": 1
      }
    }
  ]
}
```

**Ejemplo de Respuesta - Odds**:
```json
{
  "markets": [
    {
      "marketName": "1X2",
      "groups": [
        {
          "type": "1",
          "odds": [
            {
              "name": "1",
              "odd": 1.95
            },
            {
              "name": "X",
              "odd": 3.40
            },
            {
              "name": "2",
              "odd": 4.20
            }
          ]
        }
      ]
    }
  ]
}
```

**Ventajas**:
- ✅ Completamente gratis
- ✅ Sin autenticación
- ✅ **Incluye odds de apuestas en vivo**
- ✅ Datos actualizados en tiempo real
- ✅ Cobertura muy amplia
- ✅ Respuestas rápidas

**Desventajas**:
- ⚠️ API no oficial (reverse-engineered)
- ⚠️ Podría cambiar sin aviso
- ❌ Sin SLA oficial

---

### **ESPN API** ⭐⭐⭐⭐
| Aspecto | Detalles |
|--------|----------|
| **Costo** | $0 - 100% Gratuito |
| **Autenticación** | ❌ No requiere |
| **Registro** | No necesario |
| **Rate Limit** | ✅ Muy generoso |
| **HTTPS** | ✅ Sí |
| **CORS** | ✅ Soportado |
| **Respuesta** | JSON |
| **Uptime** | Excelente (ESPN.com) |
| **Documentación** | Documentación pública de ESPN |
| **Soporte** | ESPN (oficial) |

**Deportes Cubiertos**:
```
✅ Soccer/Football - Bueno (Internacional, MLS)
✅ Baseball (MLB) - Excelente
✅ American Football (NFL) - Excelente
✅ Basketball (NBA) - Excelente
✅ Hockey (NHL) - Bueno
✅ Tennis (ATP, WTA) - Bueno
⚠️ Otros deportes - Limitado según cobertura ESPN
```

**Endpoints Disponibles**:
```
/sports/soccer                        - Soccer eventos
/sports/baseball/mlb                  - MLB scores
/sports/football/nfl                  - NFL scores
/sports/basketball/nba                - NBA scores
/sports/hockey/nhl                    - NHL scores
/sports/tennis/atp                    - ATP eventos
/sports/tennis/wta                    - WTA eventos
```

**Ejemplo de Respuesta**:
```json
{
  "events": [
    {
      "id": "123456",
      "name": "Manchester United at Liverpool",
      "date": "2026-01-28T20:00Z",
      "status": "Final",
      "competitions": [
        {
          "competitors": [
            {
              "id": "1",
              "name": "Manchester United",
              "score": 2
            },
            {
              "id": "2",
              "name": "Liverpool",
              "score": 1
            }
          ]
        }
      ]
    }
  ]
}
```

**Ventajas**:
- ✅ Completamente gratis
- ✅ Sin autenticación
- ✅ Autoridad global (ESPN.com)
- ✅ Datos confiables y verificados
- ✅ Actualización muy rápida
- ✅ Endpoints públicos oficiales

**Desventajas**:
- ❌ No incluye odds de apuestas
- ⚠️ Cobertura limitada a deportes de ESPN
- ⚠️ Sin SLA publicado

---

### **The Odds API (Tier Gratis)** ⭐⭐
| Aspecto | Detalles |
|--------|----------|
| **Costo** | $0 (500 requests/mes) - Después $39/mes |
| **Autenticación** | ✅ API Key (gratis) |
| **Registro** | ✅ Necesario |
| **Rate Limit** | ⚠️ 1 request/segundo |
| **HTTPS** | ✅ Sí |
| **CORS** | ✅ Soportado |
| **Respuesta** | JSON |
| **Uptime** | Excelente |
| **Documentación** | Excelente |
| **Soporte** | Oficial muy bueno |

**Deportes Cubiertos con Odds**:
```
✅ NFL
✅ Basketball (NBA)
✅ Hockey (NHL)
✅ Baseball (MLB)
✅ Tennis
✅ Soccer (fútbol)
✅ MMA/UFC
✅ Muchos otros (20+ deportes)
```

**Endpoints Disponibles**:
```
/v4/sports                            - Deportes disponibles
/v4/sports/{sportKey}/odds            - Odds de sport
/v4/sports/{sportKey}/events          - Eventos sin odds
/v4/sports/{sportKey}/scores          - Scores recientes
```

**Ejemplo de Respuesta**:
```json
{
  "id": "123456",
  "sport_key": "football_nfl",
  "sport_title": "NFL",
  "commence_time": "2026-01-28T20:00Z",
  "home_team": "New England Patriots",
  "away_team": "Miami Dolphins",
  "bookmakers": [
    {
      "key": "draftkings",
      "title": "DraftKings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {
              "name": "New England Patriots",
              "price": 1.95
            },
            {
              "name": "Miami Dolphins",
              "price": 2.05
            }
          ]
        }
      ]
    }
  ]
}
```

**Ventajas**:
- ✅ Completamente gratis (500 req/mes)
- ✅ API oficial
- ✅ Datos de múltiples librerías de apuestas
- ✅ Documentación excelente
- ✅ Soporte oficial muy bueno
- ✅ Datos muy precisos

**Desventajas**:
- ⚠️ **Límite muy restrictivo**: 500 req/mes = ~17 req/día
- ⚠️ Requiere API Key
- ❌ Insuficiente para actualizaciones frecuentes sin pagar
- ⚠️ Después requiere pago para más acceso

**Cálculo de Suficiencia**:
```
500 requests/mes ÷ 30 días = 16.67 requests/día

Caso 1: Actualizar 1 deporte cada 3 horas
Requests/día = 8 (✅ VIABLE)

Caso 2: Actualizar 2 deportes cada 3 horas
Requests/día = 16 (✅ VIABLE pero al límite)

Caso 3: Actualizar 5 deportes cada 3 horas
Requests/día = 40 (❌ INSUFICIENTE)
```

---

## 🏆 RECOMENDACIÓN FINAL

### **OPCIÓN RECOMENDADA (Stack Óptimo)**

Para cobertura **100% gratuita** de los 12 deportes solicitados:

```
┌─────────────────────────────────────────────────────────────┐
│  STACK RECOMENDADO: Combinación de 3 APIs Gratuitas        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣  TheSportsDB (Primario)                                │
│     • Costo: $0                                            │
│     • Deportes: 12 (todos cubiertos)                       │
│     • Rate Limit: Generoso                                 │
│     • Uso: Eventos generales, historiales                 │
│                                                             │
│  2️⃣  SofaScore (Secundario - MEJOR con Odds)              │
│     • Costo: $0                                            │
│     • Deportes: 12 (todos cubiertos)                       │
│     • Rate Limit: Generoso                                 │
│     • Uso: Eventos en vivo + Odds en vivo                 │
│                                                             │
│  3️⃣  ESPN (Tertiary - Validación)                         │
│     • Costo: $0                                            │
│     • Deportes: 6 (cobertura limitada)                     │
│     • Rate Limit: Muy generoso                             │
│     • Uso: Validación de scores, datos adicionales        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

COSTO TOTAL: $0
RATE LIMIT: No restrictivos
AUTENTICACIÓN: No requiere
COBERTURA: 100% de 12 deportes
```

---

## 📊 TABLA DEFINITIVA DE DECISIÓN

| Necesidad | Recomendación | Por Qué |
|-----------|---------------|--------|
| **Eventos Generales** | TheSportsDB | Cobertura más amplia, sin límites |
| **Eventos en Vivo** | SofaScore | Actualizaciones en tiempo real |
| **Odds en Vivo** | SofaScore | La única con odds sin autenticación |
| **Scores Verificados** | ESPN | Datos oficiales confiables |
| **Cobertura Total 12 Deportes** | TheSportsDB + SofaScore | Redundancia y cobertura completa |
| **Si presupuesto permite ($39/mes)** | The Odds API | Odds más confiables, múltiples librerías |

---

## ✅ VERIFICACIÓN FINAL

### **Cada Deporte - Mejor Fuente Recomendada**

| Deporte | Mejor Fuente | Alternativas | Odds |
|---------|--------------|--------------|------|
| **Soccer** | SofaScore | TheSportsDB, ESPN | ✅ SofaScore |
| **Rugby** | TheSportsDB | SofaScore | ❌ No en APIs gratuitas |
| **NFL** | SofaScore | ESPN, TheSportsDB | ✅ SofaScore |
| **Basketball** | SofaScore | ESPN, TheSportsDB | ✅ SofaScore |
| **Hockey** | SofaScore | ESPN, TheSportsDB | ✅ SofaScore |
| **Handball** | TheSportsDB | SofaScore | ❌ No en APIs gratuitas |
| **Volleyball** | TheSportsDB | SofaScore | ❌ No en APIs gratuitas |
| **AFL** | TheSportsDB | SofaScore | ❌ No en APIs gratuitas |
| **Tennis** | SofaScore | ESPN, TheSportsDB | ✅ SofaScore |
| **Baseball** | SofaScore | ESPN, TheSportsDB | ✅ SofaScore |
| **F1** | TheSportsDB | SofaScore | ❌ No en APIs gratuitas |
| **MMA/UFC** | SofaScore | TheSportsDB | ✅ SofaScore |

---

## 🎬 IMPLEMENTACIÓN RECOMENDADA

### **Paso 1: Configuración Base**
```python
# Todas gratis, sin autenticación
services = {
    'primary': TheSportsDBService,      # Eventos generales
    'secondary': SofaScoreService,      # Eventos + odds en vivo
    'tertiary': ESPNService,            # Validación
}

# COSTO TOTAL: $0
# TIME TO MARKET: 1-2 horas
```

### **Paso 2: Agregar Odds (Opcional - Requiere Pago)**
```python
# Si decides pagar $39/mes después
services['odds_premium'] = TheOddsAPIService  # Múltiples librerías
```

---

## 🚀 CONCLUSIÓN FINAL

### **¿Son suficientes las APIs gratuitas?**

| Caso de Uso | Respuesta | Explicación |
|-------------|-----------|-------------|
| **Aplicación personal/educativa** | ✅ Sí | Más que suficiente |
| **App con usuarios ocasionales** | ✅ Sí | Rate limits generosos |
| **Aplicación comercial baja escala** | ⚠️ Sí (con cuidado) | Implementar cache |
| **Aplicación comercial alta escala** | ❌ No | Necesita planes pagos |

### **Stack Recomendado Final**

```
TheSportsDB (100% gratis) 
    ↓
SofaScore (100% gratis, incluye odds)
    ↓
ESPN (100% gratis, validación)
    ↓
TOTAL COSTO: $0
TOTAL COBERTURA: 100% de 12 deportes
TIME TO MARKET: 2-3 horas
```

---

**Última actualización**: 28 de Enero de 2026  
**Investigación completada**: Enero 2026
