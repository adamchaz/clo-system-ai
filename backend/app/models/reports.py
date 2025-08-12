"""
CLO Reports Model - Database models for report management
Stores report metadata, generated reports, and report templates
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Enum as SQLEnum, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from ..core.database import Base


class ReportType(str, Enum):
    """Report type enumeration"""
    PORTFOLIO_SUMMARY = "portfolio_summary"
    WATERFALL_ANALYSIS = "waterfall_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_REPORT = "compliance_report"
    PERFORMANCE_REPORT = "performance_report"
    CONCENTRATION_REPORT = "concentration_report"
    CASH_FLOW_REPORT = "cash_flow_report"
    ASSET_LISTING = "asset_listing"
    LIABILITY_SCHEDULE = "liability_schedule"
    CUSTOM_REPORT = "custom_report"


class ReportStatus(str, Enum):
    """Report generation status"""
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    """Report output format"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportTemplate(Base):
    """
    Report template definition for reusable report configurations
    """
    __tablename__ = 'report_templates'
    
    template_id = Column(String(50), primary_key=True)
    template_name = Column(String(200), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    description = Column(Text)
    
    # Template configuration
    default_parameters = Column(JSON)  # Default parameter values
    required_parameters = Column(JSON)  # List of required parameters
    optional_parameters = Column(JSON)  # List of optional parameters
    output_format = Column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    
    # Template metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    
    # Template definition (could be Jinja2 template, config JSON, etc.)
    template_definition = Column(Text)
    
    # Relationships
    reports = relationship("Report", back_populates="template")
    
    def __repr__(self):
        return f"<ReportTemplate({self.template_id}: {self.template_name})>"


class Report(Base):
    """
    Generated report instance with metadata and content
    """
    __tablename__ = 'reports'
    
    report_id = Column(String(50), primary_key=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    template_id = Column(String(50), ForeignKey('report_templates.template_id'), nullable=True)
    
    # Report parameters
    parameters = Column(JSON)  # Parameters used to generate the report
    filters = Column(JSON)     # Filters applied during generation
    
    # Generation metadata
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.QUEUED)
    output_format = Column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    file_size = Column(Integer)  # File size in bytes
    page_count = Column(Integer)  # Number of pages (for PDF/HTML reports)
    
    # Timing information
    requested_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)  # When report should be cleaned up
    
    # User information
    requested_by = Column(String(100))
    organization = Column(String(100))
    
    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Report content
    file_path = Column(String(500))  # Path to generated file
    content_hash = Column(String(64))  # SHA-256 hash of content
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    template = relationship("ReportTemplate", back_populates="reports")
    
    def __repr__(self):
        return f"<Report({self.report_id}: {self.report_name} - {self.status.value})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if report generation is completed"""
        return self.status == ReportStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if report generation failed"""
        return self.status == ReportStatus.FAILED
    
    @property
    def is_processing(self) -> bool:
        """Check if report is currently being processed"""
        return self.status in [ReportStatus.QUEUED, ReportStatus.GENERATING]
    
    @property
    def generation_time_seconds(self) -> Optional[float]:
        """Calculate report generation time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ReportSchedule(Base):
    """
    Scheduled report generation configuration
    """
    __tablename__ = 'report_schedules'
    
    schedule_id = Column(String(50), primary_key=True)
    schedule_name = Column(String(200), nullable=False)
    template_id = Column(String(50), nullable=False)
    
    # Schedule configuration
    cron_expression = Column(String(100))  # Cron-style schedule
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    
    # Report parameters for scheduled generation
    parameters = Column(JSON)
    output_format = Column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    
    # Distribution
    email_recipients = Column(JSON)  # List of email addresses
    auto_cleanup_days = Column(Integer, default=30)  # Days before cleanup
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Execution tracking
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<ReportSchedule({self.schedule_id}: {self.schedule_name})>"