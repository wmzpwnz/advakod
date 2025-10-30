#!/bin/bash

# Enhanced CI blocker script to prevent localhost usage in production code
# This prevents deployment with localhost references and enforces production standards

echo "🔍 Enhanced CI Check: Scanning for localhost references and production violations..."

# Configuration files to check
CONFIG_FILES=(
    ".env"
    ".env.production" 
    "backend/.env"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "nginx.conf"
    "nginx_fixed.conf"
    "frontend/.env"
    "frontend/.env.production"
    "frontend/src/config.js"
    "frontend/src/config.ts"
    "backend/app/core/config.py"
    "backend/main.py"
)

LOCALHOST_FOUND=false
FALLBACK_FOUND=false
DEBUG_CODE_FOUND=false
ERRORS=()
FALLBACK_ERRORS=()
DEBUG_ERRORS=()

# Check each configuration file for localhost references
for file in "${CONFIG_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # Check for localhost, 127.0.0.1, but exclude comments and allowed development contexts
        MATCHES=$(grep -n -E "(localhost|127\.0\.0\.1)" "$file" | grep -v -E "^[[:space:]]*#|//.*localhost|/\*.*localhost.*\*/|# .*localhost|comment.*localhost|development.*localhost|ENVIRONMENT.*development")
        
        if [[ -n "$MATCHES" ]]; then
            echo "❌ Found localhost references in $file:"
            echo "$MATCHES"
            ERRORS+=("$file")
            LOCALHOST_FOUND=true
        fi
        
        # Check for localhost fallback values in environment variables
        FALLBACK_MATCHES=$(grep -n -E "(default.*localhost|fallback.*localhost|or.*localhost|localhost.*default)" "$file" | grep -v -E "^[[:space:]]*#|//.*|/\*.*\*/")
        
        if [[ -n "$FALLBACK_MATCHES" ]]; then
            echo "⚠️  Found localhost fallback values in $file:"
            echo "$FALLBACK_MATCHES"
            FALLBACK_ERRORS+=("$file")
            FALLBACK_FOUND=true
        fi
    fi
done

# Check JavaScript/TypeScript files for hardcoded localhost and debug code
JS_FILES=$(find frontend/src -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" 2>/dev/null)
for file in $JS_FILES; do
    if [[ -f "$file" ]]; then
        # Check for localhost references (excluding comments, development code, and whitelist definitions)
        MATCHES=$(grep -n -E "(localhost|127\.0\.0\.1)" "$file" | grep -v -E "//.*localhost|/\*.*localhost.*\*/|# .*localhost|comment.*localhost|development.*localhost|test.*localhost|domain_whitelist|whitelist.*localhost|allowed.*localhost")
        
        if [[ -n "$MATCHES" ]]; then
            echo "❌ Found localhost references in $file:"
            echo "$MATCHES"
            ERRORS+=("$file")
            LOCALHOST_FOUND=true
        fi
        
        # Check for debug code (console.log, debugger, alert)
        DEBUG_MATCHES=$(grep -n -E "(console\.log|console\.debug|debugger|alert\(|confirm\(|prompt\()" "$file" | grep -v -E "//.*console|/\*.*console.*\*/|test.*console|\.test\.|\.spec\.")
        
        if [[ -n "$DEBUG_MATCHES" ]]; then
            echo "🐛 Found debug code in $file:"
            echo "$DEBUG_MATCHES"
            DEBUG_ERRORS+=("$file")
            DEBUG_CODE_FOUND=true
        fi
        
        # Check for localhost fallback values
        FALLBACK_MATCHES=$(grep -n -E "(localhost.*\|\||default.*localhost|fallback.*localhost)" "$file" | grep -v -E "//.*|/\*.*\*/|test.*|\.test\.|\.spec\.")
        
        if [[ -n "$FALLBACK_MATCHES" ]]; then
            echo "⚠️  Found localhost fallback values in $file:"
            echo "$FALLBACK_MATCHES"
            FALLBACK_ERRORS+=("$file")
            FALLBACK_FOUND=true
        fi
    fi
done

# Check Python files for localhost and debug code (excluding venv and test files)
PY_FILES=$(find backend -name "*.py" -not -path "*/venv/*" -not -path "*/test*" -not -path "*/__pycache__/*" 2>/dev/null)
for file in $PY_FILES; do
    if [[ -f "$file" ]]; then
        # Check for localhost references (exclude domain whitelist definitions, IP whitelist checks, and comments)
        MATCHES=$(grep -n -E "(localhost|127\.0\.0\.1)" "$file" | grep -v -E "^[[:space:]]*#.*localhost|# .*localhost|comment.*localhost|development.*localhost|ENVIRONMENT.*development|test.*localhost|domain_whitelist\.py|DEVELOPMENT_DOMAINS|whitelist.*localhost|allowed.*localhost|ip_str.*localhost|client_ip.*127\.0\.0\.1|block_localhost_in_production")
        
        if [[ -n "$MATCHES" ]]; then
            echo "❌ Found localhost references in $file:"
            echo "$MATCHES"
            ERRORS+=("$file")
            LOCALHOST_FOUND=true
        fi
        
        # Check for debug code (print statements, pdb)
        DEBUG_MATCHES=$(grep -n -E "(print\(|pdb\.set_trace|breakpoint\(|import pdb)" "$file" | grep -v -E "^[[:space:]]*#|# .*|logger\.|logging\.|test.*|\.test\.|_test\.py")
        
        if [[ -n "$DEBUG_MATCHES" ]]; then
            echo "🐛 Found debug code in $file:"
            echo "$DEBUG_MATCHES"
            DEBUG_ERRORS+=("$file")
            DEBUG_CODE_FOUND=true
        fi
        
        # Check for localhost fallback values in Python
        FALLBACK_MATCHES=$(grep -n -E "(localhost.*or |default.*localhost|fallback.*localhost|getenv.*localhost)" "$file" | grep -v -E "^[[:space:]]*#|# .*|test.*|ENVIRONMENT.*development")
        
        if [[ -n "$FALLBACK_MATCHES" ]]; then
            echo "⚠️  Found localhost fallback values in $file:"
            echo "$FALLBACK_MATCHES"
            FALLBACK_ERRORS+=("$file")
            FALLBACK_FOUND=true
        fi
    fi
done

# Check for hardcoded production URLs that should use environment variables
HARDCODED_URLS=$(find frontend/src backend -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.py" 2>/dev/null | xargs grep -l "advacodex\.com" | grep -v -E "test|spec|\.test\.|_test\.")

if [[ -n "$HARDCODED_URLS" ]]; then
    echo "⚠️  Found hardcoded production URLs (should use environment variables):"
    for url_file in $HARDCODED_URLS; do
        echo "  - $url_file"
        grep -n "advacodex\.com" "$url_file" | head -3
    done
    echo ""
fi

# Summary and exit logic
ISSUES_FOUND=false

if [[ "$LOCALHOST_FOUND" == true ]]; then
    echo ""
    echo "🚨 CRITICAL: localhost references found!"
    echo "Files with localhost issues:"
    for error_file in "${ERRORS[@]}"; do
        echo "  - $error_file"
    done
    ISSUES_FOUND=true
fi

if [[ "$FALLBACK_FOUND" == true ]]; then
    echo ""
    echo "⚠️  WARNING: localhost fallback values found!"
    echo "Files with fallback issues:"
    for fallback_file in "${FALLBACK_ERRORS[@]}"; do
        echo "  - $fallback_file"
    done
    ISSUES_FOUND=true
fi

if [[ "$DEBUG_CODE_FOUND" == true ]]; then
    echo ""
    echo "🐛 WARNING: debug code found in production files!"
    echo "Files with debug code:"
    for debug_file in "${DEBUG_ERRORS[@]}"; do
        echo "  - $debug_file"
    done
    ISSUES_FOUND=true
fi

if [[ "$ISSUES_FOUND" == true ]]; then
    echo ""
    echo "🚨 DEPLOYMENT BLOCKED: Issues found that must be fixed!"
    echo ""
    echo "Required fixes:"
    echo "  1. Replace localhost/127.0.0.1 with proper Docker service names:"
    echo "     - Database: postgres"
    echo "     - Redis: redis"
    echo "     - Qdrant: qdrant"
    echo "     - Backend: backend"
    echo "     - Frontend: frontend"
    echo "     - Nginx: nginx"
    echo ""
    echo "  2. Remove localhost fallback values - use strict environment variables"
    echo "  3. Remove debug code (console.log, print, debugger, pdb)"
    echo "  4. Use environment variables instead of hardcoded URLs"
    echo ""
    exit 1
else
    echo ""
    echo "✅ All checks passed!"
    echo "✅ No localhost references found"
    echo "✅ No localhost fallbacks found"
    echo "✅ No debug code found"
    echo "🚀 Ready for deployment!"
    exit 0
fi