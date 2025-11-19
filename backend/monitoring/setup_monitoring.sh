#!/bin/bash

# AI-Lawyer Monitoring Stack Setup Script
# This script sets up Prometheus, Grafana, and AlertManager for the AI-Lawyer system

set -e

echo "🚀 Setting up AI-Lawyer Monitoring Stack..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create monitoring directory if it doesn't exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR"

echo "📁 Monitoring directory: $MONITORING_DIR"

# Ensure all configuration files exist
FILES=(
    "prometheus.yml"
    "prometheus_alerts.yml"
    "grafana_dashboard.json"
    "grafana_datasources.yml" 
    "grafana_dashboards.yml"
    "alertmanager.yml"
    "docker-compose.monitoring.yml"
)

echo "🔍 Checking configuration files..."
for file in "${FILES[@]}"; do
    if [[ ! -f "$MONITORING_DIR/$file" ]]; then
        echo "❌ Missing configuration file: $file"
        exit 1
    else
        echo "✅ Found: $file"
    fi
done

# Function to start monitoring stack
start_monitoring() {
    echo "🚀 Starting monitoring stack..."
    cd "$MONITORING_DIR"
    docker-compose -f docker-compose.monitoring.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check service health
    check_service_health
}

# Function to stop monitoring stack
stop_monitoring() {
    echo "🛑 Stopping monitoring stack..."
    cd "$MONITORING_DIR"
    docker-compose -f docker-compose.monitoring.yml down
}

# Function to restart monitoring stack
restart_monitoring() {
    echo "🔄 Restarting monitoring stack..."
    stop_monitoring
    sleep 5
    start_monitoring
}

# Function to check service health
check_service_health() {
    echo "🔍 Checking service health..."
    
    # Check Prometheus
    if curl -s http://localhost:9090/-/healthy &> /dev/null; then
        echo "✅ Prometheus is healthy (http://localhost:9090)"
    else
        echo "❌ Prometheus is not responding"
    fi
    
    # Check Grafana
    if curl -s http://localhost:3000/api/health &> /dev/null; then
        echo "✅ Grafana is healthy (http://localhost:3000)"
        echo "   Default login: admin/admin123"
    else
        echo "❌ Grafana is not responding"
    fi
    
    # Check AlertManager
    if curl -s http://localhost:9093/-/healthy &> /dev/null; then
        echo "✅ AlertManager is healthy (http://localhost:9093)"
    else
        echo "❌ AlertManager is not responding"
    fi
    
    # Check Node Exporter
    if curl -s http://localhost:9100/metrics &> /dev/null; then
        echo "✅ Node Exporter is healthy (http://localhost:9100)"
    else
        echo "❌ Node Exporter is not responding"
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Showing monitoring stack logs..."
    cd "$MONITORING_DIR"
    docker-compose -f docker-compose.monitoring.yml logs -f
}

# Function to update monitoring stack
update_monitoring() {
    echo "🔄 Updating monitoring stack..."
    cd "$MONITORING_DIR"
    docker-compose -f docker-compose.monitoring.yml pull
    restart_monitoring
}

# Function to show status
show_status() {
    echo "📊 Monitoring Stack Status:"
    cd "$MONITORING_DIR"
    docker-compose -f docker-compose.monitoring.yml ps
    echo ""
    check_service_health
}

# Function to backup configuration
backup_config() {
    BACKUP_DIR="./monitoring_backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 Creating backup in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$MONITORING_DIR"/*.yml "$MONITORING_DIR"/*.json "$BACKUP_DIR/"
    echo "✅ Backup created successfully"
}

# Function to test AI-Lawyer metrics endpoint
test_metrics() {
    echo "🧪 Testing AI-Lawyer metrics endpoint..."
    if curl -s http://localhost:8000/metrics &> /dev/null; then
        echo "✅ AI-Lawyer metrics endpoint is responding"
        echo "📊 Sample metrics:"
        curl -s http://localhost:8000/metrics | head -20
    else
        echo "❌ AI-Lawyer metrics endpoint is not responding"
        echo "   Make sure the AI-Lawyer backend is running on port 8000"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "🔧 AI-Lawyer Monitoring Stack Management"
    echo "======================================="
    echo "1) Start monitoring stack"
    echo "2) Stop monitoring stack" 
    echo "3) Restart monitoring stack"
    echo "4) Show status"
    echo "5) Show logs"
    echo "6) Update stack"
    echo "7) Test AI-Lawyer metrics"
    echo "8) Backup configuration"
    echo "9) Health check"
    echo "0) Exit"
    echo ""
}

# Process command line arguments
case "${1:-menu}" in
    "start")
        start_monitoring
        ;;
    "stop")
        stop_monitoring
        ;;
    "restart")
        restart_monitoring
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "update")
        update_monitoring
        ;;
    "test")
        test_metrics
        ;;
    "backup")
        backup_config
        ;;
    "health")
        check_service_health
        ;;
    "menu"|*)
        while true; do
            show_menu
            read -p "Select an option [0-9]: " choice
            case $choice in
                1) start_monitoring ;;
                2) stop_monitoring ;;
                3) restart_monitoring ;;
                4) show_status ;;
                5) show_logs ;;
                6) update_monitoring ;;
                7) test_metrics ;;
                8) backup_config ;;
                9) check_service_health ;;
                0) echo "👋 Goodbye!"; exit 0 ;;
                *) echo "❌ Invalid option. Please try again." ;;
            esac
            echo ""
            read -p "Press Enter to continue..."
        done
        ;;
esac