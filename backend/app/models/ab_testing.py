from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base


class ABTestStatus(PyEnum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTestType(PyEnum):
    PAGE = "page"
    FEATURE = "feature"
    ELEMENT = "element"
    FLOW = "flow"


class PrimaryMetric(PyEnum):
    CONVERSION_RATE = "conversion_rate"
    CLICK_THROUGH_RATE = "click_through_rate"
    BOUNCE_RATE = "bounce_rate"
    SESSION_DURATION = "session_duration"
    REVENUE_PER_USER = "revenue_per_user"
    RETENTION_RATE = "retention_rate"


class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    hypothesis = Column(Text)
    
    # Test configuration
    type = Column(Enum(ABTestType), nullable=False, default=ABTestType.PAGE)
    status = Column(Enum(ABTestStatus), nullable=False, default=ABTestStatus.DRAFT)
    
    # Traffic and duration settings
    traffic_allocation = Column(Float, nullable=False, default=100.0)  # Percentage of users to include
    duration = Column(Integer, nullable=False, default=14)  # Duration in days
    sample_size = Column(Integer, nullable=False, default=1000)  # Target sample size
    confidence_level = Column(Float, nullable=False, default=95.0)  # Statistical confidence level
    
    # Metrics configuration
    primary_metric = Column(Enum(PrimaryMetric), nullable=False, default=PrimaryMetric.CONVERSION_RATE)
    secondary_metrics = Column(JSON)  # List of secondary metrics to track
    
    # Test results
    results = Column(JSON)  # Statistical results and analysis
    winner_variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Creator
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    variants = relationship("ABTestVariant", back_populates="test", cascade="all, delete-orphan", foreign_keys="ABTestVariant.test_id")
    participants = relationship("ABTestParticipant", back_populates="test", cascade="all, delete-orphan")
    events = relationship("ABTestEvent", back_populates="test", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    winner_variant = relationship("ABTestVariant", foreign_keys=[winner_variant_id])

    def __repr__(self):
        return f"<ABTest(id={self.id}, name='{self.name}', status='{self.status}')>"


class ABTestVariant(Base):
    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Variant configuration
    is_control = Column(Boolean, nullable=False, default=False)
    traffic_percentage = Column(Float, nullable=False)  # Percentage of test traffic
    configuration = Column(JSON)  # Variant-specific configuration
    
    # Performance metrics
    participants_count = Column(Integer, nullable=False, default=0)
    conversions_count = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Float, nullable=False, default=0.0)
    
    # Statistical metrics
    conversion_rate = Column(Float, nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    statistical_significance = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    test = relationship("ABTest", back_populates="variants", foreign_keys=[test_id])
    participants = relationship("ABTestParticipant", back_populates="variant")
    events = relationship("ABTestEvent", back_populates="variant")

    def __repr__(self):
        return f"<ABTestVariant(id={self.id}, name='{self.name}', test_id={self.test_id})>"


class ABTestParticipant(Base):
    __tablename__ = "ab_test_participants"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous users
    
    # Participant identification
    session_id = Column(String(255), nullable=True)  # For anonymous users
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Participation tracking
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    first_interaction_at = Column(DateTime(timezone=True), nullable=True)
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    
    # Conversion tracking
    converted = Column(Boolean, nullable=False, default=False)
    conversion_value = Column(Float, nullable=True)
    conversion_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metrics
    session_duration = Column(Integer, nullable=True)  # Duration in seconds
    page_views = Column(Integer, nullable=False, default=0)
    bounce = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    test = relationship("ABTest", back_populates="participants")
    variant = relationship("ABTestVariant", back_populates="participants")
    user = relationship("User", foreign_keys=[user_id])
    events = relationship("ABTestEvent", back_populates="participant")

    def __repr__(self):
        return f"<ABTestParticipant(id={self.id}, test_id={self.test_id}, variant_id={self.variant_id})>"


class ABTestEventType(PyEnum):
    VIEW = "view"
    CLICK = "click"
    CONVERSION = "conversion"
    CUSTOM = "custom"


class ABTestEvent(Base):
    __tablename__ = "ab_test_events"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("ab_test_participants.id"), nullable=False)
    
    # Event details
    event_type = Column(Enum(ABTestEventType), nullable=False)
    event_name = Column(String(255), nullable=False)
    event_data = Column(JSON)  # Additional event data
    
    # Event value (for revenue tracking)
    event_value = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    test = relationship("ABTest", back_populates="events")
    variant = relationship("ABTestVariant", back_populates="events")
    participant = relationship("ABTestParticipant", back_populates="events")

    def __repr__(self):
        return f"<ABTestEvent(id={self.id}, type='{self.event_type}', name='{self.event_name}')>"


class ABTestStatistics(Base):
    __tablename__ = "ab_test_statistics"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    
    # Statistical analysis results
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    sample_size = Column(Integer, nullable=False)
    power = Column(Float, nullable=True)  # Statistical power
    effect_size = Column(Float, nullable=True)  # Cohen's d or similar
    
    # Bayesian analysis (optional)
    bayesian_probability = Column(Float, nullable=True)  # Probability that variant is better
    credible_interval_lower = Column(Float, nullable=True)
    credible_interval_upper = Column(Float, nullable=True)
    
    # Frequentist analysis
    p_value = Column(Float, nullable=True)
    t_statistic = Column(Float, nullable=True)
    degrees_of_freedom = Column(Integer, nullable=True)
    
    # Results summary
    winner_variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=True)
    confidence_level = Column(Float, nullable=False)
    is_significant = Column(Boolean, nullable=False, default=False)
    uplift_percentage = Column(Float, nullable=True)
    
    # Additional analysis data
    analysis_data = Column(JSON)  # Detailed statistical analysis results
    
    # Relationships
    test = relationship("ABTest", foreign_keys=[test_id])
    winner_variant = relationship("ABTestVariant", foreign_keys=[winner_variant_id])

    def __repr__(self):
        return f"<ABTestStatistics(id={self.id}, test_id={self.test_id}, significant={self.is_significant})>"