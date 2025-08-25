"""
Concentration Test Threshold Database Models
SQLAlchemy ORM models for database-driven concentration test thresholds
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Boolean, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import date, datetime

from ..asset import Base


class ConcentrationTestDefinition(Base):
    """Master definition of concentration tests (91 total tests)"""
    
    __tablename__ = "concentration_test_definitions"

    test_id = Column(Integer, primary_key=True, autoincrement=True)
    test_number = Column(Integer, unique=True, nullable=False, comment="VBA TestNum enum value")
    test_name = Column(String(200), nullable=False)
    test_description = Column(Text)
    test_category = Column(String(50), nullable=False, comment="obligor, industry, rating, geographic, asset_type, portfolio")
    result_type = Column(String(20), nullable=False, comment="percentage, absolute, rating_factor, years")
    default_threshold = Column(Numeric(18, 6), comment="Default threshold value")
    calculation_method = Column(Text, comment="Description of calculation methodology")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    deal_thresholds = relationship("DealConcentrationThreshold", back_populates="test_definition", cascade="all, delete-orphan")
    executions = relationship("ConcentrationTestExecution", back_populates="test_definition", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(test_category.in_(['obligor', 'industry', 'rating', 'geographic', 'asset_type', 'portfolio', 'facility', 'covenant']), 
                       name='valid_test_category'),
        CheckConstraint(result_type.in_(['percentage', 'absolute', 'rating_factor', 'years']), 
                       name='valid_result_type'),
    )

    def __repr__(self):
        return f"<ConcentrationTestDefinition(test_number={self.test_number}, name='{self.test_name}')>"

    def to_dict(self):
        return {
            'test_id': self.test_id,
            'test_number': self.test_number,
            'test_name': self.test_name,
            'test_description': self.test_description,
            'test_category': self.test_category,
            'result_type': self.result_type,
            'default_threshold': float(self.default_threshold) if self.default_threshold else None,
            'calculation_method': self.calculation_method,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DealConcentrationThreshold(Base):
    """Deal-specific threshold overrides"""
    
    __tablename__ = "deal_concentration_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey("clo_deals.deal_id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("concentration_test_definitions.test_id", ondelete="CASCADE"), nullable=False)
    threshold_value = Column(Numeric(18, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    mag_version = Column(String(10), comment="MAG6, MAG14, MAG17")
    rating_agency = Column(String(20), comment="Moodys, SP, Fitch")
    notes = Column(Text)
    created_by = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    deal = relationship("CLODeal", back_populates="concentration_thresholds")
    test_definition = relationship("ConcentrationTestDefinition", back_populates="deal_thresholds")
    created_by_user = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(threshold_value > 0, name='positive_threshold_value'),
        CheckConstraint(mag_version.in_(['MAG6', 'MAG14', 'MAG17']) | mag_version.is_(None), 
                       name='valid_mag_version'),
        CheckConstraint(rating_agency.in_(['Moodys', 'SP', 'Fitch']) | rating_agency.is_(None), 
                       name='valid_rating_agency'),
    )

    def __repr__(self):
        return f"<DealConcentrationThreshold(deal_id={self.deal_id}, test_id={self.test_id}, threshold={self.threshold_value})>"

    def is_effective(self, analysis_date: date) -> bool:
        """Check if threshold is effective on the given analysis date"""
        return (
            self.effective_date <= analysis_date and 
            (self.expiry_date is None or self.expiry_date > analysis_date)
        )

    def to_dict(self):
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'test_id': self.test_id,
            'threshold_value': float(self.threshold_value),
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'mag_version': self.mag_version,
            'rating_agency': self.rating_agency,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ConcentrationTestExecution(Base):
    """Results of concentration test execution with threshold details"""
    
    __tablename__ = "concentration_test_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey("clo_deals.deal_id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("concentration_test_definitions.test_id", ondelete="CASCADE"), nullable=False)
    analysis_date = Column(Date, nullable=False)
    threshold_used = Column(Numeric(18, 6), nullable=False)
    calculated_value = Column(Numeric(18, 6), nullable=False)
    numerator = Column(Numeric(18, 6))
    denominator = Column(Numeric(18, 6))
    pass_fail_status = Column(String(10), nullable=False)
    excess_amount = Column(Numeric(18, 6), comment="Amount over threshold for failed tests")
    threshold_source = Column(String(20), nullable=False, comment="deal, default, template")
    comments = Column(Text)
    execution_timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    deal = relationship("CLODeal")
    test_definition = relationship("ConcentrationTestDefinition", back_populates="executions")

    # Constraints
    __table_args__ = (
        CheckConstraint(pass_fail_status.in_(['PASS', 'FAIL', 'N/A']), name='valid_pass_fail_status'),
        CheckConstraint(threshold_source.in_(['deal', 'default', 'template']), name='valid_threshold_source'),
        CheckConstraint(denominator.is_(None) | (denominator != 0), name='non_zero_denominator'),
    )

    def __repr__(self):
        return f"<ConcentrationTestExecution(deal_id={self.deal_id}, test_id={self.test_id}, date={self.analysis_date}, status={self.pass_fail_status})>"

    @property
    def is_passing(self) -> bool:
        """Check if test is passing"""
        return self.pass_fail_status == 'PASS'

    @property  
    def is_failing(self) -> bool:
        """Check if test is failing"""
        return self.pass_fail_status == 'FAIL'

    @property
    def concentration_percentage(self) -> Optional[float]:
        """Calculate concentration as percentage if applicable"""
        if self.denominator and self.denominator != 0:
            return float((self.numerator / self.denominator) * 100)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'test_id': self.test_id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'threshold_used': float(self.threshold_used),
            'calculated_value': float(self.calculated_value),
            'numerator': float(self.numerator) if self.numerator else None,
            'denominator': float(self.denominator) if self.denominator else None,
            'pass_fail_status': self.pass_fail_status,
            'excess_amount': float(self.excess_amount) if self.excess_amount else None,
            'threshold_source': self.threshold_source,
            'comments': self.comments,
            'execution_timestamp': self.execution_timestamp.isoformat() if self.execution_timestamp else None,
            'is_passing': self.is_passing,
            'is_failing': self.is_failing,
            'concentration_percentage': self.concentration_percentage
        }


# Additional helper models for query optimization
class ConcentrationTestSummary(Base):
    """Summary view for concentration test results (could be materialized view)"""
    
    __tablename__ = "concentration_test_summary"

    id = Column(Integer, primary_key=True, autoincrement=True) 
    deal_id = Column(String(50), ForeignKey("clo_deals.deal_id"), nullable=False)
    analysis_date = Column(Date, nullable=False)
    total_tests = Column(Integer, nullable=False)
    passed_tests = Column(Integer, nullable=False)
    failed_tests = Column(Integer, nullable=False)
    na_tests = Column(Integer, nullable=False)
    total_violations = Column(Numeric(18, 6), default=0)
    worst_violation_test_id = Column(Integer, ForeignKey("concentration_test_definitions.test_id"))
    worst_violation_amount = Column(Numeric(18, 6))
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    deal = relationship("CLODeal")
    worst_violation_test = relationship("ConcentrationTestDefinition")

    def __repr__(self):
        return f"<ConcentrationTestSummary(deal_id={self.deal_id}, date={self.analysis_date}, passed={self.passed_tests}/{self.total_tests})>"

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def to_dict(self):
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'na_tests': self.na_tests,
            'total_violations': float(self.total_violations) if self.total_violations else 0.0,
            'worst_violation_test_id': self.worst_violation_test_id,
            'worst_violation_amount': float(self.worst_violation_amount) if self.worst_violation_amount else None,
            'pass_rate': self.pass_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }