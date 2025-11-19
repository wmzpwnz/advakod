#!/bin/bash

# Production deployment script with localhost prevention
# This script ensures proper Docker service configuration

set -e  # Exit on any error

echo "🚀 Starting ADVAKOD production deployment..."
echo "================================================"

# Check if we're in the right directory
if [[ ! -f "docker-compose.prod.yml" ]]; then
    echo "❌ Error: docker-compose.prod.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Step 1: Check for localhost references
echo "📋 Step 1: Checking for localhost references..."
if [[ -f "scripts/check_localhost.sh" ]]; then
    ./scripts/check_localhost.sh
    if [[ $? -ne 0 ]]; then
        echo "❌ Deployment blocked due to localhost references!"
        exit 1
    fi
else
    echo "⚠️  Warning: localhost check script not found, continuing..."
fi

# Step 2: Validate environment files
echo "📋 Step 2: Validating environment configuration..."

# Check if production environment file exists
if [[ ! -f ".env.production" ]]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production with proper Docker service names."
    exit 1
fi

# Validate critical environment variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "SECRET_KEY" 
    "ENCRYPTION_KEY"
    "REACT_APP_API_URL"
    "REACT_APP_WS_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env.production; then
        echo "❌ Error: Required variable $var not found in .env.production"
        exit 1
    fi
done

# Check that URLs don't contain localhost
if grep -q "localhost\|127\.0\.0\.1" .env.production; then
    echo "❌ Error: .env.production contains localhost references!"
    echo "Please use proper domain names or Docker service names."
    exit 1
fi

echo "✅ Environment configuration validated"

# Step 3: Stop existing containers
echo "📋 Step 3: Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# Step 4: Clean up old images (optional)
echo "📋 Step 4: Cleaning up old Docker images..."
docker system prune -f --volumes || true

# Step 5: Build and start services
echo "📋 Step 5: Building and starting services..."

# Use production environment file
export $(cat .env.production | grep -v '^#' | xargs)

# Build with no cache to ensure fresh build
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services in correct order
echo "🔄 Starting database services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis qdrant

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 30

# Check database health
echo "🏥 Checking database health..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U advakod -d advakod_db
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping
docker-compose -f docker-compose.prod.yml exec -T qdrant curl -f http://localhost:6333/health

# Start backend
echo "🔄 Starting backend service..."
docker-compose -f docker-compose.prod.yml up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to load Vistral model..."
sleep 120  # Vistral-24B needs time to load

# Check backend health
echo "🏥 Checking backend health..."
for i in {1..10}; do
    if docker-compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health; then
        echo "✅ Backend is healthy"
        break
    else
        echo "⏳ Backend not ready yet, waiting... ($i/10)"
        sleep 30
    fi
    
    if [[ $i -eq 10 ]]; then
        echo "❌ Backend failed to start properly"
        echo "📋 Backend logs:"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
done

# Start frontend and nginx
echo "🔄 Starting frontend and nginx..."
docker-compose -f docker-compose.prod.yml up -d frontend nginx

# Wait for services to be ready
echo "⏳ Waiting for all services to be ready..."
sleep 30

# Step 6: Final health checks
echo "📋 Step 6: Running final health checks..."

# Check all services
SERVICES=("postgres" "redis" "qdrant" "backend" "frontend" "nginx")
for service in "${SERVICES[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps $service | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running properly"
        docker-compose -f docker-compose.prod.yml logs $service
        exit 1
    fi
done

# Test external connectivity
echo "🌐 Testing external connectivity..."
if curl -f -s https://advacodex.com/api/v1/health > /dev/null; then
    echo "✅ External API is accessible"
else
    echo "⚠️  Warning: External API not accessible (might be normal if SSL not configured)"
fi

# Step 7: Display deployment summary
echo ""
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "====================================="
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🔗 Service URLs:"
echo "  - Website: https://advacodex.com"
echo "  - API: https://advacodex.com/api/v1"
echo "  - WebSocket: wss://advacodex.com/ws"
echo "  - Health Check: https://advacodex.com/api/v1/health"
echo ""
echo "📋 Next Steps:"
echo "  1. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  2. Check metrics: curl https://advacodex.com/api/v1/metrics"
echo "  3. Test WebSocket: Open browser dev tools and test chat"
echo ""
echo "🔧 Troubleshooting:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs [service]"
echo "  - Restart service: docker-compose -f docker-compose.prod.yml restart [service]"
echo "  - Check resources: docker stats"
echo ""

# Step 8: Start monitoring (optional)
if [[ -f "scripts/monitor_system.sh" ]]; then
    echo "🔍 Starting system monitoring..."
    nohup ./scripts/monitor_system.sh > monitoring.log 2>&1 &
    echo "✅ Monitoring started (logs in monitoring.log)"
fi

echo "🚀 ADVAKOD is now running in production mode!"