"""
Concentration Threshold Repository
Data access layer for concentration test threshold management
"""

from typing import Optional, List, Dict, Tuple
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import IntegrityError

from ..models.database.concentration_threshold_models import (
    ConcentrationTestDefinition,
    DealConcentrationThreshold, 
    ConcentrationTestExecution,
    ConcentrationTestSummary
)
from ..models.clo_deal import CLODeal


class ConcentrationThresholdRepository:
    """Repository for concentration test threshold data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================
    # Test Definition Methods
    # ========================================
    
    async def get_all_test_definitions(self) -> List[ConcentrationTestDefinition]:
        """Get all concentration test definitions"""
        return self.db.query(ConcentrationTestDefinition).filter(
            ConcentrationTestDefinition.is_active == True
        ).order_by(ConcentrationTestDefinition.test_number).all()
    
    async def get_test_definition(self, test_id: int) -> Optional[ConcentrationTestDefinition]:
        """Get test definition by ID"""
        return self.db.query(ConcentrationTestDefinition).filter(
            ConcentrationTestDefinition.test_id == test_id
        ).first()
    
    async def get_test_definition_by_number(self, test_number: int) -> Optional[ConcentrationTestDefinition]:
        """Get test definition by test number (VBA TestNum enum)"""
        return self.db.query(ConcentrationTestDefinition).filter(
            ConcentrationTestDefinition.test_number == test_number
        ).first()
    
    async def get_tests_by_category(self, category: str) -> List[ConcentrationTestDefinition]:
        """Get test definitions by category"""
        return self.db.query(ConcentrationTestDefinition).filter(
            and_(
                ConcentrationTestDefinition.test_category == category,
                ConcentrationTestDefinition.is_active == True
            )
        ).order_by(ConcentrationTestDefinition.test_number).all()
    
    # ========================================
    # Deal Threshold Methods
    # ========================================
    
    async def get_deal_threshold(
        self, 
        deal_id: str, 
        test_id: int, 
        analysis_date: date
    ) -> Optional[DealConcentrationThreshold]:
        """Get deal-specific threshold effective on analysis date"""
        return self.db.query(DealConcentrationThreshold).filter(
            and_(
                DealConcentrationThreshold.deal_id == deal_id,
                DealConcentrationThreshold.test_id == test_id,
                DealConcentrationThreshold.effective_date <= analysis_date,
                or_(
                    DealConcentrationThreshold.expiry_date.is_(None),
                    DealConcentrationThreshold.expiry_date > analysis_date
                )
            )
        ).order_by(desc(DealConcentrationThreshold.effective_date)).first()
    
    async def get_all_deal_thresholds(
        self, 
        deal_id: str, 
        analysis_date: Optional[date] = None
    ) -> List[Tuple[ConcentrationTestDefinition, Optional[DealConcentrationThreshold]]]:
        """
        Get all thresholds for a deal, combining test definitions with deal-specific overrides
        Returns list of (test_definition, deal_threshold_or_none) tuples
        """
        analysis_date = analysis_date or date(2016, 3, 23)
        
        # Get all active test definitions
        test_definitions = await self.get_all_test_definitions()
        
        # Get all effective deal thresholds for this date
        deal_thresholds_query = self.db.query(DealConcentrationThreshold).filter(
            and_(
                DealConcentrationThreshold.deal_id == deal_id,
                DealConcentrationThreshold.effective_date <= analysis_date,
                or_(
                    DealConcentrationThreshold.expiry_date.is_(None),
                    DealConcentrationThreshold.expiry_date > analysis_date
                )
            )
        )
        
        # Create lookup dict for deal thresholds by test_id
        deal_thresholds_dict = {}
        for threshold in deal_thresholds_query.all():
            # Keep only the most recent effective threshold per test
            if (threshold.test_id not in deal_thresholds_dict or 
                threshold.effective_date > deal_thresholds_dict[threshold.test_id].effective_date):
                deal_thresholds_dict[threshold.test_id] = threshold
        
        # Combine test definitions with deal-specific thresholds
        result = []
        for test_def in test_definitions:
            deal_threshold = deal_thresholds_dict.get(test_def.test_id)
            result.append((test_def, deal_threshold))
        
        return result
    
    async def create_deal_threshold(
        self, 
        deal_id: str,
        test_id: int,
        threshold_value: Decimal,
        effective_date: date,
        created_by: int,
        expiry_date: Optional[date] = None,
        mag_version: Optional[str] = None,
        rating_agency: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DealConcentrationThreshold:
        """Create new deal-specific threshold override"""
        
        threshold = DealConcentrationThreshold(
            deal_id=deal_id,
            test_id=test_id,
            threshold_value=threshold_value,
            effective_date=effective_date,
            expiry_date=expiry_date,
            mag_version=mag_version,
            rating_agency=rating_agency,
            notes=notes,
            created_by=created_by
        )
        
        try:
            self.db.add(threshold)
            self.db.commit()
            self.db.refresh(threshold)
            return threshold
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Failed to create threshold: {str(e)}")
    
    async def update_deal_threshold(
        self,
        threshold_id: int,
        threshold_value: Optional[Decimal] = None,
        expiry_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Optional[DealConcentrationThreshold]:
        """Update existing deal threshold"""
        
        threshold = self.db.query(DealConcentrationThreshold).filter(
            DealConcentrationThreshold.id == threshold_id
        ).first()
        
        if not threshold:
            return None
        
        if threshold_value is not None:
            threshold.threshold_value = threshold_value
        if expiry_date is not None:
            threshold.expiry_date = expiry_date
        if notes is not None:
            threshold.notes = notes
        
        threshold.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(threshold)
            return threshold
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Failed to update threshold: {str(e)}")
    
    async def get_threshold_history(
        self, 
        deal_id: str, 
        test_id: int
    ) -> List[DealConcentrationThreshold]:
        """Get complete history of threshold changes for a deal/test"""
        return self.db.query(DealConcentrationThreshold).filter(
            and_(
                DealConcentrationThreshold.deal_id == deal_id,
                DealConcentrationThreshold.test_id == test_id
            )
        ).order_by(desc(DealConcentrationThreshold.effective_date)).all()
    
    # ========================================
    # Test Execution Methods
    # ========================================
    
    async def save_test_execution(
        self,
        deal_id: str,
        test_id: int,
        analysis_date: date,
        threshold_used: Decimal,
        calculated_value: Decimal,
        pass_fail_status: str,
        threshold_source: str,
        numerator: Optional[Decimal] = None,
        denominator: Optional[Decimal] = None,
        excess_amount: Optional[Decimal] = None,
        comments: Optional[str] = None
    ) -> ConcentrationTestExecution:
        """Save concentration test execution result"""
        
        execution = ConcentrationTestExecution(
            deal_id=deal_id,
            test_id=test_id,
            analysis_date=analysis_date,
            threshold_used=threshold_used,
            calculated_value=calculated_value,
            numerator=numerator,
            denominator=denominator,
            pass_fail_status=pass_fail_status,
            excess_amount=excess_amount,
            threshold_source=threshold_source,
            comments=comments
        )
        
        try:
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)
            return execution
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Failed to save test execution: {str(e)}")
    
    async def get_test_executions(
        self,
        deal_id: str,
        analysis_date: date,
        test_id: Optional[int] = None
    ) -> List[ConcentrationTestExecution]:
        """Get test execution results for a deal/date"""
        
        query = self.db.query(ConcentrationTestExecution).filter(
            and_(
                ConcentrationTestExecution.deal_id == deal_id,
                ConcentrationTestExecution.analysis_date == analysis_date
            )
        )
        
        if test_id:
            query = query.filter(ConcentrationTestExecution.test_id == test_id)
        
        return query.order_by(ConcentrationTestExecution.test_id).all()
    
    async def get_execution_history(
        self,
        deal_id: str,
        test_id: int,
        limit: int = 50
    ) -> List[ConcentrationTestExecution]:
        """Get historical execution results for a specific test"""
        return self.db.query(ConcentrationTestExecution).filter(
            and_(
                ConcentrationTestExecution.deal_id == deal_id,
                ConcentrationTestExecution.test_id == test_id
            )
        ).order_by(desc(ConcentrationTestExecution.analysis_date)).limit(limit).all()
    
    # ========================================
    # Summary Methods
    # ========================================
    
    async def create_test_summary(
        self,
        deal_id: str,
        analysis_date: date,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        na_tests: int,
        total_violations: Decimal = Decimal('0'),
        worst_violation_test_id: Optional[int] = None,
        worst_violation_amount: Optional[Decimal] = None
    ) -> ConcentrationTestSummary:
        """Create summary of test execution results"""
        
        # Delete existing summary for this deal/date
        self.db.query(ConcentrationTestSummary).filter(
            and_(
                ConcentrationTestSummary.deal_id == deal_id,
                ConcentrationTestSummary.analysis_date == analysis_date
            )
        ).delete()
        
        summary = ConcentrationTestSummary(
            deal_id=deal_id,
            analysis_date=analysis_date,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            na_tests=na_tests,
            total_violations=total_violations,
            worst_violation_test_id=worst_violation_test_id,
            worst_violation_amount=worst_violation_amount
        )
        
        try:
            self.db.add(summary)
            self.db.commit()
            self.db.refresh(summary)
            return summary
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Failed to create test summary: {str(e)}")
    
    async def get_test_summary(
        self,
        deal_id: str,
        analysis_date: date
    ) -> Optional[ConcentrationTestSummary]:
        """Get test summary for deal/date"""
        return self.db.query(ConcentrationTestSummary).filter(
            and_(
                ConcentrationTestSummary.deal_id == deal_id,
                ConcentrationTestSummary.analysis_date == analysis_date
            )
        ).first()
    
    # ========================================
    # Utility Methods
    # ========================================
    
    async def resolve_effective_threshold(
        self,
        deal_id: str,
        test_id: int,
        analysis_date: date
    ) -> Tuple[Decimal, str]:
        """
        Resolve effective threshold value and source for a deal/test/date
        Returns (threshold_value, threshold_source)
        """
        
        # Check for deal-specific threshold first
        deal_threshold = await self.get_deal_threshold(deal_id, test_id, analysis_date)
        if deal_threshold:
            return deal_threshold.threshold_value, 'deal'
        
        # Fall back to default threshold from test definition
        test_definition = await self.get_test_definition(test_id)
        if test_definition and test_definition.default_threshold:
            return test_definition.default_threshold, 'default'
        
        # No threshold found
        return Decimal('0'), 'none'
    
    async def get_deals_with_custom_thresholds(self) -> List[str]:
        """Get list of deal IDs that have custom threshold overrides"""
        result = self.db.query(DealConcentrationThreshold.deal_id).distinct().all()
        return [row[0] for row in result]
    
    async def get_threshold_statistics(self) -> Dict[str, any]:
        """Get statistics about threshold usage"""
        
        total_tests = self.db.query(func.count(ConcentrationTestDefinition.test_id)).scalar()
        active_tests = self.db.query(func.count(ConcentrationTestDefinition.test_id)).filter(
            ConcentrationTestDefinition.is_active == True
        ).scalar()
        
        total_custom_thresholds = self.db.query(func.count(DealConcentrationThreshold.id)).scalar()
        deals_with_custom = len(await self.get_deals_with_custom_thresholds())
        
        total_executions = self.db.query(func.count(ConcentrationTestExecution.id)).scalar()
        
        return {
            'total_test_definitions': total_tests,
            'active_test_definitions': active_tests,
            'total_custom_thresholds': total_custom_thresholds,
            'deals_with_custom_thresholds': deals_with_custom,
            'total_test_executions': total_executions
        }