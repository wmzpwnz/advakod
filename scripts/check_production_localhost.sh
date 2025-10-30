#!/bin/bash

# Production-focused localhost check
# Only flags localhost usage that would break production deployment

echo "🔍 Checking for production-breaking localhost references..."

LOCALHOST_FOUND=false
ERRORS=()

# Critical configuration files that must not have localhost in production
CRITICAL_FILES=(
    "docker-compose.prod.yml"
    ".env.production"
    "nginx.conf"
)

# Check critical files for localhost references
for file in "${CRITICAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # Look for actual localhost usage in configuration values (excluding health checks)
        MATCHES=$(grep -n -E "(localhost|127\.0\.0\.1)" "$file" | grep -v -E "^[[:space:]]*#|comment|Comment|healthcheck|health|test.*localhost")
        
        if [[ -n "$MATCHES" ]]; then
            # Filter out acceptable cases
            FILTERED_MATCHES=""
            while IFS= read -r line; do
                # Skip comments and documentation
                if [[ "$line" =~ ^[[:space:]]*# ]] || [[ "$line" =~ comment ]] || [[ "$line" =~ Comment ]]; then
                    continue
                fi
                
                # Skip if it's in a comment explaining Docker service names
                if [[ "$line" =~ "Docker service names" ]] || [[ "$line" =~ "вместо localhost" ]]; then
                    continue
                fi
                
                FILTERED_MATCHES+="$line"$'\n'
            done <<< "$MATCHES"
            
            if [[ -n "$FILTERED_MATCHES" ]]; then
                echo "❌ Found production-breaking localhost references in $file:"
                echo "$FILTERED_MATCHES"
                ERRORS+=("$file")
                LOCALHOST_FOUND=true
            fi
        fi
    fi
done

# Check for hardcoded localhost in environment variables
ENV_FILES=(".env" ".env.production" "backend/.env")
for file in "${ENV_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # Look for environment variable assignments with localhost
        MATCHES=$(grep -n -E "^[A-Z_]+=.*localhost|^[A-Z_]+=.*127\.0\.0\.1" "$file")
        
        if [[ -n "$MATCHES" ]]; then
            echo "❌ Found localhost in environment variables in $file:"
            echo "$MATCHES"
            ERRORS+=("$file")
            LOCALHOST_FOUND=true
        fi
    fi
done

# Check Docker Compose service configurations
COMPOSE_FILES=("docker-compose.yml" "docker-compose.prod.yml")
for file in "${COMPOSE_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # Look for localhost in service configurations (excluding health checks)
        MATCHES=$(grep -n -E "server.*localhost|host.*localhost|url.*localhost" "$file" | grep -v -E "healthcheck|health|test.*localhost")
        
        if [[ -n "$MATCHES" ]]; then
            echo "❌ Found localhost in Docker service configuration in $file:"
            echo "$MATCHES"
            ERRORS+=("$file")
            LOCALHOST_FOUND=true
        fi
    fi
done

if [[ "$LOCALHOST_FOUND" == true ]]; then
    echo ""
    echo "🚨 PRODUCTION DEPLOYMENT BLOCKED!"
    echo ""
    echo "Critical localhost references found that will break production:"
    for error_file in "${ERRORS[@]}"; do
        echo "  - $error_file"
    done
    echo ""
    echo "Fix these issues before deploying to production."
    echo ""
    exit 1
else
    echo "✅ No production-breaking localhost references found"
    echo "🚀 Ready for production deployment!"
    exit 0
fi