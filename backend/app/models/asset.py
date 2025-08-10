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
    
    # Credit Ratings (Enhanced with rating system integration)
    mdy_rating = Column(String(10), doc="Moody's current rating")
    mdy_dp_rating = Column(String(10), doc="Moody's Deal Pricing rating")
    mdy_dp_rating_warf = Column(String(10), doc="Moody's WARF rating")
    mdy_recovery_rate = Column(Numeric(5,4), doc="Moody's recovery rate")
    sp_rating = Column(String(10), doc="S&P current rating")
    
    # Derived Ratings (calculated by RatingDerivationEngine)
    derived_mdy_rating = Column(String(10), doc="Derived Moody's rating from cross-agency")
    derived_sp_rating = Column(String(10), doc="Derived S&P rating from cross-agency")
    rating_derivation_date = Column(Date, doc="Date when ratings were last derived")
    rating_source_hierarchy = Column(Text, doc="JSON of rating source priority used")
    
    # Yield Curve and Pricing Integration
    discount_curve_id = Column(Integer, doc="Yield curve ID for discounting")
    discount_curve_name = Column(String(100), doc="Yield curve name for pricing")
    fair_value = Column(Numeric(18,2), doc="Fair value calculated using yield curve")
    fair_value_date = Column(Date, doc="Date when fair value was calculated")
    pricing_spread_bps = Column(Integer, doc="Credit spread over base curve (basis points)")
    
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
    
    # Rating System Integration Methods
    def update_derived_ratings(self, rating_service=None):
        """
        Update derived ratings using RatingDerivationEngine
        Integrates with the VBA RatingDerivations.cls functionality
        """
        if not rating_service:
            from ..models.rating_system import RatingService
            from sqlalchemy.orm import Session
            from ..core.database import get_db
            session = next(get_db())
            rating_service = RatingService(session)
        
        try:
            # Calculate all derived ratings
            results = rating_service.update_asset_ratings(self)
            
            # Update the asset with derived ratings
            self.derived_mdy_rating = results.get('mdy_rating')
            self.derived_sp_rating = results.get('sp_rating')
            self.mdy_dp_rating = results.get('mdy_dp_rating')
            self.mdy_dp_rating_warf = results.get('mdy_dp_rating_warf')
            self.mdy_recovery_rate = results.get('mdy_recovery_rate')
            self.rating_derivation_date = date.today()
            
            # Store rating source hierarchy for audit trail
            import json
            hierarchy = self._get_rating_source_hierarchy()
            self.rating_source_hierarchy = json.dumps(hierarchy)
            
            return results
            
        except Exception as e:
            # Log error but don't fail the update
            print(f"Warning: Failed to update derived ratings for {self.blkrock_id}: {e}")
            return {}
    
    def _get_rating_source_hierarchy(self) -> Dict[str, str]:
        """Get the rating source hierarchy used for derivation"""
        hierarchy = {}
        
        # Moody's hierarchy
        if self.mdy_facility_rating and self.mdy_facility_rating != "NR":
            hierarchy['mdy_primary'] = 'facility'
        elif self.mdy_issuer_rating and self.mdy_issuer_rating != "NR":
            hierarchy['mdy_primary'] = 'issuer'
        elif self.mdy_snr_unsec_rating and self.mdy_snr_unsec_rating != "NR":
            hierarchy['mdy_primary'] = 'snr_unsec'
        elif self.mdy_snr_sec_rating and self.mdy_snr_sec_rating != "NR":
            hierarchy['mdy_primary'] = 'snr_sec'
        else:
            hierarchy['mdy_primary'] = 'derived_from_sp'
        
        # S&P hierarchy
        if self.sp_issuer_rating and self.sp_issuer_rating != "NR":
            hierarchy['sp_primary'] = 'issuer'
        elif self.sp_snr_sec_rating and self.sp_snr_sec_rating != "NR":
            hierarchy['sp_primary'] = 'snr_sec'
        elif self.sp_subordinate and self.sp_subordinate != "NR":
            hierarchy['sp_primary'] = 'subordinate'
        else:
            hierarchy['sp_primary'] = 'derived_from_mdy'
        
        return hierarchy
    
    def get_effective_mdy_rating(self) -> str:
        """Get the most appropriate Moody's rating for calculations"""
        # Priority: derived > current > facility > issuer > default
        if self.derived_mdy_rating:
            return self.derived_mdy_rating
        elif self.mdy_rating and self.mdy_rating != "NR":
            return self.mdy_rating
        elif self.mdy_facility_rating and self.mdy_facility_rating != "NR":
            return self.mdy_facility_rating
        elif self.mdy_issuer_rating and self.mdy_issuer_rating != "NR":
            return self.mdy_issuer_rating
        else:
            return "Caa3"  # Default rating
    
    def get_effective_sp_rating(self) -> str:
        """Get the most appropriate S&P rating for calculations"""
        # Priority: derived > current > issuer > facility > default
        if self.derived_sp_rating:
            return self.derived_sp_rating
        elif self.sp_rating and self.sp_rating != "NR":
            return self.sp_rating
        elif self.sp_issuer_rating and self.sp_issuer_rating != "NR":
            return self.sp_issuer_rating
        elif self.sp_facility_rating and self.sp_facility_rating != "NR":
            return self.sp_facility_rating
        else:
            return "CCC-"  # Default rating
    
    def get_effective_recovery_rate(self) -> Decimal:
        """Get the most appropriate recovery rate"""
        if self.mdy_recovery_rate:
            return Decimal(str(self.mdy_recovery_rate))
        else:
            # Default recovery rate based on asset category
            if self.flags.get('dip', False):
                return Decimal('0.5000')  # DIP assets
            elif self.seniority == "SENIOR SECURED":
                return Decimal('0.4500')  # Senior secured default
            else:
                return Decimal('0.3000')  # Other assets default
    
    def track_rating_migration(self, new_ratings: Dict[str, str], rating_service=None):
        """
        Track rating migration and create migration record
        Integrates with RatingMigrationItem functionality
        """
        if not rating_service:
            from ..models.rating_system import RatingService
            from sqlalchemy.orm import Session
            from ..core.database import get_db
            session = next(get_db())
            rating_service = RatingService(session)
        
        # Get previous ratings
        previous_ratings = {
            'sp': self.get_effective_sp_rating(),
            'mdy': self.get_effective_mdy_rating(),
            'fitch': self.fitch_rating or ""
        }
        
        # Create migration record
        migration = rating_service.create_rating_migration(
            asset_id=self.blkrock_id,
            migration_date=date.today(),
            previous_ratings=previous_ratings,
            new_ratings=new_ratings,
            par_amount=self.par_amount or Decimal('0'),
            portfolio_weight=Decimal('0.01')  # Would be calculated from portfolio context
        )
        
        return migration
    
    def get_rating_analytics(self) -> Dict[str, Any]:
        """Get comprehensive rating analytics for the asset"""
        return {
            'asset_id': self.blkrock_id,
            'issuer': self.issuer_name,
            'current_ratings': {
                'mdy_rating': self.mdy_rating,
                'sp_rating': self.sp_rating,
                'fitch_rating': getattr(self, 'fitch_rating', None)
            },
            'derived_ratings': {
                'derived_mdy': self.derived_mdy_rating,
                'derived_sp': self.derived_sp_rating,
                'mdy_dp': self.mdy_dp_rating,
                'mdy_dp_warf': self.mdy_dp_rating_warf
            },
            'effective_ratings': {
                'effective_mdy': self.get_effective_mdy_rating(),
                'effective_sp': self.get_effective_sp_rating()
            },
            'recovery_rate': float(self.get_effective_recovery_rate()),
            'derivation_info': {
                'derivation_date': self.rating_derivation_date,
                'source_hierarchy': self.rating_source_hierarchy
            },
            'asset_characteristics': {
                'bond_loan': self.bond_loan,
                'seniority': self.seniority,
                'dip': self.flags.get('dip', False) if self.flags else False,
                'default_asset': self.flags.get('default_asset', False) if self.flags else False,
                'struct_finance': self.flags.get('struct_finance', False) if self.flags else False
            }
        }
    
    # Yield Curve Integration Methods
    def update_fair_value(self, yield_curve_service=None, curve_name: str = None, 
                         credit_spread_bps: int = None, pricing_date: date = None):
        """
        Update fair value using yield curve discounting
        Integrates with YieldCurve system for market-based pricing
        """
        if not yield_curve_service:
            from ..models.yield_curve import YieldCurveService
            from sqlalchemy.orm import Session
            from ..core.database import get_db
            session = next(get_db())
            yield_curve_service = YieldCurveService(session)
        
        if not pricing_date:
            pricing_date = date.today()
        
        # Default curve selection based on asset characteristics
        if not curve_name:
            curve_name = self._select_default_discount_curve()
        
        # Default credit spread based on rating
        if credit_spread_bps is None:
            credit_spread_bps = self._estimate_credit_spread()
        
        try:
            # Generate expected cash flows
            cash_flows = self._generate_cash_flows(pricing_date)
            
            if not cash_flows:
                return None
            
            # Load discount curve
            discount_curve = yield_curve_service.load_yield_curve(curve_name, pricing_date)
            if not discount_curve:
                print(f"Warning: Discount curve {curve_name} not found for {self.blkrock_id}")
                return None
            
            # Calculate present value with credit spread adjustment
            fair_value = self._calculate_fair_value_with_spread(
                cash_flows, discount_curve, credit_spread_bps, pricing_date
            )
            
            # Update asset with calculated values
            self.fair_value = fair_value
            self.fair_value_date = pricing_date
            self.discount_curve_name = curve_name
            self.pricing_spread_bps = credit_spread_bps
            
            return {
                'fair_value': float(fair_value),
                'discount_curve': curve_name,
                'credit_spread_bps': credit_spread_bps,
                'pricing_date': pricing_date,
                'cash_flow_count': len(cash_flows)
            }
            
        except Exception as e:
            print(f"Warning: Failed to update fair value for {self.blkrock_id}: {e}")
            return None
    
    def _select_default_discount_curve(self) -> str:
        """Select appropriate discount curve based on asset characteristics"""
        # Treasury curve for government securities
        if self.sector and 'GOVERNMENT' in self.sector.upper():
            return 'USD_TREASURY'
        
        # Credit curves based on rating
        effective_rating = self.get_effective_sp_rating() or self.get_effective_mdy_rating()
        
        if effective_rating:
            # Convert to S&P equivalent for curve selection
            if effective_rating.startswith(('AAA', 'AA', 'A')):
                return 'USD_CREDIT_AAA'
            elif effective_rating.startswith(('BBB', 'Baa')):
                return 'USD_CREDIT_BBB'
            else:
                return 'USD_CREDIT_BBB'  # Default for speculative grade
        
        # Default to SOFR for floating rate assets
        if self.coupon_type == 'FLOATING':
            return 'USD_SOFR'
        
        # Default treasury curve
        return 'USD_TREASURY'
    
    def _estimate_credit_spread(self) -> int:
        """Estimate credit spread based on asset characteristics"""
        # Base spread on rating
        effective_rating = self.get_effective_sp_rating() or self.get_effective_mdy_rating()
        
        base_spread = 0
        if effective_rating:
            if effective_rating.startswith(('AAA', 'Aaa')):
                base_spread = 50  # 50 bps
            elif effective_rating.startswith(('AA', 'Aa')):
                base_spread = 75  # 75 bps
            elif effective_rating.startswith(('A', 'A')):
                base_spread = 100  # 100 bps
            elif effective_rating.startswith(('BBB', 'Baa')):
                base_spread = 150  # 150 bps
            elif effective_rating.startswith(('BB', 'Ba')):
                base_spread = 300  # 300 bps
            elif effective_rating.startswith(('B', 'B')):
                base_spread = 500  # 500 bps
            else:
                base_spread = 800  # 800 bps for CCC and below
        else:
            base_spread = 400  # Default spread
        
        # Adjust for seniority
        if self.seniority == 'SENIOR SECURED':
            base_spread = int(base_spread * 0.8)  # 20% reduction
        elif self.seniority == 'SUBORDINATE':
            base_spread = int(base_spread * 1.5)  # 50% increase
        
        # Adjust for DIP status
        if self.flags and self.flags.get('dip', False):
            base_spread = int(base_spread * 0.7)  # DIP assets get lower spread
        
        return base_spread
    
    def _generate_cash_flows(self, pricing_date: date) -> List[Tuple[date, Decimal]]:
        """Generate expected cash flows for present value calculation"""
        cash_flows = []
        
        if not self.maturity or self.maturity <= pricing_date:
            return cash_flows
        
        current_date = pricing_date
        par_amount = self.par_amount or Decimal('0')
        coupon_rate = self.coupon or Decimal('0')
        
        # Simple cash flow model - can be enhanced with more sophisticated models
        if self.bond_loan == 'BOND':
            # Bond: periodic interest + principal at maturity
            payment_frequency = 2  # Semi-annual for bonds
            payment_months = 12 // payment_frequency
            
            while current_date < self.maturity:
                next_payment = current_date
                if current_date == pricing_date:
                    # Find next payment date
                    if payment_months == 6:  # Semi-annual
                        next_payment = date(current_date.year, 6 if current_date.month <= 6 else 12, 15)
                        if next_payment <= current_date:
                            next_payment = date(current_date.year + 1, 6, 15)
                else:
                    next_payment = date(current_date.year, current_date.month + payment_months, current_date.day)
                    if current_date.month + payment_months > 12:
                        next_payment = date(current_date.year + 1, 
                                          (current_date.month + payment_months) - 12, 
                                          current_date.day)
                
                if next_payment > self.maturity:
                    break
                
                # Interest payment
                interest_payment = par_amount * (coupon_rate / payment_frequency)
                if interest_payment > 0:
                    cash_flows.append((next_payment, interest_payment))
                
                current_date = next_payment
            
            # Principal repayment at maturity
            if par_amount > 0:
                cash_flows.append((self.maturity, par_amount))
        
        else:
            # Loan: assume monthly amortization or bullet payment
            if self.bond_loan == 'LOAN':
                # Simple model: quarterly interest + bullet principal
                payment_months = 3  # Quarterly
                
                while current_date < self.maturity:
                    next_payment = date(current_date.year, 
                                      current_date.month + payment_months, 
                                      current_date.day)
                    if current_date.month + payment_months > 12:
                        next_payment = date(current_date.year + 1,
                                          (current_date.month + payment_months) - 12,
                                          current_date.day)
                    
                    if next_payment > self.maturity:
                        break
                    
                    # Interest payment
                    interest_payment = par_amount * (coupon_rate / 4)  # Quarterly
                    if interest_payment > 0:
                        cash_flows.append((next_payment, interest_payment))
                    
                    current_date = next_payment
                
                # Principal repayment at maturity
                if par_amount > 0:
                    cash_flows.append((self.maturity, par_amount))
        
        return cash_flows
    
    def _calculate_fair_value_with_spread(self, cash_flows: List[Tuple[date, Decimal]], 
                                        discount_curve, credit_spread_bps: int, 
                                        pricing_date: date) -> Decimal:
        """Calculate fair value with credit spread adjustment"""
        pv = Decimal('0')
        spread_decimal = Decimal(str(credit_spread_bps / 10000))  # Convert bps to decimal
        
        for cf_date, cf_amount in cash_flows:
            if cf_date <= pricing_date:
                continue
            
            # Get base discount rate
            base_rate = discount_curve.zero_rate(pricing_date, cf_date)
            
            # Add credit spread
            total_rate = base_rate + float(spread_decimal)
            
            # Calculate years to cash flow
            years_to_cf = (cf_date - pricing_date).days / 365.25
            
            # Present value calculation
            discount_factor = Decimal(str((1 + total_rate) ** -years_to_cf))
            pv += cf_amount * discount_factor
        
        return pv.quantize(Decimal('0.01'))
    
    def get_fair_value_analytics(self) -> Dict[str, Any]:
        """Get comprehensive fair value analytics"""
        return {
            'asset_id': self.blkrock_id,
            'current_fair_value': float(self.fair_value) if self.fair_value else None,
            'par_amount': float(self.par_amount) if self.par_amount else None,
            'fair_value_ratio': (float(self.fair_value) / float(self.par_amount) 
                               if self.fair_value and self.par_amount and self.par_amount > 0 
                               else None),
            'pricing_info': {
                'discount_curve': self.discount_curve_name,
                'credit_spread_bps': self.pricing_spread_bps,
                'pricing_date': self.fair_value_date
            },
            'asset_characteristics': {
                'maturity': self.maturity,
                'coupon': float(self.coupon) if self.coupon else None,
                'coupon_type': self.coupon_type,
                'seniority': self.seniority,
                'rating': self.get_effective_sp_rating() or self.get_effective_mdy_rating()
            }
        }
    
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