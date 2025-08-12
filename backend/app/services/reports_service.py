"""
Reports Service
Handles report generation, management, storage, and retrieval
"""

import os
import json
import uuid
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.reports import (
    Report, ReportTemplate, ReportSchedule,
    ReportType, ReportStatus, ReportFormat
)
from ..schemas.reports import (
    ReportGenerateRequest, ReportResponse, ReportTemplateCreate,
    ReportTemplateResponse, ReportStatusUpdate, ReportListResponse
)
from ..core.database_config import get_db_session
from ..core.exceptions import CLOBusinessError, CLOValidationError

logger = logging.getLogger(__name__)


class ReportsService:
    """Service for managing CLO reports"""
    
    def __init__(self, reports_directory: str = "reports"):
        self.reports_directory = Path(reports_directory)
        self.reports_directory.mkdir(exist_ok=True)
        
        # Initialize system templates on startup
        self._initialize_system_templates()
    
    def generate_report(
        self,
        request: ReportGenerateRequest,
        user_id: Optional[str] = None,
        organization: Optional[str] = None
    ) -> ReportResponse:
        """
        Generate a new report based on request parameters
        """
        try:
            with get_db_session() as db:
                # Generate unique report ID
                report_id = self._generate_report_id()
                
                # Validate template if provided
                template = None
                if request.template_id:
                    template = db.query(ReportTemplate).filter(
                        ReportTemplate.template_id == request.template_id,
                        ReportTemplate.is_active == True
                    ).first()
                    
                    if not template:
                        raise CLOValidationError(f"Template not found: {request.template_id}")
                    
                    # Validate required parameters
                    self._validate_template_parameters(template, request.parameters)
                
                # Calculate expiration date
                expires_at = None
                if request.expires_hours:
                    expires_at = datetime.utcnow() + timedelta(hours=request.expires_hours)
                
                # Create report record
                report = Report(
                    report_id=report_id,
                    report_name=request.report_name,
                    report_type=request.report_type,
                    template_id=request.template_id,
                    parameters=request.parameters,
                    filters=request.filters,
                    status=ReportStatus.QUEUED,
                    output_format=request.output_format,
                    requested_at=datetime.utcnow(),
                    expires_at=expires_at,
                    requested_by=user_id,
                    organization=organization
                )
                
                db.add(report)
                db.commit()
                db.refresh(report)
                
                # Queue report generation (async process)
                self._queue_report_generation(report)
                
                logger.info(f"Report queued for generation: {report_id}")
                return ReportResponse.from_orm(report)
                
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            if isinstance(e, (CLOBusinessError, CLOValidationError)):
                raise
            raise CLOBusinessError(f"Report generation failed: {str(e)}")
    
    def get_report(self, report_id: str) -> Optional[ReportResponse]:
        """Get report by ID"""
        try:
            with get_db_session() as db:
                report = db.query(Report).filter(
                    Report.report_id == report_id
                ).first()
                
                if not report:
                    return None
                
                return ReportResponse.from_orm(report)
                
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to retrieve report: {str(e)}")
    
    def list_reports(
        self,
        user_id: Optional[str] = None,
        organization: Optional[str] = None,
        report_type: Optional[ReportType] = None,
        status: Optional[ReportStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> ReportListResponse:
        """List reports with filtering and pagination"""
        try:
            with get_db_session() as db:
                query = db.query(Report)
                
                # Apply filters
                if user_id:
                    query = query.filter(Report.requested_by == user_id)
                if organization:
                    query = query.filter(Report.organization == organization)
                if report_type:
                    query = query.filter(Report.report_type == report_type)
                if status:
                    query = query.filter(Report.status == status)
                
                # Get total count
                total = query.count()
                
                # Apply pagination
                offset = (page - 1) * page_size
                reports = query.order_by(desc(Report.requested_at))\
                              .offset(offset)\
                              .limit(page_size)\
                              .all()
                
                # Calculate pagination info
                total_pages = (total + page_size - 1) // page_size
                
                return ReportListResponse(
                    reports=[ReportResponse.from_orm(report) for report in reports],
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
                
        except Exception as e:
            logger.error(f"Failed to list reports: {str(e)}")
            raise CLOBusinessError(f"Failed to retrieve reports: {str(e)}")
    
    def delete_report(self, report_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a report and its associated files"""
        try:
            with get_db_session() as db:
                query = db.query(Report).filter(Report.report_id == report_id)
                
                # Add user filter if provided (for security)
                if user_id:
                    query = query.filter(Report.requested_by == user_id)
                
                report = query.first()
                if not report:
                    return False
                
                # Delete physical file if exists
                if report.file_path and os.path.exists(report.file_path):
                    try:
                        os.remove(report.file_path)
                    except OSError as e:
                        logger.warning(f"Failed to delete report file {report.file_path}: {e}")
                
                # Delete database record
                db.delete(report)
                db.commit()
                
                logger.info(f"Report deleted: {report_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to delete report: {str(e)}")
    
    def get_report_content(self, report_id: str) -> Optional[Tuple[bytes, str, str]]:
        """
        Get report content for download
        Returns (content, filename, content_type) or None if not found
        """
        try:
            with get_db_session() as db:
                report = db.query(Report).filter(
                    Report.report_id == report_id,
                    Report.status == ReportStatus.COMPLETED
                ).first()
                
                if not report or not report.file_path:
                    return None
                
                if not os.path.exists(report.file_path):
                    logger.error(f"Report file not found: {report.file_path}")
                    return None
                
                # Read file content
                with open(report.file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                content_type = self._get_content_type(report.output_format)
                
                # Generate filename
                filename = f"{report.report_name}.{report.output_format.value}"
                
                return content, filename, content_type
                
        except Exception as e:
            logger.error(f"Failed to get report content {report_id}: {str(e)}")
            return None
    
    def update_report_status(
        self,
        report_id: str,
        status_update: ReportStatusUpdate
    ) -> bool:
        """Update report status (used by report generators)"""
        try:
            with get_db_session() as db:
                report = db.query(Report).filter(
                    Report.report_id == report_id
                ).first()
                
                if not report:
                    return False
                
                # Update status
                old_status = report.status
                report.status = status_update.status
                
                # Update timing based on status
                now = datetime.utcnow()
                if status_update.status == ReportStatus.GENERATING and old_status == ReportStatus.QUEUED:
                    report.started_at = now
                elif status_update.status in [ReportStatus.COMPLETED, ReportStatus.FAILED]:
                    if not report.completed_at:
                        report.completed_at = now
                
                # Update other fields
                if status_update.error_message:
                    report.error_message = status_update.error_message
                if status_update.error_details:
                    report.error_details = status_update.error_details
                if status_update.file_size:
                    report.file_size = status_update.file_size
                if status_update.page_count:
                    report.page_count = status_update.page_count
                
                report.updated_at = now
                db.commit()
                
                logger.info(f"Report status updated: {report_id} -> {status_update.status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update report status {report_id}: {str(e)}")
            return False
    
    # Template Management
    def create_template(self, template: ReportTemplateCreate) -> ReportTemplateResponse:
        """Create a new report template"""
        try:
            with get_db_session() as db:
                # Check if template ID already exists
                existing = db.query(ReportTemplate).filter(
                    ReportTemplate.template_id == template.template_id
                ).first()
                
                if existing:
                    raise CLOValidationError(f"Template ID already exists: {template.template_id}")
                
                # Create template
                db_template = ReportTemplate(
                    template_id=template.template_id,
                    template_name=template.template_name,
                    report_type=template.report_type,
                    description=template.description,
                    default_parameters=template.default_parameters or {},
                    required_parameters=template.required_parameters or [],
                    optional_parameters=template.optional_parameters or [],
                    output_format=template.output_format,
                    template_definition=template.template_definition,
                    is_system_template=False,
                    created_at=datetime.utcnow()
                )
                
                db.add(db_template)
                db.commit()
                db.refresh(db_template)
                
                logger.info(f"Report template created: {template.template_id}")
                return ReportTemplateResponse.from_orm(db_template)
                
        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            if isinstance(e, CLOValidationError):
                raise
            raise CLOBusinessError(f"Template creation failed: {str(e)}")
    
    def get_templates(self, active_only: bool = True) -> List[ReportTemplateResponse]:
        """Get all available report templates"""
        try:
            with get_db_session() as db:
                query = db.query(ReportTemplate)
                
                if active_only:
                    query = query.filter(ReportTemplate.is_active == True)
                
                templates = query.order_by(ReportTemplate.template_name).all()
                
                return [ReportTemplateResponse.from_orm(template) for template in templates]
                
        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            raise CLOBusinessError(f"Failed to retrieve templates: {str(e)}")
    
    # Private methods
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        return f"RPT_{uuid.uuid4().hex[:12].upper()}"
    
    def _validate_template_parameters(self, template: ReportTemplate, parameters: Dict[str, Any]):
        """Validate parameters against template requirements"""
        required_params = template.required_parameters or []
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise CLOValidationError(f"Required parameter missing: {param}")
        
        # Additional validation logic can be added here
    
    def _queue_report_generation(self, report: Report):
        """Queue report for background generation"""
        # This would typically integrate with Celery or similar task queue
        # For now, we'll simulate the process
        logger.info(f"Report queued for generation: {report.report_id}")
        
        # In a real implementation, this would:
        # 1. Send task to Celery queue
        # 2. Background worker would pick up the task
        # 3. Generate the report based on type and parameters
        # 4. Update status via update_report_status()
        # 5. Store the generated file
        
        # For demo purposes, let's simulate immediate processing
        self._simulate_report_generation(report)
    
    def _simulate_report_generation(self, report: Report):
        """Simulate report generation (for demo purposes)"""
        try:
            # Update status to generating
            self.update_report_status(
                report.report_id,
                ReportStatusUpdate(status=ReportStatus.GENERATING)
            )
            
            # Simulate report generation based on type
            content = self._generate_report_content(report)
            
            # Save to file
            file_path = self._save_report_content(report, content)
            
            # Update status to completed
            with get_db_session() as db:
                db_report = db.query(Report).filter(
                    Report.report_id == report.report_id
                ).first()
                if db_report:
                    db_report.file_path = str(file_path)
                    db_report.content_hash = hashlib.sha256(content).hexdigest()
                    db.commit()
            
            self.update_report_status(
                report.report_id,
                ReportStatusUpdate(
                    status=ReportStatus.COMPLETED,
                    file_size=len(content),
                    page_count=1
                )
            )
            
        except Exception as e:
            logger.error(f"Report generation failed for {report.report_id}: {str(e)}")
            self.update_report_status(
                report.report_id,
                ReportStatusUpdate(
                    status=ReportStatus.FAILED,
                    error_message=str(e)
                )
            )
    
    def _generate_report_content(self, report: Report) -> bytes:
        """Generate actual report content based on type and parameters"""
        # This is where the real report generation logic would go
        # For demo purposes, generate simple content
        
        content_map = {
            ReportType.PORTFOLIO_SUMMARY: self._generate_portfolio_summary,
            ReportType.WATERFALL_ANALYSIS: self._generate_waterfall_analysis,
            ReportType.RISK_ASSESSMENT: self._generate_risk_assessment,
            ReportType.COMPLIANCE_REPORT: self._generate_compliance_report,
            ReportType.PERFORMANCE_REPORT: self._generate_performance_report,
        }
        
        generator = content_map.get(report.report_type, self._generate_default_report)
        return generator(report)
    
    def _generate_portfolio_summary(self, report: Report) -> bytes:
        """Generate portfolio summary report"""
        content = f"""Portfolio Summary Report
        
Report Name: {report.report_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample portfolio summary report.
In a real implementation, this would contain:
- Portfolio composition
- Asset allocation
- Performance metrics
- Risk indicators
"""
        return content.encode('utf-8')
    
    def _generate_waterfall_analysis(self, report: Report) -> bytes:
        """Generate waterfall analysis report"""
        content = f"""Waterfall Analysis Report
        
Report Name: {report.report_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample waterfall analysis report.
In a real implementation, this would contain:
- Payment waterfall calculations
- Cash flow distributions
- Tranche-by-tranche analysis
- Stress testing results
"""
        return content.encode('utf-8')
    
    def _generate_risk_assessment(self, report: Report) -> bytes:
        """Generate risk assessment report"""
        content = f"""Risk Assessment Report
        
Report Name: {report.report_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample risk assessment report.
In a real implementation, this would contain:
- VaR calculations
- Concentration analysis
- Credit risk metrics
- Scenario analysis
"""
        return content.encode('utf-8')
    
    def _generate_compliance_report(self, report: Report) -> bytes:
        """Generate compliance report"""
        content = f"""Compliance Report
        
Report Name: {report.report_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample compliance report.
In a real implementation, this would contain:
- OC/IC trigger tests
- Concentration limit compliance
- Rating requirements
- Covenant testing
"""
        return content.encode('utf-8')
    
    def _generate_performance_report(self, report: Report) -> bytes:
        """Generate performance report"""
        content = f"""Performance Report
        
Report Name: {report.report_name}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample performance report.
In a real implementation, this would contain:
- Return metrics
- Benchmark comparisons
- Attribution analysis
- Historical performance
"""
        return content.encode('utf-8')
    
    def _generate_default_report(self, report: Report) -> bytes:
        """Generate default report content"""
        content = f"""CLO Report
        
Report Name: {report.report_name}
Report Type: {report.report_type.value}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Parameters: {json.dumps(report.parameters, indent=2)}

This is a sample report generated by the CLO Management System.
"""
        return content.encode('utf-8')
    
    def _save_report_content(self, report: Report, content: bytes) -> Path:
        """Save report content to file"""
        # Create report directory if it doesn't exist
        report_dir = self.reports_directory / report.report_id
        report_dir.mkdir(exist_ok=True)
        
        # Generate filename
        extension = report.output_format.value
        filename = f"{report.report_name.replace(' ', '_')}_{report.report_id}.{extension}"
        file_path = report_dir / filename
        
        # Write content to file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def _get_content_type(self, format: ReportFormat) -> str:
        """Get HTTP content type for report format"""
        content_types = {
            ReportFormat.PDF: "application/pdf",
            ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ReportFormat.CSV: "text/csv",
            ReportFormat.JSON: "application/json",
            ReportFormat.HTML: "text/html"
        }
        return content_types.get(format, "application/octet-stream")
    
    def _initialize_system_templates(self):
        """Initialize default system templates"""
        system_templates = [
            {
                "template_id": "portfolio_summary_basic",
                "template_name": "Basic Portfolio Summary",
                "report_type": ReportType.PORTFOLIO_SUMMARY,
                "description": "Standard portfolio summary with key metrics",
                "required_parameters": ["portfolio_id"],
                "optional_parameters": ["as_of_date", "include_assets"]
            },
            {
                "template_id": "waterfall_analysis_standard",
                "template_name": "Standard Waterfall Analysis",
                "report_type": ReportType.WATERFALL_ANALYSIS,
                "description": "Comprehensive waterfall payment analysis",
                "required_parameters": ["portfolio_id", "periods"],
                "optional_parameters": ["scenario_id", "stress_scenarios"]
            },
            {
                "template_id": "risk_assessment_basic",
                "template_name": "Basic Risk Assessment",
                "report_type": ReportType.RISK_ASSESSMENT,
                "description": "Standard risk metrics and analysis",
                "required_parameters": ["portfolio_id"],
                "optional_parameters": ["confidence_level", "time_horizon"]
            }
        ]
        
        try:
            with get_db_session() as db:
                for template_data in system_templates:
                    existing = db.query(ReportTemplate).filter(
                        ReportTemplate.template_id == template_data["template_id"]
                    ).first()
                    
                    if not existing:
                        template = ReportTemplate(
                            template_id=template_data["template_id"],
                            template_name=template_data["template_name"],
                            report_type=template_data["report_type"],
                            description=template_data["description"],
                            required_parameters=template_data["required_parameters"],
                            optional_parameters=template_data["optional_parameters"],
                            is_system_template=True,
                            created_at=datetime.utcnow()
                        )
                        db.add(template)
                
                db.commit()
                logger.info("System report templates initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize system templates: {str(e)}")


# Global instance
reports_service = ReportsService()