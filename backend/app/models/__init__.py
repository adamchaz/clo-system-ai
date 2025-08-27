"""
CLO Management System Models
All SQLAlchemy ORM models for the application
"""

from .asset import Asset, AssetFlags, RatingEnum, CouponTypeEnum, DayCountEnum
from .cash_flow import AssetCashFlow
from .clo_deal import CLODeal, CLOTranche, DealAsset
from .liability import Liability, LiabilityCashFlow, DayCountConvention, CouponType
from .waterfall import WaterfallConfiguration, WaterfallStep, PaymentPriority
from .waterfall_config import WaterfallTemplate, PaymentRule, WaterfallModification, PaymentOverride
from .waterfall_types import WaterfallType, BaseWaterfallStrategy, WaterfallStrategyFactory
from .dynamic_waterfall import DynamicWaterfallStrategy
from .mag_waterfall import MagWaterfallStrategy, MagWaterfallType, MagWaterfallConfiguration, MagPerformanceMetrics
from .clo_deal_engine import CLODealEngine
from .portfolio_optimization import PortfolioOptimizationEngine, OptimizationInputs, OptimizationResult
from .hypothesis_testing import HypothesisTestingEngine, HypothesisTestResult
from .constraint_satisfaction import ConstraintSatisfactionEngine, ConstraintType, ConstraintViolation
from .oc_trigger import OCTrigger, OCTriggerCalculator, OCTriggerResult
from .ic_trigger import ICTrigger, ICTriggerCalculator, ICTriggerResult
from .trigger_aware_waterfall import TriggerAwareWaterfallStrategy
from .fee import Fee, FeeCalculation, FeeCalculator, FeeType
from .collateral_pool import (
    CollateralPool, CollateralPoolAsset, CollateralPoolAccount, ConcentrationTestResult,
    CollateralPoolForCLO, AssetCashFlowForDeal,
    CollateralPoolCalculator, CollateralPoolForCLOCalculator,
    TransactionType, AnalysisType
)
# Old VBA-based concentration tests removed - using database-driven approach only
from .database.concentration_threshold_models import (
    ConcentrationTestDefinition, DealConcentrationThreshold, ConcentrationTestExecution,
    ConcentrationTestSummary
)
from .database_driven_concentration_test import (
    DatabaseDrivenConcentrationTest, DatabaseTestResult
)
from .reports import (
    Report, ReportTemplate, ReportSchedule, 
    ReportType, ReportStatus, ReportFormat
)
from .documents import (
    Document, DocumentAccess, DocumentShare, DocumentFolder, DocumentFolderItem,
    DocumentType, DocumentStatus, AccessLevel
)
from .auth import (
    User, UserRole
)

__all__ = [
    # Asset Models
    'Asset',
    'AssetCashFlow', 
    'AssetFlags',
    'RatingEnum',
    'CouponTypeEnum',
    'DayCountEnum',
    
    # CLO Structure
    'CLODeal',
    'CLOTranche', 
    'DealAsset',
    'Liability',
    'LiabilityCashFlow',
    'DayCountConvention',
    'CouponType',
    
    # Waterfall System
    'WaterfallConfiguration',
    'WaterfallTemplate',
    'PaymentRule',
    'WaterfallModification',
    'PaymentOverride',
    'WaterfallStep',
    'PaymentPriority',
    'WaterfallType',
    'BaseWaterfallStrategy',
    'WaterfallStrategyFactory',
    'DynamicWaterfallStrategy',
    
    # Magnetar Waterfall
    'MagWaterfallStrategy',
    'MagWaterfallType',
    'MagWaterfallConfiguration',
    'MagPerformanceMetrics',
    
    # CLO Engine
    'CLODealEngine',
    
    # Portfolio Optimization  
    'PortfolioOptimizationEngine',
    'OptimizationInputs',
    'OptimizationResult',
    'HypothesisTestingEngine',
    'HypothesisTestResult',
    'ConstraintSatisfactionEngine',
    'ConstraintType',
    'ConstraintViolation',
    
    # OC/IC Triggers
    'OCTrigger',
    'OCTriggerCalculator', 
    'OCTriggerResult',
    'ICTrigger',
    'ICTriggerCalculator',
    'ICTriggerResult',
    'TriggerAwareWaterfallStrategy',
    
    # Fee Management
    'Fee',
    'FeeCalculation',
    'FeeCalculator',
    'FeeType',
    
    # Collateral Pool System
    'CollateralPool',
    'CollateralPoolAsset',
    'CollateralPoolAccount',
    'ConcentrationTestResult',
    'CollateralPoolForCLO',
    'AssetCashFlowForDeal',
    'CollateralPoolCalculator',
    'CollateralPoolForCLOCalculator',
    'TransactionType',
    'AnalysisType',
    
    # Database-Driven Concentration Testing (VBA approaches removed)
    'ConcentrationTestDefinition',
    'DealConcentrationThreshold', 
    'ConcentrationTestExecution',
    'ConcentrationTestSummary',
    'DatabaseDrivenConcentrationTest',
    'DatabaseTestResult',
    
    # Reports System
    'Report',
    'ReportTemplate',
    'ReportSchedule',
    'ReportType',
    'ReportStatus',
    'ReportFormat',
    
    # Document Management
    'Document',
    'DocumentAccess',
    'DocumentShare',
    'DocumentFolder',
    'DocumentFolderItem',
    'DocumentType',
    'DocumentStatus',
    'AccessLevel',
    
    # Authentication & Authorization
    'User',
    'UserRole'
]