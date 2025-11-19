#!/bin/bash
echo "Testing frontend availability..."
for i in {1..5}; do
    echo "Attempt $i..."
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is accessible!"
        exit 0
    else
        echo "❌ Frontend not accessible, waiting..."
        sleep 3
    fi
done
echo "❌ Frontend still not accessible after 5 attempts"
exit 1
