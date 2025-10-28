from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_admin_user
from ..models.user import User
from ..models.ab_testing import ABTestStatus, ABTestType
from ..schemas.ab_testing import (
    ABTestCreate, ABTestUpdate, ABTestStatusUpdate, ABTestResponse,
    ABTestParticipantCreate, ABTestParticipantResponse,
    ABTestEventCreate, ABTestEventResponse,
    ABTestSummaryStats, ABTestDashboardResponse,
    ABTestAnalysisRequest, ABTestAnalysisResponse,
    ABTestBulkStatusUpdate, ABTestBulkDeleteRequest,
    ABTestExportRequest, ABTestExportResponse
)
from ..services.ab_testing_service import ab_testing_service

router = APIRouter()
logger = logging.getLogger(__name__)


# A/B Test Management Endpoints
@router.get("/ab-tests/stats", response_model=ABTestSummaryStats)
async def get_ab_test_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get A/B testing dashboard statistics"""
    try:
        stats = await ab_testing_service.get_dashboard_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting A/B test stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get A/B test statistics")


@router.get("/ab-tests", response_model=List[ABTestResponse])
async def get_ab_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[List[ABTestStatus]] = Query(None),
    creator_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get list of A/B tests with optional filtering"""
    try:
        tests = await ab_testing_service.get_tests(
            db=db,
            skip=skip,
            limit=limit,
            status_filter=status,
            creator_id=creator_id
        )
        return tests
    except Exception as e:
        logger.error(f"Error getting A/B tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to get A/B tests")


@router.get("/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific A/B test"""
    try:
        test = await ab_testing_service.get_test(db, test_id)
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        return test
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get A/B test")


@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    test_data: ABTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new A/B test"""
    try:
        test = await ab_testing_service.create_test(db, test_data, current_user.id)
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to create A/B test")


@router.put("/ab-tests/{test_id}", response_model=ABTestResponse)
async def update_ab_test(
    test_id: int,
    test_data: ABTestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing A/B test"""
    try:
        test = await ab_testing_service.update_test(db, test_id, test_data)
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating A/B test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update A/B test")


@router.patch("/ab-tests/{test_id}/status", response_model=ABTestResponse)
async def update_ab_test_status(
    test_id: int,
    status_data: ABTestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update the status of an A/B test"""
    try:
        test = await ab_testing_service.update_test_status(db, test_id, status_data)
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating A/B test status {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update A/B test status")


@router.delete("/ab-tests/{test_id}")
async def delete_ab_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete an A/B test"""
    try:
        success = await ab_testing_service.delete_test(db, test_id)
        if not success:
            raise HTTPException(status_code=404, detail="A/B test not found")
        return {"message": "A/B test deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting A/B test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete A/B test")


# Participant Management Endpoints
@router.post("/ab-tests/{test_id}/participants", response_model=ABTestParticipantResponse)
async def assign_participant(
    test_id: int,
    participant_data: ABTestParticipantCreate,
    db: Session = Depends(get_db)
):
    """Assign a participant to an A/B test variant"""
    try:
        participant = await ab_testing_service.assign_participant(
            db=db,
            test_id=test_id,
            user_id=participant_data.user_id,
            session_id=participant_data.session_id,
            user_agent=participant_data.user_agent,
            ip_address=participant_data.ip_address
        )
        
        if not participant:
            raise HTTPException(
                status_code=400, 
                detail="Unable to assign participant (test not running or user excluded)"
            )
        
        return participant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning participant to test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign participant")


@router.post("/ab-tests/events", response_model=ABTestEventResponse)
async def record_ab_test_event(
    event_data: ABTestEventCreate,
    db: Session = Depends(get_db)
):
    """Record an event for an A/B test participant"""
    try:
        event = await ab_testing_service.record_event(db, event_data)
        if not event:
            raise HTTPException(status_code=404, detail="Participant not found")
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording A/B test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to record event")


# Analytics and Statistics Endpoints
@router.get("/ab-tests/{test_id}/statistics")
async def get_ab_test_statistics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive statistics for an A/B test"""
    try:
        stats = await ab_testing_service.get_test_statistics(db, test_id)
        if not stats:
            raise HTTPException(status_code=404, detail="A/B test not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test statistics {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get test statistics")


@router.post("/ab-tests/{test_id}/analyze", response_model=ABTestAnalysisResponse)
async def analyze_ab_test(
    test_id: int,
    analysis_request: ABTestAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Perform statistical analysis of an A/B test"""
    try:
        # Perform analysis in background for large datasets
        if analysis_request.force_analysis:
            background_tasks.add_task(
                ab_testing_service.analyze_test,
                db, test_id, analysis_request.force_analysis
            )
            return ABTestAnalysisResponse(
                test_id=test_id,
                analysis_completed=False,
                confidence_level=95.0,
                statistical_significance=False,
                recommendations=["Analysis started in background. Check back later for results."],
                analysis_details={"status": "processing"}
            )
        else:
            analysis = await ab_testing_service.analyze_test(db, test_id, analysis_request.force_analysis)
            return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing A/B test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze A/B test")


# Bulk Operations Endpoints
@router.patch("/ab-tests/bulk/status")
async def bulk_update_ab_test_status(
    bulk_update: ABTestBulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update status of multiple A/B tests"""
    try:
        results = []
        errors = []
        
        for test_id in bulk_update.test_ids:
            try:
                status_data = ABTestStatusUpdate(status=bulk_update.status)
                test = await ab_testing_service.update_test_status(db, test_id, status_data)
                if test:
                    results.append({"test_id": test_id, "status": "updated"})
                else:
                    errors.append({"test_id": test_id, "error": "Test not found"})
            except Exception as e:
                errors.append({"test_id": test_id, "error": str(e)})
        
        return {
            "updated": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
    except Exception as e:
        logger.error(f"Error in bulk status update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update test statuses")


@router.delete("/ab-tests/bulk")
async def bulk_delete_ab_tests(
    bulk_delete: ABTestBulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete multiple A/B tests"""
    try:
        results = []
        errors = []
        
        for test_id in bulk_delete.test_ids:
            try:
                success = await ab_testing_service.delete_test(db, test_id)
                if success:
                    results.append({"test_id": test_id, "status": "deleted"})
                else:
                    errors.append({"test_id": test_id, "error": "Test not found"})
            except Exception as e:
                errors.append({"test_id": test_id, "error": str(e)})
        
        return {
            "deleted": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tests")


# Export Endpoints
@router.post("/ab-tests/export", response_model=ABTestExportResponse)
async def export_ab_tests(
    export_request: ABTestExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Export A/B test data in various formats"""
    try:
        # For now, return a placeholder response
        # In a real implementation, this would generate the export file
        import uuid
        from datetime import datetime, timedelta
        
        export_id = str(uuid.uuid4())
        
        # Add background task to generate export
        # background_tasks.add_task(generate_ab_test_export, export_request, export_id)
        
        return ABTestExportResponse(
            export_id=export_id,
            status="processing",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
    except Exception as e:
        logger.error(f"Error exporting A/B tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to export A/B tests")


# Public API for frontend integration (no auth required)
@router.get("/ab-tests/{test_id}/variant")
async def get_user_variant(
    test_id: int,
    user_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    user_agent: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get the assigned variant for a user (public endpoint for frontend)"""
    try:
        if not user_id and not session_id:
            raise HTTPException(status_code=400, detail="Either user_id or session_id is required")
        
        participant = await ab_testing_service.assign_participant(
            db=db,
            test_id=test_id,
            user_id=user_id,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        if not participant:
            return {"assigned": False, "reason": "Not included in test"}
        
        return {
            "assigned": True,
            "participant_id": participant.id,
            "variant_id": participant.variant_id,
            "test_id": participant.test_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user variant for test {test_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user variant")


@router.post("/ab-tests/track")
async def track_ab_test_event(
    event_data: ABTestEventCreate,
    db: Session = Depends(get_db)
):
    """Track an A/B test event (public endpoint for frontend)"""
    try:
        event = await ab_testing_service.record_event(db, event_data)
        if not event:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        return {"success": True, "event_id": event.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking A/B test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track event")