"""
Reports API Endpoints
Handles report generation, management, and retrieval for the CLO Management System
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from ....core.database_config import db_config
from ....services.reports_service import reports_service
from ....schemas.reports import (
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
    ReportTemplateDetail,
    PortfolioReportRequest,
    WaterfallReportRequest,
    RiskReportRequest,
    ReportAnalytics
)
from ....models.reports import ReportType, ReportStatus, ReportFormat
from ....core.exceptions import CLOBusinessError, CLOValidationError

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session


def get_current_user() -> Optional[str]:
    """Get current user (placeholder for authentication)"""
    # This would typically extract user from JWT token
    return "demo_user"


def get_user_organization() -> Optional[str]:
    """Get user organization (placeholder for authentication)"""
    # This would typically extract organization from JWT token or user profile
    return "demo_org"


# Report Generation Endpoints
@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    Generate a new report
    
    - **report_name**: Name for the generated report
    - **report_type**: Type of report to generate
    - **template_id**: Optional template to use
    - **parameters**: Report parameters (varies by type)
    - **filters**: Optional filters to apply
    - **output_format**: Desired output format (PDF, Excel, etc.)
    - **expires_hours**: Hours until report expires (default 24)
    """
    try:
        return reports_service.generate_report(
            request=request,
            user_id=current_user,
            organization=organization
        )
    except CLOValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.post("/generate/portfolio", response_model=ReportResponse)
async def generate_portfolio_report(
    request: PortfolioReportRequest,
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    Generate a portfolio-specific report
    
    Specialized endpoint for portfolio reports with portfolio-specific parameters
    """
    try:
        return reports_service.generate_report(
            request=request,
            user_id=current_user,
            organization=organization
        )
    except CLOValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate portfolio report: {str(e)}")


@router.post("/generate/waterfall", response_model=ReportResponse)
async def generate_waterfall_report(
    request: WaterfallReportRequest,
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    Generate a waterfall analysis report
    
    Specialized endpoint for waterfall analysis with waterfall-specific parameters
    """
    try:
        return reports_service.generate_report(
            request=request,
            user_id=current_user,
            organization=organization
        )
    except CLOValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate waterfall report: {str(e)}")


@router.post("/generate/risk", response_model=ReportResponse)
async def generate_risk_report(
    request: RiskReportRequest,
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    Generate a risk assessment report
    
    Specialized endpoint for risk analysis with risk-specific parameters
    """
    try:
        return reports_service.generate_report(
            request=request,
            user_id=current_user,
            organization=organization
        )
    except CLOValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate risk report: {str(e)}")


# Report Retrieval Endpoints
@router.get("/", response_model=ReportListResponse)
async def list_reports(
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    status: Optional[ReportStatus] = Query(None, description="Filter by report status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    List reports with filtering and pagination
    
    - **report_type**: Filter by specific report type
    - **status**: Filter by report status (queued, generating, completed, failed)
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    """
    try:
        return reports_service.list_reports(
            user_id=current_user,
            organization=organization,
            report_type=report_type,
            status=status,
            page=page,
            page_size=page_size
        )
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reports: {str(e)}")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str = Path(..., description="Report ID"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific report by ID
    
    Returns report metadata and status information
    """
    try:
        report = reports_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # TODO: Add permission check to ensure user can access this report
        
        return report
    except HTTPException:
        raise
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.get("/{report_id}/download")
async def download_report(
    report_id: str = Path(..., description="Report ID"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a completed report
    
    Returns the report file content with appropriate headers for download
    """
    try:
        result = reports_service.get_report_content(report_id)
        if not result:
            raise HTTPException(status_code=404, detail="Report not found or not ready")
        
        content, filename, content_type = result
        
        # Create streaming response
        def generate():
            yield content
        
        response = StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content))
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


@router.delete("/{report_id}")
async def delete_report(
    report_id: str = Path(..., description="Report ID"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a report and its associated files
    
    Permanently removes the report from the system
    """
    try:
        success = reports_service.delete_report(report_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        
        return {"message": "Report deleted successfully"}
    except HTTPException:
        raise
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


# Report Template Endpoints
@router.get("/templates/", response_model=List[ReportTemplateResponse])
async def list_templates(
    active_only: bool = Query(True, description="Include only active templates"),
    db: Session = Depends(get_db)
):
    """
    List all available report templates
    
    - **active_only**: Include only active templates
    """
    try:
        return reports_service.get_templates(active_only=active_only)
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")


@router.post("/templates/", response_model=ReportTemplateResponse)
async def create_template(
    template: ReportTemplateCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new report template
    
    Templates define reusable report configurations with parameters
    """
    try:
        return reports_service.create_template(template)
    except CLOValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


# Report Analytics Endpoints
@router.get("/analytics/summary", response_model=ReportAnalytics)
async def get_report_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: str = Depends(get_current_user),
    organization: str = Depends(get_user_organization),
    db: Session = Depends(get_db)
):
    """
    Get report generation analytics
    
    Provides insights into report usage patterns and performance
    """
    try:
        # This would typically query the database for analytics
        # For demo purposes, return sample data
        return ReportAnalytics(
            total_reports=156,
            reports_by_type={
                "portfolio_summary": 45,
                "waterfall_analysis": 32,
                "risk_assessment": 28,
                "compliance_report": 21,
                "performance_report": 18,
                "other": 12
            },
            reports_by_status={
                "completed": 142,
                "failed": 8,
                "generating": 4,
                "queued": 2
            },
            reports_by_format={
                "pdf": 98,
                "excel": 35,
                "csv": 15,
                "html": 8
            },
            avg_generation_time_seconds=12.5,
            total_file_size_bytes=1024*1024*450,  # 450 MB
            most_requested_templates=[
                {"template_id": "portfolio_summary_basic", "count": 45},
                {"template_id": "waterfall_analysis_standard", "count": 32},
                {"template_id": "risk_assessment_basic", "count": 28}
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


# Utility Endpoints
@router.get("/types/", response_model=List[str])
async def list_report_types():
    """
    List all available report types
    
    Returns the supported report types for the system
    """
    return [report_type.value for report_type in ReportType]


@router.get("/formats/", response_model=List[str])
async def list_report_formats():
    """
    List all supported output formats
    
    Returns the supported output formats for reports
    """
    return [format.value for format in ReportFormat]


@router.get("/status/{report_id}", response_model=ReportResponse)
async def check_report_status(
    report_id: str = Path(..., description="Report ID"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check the status of a report generation
    
    Useful for polling report generation progress
    """
    try:
        report = reports_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check report status: {str(e)}")