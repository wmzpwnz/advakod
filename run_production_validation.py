#!/usr/bin/env python3
"""
Complete Production Validation Runner
Orchestrates all validation tests for ADVAKOD production deployment
"""

import asyncio
import subprocess
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('production_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class ProductionValidationRunner:
    """Orchestrates complete production validation"""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 domain: str = "localhost", compose_file: str = "docker-compose.prod.yml"):
        self.base_url = base_url
        self.domain = domain
        self.compose_file = compose_file
        self.results = {}
        
    def run_command(self, command: List[str], cwd: str = None) -> tuple[bool, str]:
        """Run shell command"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=cwd
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timeout (5 minutes)"
        except Exception as e:
            return False, str(e)
    
    async def run_docker_validation(self) -> Dict[str, Any]:
        """Run Docker deployment validation"""
        logger.info("🐳 Running Docker Deployment Validation...")
        
        # Check if validation script exists
        docker_validator_path = Path("validate_docker_deployment.py")
        if not docker_validator_path.exists():
            return {
                "success": False,
                "error": "Docker validation script not found"
            }
        
        # Run Docker validation
        success, output = self.run_command([
            sys.executable, "validate_docker_deployment.py",
            "--compose-file", self.compose_file,
            "--report", "docker_validation_report.json"
        ])
        
        result = {
            "success": success,
            "output": output,
            "report_file": "docker_validation_report.json"
        }
        
        # Load detailed report if available
        if Path("docker_validation_report.json").exists():
            try:
                with open("docker_validation_report.json", 'r') as f:
                    result["detailed_report"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load Docker validation report: {e}")
        
        return result
    
    async def run_application_validation(self) -> Dict[str, Any]:
        """Run application-level validation"""
        logger.info("🚀 Running Application Validation...")
        
        # Check if validation script exists
        app_validator_path = Path("backend/validate_production_deployment.py")
        if not app_validator_path.exists():
            return {
                "success": False,
                "error": "Application validation script not found"
            }
        
        # Run application validation
        success, output = self.run_command([
            sys.executable, "backend/validate_production_deployment.py",
            "--url", self.base_url,
            "--domain", self.domain,
            "--report", "app_validation_report.json"
        ])
        
        result = {
            "success": success,
            "output": output,
            "report_file": "app_validation_report.json"
        }
        
        # Load detailed report if available
        if Path("app_validation_report.json").exists():
            try:
                with open("app_validation_report.json", 'r') as f:
                    result["detailed_report"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load application validation report: {e}")
        
        return result
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking Prerequisites...")
        
        checks = {}
        
        # Check Docker
        success, _ = self.run_command(["docker", "--version"])
        checks["docker"] = success
        
        # Check Docker Compose
        success, _ = self.run_command(["docker-compose", "--version"])
        checks["docker_compose"] = success
        
        # Check if compose file exists
        checks["compose_file_exists"] = Path(self.compose_file).exists()
        
        # Check Python dependencies
        try:
            import aiohttp
            import websockets
            checks["python_deps"] = True
        except ImportError:
            checks["python_deps"] = False
        
        # Log results
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {check}: {'OK' if result else 'FAILED'}")
        
        return checks
    
    def wait_for_services(self, timeout: int = 300) -> bool:
        """Wait for services to be ready"""
        logger.info(f"⏳ Waiting for services to be ready (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if backend is responding
            success, _ = self.run_command([
                "curl", "-f", "-s", f"{self.base_url}/health"
            ])
            
            if success:
                logger.info("✅ Services are ready!")
                return True
            
            logger.info("⏳ Services not ready yet, waiting 10s...")
            time.sleep(10)
        
        logger.warning("⚠️ Timeout waiting for services")
        return False
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🎯 Starting Complete Production Validation")
        logger.info(f"Target: {self.base_url} (domain: {self.domain})")
        logger.info(f"Compose file: {self.compose_file}")
        
        start_time = time.time()
        
        # Check prerequisites
        prerequisites = self.check_prerequisites()
        if not all(prerequisites.values()):
            failed_checks = [k for k, v in prerequisites.items() if not v]
            return {
                "success": False,
                "error": f"Prerequisites failed: {', '.join(failed_checks)}",
                "prerequisites": prerequisites
            }
        
        # Wait for services to be ready
        services_ready = self.wait_for_services()
        
        # Run Docker validation
        docker_results = await self.run_docker_validation()
        
        # Run application validation (even if Docker validation failed)
        app_results = await self.run_application_validation()
        
        total_duration = time.time() - start_time
        
        # Compile overall results
        overall_success = (
            docker_results.get("success", False) and 
            app_results.get("success", False) and
            services_ready
        )
        
        results = {
            "overall_success": overall_success,
            "validation_duration": total_duration,
            "prerequisites": prerequisites,
            "services_ready": services_ready,
            "docker_validation": docker_results,
            "application_validation": app_results,
            "timestamp": time.time()
        }
        
        # Generate summary
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: Dict[str, Any]) -> None:
        """Generate and log validation summary"""
        logger.info("\n" + "="*80)
        logger.info("🎯 COMPLETE PRODUCTION VALIDATION SUMMARY")
        logger.info("="*80)
        
        # Overall status
        if results["overall_success"]:
            logger.info("🎉 VALIDATION PASSED - PRODUCTION DEPLOYMENT IS READY!")
        else:
            logger.info("❌ VALIDATION FAILED - PRODUCTION DEPLOYMENT HAS ISSUES")
        
        logger.info(f"⏱️  Total Duration: {results['validation_duration']:.2f}s")
        
        # Prerequisites
        logger.info("\n📋 Prerequisites:")
        for check, status in results["prerequisites"].items():
            emoji = "✅" if status else "❌"
            logger.info(f"  {emoji} {check}")
        
        # Services readiness
        emoji = "✅" if results["services_ready"] else "❌"
        logger.info(f"\n🚀 Services Ready: {emoji}")
        
        # Docker validation
        docker_success = results["docker_validation"].get("success", False)
        emoji = "✅" if docker_success else "❌"
        logger.info(f"\n🐳 Docker Validation: {emoji}")
        
        if "detailed_report" in results["docker_validation"]:
            docker_report = results["docker_validation"]["detailed_report"]
            services = docker_report.get("services", {})
            logger.info(f"  Services: {services.get('healthy', 0)} healthy, "
                       f"{services.get('unhealthy', 0)} unhealthy, "
                       f"{services.get('missing', 0)} missing")
        
        # Application validation
        app_success = results["application_validation"].get("success", False)
        emoji = "✅" if app_success else "❌"
        logger.info(f"\n🚀 Application Validation: {emoji}")
        
        if "detailed_report" in results["application_validation"]:
            app_report = results["application_validation"]["detailed_report"]
            logger.info(f"  Tests: {app_report.get('passed', 0)} passed, "
                       f"{app_report.get('failed', 0)} failed, "
                       f"{app_report.get('warnings', 0)} warnings")
            logger.info(f"  Success Rate: {app_report.get('success_rate', 0):.1f}%")
        
        # Recommendations
        logger.info("\n💡 Recommendations:")
        
        if not results["overall_success"]:
            if not results["services_ready"]:
                logger.info("  • Check service logs: docker-compose logs")
                logger.info("  • Verify all containers are running: docker-compose ps")
            
            if not docker_success:
                logger.info("  • Review Docker validation report: docker_validation_report.json")
                logger.info("  • Check container health: docker-compose ps")
            
            if not app_success:
                logger.info("  • Review application validation report: app_validation_report.json")
                logger.info("  • Check backend logs for errors")
        else:
            logger.info("  • Deployment is ready for production use")
            logger.info("  • Monitor system performance and logs")
            logger.info("  • Set up regular health checks")
        
        logger.info("\n📄 Detailed reports:")
        logger.info("  • Docker: docker_validation_report.json")
        logger.info("  • Application: app_validation_report.json")
        logger.info("  • Combined: production_validation_complete.json")
    
    def save_complete_report(self, results: Dict[str, Any], 
                           filename: str = "production_validation_complete.json"):
        """Save complete validation report"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Complete validation report saved to {filename}")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ADVAKOD Complete Production Validator")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL to test (default: http://localhost:8000)")
    parser.add_argument("--domain", default="localhost", 
                       help="Domain name for production tests (default: localhost)")
    parser.add_argument("--compose-file", "-f", default="docker-compose.prod.yml",
                       help="Docker Compose file (default: docker-compose.prod.yml)")
    parser.add_argument("--report", default="production_validation_complete.json",
                       help="Output report filename")
    
    args = parser.parse_args()
    
    # Change to advakod directory if we're not already there
    if Path("advakod").exists() and not Path("docker-compose.prod.yml").exists():
        os.chdir("advakod")
        logger.info("📁 Changed to advakod directory")
    
    validator = ProductionValidationRunner(args.url, args.domain, args.compose_file)
    results = await validator.run_complete_validation()
    validator.save_complete_report(results, args.report)
    
    # Exit with appropriate code
    if results["overall_success"]:
        sys.exit(0)  # Success
    else:
        # Check severity of failures
        docker_ok = results["docker_validation"].get("success", False)
        app_ok = results["application_validation"].get("success", False)
        
        if docker_ok or app_ok:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Complete failure

if __name__ == "__main__":
    asyncio.run(main())