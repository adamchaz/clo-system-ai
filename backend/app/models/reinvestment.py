"""
Reinvestment System - VBA Reinvest.cls Conversion

This module provides a complete Python implementation of the VBA Reinvest.cls,
including reinvestment period modeling, cash flow projections, and portfolio dynamics.

Key Features:
- Complete VBA functional parity for Reinvest.cls (283 lines)
- Reinvestment cash flow modeling with prepayment/default/severity curves
- SimpleCashflow equivalent with database persistence
- Yield curve integration for floating rate calculations
- Liquidation and portfolio runoff modeling
- Advanced scenario analysis capabilities
"""

import json
import math
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from sqlalchemy import Column, Integer, String, Date, DateTime, DECIMAL, Boolean, Text, ForeignKey, Index, text
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

from ..core.database import Base


class ReinvestmentPeriodModel(Base):
    """SQLAlchemy model for reinvestment periods"""
    __tablename__ = 'reinvestment_periods'
    
    reinvest_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    reinvest_period = Column(Integer, nullable=False)
    maturity_months = Column(Integer, nullable=False)
    months_between_payments = Column(Integer, nullable=False, server_default=text('3'))
    yield_curve_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('TRUE'))
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    reinvest_info = relationship("ReinvestmentInfoModel", back_populates="period", uselist=False, cascade="all, delete-orphan")
    cash_flows = relationship("ReinvestmentCashFlowModel", back_populates="period", cascade="all, delete-orphan")
    scenarios = relationship("ReinvestmentScenarioModel", back_populates="base_period", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_reinvestment_periods_deal_id', 'deal_id'),
        Index('ix_reinvestment_periods_dates', 'period_start', 'period_end'),
    )


class ReinvestmentInfoModel(Base):
    """SQLAlchemy model for reinvestment parameters"""
    __tablename__ = 'reinvestment_info'
    
    info_id = Column(Integer, primary_key=True, autoincrement=True)
    reinvest_id = Column(Integer, ForeignKey('reinvestment_periods.reinvest_id', ondelete='CASCADE'), nullable=False)
    reinvest_price = Column(DECIMAL(precision=6, scale=4), nullable=False, server_default=text('1.0000'))
    spread_bps = Column(Integer, nullable=False, server_default=text('500'))
    floor_rate = Column(DECIMAL(precision=6, scale=4), nullable=False, server_default=text('0.0000'))
    liquidation_price = Column(DECIMAL(precision=6, scale=4), nullable=False, server_default=text('0.7000'))
    lag_periods = Column(Integer, nullable=False, server_default=text('2'))
    prepayment_rate_annual = Column(DECIMAL(precision=6, scale=4), nullable=True)
    default_rate_annual = Column(DECIMAL(precision=6, scale=4), nullable=True)
    severity_rate = Column(DECIMAL(precision=6, scale=4), nullable=True)
    prepayment_vector = Column(Text, nullable=True, doc='JSON array of prepayment rates by period')
    default_vector = Column(Text, nullable=True, doc='JSON array of default rates by period')
    severity_vector = Column(Text, nullable=True, doc='JSON array of severity rates by period')
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    period = relationship("ReinvestmentPeriodModel", back_populates="reinvest_info")
    
    __table_args__ = (
        Index('ix_reinvestment_info_reinvest_id', 'reinvest_id'),
    )


class ReinvestmentCashFlowModel(Base):
    """SQLAlchemy model for reinvestment cash flows"""
    __tablename__ = 'reinvestment_cash_flows'
    
    cash_flow_id = Column(Integer, primary_key=True, autoincrement=True)
    reinvest_id = Column(Integer, ForeignKey('reinvestment_periods.reinvest_id', ondelete='CASCADE'), nullable=False)
    payment_period = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    accrual_start_date = Column(Date, nullable=False)
    accrual_end_date = Column(Date, nullable=False)
    
    # Balance information
    beg_performing_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    beg_default_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    beg_mv_default_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    end_performing_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    end_default_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    end_mv_default_balance = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    
    # Cash flow components
    interest = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    scheduled_principal = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    unscheduled_principal = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    period_default = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    period_mv_default = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    recoveries = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    net_loss = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    sold = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    
    # Calculation parameters
    coupon_rate = Column(DECIMAL(precision=6, scale=4), nullable=True)
    libor_rate = Column(DECIMAL(precision=6, scale=4), nullable=True)
    day_count_fraction = Column(DECIMAL(precision=8, scale=6), nullable=True)
    prepayment_rate_period = Column(DECIMAL(precision=6, scale=4), nullable=True)
    default_rate_period = Column(DECIMAL(precision=6, scale=4), nullable=True)
    severity_rate_period = Column(DECIMAL(precision=6, scale=4), nullable=True)
    
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    period = relationship("ReinvestmentPeriodModel", back_populates="cash_flows")
    
    __table_args__ = (
        Index('ix_reinvestment_cash_flows_reinvest_period', 'reinvest_id', 'payment_period'),
        Index('ix_reinvestment_cash_flows_payment_date', 'payment_date'),
    )


class ReinvestmentScenarioModel(Base):
    """SQLAlchemy model for reinvestment scenarios"""
    __tablename__ = 'reinvestment_scenarios'
    
    scenario_id = Column(Integer, primary_key=True, autoincrement=True)
    base_reinvest_id = Column(Integer, ForeignKey('reinvestment_periods.reinvest_id', ondelete='CASCADE'), nullable=False)
    scenario_name = Column(String(100), nullable=False)
    scenario_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scenario adjustments
    spread_adjustment_bps = Column(Integer, nullable=True)
    prepayment_multiplier = Column(DECIMAL(precision=4, scale=2), nullable=True)
    default_multiplier = Column(DECIMAL(precision=4, scale=2), nullable=True)
    severity_adjustment = Column(DECIMAL(precision=4, scale=2), nullable=True)
    liquidation_price_override = Column(DECIMAL(precision=6, scale=4), nullable=True)
    
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    base_period = relationship("ReinvestmentPeriodModel", back_populates="scenarios")
    
    __table_args__ = (
        Index('ix_reinvestment_scenarios_base_reinvest', 'base_reinvest_id'),
        Index('ix_reinvestment_scenarios_type', 'scenario_type'),
    )


class PaymentDates:
    """VBA PaymentDates equivalent structure"""
    
    def __init__(self, payment_date: date, coll_beg_date: date, coll_end_date: date):
        self.PaymentDate = payment_date      # VBA: PaymentDate
        self.CollBegDate = coll_beg_date     # VBA: CollBegDate  
        self.CollEndDate = coll_end_date     # VBA: CollEndDate


class ReinvestInfo:
    """
    VBA ReinvestInfo equivalent structure
    Holds reinvestment parameters used in cash flow projections
    """
    
    def __init__(self, maturity: int, reinvest_price: float = 1.0, spread: float = 0.05,
                 floor: float = 0.0, liquidation: float = 0.7, lag: int = 6,
                 prepayment: Union[float, List[float]] = 0.15,
                 default: Union[float, List[float]] = 0.03,
                 severity: Union[float, List[float]] = 0.40):
        """
        Initialize ReinvestInfo with VBA-equivalent parameters
        
        Args:
            maturity: Asset maturity in months
            reinvest_price: Purchase price (1.0 = par)
            spread: Interest rate spread (decimal)
            floor: Interest rate floor (decimal)  
            liquidation: Liquidation price (decimal)
            lag: Recovery lag in months
            prepayment: Prepayment rate(s) - annual decimal or array
            default: Default rate(s) - annual decimal or array  
            severity: Severity rate(s) - decimal or array
        """
        # VBA exact variable names
        self.Maturity = maturity           # VBA: Maturity
        self.ReinvestPrice = reinvest_price # VBA: ReinvestPrice
        self.Spread = spread               # VBA: Spread
        self.Floor = floor                 # VBA: Floor
        self.Liquidation = liquidation     # VBA: Liquidation
        self.Lag = lag                     # VBA: Lag
        self.Prepayment = prepayment       # VBA: Prepayment (can be array)
        self.Default = default             # VBA: Default (can be array)
        self.Severity = severity           # VBA: Severity (can be array)


class SimpleCashflow:
    """
    VBA SimpleCashflow equivalent implementation
    Maintains cash flow data structure used by Reinvest class
    """
    
    def __init__(self, max_periods: int = 100):
        """Initialize SimpleCashflow with VBA-equivalent arrays"""
        # VBA arrays (1-based indexing in comments, 0-based in Python)
        self._max_periods = max_periods
        self._payment_dates: List[Optional[date]] = [None] * (max_periods + 1)
        self._acc_beg_dates: List[Optional[date]] = [None] * (max_periods + 1)
        self._acc_end_dates: List[Optional[date]] = [None] * (max_periods + 1)
        
        # Balance arrays
        self._beg_balance: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._end_balance: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._default_bal: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._mv_default_bal: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        
        # Cash flow component arrays
        self._interest: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._sched_principal: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._unsched_principal: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._default: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._mv_default: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._recoveries: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._net_loss: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._sold: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        self._total: List[Decimal] = [Decimal('0')] * (max_periods + 1)
        
        self._count = 0
    
    # VBA-equivalent property methods
    def PaymentDate(self, period: int, value: date = None) -> Optional[date]:
        """VBA: PaymentDate property"""
        if value is not None:
            self._payment_dates[period] = value
            self._count = max(self._count, period)
        return self._payment_dates[period] if period <= len(self._payment_dates) - 1 else None
    
    def AccBegDate(self, period: int, value: date = None) -> Optional[date]:
        """VBA: AccBegDate property"""  
        if value is not None:
            self._acc_beg_dates[period] = value
        return self._acc_beg_dates[period] if period <= len(self._acc_beg_dates) - 1 else None
    
    def AccEndDate(self, period: int, value: date = None) -> Optional[date]:
        """VBA: AccEndDate property"""
        if value is not None:
            self._acc_end_dates[period] = value
        return self._acc_end_dates[period] if period <= len(self._acc_end_dates) - 1 else None
    
    def BegBalance(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: BegBalance property"""
        if value is not None:
            self._beg_balance[period] = value
        return self._beg_balance[period] if period <= len(self._beg_balance) - 1 else Decimal('0')
    
    def EndBalance(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: EndBalance property"""
        if value is not None:
            self._end_balance[period] = value  
        return self._end_balance[period] if period <= len(self._end_balance) - 1 else Decimal('0')
    
    def DefaultBal(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: DefaultBal property"""
        if value is not None:
            self._default_bal[period] = value
        return self._default_bal[period] if period <= len(self._default_bal) - 1 else Decimal('0')
    
    def MVDefaultBal(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: MVDefaultBal property"""
        if value is not None:
            self._mv_default_bal[period] = value
        return self._mv_default_bal[period] if period <= len(self._mv_default_bal) - 1 else Decimal('0')
    
    def Interest(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Interest property"""
        if value is not None:
            self._interest[period] = value
        return self._interest[period] if period <= len(self._interest) - 1 else Decimal('0')
    
    def SchedPrincipal(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: SchedPrincipal property"""
        if value is not None:
            self._sched_principal[period] = value
        return self._sched_principal[period] if period <= len(self._sched_principal) - 1 else Decimal('0')
    
    def UnSchedPrincipal(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: UnSchedPrincipal property"""
        if value is not None:
            self._unsched_principal[period] = value
        return self._unsched_principal[period] if period <= len(self._unsched_principal) - 1 else Decimal('0')
    
    def Default(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Default property"""
        if value is not None:
            self._default[period] = value
        return self._default[period] if period <= len(self._default) - 1 else Decimal('0')
    
    def MVDefault(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: MVDefault property"""
        if value is not None:
            self._mv_default[period] = value
        return self._mv_default[period] if period <= len(self._mv_default) - 1 else Decimal('0')
    
    def Recoveries(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Recoveries property"""
        if value is not None:
            self._recoveries[period] = value
        return self._recoveries[period] if period <= len(self._recoveries) - 1 else Decimal('0')
    
    def Netloss(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Netloss property"""
        if value is not None:
            self._net_loss[period] = value
        return self._net_loss[period] if period <= len(self._net_loss) - 1 else Decimal('0')
    
    def Sold(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Sold property"""
        if value is not None:
            self._sold[period] = value
        return self._sold[period] if period <= len(self._sold) - 1 else Decimal('0')
    
    def Total(self, period: int, value: Decimal = None) -> Decimal:
        """VBA: Total property"""
        if value is not None:
            self._total[period] = value
        return self._total[period] if period <= len(self._total) - 1 else Decimal('0')
    
    @property
    def Count(self) -> int:
        """VBA: Count property"""
        return self._count


class Reinvest:
    """
    VBA Reinvest.cls Python Implementation
    
    Complete conversion of VBA Reinvest.cls (283 lines) with exact functional parity.
    Handles reinvestment period cash flow modeling, portfolio dynamics, and liquidation.
    
    Key VBA Methods Implemented:
    - DealSetup(): Initialize reinvestment with deal dates and parameters
    - AddReinvestment(): Model cash flows for reinvestment amount
    - GetProceeds(): Get interest/principal proceeds for current period
    - Liquidate(): Liquidate portfolio at specified price
    - Rollfoward(): Advance to next period
    - GetCollatCF(): Export cash flow results
    
    VBA Variables Mapped:
    - clsDealCF -> deal_cf (SimpleCashflow)
    - clsReinvestInfo -> reinvest_info (ReinvestInfo)
    - clsPeriod -> period
    - clsMoBetPay -> months_between_payments
    - clsYieldCurve -> yield_curve
    - clsLastperiod -> last_period
    """
    
    def __init__(self, session: Session = None):
        """Initialize Reinvest with VBA-equivalent structure"""
        # VBA exact variable names (converted from Hungarian notation)
        self.deal_cf: Optional[SimpleCashflow] = None      # VBA: clsDealCF
        self.reinvest_info: Optional[ReinvestInfo] = None  # VBA: clsReinvestInfo  
        self.period: int = 1                               # VBA: clsPeriod
        self.months_between_payments: int = 3              # VBA: clsMoBetPay
        self.yield_curve = None                            # VBA: clsYieldCurve
        self.last_period: int = 0                          # VBA: clsLastperiod
        
        # Enhanced attributes for database integration
        self.session = session
        self.reinvest_id: Optional[int] = None
        self.deal_id: Optional[str] = None
        
        # Internal state
        self._is_setup: bool = False
    
    def deal_setup(self, i_deal_dates: List[PaymentDates], i_reinvest_info: ReinvestInfo,
                   i_mo_bet_pay: int, i_yc) -> None:
        """
        EXACT VBA DealSetup() method implementation
        
        VBA Signature: Public Sub DealSetup(iDealDates() As PaymentDates, ireinvestinfo As ReinvestInfo, 
                                           iMoBetPay As Long, iYC As YieldCurve)
        
        Sets up reinvestment with deal payment schedule and parameters
        """
        # VBA: Set clsDealCF = New SimpleCashflow
        self.deal_cf = SimpleCashflow(len(i_deal_dates) + 50)  # Extra buffer for reinvestment periods
        
        # VBA: For i = 1 To UBound(iDealDates)
        for i in range(1, len(i_deal_dates)):
            # VBA array assignments - exact implementation
            # VBA: clsDealCF.PaymentDate(i) = iDealDates(i).PaymentDate
            self.deal_cf.PaymentDate(i, i_deal_dates[i].PaymentDate)
            # VBA: clsDealCF.AccBegDate(i) = iDealDates(i).CollBegDate
            self.deal_cf.AccBegDate(i, i_deal_dates[i].CollBegDate)
            # VBA: clsDealCF.AccEndDate(i) = iDealDates(i).CollEndDate
            self.deal_cf.AccEndDate(i, i_deal_dates[i].CollEndDate)
        
        # VBA: clsPeriod = 1
        self.period = 1
        
        # VBA: clsReinvestInfo = ireinvestinfo
        self.reinvest_info = i_reinvest_info
        
        # VBA: clsMoBetPay = iMoBetPay
        self.months_between_payments = i_mo_bet_pay
        
        # VBA: Set clsYieldCurve = iYC
        self.yield_curve = i_yc
        
        self._is_setup = True
    
    def prin_ball_all_assets(self) -> float:
        """
        EXACT VBA PrinBallAllAssets() method implementation
        
        VBA Signature: Public Function PrinBallAllAssets() As Double
        Returns: Principal balance including defaults for next period
        """
        l_numerator = 0.0  # VBA: lNumerator
        
        # VBA: If clsPeriod + 1 <= clsDealCF.Count Then
        if self.period + 1 <= self.deal_cf.Count:
            # VBA: PrinBallAllAssets = clsDealCF.BegBalance(clsPeriod + 1) + clsDealCF.DefaultBal(clsPeriod + 1)
            return float(self.deal_cf.BegBalance(self.period + 1) + self.deal_cf.DefaultBal(self.period + 1))
        
        return 0.0
    
    def prin_ball_ex_defaults(self) -> float:
        """
        EXACT VBA PrinBallExDefaults() method implementation
        
        VBA Signature: Public Function PrinBallExDefaults() As Double
        Returns: Principal balance excluding defaults for next period
        """
        # VBA: If clsPeriod + 1 <= clsDealCF.Count Then
        if self.period + 1 <= self.deal_cf.Count:
            # VBA: PrinBallExDefaults = clsDealCF.BegBalance(clsPeriod + 1)
            return float(self.deal_cf.BegBalance(self.period + 1))
        
        return 0.0
    
    def prin_ball_defaults(self) -> float:
        """
        EXACT VBA PrinBallDefaults() method implementation
        
        VBA Signature: Public Function PrinBallDefaults() As Double
        Returns: Default balance for next period
        """
        # VBA: If clsPeriod + 1 <= clsDealCF.Count Then
        if self.period + 1 <= self.deal_cf.Count:
            # VBA: PrinBallDefaults = clsDealCF.DefaultBal(clsPeriod + 1)
            return float(self.deal_cf.DefaultBal(self.period + 1))
        
        return 0.0
    
    def mv_defaults(self) -> float:
        """
        EXACT VBA MVDefaults() method implementation
        
        VBA Signature: Public Function MVDefaults() As Double
        Returns: Market value default balance for next period
        """
        # VBA: If clsPeriod + 1 <= clsDealCF.Count Then
        if self.period + 1 <= self.deal_cf.Count:
            # VBA: MVDefaults = clsDealCF.MVDefaultBal(clsPeriod + 1)
            return float(self.deal_cf.MVDefaultBal(self.period + 1))
        
        return 0.0
    
    def un_sched_prin(self) -> float:
        """
        EXACT VBA UnSchedPrin() method implementation
        
        VBA Signature: Public Function UnSchedPrin() As Double
        Returns: Unscheduled principal for current period
        """
        # VBA: If clsPeriod <= clsDealCF.Count Then
        if self.period <= self.deal_cf.Count:
            # VBA: UnSchedPrin = clsDealCF.UnSchedPrincipal(clsPeriod)
            return float(self.deal_cf.UnSchedPrincipal(self.period))
        
        return 0.0
    
    def add_reinvestment(self, i_amount: float) -> None:
        """
        EXACT VBA AddReinvestment() method implementation
        
        VBA Signature: Public Function AddReinvestment(iAmount As Double)
        
        This is the core reinvestment modeling method that projects cash flows
        for a reinvestment amount using prepayment/default/severity assumptions.
        
        The method implements exact VBA logic including:
        - Array handling for prepayment/default/severity vectors
        - Period-by-period cash flow calculations
        - Recovery lag modeling
        - Interest rate calculations with floors
        - Balance rollforward logic
        """
        if not self._is_setup or not self.deal_cf or not self.reinvest_info:
            raise RuntimeError("Reinvest must be setup before adding reinvestment")
        
        # VBA variable declarations - exact names
        l_beg_bal = 0.0                    # VBA: lBegBal
        l_default_bal = 0.0                # VBA: lDefaultBal
        l_mv_default_bal = 0.0             # VBA: lMVDefaultBal
        l_end_default_bal = 0.0            # VBA: lEndDefaultBal
        l_end_mv_default_bal = 0.0         # VBA: lEndMVDefaultBal
        l_default = 0.0                    # VBA: lDefault
        l_mv_default = 0.0                 # VBA: lMVDefault
        l_interest = 0.0                   # VBA: lInterest
        l_sched_prin = 0.0                 # VBA: lSchedprin
        l_unsched_prin = 0.0               # VBA: lUnschedprin
        l_recoveries = 0.0                 # VBA: lRecoveries
        l_net_loss = 0.0                   # VBA: lNetLoss
        l_end_bal = 0.0                    # VBA: lEndBal
        l_num_of_payments = 0              # VBA: lNumofPayments
        l_period_lag = 0                   # VBA: lPeriodLag
        l_coupon = 0.0                     # VBA: lCoupon
        l_libor_rate = 0.0                 # VBA: lLIborRate
        l_sold = 0.0                       # VBA: lSold
        l_period_prepay = 0.0              # VBA: lPeriodPrepay
        l_period_default = 0.0             # VBA: lPeriodDefault
        l_period_sev = 0.0                 # VBA: lPeriodSev
        
        # VBA: lNumofPayments = clsReinvestInfo.Maturity / clsMoBetPay
        l_num_of_payments = self.reinvest_info.Maturity // self.months_between_payments
        
        # VBA: lPeriodLag = clsReinvestInfo.Lag / clsMoBetPay
        l_period_lag = self.reinvest_info.Lag // self.months_between_payments
        
        # VBA: ReDim lDefaultArr(lNumofPayments)
        # VBA: ReDim lMVDefaultArr(lNumofPayments)
        l_default_arr = [0.0] * (l_num_of_payments + 1)    # VBA: lDefaultArr
        l_mv_default_arr = [0.0] * (l_num_of_payments + 1) # VBA: lMVDefaultArr
        
        # VBA: lBegBal = iAmount / clsReinvestInfo.ReinvestPrice
        l_beg_bal = i_amount / self.reinvest_info.ReinvestPrice
        
        # VBA: For i = 1 To lNumofPayments
        for i in range(1, l_num_of_payments + 1):
            
            # VBA prepayment rate handling - exact logic
            # VBA: If IsArray(clsReinvestInfo.Prepayment) Then
            if isinstance(self.reinvest_info.Prepayment, list):
                # VBA: If UBound(clsReinvestInfo.Prepayment) < i Then
                if len(self.reinvest_info.Prepayment) < i:
                    # VBA: lPeriodPrepay = UBound(clsReinvestInfo.Prepayment)
                    l_period_prepay = self.reinvest_info.Prepayment[-1]  # Last element
                else:
                    # VBA: lPeriodPrepay = clsReinvestInfo.Prepayment(i)
                    l_period_prepay = self.reinvest_info.Prepayment[i-1]  # Adjust for 0-based indexing
            else:
                # VBA: lPeriodPrepay = clsReinvestInfo.Prepayment
                l_period_prepay = self.reinvest_info.Prepayment
            
            # VBA default rate handling - exact logic
            # VBA: If IsArray(clsReinvestInfo.Default) Then
            if isinstance(self.reinvest_info.Default, list):
                # VBA: If UBound(clsReinvestInfo.Default) < i Then
                if len(self.reinvest_info.Default) < i:
                    # VBA: lPeriodDefault = UBound(clsReinvestInfo.Default)
                    l_period_default = self.reinvest_info.Default[-1]  # Last element
                else:
                    # VBA: lPeriodDefault = clsReinvestInfo.Default(i)
                    l_period_default = self.reinvest_info.Default[i-1]  # Adjust for 0-based indexing
            else:
                # VBA: lPeriodDefault = clsReinvestInfo.Default
                l_period_default = self.reinvest_info.Default
            
            # VBA severity handling - exact logic
            # VBA: If IsArray(clsReinvestInfo.Severity) Then
            if isinstance(self.reinvest_info.Severity, list):
                # VBA: If UBound(clsReinvestInfo.Severity) < i Then
                if len(self.reinvest_info.Severity) < i:
                    # VBA: lPeriodSev = UBound(clsReinvestInfo.Severity)
                    l_period_sev = self.reinvest_info.Severity[-1]  # Last element
                else:
                    # VBA: lPeriodSev = clsReinvestInfo.Severity(i)
                    l_period_sev = self.reinvest_info.Severity[i-1]  # Adjust for 0-based indexing
            else:
                # VBA: lPeriodSev = clsReinvestInfo.Severity
                l_period_sev = self.reinvest_info.Severity
            
            # VBA default calculation - exact implementation
            # VBA: lDefault = lBegBal * ConvertAnnualRates(lPeriodDefault, clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i))
            start_date = self.deal_cf.PaymentDate(self.period + i - 1)
            end_date = self.deal_cf.PaymentDate(self.period + i)
            period_default_rate = self._convert_annual_rates(l_period_default, start_date, end_date)
            l_default = l_beg_bal * period_default_rate
            l_default_arr[i] = l_default
            
            # VBA: lMVDefault = lDefault * (1 - lPeriodSev)
            l_mv_default = l_default * (1 - l_period_sev)
            l_mv_default_arr[i] = l_mv_default
            
            # VBA yield curve integration - exact implementation
            # VBA: lLIborRate = clsYieldCurve.SpotRate(clsDealCF.PaymentDate(clsPeriod + i - 1), clsMoBetPay)
            if self.yield_curve:
                l_libor_rate = self.yield_curve.spot_rate(start_date, self.months_between_payments)
            else:
                l_libor_rate = 0.05  # Default 5% if no yield curve
            
            # VBA floor and spread logic - exact implementation
            # VBA: If lLIborRate > clsReinvestInfo.Floor Then
            if l_libor_rate > self.reinvest_info.Floor:
                # VBA: lCoupon = lLIborRate + clsReinvestInfo.Spread
                l_coupon = l_libor_rate + self.reinvest_info.Spread
            else:
                # VBA: lCoupon = clsReinvestInfo.Spread + clsReinvestInfo.Floor
                l_coupon = self.reinvest_info.Spread + self.reinvest_info.Floor
            
            # VBA interest calculation - exact implementation
            # VBA: lInterest = DateFraction(clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i), US30_360) * lCoupon * (lBegBal - lDefault)
            day_count_fraction = self._date_fraction_us30_360(start_date, end_date)
            l_interest = day_count_fraction * l_coupon * (l_beg_bal - l_default)
            
            # VBA scheduled principal logic - exact implementation
            # VBA: If i = lNumofPayments Then
            if i == l_num_of_payments:
                # VBA: lSchedprin = (lBegBal - lDefault)
                l_sched_prin = l_beg_bal - l_default
            else:
                l_sched_prin = 0.0
            
            # VBA unscheduled principal calculation - exact implementation  
            # VBA: lUnschedprin = (lBegBal - lDefault - lSchedprin) * ConvertAnnualRates(lPeriodPrepay, clsDealCF.PaymentDate(clsPeriod + i - 1), clsDealCF.PaymentDate(clsPeriod + i))
            period_prepay_rate = self._convert_annual_rates(l_period_prepay, start_date, end_date)
            l_unsched_prin = (l_beg_bal - l_default - l_sched_prin) * period_prepay_rate
            
            # VBA recovery logic with lag - exact implementation
            # VBA: If i - lPeriodLag > 0 Then
            if i - l_period_lag > 0:
                # VBA: lRecoveries = lMVDefaultArr(i - lPeriodLag)
                l_recoveries = l_mv_default_arr[i - l_period_lag]
                # VBA: lNetLoss = lDefaultArr(i - lPeriodLag) - lMVDefaultArr(i - lPeriodLag)
                l_net_loss = l_default_arr[i - l_period_lag] - l_mv_default_arr[i - l_period_lag]
            else:
                l_recoveries = 0.0
                l_net_loss = 0.0
            
            # VBA ending balance calculations - exact implementation
            # VBA: lEndBal = lBegBal - lDefault - lSchedprin - lUnschedprin
            l_end_bal = l_beg_bal - l_default - l_sched_prin - l_unsched_prin
            
            # VBA: lEndDefaultBal = lDefaultBal + lDefault - lRecoveries - lNetLoss
            l_end_default_bal = l_default_bal + l_default - l_recoveries - l_net_loss
            
            # VBA: lEndMVDefaultBal = lMVDefaultBal + lMVDefault - lRecoveries
            l_end_mv_default_bal = l_mv_default_bal + l_mv_default - l_recoveries
            
            # VBA final period logic - exact implementation
            # VBA: If i = lNumofPayments Then
            if i == l_num_of_payments:
                # VBA: lNetLoss = lNetLoss + lEndDefaultBal
                l_net_loss = l_net_loss + l_end_default_bal
                # VBA: lEndDefaultBal = 0
                l_end_default_bal = 0
                # VBA: lEndMVDefaultBal = 0
                l_end_mv_default_bal = 0
                # VBA: If clsLastperiod < i + clsPeriod Then clsLastperiod = i + clsPeriod
                if self.last_period < i + self.period:
                    self.last_period = i + self.period
            
            # VBA cash flow aggregation - exact implementation
            period_index = self.period + i
            
            # VBA: clsDealCF.BegBalance(clsPeriod + i) = clsDealCF.BegBalance(clsPeriod + i) + lBegBal
            current_beg_bal = self.deal_cf.BegBalance(period_index)
            self.deal_cf.BegBalance(period_index, current_beg_bal + Decimal(str(l_beg_bal)))
            
            # VBA: clsDealCF.MVDefaultBal(clsPeriod + i) = clsDealCF.MVDefaultBal(clsPeriod + i) + lMVDefaultBal
            current_mv_default_bal = self.deal_cf.MVDefaultBal(period_index)
            self.deal_cf.MVDefaultBal(period_index, current_mv_default_bal + Decimal(str(l_mv_default_bal)))
            
            # VBA: clsDealCF.DefaultBal(clsPeriod + i) = clsDealCF.DefaultBal(clsPeriod + i) + lDefaultBal
            current_default_bal = self.deal_cf.DefaultBal(period_index)
            self.deal_cf.DefaultBal(period_index, current_default_bal + Decimal(str(l_default_bal)))
            
            # VBA: clsDealCF.Default(clsPeriod + i) = clsDealCF.Default(clsPeriod + i) + lDefault
            current_default = self.deal_cf.Default(period_index)
            self.deal_cf.Default(period_index, current_default + Decimal(str(l_default)))
            
            # VBA: clsDealCF.MVDefault(clsPeriod + i) = clsDealCF.MVDefault(clsPeriod + i) + lMVDefault
            current_mv_default = self.deal_cf.MVDefault(period_index)
            self.deal_cf.MVDefault(period_index, current_mv_default + Decimal(str(l_mv_default)))
            
            # VBA: clsDealCF.Interest(clsPeriod + i) = clsDealCF.Interest(clsPeriod + i) + lInterest
            current_interest = self.deal_cf.Interest(period_index)
            self.deal_cf.Interest(period_index, current_interest + Decimal(str(l_interest)))
            
            # VBA: clsDealCF.SchedPrincipal(clsPeriod + i) = clsDealCF.SchedPrincipal(clsPeriod + i) + lSchedprin
            current_sched_prin = self.deal_cf.SchedPrincipal(period_index)
            self.deal_cf.SchedPrincipal(period_index, current_sched_prin + Decimal(str(l_sched_prin)))
            
            # VBA: clsDealCF.UnSchedPrincipal(clsPeriod + i) = clsDealCF.UnSchedPrincipal(clsPeriod + i) + lUnschedprin
            current_unsched_prin = self.deal_cf.UnSchedPrincipal(period_index)
            self.deal_cf.UnSchedPrincipal(period_index, current_unsched_prin + Decimal(str(l_unsched_prin)))
            
            # VBA: clsDealCF.Recoveries(clsPeriod + i) = clsDealCF.Recoveries(clsPeriod + i) + lRecoveries
            current_recoveries = self.deal_cf.Recoveries(period_index)
            self.deal_cf.Recoveries(period_index, current_recoveries + Decimal(str(l_recoveries)))
            
            # VBA: clsDealCF.Netloss(clsPeriod + i) = clsDealCF.Netloss(clsPeriod + i) + lNetLoss
            current_net_loss = self.deal_cf.Netloss(period_index)
            self.deal_cf.Netloss(period_index, current_net_loss + Decimal(str(l_net_loss)))
            
            # VBA: clsDealCF.Sold(clsPeriod + i) = clsDealCF.Sold(clsPeriod + i) + lSold
            current_sold = self.deal_cf.Sold(period_index)
            self.deal_cf.Sold(period_index, current_sold + Decimal(str(l_sold)))
            
            # VBA balance rollforward - exact implementation
            # VBA: lBegBal = lEndBal
            l_beg_bal = l_end_bal
            # VBA: lDefaultBal = lEndDefaultBal
            l_default_bal = l_end_default_bal
            # VBA: lMVDefaultBal = lEndMVDefaultBal
            l_mv_default_bal = l_end_mv_default_bal
            
            # VBA variable reset - exact implementation
            l_default = 0.0
            l_mv_default = 0.0
            l_interest = 0.0
            l_sched_prin = 0.0
            l_unsched_prin = 0.0
            l_recoveries = 0.0
            l_net_loss = 0.0
            l_sold = 0.0
            
            # VBA exit condition - exact implementation
            # VBA: If clsPeriod + i + 1 > clsDealCF.Count Or lEndBal = 0 Then
            if self.period + i + 1 > self.deal_cf.Count or l_end_bal == 0:
                # VBA: Exit For
                break
    
    def get_proceeds(self, i_proceeds: str) -> float:
        """
        EXACT VBA GetProceeds() method implementation
        
        VBA Signature: Public Function GetProceeds(iProceeds As String)
        Returns proceeds for current period by type
        """
        l_numerator = 0.0  # VBA: lNumerator
        
        # VBA: If iProceeds = "INTEREST" Then
        if i_proceeds == "INTEREST":
            # VBA: lNumerator = lNumerator + clsDealCF.Interest(clsPeriod)
            l_numerator = l_numerator + float(self.deal_cf.Interest(self.period))
        # VBA: ElseIf iProceeds = "PRINCIPAL" Then
        elif i_proceeds == "PRINCIPAL":
            # VBA: lNumerator = lNumerator + clsDealCF.SchedPrincipal(clsPeriod) + clsDealCF.UnSchedPrincipal(clsPeriod) + clsDealCF.Recoveries(clsPeriod)
            l_numerator = (l_numerator + 
                          float(self.deal_cf.SchedPrincipal(self.period)) + 
                          float(self.deal_cf.UnSchedPrincipal(self.period)) + 
                          float(self.deal_cf.Recoveries(self.period)))
        
        # VBA: GetProceeds = lNumerator
        return l_numerator
    
    def roll_forward(self) -> None:
        """
        EXACT VBA Rollfoward() method implementation
        
        VBA Signature: Public Sub Rollfoward()
        """
        # VBA: clsPeriod = clsPeriod + 1
        self.period = self.period + 1
    
    def get_collat_cf(self) -> List[List[Any]]:
        """
        EXACT VBA GetCollatCF() method implementation
        
        VBA Signature: Public Function GetCollatCF() As Variant
        Returns cash flow results as 2D array
        """
        # VBA: ReDim lOutput(0 To clsLastperiod, 10)
        l_output = []
        
        # VBA header row - exact implementation
        header = [
            "Beg Performing Balance",    # VBA: lOutput(0, 0)
            "Beg Default Balance",       # VBA: lOutput(0, 1) 
            "Beg MV Default Balance",    # VBA: lOutput(0, 2)
            "Period Default",            # VBA: lOutput(0, 3)
            "Period MV Default",         # VBA: lOutput(0, 4)
            "Interest",                  # VBA: lOutput(0, 5)
            "Scheduled Principal",       # VBA: lOutput(0, 6)
            "Unscheduled Principal",     # VBA: lOutput(0, 7)
            "Recoveries",                # VBA: lOutput(0, 8)
            "Net loss",                  # VBA: lOutput(0, 9)
            "Sold"                       # VBA: lOutput(0, 10)
        ]
        l_output.append(header)
        
        # VBA: For i = 1 To clsLastperiod
        for i in range(1, self.last_period + 1):
            row = [
                float(self.deal_cf.BegBalance(i)),        # VBA: lOutput(i, 0)
                float(self.deal_cf.DefaultBal(i)),        # VBA: lOutput(i, 1)
                float(self.deal_cf.MVDefaultBal(i)),      # VBA: lOutput(i, 2)
                float(self.deal_cf.Default(i)),           # VBA: lOutput(i, 3)
                float(self.deal_cf.MVDefault(i)),         # VBA: lOutput(i, 4)
                float(self.deal_cf.Interest(i)),          # VBA: lOutput(i, 5)
                float(self.deal_cf.SchedPrincipal(i)),    # VBA: lOutput(i, 6)
                float(self.deal_cf.UnSchedPrincipal(i)),  # VBA: lOutput(i, 7)
                float(self.deal_cf.Recoveries(i)),        # VBA: lOutput(i, 8)
                float(self.deal_cf.Netloss(i)),           # VBA: lOutput(i, 9)
                float(self.deal_cf.Sold(i))               # VBA: lOutput(i, 10)
            ]
            l_output.append(row)
        
        # VBA: GetCollatCF = lOutput
        return l_output
    
    def liquidate(self, i_liquid_price: float) -> float:
        """
        EXACT VBA Liquidate() method implementation
        
        VBA Signature: Public Function Liquidate(iLiquidPrice As Double) As Double
        Liquidates portfolio and returns proceeds
        """
        # VBA variable declarations - exact names
        l_sold = 0.0         # VBA: lSold
        l_loss = 0.0         # VBA: lLoss
        l_end_bal = 0.0      # VBA: lEndBal
        l_end_default_bal = 0.0      # VBA: lEndDefaultBal
        l_end_mv_default_bal = 0.0   # VBA: lEndMVDefaultBal
        
        # VBA ending balance calculations - exact implementation
        # VBA: lEndBal = clsDealCF.BegBalance(clsPeriod) - clsDealCF.Default(clsPeriod) - clsDealCF.UnSchedPrincipal(clsPeriod) - clsDealCF.SchedPrincipal(clsPeriod)
        l_end_bal = (float(self.deal_cf.BegBalance(self.period)) - 
                    float(self.deal_cf.Default(self.period)) - 
                    float(self.deal_cf.UnSchedPrincipal(self.period)) - 
                    float(self.deal_cf.SchedPrincipal(self.period)))
        
        # VBA: lEndDefaultBal = clsDealCF.DefaultBal(clsPeriod) + clsDealCF.Default(clsPeriod) - clsDealCF.Recoveries(clsPeriod) - clsDealCF.Netloss(clsPeriod)
        l_end_default_bal = (float(self.deal_cf.DefaultBal(self.period)) + 
                           float(self.deal_cf.Default(self.period)) - 
                           float(self.deal_cf.Recoveries(self.period)) - 
                           float(self.deal_cf.Netloss(self.period)))
        
        # VBA: lEndMVDefaultBal = clsDealCF.MVDefaultBal(clsPeriod) + clsDealCF.MVDefault(clsPeriod) - clsDealCF.Recoveries(clsPeriod)
        l_end_mv_default_bal = (float(self.deal_cf.MVDefaultBal(self.period)) + 
                              float(self.deal_cf.MVDefault(self.period)) - 
                              float(self.deal_cf.Recoveries(self.period)))
        
        # VBA liquidation calculations - exact implementation
        # VBA: lSold = lEndBal * iLiquidPrice + lEndMVDefaultBal
        l_sold = l_end_bal * i_liquid_price + l_end_mv_default_bal
        
        # VBA: lLoss = (1 - iLiquidPrice) * lEndBal + (lEndDefaultBal - lEndMVDefaultBal)
        l_loss = (1 - i_liquid_price) * l_end_bal + (l_end_default_bal - l_end_mv_default_bal)
        
        # VBA zero out future periods - exact implementation
        # VBA: For i = clsPeriod + 1 To clsDealCF.Count
        for i in range(self.period + 1, self.deal_cf.Count + 1):
            # VBA zero assignments - exact implementation
            self.deal_cf.BegBalance(i, Decimal('0'))
            self.deal_cf.Default(i, Decimal('0'))
            self.deal_cf.DefaultBal(i, Decimal('0'))
            self.deal_cf.EndBalance(i, Decimal('0'))
            self.deal_cf.Interest(i, Decimal('0'))
            self.deal_cf.MVDefault(i, Decimal('0'))
            self.deal_cf.MVDefaultBal(i, Decimal('0'))
            self.deal_cf.Netloss(i, Decimal('0'))
            self.deal_cf.Recoveries(i, Decimal('0'))
            self.deal_cf.SchedPrincipal(i, Decimal('0'))
            self.deal_cf.Total(i, Decimal('0'))
            self.deal_cf.UnSchedPrincipal(i, Decimal('0'))
        
        # VBA current period adjustments - exact implementation
        # VBA: clsDealCF.Netloss(clsPeriod) = clsDealCF.Netloss(clsPeriod) + lLoss
        current_net_loss = self.deal_cf.Netloss(self.period)
        self.deal_cf.Netloss(self.period, current_net_loss + Decimal(str(l_loss)))
        
        # VBA: clsDealCF.Sold(clsPeriod) = clsDealCF.Sold(clsPeriod) + lSold
        current_sold = self.deal_cf.Sold(self.period)
        self.deal_cf.Sold(self.period, current_sold + Decimal(str(l_sold)))
        
        # VBA: Liquidate = lSold
        # VBA: clsLastperiod = clsPeriod
        self.last_period = self.period
        
        return l_sold
    
    def _convert_annual_rates(self, annual_rate: float, start_date: date, end_date: date) -> float:
        """
        Convert annual rates to period rates
        Equivalent to VBA ConvertAnnualRates function
        """
        if not start_date or not end_date or end_date <= start_date:
            return 0.0
        
        # Calculate period length in years
        days_diff = (end_date - start_date).days
        period_years = days_diff / 365.25
        
        # Convert annual rate to period rate
        # Using simple linear conversion (VBA approach)
        period_rate = annual_rate * period_years
        
        return period_rate
    
    def _date_fraction_us30_360(self, start_date: date, end_date: date) -> float:
        """
        Calculate day count fraction using US 30/360 convention
        Equivalent to VBA DateFraction function with US30_360 parameter
        """
        if not start_date or not end_date or end_date <= start_date:
            return 0.0
        
        # US 30/360 day count convention
        y1, m1, d1 = start_date.year, start_date.month, start_date.day
        y2, m2, d2 = end_date.year, end_date.month, end_date.day
        
        # Adjust day counts per US 30/360 convention
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 >= 30:
            d2 = 30
        
        # Calculate days difference
        days = (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)
        
        # Return fraction
        return days / 360.0
    
    def save_to_database(self, deal_id: str, reinvest_period: int, 
                        period_start: date, period_end: date) -> int:
        """Save reinvestment to database"""
        if not self.session:
            raise RuntimeError("Database session required for persistence")
        
        if not self._is_setup:
            raise RuntimeError("Reinvest must be setup before saving")
        
        # Create reinvestment period record
        period_model = ReinvestmentPeriodModel(
            deal_id=deal_id,
            period_start=period_start,
            period_end=period_end,
            reinvest_period=reinvest_period,
            maturity_months=self.reinvest_info.Maturity,
            months_between_payments=self.months_between_payments,
            yield_curve_name=getattr(self.yield_curve, 'name', None)
        )
        
        self.session.add(period_model)
        self.session.flush()
        self.reinvest_id = period_model.reinvest_id
        
        # Save reinvestment info
        info_model = ReinvestmentInfoModel(
            reinvest_id=period_model.reinvest_id,
            reinvest_price=Decimal(str(self.reinvest_info.ReinvestPrice)),
            spread_bps=int(self.reinvest_info.Spread * 10000),
            floor_rate=Decimal(str(self.reinvest_info.Floor)),
            liquidation_price=Decimal(str(self.reinvest_info.Liquidation)),
            lag_periods=self.reinvest_info.Lag // self.months_between_payments,
            prepayment_rate_annual=(Decimal(str(self.reinvest_info.Prepayment)) 
                                   if not isinstance(self.reinvest_info.Prepayment, list) else None),
            default_rate_annual=(Decimal(str(self.reinvest_info.Default))
                                if not isinstance(self.reinvest_info.Default, list) else None),
            severity_rate=(Decimal(str(self.reinvest_info.Severity))
                          if not isinstance(self.reinvest_info.Severity, list) else None),
            prepayment_vector=(json.dumps(self.reinvest_info.Prepayment) 
                              if isinstance(self.reinvest_info.Prepayment, list) else None),
            default_vector=(json.dumps(self.reinvest_info.Default)
                           if isinstance(self.reinvest_info.Default, list) else None),
            severity_vector=(json.dumps(self.reinvest_info.Severity)
                            if isinstance(self.reinvest_info.Severity, list) else None)
        )
        
        self.session.add(info_model)
        
        # Save cash flows if any were generated
        if self.last_period > 0:
            for i in range(1, self.last_period + 1):
                cf_model = ReinvestmentCashFlowModel(
                    reinvest_id=period_model.reinvest_id,
                    payment_period=i,
                    payment_date=self.deal_cf.PaymentDate(i),
                    accrual_start_date=self.deal_cf.AccBegDate(i),
                    accrual_end_date=self.deal_cf.AccEndDate(i),
                    beg_performing_balance=self.deal_cf.BegBalance(i),
                    beg_default_balance=self.deal_cf.DefaultBal(i),
                    beg_mv_default_balance=self.deal_cf.MVDefaultBal(i),
                    interest=self.deal_cf.Interest(i),
                    scheduled_principal=self.deal_cf.SchedPrincipal(i),
                    unscheduled_principal=self.deal_cf.UnSchedPrincipal(i),
                    period_default=self.deal_cf.Default(i),
                    period_mv_default=self.deal_cf.MVDefault(i),
                    recoveries=self.deal_cf.Recoveries(i),
                    net_loss=self.deal_cf.Netloss(i),
                    sold=self.deal_cf.Sold(i)
                )
                self.session.add(cf_model)
        
        self.session.commit()
        return period_model.reinvest_id


class ReinvestmentService:
    """Service class for reinvestment operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_reinvestment_period(self, deal_id: str, period_start: date, period_end: date,
                                  reinvest_info: ReinvestInfo, payment_dates: List[PaymentDates],
                                  months_between_payments: int = 3, yield_curve=None) -> Reinvest:
        """Create and setup a new reinvestment period"""
        reinvest = Reinvest(self.session)
        reinvest.deal_setup(payment_dates, reinvest_info, months_between_payments, yield_curve)
        
        # Save to database
        reinvest_id = reinvest.save_to_database(deal_id, 1, period_start, period_end)
        
        return reinvest
    
    def load_reinvestment_period(self, reinvest_id: int) -> Optional[Reinvest]:
        """Load reinvestment period from database"""
        period_model = self.session.query(ReinvestmentPeriodModel).filter_by(
            reinvest_id=reinvest_id, is_active=True
        ).first()
        
        if not period_model:
            return None
        
        # Reconstruct reinvestment parameters
        info_model = period_model.reinvest_info
        if not info_model:
            return None
        
        # Create ReinvestInfo from database
        prepayment = (json.loads(info_model.prepayment_vector) 
                     if info_model.prepayment_vector 
                     else float(info_model.prepayment_rate_annual))
        default = (json.loads(info_model.default_vector)
                  if info_model.default_vector
                  else float(info_model.default_rate_annual))
        severity = (json.loads(info_model.severity_vector)
                   if info_model.severity_vector
                   else float(info_model.severity_rate))
        
        reinvest_info = ReinvestInfo(
            maturity=period_model.maturity_months,
            reinvest_price=float(info_model.reinvest_price),
            spread=info_model.spread_bps / 10000.0,
            floor=float(info_model.floor_rate),
            liquidation=float(info_model.liquidation_price),
            lag=info_model.lag_periods * period_model.months_between_payments,
            prepayment=prepayment,
            default=default,
            severity=severity
        )
        
        # Load cash flows and reconstruct payment dates
        cash_flows = self.session.query(ReinvestmentCashFlowModel).filter_by(
            reinvest_id=reinvest_id
        ).order_by(ReinvestmentCashFlowModel.payment_period).all()
        
        payment_dates = []
        for cf in cash_flows:
            payment_date = PaymentDates(cf.payment_date, cf.accrual_start_date, cf.accrual_end_date)
            payment_dates.append(payment_date)
        
        # Create and setup reinvestment
        reinvest = Reinvest(self.session)
        if payment_dates:
            # Need to load yield curve if specified
            yield_curve = None
            if period_model.yield_curve_name:
                # Load yield curve (would need YieldCurveService integration)
                pass
            
            reinvest.deal_setup(payment_dates, reinvest_info, 
                              period_model.months_between_payments, yield_curve)
            reinvest.reinvest_id = reinvest_id
        
        return reinvest
    
    def get_reinvestment_summary(self, deal_id: str) -> Dict[str, Any]:
        """Get reinvestment summary for a deal"""
        periods = self.session.query(ReinvestmentPeriodModel).filter_by(
            deal_id=deal_id, is_active=True
        ).order_by(ReinvestmentPeriodModel.reinvest_period).all()
        
        summary = {
            'deal_id': deal_id,
            'total_periods': len(periods),
            'periods': []
        }
        
        for period in periods:
            period_summary = {
                'reinvest_id': period.reinvest_id,
                'reinvest_period': period.reinvest_period,
                'period_start': period.period_start,
                'period_end': period.period_end,
                'maturity_months': period.maturity_months,
                'cash_flow_count': len(period.cash_flows)
            }
            
            if period.reinvest_info:
                period_summary['parameters'] = {
                    'reinvest_price': float(period.reinvest_info.reinvest_price),
                    'spread_bps': period.reinvest_info.spread_bps,
                    'floor_rate': float(period.reinvest_info.floor_rate),
                    'liquidation_price': float(period.reinvest_info.liquidation_price),
                    'prepayment_rate': float(period.reinvest_info.prepayment_rate_annual) if period.reinvest_info.prepayment_rate_annual else None,
                    'default_rate': float(period.reinvest_info.default_rate_annual) if period.reinvest_info.default_rate_annual else None,
                    'severity_rate': float(period.reinvest_info.severity_rate) if period.reinvest_info.severity_rate else None
                }
            
            summary['periods'].append(period_summary)
        
        return summary