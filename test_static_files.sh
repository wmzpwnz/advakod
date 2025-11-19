#!/bin/bash

echo "=== Testing Static Files Delivery ==="
echo

# Test CSS files
echo "Testing CSS files:"
curl -s -I https://advacodex.com/static/css/main.0e3cbb1b.css -k | grep -E "(HTTP|content-type|cache-control|expires)"
echo

# Test JS files  
echo "Testing JS files:"
curl -s -I https://advacodex.com/static/js/main.a61420f6.js -k | grep -E "(HTTP|content-type|cache-control|expires)"
echo

# Test manifest
echo "Testing manifest.json:"
curl -s -I https://advacodex.com/manifest.json -k | grep -E "(HTTP|content-type|cache-control)"
echo

# Test gzip compression
echo "Testing gzip compression:"
curl -s -H "Accept-Encoding: gzip" -I https://advacodex.com/static/css/main.0e3cbb1b.css -k | grep -E "(content-encoding|vary)"
echo

# Test 404 handling
echo "Testing 404 handling:"
curl -s -I https://advacodex.com/static/js/nonexistent.js -k | grep "HTTP"
echo

# Test performance (5 parallel requests)
echo "Testing performance (5 parallel requests):"
for i in {1..5}; do
    curl -s -w "%{http_code} %{time_total}s\n" -o /dev/null https://advacodex.com/static/css/main.0e3cbb1b.css -k &
done
wait
echo

echo "=== Static Files Test Complete ==="