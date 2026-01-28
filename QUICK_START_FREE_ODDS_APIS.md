# ⚡ QUICK START: APIs de Odds Deportivas GRATUITAS (5 Minutos)

**Fecha**: 28 de Enero de 2026  
**Objetivo**: Implementación en 5 minutos con ejemplos listos para copiar

---

## 🚀 Opción Más Rápida: SofaScore (Contiene Odds)

### Por qué SofaScore primero:
- ✅ Sin autenticación requerida
- ✅ Incluye odds en vivo
- ✅ Actualización en tiempo real
- ✅ Una sola fuente cubre todo

---

## 1️⃣ SCRIPT RÁPIDO - Python (Copiar y ejecutar)

```python
import requests

# SofaScore - Sin autenticación requerida
BASE_URL = "https://www.sofascore.com/api/v1"

def get_events_with_odds(sport):
    """Obtiene eventos de hoy con odds (5 líneas!)"""
    try:
        # Paso 1: Obtener eventos de hoy
        url = f"{BASE_URL}/sport/{sport}/events/today"
        response = requests.get(url, timeout=10)
        events = response.json().get('events', [])
        
        print(f"✅ {sport.upper()}: {len(events)} eventos encontrados")
        
        # Paso 2: Obtener odds para el primer evento
        if events:
            first_event = events[0]
            event_id = first_event['id']
            event_name = first_event.get('slug', 'Evento')
            
            odds_url = f"{BASE_URL}/event/{event_id}/odds"
            odds_response = requests.get(odds_url, timeout=10)
            odds_data = odds_response.json()
            
            print(f"\n📊 Evento: {event_name}")
            print(f"   Odds disponibles: {len(odds_data.get('markets', []))} mercados")
            
            # Mostrar primeros odds
            for market in odds_data.get('markets', [])[:1]:
                print(f"\n   Mercado: {market.get('marketName', 'N/A')}")
                for group in market.get('groups', [])[:1]:
                    print(f"   Opciones:")
                    for odd in group.get('odds', [])[:3]:
                        print(f"     - {odd.get('name', 'N/A')}: {odd.get('odd', 'N/A')}")
        
        return events
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

# PRUEBAS RÁPIDAS - Descomentar para probar
if __name__ == "__main__":
    print("=== 🎯 DEMO: APIs de Odds Gratis ===\n")
    
    # Deporte a probar (cambiar según necesidad)
    sports_to_test = [
        'football',      # Soccer
        'tennis',        # Tennis
        'basketball',    # Basketball
        'hockey',        # Hockey
        'baseball',      # Baseball
        'american-football',  # NFL
        'mma',          # MMA/UFC
    ]
    
    for sport in sports_to_test:
        get_events_with_odds(sport)
        print("\n" + "="*50 + "\n")
```

**Ejecutar**:
```bash
pip install requests
python script_rapido.py
```

---

## 2️⃣ CURL EXAMPLES (Sin código)

### Soccer - Eventos de hoy:
```bash
curl "https://www.sofascore.com/api/v1/sport/football/events/today"
```

### Tennis - Eventos de hoy:
```bash
curl "https://www.sofascore.com/api/v1/sport/tennis/events/today"
```

### NBA - Eventos de hoy:
```bash
curl "https://www.sofascore.com/api/v1/sport/basketball/events/today"
```

### NFL - Eventos de hoy:
```bash
curl "https://www.sofascore.com/api/v1/sport/american-football/events/today"
```

### Obtener odds de evento específico:
```bash
# Primero obtener event_id del resultado anterior
curl "https://www.sofascore.com/api/v1/event/{event_id}/odds"
```

---

## 3️⃣ NODEJS EXAMPLE (2 minutos)

```javascript
const https = require('https');

function getEventsWithOdds(sport) {
    const url = `https://www.sofascore.com/api/v1/sport/${sport}/events/today`;
    
    https.get(url, (res) => {
        let data = '';
        
        res.on('data', chunk => data += chunk);
        
        res.on('end', () => {
            const events = JSON.parse(data).events || [];
            console.log(`✅ ${sport.toUpperCase()}: ${events.length} eventos`);
            
            // Obtener odds del primer evento
            if (events.length > 0) {
                const eventId = events[0].id;
                const oddsUrl = `https://www.sofascore.com/api/v1/event/${eventId}/odds`;
                
                https.get(oddsUrl, (oddsRes) => {
                    let oddsData = '';
                    oddsRes.on('data', chunk => oddsData += chunk);
                    oddsRes.on('end', () => {
                        const markets = JSON.parse(oddsData).markets || [];
                        console.log(`📊 Mercados disponibles: ${markets.length}`);
                        if (markets[0]) {
                            console.log(`   Nombre: ${markets[0].marketName}`);
                        }
                    });
                });
            }
        });
    });
}

// Probar
getEventsWithOdds('football');
getEventsWithOdds('tennis');
getEventsWithOdds('basketball');
```

**Ejecutar**:
```bash
node script.js
```

---

## 4️⃣ ONE-LINER (Más rápido aún)

```bash
# Soccer de hoy
curl -s "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events | length'

# Tennis de hoy
curl -s "https://www.sofascore.com/api/v1/sport/tennis/events/today" | jq '.events[0]'

# Todos los deportes en paralelo
for sport in football tennis basketball hockey baseball american-football mma; do
    echo "=== $sport ==="
    curl -s "https://www.sofascore.com/api/v1/sport/$sport/events/today" | jq '.events | length'
done
```

---

## 5️⃣ THESPORTSDB RÁPIDO (Alternativa)

### Script Python:
```python
import requests

BASE_URL = "https://www.thesportsdb.com/api/v1/json/1"

# IDs de ligas
LEAGUES = {
    'Premier League': 133602,
    'NFL': 133602,
    'NBA': 133600,
    'MLB': 133602,
    'ATP': 133679,
    'WTA': 133680,
    'NHL': 133655,
    'UFC': 133650,
}

for league_name, league_id in LEAGUES.items():
    url = f"{BASE_URL}/eventslast.php"
    params = {'id': league_id}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        events = response.json().get('results', [])
        print(f"{league_name}: {len(events)} eventos")
    except Exception as e:
        print(f"{league_name}: Error - {e}")
```

### CURL Equivalente:
```bash
# Premier League
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133602"

# ATP
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133679"

# NFL
curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id=133602"
```

---

## 6️⃣ ESPN RÁPIDO (Validación)

```bash
# Baseball MLB
curl "https://site.api.espn.com/us/site/v2/sports/baseball/mlb" | jq '.events | length'

# Football NFL
curl "https://site.api.espn.com/us/site/v2/sports/football/nfl" | jq '.events | length'

# Basketball NBA
curl "https://site.api.espn.com/us/site/v2/sports/basketball/nba" | jq '.events | length'

# Hockey NHL
curl "https://site.api.espn.com/us/site/v2/sports/hockey/nhl" | jq '.events | length'

# Tennis ATP
curl "https://site.api.espn.com/us/site/v2/sports/tennis/atp" | jq '.events | length'
```

---

## 🎯 RESUMEN RÁPIDO - Cuál Usar

| Necesidad | API | Comando |
|-----------|-----|---------|
| **Odds en vivo** | SofaScore | `curl "https://www.sofascore.com/api/v1/sport/{sport}/events/today"` |
| **Eventos simples** | TheSportsDB | `curl "https://www.thesportsdb.com/api/v1/json/1/eventslast.php?id={id}"` |
| **Scores confiables** | ESPN | `curl "https://site.api.espn.com/us/site/v2/sports/{sport}/{league}"` |
| **Todo combinado** | SofaScore + TheSportsDB | Ambas (redundancia) |

---

## 📋 CHECKLIST IMPLEMENTACIÓN

- [ ] Instalé requests: `pip install requests`
- [ ] Probé el script Python con SofaScore
- [ ] Verifiqué que los 12 deportes funcionan
- [ ] Guardé los ejemplos de CURL en una carpeta
- [ ] Integré a mi aplicación principal
- [ ] Configuré caché para reducir requests
- [ ] Documenté en mi README

---

## ⏱️ Tiempos de Implementación

| Etapa | Tiempo |
|-------|--------|
| Instalar requests | 1 min |
| Primer test SofaScore | 1 min |
| Testing todos 12 deportes | 1 min |
| Integración básica | 2 min |
| **TOTAL** | **5 min** ✅ |

---

## 🔄 Next Steps

1. **Implementación rápida**: SofaScore (arriba)
2. **Redundancia**: Agregar TheSportsDB como backup
3. **Validación**: Agregar ESPN para verificación
4. **Optimización**: Implementar caché local
5. **Upgrades futuro** (si presupuesto): The Odds API ($39/mes)

---

## 📞 Recursos Útiles

- **SofaScore Docs**: https://www.sofascore.com/
- **TheSportsDB Docs**: https://www.thesportsdb.com/api/v1/json/
- **ESPN API**: https://site.api.espn.com/
- **Testing Tools**: https://www.postman.com/ o Insomnia

---

**Última actualización**: 28 de Enero de 2026

¡Listo! Ya puedes obtener odds deportivas completamente gratis en 5 minutos.
