"""
CLO Cash Flow Models - Python conversion of SimpleCashflow.cls VBA class
Represents asset cash flow data with payment schedules and calculations
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

from ..core.database import Base


class AssetCashFlow(Base):
    """
    Asset Cash Flow Model - Individual cash flow record for an asset
    Converted from VBA SimpleCashflow.cls dynamic arrays to relational model
    """
    __tablename__ = 'asset_cash_flows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    blkrock_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False, doc="Asset identifier")
    period_number = Column(Integer, nullable=False, doc="Cash flow period sequence")
    
    # Dates
    payment_date = Column(Date, nullable=False, doc="Payment date")
    accrual_start_date = Column(Date, nullable=False, doc="Interest accrual start date")
    accrual_end_date = Column(Date, nullable=False, doc="Interest accrual end date")
    
    # Balances
    beginning_balance = Column(Numeric(18,2), nullable=False, default=0, doc="Beginning balance")
    ending_balance = Column(Numeric(18,2), nullable=False, default=0, doc="Ending balance")
    default_balance = Column(Numeric(18,2), default=0, doc="Defaulted balance")
    mv_default_balance = Column(Numeric(18,2), default=0, doc="Market value default balance")
    
    # Cash Flows
    interest_payment = Column(Numeric(18,2), default=0, doc="Interest payment")
    scheduled_principal = Column(Numeric(18,2), default=0, doc="Scheduled principal payment")
    unscheduled_principal = Column(Numeric(18,2), default=0, doc="Unscheduled principal payment (prepayments)")
    default_amount = Column(Numeric(18,2), default=0, doc="Default amount")
    mv_default_amount = Column(Numeric(18,2), default=0, doc="Market value default amount")
    recoveries = Column(Numeric(18,2), default=0, doc="Recovery amount")
    net_loss = Column(Numeric(18,2), default=0, doc="Net loss amount")
    
    # Purchases/Sales
    purchases = Column(Numeric(18,2), default=0, doc="Asset purchases")
    sales = Column(Numeric(18,2), default=0, doc="Asset sales")
    
    # Total cash flow (computed)
    total_cash_flow = Column(Numeric(18,2), default=0, doc="Total cash flow for period")
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship back to asset
    asset = relationship("Asset", back_populates="cash_flows")
    
    def __repr__(self):
        return f"<AssetCashFlow({self.blkrock_id}[{self.period_number}]: ${self.total_cash_flow:,.0f} on {self.payment_date})>"
    
    @property
    def total_principal(self) -> Decimal:
        """Total principal payment (scheduled + unscheduled)"""
        return (self.scheduled_principal or Decimal('0')) + (self.unscheduled_principal or Decimal('0'))
    
    def calculate_total_cash_flow(self) -> Decimal:
        """Calculate and update total cash flow for period"""
        total = ((self.interest_payment or Decimal('0')) +
                (self.scheduled_principal or Decimal('0')) +
                (self.unscheduled_principal or Decimal('0')) +
                (self.recoveries or Decimal('0')))
        
        self.total_cash_flow = total
        return total


class CashFlowSummary(Base):
    """
    Cash Flow Summary - Aggregated cash flows by date range
    Supports period-based queries like VBA GetDefaults(), GetInterest() methods
    """
    __tablename__ = 'cash_flow_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    blkrock_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False)
    summary_date = Column(Date, nullable=False, doc="Summary date")
    period_start = Column(Date, nullable=False, doc="Period start date")
    period_end = Column(Date, nullable=False, doc="Period end date")
    
    # Aggregated amounts
    total_interest = Column(Numeric(18,2), default=0)
    total_scheduled_principal = Column(Numeric(18,2), default=0)  
    total_unscheduled_principal = Column(Numeric(18,2), default=0)
    total_defaults = Column(Numeric(18,2), default=0)
    total_recoveries = Column(Numeric(18,2), default=0)
    total_net_losses = Column(Numeric(18,2), default=0)
    
    # Balances
    beginning_balance = Column(Numeric(18,2), default=0)
    ending_balance = Column(Numeric(18,2), default=0)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<CashFlowSummary({self.blkrock_id}: {self.period_start} to {self.period_end})>"


# Add relationship to Asset model
from ..models.asset import Asset
Asset.cash_flows = relationship("AssetCashFlow", back_populates="asset", cascade="all, delete-orphan")


class CashFlowCalculator:
    """
    Cash Flow Calculator - Business logic for asset cash flow calculations
    Converts VBA SimpleCashflow methods to Python service class
    """
    
    @staticmethod
    def get_defaults_in_period(cash_flows: List[AssetCashFlow], 
                              start_date: date, 
                              end_date: date,
                              is_first_period: bool = False) -> Decimal:
        """
        Convert VBA GetDefaults() method
        Defaults happen at beginning of accrual period
        """
        total_defaults = Decimal('0')
        
        for cf in cash_flows:
            if is_first_period and cf.accrual_start_date <= end_date:
                total_defaults += (cf.default_amount or Decimal('0'))
            elif start_date < cf.accrual_start_date <= end_date:
                total_defaults += (cf.default_amount or Decimal('0'))
                
        return total_defaults
    
    @staticmethod 
    def get_interest_in_period(cash_flows: List[AssetCashFlow],
                              start_date: date,
                              end_date: date) -> Decimal:
        """Convert VBA GetInterest() method"""
        total_interest = Decimal('0')
        
        for cf in cash_flows:
            if start_date < cf.payment_date <= end_date:
                total_interest += (cf.interest_payment or Decimal('0'))
                
        return total_interest
    
    @staticmethod
    def get_principal_in_period(cash_flows: List[AssetCashFlow],
                               start_date: date, 
                               end_date: date,
                               scheduled_only: bool = False) -> Decimal:
        """Convert VBA GetSchedPrin() and GetUnschedPrin() methods"""
        total_principal = Decimal('0')
        
        for cf in cash_flows:
            if start_date < cf.payment_date <= end_date:
                total_principal += (cf.scheduled_principal or Decimal('0'))
                if not scheduled_only:
                    total_principal += (cf.unscheduled_principal or Decimal('0'))
                    
        return total_principal
    
    @staticmethod
    def get_recoveries_in_period(cash_flows: List[AssetCashFlow],
                                start_date: date,
                                end_date: date) -> Decimal:
        """Convert VBA GetRecoveries() method"""
        total_recoveries = Decimal('0')
        
        for cf in cash_flows:
            if start_date < cf.payment_date <= end_date:
                total_recoveries += (cf.recoveries or Decimal('0'))
                
        return total_recoveries
    
    @staticmethod
    def get_balance_at_date(cash_flows: List[AssetCashFlow],
                           target_date: date) -> Decimal:
        """Convert VBA GetBegBlance() method"""
        if not cash_flows:
            return Decimal('0')
        
        # Sort by payment date
        sorted_flows = sorted(cash_flows, key=lambda x: x.payment_date)
        
        # If date is after all payments, balance is 0
        if target_date > sorted_flows[-1].payment_date:
            return Decimal('0')
            
        # If date is before all payments, return initial balance
        if target_date < sorted_flows[0].payment_date:
            return sorted_flows[0].beginning_balance or Decimal('0')
        
        # Find appropriate balance
        for cf in reversed(sorted_flows):
            if cf.payment_date <= target_date:
                return cf.ending_balance or Decimal('0')
                
        return Decimal('0')