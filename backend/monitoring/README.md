# AI-Lawyer Monitoring & Observability Guide

## 📊 Overview

This comprehensive monitoring stack provides full observability for the AI-Lawyer system using:
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alert routing and notifications
- **Node Exporter** - System metrics
- **Redis Exporter** - Redis metrics
- **cAdvisor** - Container metrics

## 🚀 Quick Start

1. **Start the monitoring stack:**
   ```bash
   cd backend/monitoring
   ./setup_monitoring.sh start
   ```

2. **Access the services:**
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
   - **Prometheus**: http://localhost:9090
   - **AlertManager**: http://localhost:9093

3. **Check system health:**
   ```bash
   ./setup_monitoring.sh health
   ```

## 📋 Available Scripts

| Command | Description |
|---------|-------------|
| `./setup_monitoring.sh start` | Start monitoring stack |
| `./setup_monitoring.sh stop` | Stop monitoring stack |
| `./setup_monitoring.sh restart` | Restart monitoring stack |
| `./setup_monitoring.sh status` | Show service status |
| `./setup_monitoring.sh logs` | Show service logs |
| `./setup_monitoring.sh test` | Test AI-Lawyer metrics endpoint |
| `./setup_monitoring.sh health` | Health check all services |
| `./setup_monitoring.sh backup` | Backup configuration |

## 📊 Key Metrics

### HTTP Metrics
- `ai_lawyer_http_requests_total` - Total HTTP requests
- `ai_lawyer_http_request_duration_seconds` - Request latency
- `ai_lawyer_http_requests_in_flight` - Concurrent requests

### AI/ML Metrics
- `ai_lawyer_ai_inference_requests_total` - AI inference requests
- `ai_lawyer_ai_inference_duration_seconds` - Inference latency
- `ai_lawyer_ai_tokens_generated_total` - Tokens generated
- `ai_lawyer_ai_tokens_generated_per_second` - Token generation rate

### Rate Limiting Metrics
- `ai_lawyer_rate_limit_allowed_total` - Allowed requests
- `ai_lawyer_rate_limit_blocked_total` - Blocked requests
- `ai_lawyer_rate_limit_tokens_remaining` - Remaining tokens
- `ai_lawyer_rate_limit_queue_size` - Queue size

### Cache Metrics
- `ai_lawyer_cache_hits_total` - Cache hits
- `ai_lawyer_cache_misses_total` - Cache misses
- `ai_lawyer_cache_size_bytes` - Cache size
- `ai_lawyer_cache_evictions_total` - Cache evictions

### Database Metrics
- `ai_lawyer_database_connections_active` - Active connections
- `ai_lawyer_database_query_duration_seconds` - Query latency
- `ai_lawyer_database_operations_total` - Database operations

### Vector Store Metrics
- `ai_lawyer_vector_store_operations_total` - Vector operations
- `ai_lawyer_vector_store_duration_seconds` - Operation latency
- `ai_lawyer_vector_store_documents_total` - Document count

### Business Metrics
- `ai_lawyer_chat_sessions_total` - Chat sessions
- `ai_lawyer_legal_queries_total` - Legal queries
- `ai_lawyer_document_analysis_total` - Document analyses
- `ai_lawyer_user_registrations_total` - User registrations

### System Metrics
- `ai_lawyer_system_cpu_usage_percent` - CPU usage
- `ai_lawyer_system_memory_usage_percent` - Memory usage
- `ai_lawyer_system_disk_usage_percent` - Disk usage

## 🚨 Alerting Rules

### Critical Alerts
- **Service Down** - Service unavailable for >1 minute
- **High Error Rate** - Error rate >5% for 2 minutes
- **AI Inference Errors** - AI error rate >10% for 2 minutes
- **Vector Store Errors** - Vector store error rate >5% for 2 minutes
- **Low Disk Space** - Disk usage >90% for 5 minutes

### Warning Alerts
- **High Response Time** - 95th percentile >5s for 3 minutes
- **AI Latency High** - AI inference >30s for 2 minutes
- **High CPU Usage** - CPU >80% for 5 minutes
- **High Memory Usage** - Memory >85% for 3 minutes
- **Low Cache Hit Rate** - Cache hit rate <70% for 5 minutes

### Info Alerts
- **Low Activity** - Chat sessions <0.1/hour for 30 minutes

## 📈 Grafana Dashboard

The included dashboard provides:

1. **Overview Panel**
   - Request rate, response time, AI inference rate, cache hit rate

2. **HTTP Performance**
   - Requests by status code, response time percentiles

3. **AI/ML Performance**
   - Model response times, inference rates, token generation

4. **Rate Limiting**
   - Blocked vs allowed requests, token availability

5. **System Resources**
   - CPU, memory, disk usage over time

6. **Vector Store Operations**
   - Search and insert operations, latencies

7. **Business Metrics**
   - Chat sessions, legal queries, document analyses

## 🔧 Configuration

### Prometheus Configuration
- **Location**: `monitoring/prometheus.yml`
- **Scrape Interval**: 15s
- **Retention**: 30 days
- **Targets**: AI-Lawyer backend, system metrics, Redis

### Grafana Configuration
- **Default Login**: admin/admin123
- **Datasource**: Prometheus (auto-configured)
- **Dashboard**: AI-Lawyer Performance Dashboard (auto-imported)

### AlertManager Configuration
- **Location**: `monitoring/alertmanager.yml`
- **Email Alerts**: Configure SMTP settings
- **Webhook Alerts**: Configure webhook URL and token

## 🔍 Troubleshooting

### Common Issues

1. **AI-Lawyer metrics not available**
   ```bash
   # Check if AI-Lawyer is running
   curl http://localhost:8000/health
   
   # Check metrics endpoint
   curl http://localhost:8000/metrics
   ```

2. **Prometheus not scraping**
   ```bash
   # Check Prometheus targets
   # Go to http://localhost:9090/targets
   ```

3. **Grafana dashboard not loading**
   ```bash
   # Check Grafana logs
   docker logs ai-lawyer-grafana
   ```

4. **Alerts not firing**
   ```bash
   # Check AlertManager status
   # Go to http://localhost:9093
   ```

### Log Locations
- **Prometheus**: `docker logs ai-lawyer-prometheus`
- **Grafana**: `docker logs ai-lawyer-grafana`
- **AlertManager**: `docker logs ai-lawyer-alertmanager`

## 🔐 Security Considerations

1. **Change default passwords** in production
2. **Configure TLS** for external access
3. **Set up authentication** for Grafana
4. **Restrict network access** to monitoring services
5. **Use secure SMTP** for alert emails

## 📊 Performance Tuning

1. **Prometheus Storage**
   - Adjust retention time based on disk space
   - Use remote storage for long-term retention

2. **Scrape Intervals**
   - Reduce for less critical metrics
   - Increase for high-frequency metrics

3. **Alert Thresholds**
   - Tune based on baseline performance
   - Avoid alert fatigue with proper thresholds

## 🚀 Production Deployment

### High Availability Setup
1. **Multiple Prometheus replicas**
2. **Grafana with external database**
3. **AlertManager clustering**
4. **Load balancer for Grafana**

### Backup Strategy
1. **Automated configuration backups**
2. **Prometheus data backups**
3. **Grafana dashboard exports**

### Monitoring Best Practices
1. **Set up SLA dashboards**
2. **Create runbooks for alerts**
3. **Regular monitoring stack health checks**
4. **Performance baseline documentation**

## 📞 Support

For monitoring issues:
1. Check logs using `./setup_monitoring.sh logs`
2. Verify service health with `./setup_monitoring.sh health`
3. Backup configuration before changes: `./setup_monitoring.sh backup`
4. Test metrics endpoint: `./setup_monitoring.sh test`

## 🔄 Maintenance

### Regular Tasks
- [ ] Review and tune alert thresholds
- [ ] Clean up old metrics and logs
- [ ] Update monitoring stack: `./setup_monitoring.sh update`
- [ ] Backup configurations: `./setup_monitoring.sh backup`
- [ ] Review dashboard usage and optimize