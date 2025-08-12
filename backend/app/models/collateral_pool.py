"""
CLO Collateral Pool Management System
Converted from VBA CollateralPool.cls and CollateralPoolForCLO.cls
Handles portfolio aggregation, cash flow coordination, and risk calculations
"""

from typing import List, Dict, Optional, Any, Tuple, Union
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
import numpy as np
from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .asset import Asset
from .clo_deal import CLODeal
from .clo_deal_engine import Account, AccountType, CashType
from .cash_flow import AssetCashFlow
from .liability import DayCountConvention


class TransactionType(str, Enum):
    """Transaction types for portfolio management"""
    BUY = "BUY"
    SELL = "SELL" 
    SALE = "SALE"  # VBA compatibility


class AnalysisType(str, Enum):
    """Analysis types for different calculation modes"""
    STATIC = "STATIC"           # Static analysis without rating migration
    RATING_MIGRATION = "RATING_MIGRATION"  # Dynamic rating migration
    MONTE_CARLO = "MONTE_CARLO" # Monte Carlo simulation


class CollateralPool(Base):
    """
    Main Collateral Pool Model - converted from VBA CollateralPool.cls
    Handles portfolio-level aggregation, compliance testing, and optimization
    """
    __tablename__ = 'collateral_pools'
    
    pool_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    pool_name = Column(String(100), nullable=False)  # "Main Pool", "Ramp-Up Pool", etc.
    
    # Pool Configuration
    analysis_date = Column(Date, nullable=False)
    analysis_type = Column(String(20), default=AnalysisType.STATIC.value)
    use_rating_migration = Column(Boolean, default=False)
    
    # Pool State
    current_period = Column(Integer, default=1)
    last_calculated_period = Column(Integer, default=0)
    rerun_tests_required = Column(Boolean, default=True)
    
    # Portfolio Metrics (Cached)
    total_par_amount = Column(Numeric(18,2), default=0)
    total_market_value = Column(Numeric(18,2), default=0)
    total_assets = Column(Integer, default=0)
    average_par_amount = Column(Numeric(18,2), default=0)
    last_maturity_date = Column(Date)
    
    # Objective Function Results (Portfolio Optimization)
    current_objective_value = Column(Numeric(18,6), default=0)
    previous_objective_value = Column(Numeric(18,6), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="collateral_pools")
    pool_assets = relationship("CollateralPoolAsset", back_populates="pool", cascade="all, delete-orphan")
    pool_accounts = relationship("CollateralPoolAccount", back_populates="pool", cascade="all, delete-orphan")
    concentration_results = relationship("ConcentrationTestResult", back_populates="pool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CollateralPool({self.deal_id}:{self.pool_name}, Assets={self.total_assets})>"


class CollateralPoolAsset(Base):
    """
    Asset membership in collateral pool with position tracking
    """
    __tablename__ = 'collateral_pool_assets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey('collateral_pools.pool_id'), nullable=False)
    asset_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False)
    
    # Position Information
    par_amount = Column(Numeric(18,2), nullable=False)  # Current position size
    original_par_amount = Column(Numeric(18,2), nullable=False)  # Original position
    position_date = Column(Date, nullable=False)  # When position was established
    
    # Performance Tracking
    market_value_override = Column(Numeric(18,2))  # Pool-specific market value
    is_defaulted = Column(Boolean, default=False)
    last_rating_date = Column(Date)
    
    # Metadata
    added_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    pool = relationship("CollateralPool", back_populates="pool_assets")
    asset = relationship("Asset")
    
    def __repr__(self):
        return f"<PoolAsset(Pool={self.pool_id}, Asset={self.asset_id}, Par={self.par_amount})>"


class CollateralPoolAccount(Base):
    """
    Account tracking for collateral pool (converted from VBA Accounts integration)
    """
    __tablename__ = 'collateral_pool_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey('collateral_pools.pool_id'), nullable=False)
    account_type = Column(String(20), nullable=False)  # Collection, RampUp, etc.
    
    # Cash Balances
    principal_proceeds = Column(Numeric(18,2), default=0)
    interest_proceeds = Column(Numeric(18,2), default=0)
    
    # Metadata
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships  
    pool = relationship("CollateralPool", back_populates="pool_accounts")
    
    @property
    def total_proceeds(self) -> Decimal:
        """Total cash proceeds (interest + principal)"""
        return Decimal(str(self.principal_proceeds)) + Decimal(str(self.interest_proceeds))
    
    def __repr__(self):
        return f"<PoolAccount(Pool={self.pool_id}, Type={self.account_type}, Total={self.total_proceeds})>"


class ConcentrationTestResult(Base):
    """
    Storage for concentration test results by pool
    """
    __tablename__ = 'concentration_test_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey('collateral_pools.pool_id'), nullable=False)
    test_date = Column(Date, nullable=False)
    
    # Test Results Summary
    test_number = Column(Integer, nullable=False)
    test_name = Column(String(200), nullable=False)
    threshold_value = Column(Numeric(18,6))
    result_value = Column(Numeric(18,6))
    pass_fail = Column(String(10))  # "PASS", "FAIL", "N/A"
    pass_fail_comment = Column(Text)
    
    # Detailed Results (JSON)
    test_details = Column(JSON)  # Store complex test-specific data
    objective_contribution = Column(Numeric(18,6), default=0)
    
    # Metadata
    calculated_at = Column(DateTime, default=func.now())
    
    # Relationships
    pool = relationship("CollateralPool", back_populates="concentration_results")
    
    def __repr__(self):
        return f"<ConcentrationResult(Pool={self.pool_id}, Test={self.test_number}, Result={self.pass_fail})>"


class CollateralPoolForCLO(Base):
    """
    Deal-specific collateral pool - converted from VBA CollateralPoolForCLO.cls
    Focused on cash flow aggregation and deal processing
    """
    __tablename__ = 'collateral_pools_for_clo'
    
    pool_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    parent_pool_id = Column(Integer, ForeignKey('collateral_pools.pool_id'))  # Link to main pool
    
    # Deal Integration
    current_period = Column(Integer, default=1)
    last_calculated_period = Column(Integer, default=0)
    analysis_date = Column(Date, nullable=False)
    use_rating_migration = Column(Boolean, default=False)
    
    # Cash Flow State
    combined_cash_flows = Column(JSON)  # Aggregated deal cash flows
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal")
    parent_pool = relationship("CollateralPool", foreign_keys=[parent_pool_id])
    asset_cash_flows = relationship("AssetCashFlowForDeal", back_populates="pool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CollateralPoolForCLO({self.deal_id}, Period={self.current_period})>"


class AssetCashFlowForDeal(Base):
    """
    Asset-level cash flows aligned to deal payment schedule
    """
    __tablename__ = 'asset_cash_flows_for_deal'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey('collateral_pools_for_clo.pool_id'), nullable=False)
    asset_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False)
    blkrock_id = Column(String(50), nullable=False)  # For VBA compatibility
    
    # Period-by-Period Cash Flows (JSON Array)
    period_cash_flows = Column(JSON)  # Array of cash flow data by period
    
    # Summary Metrics
    total_periods = Column(Integer, default=0)
    final_maturity_date = Column(Date)
    
    # Metadata
    calculated_at = Column(DateTime, default=func.now())
    
    # Relationships
    pool = relationship("CollateralPoolForCLO", back_populates="asset_cash_flows")
    asset = relationship("Asset")
    
    def __repr__(self):
        return f"<AssetCashFlowForDeal(Pool={self.pool_id}, Asset={self.blkrock_id})>"


class CollateralPoolCalculator:
    """
    Main calculation engine - complete VBA CollateralPool.cls conversion
    Handles portfolio aggregation, optimization, and compliance testing
    """
    
    def __init__(self, pool_config: CollateralPool):
        """Initialize with pool configuration"""
        self.pool_id = pool_config.pool_id
        self.deal_id = pool_config.deal_id
        self.pool_name = pool_config.pool_name
        self.analysis_date = pool_config.analysis_date
        self.analysis_type = AnalysisType(pool_config.analysis_type)
        self.use_rating_migration = pool_config.use_rating_migration
        
        # State tracking
        self.current_period = pool_config.current_period
        self.last_calculated_period = pool_config.last_calculated_period
        self.rerun_tests_required = pool_config.rerun_tests_required
        
        # Asset and account dictionaries (VBA style)
        self.assets_dict: Dict[str, Asset] = {}
        self.accounts_dict: Dict[AccountType, Account] = {}
        
        # Supporting components (will be injected)
        self.concentration_test = None  # ConcentrationTest instance
        self.ratings_derivation = None  # RatingDerivations instance
        self.test_settings = None  # TestSettings instance
        
        # Calculated metrics
        self.total_par_amount = Decimal('0')
        self.total_market_value = Decimal('0')
        self.current_objective_value = Decimal('0')
    
    def check_account_balance(self, account_type: AccountType, cash_type: CashType) -> Decimal:
        """
        Check account balance - complete VBA CheckAccountBalance() conversion
        """
        if account_type not in self.accounts_dict:
            return Decimal('0')
        
        account = self.accounts_dict[account_type]
        
        if cash_type == CashType.PRINCIPAL:
            return account.principal_proceeds
        elif cash_type == CashType.INTEREST:
            return account.interest_proceeds  
        else:  # Total
            return account.total_proceeds
    
    def get_blkrock_ids(self) -> List[str]:
        """Get all asset BlackRock IDs - VBA GetBLKRockIDs() conversion"""
        return list(self.assets_dict.keys())
    
    def get_collateral_par_amount(self, filter_criteria: Optional[str] = None) -> Decimal:
        """
        Calculate total par amount with optional filtering - VBA GetCollatParAmount() conversion
        """
        total_par = Decimal('0')
        
        for blkrock_id, asset in self.assets_dict.items():
            if filter_criteria is None or len(filter_criteria) == 0:
                total_par += asset.par_amount
            elif asset.apply_filter(filter_criteria):
                total_par += asset.par_amount
        
        return total_par
    
    def add_asset(self, asset: Asset, reduce_cash: bool = False, 
                  account_type: Optional[AccountType] = None) -> None:
        """
        Add asset to pool - complete VBA AddAsset() conversion
        """
        if asset.blkrock_id in self.assets_dict:
            # Asset exists - add to position
            self.assets_dict[asset.blkrock_id].add_par(asset.par_amount)
        else:
            # New asset - copy and add rating derivations
            new_asset = asset.copy()
            
            # Rating derivations (will be implemented when RatingDerivations is available)
            if self.ratings_derivation and new_asset.mdy_rating is None:
                self.ratings_derivation.get_moodys_rating(new_asset)
            
            if self.ratings_derivation and new_asset.sp_rating is None:
                self.ratings_derivation.get_snp_ratings(new_asset)
            
            # Add rating history for analysis date
            if self.analysis_date:
                new_asset.add_moody_rating(self.analysis_date, new_asset.mdy_rating)
                new_asset.add_sp_rating(self.analysis_date, new_asset.sp_rating)
            
            self.assets_dict[asset.blkrock_id] = new_asset
        
        self.rerun_tests_required = True
    
    def remove_asset(self, blkrock_id: str) -> None:
        """Remove asset from pool - VBA RemoveAsset() conversion"""
        if blkrock_id in self.assets_dict:
            del self.assets_dict[blkrock_id]
        self.rerun_tests_required = True
    
    def get_asset(self, blkrock_id: str, copy: bool = True) -> Optional[Asset]:
        """
        Get asset from pool - VBA GetAsset() and GetAssetNonCopy() conversion
        """
        if blkrock_id not in self.assets_dict:
            return None
        
        if copy:
            return self.assets_dict[blkrock_id].copy()
        else:
            return self.assets_dict[blkrock_id]
    
    def get_asset_parameter(self, blkrock_id: str, parameter: str) -> Any:
        """
        Get specific asset parameter - complete VBA GetAssetParameter() conversion
        """
        if blkrock_id not in self.assets_dict:
            return None
        
        asset = self.assets_dict[blkrock_id]
        param_upper = parameter.upper()
        
        # VBA parameter mapping
        parameter_map = {
            "MARKET VALUE": asset.market_value,
            "PAR AMOUNT": asset.par_amount,
            "S & P RATING": asset.sp_rating,
            "S&P RATING": asset.sp_rating,
            "S&P INDUSTRY": asset.sp_industry,
            "MOODY'S INDUSTRY": asset.mdy_industry,
            "MOODY'S RATING": asset.mdy_rating,
            "MOODY'S RATING WARF": asset.mdy_dp_rating_warf,
            "MOODY'S RATING DPR": asset.mdy_dp_rating,
            "DEFAULTED": asset.default_asset,
            "MATURITY": asset.maturity,
            "WAL": asset.wal,
            "ISSUE NAME": asset.issuer_name,
            "COV-LITE": asset.cov_lite,
            "COUNTRY": asset.country,
            "FACILITY SIZE": asset.facility_size,
            "ANALYST OPINION": asset.analyst_opinion,
            "SPREAD": asset.cpn_spread,
            "LIBOR FLOOR": asset.libor_floor,
            "MOODY'S RECOVERY RATE": asset.mdy_recovery_rate
        }
        
        return parameter_map.get(param_upper)
    
    def add_account(self, account: Account, account_type: AccountType) -> None:
        """Add account to pool - VBA AddAccount() conversion"""
        self.accounts_dict[account_type] = account
        self.rerun_tests_required = True
    
    def add_cash(self, account_type: AccountType, cash_type: CashType, amount: Decimal) -> None:
        """Add cash to account - VBA AddCash() conversion"""
        if account_type in self.accounts_dict:
            self.accounts_dict[account_type].add(cash_type, amount)
        self.rerun_tests_required = True
    
    def asset_exists(self, blkrock_id: str) -> bool:
        """Check if asset exists in pool - VBA AssetExist() conversion"""
        return blkrock_id in self.assets_dict
    
    def add_par(self, blkrock_id: str, amount: Decimal) -> None:
        """
        Add par amount to existing asset - VBA AddPar() conversion
        Removes asset if par amount falls below $1
        """
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_par(amount)
            
            # Remove asset if position too small (VBA logic)
            if abs(self.assets_dict[blkrock_id].par_amount) <= 1:
                del self.assets_dict[blkrock_id]
    
    def purchase_asset(self, asset: Asset, price: Optional[Decimal] = None) -> None:
        """
        Purchase asset using available cash - complete VBA PurchaseAsset() conversion
        """
        # Calculate purchase price
        if price is None or price == 0:
            purchase_price = asset.market_value / 100
        else:
            purchase_price = price / 100 if price > 1 else price
        
        # Calculate purchase amount
        purchase_amount = purchase_price * asset.par_amount
        
        # Check available cash
        available_cash = self.check_account_balance(AccountType.COLLECTION, CashType.PRINCIPAL)
        
        if purchase_amount > available_cash:
            # Partial purchase - reduce par amount to match available cash
            affordable_par = available_cash / purchase_price
            par_reduction = affordable_par - asset.par_amount
            asset.add_par(par_reduction)
            purchase_amount = available_cash
        
        # Reduce cash and add asset
        self.add_cash(AccountType.COLLECTION, CashType.PRINCIPAL, -purchase_amount)
        self.add_asset(asset)
        
        self.rerun_tests_required = True
    
    def sell_asset(self, asset: Asset, price: Optional[Decimal] = None) -> None:
        """
        Sell asset and add cash - complete VBA SaleAsset() conversion  
        """
        if not self.asset_exists(asset.blkrock_id):
            return
        
        # Calculate sale price
        if price is None or price == 0:
            sale_price = asset.market_value / 100
        else:
            sale_price = price / 100 if price > 1 else price
        
        # Adjust sale amount if trying to sell more than owned
        existing_asset = self.assets_dict[asset.blkrock_id]
        if asset.par_amount > existing_asset.par_amount:
            par_reduction = existing_asset.par_amount - asset.par_amount  
            asset.add_par(par_reduction)
        
        # Calculate sale proceeds and reduce position
        sale_proceeds = asset.par_amount * sale_price
        self.add_cash(AccountType.COLLECTION, CashType.PRINCIPAL, sale_proceeds)
        self.add_par(asset.blkrock_id, -asset.par_amount)
        
        self.rerun_tests_required = True
    
    def calculate_average_par_amount(self) -> Decimal:
        """Calculate average par amount per asset - VBA CalcAverageParAmount() conversion"""
        if not self.assets_dict:
            return Decimal('0')
        
        total_par = sum(asset.par_amount for asset in self.assets_dict.values())
        return total_par / len(self.assets_dict)
    
    def get_num_assets(self, filter_criteria: Optional[str] = None) -> int:
        """Get number of assets with optional filter - VBA NumOfAssets() conversion"""
        if filter_criteria is None or len(filter_criteria) == 0:
            return len(self.assets_dict)
        
        count = 0
        for asset in self.assets_dict.values():
            if asset.apply_filter(filter_criteria):
                count += 1
        
        return count
    
    def get_last_maturity_date(self) -> Optional[date]:
        """Get latest asset maturity date - VBA LastMaturityDate() conversion"""
        if not self.assets_dict:
            return None
        
        latest_date = None
        for asset in self.assets_dict.values():
            if asset.maturity and (latest_date is None or asset.maturity > latest_date):
                latest_date = asset.maturity
        
        return latest_date
    
    def apply_filter(self, filter_criteria: str) -> Dict[str, int]:
        """
        Apply filter to assets - VBA ApplyFilter() conversion
        Returns dictionary of matching asset IDs
        """
        matching_assets = {}
        
        for blkrock_id, asset in self.assets_dict.items():
            if asset.apply_filter(filter_criteria):
                matching_assets[blkrock_id] = 1
        
        return matching_assets
    
    def calculate_cash_flows(self, current_balance: Optional[Decimal] = None,
                           initial_settlement_date: Optional[date] = None,
                           analysis_date: Optional[date] = None,
                           prepay_assumptions: Optional[Any] = None,
                           default_assumptions: Optional[Any] = None,
                           severity_assumptions: Optional[Any] = None,
                           lag_months: int = 0,
                           end_cf_date: Optional[date] = None,
                           yield_curve: Optional[Any] = None) -> None:
        """
        Calculate cash flows for all assets - VBA CalcCF() conversion
        """
        for asset in self.assets_dict.values():
            asset.calculate_cash_flows(
                current_balance=current_balance,
                initial_settlement_date=initial_settlement_date,
                analysis_date=analysis_date or self.analysis_date,
                prepay_assumptions=prepay_assumptions,
                default_assumptions=default_assumptions,
                severity_assumptions=severity_assumptions,
                lag_months=lag_months,
                end_cf_date=end_cf_date,
                yield_curve=yield_curve
            )
    
    def reset_assets_for_simulation(self) -> None:
        """Reset assets for simulation - VBA ReesetAssets() conversion"""
        for asset in self.assets_dict.values():
            asset.reset_for_simulation(self.analysis_date)
    
    def set_use_rating_migration(self, use_rm: bool) -> None:
        """Set rating migration flag for all assets - VBA SetUseRM() conversion"""
        for asset in self.assets_dict.values():
            asset.use_rm = use_rm
    
    def add_sp_rating(self, blkrock_id: str, rating_date: date, rating: str) -> None:
        """Add S&P rating to asset - VBA AddSPRating() conversion"""
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_sp_rating(rating_date, rating)
    
    def add_moody_rating(self, blkrock_id: str, rating_date: date, rating: str) -> None:
        """Add Moody's rating to asset - VBA AddMoodyRating() conversion"""
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_moody_rating(rating_date, rating)


class CollateralPoolForCLOCalculator:
    """
    Deal-specific cash flow calculator - complete VBA CollateralPoolForCLO.cls conversion
    """
    
    def __init__(self, pool_config: CollateralPoolForCLO):
        """Initialize with deal-specific pool configuration"""
        self.pool_id = pool_config.pool_id
        self.deal_id = pool_config.deal_id
        self.current_period = pool_config.current_period
        self.last_calculated_period = pool_config.last_calculated_period
        self.analysis_date = pool_config.analysis_date
        self.use_rating_migration = pool_config.use_rating_migration
        
        # Asset and cash flow tracking
        self.assets_dict: Dict[str, Asset] = {}
        self.deal_cf_dict: Dict[str, SimpleCashFlow] = {}  # Asset-specific cash flows
        self.combined_cash_flows: Optional[SimpleCashFlow] = None
        
        # Supporting components
        self.ratings_derivation = None
    
    def set_analysis_date(self, analysis_date: date, use_rating_migration: bool) -> None:
        """Set analysis parameters - VBA SetAnalysisDate() conversion"""
        self.analysis_date = analysis_date
        self.use_rating_migration = use_rating_migration
        self.set_use_rating_migration(use_rating_migration)
    
    def reset_par_amounts(self) -> None:
        """Reset all asset par amounts - VBA ResetParAmount() conversion"""
        for asset in self.assets_dict.values():
            current_par = asset.par_amount
            asset.add_par(-current_par)  # Zero out position
    
    def get_blkrock_ids(self) -> List[str]:
        """Get all asset IDs - VBA GetBLKRockIDs() conversion"""
        return list(self.assets_dict.keys())
    
    def get_proceeds(self, proceeds_type: str) -> Decimal:
        """
        Get aggregated proceeds by type - VBA GetProceeds() conversion
        """
        total_proceeds = Decimal('0')
        
        for blkrock_id in self.deal_cf_dict:
            cash_flow = self.deal_cf_dict[blkrock_id]
            
            if proceeds_type.upper() == "INTEREST":
                total_proceeds += cash_flow.get_interest_for_period(self.current_period)
            elif proceeds_type.upper() == "PRINCIPAL":
                # Principal = Scheduled + Unscheduled + Recoveries
                total_proceeds += (
                    cash_flow.get_scheduled_principal_for_period(self.current_period) +
                    cash_flow.get_unscheduled_principal_for_period(self.current_period) +
                    cash_flow.get_recoveries_for_period(self.current_period)
                )
        
        return total_proceeds
    
    def rollforward(self) -> None:
        """Move to next period - VBA Rollfoward() conversion"""
        self.current_period += 1
    
    def add_asset(self, asset: Asset) -> None:
        """
        Add asset with rating derivation - VBA AddAsset() conversion
        """
        if asset.blkrock_id in self.assets_dict:
            self.assets_dict[asset.blkrock_id].add_par(asset.par_amount)
        else:
            # Apply rating derivations if missing
            if self.ratings_derivation:
                if not asset.mdy_rating:
                    self.ratings_derivation.get_moodys_rating(asset)
                if not asset.mdy_dp_rating:
                    self.ratings_derivation.get_moodys_def_prob_rating(asset)
                if not asset.sp_rating:
                    self.ratings_derivation.get_snp_ratings(asset)
            
            self.assets_dict[asset.blkrock_id] = asset
    
    def remove_asset(self, blkrock_id: str) -> None:
        """Remove asset - VBA RemoveAsset() conversion"""
        if blkrock_id in self.assets_dict:
            del self.assets_dict[blkrock_id]
    
    def get_asset(self, blkrock_id: str) -> Optional[Asset]:
        """Get asset copy - VBA GetAsset() conversion"""
        if blkrock_id in self.assets_dict:
            return self.assets_dict[blkrock_id].copy()
        return None
    
    def get_asset_parameter(self, blkrock_id: str, parameter: str) -> Any:
        """
        Get asset parameter - simplified VBA GetAssetParameter() conversion
        """
        if blkrock_id not in self.assets_dict:
            return None
        
        asset = self.assets_dict[blkrock_id]
        param_upper = parameter.upper()
        
        if param_upper == "PAR AMOUNT":
            return asset.par_amount
        elif param_upper == "S & P RATING":
            return asset.sp_rating
        elif param_upper == "DEFAULTED":
            return asset.default_asset
        elif param_upper == "MATURITY":
            return asset.maturity
        
        return None
    
    def asset_exists(self, blkrock_id: str) -> bool:
        """Check asset existence - VBA AssetExist() conversion"""
        return blkrock_id in self.assets_dict
    
    def add_par(self, blkrock_id: str, amount: Decimal) -> None:
        """Add par amount to asset - VBA AddPar() conversion"""
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_par(amount)
    
    def get_last_maturity_date(self) -> Optional[date]:
        """Get latest maturity date - VBA LastMaturityDate() conversion"""
        if not self.assets_dict:
            return None
        
        latest_date = None
        for asset in self.assets_dict.values():
            if asset.maturity and (latest_date is None or asset.maturity > latest_date):
                latest_date = asset.maturity
        
        return latest_date
    
    def set_use_rating_migration(self, use_rm: bool) -> None:
        """Set rating migration for all assets - VBA SetUseRM() conversion"""
        for asset in self.assets_dict.values():
            asset.use_rm = use_rm
    
    def add_sp_rating(self, blkrock_id: str, rating_date: date, rating: str) -> None:
        """Add S&P rating - VBA AddSPRating() conversion"""
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_sp_rating(rating_date, rating)
    
    def add_moody_rating(self, blkrock_id: str, rating_date: date, rating: str) -> None:
        """Add Moody's rating - VBA AddMoodyRating() conversion"""
        if blkrock_id in self.assets_dict:
            self.assets_dict[blkrock_id].add_moody_rating(rating_date, rating)