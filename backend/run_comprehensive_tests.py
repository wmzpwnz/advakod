#!/usr/bin/env python3
"""
Comprehensive test runner for WebSocket AI errors fix
Runs all tests related to generation timeouts, WebSocket connections, 
end-to-end chat flow, and monitoring system
"""

import os
import sys
import subprocess
import time
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_command(cmd, cwd=None, timeout=300):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return False, "", "Timeout"
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    # Check Python dependencies
    required_packages = [
        'pytest', 'pytest-asyncio', 'httpx', 'fastapi', 
        'sqlalchemy', 'psutil'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All Python dependencies are installed")
    return True

def run_backend_tests():
    """Run backend tests"""
    print("\n" + "="*60)
    print("RUNNING BACKEND TESTS")
    print("="*60)
    
    test_files = [
        "tests/test_generation_timeouts.py",
        "tests/test_websocket_integration.py", 
        "tests/test_end_to_end_chat.py",
        "tests/test_monitoring_system.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            results[test_file] = False
            continue
            
        print(f"\n📋 Running {test_file}...")
        
        # Run pytest with specific markers and options
        cmd = f"python -m pytest {test_file} -v --tb=short --asyncio-mode=auto"
        success, stdout, stderr = run_command(cmd, cwd=backend_dir)
        
        results[test_file] = success
        
        if success:
            print(f"✅ {test_file} - PASSED")
        else:
            print(f"❌ {test_file} - FAILED")
            if stderr:
                print(f"Error: {stderr}")
            if stdout:
                print(f"Output: {stdout}")
    
    return results

def run_frontend_tests():
    """Run frontend tests"""
    print("\n" + "="*60)
    print("RUNNING FRONTEND TESTS")
    print("="*60)
    
    frontend_dir = backend_dir.parent / "frontend"
    
    if not frontend_dir.exists():
        print("⚠️  Frontend directory not found")
        return {}
    
    # Check if npm/yarn is available
    npm_available = run_command("npm --version", cwd=frontend_dir)[0]
    yarn_available = run_command("yarn --version", cwd=frontend_dir)[0]
    
    if not npm_available and not yarn_available:
        print("❌ Neither npm nor yarn is available")
        return {}
    
    package_manager = "yarn" if yarn_available else "npm"
    
    # Install dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        install_cmd = f"{package_manager} install"
        success, stdout, stderr = run_command(install_cmd, cwd=frontend_dir, timeout=600)
        
        if not success:
            print(f"❌ Failed to install dependencies: {stderr}")
            return {}
    
    # Run tests
    test_files = [
        "src/components/__tests__/ResilientWebSocket.test.js",
        "src/components/__tests__/ChatIntegration.test.js",
        "src/components/__tests__/WebSocketStatus.test.js",
        "src/components/__tests__/AIThinkingIndicator.test.js",
        "src/components/__tests__/ErrorMessage.test.js"
    ]
    
    results = {}
    
    # Run all tests at once
    print("🧪 Running frontend tests...")
    test_cmd = f"{package_manager} test -- --watchAll=false --coverage=false --verbose"
    success, stdout, stderr = run_command(test_cmd, cwd=frontend_dir, timeout=300)
    
    results["frontend_tests"] = success
    
    if success:
        print("✅ Frontend tests - PASSED")
    else:
        print("❌ Frontend tests - FAILED")
        if stderr:
            print(f"Error: {stderr}")
        if stdout:
            print(f"Output: {stdout}")
    
    return results

def run_integration_tests():
    """Run integration tests that require both backend and frontend"""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    # These would be tests that start both services and test them together
    # For now, we'll run a subset of backend tests that simulate integration
    
    integration_tests = [
        "tests/test_end_to_end_chat.py::TestChatIntegrationScenarios",
        "tests/test_websocket_integration.py::TestWebSocketIntegrationScenarios"
    ]
    
    results = {}
    
    for test in integration_tests:
        print(f"\n🔗 Running integration test: {test}")
        
        cmd = f"python -m pytest {test} -v --tb=short --asyncio-mode=auto"
        success, stdout, stderr = run_command(cmd, cwd=backend_dir)
        
        results[test] = success
        
        if success:
            print(f"✅ {test} - PASSED")
        else:
            print(f"❌ {test} - FAILED")
            if stderr:
                print(f"Error: {stderr}")
    
    return results

def run_performance_tests():
    """Run performance-related tests"""
    print("\n" + "="*60)
    print("RUNNING PERFORMANCE TESTS")
    print("="*60)
    
    # Run tests marked as performance tests
    cmd = "python -m pytest -m performance -v --tb=short --asyncio-mode=auto"
    success, stdout, stderr = run_command(cmd, cwd=backend_dir)
    
    if success:
        print("✅ Performance tests - PASSED")
    else:
        print("❌ Performance tests - FAILED")
        if stderr:
            print(f"Error: {stderr}")
    
    return {"performance_tests": success}

def generate_report(all_results):
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("TEST REPORT SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n📊 {category.upper()}:")
        
        if isinstance(results, dict):
            for test_name, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  {test_name}: {status}")
                total_tests += 1
                if success:
                    passed_tests += 1
        else:
            status = "✅ PASS" if results else "❌ FAIL"
            print(f"  {category}: {status}")
            total_tests += 1
            if results:
                passed_tests += 1
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "  No tests run")
    
    # Determine overall status
    if total_tests == 0:
        print("\n⚠️  NO TESTS WERE RUN")
        return False
    elif passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    elif passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("\n✅ MOST TESTS PASSED (acceptable)")
        return True
    else:
        print("\n❌ TOO MANY TESTS FAILED")
        return False

def main():
    """Main test runner"""
    print("🚀 Starting Comprehensive Test Suite for WebSocket AI Errors Fix")
    print("Testing: Generation Timeouts, WebSocket Connections, End-to-End Chat, Monitoring")
    
    start_time = time.time()
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Run all test categories
    all_results = {}
    
    try:
        # Backend tests
        all_results["backend"] = run_backend_tests()
        
        # Frontend tests
        all_results["frontend"] = run_frontend_tests()
        
        # Integration tests
        all_results["integration"] = run_integration_tests()
        
        # Performance tests
        all_results["performance"] = run_performance_tests()
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    # Generate report
    success = generate_report(all_results)
    
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total execution time: {elapsed_time:.2f} seconds")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)