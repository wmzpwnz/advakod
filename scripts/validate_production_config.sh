#!/bin/bash

# Comprehensive production configuration validation script
# This script validates that the system is properly configured for production deployment

set -e

echo "🔍 ADVAKOD Production Configuration Validation"
echo "=============================================="

VALIDATION_FAILED=false
WARNINGS=()
ERRORS=()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS+=("$1")
    VALIDATION_FAILED=true
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS+=("$1")
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 1. Check for localhost references
echo ""
echo "1. Checking for localhost references..."
if ./scripts/check_localhost.sh > /dev/null 2>&1; then
    log_success "No localhost references found"
else
    log_error "Localhost references found - run ./scripts/check_localhost.sh for details"
fi

# 2. Validate environment variables
echo ""
echo "2. Validating environment variables..."

required_env_vars=(
    "ENVIRONMENT"
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "DATABASE_URL"
    "REDIS_URL"
    "QDRANT_HOST"
    "VISTRAL_MODEL_PATH"
    "CORS_ORIGINS"
)

for var in "${required_env_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        log_error "Required environment variable $var is not set"
    else
        # Check for localhost in environment variables
        if echo "${!var}" | grep -q -E "(localhost|127\.0\.0\.1)"; then
            log_error "Environment variable $var contains localhost: ${!var}"
        else
            log_success "Environment variable $var is properly set"
        fi
    fi
done

# 3. Check ENVIRONMENT setting
echo ""
echo "3. Checking environment setting..."
if [[ "$ENVIRONMENT" == "production" ]]; then
    log_success "Environment is set to production"
    
    # Additional production checks
    if [[ "$DEBUG" == "true" ]]; then
        log_error "DEBUG is enabled in production"
    else
        log_success "DEBUG is disabled in production"
    fi
    
    # Check CORS origins
    if [[ "$CORS_ORIGINS" == *"localhost"* ]]; then
        log_error "CORS_ORIGINS contains localhost in production"
    elif [[ "$CORS_ORIGINS" == *"https://"* ]]; then
        log_success "CORS_ORIGINS uses HTTPS in production"
    else
        log_warning "CORS_ORIGINS should use HTTPS in production"
    fi
    
else
    log_warning "Environment is not set to production (current: $ENVIRONMENT)"
fi

# 4. Check SSL configuration
echo ""
echo "4. Checking SSL configuration..."
if [[ -f "/etc/letsencrypt/live/advacodex.com/fullchain.pem" ]]; then
    log_success "SSL certificate found"
    
    # Check certificate expiry
    if command -v openssl >/dev/null 2>&1; then
        CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/advacodex.com/fullchain.pem | cut -d= -f2)
        EXPIRY_TIMESTAMP=$(date -d "$CERT_EXPIRY" +%s)
        CURRENT_TIMESTAMP=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( (EXPIRY_TIMESTAMP - CURRENT_TIMESTAMP) / 86400 ))
        
        if [[ $DAYS_UNTIL_EXPIRY -lt 30 ]]; then
            log_warning "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
        else
            log_success "SSL certificate is valid for $DAYS_UNTIL_EXPIRY days"
        fi
    fi
else
    log_error "SSL certificate not found at /etc/letsencrypt/live/advacodex.com/fullchain.pem"
fi

# 5. Check Docker configuration
echo ""
echo "5. Checking Docker configuration..."
if [[ -f "docker-compose.prod.yml" ]]; then
    log_success "Production Docker Compose file found"
    
    # Check for localhost in Docker Compose
    if grep -q -E "(localhost|127\.0\.0\.1)" docker-compose.prod.yml; then
        log_error "localhost references found in docker-compose.prod.yml"
    else
        log_success "No localhost references in Docker Compose"
    fi
    
    # Check for proper service names
    REQUIRED_SERVICES=("postgres" "redis" "qdrant" "backend" "frontend" "nginx")
    for service in "${REQUIRED_SERVICES[@]}"; do
        if grep -q "^  $service:" docker-compose.prod.yml; then
            log_success "Service $service defined in Docker Compose"
        else
            log_error "Service $service not found in Docker Compose"
        fi
    done
else
    log_error "Production Docker Compose file not found"
fi

# 6. Check Nginx configuration
echo ""
echo "6. Checking Nginx configuration..."
if [[ -f "nginx.conf" ]]; then
    log_success "Nginx configuration found"
    
    # Check for proper upstream definitions
    if grep -q "upstream backend" nginx.conf; then
        log_success "Backend upstream defined in Nginx"
    else
        log_error "Backend upstream not defined in Nginx"
    fi
    
    if grep -q "upstream frontend" nginx.conf; then
        log_success "Frontend upstream defined in Nginx"
    else
        log_error "Frontend upstream not defined in Nginx"
    fi
    
    # Check for HTTPS redirect
    if grep -q "return 301 https" nginx.conf; then
        log_success "HTTPS redirect configured in Nginx"
    else
        log_warning "HTTPS redirect not found in Nginx configuration"
    fi
    
    # Check for security headers
    SECURITY_HEADERS=("Strict-Transport-Security" "X-Frame-Options" "X-Content-Type-Options")
    for header in "${SECURITY_HEADERS[@]}"; do
        if grep -q "$header" nginx.conf; then
            log_success "Security header $header found in Nginx"
        else
            log_warning "Security header $header not found in Nginx"
        fi
    done
else
    log_error "Nginx configuration not found"
fi

# 7. Check model files
echo ""
echo "7. Checking AI model files..."
if [[ -n "$VISTRAL_MODEL_PATH" && -f "$VISTRAL_MODEL_PATH" ]]; then
    MODEL_SIZE=$(du -h "$VISTRAL_MODEL_PATH" | cut -f1)
    log_success "Vistral model found ($MODEL_SIZE)"
else
    log_error "Vistral model not found at $VISTRAL_MODEL_PATH"
fi

# 8. Check database connectivity
echo ""
echo "8. Checking database connectivity..."
if command -v psql >/dev/null 2>&1 && [[ -n "$DATABASE_URL" ]]; then
    if psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Database connection successful"
    else
        log_error "Cannot connect to database"
    fi
else
    log_warning "Cannot test database connectivity (psql not available or DATABASE_URL not set)"
fi

# 9. Check Redis connectivity
echo ""
echo "9. Checking Redis connectivity..."
if command -v redis-cli >/dev/null 2>&1 && [[ -n "$REDIS_URL" ]]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed 's|redis://||' | cut -d: -f1)
    REDIS_PORT=$(echo "$REDIS_URL" | sed 's|redis://||' | cut -d: -f2)
    
    if redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ping >/dev/null 2>&1; then
        log_success "Redis connection successful"
    else
        log_error "Cannot connect to Redis"
    fi
else
    log_warning "Cannot test Redis connectivity (redis-cli not available or REDIS_URL not set)"
fi

# 10. Check Qdrant connectivity
echo ""
echo "10. Checking Qdrant connectivity..."
if command -v curl >/dev/null 2>&1 && [[ -n "$QDRANT_HOST" ]]; then
    QDRANT_PORT="${QDRANT_PORT:-6333}"
    if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" >/dev/null 2>&1; then
        log_success "Qdrant connection successful"
    else
        log_error "Cannot connect to Qdrant"
    fi
else
    log_warning "Cannot test Qdrant connectivity (curl not available or QDRANT_HOST not set)"
fi

# 11. Check disk space
echo ""
echo "11. Checking disk space..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 90 ]]; then
    log_error "Disk usage is ${DISK_USAGE}% - critically high"
elif [[ $DISK_USAGE -gt 80 ]]; then
    log_warning "Disk usage is ${DISK_USAGE}% - getting high"
else
    log_success "Disk usage is ${DISK_USAGE}% - acceptable"
fi

# 12. Check memory usage
echo ""
echo "12. Checking memory usage..."
if command -v free >/dev/null 2>&1; then
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $MEMORY_USAGE -gt 90 ]]; then
        log_error "Memory usage is ${MEMORY_USAGE}% - critically high"
    elif [[ $MEMORY_USAGE -gt 80 ]]; then
        log_warning "Memory usage is ${MEMORY_USAGE}% - getting high"
    else
        log_success "Memory usage is ${MEMORY_USAGE}% - acceptable"
    fi
else
    log_warning "Cannot check memory usage (free command not available)"
fi

# 13. Check for debug code
echo ""
echo "13. Checking for debug code..."
DEBUG_FILES=()

# Check JavaScript files for console.log
JS_DEBUG=$(find frontend/src -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" 2>/dev/null | \
           grep -v -E "(test|spec)" | \
           xargs grep -l "console\.log" 2>/dev/null || true)

if [[ -n "$JS_DEBUG" ]]; then
    log_error "console.log found in JavaScript files"
    DEBUG_FILES+=($JS_DEBUG)
else
    log_success "No console.log found in JavaScript files"
fi

# Check Python files for print statements
PY_DEBUG=$(find backend -name "*.py" 2>/dev/null | \
           grep -v -E "(test|venv|__pycache__)" | \
           xargs grep -l "print(" 2>/dev/null || true)

if [[ -n "$PY_DEBUG" ]]; then
    log_error "print() statements found in Python files"
    DEBUG_FILES+=($PY_DEBUG)
else
    log_success "No print() statements found in Python files"
fi

# Summary
echo ""
echo "=============================================="
echo "📊 VALIDATION SUMMARY"
echo "=============================================="

if [[ ${#ERRORS[@]} -eq 0 ]]; then
    log_success "All critical validations passed!"
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Critical errors that must be fixed:"
    for error in "${ERRORS[@]}"; do
        echo -e "  ${RED}• $error${NC}"
    done
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "Warnings (should be addressed):"
    for warning in "${WARNINGS[@]}"; do
        echo -e "  ${YELLOW}• $warning${NC}"
    done
fi

echo ""
echo "Validation completed with:"
echo "  - Errors: ${#ERRORS[@]}"
echo "  - Warnings: ${#WARNINGS[@]}"

if [[ "$VALIDATION_FAILED" == true ]]; then
    echo ""
    echo -e "${RED}🚨 PRODUCTION DEPLOYMENT BLOCKED${NC}"
    echo "Fix all errors before deploying to production."
    exit 1
else
    echo ""
    echo -e "${GREEN}🚀 PRODUCTION DEPLOYMENT APPROVED${NC}"
    echo "System is ready for production deployment."
    exit 0
fi