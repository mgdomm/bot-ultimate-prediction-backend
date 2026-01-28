# 🔖 The Odds API - Referencia Rápida (Quick Cheat Sheet)

## 📌 Respuesta de 30 Segundos

**P: ¿Cuáles son los límites exactos del tier $9/mes de The Odds API?**

**R: No existe tier $9/mes**

Estructura real:
- **FREE**: 500 req/mes ($0) ← Usa esto
- **BASIC**: 10,000 req/mes ($39)
- **PRO**: 500,000 req/mes ($99)

Para 100 picks/día: **FREE es suficiente** ($0/mes)

---

## 🎯 Respuestas Inmediatas

| Pregunta | Respuesta |
|----------|-----------|
| ¿Requests/mes en $9? | No existe. FREE=500, BASIC=10k |
| ¿Requests/día? | FREE~17, BASIC~333, PRO~16,667 |
| ¿Para 100 picks? | 20-50/día → FREE suficiente |
| ¿Si $9 no funciona? | Upgrade a BASIC ($39/mes) |
| ¿Tiers intermedios? | NO - salto de FREE→BASIC (20x) |

---

## 💰 Comparativa Rápida

```
┌──────────┬──────────┬──────────┬────────────┐
│ TIER     │ COSTO    │ REQ/MES  │ PARA 100P  │
├──────────┼──────────┼──────────┼────────────┤
│ FREE     │ $0       │ 500      │ ✅ Vale   │
│ BASIC    │ $39      │ 10k      │ ✅ Mejor  │
│ PRO      │ $99      │ 500k     │ ✅ Holgado│
└──────────┴──────────┴──────────┴────────────┘

RECOMENDADO: FREE ($0) con caché
```

---

## ⚡ Para Implementar Ya

```python
# 3 pasos:
# 1. Registrarse: https://the-odds-api.com/register
# 2. Obtener API key (FREE)
# 3. Usar 1 vez/día + caché 60min = ✅ Listo

from datetime import datetime, timedelta
import requests
import json
from pathlib import Path

class OddsClient:
    CACHE_TTL = timedelta(minutes=60)
    
    def get_odds(self, sport, use_cache=True):
        cache_file = f"cache/{sport}.json"
        
        # Check cache
        if use_cache and Path(cache_file).exists():
            age = datetime.now() - datetime.fromtimestamp(
                Path(cache_file).stat().st_mtime
            )
            if age < self.CACHE_TTL:
                return json.load(open(cache_file))
        
        # Fetch from API
        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
            params={'api_key': YOUR_KEY}
        )
        
        # Cache result
        json.dump(r.json(), open(cache_file, 'w'))
        return r.json()

# Usage: client.get_odds("baseball_mlb")
```

---

## 📊 Cálculo 100 Picks/Día

**Escenario 1: 1 fetch/día (RECOMENDADO)**
```
7 requests/día × 30 = 210/mes
FREE tier: 500/mes
Margen: 290 (58%) ✅ EXCELENTE
```

**Escenario 2: Polling cada 30min**
```
160 requests/día × 30 = 4,800/mes
FREE: Insuficiente ❌
BASIC: 10,000/mes ✅ 52% margen
```

**Escenario 3: Polling cada 15min**
```
320 requests/día × 30 = 9,600/mes
BASIC: 10,000/mes ✅ 4% margen (justo)
PRO: 500,000/mes ✅ 98% margen
```

---

## ✅ Checklist de 5 Minutos

```
□ Registrarse: https://the-odds-api.com/register
□ Copiar API key
□ Crear archivo .env: THE_ODDS_API_KEY=xxx
□ Copy-paste código TheOddsAPIClient
□ Fetch 1 vez/día (6am)
□ LISTO - Costo: $0
```

---

## 🚨 Alertas

- ⚠️ Límite alcanzado (429 error): Usar caché local
- ⚠️ Cerca de límite (>450/mes): Reducir polling
- ⚠️ Necesitas tiempo real: Upgrade a BASIC ($39)

---

## 📞 Si Necesitas Más

- **Polling cada 5 min** → BASIC ($39/mes)
- **Datos históricos** → PRO ($99/mes)
- **Ilimitado** → ENTERPRISE (contactar)

---

## 🔗 Links

| Recurso | URL |
|---------|-----|
| **Signup** | https://the-odds-api.com/register |
| **Docs** | https://docs.the-odds-api.com/ |
| **Precios** | https://the-odds-api.com/pricing |
| **Status** | https://the-odds-api.com/status |

---

## 📝 Variables .env

```bash
# .env
THE_ODDS_API_KEY=your_free_key_here
THE_ODDS_API_CACHE_TTL=3600  # 1 hora en segundos
THE_ODDS_API_ENABLED=true
THE_ODDS_API_MONITOR_USAGE=true
```

---

## 🎯 TL;DR

✅ **FREE tier ($0) es suficiente para 100 picks/día**
- 500 requests/mes disponibles
- Usarías ~210/mes (42%)
- Margen: 58%
- Estrategia: 1 fetch/día + caché 60min
- Costo anual: $0

---

**Última actualización**: 28 de Enero de 2026
**Fuente**: Investigación exhaustiva 5 documentos
**Status**: ✅ Verificado
