#!/usr/bin/env bash
# Quick endpoint tester for AlphaForge Recommendations

API_URL="http://localhost:8000"
TOKEN="${FIREBASE_TOKEN:-demo-token}"  # Use demo token for development

echo "🧪 AlphaForge Recommendations - Endpoint Test Suite"
echo "=================================================="
echo "API URL: $API_URL"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing:${NC} $description"
    echo "  $method $endpoint"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL$endpoint")
    else
        response=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
    fi
    
    # Check if response contains "success"
    if echo "$response" | grep -q "success"; then
        echo -e "${GREEN}✅ Success${NC}"
        echo "  Response: ${response:0:100}..."
    else
        echo -e "${RED}❌ Failed${NC}"
        echo "  Response: $response"
    fi
    echo ""
}

# Test endpoints
echo -e "${YELLOW}1️⃣  Testing Signal Performance Endpoints${NC}"
test_endpoint "GET" "/api/signals/high-performers?limit=10" "" "Get high-performing signals"

echo -e "${YELLOW}2️⃣  Testing External Signal Validation${NC}"
test_endpoint "GET" "/api/external-signals/sources" "" "Get external signal sources"

echo -e "${YELLOW}3️⃣  Testing Market Correlation Analysis${NC}"
test_endpoint "GET" "/api/market/correlations?time_window=30d" "" "Get market correlations"

echo -e "${YELLOW}4️⃣  Testing Cache Stats${NC}"
test_endpoint "GET" "/api/cache/stats" "" "Get cache statistics"

echo -e "${YELLOW}5️⃣  Testing WebSocket Status${NC}"
test_endpoint "GET" "/api/websocket/status" "" "Get WebSocket connection status"

echo -e "${YELLOW}6️⃣  Testing Signal Conflict Check${NC}"
test_endpoint "POST" "/api/market/signals/conflicts" \
    '{"asset":"BTC","signal_type":"BUY","related_assets":["ETH","SOL"]}' \
    "Check signal conflicts"

echo ""
echo "🎉 Endpoint tests complete!"
echo ""
echo "To use real Firebase tokens:"
echo "  FIREBASE_TOKEN=<your-token> ./test_endpoints.sh"
