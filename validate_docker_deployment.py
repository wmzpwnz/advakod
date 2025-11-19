#!/usr/bin/env python3
"""
Docker Deployment Validation Script
Validates Docker services and container health for ADVAKOD system
"""

import subprocess
import json
import time
import sys
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    NOT_FOUND = "not_found"
    ERROR = "error"

@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    container_id: str
    image: str
    ports: List[str]
    health_check: Optional[str]
    uptime: str
    message: str

class DockerValidator:
    """Docker deployment validator"""
    
    def __init__(self, compose_file: str = "docker-compose.prod.yml"):
        self.compose_file = compose_file
        self.services: List[ServiceInfo] = []
        
        # Expected services for production
        self.expected_services = [
            "nginx",
            "postgres", 
            "qdrant",
            "redis",
            "backend",
            "celery_worker",
            "celery_beat",
            "frontend"
        ]
    
    def run_command(self, command: List[str]) -> tuple[bool, str]:
        """Run shell command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)
    
    def check_docker_compose_status(self) -> bool:
        """Check if Docker Compose services are running"""
        logger.info("🐳 Checking Docker Compose services...")
        
        success, output = self.run_command([
            "docker-compose", "-f", self.compose_file, "ps", "--format", "json"
        ])
        
        if not success:
            logger.error(f"Failed to get Docker Compose status: {output}")
            return False
        
        try:
            # Parse JSON output
            containers = []
            for line in output.split('\n'):
                if line.strip():
                    containers.append(json.loads(line))
            
            # Check each expected service
            for service_name in self.expected_services:
                container_info = next(
                    (c for c in containers if c.get('Service') == service_name),
                    None
                )
                
                if container_info:
                    state = container_info.get('State', 'unknown')
                    health = container_info.get('Health', 'no healthcheck')
                    
                    if state == 'running':
                        if health == 'healthy' or health == 'no healthcheck':
                            status = ServiceStatus.HEALTHY
                            message = f"Running and {health}"
                        else:
                            status = ServiceStatus.UNHEALTHY
                            message = f"Running but {health}"
                    elif state == 'restarting':
                        status = ServiceStatus.STARTING
                        message = "Restarting"
                    else:
                        status = ServiceStatus.UNHEALTHY
                        message = f"State: {state}"
                    
                    service_info = ServiceInfo(
                        name=service_name,
                        status=status,
                        container_id=container_info.get('ID', 'unknown')[:12],
                        image=container_info.get('Image', 'unknown'),
                        ports=container_info.get('Publishers', []),
                        health_check=health,
                        uptime=container_info.get('RunningFor', 'unknown'),
                        message=message
                    )
                else:
                    service_info = ServiceInfo(
                        name=service_name,
                        status=ServiceStatus.NOT_FOUND,
                        container_id="",
                        image="",
                        ports=[],
                        health_check=None,
                        uptime="",
                        message="Service not found"
                    )
                
                self.services.append(service_info)
                
                # Log service status
                status_emoji = {
                    ServiceStatus.HEALTHY: "✅",
                    ServiceStatus.UNHEALTHY: "❌",
                    ServiceStatus.STARTING: "🔄",
                    ServiceStatus.NOT_FOUND: "❓",
                    ServiceStatus.ERROR: "💥"
                }
                
                logger.info(f"{status_emoji[service_info.status]} {service_name}: {service_info.message}")
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Docker Compose output: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking Docker Compose status: {e}")
            return False
    
    def check_service_logs(self, service_name: str, lines: int = 50) -> Dict[str, Any]:
        """Check recent logs for a service"""
        success, output = self.run_command([
            "docker-compose", "-f", self.compose_file, 
            "logs", "--tail", str(lines), service_name
        ])
        
        if success:
            # Look for error patterns
            error_patterns = [
                "ERROR", "CRITICAL", "FATAL", "Exception", "Traceback",
                "failed", "timeout", "connection refused", "cannot connect"
            ]
            
            errors = []
            for line in output.split('\n'):
                line_lower = line.lower()
                for pattern in error_patterns:
                    if pattern.lower() in line_lower:
                        errors.append(line.strip())
                        break
            
            return {
                "success": True,
                "total_lines": len(output.split('\n')),
                "error_count": len(errors),
                "recent_errors": errors[-10:] if errors else [],  # Last 10 errors
                "has_errors": len(errors) > 0
            }
        else:
            return {
                "success": False,
                "error": output
            }
    
    def check_resource_usage(self) -> Dict[str, Any]:
        """Check Docker resource usage"""
        success, output = self.run_command([
            "docker", "stats", "--no-stream", "--format", 
            "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
        ])
        
        if success:
            lines = output.split('\n')[1:]  # Skip header
            resource_info = {}
            
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        container = parts[0]
                        cpu_perc = parts[1]
                        mem_usage = parts[2]
                        mem_perc = parts[3]
                        
                        resource_info[container] = {
                            "cpu_percent": cpu_perc,
                            "memory_usage": mem_usage,
                            "memory_percent": mem_perc
                        }
            
            return {
                "success": True,
                "containers": resource_info
            }
        else:
            return {
                "success": False,
                "error": output
            }
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity between services"""
        network_tests = []
        
        # Test internal network connectivity
        test_commands = [
            ("backend-to-postgres", ["docker-compose", "-f", self.compose_file, 
             "exec", "-T", "backend", "nc", "-z", "advakod_postgres", "5432"]),
            ("backend-to-redis", ["docker-compose", "-f", self.compose_file,
             "exec", "-T", "backend", "nc", "-z", "advakod_redis", "6379"]),
            ("backend-to-qdrant", ["docker-compose", "-f", self.compose_file,
             "exec", "-T", "backend", "nc", "-z", "advakod_qdrant", "6333"]),
        ]
        
        for test_name, command in test_commands:
            success, output = self.run_command(command)
            network_tests.append({
                "test": test_name,
                "success": success,
                "message": "Connected" if success else f"Failed: {output}"
            })
        
        return {
            "tests": network_tests,
            "all_passed": all(test["success"] for test in network_tests)
        }
    
    def validate_deployment(self) -> Dict[str, Any]:
        """Run complete Docker deployment validation"""
        logger.info("🚀 Starting Docker Deployment Validation")
        logger.info(f"Compose file: {self.compose_file}")
        
        start_time = time.time()
        
        # Check Docker Compose status
        compose_ok = self.check_docker_compose_status()
        
        # Analyze service health
        healthy_services = len([s for s in self.services if s.status == ServiceStatus.HEALTHY])
        unhealthy_services = len([s for s in self.services if s.status == ServiceStatus.UNHEALTHY])
        missing_services = len([s for s in self.services if s.status == ServiceStatus.NOT_FOUND])
        
        # Check logs for critical services
        log_analysis = {}
        critical_services = ["backend", "nginx", "postgres"]
        
        for service in critical_services:
            if any(s.name == service and s.status != ServiceStatus.NOT_FOUND for s in self.services):
                log_analysis[service] = self.check_service_logs(service)
        
        # Check resource usage
        resource_usage = self.check_resource_usage()
        
        # Check network connectivity
        network_status = self.check_network_connectivity()
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = {
            "deployment_status": "healthy" if (healthy_services >= 6 and unhealthy_services == 0) else 
                               "degraded" if (healthy_services >= 4) else "unhealthy",
            "services": {
                "total": len(self.services),
                "healthy": healthy_services,
                "unhealthy": unhealthy_services,
                "missing": missing_services,
                "details": [
                    {
                        "name": s.name,
                        "status": s.status.value,
                        "container_id": s.container_id,
                        "image": s.image,
                        "uptime": s.uptime,
                        "message": s.message,
                        "health_check": s.health_check
                    }
                    for s in self.services
                ]
            },
            "logs": log_analysis,
            "resources": resource_usage,
            "network": network_status,
            "validation_duration": total_duration,
            "timestamp": time.time()
        }
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("📊 DOCKER VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Deployment Status: {summary['deployment_status'].upper()}")
        logger.info(f"Services: {healthy_services} healthy, {unhealthy_services} unhealthy, {missing_services} missing")
        
        if network_status["all_passed"]:
            logger.info("✅ Network connectivity: All tests passed")
        else:
            logger.info("❌ Network connectivity: Some tests failed")
        
        # Log service details
        for service in self.services:
            status_emoji = {
                ServiceStatus.HEALTHY: "✅",
                ServiceStatus.UNHEALTHY: "❌", 
                ServiceStatus.STARTING: "🔄",
                ServiceStatus.NOT_FOUND: "❓"
            }
            logger.info(f"  {status_emoji[service.status]} {service.name}: {service.message}")
        
        # Log critical errors from logs
        for service_name, log_info in log_analysis.items():
            if log_info.get("has_errors"):
                logger.warning(f"⚠️  {service_name} has {log_info['error_count']} errors in recent logs")
        
        logger.info(f"⏱️  Validation completed in {total_duration:.2f}s")
        
        return summary
    
    def save_report(self, summary: Dict[str, Any], filename: str = "docker_validation_report.json"):
        """Save validation report"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Docker validation report saved to {filename}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ADVAKOD Docker Deployment Validator")
    parser.add_argument("--compose-file", "-f", default="docker-compose.prod.yml",
                       help="Docker Compose file to validate (default: docker-compose.prod.yml)")
    parser.add_argument("--report", default="docker_validation_report.json",
                       help="Output report filename")
    
    args = parser.parse_args()
    
    validator = DockerValidator(args.compose_file)
    summary = validator.validate_deployment()
    validator.save_report(summary, args.report)
    
    # Exit with appropriate code
    if summary["deployment_status"] == "healthy":
        sys.exit(0)
    elif summary["deployment_status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()