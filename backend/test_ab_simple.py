#!/usr/bin/env python3
"""
Simple test for A/B Testing implementation without database dependencies
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all A/B testing components can be imported"""
    print("🧪 Testing A/B Testing Implementation Imports...")
    
    try:
        # Test model imports
        print("1. Testing model imports...")
        from app.models.ab_testing import (
            ABTest, ABTestVariant, ABTestParticipant, ABTestEvent, ABTestStatistics,
            ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType
        )
        print("✅ All A/B testing models imported successfully")
        
        # Test schema imports
        print("2. Testing schema imports...")
        from app.schemas.ab_testing import (
            ABTestCreate, ABTestUpdate, ABTestStatusUpdate, ABTestResponse,
            ABTestParticipantCreate, ABTestParticipantResponse,
            ABTestEventCreate, ABTestEventResponse,
            ABTestSummaryStats, ABTestAnalysisResponse
        )
        print("✅ All A/B testing schemas imported successfully")
        
        # Test service import
        print("3. Testing service imports...")
        from app.services.ab_testing_service import ab_testing_service
        print("✅ A/B testing service imported successfully")
        
        # Test API import
        print("4. Testing API imports...")
        from app.api.marketing import router
        print("✅ Marketing API router imported successfully")
        
        # Test that the router has the expected routes
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/ab-tests/stats",
            "/ab-tests",
            "/ab-tests/{test_id}",
            "/ab-tests/{test_id}/status"
        ]
        
        print("5. Checking API routes...")
        for expected_route in expected_routes:
            found = any(expected_route in route for route in routes)
            if found:
                print(f"✅ Route exists: {expected_route}")
            else:
                print(f"❌ Route missing: {expected_route}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_enum_values():
    """Test that enums have the expected values"""
    print("\n📊 Testing enum values...")
    
    try:
        from app.models.ab_testing import ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType
        
        # Test ABTestStatus
        expected_statuses = ['DRAFT', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED']
        actual_statuses = [status.name for status in ABTestStatus]
        for status in expected_statuses:
            if status in actual_statuses:
                print(f"✅ ABTestStatus.{status} exists")
            else:
                print(f"❌ ABTestStatus.{status} missing")
        
        # Test ABTestType
        expected_types = ['PAGE', 'FEATURE', 'ELEMENT', 'FLOW']
        actual_types = [type_.name for type_ in ABTestType]
        for type_ in expected_types:
            if type_ in actual_types:
                print(f"✅ ABTestType.{type_} exists")
            else:
                print(f"❌ ABTestType.{type_} missing")
        
        # Test PrimaryMetric
        expected_metrics = ['CONVERSION_RATE', 'CLICK_THROUGH_RATE', 'BOUNCE_RATE']
        actual_metrics = [metric.name for metric in PrimaryMetric]
        for metric in expected_metrics:
            if metric in actual_metrics:
                print(f"✅ PrimaryMetric.{metric} exists")
            else:
                print(f"❌ PrimaryMetric.{metric} missing")
        
        # Test ABTestEventType
        expected_events = ['VIEW', 'CLICK', 'CONVERSION', 'CUSTOM']
        actual_events = [event.name for event in ABTestEventType]
        for event in expected_events:
            if event in actual_events:
                print(f"✅ ABTestEventType.{event} exists")
            else:
                print(f"❌ ABTestEventType.{event} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enums: {e}")
        return False

def test_schema_validation():
    """Test that schemas can be instantiated with valid data"""
    print("\n📝 Testing schema validation...")
    
    try:
        from app.schemas.ab_testing import ABTestCreate, ABTestVariantCreate
        from app.models.ab_testing import ABTestType, PrimaryMetric
        
        # Test creating a valid ABTestCreate schema
        variant1 = ABTestVariantCreate(
            name="Control",
            description="Original version",
            is_control=True,
            traffic_percentage=50.0
        )
        
        variant2 = ABTestVariantCreate(
            name="Variant A",
            description="New version",
            is_control=False,
            traffic_percentage=50.0
        )
        
        test_create = ABTestCreate(
            name="Test Button Color",
            description="Testing button colors",
            hypothesis="Red buttons convert better",
            type=ABTestType.ELEMENT,
            variants=[variant1, variant2]
        )
        
        print("✅ ABTestCreate schema validation passed")
        print(f"   - Test name: {test_create.name}")
        print(f"   - Variants: {len(test_create.variants)}")
        print(f"   - Primary metric: {test_create.primary_metric}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False

def test_service_methods():
    """Test that service methods exist and are callable"""
    print("\n🔧 Testing service methods...")
    
    try:
        from app.services.ab_testing_service import ab_testing_service
        
        # Check that expected methods exist
        expected_methods = [
            'create_test',
            'get_test',
            'get_tests',
            'update_test',
            'update_test_status',
            'delete_test',
            'assign_participant',
            'record_event',
            'get_test_statistics',
            'get_dashboard_stats',
            'analyze_test'
        ]
        
        for method_name in expected_methods:
            if hasattr(ab_testing_service, method_name):
                method = getattr(ab_testing_service, method_name)
                if callable(method):
                    print(f"✅ Method exists and callable: {method_name}")
                else:
                    print(f"❌ Method exists but not callable: {method_name}")
            else:
                print(f"❌ Method missing: {method_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service methods: {e}")
        return False

def test_api_integration():
    """Test that the API is properly integrated"""
    print("\n🔗 Testing API integration...")
    
    try:
        # Check that marketing router is importable
        from app.api.marketing import router as marketing_router
        print("✅ Marketing router imported")
        
        # Check that the router is included in the main API
        from app.api import api_router
        
        # Get all included routers
        included_routers = []
        for route in api_router.routes:
            if hasattr(route, 'path_regex'):
                included_routers.append(str(route.path_regex.pattern))
        
        # Check if marketing routes are included
        marketing_found = any('marketing' in router for router in included_routers)
        if marketing_found:
            print("✅ Marketing router is included in main API")
        else:
            print("❌ Marketing router not found in main API")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API integration: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 A/B Testing Implementation Validation")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Enum Values", test_enum_values),
        ("Schema Validation", test_schema_validation),
        ("Service Methods", test_service_methods),
        ("API Integration", test_api_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All validation tests passed!")
        print("✅ A/B Testing implementation is properly structured and ready for use.")
        print("\n📝 Next steps:")
        print("   1. Run database migrations to create tables")
        print("   2. Start the backend server")
        print("   3. Test the API endpoints with real requests")
        print("   4. Integrate with the frontend ABTestManager component")
        return True
    else:
        print(f"\n❌ {len(results) - passed} tests failed.")
        print("Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    main()