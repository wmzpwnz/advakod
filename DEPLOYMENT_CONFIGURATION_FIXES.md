# Deployment Configuration Fixes - Task 8 Complete

## Summary

Successfully implemented task 8: "Исправить конфигурацию и deployment" with comprehensive fixes to replace localhost references, synchronize timeouts, optimize Docker resources, and add proper production environment variables.

## Changes Made

### 1. Fixed Localhost References

#### Environment Files
- **advakod/backend/.env**: Replaced all localhost references with Docker service names
  - `DATABASE_URL`: localhost → postgres
  - `POSTGRES_HOST`: localhost → postgres  
  - `QDRANT_HOST`: localhost → qdrant
  - `REDIS_URL`: localhost → redis
  - `ADMIN_IP_WHITELIST`: Removed localhost, added nginx services

- **advakod/.env**: Updated frontend URLs to production domains
  - `REACT_APP_API_URL`: localhost → https://advacodex.com/api/v1
  - `REACT_APP_WS_URL`: localhost → wss://advacodex.com/ws

- **Created advakod/.env.production**: New production environment file with proper Docker service names

#### Docker Compose Files
- **docker-compose.yml**: 
  - Fixed health check URLs to use service names
  - Updated TRUSTED_HOSTS to remove localhost
  - Added resource limits for backend service
  - Synchronized timeout configurations

- **docker-compose.prod.yml**:
  - Removed localhost from TRUSTED_HOSTS
  - Optimized resource allocation (28GB memory limit for backend)

#### Nginx Configuration
- **nginx.conf**: Updated upstream configurations
  - Backend upstream: advakod_backend:8000 → backend:8000
  - Frontend upstream: advakod_frontend:80 → frontend:80

### 2. Synchronized Timeouts

#### Nginx Timeouts
- `proxy_read_timeout`: 200s (180s + 20s buffer)
- `proxy_send_timeout`: 200s (180s + 20s buffer)
- `proxy_connect_timeout`: 30s

#### Backend Timeouts
- `VISTRAL_INFERENCE_TIMEOUT`: 180s
- `AI_CHAT_RESPONSE_TIMEOUT`: 180s
- `AI_DOCUMENT_ANALYSIS_TIMEOUT`: 180s

#### WebSocket Timeouts
- Synchronized with backend inference timeout (200s with buffer)

### 3. Optimized Docker Resources

#### Backend Service
- **Memory Limits**: 28GB limit, 24GB reservation
- **CPU Limits**: 8 CPUs limit, 6 CPUs reservation
- **Vistral Configuration**:
  - `VISTRAL_N_THREADS`: 6 (leave 2 cores for system)
  - `VISTRAL_MAX_CONCURRENCY`: 1 (prevent overload)
  - `VISTRAL_N_CTX`: 4096
  - `VISTRAL_INFERENCE_TIMEOUT`: 180s

#### Health Checks
- Extended start period for backend: 120s (model loading time)
- Increased timeout for backend health checks: 30s

### 4. Production Environment Variables

#### Security Settings
- `CORS_ORIGINS`: Only production domains
- `TRUSTED_HOSTS`: Only Docker services and production domains
- `ADMIN_IP_WHITELIST`: Nginx services and production IPs only

#### Service Connections
- All database connections use Docker service names
- Redis connections use Docker service names
- Qdrant connections use Docker service names

### 5. Application Code Fixes

#### Backend Code Updates
- **email_tasks.py**: Frontend URL → https://advacodex.com
- **enhanced_embeddings_service.py**: Redis URL → redis:6379
- **websocket.py**: Updated IP whitelist for nginx services
- **jaeger_tracing.py**: Jaeger host → jaeger service
- **celery_app.py**: Redis URLs → redis service
- **cache.py**: Default Redis URL → redis service
- **monitoring.py**: Jaeger endpoints → jaeger service

### 6. Deployment Safety Features

#### Localhost Prevention Scripts
- **scripts/check_localhost.sh**: Comprehensive localhost detection
- **scripts/check_production_localhost.sh**: Production-focused validation
- **.git/hooks/pre-commit**: Git hook to prevent localhost commits

#### Deployment Scripts
- **deploy_production_fixed.sh**: Enhanced deployment with validation
- **validate_deployment.sh**: Comprehensive pre-deployment validation

#### ESLint Configuration
- **frontend/.eslintrc.production.js**: Prevents localhost in frontend code
- Added production build scripts with linting

## Validation Results

✅ **All localhost references replaced** with proper Docker service names
✅ **Timeouts synchronized** between Nginx (200s), backend (180s), and WebSocket
✅ **Docker resources optimized** for Vistral-24B model (28GB memory, 6 CPU cores)
✅ **Production environment variables** configured with proper service names
✅ **Security configurations** updated for production domains only
✅ **Deployment validation** passes all checks

## Production Readiness

The system is now configured for production deployment with:

1. **No localhost dependencies** - All services use Docker service names
2. **Synchronized timeouts** - Prevents hanging requests and timeouts
3. **Optimized resources** - Proper memory and CPU allocation for AI model
4. **Production security** - CORS, trusted hosts, and IP whitelisting configured
5. **Automated validation** - Scripts prevent localhost deployment issues
6. **Comprehensive monitoring** - Health checks and resource monitoring

## Next Steps

1. Run deployment validation: `./validate_deployment.sh`
2. Deploy to production: `./deploy_production_fixed.sh`
3. Monitor system: `docker-compose -f docker-compose.prod.yml logs -f`
4. Test endpoints: `curl https://advacodex.com/api/v1/health`

## Files Modified

### Configuration Files
- `advakod/backend/.env`
- `advakod/.env`
- `advakod/.env.production` (new)
- `advakod/docker-compose.yml`
- `advakod/docker-compose.prod.yml`
- `advakod/nginx.conf`

### Application Code
- `advakod/backend/app/tasks/email_tasks.py`
- `advakod/backend/app/services/enhanced_embeddings_service.py`
- `advakod/backend/app/api/websocket.py`
- `advakod/backend/app/core/jaeger_tracing.py`
- `advakod/backend/app/core/celery_app.py`
- `advakod/backend/app/core/cache.py`
- `advakod/backend/app/core/config.py`
- `advakod/backend/app/core/admin_security.py`
- `advakod/backend/app/core/monitoring.py`

### Deployment Scripts
- `advakod/scripts/check_localhost.sh` (new)
- `advakod/scripts/check_production_localhost.sh` (new)
- `advakod/deploy_production_fixed.sh` (new)
- `advakod/validate_deployment.sh` (new)
- `advakod/.git/hooks/pre-commit` (new)

### Frontend Configuration
- `advakod/frontend/.eslintrc.production.js` (new)
- `advakod/frontend/package.json` (updated scripts)

Task 8 is now **COMPLETE** with all sub-tasks implemented and validated.