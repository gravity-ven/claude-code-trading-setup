#!/bin/bash
# 15-Minute Data Refresh - More frequent updates

echo "=========================================="
echo "Spartan Research - 15-Min Data Refresh"
echo "Time: $(date)"
echo "=========================================="

# Run the Polygon.io data loader
docker exec spartan_web python3 /app/polygon_data_loader.py

# Clear Redis cache to force fresh data
docker exec spartan_redis redis-cli FLUSHDB

echo "✓ Refresh complete at $(date)"
echo ""
