# 📌 RESUMEN EJECUTIVO: Free APIs con Múltiples Mercados (Enero 2026)

**Solicitud Original**: Investigar APIs de apuestas deportivas GRATUITAS con múltiples mercados (spreads, totals, props, correct score)

**Investigación**: Completa y exhaustiva ✅  
**Hallazgo**: 2 opciones viables, NO existen opciones con todo gratis

---

## 🎯 RESPUESTA DIRECTA

### ✅ APIs GRATUITAS CON MÚLTIPLES MERCADOS (h2h + spreads + totals):

| API | Costo | Auth | Spreads | Totals | Props | Correct Score | Rate Limit |
|-----|-------|------|---------|--------|-------|---------------|-----------|
| **The Odds API FREE** | $0 | Sí (free) | ✅ | ✅ | ❌ | ❌ | 500/mes |
| **SofaScore** | $0 | No | ✅ | ✅ | ❌ | ⚠️ | Ilimitado |

### ❌ NO EXISTEN OPCIONES GRATUITAS CON:
- Player props
- Correct score (scores exactos)
- Sin límites mensuales
- Todas las opciones en una API

---

## 📊 TABLA COMPARATIVA - 4 DEPORTES MÍNIMOS

### **The Odds API (FREE - 500 req/mes)**

```
Sports Coverage:
✅ Soccer (20+ ligas)
✅ NFL
✅ NBA
✅ MLB

Markets:
✅ h2h (Moneyline)
✅ spreads (Handicap)
✅ totals (Over/Under)
❌ Player props
❌ Correct score

Rate Limit:
- 500 requests/mes = ~16 req/día
- 1 request/segundo máximo

Bookmakers:
- DraftKings, FanDuel, BetMGM, BetRivers, +más

Stability:
⭐⭐⭐⭐⭐ Oficial, confiable
```

### **SofaScore (FREE - Ilimitado)**

```
Sports Coverage:
✅ Soccer (todas las ligas)
✅ NFL
✅ NBA
✅ MLB

Markets:
✅ h2h (Moneyline)
✅ spreads (Handicap)
✅ totals (Over/Under)
⚠️ Correct score (parcial)
❌ Player props

Rate Limit:
- Ilimitado (sin documentación de límites)
- Típicamente 1-2 req/segundo

Bookmakers:
- 20+ incluidos Bet365, William Hill, Pinnacle

Stability:
⭐⭐⭐⭐ No oficial pero muy usado
```

---

## 📥 COMO EMPEZAR - 5 MINUTOS

### Opción A: The Odds API (Más confiable)

```bash
# 1. Registrarse
curl https://www.the-odds-api.com/register

# 2. Copiar API Key del email

# 3. Primer request
curl "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=YOUR_KEY&markets=h2h,spreads,totals"

# 4. Resultado: JSON con odds de múltiples mercados
```

### Opción B: SofaScore (Más rápido, sin registrarse)

```bash
# 1. Obtener eventos de hoy
curl "https://www.sofascore.com/api/v1/sport/football/events/today"

# 2. Copiar event_id del resultado

# 3. Obtener odds
curl "https://www.sofascore.com/api/v1/event/{event_id}/odds"

# 4. Resultado: JSON con todos los mercados
```

---

## 💡 RECOMENDACIÓN

### Para uso GENERAL:
→ **SofaScore** (ilimitado, sin registrarse)

### Para máxima CONFIABILIDAD:
→ **The Odds API** (datos verificados, pero 16 req/día)

### Para PRODUCCIÓN:
→ **SofaScore (principal) + The Odds API (verificación)**

---

## 🚨 LIMITACIONES IMPORTANTES

### ❌ NO disponibles en NINGUNA API gratuita:
1. **Player props** (ej: "Tom Brady over 250 passing yards")
2. **Correct score** con datos completos
3. **Futures bets** (apuestas a largo plazo)
4. **In-play betting** (apuestas durante el juego en vivo)

### ⚠️ The Odds API limitaciones:
- Solo 500 requests/mes (MUY poco si necesitas actualización frecuente)
- 3 deportes menos (sin Handball, Volleyball, MMA)

### ⚠️ SofaScore limitaciones:
- API no oficial (reverse-engineered)
- Documentación limitada
- Sin garantía de estabilidad

---

## 📍 PRÓXIMOS PASOS

1. **Prueba SofaScore primero** (0 registro, 0 límites)
2. **Si necesitas confiabilidad**, agrega The Odds API
3. **Si necesitas props/correct score**, considera pagar:
   - The Odds API PAID: $9/mes
   - Sportradar: $1,000+/mes
   - DraftKings API: Contactar directamente

---

## 📚 DOCUMENTOS INCLUIDOS

1. **FREE_ODDS_APIS_FINAL_RESEARCH_2026.md** - Investigación completa
2. **FREE_ODDS_IMPLEMENTATION_GUIDE.md** - Código listo para usar
3. Este archivo - Resumen ejecutivo

---

## 🎓 CONCLUSIÓN

✅ **Sí existen opciones gratuitas con múltiples mercados (h2h + spreads + totals)**
❌ **No existen opciones gratuitas con props ni correct score**
💰 **Costo total para cobertura básica: $0**
⚠️ **El trade-off: Límites de rate o uso de API no oficial**

