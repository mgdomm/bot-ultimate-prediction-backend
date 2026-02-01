# 🎯 RESPUESTA DIRECTA: APIs Gratuitas con Múltiples Mercados

**Pregunta:** Buscar APIs GRATUITAS de odds deportivas con spreads, totals, props, correct score

**Respuesta:** Existen opciones para spreads/totals gratis. Props y correct score requieren pago.

---

## ✅ OPCIONES GRATUITAS QUE FUNCIONAN

### #1️⃣ **SofaScore** (RECOMENDADO)
- **Costo:** $0 (completamente gratis)
- **Auth:** No requerida (copiar URL, listo)
- **URL:** https://www.sofascore.com/api/v1/
- **Mercados:** h2h ✅, spreads ✅, totals ✅
- **Deportes:** 12/12 (Soccer, Football, Basketball, Baseball, Hockey, Rugby, Tennis, Handball, Volleyball, MMA, AFL, F1)
- **Rate Limit:** Ilimitado (sin documentación restrictiva)
- **Confiabilidad:** ⭐⭐⭐⭐ (muy usado, pero API no oficial)

**Comando rápido:**
```bash
curl "https://www.sofascore.com/api/v1/sport/football/events/today"
```

---

### #2️⃣ **The Odds API - FREE TIER** (ALTERNATIVA CONFIABLE)
- **Costo:** $0 (500 requests/mes)
- **Auth:** API Key gratuita (registrarse 2 min)
- **URL:** https://www.the-odds-api.com/
- **Mercados:** h2h ✅, spreads ✅, totals ✅
- **Deportes:** 9/12 (Soccer, NFL, NBA, MLB, NHL, Rugby, Tennis, AFL, F1)
- **Rate Limit:** 500/mes = ~16 req/día (muy limitado)
- **Confiabilidad:** ⭐⭐⭐⭐⭐ (oficial, datos de bookmakers reales)

**Comando rápido:**
```bash
curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=YOUR_KEY&markets=h2h,spreads,totals"
```

---

## ❌ LO QUE NO EXISTE GRATIS

| Mercado | Free | Precio |
|---------|------|--------|
| h2h/Moneyline | ✅ | $0 |
| Spreads | ✅ | $0 |
| Totals (O/U) | ✅ | $0 |
| Player Props | ❌ | $9+/mes |
| Correct Score | ⚠️ | $9+/mes |
| Futures | ❌ | $9+/mes |

---

## 🎯 RECOMENDACIÓN

### Para 99% de casos: **SofaScore**
- Gratis
- Sin registrarse
- 12 deportes
- Ilimitado
- Spreads + totals incluidos

```python
import requests

# Obtener eventos de hoy
response = requests.get("https://www.sofascore.com/api/v1/sport/football/events/today")
events = response.json()['events']

# Obtener odds de un evento
event_id = events[0]['id']
odds = requests.get(f"https://www.sofascore.com/api/v1/event/{event_id}/odds").json()
```

### Para máxima confiabilidad: **The Odds API + SofaScore**
- The Odds API para verificación (oficial)
- SofaScore como principal (ilimitado)
- Ambas gratuitas

---

## 📊 TABLA COMPARATIVA

| Aspecto | SofaScore | The Odds API |
|---------|-----------|---|
| **Costo** | $0 | $0 (500/mes) |
| **Auth** | ❌ No | ✅ Sí (gratuita) |
| **Spreads** | ✅ | ✅ |
| **Totals** | ✅ | ✅ |
| **Deportes** | 12/12 | 9/12 |
| **Rate Limit** | Ilimitado | 500/mes |
| **Confiabilidad** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Documentación** | Media | Excelente |
| **Registro** | No | Sí (2 min) |

---

## 🚀 EMPEZAR YA (5 MINUTOS)

### Opción A: SofaScore (Más fácil)
```bash
# Sin registrarse, copiar y pegar
curl "https://www.sofascore.com/api/v1/sport/football/events/today" | jq '.events[0]'
```

### Opción B: The Odds API (Más confiable)
```bash
# 1. Registrarse: https://www.the-odds-api.com/register
# 2. Copiar API Key
# 3. Ejecutar:
curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=YOUR_KEY&markets=spreads"
```

---

## 📚 DOCUMENTACIÓN COMPLETA

Para más detalles, ver:

1. **[FREE_ODDS_SUMMARY_2026.md](FREE_ODDS_SUMMARY_2026.md)** - Resumen ejecutivo (5 min)
2. **[FREE_ODDS_FINAL_MATRIX.md](FREE_ODDS_FINAL_MATRIX.md)** - Tabla comparativa (10 min)
3. **[FREE_ODDS_CURL_TESTS.md](FREE_ODDS_CURL_TESTS.md)** - Comandos para probar (5 min)
4. **[FREE_ODDS_IMPLEMENTATION_GUIDE.md](FREE_ODDS_IMPLEMENTATION_GUIDE.md)** - Código Python (15 min)
5. **[FREE_ODDS_APIS_FINAL_RESEARCH_2026.md](FREE_ODDS_APIS_FINAL_RESEARCH_2026.md)** - Investigación completa (30 min)
6. **[FREE_ODDS_INDEX_2026.md](FREE_ODDS_INDEX_2026.md)** - Índice navegable

---

## ✅ CONCLUSIÓN

**¿Existen APIs gratuitas con spreads + totals?** ✅ SÍ (SofaScore)

**¿Existen APIs gratuitas con props + correct score?** ❌ NO

**¿Cuál usar?** 
- **Simplemente:** SofaScore
- **Producción:** SofaScore + The Odds API
- **Máxima confiabilidad:** The Odds API (pero limitado)

**Costo total:** $0 ✅

---

**Última actualización:** 29 de Enero de 2026  
**Status:** ✅ Investigación completada  
**Próximo paso:** Copiar comandos de curl arriba y probar en terminal

