import asyncio
import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError
import numpy as np
from scipy import stats
import logging

from ..models.ab_testing import (
    ABTest, ABTestVariant, ABTestParticipant, ABTestEvent, ABTestStatistics,
    ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType
)
from ..models.user import User
from ..schemas.ab_testing import (
    ABTestCreate, ABTestUpdate, ABTestStatusUpdate,
    ABTestParticipantCreate, ABTestEventCreate,
    ABTestSummaryStats, ABTestAnalysisResponse
)
from ..core.database import get_db

logger = logging.getLogger(__name__)


class ABTestingService:
    """Service for managing A/B tests and statistical analysis"""

    def __init__(self):
        self.logger = logger

    # Test Management
    async def create_test(self, db: Session, test_data: ABTestCreate, creator_id: int) -> ABTest:
        """Create a new A/B test with variants"""
        try:
            # Create the test
            test = ABTest(
                name=test_data.name,
                description=test_data.description,
                hypothesis=test_data.hypothesis,
                type=test_data.type,
                traffic_allocation=test_data.traffic_allocation,
                duration=test_data.duration,
                sample_size=test_data.sample_size,
                confidence_level=test_data.confidence_level,
                primary_metric=test_data.primary_metric,
                secondary_metrics=test_data.secondary_metrics or [],
                created_by=creator_id
            )
            
            db.add(test)
            db.flush()  # Get the test ID
            
            # Create variants
            for variant_data in test_data.variants:
                variant = ABTestVariant(
                    test_id=test.id,
                    name=variant_data.name,
                    description=variant_data.description,
                    is_control=variant_data.is_control,
                    traffic_percentage=variant_data.traffic_percentage,
                    configuration=variant_data.configuration or {}
                )
                db.add(variant)
            
            db.commit()
            db.refresh(test)
            
            self.logger.info(f"Created A/B test: {test.name} (ID: {test.id})")
            return test
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Failed to create A/B test: {e}")
            raise ValueError("Test name must be unique")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating A/B test: {e}")
            raise

    async def get_test(self, db: Session, test_id: int) -> Optional[ABTest]:
        """Get a specific A/B test with all related data"""
        return db.query(ABTest).filter(ABTest.id == test_id).first()

    async def get_tests(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[List[ABTestStatus]] = None,
        creator_id: Optional[int] = None
    ) -> List[ABTest]:
        """Get list of A/B tests with optional filtering"""
        query = db.query(ABTest)
        
        if status_filter:
            query = query.filter(ABTest.status.in_(status_filter))
        
        if creator_id:
            query = query.filter(ABTest.created_by == creator_id)
        
        return query.order_by(desc(ABTest.created_at)).offset(skip).limit(limit).all()

    async def update_test(self, db: Session, test_id: int, test_data: ABTestUpdate) -> Optional[ABTest]:
        """Update an existing A/B test"""
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        # Only allow updates if test is in draft status
        if test.status != ABTestStatus.DRAFT:
            raise ValueError("Can only update tests in draft status")
        
        # Update fields
        for field, value in test_data.dict(exclude_unset=True).items():
            setattr(test, field, value)
        
        test.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(test)
        
        self.logger.info(f"Updated A/B test: {test.name} (ID: {test.id})")
        return test

    async def update_test_status(self, db: Session, test_id: int, status_data: ABTestStatusUpdate) -> Optional[ABTest]:
        """Update the status of an A/B test"""
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        old_status = test.status
        new_status = status_data.status
        
        # Validate status transitions
        if not self._is_valid_status_transition(old_status, new_status):
            raise ValueError(f"Invalid status transition from {old_status} to {new_status}")
        
        test.status = new_status
        test.updated_at = datetime.utcnow()
        
        # Set timestamps based on status
        if new_status == ABTestStatus.RUNNING and old_status == ABTestStatus.DRAFT:
            test.started_at = datetime.utcnow()
        elif new_status in [ABTestStatus.COMPLETED, ABTestStatus.CANCELLED]:
            test.ended_at = datetime.utcnow()
        
        db.commit()
        db.refresh(test)
        
        self.logger.info(f"Updated test {test.id} status from {old_status} to {new_status}")
        return test

    async def delete_test(self, db: Session, test_id: int) -> bool:
        """Delete an A/B test and all related data"""
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return False
        
        # Only allow deletion of draft or completed tests
        if test.status not in [ABTestStatus.DRAFT, ABTestStatus.COMPLETED, ABTestStatus.CANCELLED]:
            raise ValueError("Can only delete draft, completed, or cancelled tests")
        
        db.delete(test)
        db.commit()
        
        self.logger.info(f"Deleted A/B test: {test.name} (ID: {test.id})")
        return True

    # Participant Management
    async def assign_participant(
        self, 
        db: Session, 
        test_id: int, 
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[ABTestParticipant]:
        """Assign a user to a test variant"""
        test = db.query(ABTest).filter(
            and_(ABTest.id == test_id, ABTest.status == ABTestStatus.RUNNING)
        ).first()
        
        if not test:
            return None
        
        # Check if user is already participating
        existing_participant = db.query(ABTestParticipant).filter(
            and_(
                ABTestParticipant.test_id == test_id,
                or_(
                    ABTestParticipant.user_id == user_id if user_id else False,
                    ABTestParticipant.session_id == session_id if session_id else False
                )
            )
        ).first()
        
        if existing_participant:
            return existing_participant
        
        # Determine if user should be included based on traffic allocation
        if not self._should_include_in_test(test.traffic_allocation, user_id, session_id):
            return None
        
        # Select variant based on traffic distribution
        variant = self._select_variant(test.variants, user_id, session_id)
        if not variant:
            return None
        
        # Create participant
        participant = ABTestParticipant(
            test_id=test_id,
            variant_id=variant.id,
            user_id=user_id,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(participant)
        
        # Update variant participant count
        variant.participants_count += 1
        
        db.commit()
        db.refresh(participant)
        
        self.logger.info(f"Assigned participant to test {test_id}, variant {variant.id}")
        return participant

    async def record_event(
        self, 
        db: Session, 
        event_data: ABTestEventCreate
    ) -> Optional[ABTestEvent]:
        """Record an event for a test participant"""
        participant = db.query(ABTestParticipant).filter(
            ABTestParticipant.id == event_data.participant_id
        ).first()
        
        if not participant:
            return None
        
        # Create event
        event = ABTestEvent(
            test_id=event_data.test_id,
            variant_id=event_data.variant_id,
            participant_id=event_data.participant_id,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            event_data=event_data.event_data or {},
            event_value=event_data.event_value
        )
        
        db.add(event)
        
        # Update participant metrics
        participant.last_interaction_at = datetime.utcnow()
        if not participant.first_interaction_at:
            participant.first_interaction_at = datetime.utcnow()
        
        if event_data.event_type == ABTestEventType.VIEW:
            participant.page_views += 1
        elif event_data.event_type == ABTestEventType.CONVERSION:
            if not participant.converted:
                participant.converted = True
                participant.conversion_at = datetime.utcnow()
                participant.conversion_value = event_data.event_value or 0
                
                # Update variant conversion count
                variant = db.query(ABTestVariant).filter(
                    ABTestVariant.id == event_data.variant_id
                ).first()
                if variant:
                    variant.conversions_count += 1
                    variant.total_revenue += event_data.event_value or 0
        
        db.commit()
        db.refresh(event)
        
        return event

    # Analytics and Statistics
    async def get_test_statistics(self, db: Session, test_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive statistics for a test"""
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        # Get variant statistics
        variant_stats = []
        for variant in test.variants:
            stats_data = {
                'variant_id': variant.id,
                'name': variant.name,
                'is_control': variant.is_control,
                'participants': variant.participants_count,
                'conversions': variant.conversions_count,
                'conversion_rate': variant.conversions_count / variant.participants_count if variant.participants_count > 0 else 0,
                'total_revenue': variant.total_revenue,
                'revenue_per_user': variant.total_revenue / variant.participants_count if variant.participants_count > 0 else 0
            }
            variant_stats.append(stats_data)
        
        # Perform statistical analysis if test has enough data
        analysis_results = None
        if len(variant_stats) >= 2 and all(v['participants'] >= 30 for v in variant_stats):
            analysis_results = await self._perform_statistical_analysis(variant_stats, test.confidence_level)
        
        return {
            'test_id': test_id,
            'test_name': test.name,
            'status': test.status,
            'started_at': test.started_at,
            'duration_days': test.duration,
            'variants': variant_stats,
            'statistical_analysis': analysis_results,
            'total_participants': sum(v['participants'] for v in variant_stats),
            'total_conversions': sum(v['conversions'] for v in variant_stats)
        }

    async def get_dashboard_stats(self, db: Session) -> ABTestSummaryStats:
        """Get summary statistics for the A/B testing dashboard"""
        # Basic counts
        total_tests = db.query(ABTest).count()
        running_tests = db.query(ABTest).filter(ABTest.status == ABTestStatus.RUNNING).count()
        completed_tests = db.query(ABTest).filter(ABTest.status == ABTestStatus.COMPLETED).count()
        
        # Successful tests (with statistical significance)
        successful_tests = db.query(ABTestStatistics).filter(
            ABTestStatistics.is_significant == True
        ).count()
        
        # Total participants
        total_participants = db.query(func.sum(ABTestVariant.participants_count)).scalar() or 0
        
        # Average uplift from successful tests
        avg_uplift_result = db.query(func.avg(ABTestStatistics.uplift_percentage)).filter(
            ABTestStatistics.is_significant == True
        ).scalar()
        
        # Average confidence from all completed analyses
        avg_confidence_result = db.query(func.avg(ABTestStatistics.confidence_level)).scalar()
        
        return ABTestSummaryStats(
            total_tests=total_tests,
            running_tests=running_tests,
            completed_tests=completed_tests,
            successful_tests=successful_tests,
            total_participants=total_participants,
            average_uplift=float(avg_uplift_result) if avg_uplift_result else None,
            average_confidence=float(avg_confidence_result) if avg_confidence_result else None
        )

    async def analyze_test(self, db: Session, test_id: int, force_analysis: bool = False) -> ABTestAnalysisResponse:
        """Perform comprehensive statistical analysis of a test"""
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise ValueError("Test not found")
        
        # Get current statistics
        stats = await self.get_test_statistics(db, test_id)
        if not stats:
            raise ValueError("Unable to get test statistics")
        
        variant_stats = stats['variants']
        
        # Check if we have enough data for analysis
        min_sample_size = 30  # Minimum for statistical significance
        if not force_analysis and any(v['participants'] < min_sample_size for v in variant_stats):
            return ABTestAnalysisResponse(
                test_id=test_id,
                analysis_completed=False,
                confidence_level=test.confidence_level,
                statistical_significance=False,
                recommendations=["Need more data for statistical analysis (minimum 30 participants per variant)"],
                analysis_details={"error": "Insufficient sample size"}
            )
        
        # Perform statistical analysis
        analysis_results = await self._perform_statistical_analysis(variant_stats, test.confidence_level)
        
        # Save analysis results
        statistics_record = ABTestStatistics(
            test_id=test_id,
            sample_size=stats['total_participants'],
            confidence_level=test.confidence_level,
            is_significant=analysis_results.get('is_significant', False),
            uplift_percentage=analysis_results.get('uplift_percentage'),
            p_value=analysis_results.get('p_value'),
            winner_variant_id=analysis_results.get('winner_variant_id'),
            analysis_data=analysis_results
        )
        
        db.add(statistics_record)
        
        # Update test results
        test.results = analysis_results
        if analysis_results.get('winner_variant_id'):
            test.winner_variant_id = analysis_results['winner_variant_id']
        
        db.commit()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis_results, variant_stats)
        
        return ABTestAnalysisResponse(
            test_id=test_id,
            analysis_completed=True,
            winner_variant_id=analysis_results.get('winner_variant_id'),
            confidence_level=test.confidence_level,
            statistical_significance=analysis_results.get('is_significant', False),
            uplift_percentage=analysis_results.get('uplift_percentage'),
            p_value=analysis_results.get('p_value'),
            bayesian_probability=analysis_results.get('bayesian_probability'),
            recommendations=recommendations,
            analysis_details=analysis_results
        )

    # Private helper methods
    def _is_valid_status_transition(self, old_status: ABTestStatus, new_status: ABTestStatus) -> bool:
        """Check if a status transition is valid"""
        valid_transitions = {
            ABTestStatus.DRAFT: [ABTestStatus.RUNNING, ABTestStatus.CANCELLED],
            ABTestStatus.RUNNING: [ABTestStatus.PAUSED, ABTestStatus.COMPLETED, ABTestStatus.CANCELLED],
            ABTestStatus.PAUSED: [ABTestStatus.RUNNING, ABTestStatus.COMPLETED, ABTestStatus.CANCELLED],
            ABTestStatus.COMPLETED: [],  # Terminal state
            ABTestStatus.CANCELLED: []   # Terminal state
        }
        
        return new_status in valid_transitions.get(old_status, [])

    def _should_include_in_test(self, traffic_allocation: float, user_id: Optional[int], session_id: Optional[str]) -> bool:
        """Determine if a user should be included in the test based on traffic allocation"""
        if traffic_allocation >= 100:
            return True
        
        # Use consistent hashing to ensure same user always gets same decision
        identifier = str(user_id) if user_id else session_id or "anonymous"
        hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= traffic_allocation

    def _select_variant(self, variants: List[ABTestVariant], user_id: Optional[int], session_id: Optional[str]) -> Optional[ABTestVariant]:
        """Select a variant for a user based on traffic distribution"""
        if not variants:
            return None
        
        # Use consistent hashing for variant selection
        identifier = str(user_id) if user_id else session_id or "anonymous"
        hash_value = int(hashlib.md5(f"variant_{identifier}".encode()).hexdigest(), 16)
        percentage = hash_value % 100
        
        # Select variant based on cumulative traffic percentages
        cumulative = 0
        for variant in sorted(variants, key=lambda v: v.id):  # Ensure consistent ordering
            cumulative += variant.traffic_percentage
            if percentage < cumulative:
                return variant
        
        # Fallback to first variant
        return variants[0]

    async def _perform_statistical_analysis(self, variant_stats: List[Dict], confidence_level: float) -> Dict[str, Any]:
        """Perform statistical analysis on variant data"""
        if len(variant_stats) < 2:
            return {"error": "Need at least 2 variants for analysis"}
        
        # Find control variant
        control_variant = next((v for v in variant_stats if v.get('is_control')), variant_stats[0])
        test_variants = [v for v in variant_stats if not v.get('is_control')]
        
        results = {
            'control_variant_id': control_variant['variant_id'],
            'control_conversion_rate': control_variant['conversion_rate'],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'confidence_level': confidence_level,
            'variant_comparisons': []
        }
        
        best_variant = control_variant
        best_p_value = 1.0
        
        # Compare each test variant against control
        for test_variant in test_variants:
            comparison = self._compare_variants(control_variant, test_variant, confidence_level)
            results['variant_comparisons'].append(comparison)
            
            # Track best performing variant
            if comparison.get('is_significant') and comparison.get('p_value', 1) < best_p_value:
                best_variant = test_variant
                best_p_value = comparison.get('p_value', 1)
        
        # Overall results
        results['is_significant'] = any(c.get('is_significant') for c in results['variant_comparisons'])
        results['winner_variant_id'] = best_variant['variant_id']
        
        if best_variant != control_variant:
            uplift = ((best_variant['conversion_rate'] - control_variant['conversion_rate']) / 
                     control_variant['conversion_rate'] * 100) if control_variant['conversion_rate'] > 0 else 0
            results['uplift_percentage'] = uplift
        else:
            results['uplift_percentage'] = 0
        
        results['p_value'] = best_p_value
        
        return results

    def _compare_variants(self, control: Dict, test: Dict, confidence_level: float) -> Dict[str, Any]:
        """Compare two variants using statistical tests"""
        # Extract data
        control_conversions = control['conversions']
        control_participants = control['participants']
        test_conversions = test['conversions']
        test_participants = test['participants']
        
        # Avoid division by zero
        if control_participants == 0 or test_participants == 0:
            return {
                'test_variant_id': test['variant_id'],
                'is_significant': False,
                'p_value': 1.0,
                'error': 'Insufficient data'
            }
        
        # Two-proportion z-test
        p1 = control_conversions / control_participants
        p2 = test_conversions / test_participants
        
        # Pooled proportion
        p_pool = (control_conversions + test_conversions) / (control_participants + test_participants)
        
        # Standard error
        se = np.sqrt(p_pool * (1 - p_pool) * (1/control_participants + 1/test_participants))
        
        if se == 0:
            return {
                'test_variant_id': test['variant_id'],
                'is_significant': False,
                'p_value': 1.0,
                'error': 'No variance in data'
            }
        
        # Z-score
        z_score = (p2 - p1) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Statistical significance
        alpha = (100 - confidence_level) / 100
        is_significant = p_value < alpha
        
        # Effect size (Cohen's h)
        h = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
        
        # Confidence interval for difference in proportions
        diff = p2 - p1
        se_diff = np.sqrt(p1 * (1 - p1) / control_participants + p2 * (1 - p2) / test_participants)
        z_critical = stats.norm.ppf(1 - alpha/2)
        ci_lower = diff - z_critical * se_diff
        ci_upper = diff + z_critical * se_diff
        
        return {
            'test_variant_id': test['variant_id'],
            'control_conversion_rate': p1,
            'test_conversion_rate': p2,
            'difference': diff,
            'relative_uplift': (diff / p1 * 100) if p1 > 0 else 0,
            'z_score': z_score,
            'p_value': p_value,
            'is_significant': is_significant,
            'effect_size': h,
            'confidence_interval_lower': ci_lower,
            'confidence_interval_upper': ci_upper,
            'sample_size_control': control_participants,
            'sample_size_test': test_participants
        }

    def _generate_recommendations(self, analysis_results: Dict, variant_stats: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on analysis results"""
        recommendations = []
        
        if not analysis_results.get('is_significant'):
            recommendations.append("No statistically significant difference found between variants")
            
            # Check sample size
            total_participants = sum(v['participants'] for v in variant_stats)
            if total_participants < 1000:
                recommendations.append("Consider running the test longer to gather more data")
            
            # Check conversion rates
            conversion_rates = [v['conversion_rate'] for v in variant_stats]
            if max(conversion_rates) - min(conversion_rates) < 0.01:  # Less than 1% difference
                recommendations.append("Conversion rates are very similar - consider testing more dramatic changes")
        
        else:
            winner_id = analysis_results.get('winner_variant_id')
            winner = next((v for v in variant_stats if v['variant_id'] == winner_id), None)
            
            if winner:
                uplift = analysis_results.get('uplift_percentage', 0)
                recommendations.append(f"Variant '{winner['name']}' shows significant improvement (+{uplift:.1f}%)")
                recommendations.append("Consider implementing the winning variant for all users")
                
                if uplift > 20:
                    recommendations.append("Exceptional results! Investigate what made this variant so successful")
        
        # Check for low conversion rates
        avg_conversion = sum(v['conversion_rate'] for v in variant_stats) / len(variant_stats)
        if avg_conversion < 0.02:  # Less than 2%
            recommendations.append("Overall conversion rates are low - consider optimizing the entire funnel")
        
        return recommendations


# Global service instance
ab_testing_service = ABTestingService()