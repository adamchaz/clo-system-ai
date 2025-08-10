"""
CLO Asset Model - Python conversion of Asset.cls VBA class
Core business object representing individual financial assets in CLO portfolio
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any, Union, TYPE_CHECKING
from enum import Enum
import QuantLib as ql
from pydantic import BaseModel, validator
import calendar

if TYPE_CHECKING:
    from ..services.asset_service import AssetService

from ..core.database import Base
from ..core.config import QuantLibConfig


class RatingEnum(str, Enum):
    """Standard credit ratings for validation"""
    
    # Moody's Ratings
    AAA_MDY = "Aaa"
    AA1 = "Aa1"
    AA2 = "Aa2" 
    AA3 = "Aa3"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    BAA1 = "Baa1"
    BAA2 = "Baa2"
    BAA3 = "Baa3"
    BA1 = "Ba1"
    BA2 = "Ba2"
    BA3 = "Ba3"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    CAA1 = "Caa1"
    CAA2 = "Caa2"
    CAA3 = "Caa3"
    CA = "Ca"
    C = "C"
    
    # S&P Ratings
    AAA_SP = "AAA"
    AA_PLUS = "AA+"
    AA = "AA"
    AA_MINUS = "AA-"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB_PLUS = "BBB+"
    BBB = "BBB"
    BBB_MINUS = "BBB-"
    BB_PLUS = "BB+"
    BB = "BB"
    BB_MINUS = "BB-"
    B_PLUS = "B+"
    B_SP = "B"
    B_MINUS = "B-"
    CCC = "CCC"
    D = "D"


class CouponTypeEnum(str, Enum):
    """Interest rate type classification"""
    FIXED = "FIXED"
    FLOAT = "FLOAT"


class DayCountEnum(str, Enum):
    """Day count conventions for interest calculations"""
    THIRTY_360 = "30/360"
    ACTUAL_ACTUAL = "ACTUAL/ACTUAL"
    ACTUAL_365 = "ACTUAL/365"
    ACTUAL_360 = "ACTUAL/360"


class AssetFlags(BaseModel):
    """Asset classification flags - stored as JSON in database"""
    pik_asset: bool = False
    default_asset: bool = False
    delay_drawdown: bool = False
    revolver: bool = False
    loc: bool = False  # Letter of Credit
    participation: bool = False
    dip: bool = False  # Debtor-in-Possession
    convertible: bool = False
    struct_finance: bool = False
    bridge_loan: bool = False
    current_pay: bool = False
    cov_lite: bool = False
    fllo: bool = False  # First Lien Last Out


class Asset(Base):
    """
    CLO Asset Model - Individual financial asset in portfolio
    Converted from VBA Asset.cls (1,217 lines) to Python SQLAlchemy model
    """
    __tablename__ = 'assets'

    # Primary Identification
    blkrock_id = Column(String(50), primary_key=True, doc="BlackRock asset identifier")
    issue_name = Column(String(255), nullable=False, doc="Asset issue name")
    issuer_name = Column(String(255), nullable=False, doc="Issuer company name")
    issuer_id = Column(String(50), doc="Issuer identifier")
    tranche = Column(String(10), doc="Tranche designation")
    
    # Asset Classification
    bond_loan = Column(String(10), doc="BOND or LOAN classification")
    par_amount = Column(Numeric(18,2), nullable=False, doc="Principal amount outstanding")
    market_value = Column(Numeric(8,4), doc="Market value as percentage of par")
    currency = Column(String(3), default="USD", doc="Currency denomination")
    
    # Dates
    maturity = Column(Date, nullable=False, doc="Asset maturity date")
    dated_date = Column(Date, doc="Interest accrual start date") 
    issue_date = Column(Date, doc="Asset issue date")
    first_payment_date = Column(Date, doc="First interest payment date")
    date_of_default = Column(Date, doc="Default date if applicable")
    
    # Interest Rate Properties
    coupon = Column(Numeric(10,6), doc="Current coupon rate (decimal)")
    coupon_type = Column(String(10), doc="FIXED or FLOAT")
    index_name = Column(String(20), doc="Interest rate index (LIBOR, SOFR, etc.)")
    cpn_spread = Column(Numeric(10,6), doc="Spread over index (bp as decimal)")
    libor_floor = Column(Numeric(10,6), doc="Interest rate floor")
    index_cap = Column(Numeric(10,6), doc="Interest rate cap")
    payment_freq = Column(Integer, doc="Payments per year (1,2,4,12)")
    
    # Cash Flow Properties
    amortization_type = Column(String(20), doc="Amortization schedule type")
    day_count = Column(String(20), doc="Day count convention")
    business_day_conv = Column(String(30), doc="Business day convention")
    payment_eom = Column(Boolean, default=False, doc="End-of-month payment flag")
    amount_issued = Column(Numeric(18,2), doc="Original issue amount")
    
    # PIK (Payment-in-Kind) Properties  
    piking = Column(Boolean, default=False, doc="Currently PIKing flag")
    pik_amount = Column(Numeric(18,2), doc="Current PIK amount")
    unfunded_amount = Column(Numeric(18,2), doc="Unfunded commitment")
    
    # Credit Ratings
    mdy_rating = Column(String(10), doc="Moody's current rating")
    mdy_dp_rating = Column(String(10), doc="Moody's Deal Pricing rating")
    mdy_dp_rating_warf = Column(String(10), doc="Moody's WARF rating")
    mdy_recovery_rate = Column(Numeric(5,4), doc="Moody's recovery rate")
    sp_rating = Column(String(10), doc="S&P current rating")
    
    # Additional Ratings
    mdy_facility_rating = Column(String(10), doc="Moody's facility rating")
    mdy_facility_outlook = Column(String(10), doc="Moody's facility outlook")
    mdy_issuer_rating = Column(String(10), doc="Moody's issuer rating")
    mdy_issuer_outlook = Column(String(10), doc="Moody's issuer outlook")
    mdy_snr_sec_rating = Column(String(10), doc="Moody's senior secured rating")
    mdy_snr_unsec_rating = Column(String(10), doc="Moody's senior unsecured rating")
    mdy_sub_rating = Column(String(10), doc="Moody's subordinate rating")
    mdy_credit_est_rating = Column(String(10), doc="Moody's credit estimate rating")
    mdy_credit_est_date = Column(Date, doc="Moody's credit estimate date")
    
    sandp_facility_rating = Column(String(10), doc="S&P facility rating")
    sandp_issuer_rating = Column(String(10), doc="S&P issuer rating")
    sandp_snr_sec_rating = Column(String(10), doc="S&P senior secured rating")
    sandp_subordinate = Column(String(10), doc="S&P subordinate rating")
    sandp_rec_rating = Column(String(10), doc="S&P recovery rating")
    
    # Industry Classifications
    mdy_industry = Column(String(100), doc="Moody's industry classification")
    sp_industry = Column(String(100), doc="S&P industry classification")
    country = Column(String(50), doc="Country of domicile")
    seniority = Column(String(20), doc="Seniority level")
    mdy_asset_category = Column(String(50), doc="Moody's asset category")
    sp_priority_category = Column(String(50), doc="S&P priority category")
    
    # Financial Properties
    commit_fee = Column(Numeric(10,6), doc="Commitment fee rate")
    facility_size = Column(Numeric(18,2), doc="Total facility size")
    wal = Column(Numeric(8,4), doc="Weighted Average Life")
    
    # Asset Flags (stored as JSON)
    flags = Column(JSON, doc="Asset classification flags")
    
    # Analyst Information
    analyst_opinion = Column(Text, doc="Analyst opinion/notes")
    
    # Audit Fields
    created_at = Column(DateTime, default=func.now(), doc="Record creation timestamp")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), doc="Record update timestamp")
    
    def __init__(self, **kwargs):
        """Initialize Asset with validation"""
        super().__init__(**kwargs)
        
        # Initialize flags if not provided
        if self.flags is None:
            self.flags = AssetFlags().dict()
    
    def __repr__(self):
        return f"<Asset({self.blkrock_id}: {self.issuer_name} - ${self.par_amount:,.0f})>"
    
    @property
    def is_defaulted(self) -> bool:
        """Check if asset is currently in default"""
        return (self.flags.get('default_asset', False) or 
                self.mdy_rating == 'D' or 
                self.sp_rating == 'D' or
                self.date_of_default is not None)
    
    @property
    def is_pik_asset(self) -> bool:
        """Check if asset is PIK-eligible"""
        return self.flags.get('pik_asset', False) or self.piking
    
    @property
    def effective_coupon(self) -> Decimal:
        """Calculate effective coupon including spread"""
        if self.coupon_type == CouponTypeEnum.FIXED:
            return self.coupon or Decimal('0')
        else:
            # For floating rate, would need current index rate
            return (self.coupon or Decimal('0')) + (self.cpn_spread or Decimal('0'))
    
    def get_day_count_convention(self) -> ql.DayCounter:
        """Get QuantLib day count convention for calculations"""
        return QuantLibConfig.get_day_count(self.day_count)
    
    def calculate_interest_accrual(self, 
                                 start_date: date, 
                                 end_date: date, 
                                 balance: Decimal,
                                 coupon_rate: Optional[Decimal] = None) -> Decimal:
        """
        Calculate interest accrual between dates using QuantLib
        Replaces VBA DateFraction calculation
        """
        if coupon_rate is None:
            coupon_rate = self.effective_coupon
            
        # Convert Python dates to QuantLib dates
        ql_start = ql.Date(start_date.day, start_date.month, start_date.year)
        ql_end = ql.Date(end_date.day, end_date.month, end_date.year)
        
        # Get day count convention
        day_counter = self.get_day_count_convention()
        
        # Calculate year fraction
        year_fraction = day_counter.yearFraction(ql_start, ql_end)
        
        # Return interest amount
        return Decimal(str(year_fraction)) * coupon_rate * balance
    
    def calculate_cash_flows(self,
                           analysis_date: date,
                           maturity_date: Optional[date] = None,
                           prepay_rate: Optional[List[Decimal]] = None,
                           default_rate: Optional[List[Decimal]] = None,
                           severity_rate: Optional[List[Decimal]] = None,
                           recovery_lag: int = 6) -> Dict[str, List]:
        """
        Convert VBA CalcCF() method - generates asset cash flows
        Returns structured cash flow data with payment dates, balances, interest, principal, defaults
        """
        if maturity_date is None:
            maturity_date = self.maturity
            
        # Initialize payment schedule based on payment frequency
        payment_dates = self._generate_payment_dates(analysis_date, maturity_date)
        num_periods = len(payment_dates)
        
        # Initialize cash flow arrays
        cash_flows = {
            'payment_dates': payment_dates,
            'accrual_start_dates': [],
            'accrual_end_dates': [],
            'beginning_balances': [],
            'interest_payments': [],
            'scheduled_principal': [],
            'unscheduled_principal': [],
            'defaults': [],
            'recoveries': [],
            'net_losses': [],
            'ending_balances': [],
            'total_cash_flows': []
        }
        
        # Initialize starting values
        current_balance = self.par_amount or Decimal('0')
        default_balance = Decimal('0')
        
        for i in range(num_periods):
            period_start = analysis_date if i == 0 else payment_dates[i-1]
            period_end = payment_dates[i]
            
            # Set accrual period dates
            cash_flows['accrual_start_dates'].append(period_start)
            cash_flows['accrual_end_dates'].append(period_end)
            cash_flows['beginning_balances'].append(float(current_balance))
            
            # Calculate defaults for period
            default_rate_period = default_rate[i] if default_rate and i < len(default_rate) else Decimal('0')
            period_default = current_balance * default_rate_period
            cash_flows['defaults'].append(float(period_default))
            
            # Update balances after defaults
            current_balance -= period_default
            default_balance += period_default
            
            # Calculate interest on remaining balance
            if current_balance > 0 and not self.is_defaulted:
                interest_payment = self.calculate_interest_accrual(
                    period_start, period_end, current_balance
                )
                
                # Handle PIK interest
                if self.is_pik_asset and self.piking:
                    # PIK interest adds to principal balance
                    current_balance += interest_payment
                    interest_payment = Decimal('0')
                    
                cash_flows['interest_payments'].append(float(interest_payment))
            else:
                cash_flows['interest_payments'].append(0.0)
            
            # Calculate principal payments
            scheduled_principal = Decimal('0')
            unscheduled_principal = Decimal('0')
            
            if current_balance > 0:
                # Scheduled amortization (simplified - could be enhanced)
                if self.amortization_type and self.amortization_type != 'BULLET':
                    scheduled_principal = current_balance / Decimal(str(num_periods - i))
                
                # Unscheduled prepayments
                prepay_rate_period = prepay_rate[i] if prepay_rate and i < len(prepay_rate) else Decimal('0')
                unscheduled_principal = (current_balance - scheduled_principal) * prepay_rate_period
                
                # Final maturity payment
                if i == num_periods - 1:
                    scheduled_principal = current_balance - unscheduled_principal
            
            cash_flows['scheduled_principal'].append(float(scheduled_principal))
            cash_flows['unscheduled_principal'].append(float(unscheduled_principal))
            
            # Update balance after principal payments
            current_balance -= (scheduled_principal + unscheduled_principal)
            
            # Calculate recoveries (with lag)
            recoveries = Decimal('0')
            if default_balance > 0 and i >= recovery_lag:
                recovery_rate = (Decimal('1') - (severity_rate[i-recovery_lag] if severity_rate and i-recovery_lag < len(severity_rate) else Decimal('0.5')))
                recoveries = default_balance * recovery_rate
                default_balance -= recoveries
            
            cash_flows['recoveries'].append(float(recoveries))
            
            # Net losses (defaults not recovered)
            net_loss = Decimal('0')
            if i == num_periods - 1 and default_balance > 0:
                net_loss = default_balance
                default_balance = Decimal('0')
            
            cash_flows['net_losses'].append(float(net_loss))
            cash_flows['ending_balances'].append(float(current_balance))
            
            # Total cash flow for period
            total_cf = (cash_flows['interest_payments'][i] + 
                       cash_flows['scheduled_principal'][i] + 
                       cash_flows['unscheduled_principal'][i] + 
                       cash_flows['recoveries'][i])
            cash_flows['total_cash_flows'].append(total_cf)
        
        return cash_flows
    
    def _generate_payment_dates(self, start_date: date, end_date: date) -> List[date]:
        """
        Generate payment dates based on payment frequency
        """
        dates = []
        current_date = self.first_payment_date or start_date
        
        # Determine months between payments
        freq_map = {
            12: 1,  # Monthly
            4: 3,   # Quarterly  
            2: 6,   # Semi-annually
            1: 12   # Annually
        }
        
        months_between = freq_map.get(self.payment_freq or 4, 3)  # Default quarterly
        
        while current_date <= end_date:
            dates.append(current_date)
            # Add months to current date
            year = current_date.year
            month = current_date.month + months_between
            day = current_date.day
            
            # Handle month overflow
            while month > 12:
                month -= 12
                year += 1
                
            # Handle end-of-month dates
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            if day > max_day:
                day = max_day
                
            current_date = date(year, month, day)
            
        return dates
    
    def validate_ratings(self):
        """Validate credit ratings against standard scales"""
        if self.mdy_rating and self.mdy_rating not in [r.value for r in RatingEnum if 'mdy' in r.name.lower() or r.value in ['Aaa', 'Aa1', 'Aa2', 'Aa3', 'A1', 'A2', 'A3', 'Baa1', 'Baa2', 'Baa3', 'Ba1', 'Ba2', 'Ba3', 'B1', 'B2', 'B3', 'Caa1', 'Caa2', 'Caa3', 'Ca', 'C']]:
            raise ValueError(f"Invalid Moody's rating: {self.mdy_rating}")
            
        if self.sp_rating and self.sp_rating not in [r.value for r in RatingEnum if 'sp' in r.name.lower() or r.value in ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC', 'D']]:
            raise ValueError(f"Invalid S&P rating: {self.sp_rating}")
    
    def validate_financial_data(self):
        """Validate financial properties"""
        if self.par_amount is not None and self.par_amount < 0:
            raise ValueError("Par amount cannot be negative")
            
        if self.first_payment_date and self.dated_date:
            if self.first_payment_date <= self.dated_date:
                raise ValueError("First payment date must be after dated date")
                
        if self.coupon is not None and (self.coupon < 0 or self.coupon > 1):
            raise ValueError("Coupon rate must be between 0 and 1 (as decimal)")
    
    def apply_filter(self, filter_expression: str) -> bool:
        """
        Convert VBA ApplyFilter() method - evaluates complex filter expressions
        Supports comparison operators (=, !=, <, >, <=, >=) and logical operators (AND, OR)
        with parentheses for grouping
        """
        if not filter_expression:
            return True
            
        # Handle parentheses recursively
        while '(' in filter_expression:
            # Find innermost parentheses
            left_paren = filter_expression.rfind('(')
            right_paren = filter_expression.find(')', left_paren)
            
            if right_paren == -1:
                raise ValueError("Mismatched parentheses in filter expression")
                
            # Extract and evaluate sub-expression
            sub_expr = filter_expression[left_paren + 1:right_paren]
            result = self.apply_filter(sub_expr)
            
            # Replace parentheses expression with result
            filter_expression = (filter_expression[:left_paren] + 
                               str(result).upper() + 
                               filter_expression[right_paren + 1:])
        
        # Find logical operators (AND, OR)
        logical_ops = self._find_logical_operators(filter_expression)
        
        if not logical_ops:
            # No logical operators - evaluate single comparison
            if filter_expression.upper() == 'TRUE':
                return True
            elif filter_expression.upper() == 'FALSE':
                return False
            else:
                return self._evaluate_comparison(filter_expression)
        
        # Process logical operators left to right
        result = None
        current_pos = 0
        
        for op_pos, operator in logical_ops:
            # Get left operand
            if result is None:
                left_expr = filter_expression[current_pos:op_pos].strip()
                result = self.apply_filter(left_expr)
            
            # Get right operand (to next operator or end)
            next_pos = logical_ops[logical_ops.index((op_pos, operator)) + 1][0] if logical_ops.index((op_pos, operator)) + 1 < len(logical_ops) else len(filter_expression)
            right_expr = filter_expression[op_pos + len(operator):next_pos].strip()
            right_result = self.apply_filter(right_expr)
            
            # Apply logical operation
            if operator.upper() == 'AND':
                result = result and right_result
            elif operator.upper() == 'OR':
                result = result or right_result
                
            current_pos = next_pos
        
        return result
    
    def _find_logical_operators(self, expression: str) -> List[tuple]:
        """Find all logical operators (AND, OR) in expression"""
        operators = []
        words = expression.split()
        pos = 0
        
        for word in words:
            if word.upper() in ('AND', 'OR'):
                operators.append((pos, word.upper()))
            pos += len(word) + 1  # +1 for space
            
        return operators
    
    def _evaluate_comparison(self, expression: str) -> bool:
        """Evaluate single comparison expression (field operator value)"""
        # Find comparison operator
        operators = ['<=', '>=', '!=', '<', '>', '=']
        operator = None
        op_pos = -1
        
        for op in operators:
            pos = expression.find(op)
            if pos != -1:
                operator = op
                op_pos = pos
                break
        
        if operator is None:
            raise ValueError(f"No comparison operator found in: {expression}")
        
        # Extract field and value
        field = expression[:op_pos].strip()
        value_str = expression[op_pos + len(operator):].strip()
        
        # Get field value from asset
        field_value = self._get_field_value(field)
        
        # Convert comparison value to appropriate type
        comparison_value = self._convert_value(value_str, type(field_value))
        
        # Perform comparison
        if operator == '=':
            return field_value == comparison_value
        elif operator == '!=':
            return field_value != comparison_value
        elif operator == '<':
            return field_value < comparison_value
        elif operator == '>':
            return field_value > comparison_value
        elif operator == '<=':
            return field_value <= comparison_value
        elif operator == '>=':
            return field_value >= comparison_value
        
        return False
    
    def _get_field_value(self, field_name: str):
        """Get asset field value by name (case-insensitive)"""
        field_map = {
            "MOODY'S INDUSTRY": (self.mdy_industry or "").upper(),
            "S&P INDUSTRY": (self.sp_industry or "").upper(),
            "MOODY'S RATING": self.mdy_rating,
            "MOODY'S RATING WARF": self.mdy_dp_rating_warf,
            "MOODY'S RATING DPR": self.mdy_dp_rating,
            "S&P RATING": self.sp_rating,
            "WAL": float(self.wal) if self.wal else 0.0,
            "COV-LITE": self.flags.get('cov_lite', False) if self.flags else False,
            "COUNTRY": (self.country or "").upper(),
            "FACILITY SIZE": float(self.facility_size) if self.facility_size else 0.0,
            "MARKET VALUE": float(self.market_value) if self.market_value else 0.0,
            "ANALYST OPINION": (self.analyst_opinion or "").upper()
        }
        
        field_upper = field_name.upper()
        if field_upper in field_map:
            return field_map[field_upper]
        
        raise ValueError(f"Unknown field: {field_name}")
    
    def _convert_value(self, value_str: str, target_type):
        """Convert string value to target type"""
        if target_type == bool:
            return value_str.upper() in ('TRUE', '1', 'YES')
        elif target_type in (int, float):
            return float(value_str)
        else:
            return value_str.upper()  # String comparison (case-insensitive)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary for API responses"""
        return {
            'blkrock_id': self.blkrock_id,
            'issue_name': self.issue_name,
            'issuer_name': self.issuer_name,
            'par_amount': float(self.par_amount) if self.par_amount else None,
            'coupon': float(self.coupon) if self.coupon else None,
            'maturity': self.maturity.isoformat() if self.maturity else None,
            'mdy_rating': self.mdy_rating,
            'sp_rating': self.sp_rating,
            'is_defaulted': self.is_defaulted,
            'is_pik_asset': self.is_pik_asset,
            'effective_coupon': float(self.effective_coupon)
        }


    def add_rating_history(self, rating_date: date, rating: str, agency: str = 'moody'):
        """Add historical rating data (converted from VBA AddMoodyRating/AddSPRating)"""
        if agency.lower() == 'moody':
            # Store in asset history table
            history_record = AssetHistory(
                blkrock_id=self.blkrock_id,
                history_date=rating_date,
                property_name='mdy_rating',
                property_value=rating
            )
        elif agency.lower() == 'sp':
            history_record = AssetHistory(
                blkrock_id=self.blkrock_id,
                history_date=rating_date,
                property_name='sp_rating', 
                property_value=rating
            )
        else:
            raise ValueError("Agency must be 'moody' or 'sp'")
        
        # Would need session to add to database
        # This is typically handled at the service layer
        return history_record
    
    def get_rating_at_date(self, target_date: date, agency: str = 'moody') -> str:
        """Get asset rating at specific date (converted from VBA GetMoodyRating/GetSPRating)"""
        # This would typically query the database for historical ratings
        # For now, return current rating as fallback
        if agency.lower() == 'moody':
            return self.mdy_rating or ""
        elif agency.lower() == 'sp':
            return self.sp_rating or ""
        else:
            raise ValueError("Agency must be 'moody' or 'sp'")


class AssetHistory(Base):
    """Historical data for asset properties (ratings, prices, etc.)"""
    __tablename__ = 'asset_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    blkrock_id = Column(String(50), nullable=False, doc="Asset identifier")
    history_date = Column(Date, nullable=False, doc="Historical date")
    property_name = Column(String(50), nullable=False, doc="Property name (mdy_rating, sp_rating, market_value, etc.)")
    property_value = Column(String(100), doc="Historical property value")
    
    # Audit fields
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<AssetHistory({self.blkrock_id}: {self.property_name}={self.property_value} on {self.history_date})>"


# Pydantic models for API validation
class AssetCreate(BaseModel):
    """Pydantic model for creating new assets"""
    blkrock_id: str
    issue_name: str
    issuer_name: str
    par_amount: Decimal
    coupon: Optional[Decimal] = None
    maturity: date
    mdy_rating: Optional[str] = None
    sp_rating: Optional[str] = None
    
    @validator('par_amount')
    def validate_par_amount(cls, v):
        if v < 0:
            raise ValueError('Par amount must be positive')
        return v
    
    @validator('coupon')
    def validate_coupon(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Coupon must be between 0 and 1')
        return v


class AssetUpdate(BaseModel):
    """Pydantic model for updating existing assets"""
    issue_name: Optional[str] = None
    par_amount: Optional[Decimal] = None
    coupon: Optional[Decimal] = None
    mdy_rating: Optional[str] = None
    sp_rating: Optional[str] = None
    
    @validator('par_amount')
    def validate_par_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Par amount must be positive')
        return v


class AssetResponse(BaseModel):
    """Pydantic model for API responses"""
    blkrock_id: str
    issue_name: str
    issuer_name: str
    par_amount: Decimal
    coupon: Optional[Decimal]
    maturity: date
    mdy_rating: Optional[str]
    sp_rating: Optional[str]
    is_defaulted: bool
    effective_coupon: Decimal
    
    class Config:
        from_attributes = True