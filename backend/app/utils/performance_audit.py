"""
Performance Audit Utility
Comprehensive performance analysis and optimization recommendations
"""

import asyncio
import time
import psutil
import gc
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import json

from sqlalchemy import text
from app.core.database import get_db
from app.core.admin_panel_metrics import admin_panel_metrics
from app.services.admin_cache_service import admin_cache_service

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    threshold: float
    status: str  # "good", "warning", "critical"
    recommendation: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class PerformanceAuditResult:
    """Performance audit result"""
    overall_score: float
    metrics: List[PerformanceMetric]
    recommendations: List[str]
    critical_issues: List[str]
    warnings: List[str]
    audit_timestamp: datetime
    execution_time: float

class PerformanceAuditor:
    """Comprehensive performance auditor for admin panel"""
    
    def __init__(self):
        self.thresholds = {
            # Response time thresholds (seconds)
            "api_response_time_p95": {"warning": 2.0, "critical": 5.0},
            "api_response_time_p99": {"warning": 5.0, "critical": 10.0},
            "database_query_time_p95": {"warning": 1.0, "critical": 3.0},
            
            # System resource thresholds (percentage)
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 80.0, "critical": 95.0},
            
            # Cache performance thresholds (percentage)
            "cache_hit_rate": {"warning": 70.0, "critical": 50.0},
            
            # Database performance thresholds
            "active_connections": {"warning": 80, "critical": 95},
            "slow_queries_per_minute": {"warning": 10, "critical": 50},
            
            # Admin panel specific thresholds
            "admin_error_rate": {"warning": 1.0, "critical": 5.0},
            "websocket_connections": {"warning": 500, "critical": 1000},
            "notification_queue_size": {"warning": 100, "critical": 500}
        }
    
    async def run_full_audit(self) -> PerformanceAuditResult:
        """Run comprehensive performance audit"""
        start_time = time.time()
        
        logger.info("Starting performance audit...")
        
        # Collect all metrics
        metrics = []
        
        # System metrics
        system_metrics = await self._audit_system_performance()
        metrics.extend(system_metrics)
        
        # Database metrics
        db_metrics = await self._audit_database_performance()
        metrics.extend(db_metrics)
        
        # Cache metrics
        cache_metrics = await self._audit_cache_performance()
        metrics.extend(cache_metrics)
        
        # API metrics
        api_metrics = await self._audit_api_performance()
        metrics.extend(api_metrics)
        
        # Admin panel specific metrics
        admin_metrics = await self._audit_admin_panel_performance()
        metrics.extend(admin_metrics)
        
        # Memory and garbage collection metrics
        memory_metrics = await self._audit_memory_performance()
        metrics.extend(memory_metrics)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics)
        
        # Categorize issues
        critical_issues = [m.name for m in metrics if m.status == "critical"]
        warnings = [m.name for m in metrics if m.status == "warning"]
        
        execution_time = time.time() - start_time
        
        result = PerformanceAuditResult(
            overall_score=overall_score,
            metrics=metrics,
            recommendations=recommendations,
            critical_issues=critical_issues,
            warnings=warnings,
            audit_timestamp=datetime.utcnow(),
            execution_time=execution_time
        )
        
        logger.info(f"Performance audit completed in {execution_time:.2f}s. Score: {overall_score:.1f}/100")
        
        return result
    
    async def _audit_system_performance(self) -> List[PerformanceMetric]:
        """Audit system-level performance"""
        metrics = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(self._create_metric(
                "cpu_usage", cpu_percent, "%",
                "System CPU utilization"
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics.append(self._create_metric(
                "memory_usage", memory.percent, "%",
                "System memory utilization"
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(self._create_metric(
                "disk_usage", disk_percent, "%",
                "System disk utilization"
            ))
            
            # Load average (Unix systems)
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
                cpu_count = psutil.cpu_count()
                load_percent = (load_avg / cpu_count) * 100
                metrics.append(self._create_metric(
                    "load_average", load_percent, "%",
                    "System load average"
                ))
            
        except Exception as e:
            logger.error(f"Error auditing system performance: {e}")
        
        return metrics
    
    async def _audit_database_performance(self) -> List[PerformanceMetric]:
        """Audit database performance"""
        metrics = []
        
        try:
            async for db in get_db():
                # Active connections
                result = await db.execute(text(
                    "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'"
                ))
                active_connections = result.scalar()
                
                metrics.append(PerformanceMetric(
                    name="database_active_connections",
                    value=active_connections,
                    unit="connections",
                    threshold=self.thresholds.get("active_connections", {}).get("warning", 80),
                    status=self._get_status("active_connections", active_connections),
                    recommendation="Monitor connection pooling and query optimization"
                ))
                
                # Slow queries
                result = await db.execute(text("""
                    SELECT count(*) as slow_queries 
                    FROM pg_stat_statements 
                    WHERE mean_time > 1000 
                    AND calls > 10
                """))
                slow_queries = result.scalar() or 0
                
                metrics.append(PerformanceMetric(
                    name="database_slow_queries",
                    value=slow_queries,
                    unit="queries",
                    threshold=self.thresholds.get("slow_queries_per_minute", {}).get("warning", 10),
                    status=self._get_status("slow_queries_per_minute", slow_queries),
                    recommendation="Optimize slow queries and add appropriate indexes"
                ))
                
                # Database size
                result = await db.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size"
                ))
                db_size = result.scalar()
                
                metrics.append(PerformanceMetric(
                    name="database_size",
                    value=0,  # Size in pretty format
                    unit="bytes",
                    threshold=0,
                    status="good",
                    recommendation=f"Database size: {db_size}"
                ))
                
                break  # Only need one connection
                
        except Exception as e:
            logger.error(f"Error auditing database performance: {e}")
        
        return metrics
    
    async def _audit_cache_performance(self) -> List[PerformanceMetric]:
        """Audit cache performance"""
        metrics = []
        
        try:
            cache_stats = admin_cache_service.get_cache_stats()
            
            # Cache hit rate
            hit_rate = cache_stats.get("hit_rate_percent", 0)
            metrics.append(self._create_metric(
                "cache_hit_rate", hit_rate, "%",
                "Cache hit rate performance"
            ))
            
            # Cache operations
            total_ops = cache_stats.get("total_operations", 0)
            metrics.append(PerformanceMetric(
                name="cache_total_operations",
                value=total_ops,
                unit="operations",
                threshold=0,
                status="good",
                recommendation=f"Total cache operations: {total_ops}"
            ))
            
            # Cache errors
            errors = cache_stats.get("errors", 0)
            error_rate = (errors / total_ops * 100) if total_ops > 0 else 0
            metrics.append(PerformanceMetric(
                name="cache_error_rate",
                value=error_rate,
                unit="%",
                threshold=1.0,
                status="critical" if error_rate > 5 else "warning" if error_rate > 1 else "good",
                recommendation="Investigate cache errors and connection issues"
            ))
            
        except Exception as e:
            logger.error(f"Error auditing cache performance: {e}")
        
        return metrics
    
    async def _audit_api_performance(self) -> List[PerformanceMetric]:
        """Audit API performance metrics"""
        metrics = []
        
        try:
            # This would integrate with your metrics collection system
            # For now, we'll simulate some metrics
            
            # API response times (would come from Prometheus)
            metrics.append(PerformanceMetric(
                name="api_response_time_p95",
                value=1.2,  # Simulated value
                unit="seconds",
                threshold=self.thresholds["api_response_time_p95"]["warning"],
                status=self._get_status("api_response_time_p95", 1.2),
                recommendation="Optimize slow API endpoints and add caching"
            ))
            
            # Error rate
            metrics.append(PerformanceMetric(
                name="api_error_rate",
                value=0.5,  # Simulated value
                unit="%",
                threshold=self.thresholds["admin_error_rate"]["warning"],
                status=self._get_status("admin_error_rate", 0.5),
                recommendation="Monitor and fix API errors"
            ))
            
        except Exception as e:
            logger.error(f"Error auditing API performance: {e}")
        
        return metrics
    
    async def _audit_admin_panel_performance(self) -> List[PerformanceMetric]:
        """Audit admin panel specific performance"""
        metrics = []
        
        try:
            # WebSocket connections (simulated)
            ws_connections = 25  # Would come from actual metrics
            metrics.append(self._create_metric(
                "websocket_connections", ws_connections, "connections",
                "Active WebSocket connections"
            ))
            
            # Notification queue size (simulated)
            queue_size = 15  # Would come from actual metrics
            metrics.append(self._create_metric(
                "notification_queue_size", queue_size, "items",
                "Pending notifications in queue"
            ))
            
        except Exception as e:
            logger.error(f"Error auditing admin panel performance: {e}")
        
        return metrics
    
    async def _audit_memory_performance(self) -> List[PerformanceMetric]:
        """Audit memory and garbage collection performance"""
        metrics = []
        
        try:
            # Python memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            metrics.append(PerformanceMetric(
                name="process_memory_rss",
                value=memory_info.rss / 1024 / 1024,  # MB
                unit="MB",
                threshold=1000,  # 1GB warning
                status="warning" if memory_info.rss > 1024*1024*1024 else "good",
                recommendation="Monitor memory usage and optimize data structures"
            ))
            
            # Garbage collection stats
            gc_stats = gc.get_stats()
            if gc_stats:
                total_collections = sum(stat['collections'] for stat in gc_stats)
                metrics.append(PerformanceMetric(
                    name="gc_total_collections",
                    value=total_collections,
                    unit="collections",
                    threshold=0,
                    status="good",
                    recommendation=f"Total GC collections: {total_collections}"
                ))
            
        except Exception as e:
            logger.error(f"Error auditing memory performance: {e}")
        
        return metrics
    
    def _create_metric(self, name: str, value: float, unit: str, description: str) -> PerformanceMetric:
        """Create a performance metric with status evaluation"""
        threshold_config = self.thresholds.get(name, {})
        warning_threshold = threshold_config.get("warning", 0)
        critical_threshold = threshold_config.get("critical", 0)
        
        status = self._get_status(name, value)
        recommendation = self._get_recommendation(name, value, status)
        
        return PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            threshold=warning_threshold,
            status=status,
            recommendation=recommendation
        )
    
    def _get_status(self, metric_name: str, value: float) -> str:
        """Determine metric status based on thresholds"""
        thresholds = self.thresholds.get(metric_name, {})
        warning = thresholds.get("warning", float('inf'))
        critical = thresholds.get("critical", float('inf'))
        
        # For cache hit rate, lower is worse
        if metric_name == "cache_hit_rate":
            if value < critical:
                return "critical"
            elif value < warning:
                return "warning"
            else:
                return "good"
        
        # For most metrics, higher is worse
        if value >= critical:
            return "critical"
        elif value >= warning:
            return "warning"
        else:
            return "good"
    
    def _get_recommendation(self, metric_name: str, value: float, status: str) -> str:
        """Get recommendation based on metric and status"""
        recommendations = {
            "cpu_usage": {
                "critical": "Immediate action required: Scale up resources or optimize CPU-intensive operations",
                "warning": "Monitor CPU usage and consider optimization",
                "good": "CPU usage is within acceptable limits"
            },
            "memory_usage": {
                "critical": "Critical memory usage: Add more RAM or optimize memory consumption",
                "warning": "High memory usage: Monitor and optimize memory-intensive operations",
                "good": "Memory usage is healthy"
            },
            "cache_hit_rate": {
                "critical": "Very low cache hit rate: Review caching strategy and TTL settings",
                "warning": "Low cache hit rate: Optimize cache keys and expiration policies",
                "good": "Cache performance is good"
            }
        }
        
        return recommendations.get(metric_name, {}).get(status, "Monitor this metric")
    
    def _calculate_overall_score(self, metrics: List[PerformanceMetric]) -> float:
        """Calculate overall performance score (0-100)"""
        if not metrics:
            return 0.0
        
        score_weights = {"good": 100, "warning": 60, "critical": 20}
        total_score = sum(score_weights.get(metric.status, 0) for metric in metrics)
        max_possible_score = len(metrics) * 100
        
        return (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0.0
    
    def _generate_recommendations(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        critical_metrics = [m for m in metrics if m.status == "critical"]
        warning_metrics = [m for m in metrics if m.status == "warning"]
        
        if critical_metrics:
            recommendations.append("🚨 CRITICAL ISSUES FOUND:")
            for metric in critical_metrics:
                recommendations.append(f"  • {metric.name}: {metric.recommendation}")
        
        if warning_metrics:
            recommendations.append("⚠️  WARNING ISSUES:")
            for metric in warning_metrics:
                recommendations.append(f"  • {metric.name}: {metric.recommendation}")
        
        # General recommendations
        if len(critical_metrics) == 0 and len(warning_metrics) == 0:
            recommendations.append("✅ System performance is good!")
        
        recommendations.extend([
            "",
            "📋 GENERAL RECOMMENDATIONS:",
            "  • Regularly monitor performance metrics",
            "  • Set up automated alerts for critical thresholds",
            "  • Review and optimize slow database queries",
            "  • Implement proper caching strategies",
            "  • Monitor resource usage trends over time"
        ])
        
        return recommendations

# Global instance
performance_auditor = PerformanceAuditor()

# Utility functions
async def run_performance_audit() -> Dict[str, Any]:
    """Run performance audit and return results as dict"""
    result = await performance_auditor.run_full_audit()
    return asdict(result)

async def get_performance_summary() -> Dict[str, Any]:
    """Get a quick performance summary"""
    try:
        # Quick system check
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return {"status": "error", "error": str(e)}