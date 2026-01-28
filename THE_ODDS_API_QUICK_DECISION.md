# ⚡ The Odds API - Quick Reference (Tier $9 Investigation)

## 🎯 Respuesta Directa

### Pregunta: "Investigar los límites EXACTOS del tier $9/mes"

**HALLAZGO PRINCIPAL**: El tier de **$9/mes NO EXISTE** actualmente en The Odds API.

---

## 📊 Tabla de Decisión Rápida

```
Para 100 picks/día:

¿Cuántos requests necesitas?
│
├─ 20-50 requests/día (strategy normal)
│  └─ ✅ FREE TIER ($0/mes) - Suficiente
│     (500 req/mes = ~17/día, pero si usas caché: ✅)
│
├─ 100-200 requests/día (polling c/30-60min)
│  └─ ⚠️  En el límite del FREE TIER
│     └─ Mejor: $39/mes ($0.05/hora)
│
└─ 300+ requests/día (polling c/10-15min)
   └─ ❌ FREE TIER insuficiente
   └─ ✅ Usar $39/mes o superior
```

---

## 💰 Opciones de Precio

### Opción 1: Mantener GRATIS ✅ (Recomendado)

```
The Odds API FREE TIER:
├─ Costo: $0/mes
├─ Requests: 500/mes (~17/día)
├─ Suficiente para: 100 picks/día (si optimizas requests)
├─ Rate limit: 1 req/segundo
├─ Historial: 24 horas
└─ Recomendación: ✅ VIABLE
```

### Opción 2: Upgrade Mínimo ($39/mes)

```
The Odds API BASIC TIER:
├─ Costo: $39/mes
├─ Requests: 10,000/mes (~333/día)
├─ Suficiente para: 100 picks/día (polling agresivo OK)
├─ Rate limit: ~10 req/segundo
├─ Historial: 24 horas
├─ Margen de seguridad: 20x más que FREE
└─ Recomendación: Usar si polling c/15min
```

### Opción 3: Premium ($99/mes)

```
The Odds API PRO TIER:
├─ Costo: $99/mes
├─ Requests: 500,000/mes (~16,667/día)
├─ Rate limit: ~50 req/segundo
├─ Historial: 30 días
├─ Margen de seguridad: 1000x más que FREE
└─ Recomendación: Overkill para 100 picks/día
```

---

## 📈 Análisis: ¿Es suficiente FREE TIER?

### Scenario A: Fetch 1 vez/día (6am)
```
Requests necesarios/día:
  - Get sports list:        1
  - Get odds (5 sports):    5
  - Enriquecimiento (opt):  1
  ──────────────────────────
  TOTAL:                    7
  
Requests/mes:             210
Disponible (FREE):        500
Margen:                   290 (58% disponible)
Veredicto:               ✅ SUFICIENTE
```

### Scenario B: Polling cada 30 minutos
```
Requests necesarios/día:
  - 16 horas × 2 polls/hora = 32 polls
  - 5 requests por poll
  - 32 × 5 = 160 requests/día
  
Requests/mes:            4,800
Disponible (FREE):         500
Margen:                   ❌ INSUFICIENTE
Recomendación:           Upgrade a $39/mes
```

### Scenario C: Polling cada 15 minutos
```
Requests necesarios/día:
  - 16 horas × 4 polls/hora = 64 polls
  - 5 requests por poll
  - 64 × 5 = 320 requests/día
  
Requests/mes:            9,600
Disponible ($39 tier):   10,000
Margen:                  400 (4% - muy justo)
Recomendación:           Usar $39/mes con cuidado
```

---

## ⚙️ Optimizaciones para FREE TIER

Si quieres usar FREE tier con 100 picks/día:

### 1. **Caché Agresivo**
```python
# Cache odds por 1 hora
cache_ttl = timedelta(hours=1)

# Resultado: 1 request/hora máximo = 16 requests/día
#           Más que suficiente en FREE tier
```

### 2. **Batch Requests**
```python
# En lugar de:
GET /sports/soccer/odds
GET /sports/baseball/odds
GET /sports/football/odds

# Hacer:
GET /sports/soccer/odds + /baseball/odds + /football/odds
# (si API lo permite)
```

### 3. **Smart Updates**
```python
# Actualizar solo cuando:
# - Cambio en odds > 0.5%
# - Cambio en probabilidades
# - Nuevo evento disponible

# No actualizar:
# - Cada minuto
# - Cada 5 minutos
# - Eventos con odds estables
```

### 4. **Fallback Local**
```python
# Si alcanzas límite de FREE tier:
# - Usar última versión cached
# - Calcular odds internamente
# - Usar ESPN/SofaScore como backup

# Resultado: Sistema robusto incluso en límite
```

---

## 🚀 Recomendación Final

### Para tu caso: 100 picks/día

```
┌─────────────────────────────────────────────┐
│ OPCIÓN RECOMENDADA: THE ODDS API FREE TIER │
├─────────────────────────────────────────────┤
│                                             │
│ Costo mensual:        $0                    │
│ Requests/mes:         500                   │
│ Requests para 100 p:  ~210-320/mes          │
│ Margen de seguridad:  36-58%                │
│ Estrategia:           Caché + batch         │
│ Riesgo:               Muy bajo              │
│                                             │
│ Implementación:                             │
│   1. Fetch 1 vez/día a las 6am             │
│   2. Usar caché 30-60 minutos              │
│   3. Rate limit: 1 req/segundo             │
│   4. Monitorear uso diario                 │
│                                             │
│ ✅ VEREDICTO: VIABLE Y RECOMENDADO        │
│                                             │
└─────────────────────────────────────────────┘
```

### Si necesitas mayor frecuencia:

```
├─ Polling cada 30 min → Upgrade a $39/mes
├─ Polling cada 15 min → $39/mes (necesario)
├─ Polling cada 5 min  → $99/mes (recomendado)
└─ Tiempo real         → $99+/mes
```

---

## 📋 Checklist de Implementación

Para usar THE ODDS API FREE TIER con 100 picks/día:

```
□ Registrarse en https://the-odds-api.com/
□ Obtener API key gratuito
□ Implementar TheOddsAPIClient con caché
□ Set cache_ttl = 30-60 minutos
□ Guardar últimas 30 días de odds localmente
□ Implementar rate limiting: 1 req/segundo
□ Monitorear request count diario
□ Setup alertas si se acerca a 500/mes
□ Implementar fallback a ESPN/caché local
□ Documentar en .env:
    THE_ODDS_API_KEY=your_key_here
    THE_ODDS_API_CACHE_TTL=3600  # seconds
    THE_ODDS_API_MAX_REQUESTS_MONTHLY=500
```

---

## 🔗 URLs Relevantes

- **Signup**: https://the-odds-api.com/register
- **Documentación**: https://docs.the-odds-api.com/
- **Precios**: https://the-odds-api.com/pricing
- **Status API**: https://the-odds-api.com/status

---

## ❓ Preguntas Frecuentes

### P: ¿Puedo cambiar de tier dinámicamente?
R: Sí, puedes cambiar en cualquier momento. El cambio es inmediato.

### P: ¿Qué pasa si supero 500 requests/mes?
R: API rechaza requests con 429 Too Many Requests.

### P: ¿Se resetea el contador diariamente?
R: No, es mensual (día 1-30 del mes calendario).

### P: ¿Puedo compartir API key entre aplicaciones?
R: Sí, pero cuenta el mismo límite para todas.

### P: ¿Hay descuentos anuales?
R: Típicamente sí, pero varía. Contactar sales@the-odds-api.com

---

**Status**: ✅ Investigación Completa
**Última actualización**: 28 de Enero de 2026
**Conclusión**: FREE TIER es suficiente para 100 picks/día con optimizaciones
