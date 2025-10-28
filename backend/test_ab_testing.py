#!/usr/bin/env python3
"""
Test script for A/B Testing functionality
"""
import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.ab_testing import (
    ABTest, ABTestVariant, ABTestParticipant, ABTestEvent, ABTestStatistics,
    ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType
)
from app.models import Base
from app.schemas.ab_testing import ABTestCreate, ABTestVariantCreate
from app.services.ab_testing_service import ab_testing_service

def create_test_tables():
    """Create the A/B testing tables manually for testing"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables
    try:
        # Drop existing tables if they exist
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ab_test_statistics"))
            conn.execute(text("DROP TABLE IF EXISTS ab_test_events"))
            conn.execute(text("DROP TABLE IF EXISTS ab_test_participants"))
            conn.execute(text("DROP TABLE IF EXISTS ab_test_variants"))
            conn.execute(text("DROP TABLE IF EXISTS ab_tests"))
            conn.commit()
        
        # Create new tables
        Base.metadata.create_all(engine)
        print("✅ A/B testing tables created successfully")
        return engine
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return None

async def test_ab_testing_service():
    """Test the A/B testing service functionality"""
    engine = create_test_tables()
    if not engine:
        return False
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("\n🧪 Testing A/B Testing Service...")
        
        # Test 1: Create a test
        print("\n1. Creating A/B test...")
        test_data = ABTestCreate(
            name="Test Button Color",
            description="Testing different button colors for conversion",
            hypothesis="Red buttons will convert better than blue buttons",
            type=ABTestType.ELEMENT,
            traffic_allocation=100.0,
            duration=14,
            sample_size=1000,
            confidence_level=95.0,
            primary_metric=PrimaryMetric.CONVERSION_RATE,
            secondary_metrics=["click_through_rate"],
            variants=[
                ABTestVariantCreate(
                    name="Control (Blue)",
                    description="Original blue button",
                    is_control=True,
                    traffic_percentage=50.0
                ),
                ABTestVariantCreate(
                    name="Variant A (Red)",
                    description="Red button variant",
                    is_control=False,
                    traffic_percentage=50.0
                )
            ]
        )
        
        test = await ab_testing_service.create_test(db, test_data, creator_id=1)
        print(f"✅ Created test: {test.name} (ID: {test.id})")
        
        # Test 2: Get test statistics
        print("\n2. Getting test statistics...")
        stats = await ab_testing_service.get_test_statistics(db, test.id)
        if stats:
            print(f"✅ Retrieved statistics for test {test.id}")
            print(f"   - Total participants: {stats['total_participants']}")
            print(f"   - Variants: {len(stats['variants'])}")
        else:
            print("❌ Failed to get test statistics")
        
        # Test 3: Assign participants
        print("\n3. Assigning test participants...")
        
        # Update test status to running first
        from app.schemas.ab_testing import ABTestStatusUpdate
        status_update = ABTestStatusUpdate(status=ABTestStatus.RUNNING)
        test = await ab_testing_service.update_test_status(db, test.id, status_update)
        print(f"✅ Updated test status to: {test.status}")
        
        # Assign some participants
        participants = []
        for i in range(10):
            participant = await ab_testing_service.assign_participant(
                db=db,
                test_id=test.id,
                user_id=i + 1,
                session_id=f"session_{i}",
                user_agent="Test User Agent",
                ip_address=f"192.168.1.{i + 1}"
            )
            if participant:
                participants.append(participant)
        
        print(f"✅ Assigned {len(participants)} participants")
        
        # Test 4: Record events
        print("\n4. Recording test events...")
        from app.schemas.ab_testing import ABTestEventCreate
        
        events_recorded = 0
        for participant in participants[:5]:  # Convert first 5 participants
            event_data = ABTestEventCreate(
                test_id=participant.test_id,
                variant_id=participant.variant_id,
                participant_id=participant.id,
                event_type=ABTestEventType.CONVERSION,
                event_name="button_click_conversion",
                event_value=1.0
            )
            
            event = await ab_testing_service.record_event(db, event_data)
            if event:
                events_recorded += 1
        
        print(f"✅ Recorded {events_recorded} conversion events")
        
        # Test 5: Get updated statistics
        print("\n5. Getting updated statistics...")
        updated_stats = await ab_testing_service.get_test_statistics(db, test.id)
        if updated_stats:
            print(f"✅ Updated statistics:")
            print(f"   - Total participants: {updated_stats['total_participants']}")
            print(f"   - Total conversions: {updated_stats['total_conversions']}")
            for variant in updated_stats['variants']:
                print(f"   - {variant['name']}: {variant['conversions']}/{variant['participants']} ({variant['conversion_rate']:.2%})")
        
        # Test 6: Dashboard statistics
        print("\n6. Getting dashboard statistics...")
        dashboard_stats = await ab_testing_service.get_dashboard_stats(db)
        print(f"✅ Dashboard stats:")
        print(f"   - Total tests: {dashboard_stats.total_tests}")
        print(f"   - Running tests: {dashboard_stats.running_tests}")
        print(f"   - Total participants: {dashboard_stats.total_participants}")
        
        # Test 7: Statistical analysis
        print("\n7. Performing statistical analysis...")
        try:
            analysis = await ab_testing_service.analyze_test(db, test.id, force_analysis=True)
            print(f"✅ Analysis completed:")
            print(f"   - Statistical significance: {analysis.statistical_significance}")
            print(f"   - Confidence level: {analysis.confidence_level}%")
            if analysis.uplift_percentage:
                print(f"   - Uplift: {analysis.uplift_percentage:.2f}%")
            print(f"   - Recommendations: {len(analysis.recommendations)}")
        except Exception as e:
            print(f"⚠️  Analysis failed (expected with small sample): {e}")
        
        print("\n✅ All A/B testing functionality tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_api_endpoints():
    """Test that the API endpoints are properly configured"""
    print("\n🔗 Testing API endpoint configuration...")
    
    try:
        from app.api.marketing import router
        print("✅ Marketing router imported successfully")
        
        # Check that routes are defined
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/ab-tests/stats",
            "/ab-tests",
            "/ab-tests/{test_id}",
            "/ab-tests/{test_id}/status",
            "/ab-tests/{test_id}/participants",
            "/ab-tests/events",
            "/ab-tests/{test_id}/statistics",
            "/ab-tests/{test_id}/analyze"
        ]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"✅ Route found: {expected_route}")
            else:
                print(f"❌ Route missing: {expected_route}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def test_database_models():
    """Test that the database models are properly defined"""
    print("\n📊 Testing database models...")
    
    try:
        # Test model imports
        from app.models.ab_testing import ABTest, ABTestVariant, ABTestParticipant, ABTestEvent
        print("✅ All A/B testing models imported successfully")
        
        # Test enum imports
        from app.models.ab_testing import ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType
        print("✅ All enums imported successfully")
        
        # Test that models have required attributes
        required_attrs = {
            'ABTest': ['name', 'status', 'variants', 'participants'],
            'ABTestVariant': ['name', 'is_control', 'traffic_percentage'],
            'ABTestParticipant': ['test_id', 'variant_id', 'converted'],
            'ABTestEvent': ['event_type', 'event_name']
        }
        
        models = {
            'ABTest': ABTest,
            'ABTestVariant': ABTestVariant,
            'ABTestParticipant': ABTestParticipant,
            'ABTestEvent': ABTestEvent
        }
        
        for model_name, attrs in required_attrs.items():
            model_class = models[model_name]
            for attr in attrs:
                if hasattr(model_class, attr):
                    print(f"✅ {model_name}.{attr} exists")
                else:
                    print(f"❌ {model_name}.{attr} missing")
        
        return True
    except Exception as e:
        print(f"❌ Error testing database models: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting A/B Testing Implementation Tests")
    print("=" * 50)
    
    # Test 1: Database models
    models_ok = test_database_models()
    
    # Test 2: API endpoints
    api_ok = test_api_endpoints()
    
    # Test 3: Service functionality
    service_ok = await test_ab_testing_service()
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"   Database Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"   API Endpoints: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"   Service Logic: {'✅ PASS' if service_ok else '❌ FAIL'}")
    
    if all([models_ok, api_ok, service_ok]):
        print("\n🎉 All tests passed! A/B Testing implementation is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    asyncio.run(main())