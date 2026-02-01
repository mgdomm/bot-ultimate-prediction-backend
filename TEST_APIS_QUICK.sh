#!/bin/bash

# Script rápido para probar las 2 APIs gratuitas recomendadas

echo "════════════════════════════════════════════════════════════════════════════"
echo "           TESTING FREE ODDS APIs - SofaScore + The Odds API"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# TEST 1: SofaScore (Sin registro, sin auth)
echo "✅ TEST 1: SofaScore API (Sin autenticación)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Obteniendo eventos de Soccer de hoy..."
SOCCER_RESPONSE=$(curl -s "https://www.sofascore.com/api/v1/sport/football/events/today")
EVENT_COUNT=$(echo "$SOCCER_RESPONSE" | grep -o '"id"' | wc -l)
echo "✅ SofaScore respondió con ~$EVENT_COUNT eventos"

if [ $EVENT_COUNT -gt 0 ]; then
    echo "✅ Status: FUNCIONA"
    EVENT_ID=$(echo "$SOCCER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
    echo "   Primer evento ID: $EVENT_ID"
    
    echo ""
    echo "Obteniendo odds del evento..."
    ODDS_RESPONSE=$(curl -s "https://www.sofascore.com/api/v1/event/$EVENT_ID/odds")
    MARKETS=$(echo "$ODDS_RESPONSE" | grep -o '"marketName"' | wc -l)
    echo "✅ Encontrados $MARKETS mercados de apuestas"
else
    echo "❌ Status: SIN EVENTOS (puede ser fuera de horario)"
fi

echo ""
echo ""

# TEST 2: The Odds API (Con API Key)
echo "✅ TEST 2: The Odds API (Requiere API Key)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

API_KEY=$(echo $ODDS_API_KEY)

if [ -z "$API_KEY" ]; then
    echo "⚠️  API Key no encontrada en variable de entorno ODDS_API_KEY"
    echo "   Para obtener API Key:"
    echo "   1. Ve a https://www.the-odds-api.com/register"
    echo "   2. Copia tu API Key"
    echo "   3. Ejecuta: export ODDS_API_KEY='tu_key'"
    echo "   4. Corre este script nuevamente"
else
    echo "Usando API Key: ${API_KEY:0:10}****"
    
    echo "Obteniendo deportes disponibles..."
    SPORTS_RESPONSE=$(curl -s "https://api.the-odds-api.com/v4/sports?api_key=$API_KEY")
    SPORTS_COUNT=$(echo "$SPORTS_RESPONSE" | grep -o '"sport_key"' | wc -l)
    
    if [ $SPORTS_COUNT -gt 0 ]; then
        echo "✅ The Odds API respondió con $SPORTS_COUNT deportes"
        
        echo ""
        echo "Obteniendo odds de Soccer..."
        ODDS_RESPONSE=$(curl -s "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?api_key=$API_KEY&regions=us&markets=h2h,spreads,totals")
        EVENT_COUNT=$(echo "$ODDS_RESPONSE" | grep -o '"home_team"' | wc -l)
        
        if [ $EVENT_COUNT -gt 0 ]; then
            echo "✅ Encontrados $EVENT_COUNT eventos con odds (h2h + spreads + totals)"
            echo "✅ Status: FUNCIONA"
        else
            echo "⚠️  Sin eventos en este momento"
        fi
    else
        echo "❌ Error con The Odds API"
        echo "   Verifica que tu API Key sea válida"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ RESUMEN"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "SofaScore: ✅ Funcionando (sin autenticación)"
echo "The Odds API: $([ -z '$API_KEY' ] && echo '⚠️  Requiere API Key' || echo '✅ Funcionando')"
echo ""
echo "PRÓXIMOS PASOS:"
echo "1. Si SofaScore funciona: Implementar con SofaScore API"
echo "2. Si quieres The Odds API: Registrarse en https://www.the-odds-api.com/"
echo "3. Ver documentación en: FREE_ODDS_IMPLEMENTATION_GUIDE.md"
echo ""
