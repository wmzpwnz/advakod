#!/usr/bin/env python3
"""
Comprehensive test runner for admin panel enhancement
Runs E2E, performance, and security tests
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import argparse


class ComprehensiveTestRunner:
    """Runs all types of tests for the admin panel enhancement."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "backend_tests": {},
            "frontend_tests": {},
            "e2e_tests": {},
            "performance_tests": {},
            "security_tests": {},
            "summary": {}
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command: List[str], cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Run a command and return results."""
        self.log(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(command)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command)
            }
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        self.log("Checking prerequisites...")
        
        prerequisites = [
            ("python", ["python", "--version"]),
            ("node", ["node", "--version"]),
            ("npm", ["npm", "--version"]),
            ("pytest", ["python", "-m", "pytest", "--version"]),
        ]
        
        missing = []
        for name, command in prerequisites:
            result = self.run_command(command, timeout=10)
            if not result["success"]:
                missing.append(name)
                self.log(f"Missing prerequisite: {name}", "ERROR")
            else:
                version = result["stdout"].strip()
                self.log(f"{name}: {version}")
        
        if missing:
            self.log(f"Missing prerequisites: {', '.join(missing)}", "ERROR")
            return False
        
        return True
    
    def setup_test_environment(self) -> bool:
        """Set up the test environment."""
        self.log("Setting up test environment...")
        
        # Install backend test dependencies
        backend_result = self.run_command([
            "pip", "install", "-r", "requirements-test.txt"
        ], cwd="advakod/backend")
        
        if not backend_result["success"]:
            self.log("Failed to install backend test dependencies", "ERROR")
            return False
        
        # Install frontend test dependencies
        frontend_result = self.run_command([
            "npm", "install", "--save-dev", 
            "cypress@^13.6.0",
            "cypress-axe@^1.5.0", 
            "cypress-real-events@^1.11.0",
            "jest-axe@^8.0.0",
            "puppeteer@^21.6.1",
            "lighthouse@^11.4.0"
        ], cwd="advakod/frontend")
        
        if not frontend_result["success"]:
            self.log("Failed to install frontend test dependencies", "ERROR")
            return False
        
        return True
    
    def run_backend_unit_tests(self) -> bool:
        """Run backend unit tests."""
        self.log("Running backend unit tests...")
        
        result = self.run_command([
            "python", "-m", "pytest", 
            "tests/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=json:coverage.json",
            "-m", "not integration and not performance and not security"
        ], cwd="advakod/backend")
        
        self.results["backend_tests"]["unit"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            self.log("Backend unit tests passed", "SUCCESS")
        else:
            self.log("Backend unit tests failed", "ERROR")
            if self.verbose:
                print(result["stderr"])
        
        return result["success"]
    
    def run_backend_integration_tests(self) -> bool:
        """Run backend integration tests."""
        self.log("Running backend integration tests...")
        
        result = self.run_command([
            "python", "-m", "pytest", 
            "tests/integration/",
            "-v",
            "--tb=short",
            "-m", "integration"
        ], cwd="advakod/backend")
        
        self.results["backend_tests"]["integration"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            self.log("Backend integration tests passed", "SUCCESS")
        else:
            self.log("Backend integration tests failed", "ERROR")
            if self.verbose:
                print(result["stderr"])
        
        return result["success"]
    
    def run_frontend_unit_tests(self) -> bool:
        """Run frontend unit tests."""
        self.log("Running frontend unit tests...")
        
        result = self.run_command([
            "npm", "test", "--", "--watchAll=false", "--coverage"
        ], cwd="advakod/frontend")
        
        self.results["frontend_tests"]["unit"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            self.log("Frontend unit tests passed", "SUCCESS")
        else:
            self.log("Frontend unit tests failed", "ERROR")
            if self.verbose:
                print(result["stderr"])
        
        return result["success"]
    
    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests."""
        self.log("Running E2E tests...")
        
        # Check if servers are running
        self.log("Checking if servers are running...")
        
        # Run Cypress E2E tests
        result = self.run_command([
            "npx", "cypress", "run", 
            "--spec", "cypress/e2e/critical-flows/**/*",
            "--reporter", "json",
            "--reporter-options", "outputFile=cypress/reports/e2e-results.json"
        ], cwd="advakod/frontend", timeout=600)  # 10 minutes timeout
        
        self.results["e2e_tests"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            self.log("E2E tests passed", "SUCCESS")
        else:
            self.log("E2E tests failed", "ERROR")
            if self.verbose:
                print(result["stderr"])
        
        return result["success"]
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        self.log("Running performance tests...")
        
        # Backend performance tests
        backend_result = self.run_command([
            "python", "-m", "pytest", 
            "tests/performance/",
            "-v",
            "--tb=short",
            "-m", "performance"
        ], cwd="advakod/backend", timeout=600)
        
        # Frontend performance tests
        frontend_result = self.run_command([
            "node", "scripts/performance-tests.js"
        ], cwd="advakod/frontend", timeout=600)
        
        # Cypress performance tests
        cypress_result = self.run_command([
            "npx", "cypress", "run",
            "--spec", "cypress/e2e/performance/**/*"
        ], cwd="advakod/frontend", timeout=600)
        
        success = all([
            backend_result["success"],
            frontend_result["success"],
            cypress_result["success"]
        ])
        
        self.results["performance_tests"] = {
            "success": success,
            "backend": backend_result,
            "frontend": frontend_result,
            "cypress": cypress_result
        }
        
        if success:
            self.log("Performance tests passed", "SUCCESS")
        else:
            self.log("Performance tests failed", "ERROR")
        
        return success
    
    def run_security_tests(self) -> bool:
        """Run security tests."""
        self.log("Running security tests...")
        
        # Backend security tests
        backend_result = self.run_command([
            "python", "-m", "pytest", 
            "tests/security/",
            "-v",
            "--tb=short",
            "-m", "security"
        ], cwd="advakod/backend")
        
        # Frontend security tests (Cypress)
        cypress_result = self.run_command([
            "npx", "cypress", "run",
            "--spec", "cypress/e2e/security/**/*"
        ], cwd="advakod/frontend", timeout=300)
        
        # Security linting
        security_lint_result = self.run_command([
            "npm", "run", "test:security"
        ], cwd="advakod/frontend")
        
        success = all([
            backend_result["success"],
            cypress_result["success"],
            security_lint_result["success"]
        ])
        
        self.results["security_tests"] = {
            "success": success,
            "backend": backend_result,
            "cypress": cypress_result,
            "security_lint": security_lint_result
        }
        
        if success:
            self.log("Security tests passed", "SUCCESS")
        else:
            self.log("Security tests failed", "ERROR")
        
        return success
    
    def generate_report(self) -> None:
        """Generate comprehensive test report."""
        self.log("Generating test report...")
        
        # Calculate summary
        test_categories = [
            "backend_tests", "frontend_tests", "e2e_tests", 
            "performance_tests", "security_tests"
        ]
        
        passed = 0
        total = len(test_categories)
        
        for category in test_categories:
            if category in self.results:
                if isinstance(self.results[category], dict):
                    if self.results[category].get("success", False):
                        passed += 1
                else:
                    # Handle nested results
                    category_passed = True
                    for subcategory, result in self.results[category].items():
                        if isinstance(result, dict) and not result.get("success", False):
                            category_passed = False
                            break
                    if category_passed:
                        passed += 1
        
        self.results["summary"] = {
            "total_categories": total,
            "passed_categories": passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "overall_success": passed == total
        }
        
        # Write JSON report
        report_path = Path("test_results.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate HTML report
        html_report = self.generate_html_report()
        html_path = Path("test_report.html")
        with open(html_path, "w") as f:
            f.write(html_report)
        
        self.log(f"Test report generated: {html_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total test categories: {total}")
        print(f"Passed categories: {passed}")
        print(f"Success rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Overall result: {'PASS' if self.results['summary']['overall_success'] else 'FAIL'}")
        print("="*60)
    
    def generate_html_report(self) -> str:
        """Generate HTML test report."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel Enhancement - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }}
        .success {{ border-color: #28a745; }}
        .failure {{ border-color: #dc3545; }}
        .details {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        pre {{ background: #f1f1f1; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Admin Panel Enhancement - Comprehensive Test Report</h1>
        <p>Generated: {self.results['timestamp']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Success Rate:</strong> {self.results['summary']['success_rate']:.1f}%</p>
        <p><strong>Categories Passed:</strong> {self.results['summary']['passed_categories']}/{self.results['summary']['total_categories']}</p>
        <p><strong>Overall Result:</strong> {'PASS' if self.results['summary']['overall_success'] else 'FAIL'}</p>
    </div>
    
    <div class="categories">
        <h2>Test Categories</h2>
        {self._generate_category_html()}
    </div>
</body>
</html>
        """
    
    def _generate_category_html(self) -> str:
        """Generate HTML for test categories."""
        html = ""
        
        categories = {
            "backend_tests": "Backend Tests",
            "frontend_tests": "Frontend Tests", 
            "e2e_tests": "End-to-End Tests",
            "performance_tests": "Performance Tests",
            "security_tests": "Security Tests"
        }
        
        for key, title in categories.items():
            if key in self.results:
                result = self.results[key]
                success = result.get("success", False) if isinstance(result, dict) else False
                css_class = "success" if success else "failure"
                status = "PASS" if success else "FAIL"
                
                html += f"""
                <div class="category {css_class}">
                    <h3>{title} - {status}</h3>
                    <div class="details">
                        <p><strong>Status:</strong> {status}</p>
                    </div>
                </div>
                """
        
        return html
    
    def run_all_tests(self, skip_setup: bool = False) -> bool:
        """Run all comprehensive tests."""
        self.log("Starting comprehensive test suite...")
        
        if not skip_setup:
            if not self.check_prerequisites():
                return False
            
            if not self.setup_test_environment():
                return False
        
        # Run all test categories
        test_functions = [
            ("Backend Unit Tests", self.run_backend_unit_tests),
            ("Backend Integration Tests", self.run_backend_integration_tests),
            ("Frontend Unit Tests", self.run_frontend_unit_tests),
            ("End-to-End Tests", self.run_e2e_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Security Tests", self.run_security_tests)
        ]
        
        results = []
        for name, func in test_functions:
            self.log(f"Starting {name}...")
            try:
                result = func()
                results.append(result)
                status = "PASSED" if result else "FAILED"
                self.log(f"{name}: {status}")
            except Exception as e:
                self.log(f"{name} failed with exception: {e}", "ERROR")
                results.append(False)
        
        # Generate report
        self.generate_report()
        
        # Return overall success
        overall_success = all(results)
        self.log(f"Comprehensive test suite: {'PASSED' if overall_success else 'FAILED'}")
        
        return overall_success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for admin panel enhancement")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-setup", action="store_true", help="Skip environment setup")
    parser.add_argument("--category", choices=["unit", "integration", "e2e", "performance", "security"], 
                       help="Run only specific test category")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(verbose=args.verbose)
    
    if args.category:
        # Run specific category
        category_functions = {
            "unit": lambda: runner.run_backend_unit_tests() and runner.run_frontend_unit_tests(),
            "integration": runner.run_backend_integration_tests,
            "e2e": runner.run_e2e_tests,
            "performance": runner.run_performance_tests,
            "security": runner.run_security_tests
        }
        
        if args.category in category_functions:
            success = category_functions[args.category]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown category: {args.category}")
            sys.exit(1)
    else:
        # Run all tests
        success = runner.run_all_tests(skip_setup=args.skip_setup)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()