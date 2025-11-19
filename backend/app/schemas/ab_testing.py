from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from ..models.ab_testing import ABTestStatus, ABTestType, PrimaryMetric, ABTestEventType


# Base schemas
class ABTestVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_control: bool = False
    traffic_percentage: float = Field(..., ge=0, le=100)
    configuration: Optional[Dict[str, Any]] = None


class ABTestVariantCreate(ABTestVariantBase):
    pass


class ABTestVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    traffic_percentage: Optional[float] = Field(None, ge=0, le=100)
    configuration: Optional[Dict[str, Any]] = None


class ABTestVariantResponse(ABTestVariantBase):
    id: int
    test_id: int
    participants_count: int = 0
    conversions_count: int = 0
    total_revenue: float = 0.0
    conversion_rate: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    statistical_significance: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# A/B Test schemas
class ABTestBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    type: ABTestType = ABTestType.PAGE
    traffic_allocation: float = Field(100.0, ge=0, le=100)
    duration: int = Field(14, ge=1, le=365)
    sample_size: int = Field(1000, ge=100)
    confidence_level: float = Field(95.0, ge=80, le=99.9)
    primary_metric: PrimaryMetric = PrimaryMetric.CONVERSION_RATE
    secondary_metrics: Optional[List[str]] = None


class ABTestCreate(ABTestBase):
    variants: List[ABTestVariantCreate] = Field(..., min_items=2)

    @validator('variants')
    def validate_variants(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 variants are required')
        
        # Check that traffic percentages sum to 100
        total_traffic = sum(variant.traffic_percentage for variant in v)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError('Variant traffic percentages must sum to 100%')
        
        # Check that exactly one variant is control
        control_count = sum(1 for variant in v if variant.is_control)
        if control_count != 1:
            raise ValueError('Exactly one variant must be marked as control')
        
        return v


class ABTestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    traffic_allocation: Optional[float] = Field(None, ge=0, le=100)
    duration: Optional[int] = Field(None, ge=1, le=365)
    sample_size: Optional[int] = Field(None, ge=100)
    confidence_level: Optional[float] = Field(None, ge=80, le=99.9)
    primary_metric: Optional[PrimaryMetric] = None
    secondary_metrics: Optional[List[str]] = None


class ABTestStatusUpdate(BaseModel):
    status: ABTestStatus


class ABTestResponse(ABTestBase):
    id: int
    status: ABTestStatus
    results: Optional[Dict[str, Any]] = None
    winner_variant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: int
    variants: List[ABTestVariantResponse] = []

    class Config:
        from_attributes = True


# Participant schemas
class ABTestParticipantBase(BaseModel):
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class ABTestParticipantCreate(ABTestParticipantBase):
    test_id: int
    variant_id: int


class ABTestParticipantResponse(ABTestParticipantBase):
    id: int
    test_id: int
    variant_id: int
    assigned_at: datetime
    first_interaction_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    converted: bool = False
    conversion_value: Optional[float] = None
    conversion_at: Optional[datetime] = None
    session_duration: Optional[int] = None
    page_views: int = 0
    bounce: bool = False

    class Config:
        from_attributes = True


# Event schemas
class ABTestEventBase(BaseModel):
    event_type: ABTestEventType
    event_name: str = Field(..., min_length=1, max_length=255)
    event_data: Optional[Dict[str, Any]] = None
    event_value: Optional[float] = None


class ABTestEventCreate(ABTestEventBase):
    test_id: int
    variant_id: int
    participant_id: int


class ABTestEventResponse(ABTestEventBase):
    id: int
    test_id: int
    variant_id: int
    participant_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Statistics schemas
class ABTestStatisticsResponse(BaseModel):
    id: int
    test_id: int
    analysis_date: datetime
    sample_size: int
    power: Optional[float] = None
    effect_size: Optional[float] = None
    bayesian_probability: Optional[float] = None
    credible_interval_lower: Optional[float] = None
    credible_interval_upper: Optional[float] = None
    p_value: Optional[float] = None
    t_statistic: Optional[float] = None
    degrees_of_freedom: Optional[int] = None
    winner_variant_id: Optional[int] = None
    confidence_level: float
    is_significant: bool = False
    uplift_percentage: Optional[float] = None
    analysis_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Dashboard and summary schemas
class ABTestSummaryStats(BaseModel):
    total_tests: int = 0
    running_tests: int = 0
    completed_tests: int = 0
    successful_tests: int = 0
    total_participants: int = 0
    average_uplift: Optional[float] = None
    average_confidence: Optional[float] = None


class ABTestDashboardResponse(BaseModel):
    stats: ABTestSummaryStats
    recent_tests: List[ABTestResponse]
    top_performing_tests: List[ABTestResponse]


# Analysis request schemas
class ABTestAnalysisRequest(BaseModel):
    test_id: int
    force_analysis: bool = False
    include_bayesian: bool = True
    include_frequentist: bool = True


class ABTestAnalysisResponse(BaseModel):
    test_id: int
    analysis_completed: bool
    winner_variant_id: Optional[int] = None
    confidence_level: float
    statistical_significance: bool
    uplift_percentage: Optional[float] = None
    p_value: Optional[float] = None
    bayesian_probability: Optional[float] = None
    recommendations: List[str] = []
    analysis_details: Dict[str, Any]


# Bulk operations schemas
class ABTestBulkStatusUpdate(BaseModel):
    test_ids: List[int] = Field(..., min_items=1)
    status: ABTestStatus


class ABTestBulkDeleteRequest(BaseModel):
    test_ids: List[int] = Field(..., min_items=1)
    confirm: bool = Field(..., description="Must be True to confirm deletion")

    @validator('confirm')
    def confirm_must_be_true(cls, v):
        if not v:
            raise ValueError('Confirmation is required for bulk deletion')
        return v


# Export schemas
class ABTestExportRequest(BaseModel):
    test_ids: Optional[List[int]] = None
    status_filter: Optional[List[ABTestStatus]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_participants: bool = False
    include_events: bool = False
    format: str = Field("csv", pattern="^(csv|json|xlsx)$")


class ABTestExportResponse(BaseModel):
    export_id: str
    status: str
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: datetime