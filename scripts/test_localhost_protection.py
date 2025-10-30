#!/usr/bin/env python3
"""
Comprehensive test suite for localhost protection mechanisms.
This script tests all the protection systems we've implemented.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any


class LocalhostProtectionTester:
    """Test suite for localhost protection mechanisms."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.test_results = []
        self.failed_tests = []
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        print(f"🧪 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"   ✅ PASSED")
                self.test_results.append({"name": test_name, "status": "PASSED"})
                return True
            else:
                print(f"   ❌ FAILED")
                self.test_results.append({"name": test_name, "status": "FAILED"})
                self.failed_tests.append(test_name)
                return False
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.test_results.append({"name": test_name, "status": "ERROR", "error": str(e)})
            self.failed_tests.append(test_name)
            return False
    
    def test_ci_blocker_script(self) -> bool:
        """Test the CI blocker script."""
        script_path = self.project_root / "scripts" / "check_localhost.sh"
        if not script_path.exists():
            return False
        
        # Test with clean code (should pass)
        result = subprocess.run([str(script_path)], capture_output=True, text=True)
        return result.returncode == 0
    
    def test_pre_commit_hook(self) -> bool:
        """Test the pre-commit hook."""
        hook_path = self.project_root / ".git" / "hooks" / "pre-commit"
        if not hook_path.exists():
            return False
        
        # Check if hook is executable
        return os.access(hook_path, os.X_OK)
    
    def test_eslint_production_rules(self) -> bool:
        """Test ESLint production rules."""
        eslint_config = self.project_root / "frontend" / ".eslintrc.production.js"
        if not eslint_config.exists():
            return False
        
        # Check if config contains localhost restrictions
        with open(eslint_config, 'r') as f:
            content = f.read()
            return 'localhost' in content and 'no-restricted-syntax' in content
    
    def test_domain_whitelist_module(self) -> bool:
        """Test the domain whitelist module."""
        try:
            # Add backend to Python path
            sys.path.insert(0, str(self.project_root / "backend"))
            
            from app.core.domain_whitelist import DomainWhitelist
            
            # Test production whitelist
            prod_whitelist = DomainWhitelist("production")
            
            # Should allow production domains
            if not prod_whitelist.validate_origin("https://advacodex.com"):
                return False
            
            # Should block localhost in production
            if prod_whitelist.validate_origin("http://localhost:3000"):
                return False
            
            # Test development whitelist
            dev_whitelist = DomainWhitelist("development")
            
            # Should allow localhost in development
            if not dev_whitelist.validate_origin("http://localhost:3000"):
                return False
            
            return True
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def test_environment_variable_validation(self) -> bool:
        """Test environment variable validation."""
        try:
            # Test with production environment
            os.environ["ENVIRONMENT"] = "production"
            
            # Add backend to Python path
            sys.path.insert(0, str(self.project_root / "backend"))
            
            from app.core.domain_whitelist import domain_whitelist
            
            # Should not raise error with clean environment
            domain_whitelist.block_localhost_in_production()
            
            # Test with localhost in environment (should raise error)
            os.environ["TEST_VAR"] = "http://localhost:3000"
            try:
                domain_whitelist.block_localhost_in_production()
                return False  # Should have raised an error
            except ValueError:
                return True  # Expected error
            finally:
                # Clean up
                if "TEST_VAR" in os.environ:
                    del os.environ["TEST_VAR"]
            
        except ImportError:
            return False
        except Exception:
            return False
    
    def test_nginx_configuration(self) -> bool:
        """Test Nginx configuration for domain restrictions."""
        nginx_configs = [
            self.project_root / "nginx.conf",
            self.project_root / "nginx.strict.conf"
        ]
        
        for config_path in nginx_configs:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                    
                    # Should have server_name restrictions
                    if "server_name advacodex.com" not in content:
                        continue
                    
                    # Should have default server block that returns 444
                    if "return 444" not in content:
                        continue
                    
                    return True
        
        return False
    
    def test_docker_compose_configuration(self) -> bool:
        """Test Docker Compose configuration."""
        docker_compose = self.project_root / "docker-compose.prod.yml"
        if not docker_compose.exists():
            return False
        
        with open(docker_compose, 'r') as f:
            content = f.read()
            
            # Should not contain localhost
            if 'localhost' in content.lower():
                return False
            
            # Should use service names
            required_services = ['postgres', 'redis', 'qdrant', 'backend', 'frontend', 'nginx']
            for service in required_services:
                if f'{service}:' not in content:
                    return False
            
            return True
    
    def test_github_actions_workflow(self) -> bool:
        """Test GitHub Actions workflow for localhost protection."""
        workflow_path = self.project_root / ".github" / "workflows" / "localhost-protection.yml"
        if not workflow_path.exists():
            return False
        
        with open(workflow_path, 'r') as f:
            content = f.read()
            
            # Should have localhost check job
            if 'localhost-check' not in content:
                return False
            
            # Should run the check script
            if 'check_localhost.sh' not in content:
                return False
            
            return True
    
    def test_fallback_removal_script(self) -> bool:
        """Test the fallback removal script."""
        script_path = self.project_root / "scripts" / "remove_localhost_fallbacks.py"
        if not script_path.exists():
            return False
        
        # Check if script is executable
        if not os.access(script_path, os.X_OK):
            return False
        
        # Test script with dry run (create a temporary test file)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/test")\n')
            temp_file = f.name
        
        try:
            # Run the script (it should detect the fallback)
            result = subprocess.run([
                sys.executable, str(script_path), str(Path(temp_file).parent)
            ], capture_output=True, text=True)
            
            # Script should detect the fallback
            return 'localhost' in result.stdout.lower()
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_production_validation_script(self) -> bool:
        """Test the production validation script."""
        script_path = self.project_root / "scripts" / "validate_production_config.sh"
        if not script_path.exists():
            return False
        
        # Check if script is executable
        return os.access(script_path, os.X_OK)
    
    def test_cors_configuration(self) -> bool:
        """Test CORS configuration in main.py."""
        main_py = self.project_root / "backend" / "main.py"
        if not main_py.exists():
            return False
        
        with open(main_py, 'r') as f:
            content = f.read()
            
            # Should use domain_whitelist
            if 'domain_whitelist' not in content:
                return False
            
            # Should validate origins
            if 'validate_origin' not in content:
                return False
            
            return True
    
    def create_test_files_with_localhost(self) -> Dict[str, str]:
        """Create temporary test files with localhost references."""
        test_files = {}
        
        # JavaScript file with localhost
        js_content = '''
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3000";
console.log("Debug: API URL is", API_URL);
'''
        
        # Python file with localhost
        py_content = '''
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/test")
print("Database URL:", DATABASE_URL)
'''
        
        # Environment file with localhost
        env_content = '''
REACT_APP_API_URL=http://localhost:3000
DATABASE_URL=postgresql://localhost:5432/test
'''
        
        for name, content in [("test.js", js_content), ("test.py", py_content), (".env.test", env_content)]:
            with tempfile.NamedTemporaryFile(mode='w', suffix=name, delete=False) as f:
                f.write(content)
                test_files[name] = f.name
        
        return test_files
    
    def test_localhost_detection_accuracy(self) -> bool:
        """Test that our detection scripts accurately find localhost references."""
        test_files = self.create_test_files_with_localhost()
        
        try:
            # Test CI blocker script
            script_path = self.project_root / "scripts" / "check_localhost.sh"
            if script_path.exists():
                # Copy test files to a temporary directory structure
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Create directory structure
                    (temp_path / "frontend" / "src").mkdir(parents=True)
                    (temp_path / "backend").mkdir(parents=True)
                    
                    # Copy test files
                    for name, file_path in test_files.items():
                        if name.endswith('.js'):
                            target = temp_path / "frontend" / "src" / name
                        elif name.endswith('.py'):
                            target = temp_path / "backend" / name
                        else:
                            target = temp_path / name
                        
                        with open(file_path, 'r') as src, open(target, 'w') as dst:
                            dst.write(src.read())
                    
                    # Run the check script in the temp directory
                    result = subprocess.run([
                        str(script_path)
                    ], cwd=temp_dir, capture_output=True, text=True)
                    
                    # Should detect localhost and fail
                    return result.returncode != 0 and 'localhost' in result.stdout.lower()
            
            return False
            
        finally:
            # Clean up test files
            for file_path in test_files.values():
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def run_all_tests(self) -> bool:
        """Run all localhost protection tests."""
        print("🔒 LOCALHOST PROTECTION TEST SUITE")
        print("=" * 50)
        
        tests = [
            ("CI Blocker Script", self.test_ci_blocker_script),
            ("Pre-commit Hook", self.test_pre_commit_hook),
            ("ESLint Production Rules", self.test_eslint_production_rules),
            ("Domain Whitelist Module", self.test_domain_whitelist_module),
            ("Environment Variable Validation", self.test_environment_variable_validation),
            ("Nginx Configuration", self.test_nginx_configuration),
            ("Docker Compose Configuration", self.test_docker_compose_configuration),
            ("GitHub Actions Workflow", self.test_github_actions_workflow),
            ("Fallback Removal Script", self.test_fallback_removal_script),
            ("Production Validation Script", self.test_production_validation_script),
            ("CORS Configuration", self.test_cors_configuration),
            ("Localhost Detection Accuracy", self.test_localhost_detection_accuracy),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Localhost protection is working correctly")
            return True
        else:
            print(f"\n⚠️  Some tests failed - localhost protection may not be fully effective")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a detailed test report."""
        return {
            "timestamp": str(subprocess.check_output(["date"], text=True).strip()),
            "total_tests": len(self.test_results),
            "passed_tests": len([t for t in self.test_results if t["status"] == "PASSED"]),
            "failed_tests": len(self.failed_tests),
            "test_results": self.test_results,
            "failed_test_names": self.failed_tests
        }


def main():
    """Main function."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    tester = LocalhostProtectionTester(project_root)
    success = tester.run_all_tests()
    
    # Generate report
    report = tester.generate_report()
    report_file = Path(project_root) / "localhost_protection_test_report.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()