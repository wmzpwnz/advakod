#!/usr/bin/env python3
"""
Production Deployment Validation Script
Validates complete system functionality for ADVAKOD AI-Lawyer system
"""

import asyncio
import aiohttp
import websockets
import json
import time
import sys
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import ssl
import socket
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('validation_report.log')
    ]
)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"

@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    duration: float
    details: Optional[Dict[str, Any]] = None

class ProductionValidator:
    """Comprehensive production deployment validator"""
    
    def __init__(self, base_url: str = "http://localhost:8000", domain: str = "localhost"):
        self.base_url = base_url.rstrip('/')
        self.domain = domain
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Test configuration
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.test_user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def add_result(self, name: str, status: TestStatus, message: str, 
                   duration: float, details: Optional[Dict[str, Any]] = None):
        """Add test result"""
        result = TestResult(name, status, message, duration, details)
        self.results.append(result)
        
        # Log result
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌", 
            TestStatus.WARNING: "⚠️",
            TestStatus.SKIPPED: "⏭️"
        }
        
        logger.info(f"{status_emoji[status]} {name}: {message} ({duration:.2f}s)")
        if details:
            logger.debug(f"   Details: {details}")
    
    async def test_service_startup(self) -> None:
        """Test 11.1.1: Verify all services start without errors"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    duration = time.time() - start_time
                    
                    self.add_result(
                        "Service Startup - Health Check",
                        TestStatus.PASSED,
                        f"Backend service is healthy (version: {health_data.get('version', 'unknown')})",
                        duration,
                        health_data
                    )
                else:
                    duration = time.time() - start_time
                    self.add_result(
                        "Service Startup - Health Check",
                        TestStatus.FAILED,
                        f"Health check failed with status {response.status}",
                        duration
                    )
                    return
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Service Startup - Health Check",
                TestStatus.FAILED,
                f"Failed to connect to backend: {str(e)}",
                duration
            )
            return
        
        # Test readiness probe
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/ready") as response:
                readiness_data = await response.json()
                duration = time.time() - start_time
                
                if response.status == 200 and readiness_data.get("ready", False):
                    self.add_result(
                        "Service Startup - Readiness Check",
                        TestStatus.PASSED,
                        f"All services ready (AI Model: {'loaded' if readiness_data.get('ai_model', {}).get('loaded') else 'not loaded'})",
                        duration,
                        readiness_data
                    )
                elif response.status == 200:
                    self.add_result(
                        "Service Startup - Readiness Check", 
                        TestStatus.WARNING,
                        "Services partially ready (degraded mode)",
                        duration,
                        readiness_data
                    )
                else:
                    self.add_result(
                        "Service Startup - Readiness Check",
                        TestStatus.FAILED,
                        f"Readiness check failed with status {response.status}",
                        duration,
                        readiness_data
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Service Startup - Readiness Check",
                TestStatus.FAILED,
                f"Readiness check error: {str(e)}",
                duration
            )
    
    async def test_ai_model_health(self) -> None:
        """Test AI model specific health"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}/health/ai-model") as response:
                model_health = await response.json()
                duration = time.time() - start_time
                
                status = model_health.get("status", "unknown")
                if status == "healthy":
                    self.add_result(
                        "AI Model Health",
                        TestStatus.PASSED,
                        "AI model is healthy and ready",
                        duration,
                        model_health
                    )
                elif status == "degraded":
                    self.add_result(
                        "AI Model Health",
                        TestStatus.WARNING,
                        "AI model is loaded but degraded",
                        duration,
                        model_health
                    )
                else:
                    self.add_result(
                        "AI Model Health",
                        TestStatus.FAILED,
                        f"AI model is unhealthy: {status}",
                        duration,
                        model_health
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "AI Model Health",
                TestStatus.FAILED,
                f"AI model health check failed: {str(e)}",
                duration
            )
    
    async def test_ai_response_generation(self) -> None:
        """Test 11.1.2: Test AI response generation end-to-end"""
        start_time = time.time()
        
        # First, try to register/login a test user
        auth_token = await self._get_auth_token()
        if not auth_token:
            duration = time.time() - start_time
            self.add_result(
                "AI Response Generation",
                TestStatus.FAILED,
                "Could not authenticate test user",
                duration
            )
            return
        
        # Test AI chat endpoint
        test_prompt = "Что такое гражданское право в России?"
        
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            payload = {
                "message": test_prompt,
                "conversation_id": "test_conversation_001"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    chat_response = await response.json()
                    duration = time.time() - start_time
                    
                    if chat_response.get("success") and chat_response.get("response"):
                        self.add_result(
                            "AI Response Generation",
                            TestStatus.PASSED,
                            f"AI generated response successfully ({len(chat_response['response'])} chars)",
                            duration,
                            {
                                "prompt": test_prompt,
                                "response_length": len(chat_response.get("response", "")),
                                "processing_time": chat_response.get("processing_time")
                            }
                        )
                    else:
                        self.add_result(
                            "AI Response Generation",
                            TestStatus.FAILED,
                            "AI response was empty or unsuccessful",
                            duration,
                            chat_response
                        )
                else:
                    duration = time.time() - start_time
                    error_data = await response.text()
                    self.add_result(
                        "AI Response Generation",
                        TestStatus.FAILED,
                        f"Chat API failed with status {response.status}",
                        duration,
                        {"error": error_data}
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "AI Response Generation",
                TestStatus.FAILED,
                f"AI response generation failed: {str(e)}",
                duration
            )
    
    async def test_websocket_communication(self) -> None:
        """Test 11.1.3: Validate WebSocket communication"""
        start_time = time.time()
        
        # Get auth token first
        auth_token = await self._get_auth_token()
        if not auth_token:
            duration = time.time() - start_time
            self.add_result(
                "WebSocket Communication",
                TestStatus.FAILED,
                "Could not authenticate for WebSocket test",
                duration
            )
            return
        
        # Convert HTTP URL to WebSocket URL
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/chat"
        
        try:
            # Test WebSocket connection
            extra_headers = {"Authorization": f"Bearer {auth_token}"}
            
            async with websockets.connect(
                ws_url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                
                # Send test message
                test_message = {
                    "type": "chat_message",
                    "message": "Тест WebSocket соединения",
                    "conversation_id": "test_ws_001"
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    
                    duration = time.time() - start_time
                    
                    if response_data.get("type") == "chat_response":
                        self.add_result(
                            "WebSocket Communication",
                            TestStatus.PASSED,
                            "WebSocket communication successful",
                            duration,
                            {
                                "message_sent": test_message,
                                "response_received": response_data.get("type"),
                                "response_length": len(response_data.get("content", ""))
                            }
                        )
                    else:
                        self.add_result(
                            "WebSocket Communication",
                            TestStatus.WARNING,
                            f"Unexpected WebSocket response type: {response_data.get('type')}",
                            duration,
                            response_data
                        )
                        
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    self.add_result(
                        "WebSocket Communication",
                        TestStatus.FAILED,
                        "WebSocket response timeout (30s)",
                        duration
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "WebSocket Communication",
                TestStatus.FAILED,
                f"WebSocket connection failed: {str(e)}",
                duration
            )
    
    async def test_production_domain(self) -> None:
        """Test 11.2.1: Test system with production domain"""
        if self.domain == "localhost":
            self.add_result(
                "Production Domain Test",
                TestStatus.SKIPPED,
                "Skipped - testing on localhost",
                0.0
            )
            return
        
        start_time = time.time()
        
        try:
            # Test domain resolution
            socket.gethostbyname(self.domain)
            
            # Test HTTPS if production domain
            if self.domain != "localhost":
                https_url = f"https://{self.domain}"
                
                async with self.session.get(f"{https_url}/health") as response:
                    if response.status == 200:
                        duration = time.time() - start_time
                        self.add_result(
                            "Production Domain Test",
                            TestStatus.PASSED,
                            f"Production domain {self.domain} is accessible via HTTPS",
                            duration
                        )
                    else:
                        duration = time.time() - start_time
                        self.add_result(
                            "Production Domain Test",
                            TestStatus.FAILED,
                            f"Production domain returned status {response.status}",
                            duration
                        )
            
        except socket.gaierror:
            duration = time.time() - start_time
            self.add_result(
                "Production Domain Test",
                TestStatus.FAILED,
                f"Domain {self.domain} does not resolve",
                duration
            )
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Production Domain Test",
                TestStatus.FAILED,
                f"Production domain test failed: {str(e)}",
                duration
            )
    
    async def test_https_wss_connections(self) -> None:
        """Test 11.2.2: Verify HTTPS and WSS connections work"""
        if self.domain == "localhost":
            self.add_result(
                "HTTPS/WSS Connections",
                TestStatus.SKIPPED,
                "Skipped - testing on localhost (no SSL)",
                0.0
            )
            return
        
        start_time = time.time()
        
        try:
            # Test HTTPS
            https_url = f"https://{self.domain}"
            
            async with self.session.get(f"{https_url}/health") as response:
                if response.status == 200:
                    # Test WSS
                    wss_url = f"wss://{self.domain}/ws/chat"
                    
                    # Get auth token for WSS test
                    auth_token = await self._get_auth_token()
                    if auth_token:
                        extra_headers = {"Authorization": f"Bearer {auth_token}"}
                        
                        try:
                            async with websockets.connect(
                                wss_url,
                                extra_headers=extra_headers,
                                ping_interval=20,
                                ping_timeout=10
                            ) as websocket:
                                await websocket.ping()
                                
                                duration = time.time() - start_time
                                self.add_result(
                                    "HTTPS/WSS Connections",
                                    TestStatus.PASSED,
                                    "Both HTTPS and WSS connections work",
                                    duration
                                )
                        except Exception as wss_error:
                            duration = time.time() - start_time
                            self.add_result(
                                "HTTPS/WSS Connections",
                                TestStatus.WARNING,
                                f"HTTPS works but WSS failed: {str(wss_error)}",
                                duration
                            )
                    else:
                        duration = time.time() - start_time
                        self.add_result(
                            "HTTPS/WSS Connections",
                            TestStatus.WARNING,
                            "HTTPS works but could not test WSS (auth failed)",
                            duration
                        )
                else:
                    duration = time.time() - start_time
                    self.add_result(
                        "HTTPS/WSS Connections",
                        TestStatus.FAILED,
                        f"HTTPS connection failed with status {response.status}",
                        duration
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "HTTPS/WSS Connections",
                TestStatus.FAILED,
                f"HTTPS/WSS test failed: {str(e)}",
                duration
            )
    
    async def test_static_files_loading(self) -> None:
        """Test 11.2.3: Validate static file loading in production"""
        start_time = time.time()
        
        # Test common static file paths
        static_files = [
            "/static/css/main.css",
            "/static/js/main.js", 
            "/static/favicon.ico"
        ]
        
        passed_files = 0
        failed_files = []
        
        for static_file in static_files:
            try:
                async with self.session.get(f"{self.base_url}{static_file}") as response:
                    if response.status == 200:
                        passed_files += 1
                    else:
                        failed_files.append(f"{static_file} (status: {response.status})")
                        
            except Exception as e:
                failed_files.append(f"{static_file} (error: {str(e)})")
        
        duration = time.time() - start_time
        
        if passed_files == len(static_files):
            self.add_result(
                "Static Files Loading",
                TestStatus.PASSED,
                f"All {passed_files} static files loaded successfully",
                duration
            )
        elif passed_files > 0:
            self.add_result(
                "Static Files Loading",
                TestStatus.WARNING,
                f"{passed_files}/{len(static_files)} static files loaded. Failed: {', '.join(failed_files)}",
                duration
            )
        else:
            self.add_result(
                "Static Files Loading",
                TestStatus.FAILED,
                f"No static files could be loaded. Failed: {', '.join(failed_files)}",
                duration
            )
    
    async def test_database_connections(self) -> None:
        """Test database connectivity"""
        start_time = time.time()
        
        try:
            # Test through API endpoint that uses database
            async with self.session.get(f"{self.base_url}/api/v1/users/me") as response:
                # We expect 401 (unauthorized) which means the endpoint works
                # but we're not authenticated - this confirms DB connectivity
                if response.status in [401, 422]:  # 422 for validation error
                    duration = time.time() - start_time
                    self.add_result(
                        "Database Connectivity",
                        TestStatus.PASSED,
                        "Database connection working (API responds correctly)",
                        duration
                    )
                elif response.status == 500:
                    duration = time.time() - start_time
                    self.add_result(
                        "Database Connectivity",
                        TestStatus.FAILED,
                        "Database connection may be failing (500 error)",
                        duration
                    )
                else:
                    duration = time.time() - start_time
                    self.add_result(
                        "Database Connectivity",
                        TestStatus.WARNING,
                        f"Unexpected response status: {response.status}",
                        duration
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Database Connectivity",
                TestStatus.FAILED,
                f"Database connectivity test failed: {str(e)}",
                duration
            )
    
    async def test_api_endpoints(self) -> None:
        """Test critical API endpoints"""
        start_time = time.time()
        
        # Test public endpoints
        public_endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/ready", "Readiness check"),
            ("/api/v1/auth/register", "Registration endpoint (POST)"),
        ]
        
        passed_endpoints = 0
        failed_endpoints = []
        
        for endpoint, description in public_endpoints:
            try:
                method = "POST" if "register" in endpoint else "GET"
                
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status in [200, 422]:  # 422 for validation errors is OK
                            passed_endpoints += 1
                        else:
                            failed_endpoints.append(f"{description} ({response.status})")
                else:
                    # For POST endpoints, just check they respond (even with validation errors)
                    async with self.session.post(f"{self.base_url}{endpoint}", json={}) as response:
                        if response.status in [200, 400, 422]:  # These are expected for empty POST
                            passed_endpoints += 1
                        else:
                            failed_endpoints.append(f"{description} ({response.status})")
                            
            except Exception as e:
                failed_endpoints.append(f"{description} (error: {str(e)})")
        
        duration = time.time() - start_time
        
        if passed_endpoints == len(public_endpoints):
            self.add_result(
                "API Endpoints",
                TestStatus.PASSED,
                f"All {passed_endpoints} critical endpoints responding",
                duration
            )
        elif passed_endpoints > 0:
            self.add_result(
                "API Endpoints",
                TestStatus.WARNING,
                f"{passed_endpoints}/{len(public_endpoints)} endpoints OK. Issues: {', '.join(failed_endpoints)}",
                duration
            )
        else:
            self.add_result(
                "API Endpoints",
                TestStatus.FAILED,
                f"No endpoints responding. Issues: {', '.join(failed_endpoints)}",
                duration
            )
    
    async def _get_auth_token(self) -> Optional[str]:
        """Helper method to get authentication token for testing"""
        try:
            # Try to register test user (may fail if already exists)
            register_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"],
                "full_name": self.test_user_data["full_name"]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=register_data
            ) as response:
                # Registration may fail if user exists, that's OK
                pass
            
            # Try to login
            login_data = {
                "username": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data  # Form data for OAuth2
            ) as response:
                if response.status == 200:
                    login_response = await response.json()
                    return login_response.get("access_token")
                    
        except Exception as e:
            logger.warning(f"Could not get auth token: {e}")
            
        return None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("🚀 Starting Production Deployment Validation")
        logger.info(f"Target: {self.base_url} (domain: {self.domain})")
        
        start_time = time.time()
        
        # Test 11.1: Complete system functionality
        logger.info("\n📋 Testing Complete System Functionality (11.1)")
        await self.test_service_startup()
        await self.test_ai_model_health()
        await self.test_database_connections()
        await self.test_api_endpoints()
        await self.test_ai_response_generation()
        await self.test_websocket_communication()
        
        # Test 11.2: Production environment testing
        logger.info("\n🌐 Testing Production Environment (11.2)")
        await self.test_production_domain()
        await self.test_https_wss_connections()
        await self.test_static_files_loading()
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = self._generate_summary(total_duration)
        
        logger.info("\n" + "="*60)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"⚠️  Warnings: {summary['warnings']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"⏭️  Skipped: {summary['skipped']}")
        logger.info(f"⏱️  Total Duration: {total_duration:.2f}s")
        logger.info(f"🎯 Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failed'] == 0:
            logger.info("\n🎉 ALL CRITICAL TESTS PASSED - DEPLOYMENT VALIDATED!")
        elif summary['failed'] <= 2:
            logger.info("\n⚠️  DEPLOYMENT MOSTLY SUCCESSFUL - MINOR ISSUES DETECTED")
        else:
            logger.info("\n❌ DEPLOYMENT HAS SIGNIFICANT ISSUES - REVIEW REQUIRED")
        
        return summary
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate test summary"""
        passed = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed = len([r for r in self.results if r.status == TestStatus.FAILED])
        warnings = len([r for r in self.results if r.status == TestStatus.WARNING])
        skipped = len([r for r in self.results if r.status == TestStatus.SKIPPED])
        total = len(self.results)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details
                }
                for r in self.results
            ]
        }
    
    def save_report(self, filename: str = "validation_report.json"):
        """Save detailed validation report"""
        summary = self._generate_summary(0)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Detailed report saved to {filename}")

async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ADVAKOD Production Deployment Validator")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL to test (default: http://localhost:8000)")
    parser.add_argument("--domain", default="localhost",
                       help="Domain name for production tests (default: localhost)")
    parser.add_argument("--report", default="validation_report.json",
                       help="Output report filename (default: validation_report.json)")
    
    args = parser.parse_args()
    
    async with ProductionValidator(args.url, args.domain) as validator:
        summary = await validator.run_all_tests()
        validator.save_report(args.report)
        
        # Exit with appropriate code
        if summary['failed'] == 0:
            sys.exit(0)  # Success
        elif summary['failed'] <= 2:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues

if __name__ == "__main__":
    asyncio.run(main())