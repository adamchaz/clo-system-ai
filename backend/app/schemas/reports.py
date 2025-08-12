"""
Report Schemas
Pydantic models for report-related API requests and responses
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models.reports import ReportType, ReportStatus, ReportFormat


class ReportParameterType(str, Enum):
    """Parameter type for report templates"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi_select"


class ParameterDefinition(BaseModel):
    """Definition of a report parameter"""
    name: str = Field(..., description="Parameter name")
    type: ReportParameterType = Field(..., description="Parameter data type")
    label: str = Field(..., description="Display label for the parameter")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether parameter is required")
    default_value: Optional[Any] = Field(None, description="Default parameter value")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    options: Optional[List[Dict[str, str]]] = Field(None, description="Options for select parameters")


# Report Template Schemas
class ReportTemplateBase(BaseModel):
    """Base report template model"""
    template_name: str = Field(..., min_length=1, max_length=200)
    report_type: ReportType
    description: Optional[str] = None
    output_format: ReportFormat = ReportFormat.PDF
    is_active: bool = True


class ReportTemplateCreate(ReportTemplateBase):
    """Schema for creating a new report template"""
    template_id: str = Field(..., min_length=1, max_length=50)
    default_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    required_parameters: Optional[List[str]] = Field(default_factory=list)
    optional_parameters: Optional[List[str]] = Field(default_factory=list)
    template_definition: Optional[str] = None


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    required_parameters: Optional[List[str]] = None
    optional_parameters: Optional[List[str]] = None
    output_format: Optional[ReportFormat] = None
    is_active: Optional[bool] = None
    template_definition: Optional[str] = None


class ReportTemplateResponse(ReportTemplateBase):
    """Schema for report template responses"""
    template_id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_system_template: bool
    default_parameters: Dict[str, Any]
    required_parameters: List[str]
    optional_parameters: List[str]
    
    class Config:
        from_attributes = True


class ReportTemplateDetail(ReportTemplateResponse):
    """Detailed report template response including definition"""
    template_definition: Optional[str]
    parameter_definitions: Optional[List[ParameterDefinition]] = None


# Report Generation Schemas
class ReportGenerateRequest(BaseModel):
    """Schema for report generation requests"""
    report_name: str = Field(..., min_length=1, max_length=200)
    report_type: ReportType
    template_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    output_format: ReportFormat = ReportFormat.PDF
    expires_hours: Optional[int] = Field(24, ge=1, le=168)  # 1 hour to 1 week
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Ensure parameters is a dictionary"""
        if not isinstance(v, dict):
            raise ValueError('Parameters must be a dictionary')
        return v


class ReportResponse(BaseModel):
    """Schema for report responses"""
    report_id: str
    report_name: str
    report_type: ReportType
    template_id: Optional[str]
    status: ReportStatus
    output_format: ReportFormat
    file_size: Optional[int]
    page_count: Optional[int]
    requested_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    requested_by: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
    
    @property
    def is_ready(self) -> bool:
        """Check if report is ready for download"""
        return self.status == ReportStatus.COMPLETED
    
    @property
    def generation_time_seconds(self) -> Optional[float]:
        """Calculate generation time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ReportListResponse(BaseModel):
    """Schema for paginated report list responses"""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportStatusUpdate(BaseModel):
    """Schema for updating report status"""
    status: ReportStatus
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None


# Report Content Schemas
class ReportDownloadResponse(BaseModel):
    """Schema for report download information"""
    report_id: str
    report_name: str
    output_format: ReportFormat
    file_size: int
    content_hash: str
    download_url: str
    expires_at: Optional[datetime]


# Portfolio-specific report schemas
class PortfolioReportRequest(ReportGenerateRequest):
    """Portfolio-specific report generation request"""
    portfolio_id: str = Field(..., description="Portfolio/deal ID")
    as_of_date: Optional[str] = Field(None, description="Report as-of date (YYYY-MM-DD)")
    include_assets: bool = Field(True, description="Include asset details")
    include_liabilities: bool = Field(True, description="Include liability details")
    include_waterfall: bool = Field(False, description="Include waterfall calculations")


class WaterfallReportRequest(ReportGenerateRequest):
    """Waterfall analysis report request"""
    portfolio_id: str = Field(..., description="Portfolio/deal ID")
    waterfall_type: str = Field("current", description="Waterfall type to analyze")
    periods: Optional[List[int]] = Field(None, description="Specific periods to include")
    scenario_id: Optional[str] = Field(None, description="Scenario ID for analysis")


class RiskReportRequest(ReportGenerateRequest):
    """Risk assessment report request"""
    portfolio_id: str = Field(..., description="Portfolio/deal ID")
    risk_metrics: List[str] = Field(default_factory=lambda: ["var", "concentration", "rating_distribution"])
    confidence_level: float = Field(0.95, ge=0.01, le=0.99)
    time_horizon_days: int = Field(30, ge=1, le=365)


# Report Analytics Schemas
class ReportAnalytics(BaseModel):
    """Report generation analytics"""
    total_reports: int
    reports_by_type: Dict[str, int]
    reports_by_status: Dict[str, int]
    reports_by_format: Dict[str, int]
    avg_generation_time_seconds: Optional[float]
    total_file_size_bytes: int
    most_requested_templates: List[Dict[str, Any]]


class ReportError(BaseModel):
    """Report error details"""
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    report_id: Optional[str] = None