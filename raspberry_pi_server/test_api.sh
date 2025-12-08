#!/bin/bash
# PSMS API Test Script
# Tests all API endpoints to verify server functionality

SERVER_URL="${1:-http://localhost:5000}"
DEVICE_ID="TEST_DEVICE_$(date +%s)"

echo "========================================="
echo "PSMS API Test Suite"
echo "Server: $SERVER_URL"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$SERVER_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$SERVER_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" == "200" ] || [ "$http_code" == "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((test_passed++))
        if [ ! -z "$5" ]; then
            echo "  Response: $(echo $body | head -c 100)..."
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        ((test_failed++))
        echo "  Response: $body"
    fi
    echo ""
}

# Test 1: Health Check
echo -e "${YELLOW}1. Health Check Endpoint${NC}"
test_endpoint "Health Check" "GET" "/api/health"

# Test 2: Root Endpoint
echo -e "${YELLOW}2. Root API Endpoint${NC}"
test_endpoint "Root API" "GET" "/"

# Test 3: Post Sensor Data
echo -e "${YELLOW}3. Post Sensor Data${NC}"
test_data='{
  "device_id": "'$DEVICE_ID'",
  "location": "Test_Room",
  "timestamp": '$(date +%s000)',
  "sensors": {
    "temperature": 25.5,
    "humidity": 60.0,
    "air_quality": 400,
    "distance": 100
  },
  "alert_type": "none",
  "alert_active": false
}'
test_endpoint "Post Sensor Data" "POST" "/api/sensor-data" "$test_data" "show"

# Test 4: Get Latest Data
echo -e "${YELLOW}4. Get Latest Data${NC}"
test_endpoint "Get All Latest Data" "GET" "/api/latest-data"
test_endpoint "Get Device Latest Data" "GET" "/api/latest-data?device_id=$DEVICE_ID"

# Test 5: Get Alerts
echo -e "${YELLOW}5. Get Alerts${NC}"
test_endpoint "Get All Alerts" "GET" "/api/alerts"
test_endpoint "Get Active Alerts" "GET" "/api/alerts?active=true"

# Test 6: Get Devices
echo -e "${YELLOW}6. Get Devices${NC}"
test_endpoint "Get All Devices" "GET" "/api/devices"

# Test 7: Get Statistics
echo -e "${YELLOW}7. Get Statistics${NC}"
test_endpoint "Get Statistics" "GET" "/api/statistics"

# Test 8: Post Alert Data
echo -e "${YELLOW}8. Post Alert Sensor Data${NC}"
alert_data='{
  "device_id": "'$DEVICE_ID'",
  "location": "Test_Room",
  "timestamp": '$(date +%s000)',
  "sensors": {
    "temperature": 35.0,
    "humidity": 80.0,
    "air_quality": 800,
    "distance": 30
  },
  "alert_type": "high_temperature",
  "alert_active": true
}'
test_endpoint "Post Alert Data" "POST" "/api/sensor-data" "$alert_data"

# Test 9: Verify Alert Created
echo -e "${YELLOW}9. Verify Alert Created${NC}"
sleep 1
test_endpoint "Check Device Alerts" "GET" "/api/alerts?device_id=$DEVICE_ID"

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Passed: ${GREEN}$test_passed${NC}"
echo -e "Failed: ${RED}$test_failed${NC}"
echo -e "Total:  $((test_passed + test_failed))"
echo ""

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
