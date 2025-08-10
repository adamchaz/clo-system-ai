"""
Incentive Fee Business Logic Service

Provides comprehensive incentive fee calculation and management services
for CLO deals, implementing VBA IncentiveFee.cls functionality with 
complete functional parity.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json
import math
from sqlalchemy.orm import Session

from ..models.incentive_fee import (
    IncentiveFeeStructure,
    SubordinatedPayment, 
    IncentiveFeeCalculation,
    FeePaymentTransaction,
    IRRCalculationHistory
)


class IncentiveFeeService:
    """
    Service for managing incentive fee structures and calculations
    
    Provides database persistence and business logic for incentive fee
    operations within CLO deals.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_fee_structure(
        self,
        deal_id: str,
        fee_structure_name: str,
        hurdle_rate: float,
        incentive_fee_rate: float,
        closing_date: date,
        description: Optional[str] = None
    ) -> IncentiveFeeStructure:
        """Create new incentive fee structure"""
        
        structure = IncentiveFeeStructure(
            deal_id=deal_id,
            fee_structure_name=fee_structure_name,
            hurdle_rate=Decimal(str(hurdle_rate)),
            incentive_fee_rate=Decimal(str(incentive_fee_rate)),
            closing_date=closing_date,
            description=description,
            is_active=True,
            threshold_reached=False,
            cum_discounted_sub_payments=Decimal('0')
        )
        
        self.session.add(structure)
        self.session.commit()
        return structure
    
    def load_fee_structure(self, fee_structure_id: int) -> Optional[IncentiveFeeStructure]:
        """Load existing fee structure by ID"""
        return self.session.query(IncentiveFeeStructure).filter_by(
            fee_structure_id=fee_structure_id
        ).first()
    
    def add_subordinated_payment(
        self,
        fee_structure_id: int,
        payment_date: date,
        payment_amount: float,
        is_historical: bool = False
    ) -> SubordinatedPayment:
        """Add subordinated payment record"""
        
        payment = SubordinatedPayment(
            fee_structure_id=fee_structure_id,
            payment_date=payment_date,
            payment_amount=Decimal(str(payment_amount)),
            is_historical=is_historical
        )
        
        self.session.add(payment)
        self.session.commit()
        return payment
    
    def get_subordinated_payments(
        self,
        fee_structure_id: int,
        up_to_date: Optional[date] = None
    ) -> List[SubordinatedPayment]:
        """Get subordinated payments for fee structure"""
        
        query = self.session.query(SubordinatedPayment).filter_by(
            fee_structure_id=fee_structure_id
        )
        
        if up_to_date:
            query = query.filter(SubordinatedPayment.payment_date <= up_to_date)
        
        return query.order_by(SubordinatedPayment.payment_date).all()


class IncentiveFee:
    """
    VBA IncentiveFee.cls equivalent with complete functional parity
    
    Implements manager incentive fee calculations based on IRR hurdle rates
    and subordinated noteholder payment performance.
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        
        # VBA private variables - exact mapping
        self.cls_fee_hurdle_rate: float = 0.0              # clsFeeHurdleRate
        self.cls_incent_fee: float = 0.0                   # clsIncentFee
        self.cls_threshold_reach: bool = False             # clsThresholdReach
        self.cls_sub_payments_dict: Dict[date, float] = {} # clsSubPaymentsDict
        self.cls_closing_date: Optional[date] = None       # clsClosingDate
        self.cls_current_threshold: float = 0.0            # clsCurrentThreshold
        self.cls_curr_incetive_payments: float = 0.0       # clsCurrIncetivePayments (preserving VBA typo)
        self.cls_curr_sub_payments: float = 0.0            # clsCurrSubPayments
        self.cls_curr_date: Optional[date] = None          # clsCurrDate
        self.cls_period: int = 0                           # clsPeriod
        self.cls_cum_dicounted_sub_payments: float = 0.0   # clsCumDicountedSubPayments (preserving VBA typo)
        
        # VBA arrays
        self.cls_threshold: List[float] = []               # clsThreshold()
        self.cls_irr: List[float] = []                     # clsIRR()
        self.cls_fee_paid: List[float] = []                # clsFeePaid()
        
        # Additional tracking for database persistence
        self.fee_structure_id: Optional[int] = None
        self._is_setup: bool = False
        self._is_deal_setup: bool = False
    
    def setup(
        self,
        i_fee_threshold: float,
        i_incentive_fee: float,
        i_payto_sub_notholder: Dict[date, float]
    ) -> None:
        """
        VBA Setup() method equivalent
        
        Public Sub Setup(iFeeThreshold As Double, iIncentiveFee As Double, iPaytoSubNotholder As Dictionary)
        """
        # VBA: clsFeeHurdleRate = iFeeThreshold
        self.cls_fee_hurdle_rate = i_fee_threshold
        
        # VBA: clsIncentFee = iIncentiveFee
        self.cls_incent_fee = i_incentive_fee
        
        # VBA: Set clsSubPaymentsDict = iPaytoSubNotholder
        self.cls_sub_payments_dict = i_payto_sub_notholder.copy()
        
        self._is_setup = True
    
    def deal_setup(
        self,
        i_num_of_payments: int,
        i_close_date: date,
        i_analysis_date: date
    ) -> None:
        """
        VBA DealSetup() method equivalent
        
        Public Sub DealSetup(iNumofPayments As Long, iCloseDate As Date, ianalysisDate As Date)
        """
        if not self._is_setup:
            raise RuntimeError("Must call setup() before deal_setup()")
        
        # VBA: ReDim clsThreshold(iNumofPayments)
        # VBA: ReDim clsIRR(iNumofPayments)  
        # VBA: ReDim clsFeePaid(iNumofPayments)
        self.cls_threshold = [0.0] * (i_num_of_payments + 1)  # +1 for 1-based indexing like VBA
        self.cls_irr = [0.0] * (i_num_of_payments + 1)
        self.cls_fee_paid = [0.0] * (i_num_of_payments + 1)
        
        # VBA: clsPeriod = 1
        self.cls_period = 1
        
        # VBA: clsClosingDate = iCloseDate
        self.cls_closing_date = i_close_date
        
        # VBA: Remove future payments beyond analysis date
        # For Each lDate In clsSubPaymentsDict.Keys
        #     If CDate(lDate) > ianalysisDate Then
        #         clsSubPaymentsDict.Remove lDate
        #     End If
        # Next
        dates_to_remove = [d for d in self.cls_sub_payments_dict.keys() if d > i_analysis_date]
        for date_key in dates_to_remove:
            del self.cls_sub_payments_dict[date_key]
        
        # VBA: Calculate cumulative discounted subordinated payments
        # For Each lDate In clsSubPaymentsDict.Keys
        #     clsCumDicountedSubPayments = clsCumDicountedSubPayments + (clsSubPaymentsDict(lDate) / ((1 + clsFeeHurdleRate) ^ ((lDate - clsClosingDate) / 365)))
        #     If clsCumDicountedSubPayments > 0 Then
        #        clsThresholdReach = True
        #        Exit For
        #     End If
        # Next
        self.cls_cum_dicounted_sub_payments = 0.0
        
        for l_date, payment in self.cls_sub_payments_dict.items():
            days_diff = (l_date - self.cls_closing_date).days
            discount_factor = (1 + self.cls_fee_hurdle_rate) ** (days_diff / 365.0)
            discounted_payment = payment / discount_factor
            
            self.cls_cum_dicounted_sub_payments += discounted_payment
            
            # VBA threshold logic
            if self.cls_cum_dicounted_sub_payments > 0:
                self.cls_threshold_reach = True
                break
        
        self._is_deal_setup = True
    
    def calc(self, i_next_pay: date) -> None:
        """
        VBA Calc() method equivalent
        
        Public Sub Calc(iNextPay As Date)
        """
        if not self._is_deal_setup:
            raise RuntimeError("Must call deal_setup() before calc()")
        
        # VBA: clsCurrDate = iNextPay
        self.cls_curr_date = i_next_pay
        
        # VBA threshold calculation logic
        # If clsThresholdReach Then
        #     clsCurrentThreshold = 0
        # Else
        #     clsCurrentThreshold = clsCumDicountedSubPayments * (1 + clsFeeHurdleRate) ^ ((iNextPay - clsClosingDate) / 365)
        #     clsCurrentThreshold = -1 * clsCurrentThreshold
        # End If
        if self.cls_threshold_reach:
            self.cls_current_threshold = 0.0
        else:
            days_diff = (i_next_pay - self.cls_closing_date).days
            growth_factor = (1 + self.cls_fee_hurdle_rate) ** (days_diff / 365.0)
            self.cls_current_threshold = self.cls_cum_dicounted_sub_payments * growth_factor
            self.cls_current_threshold = -1 * self.cls_current_threshold
        
        # VBA: clsThreshold(clsPeriod) = clsCurrentThreshold
        if self.cls_period < len(self.cls_threshold):
            self.cls_threshold[self.cls_period] = self.cls_current_threshold
    
    def incentive_fee_threshold(self) -> float:
        """
        VBA IncentiveFeeThreshold() function equivalent
        
        Public Function IncentiveFeeThreshold() As Double
        """
        # VBA: If clsThresholdReach Then
        #          IncentiveFeeThreshold = 0
        #      Else
        #          IncentiveFeeThreshold = clsThreshold(clsPeriod) - clsCurrSubPayments
        #      End If
        if self.cls_threshold_reach:
            return 0.0
        else:
            if self.cls_period < len(self.cls_threshold):
                return self.cls_threshold[self.cls_period] - self.cls_curr_sub_payments
            return 0.0
    
    def payment_to_sub_notholder(self, i_amount: float) -> None:
        """
        VBA PaymentToSubNotholder() method equivalent
        
        Public Sub PaymentToSubNotholder(iAmount As Double)
        """
        # VBA: clsCurrSubPayments = clsCurrSubPayments + iAmount
        self.cls_curr_sub_payments += i_amount
        
        # VBA: If clsCurrSubPayments >= clsCurrentThreshold Then clsThresholdReach = True
        if self.cls_curr_sub_payments >= self.cls_current_threshold:
            self.cls_threshold_reach = True
    
    def pay_incentive_fee(self, i_amount: float) -> float:
        """
        VBA PayIncentiveFee() method equivalent
        
        Public Sub PayIncentiveFee(iAmount As Double)
        
        Returns the net amount after fee deduction (modified i_amount)
        """
        # VBA: If clsThresholdReach Then
        #          clsCurrIncetivePayments = clsCurrIncetivePayments + iAmount * clsIncentFee
        #          iAmount = iAmount * (1 - clsIncentFee)
        #      End If
        if self.cls_threshold_reach:
            fee_amount = i_amount * self.cls_incent_fee
            self.cls_curr_incetive_payments += fee_amount
            return i_amount * (1 - self.cls_incent_fee)
        else:
            return i_amount
    
    def rollfoward(self) -> None:
        """
        VBA Rollfoward() method equivalent (preserving VBA typo in method name)
        
        Public Sub Rollfoward()
        """
        if not self.cls_curr_date:
            raise RuntimeError("Must call calc() before rollfoward()")
        
        # VBA: clsThreshold(clsPeriod) = clsCurrentThreshold
        if self.cls_period < len(self.cls_threshold):
            self.cls_threshold[self.cls_period] = self.cls_current_threshold
        
        # VBA: clsFeePaid(clsPeriod) = clsCurrIncetivePayments
        if self.cls_period < len(self.cls_fee_paid):
            self.cls_fee_paid[self.cls_period] = self.cls_curr_incetive_payments
        
        # VBA: clsCumDicountedSubPayments = clsCumDicountedSubPayments + (clsCurrSubPayments / ((1 + clsFeeHurdleRate) ^ ((clsCurrDate - clsClosingDate) / 365)))
        days_diff = (self.cls_curr_date - self.cls_closing_date).days
        discount_factor = (1 + self.cls_fee_hurdle_rate) ** (days_diff / 365.0)
        discounted_current_payment = self.cls_curr_sub_payments / discount_factor
        self.cls_cum_dicounted_sub_payments += discounted_current_payment
        
        # VBA: clsSubPaymentsDict.Add clsCurrDate, clsCurrSubPayments
        self.cls_sub_payments_dict[self.cls_curr_date] = self.cls_curr_sub_payments
        
        # VBA XIRR calculation
        # lDates = clsSubPaymentsDict.Keys
        # lValues = clsSubPaymentsDict.Items
        # For i = LBound(lDates) To UBound(lDates)
        #     lDates(i) = CDate(lDates(i))
        # Next i
        # lValue = Application.Xirr(lValues, lDates)
        # If VarType(lValue) = vbDouble Then
        #     clsIRR(clsPeriod) = CDbl(lValue)
        # End If
        l_dates = list(self.cls_sub_payments_dict.keys())
        l_values = list(self.cls_sub_payments_dict.values())
        
        try:
            irr_value = self._calculate_xirr(l_values, l_dates)
            if irr_value is not None and self.cls_period < len(self.cls_irr):
                self.cls_irr[self.cls_period] = irr_value
        except:
            # If XIRR calculation fails, leave as 0
            pass
        
        # VBA: clsPeriod = clsPeriod + 1
        self.cls_period += 1
        
        # VBA: clsCurrSubPayments = 0
        # VBA: clsCurrIncetivePayments = 0
        self.cls_curr_sub_payments = 0.0
        self.cls_curr_incetive_payments = 0.0
    
    def fee_paid(self) -> float:
        """
        VBA FeePaid() function equivalent
        
        Public Function FeePaid() As Double
        """
        # VBA: For i = LBound(clsFeePaid) To UBound(clsFeePaid)
        #          lTotal = lTotal + clsFeePaid(i)
        #      Next i
        #      FeePaid = lTotal
        total = 0.0
        for fee in self.cls_fee_paid:
            total += fee
        return total
    
    def output(self) -> List[List[Any]]:
        """
        VBA Output() function equivalent
        
        Public Function Output() As Variant
        """
        # VBA: ReDim lOutput(0 To clsPeriod - 1, 2)
        # VBA: lOutput(0, 0) = "Threshold"
        # VBA: lOutput(0, 1) = "Fee Paid" 
        # VBA: lOutput(0, 2) = "IRR"
        # VBA: For i = 1 To clsPeriod - 1
        #          lOutput(i, 0) = clsThreshold(i)
        #          lOutput(i, 1) = clsFeePaid(i)
        #          lOutput(i, 2) = Format(clsIRR(i), "0.000%")
        #      Next i
        l_output = []
        
        # Header row
        l_output.append(["Threshold", "Fee Paid", "IRR"])
        
        # Data rows
        for i in range(1, self.cls_period):
            if i < len(self.cls_threshold):
                threshold_val = self.cls_threshold[i]
                fee_paid_val = self.cls_fee_paid[i] if i < len(self.cls_fee_paid) else 0.0
                irr_val = f"{self.cls_irr[i]:.3%}" if i < len(self.cls_irr) else "0.000%"
                
                l_output.append([threshold_val, fee_paid_val, irr_val])
        
        return l_output
    
    def _calculate_xirr(self, cash_flows: List[float], dates: List[date], guess: float = 0.1) -> Optional[float]:
        """
        Excel XIRR function equivalent using Newton-Raphson method
        
        This implements the same XIRR calculation as Excel's Application.Xirr function
        """
        if len(cash_flows) != len(dates) or len(cash_flows) < 2:
            return None
        
        # Sort by dates
        sorted_pairs = sorted(zip(dates, cash_flows))
        dates = [pair[0] for pair in sorted_pairs]
        cash_flows = [pair[1] for pair in sorted_pairs]
        
        # Calculate days from first date
        base_date = dates[0]
        days = [(d - base_date).days for d in dates]
        
        # Newton-Raphson method for XIRR
        rate = guess
        max_iterations = 100
        tolerance = 1e-6
        
        for _ in range(max_iterations):
            # Calculate NPV and its derivative
            npv = 0.0
            dnpv = 0.0
            
            for i, (cf, day) in enumerate(zip(cash_flows, days)):
                if rate == -1:
                    return None  # Division by zero
                
                factor = (1 + rate) ** (day / 365.0)
                npv += cf / factor
                
                if day > 0:
                    dnpv -= cf * day / (365.0 * factor * (1 + rate))
            
            # Check convergence
            if abs(npv) < tolerance:
                return rate
            
            # Newton-Raphson update
            if abs(dnpv) < tolerance:
                break
            
            new_rate = rate - npv / dnpv
            
            # Bounds checking to prevent unreasonable rates
            if new_rate < -0.99:
                new_rate = -0.99
            elif new_rate > 10:
                new_rate = 10
            
            if abs(new_rate - rate) < tolerance:
                return new_rate
            
            rate = new_rate
        
        return None
    
    def save_to_database(self, deal_id: str, fee_structure_name: str) -> int:
        """Save incentive fee data to database"""
        if not self.session:
            raise RuntimeError("Database session required for persistence")
        
        # Create or update fee structure
        if not self.fee_structure_id:
            structure = self.session.query(IncentiveFeeStructure).filter_by(
                deal_id=deal_id,
                fee_structure_name=fee_structure_name
            ).first()
            
            if not structure:
                structure = IncentiveFeeStructure(
                    deal_id=deal_id,
                    fee_structure_name=fee_structure_name,
                    hurdle_rate=Decimal(str(self.cls_fee_hurdle_rate)),
                    incentive_fee_rate=Decimal(str(self.cls_incent_fee)),
                    closing_date=self.cls_closing_date,
                    is_active=True,
                    threshold_reached=self.cls_threshold_reach,
                    cum_discounted_sub_payments=Decimal(str(self.cls_cum_dicounted_sub_payments))
                )
                self.session.add(structure)
                self.session.flush()
            
            self.fee_structure_id = structure.fee_structure_id
        
        # Save subordinated payments
        for payment_date, amount in self.cls_sub_payments_dict.items():
            existing = self.session.query(SubordinatedPayment).filter_by(
                fee_structure_id=self.fee_structure_id,
                payment_date=payment_date
            ).first()
            
            if not existing:
                payment = SubordinatedPayment(
                    fee_structure_id=self.fee_structure_id,
                    payment_date=payment_date,
                    payment_amount=Decimal(str(amount))
                )
                self.session.add(payment)
        
        # Save period calculations
        for i in range(1, self.cls_period):
            if i < len(self.cls_threshold):
                existing = self.session.query(IncentiveFeeCalculation).filter_by(
                    fee_structure_id=self.fee_structure_id,
                    period_number=i
                ).first()
                
                if not existing:
                    calc = IncentiveFeeCalculation(
                        fee_structure_id=self.fee_structure_id,
                        period_number=i,
                        calculation_date=self.cls_curr_date or date.today(),
                        current_threshold=Decimal(str(self.cls_threshold[i])),
                        threshold_reached=self.cls_threshold_reach,
                        fee_paid_period=Decimal(str(self.cls_fee_paid[i] if i < len(self.cls_fee_paid) else 0)),
                        period_irr=Decimal(str(self.cls_irr[i])) if i < len(self.cls_irr) else None
                    )
                    self.session.add(calc)
        
        self.session.commit()
        return self.fee_structure_id
    
    @classmethod
    def load_from_database(cls, session: Session, fee_structure_id: int) -> 'IncentiveFee':
        """Load incentive fee from database"""
        structure = session.query(IncentiveFeeStructure).filter_by(
            fee_structure_id=fee_structure_id
        ).first()
        
        if not structure:
            raise ValueError(f"Fee structure {fee_structure_id} not found")
        
        # Create instance
        incentive_fee = cls(session)
        incentive_fee.fee_structure_id = fee_structure_id
        
        # Load basic parameters
        incentive_fee.cls_fee_hurdle_rate = float(structure.hurdle_rate)
        incentive_fee.cls_incent_fee = float(structure.incentive_fee_rate)
        incentive_fee.cls_closing_date = structure.closing_date
        incentive_fee.cls_threshold_reach = structure.threshold_reached
        incentive_fee.cls_cum_dicounted_sub_payments = float(structure.cum_discounted_sub_payments)
        
        # Load subordinated payments
        payments = session.query(SubordinatedPayment).filter_by(
            fee_structure_id=fee_structure_id
        ).order_by(SubordinatedPayment.payment_date).all()
        
        incentive_fee.cls_sub_payments_dict = {
            p.payment_date: float(p.payment_amount) for p in payments
        }
        
        # Load calculations
        calculations = session.query(IncentiveFeeCalculation).filter_by(
            fee_structure_id=fee_structure_id
        ).order_by(IncentiveFeeCalculation.period_number).all()
        
        if calculations:
            max_period = max(c.period_number for c in calculations) + 1
            incentive_fee.cls_threshold = [0.0] * (max_period + 1)
            incentive_fee.cls_irr = [0.0] * (max_period + 1)
            incentive_fee.cls_fee_paid = [0.0] * (max_period + 1)
            
            for calc in calculations:
                period = calc.period_number
                if period < len(incentive_fee.cls_threshold):
                    incentive_fee.cls_threshold[period] = float(calc.current_threshold)
                    incentive_fee.cls_fee_paid[period] = float(calc.fee_paid_period)
                    if calc.period_irr:
                        incentive_fee.cls_irr[period] = float(calc.period_irr)
            
            incentive_fee.cls_period = max_period
        
        incentive_fee._is_setup = True
        incentive_fee._is_deal_setup = True
        
        return incentive_fee