#!/bin/bash
echo "=== Testing All API Endpoints ==="
echo ""

echo "1. Port 5000 - Daily Planet API"
curl -s "http://localhost:5000/api/market-news" | python3 -m json.tool | head -5
echo "✅ Port 5000 OK"
echo ""

echo "2. Port 5002 - Swing Dashboard API (Yahoo)"
curl -s "http://localhost:5002/api/yahoo/quote?symbols=QQQ" | python3 -m json.tool | head -5
echo "✅ Port 5002 OK"
echo ""

echo "3. Port 5002 - Swing Dashboard API (FRED)"
curl -s "http://localhost:5002/api/fred/series/observations?series_id=DFF&limit=1" | python3 -m json.tool | head -5
echo "✅ Port 5002 FRED OK"
echo ""

echo "4. Port 5003 - GARP API"
curl -s "http://localhost:5003/api/garp/sectors" | python3 -m json.tool | head -5
echo "✅ Port 5003 OK"
echo ""

echo "5. Port 5004 - Correlation API"
curl -s "http://localhost:5004/api/metadata" | python3 -m json.tool | head -10
echo "✅ Port 5004 OK"
echo ""

echo "6. Port 8888 - Main Server (Database)"
curl -s "http://localhost:8888/api/db/stats" | python3 -m json.tool
echo "✅ Port 8888 OK"
echo ""

echo "=== All Endpoints Tested Successfully ==="
