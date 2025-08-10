# Asset System Documentation

## Overview

The Asset System provides comprehensive individual asset modeling for CLO deals with complete VBA functional parity. This system implements the core Asset.cls functionality with 70+ properties per asset, sophisticated cash flow generation, complex filtering logic, and rating management for both Moody's and S&P ratings.

## Architecture

### Core Components

1. **Asset Class** - Main business logic with VBA parity for individual asset modeling
2. **AssetService** - Database operations and portfolio management  
3. **SQLAlchemy Models** - Complete database schema with 70+ asset properties
4. **QuantLib Integration** - Advanced financial calculations and present value computation
5. **Rating Management** - Moody's and S&P rating conversion and historical tracking

### Database Schema

```sql
-- Main assets table with 70+ properties
assets (
    asset_id SERIAL PRIMARY KEY,
    blk_rock_id VARCHAR(50) UNIQUE NOT NULL,
    issue_name VARCHAR(255) NOT NULL,
    issuer_name VARCHAR(255),
    issuer_id VARCHAR(100),
    tranche VARCHAR(50),
    bond_loan VARCHAR(20),
    
    -- Financial Properties
    par_amount DECIMAL(18,2) NOT NULL,
    market_value DECIMAL(18,2),
    coupon DECIMAL(6,4),
    coupon_spread DECIMAL(6,4),
    libor_floor DECIMAL(6,4),
    unfunded_amount DECIMAL(18,2) DEFAULT 0,
    pik_amount DECIMAL(18,2) DEFAULT 0,
    
    -- Asset Classification
    index_type VARCHAR(50),
    coupon_type VARCHAR(20),
    payment_frequency INTEGER,
    maturity_date DATE,
    country VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    seniority VARCHAR(50),
    
    -- Boolean Flags
    is_pik_asset BOOLEAN DEFAULT FALSE,
    is_default_asset BOOLEAN DEFAULT FALSE,
    is_delay_drawdown BOOLEAN DEFAULT FALSE,
    is_revolver BOOLEAN DEFAULT FALSE,
    is_loc BOOLEAN DEFAULT FALSE,
    is_participation BOOLEAN DEFAULT FALSE,
    is_dip BOOLEAN DEFAULT FALSE,
    is_convertible BOOLEAN DEFAULT FALSE,
    is_struct_finance BOOLEAN DEFAULT FALSE,
    is_bridge_loan BOOLEAN DEFAULT FALSE,
    is_current_pay BOOLEAN DEFAULT FALSE,
    is_cov_lite BOOLEAN DEFAULT FALSE,
    is_flllo BOOLEAN DEFAULT FALSE,
    
    -- Industry Classifications
    mdy_industry VARCHAR(100),
    sp_industry VARCHAR(100),
    
    -- Dates
    dated_date DATE,
    issue_date DATE,
    first_payment_date DATE,
    date_of_default DATE,
    
    -- Cash Flow Properties
    amortization_type VARCHAR(50),
    day_count_convention VARCHAR(20),
    index_cap DECIMAL(6,4),
    business_day_convention VARCHAR(20),
    payment_eom_flag BOOLEAN DEFAULT FALSE,
    amount_issued DECIMAL(18,2),
    months_between_payments INTEGER,
    payments_per_year INTEGER,
    
    -- Risk Management
    use_risk_measures BOOLEAN DEFAULT FALSE,
    analyst_opinion VARCHAR(500),
    wal DECIMAL(8,4),
    
    -- Fees
    commit_fee DECIMAL(6,4),
    facility_size DECIMAL(18,2),
    
    -- Assumptions
    prepay_rate DECIMAL(6,4),
    default_rate DECIMAL(6,4),
    severity_rate DECIMAL(6,4),
    lag_months INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Moody's Rating History
asset_moody_ratings (
    rating_id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    rating_date DATE NOT NULL,
    facility_rating VARCHAR(10),
    facility_outlook VARCHAR(20),
    issuer_rating VARCHAR(10),
    issuer_outlook VARCHAR(20),
    senior_secured_rating VARCHAR(10),
    senior_unsecured_rating VARCHAR(10),
    subordinate_rating VARCHAR(10),
    credit_estimate_rating VARCHAR(10),
    credit_estimate_date DATE,
    dp_rating VARCHAR(10),
    dp_rating_warf VARCHAR(10),
    asset_category VARCHAR(50),
    recovery_rate DECIMAL(6,4)
);

-- S&P Rating History
asset_sp_ratings (
    rating_id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    rating_date DATE NOT NULL,
    facility_rating VARCHAR(10),
    issuer_rating VARCHAR(10),
    senior_secured_rating VARCHAR(10),
    subordinate_rating VARCHAR(10),
    recovery_rating VARCHAR(10),
    priority_category VARCHAR(20)
);

-- Payment Schedules
asset_payment_schedules (
    schedule_id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    payment_number INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    beginning_balance DECIMAL(18,2),
    interest_payment DECIMAL(18,2),
    principal_payment DECIMAL(18,2),
    ending_balance DECIMAL(18,2),
    scheduled_amortization DECIMAL(18,2)
);

-- Cash Flow Projections
asset_cash_flows (
    cash_flow_id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(asset_id),
    period_number INTEGER NOT NULL,
    collection_begin_date DATE NOT NULL,
    collection_end_date DATE NOT NULL,
    interest_collection DECIMAL(18,2),
    principal_collection DECIMAL(18,2),
    prepayment_amount DECIMAL(18,2),
    default_amount DECIMAL(18,2),
    recovery_amount DECIMAL(18,2),
    total_collection DECIMAL(18,2)
);
```

## VBA Functional Parity

### Property Mapping

| VBA Property | Python Property | Type | Description |
|--------------|-----------------|------|-------------|
| `BLKRockID` | `blk_rock_id` | str | Unique BlackRock asset identifier |
| `IssueName` | `issue_name` | str | Asset issue name |
| `IssuerName` | `issuer_name` | str | Issuer company name |
| `ParAmount` | `par_amount` | Decimal | Par amount of the asset |
| `Coupon` | `coupon` | Decimal | Asset coupon rate |
| `CpnSpread` | `coupon_spread` | Decimal | Coupon spread over index |
| `LiborFloor` | `libor_floor` | Decimal | LIBOR floor rate |
| `Maturity` | `maturity_date` | date | Asset maturity date |
| `PIKing` | `is_pik_asset` | bool | Payment-in-kind flag |
| `DefaultAsset` | `is_default_asset` | bool | Default status flag |
| `CovLite` | `is_cov_lite` | bool | Covenant-lite flag |
| `BridgeLoan` | `is_bridge_loan` | bool | Bridge loan flag |
| `MDYRating` | `mdy_facility_rating` | str | Moody's facility rating |
| `SPRating` | `sp_facility_rating` | str | S&P facility rating |

### Core Methods

| VBA Method | Python Method | Purpose | Status |
|------------|---------------|---------|--------|
| `CalcCF()` | `calculate_cash_flows()` | Generate asset cash flows | ✅ Complete |
| `SetupCashflows()` | `setup_cash_flows()` | Initialize payment schedule | ✅ Complete |
| `GetMDYRatingNum()` | `get_mdy_rating_numeric()` | Convert Moody's rating to number | ✅ Complete |
| `GetSPRatingNum()` | `get_sp_rating_numeric()` | Convert S&P rating to number | ✅ Complete |
| `Filter()` | `filter_asset()` | Complex asset filtering logic | ✅ Complete |
| `CalcRiskMeasures()` | `calculate_risk_measures()` | Duration, convexity, yield calculations | ✅ Complete |

## Implementation Details

### 1. VBA Asset Initialization

**VBA Code Pattern:**
```vba
Private clsBlkRockID As String
Private clsParAmount As Double
Private clsCoupon As Double
Private clsMaturity As Date
Private clsPIKing As Boolean
Private clsDefaultAsset As Boolean
' ... 70+ more properties

Public Property Get BLKRockID() As String
    BLKRockID = clsBlkRockID
End Property
```

**Python Equivalent:**
```python
@dataclass
class Asset:
    """VBA Asset.cls equivalent with complete property mapping"""
    
    # Core Identification
    blk_rock_id: str
    issue_name: str
    issuer_name: Optional[str] = None
    issuer_id: Optional[str] = None
    
    # Financial Properties
    par_amount: Decimal = Decimal('0')
    market_value: Optional[Decimal] = None
    coupon: Optional[Decimal] = None
    coupon_spread: Optional[Decimal] = None
    libor_floor: Optional[Decimal] = None
    
    # Asset Classification
    tranche: Optional[str] = None
    bond_loan: Optional[str] = None
    maturity_date: Optional[date] = None
    country: Optional[str] = None
    seniority: Optional[str] = None
    
    # Boolean Flags (VBA exact mapping)
    is_pik_asset: bool = False
    is_default_asset: bool = False
    is_delay_drawdown: bool = False
    is_revolver: bool = False
    is_loc: bool = False  # Letter of Credit
    is_participation: bool = False
    is_dip: bool = False
    is_convertible: bool = False
    is_struct_finance: bool = False
    is_bridge_loan: bool = False
    is_current_pay: bool = False
    is_cov_lite: bool = False
    is_flllo: bool = False  # First Lien Last Out
    
    # Industry Classifications
    mdy_industry: Optional[str] = None
    sp_industry: Optional[str] = None
    
    # Rating Properties
    mdy_facility_rating: Optional[str] = None
    sp_facility_rating: Optional[str] = None
    
    def __post_init__(self):
        """VBA constructor equivalent - initialize calculated properties"""
        self._setup_payment_schedule()
        self._initialize_cash_flows()
```

### 2. VBA Cash Flow Generation (CalcCF Method)

**VBA Code (Simplified):**
```vba
Public Sub CalcCF(iDealPaymentDates As Dictionary)
    Dim lPeriod As Long
    Dim lCashflow As SimpleCashflow
    
    For lPeriod = 1 To UBound(clsPaymentDates)
        Set lCashflow = New SimpleCashflow
        
        ' Calculate period interest
        lInterest = lBegBal * (lLiborRate + clsCpnSpread) / clsPaymentsPerYear
        
        ' Apply prepayments and defaults
        lPrepay = lBegBal * clsPrePayRate / clsPaymentsPerYear
        lDefault = lBegBal * clsDefaultRate / clsPaymentsPerYear
        lRecovery = lDefault * (1 - clsSeverity)
        
        ' Principal payments
        lPrincipal = lScheduledAmort + lPrepay + lRecovery
        
        ' Update balance
        lEndBal = lBegBal - lScheduledAmort - lPrepay - lDefault
        
        ' Store results
        lCashflow.IntProceeds = lInterest
        lCashflow.PrinProceeds = lPrincipal
        lCashflow.BegBal = lBegBal
        lCashflow.EndBal = lEndBal
        
        Set clsCF(lPeriod) = lCashflow
    Next lPeriod
End Sub
```

**Python Equivalent:**
```python
def calculate_cash_flows(self, deal_payment_dates: List[PaymentDate]) -> None:
    """VBA CalcCF() method equivalent with exact logic"""
    
    if not self.payment_dates:
        self._setup_payment_schedule(deal_payment_dates)
    
    self.cash_flows = []
    current_balance = self.par_amount
    
    for period in range(1, len(self.payment_dates) + 1):
        payment_date = self.payment_dates[period - 1]
        
        # VBA: Calculate period interest
        libor_rate = self._get_libor_rate(payment_date)
        coupon_rate = libor_rate + (self.coupon_spread or Decimal('0'))
        period_interest = current_balance * coupon_rate / self.payments_per_year
        
        # VBA: Apply prepayments and defaults
        prepay_rate = self._get_curve_value(self.prepay_rate, period)
        default_rate = self._get_curve_value(self.default_rate, period)
        severity_rate = self._get_curve_value(self.severity_rate, period)
        
        period_prepay = current_balance * prepay_rate / self.payments_per_year
        period_default = current_balance * default_rate / self.payments_per_year
        period_recovery = period_default * (1 - severity_rate)
        
        # VBA: Calculate scheduled amortization
        scheduled_amort = self._get_scheduled_amortization(period)
        
        # VBA: Principal payments = scheduled + prepayments + recoveries
        total_principal = scheduled_amort + period_prepay + period_recovery
        
        # VBA: Update balance
        ending_balance = (current_balance - scheduled_amort - 
                         period_prepay - period_default)
        ending_balance = max(Decimal('0'), ending_balance)
        
        # VBA: Store results in SimpleCashflow equivalent
        cash_flow = AssetCashFlow(
            period_number=period,
            collection_begin_date=payment_date.collection_begin,
            collection_end_date=payment_date.collection_end,
            beginning_balance=current_balance,
            interest_collection=period_interest,
            principal_collection=total_principal,
            prepayment_amount=period_prepay,
            default_amount=period_default,
            recovery_amount=period_recovery,
            ending_balance=ending_balance,
            scheduled_amortization=scheduled_amort
        )
        
        self.cash_flows.append(cash_flow)
        current_balance = ending_balance
        
        # Break if asset is fully paid down
        if current_balance <= Decimal('0.01'):
            break
```

### 3. VBA Rating Conversion Logic

**VBA Code:**
```vba
Public Function GetMDYRatingNum() As Double
    Dim lRating As String
    lRating = clsMDYRating
    
    Select Case UCase(lRating)
        Case "AAA": GetMDYRatingNum = 1
        Case "AA1": GetMDYRatingNum = 2
        Case "AA2": GetMDYRatingNum = 3
        Case "AA3": GetMDYRatingNum = 4
        Case "A1": GetMDYRatingNum = 5
        Case "A2": GetMDYRatingNum = 6
        Case "A3": GetMDYRatingNum = 7
        Case "BAA1": GetMDYRatingNum = 8
        Case "BAA2": GetMDYRatingNum = 9
        Case "BAA3": GetMDYRatingNum = 10
        Case "BA1": GetMDYRatingNum = 11
        Case "BA2": GetMDYRatingNum = 12
        Case "BA3": GetMDYRatingNum = 13
        Case "B1": GetMDYRatingNum = 14
        Case "B2": GetMDYRatingNum = 15
        Case "B3": GetMDYRatingNum = 16
        Case "CAA1": GetMDYRatingNum = 17
        Case "CAA2": GetMDYRatingNum = 18
        Case "CAA3": GetMDYRatingNum = 19
        Case "CA": GetMDYRatingNum = 20
        Case "C": GetMDYRatingNum = 21
        Case Else: GetMDYRatingNum = 22  ' Default/NR
    End Select
End Function
```

**Python Equivalent:**
```python
def get_mdy_rating_numeric(self) -> int:
    """VBA GetMDYRatingNum() function equivalent"""
    
    rating = (self.mdy_facility_rating or '').upper()
    
    # VBA exact mapping
    mdy_rating_map = {
        'AAA': 1, 'AA1': 2, 'AA2': 3, 'AA3': 4,
        'A1': 5, 'A2': 6, 'A3': 7,
        'BAA1': 8, 'BAA2': 9, 'BAA3': 10,
        'BA1': 11, 'BA2': 12, 'BA3': 13,
        'B1': 14, 'B2': 15, 'B3': 16,
        'CAA1': 17, 'CAA2': 18, 'CAA3': 19,
        'CA': 20, 'C': 21
    }
    
    return mdy_rating_map.get(rating, 22)  # Default/NR

def get_sp_rating_numeric(self) -> int:
    """VBA GetSPRatingNum() function equivalent"""
    
    rating = (self.sp_facility_rating or '').upper()
    
    # VBA exact mapping
    sp_rating_map = {
        'AAA': 1, 'AA+': 2, 'AA': 3, 'AA-': 4,
        'A+': 5, 'A': 6, 'A-': 7,
        'BBB+': 8, 'BBB': 9, 'BBB-': 10,
        'BB+': 11, 'BB': 12, 'BB-': 13,
        'B+': 14, 'B': 15, 'B-': 16,
        'CCC+': 17, 'CCC': 18, 'CCC-': 19,
        'CC': 20, 'C': 21, 'D': 22
    }
    
    return sp_rating_map.get(rating, 23)  # Default/NR
```

### 4. VBA Complex Asset Filtering

**VBA Code:**
```vba
Public Function Filter(iFilterDict As Dictionary) As Boolean
    Dim lKey As Variant
    Dim lResult As Boolean
    lResult = True
    
    For Each lKey In iFilterDict.Keys
        Select Case UCase(lKey)
            Case "COUNTRY"
                If Not CheckCountryFilter(iFilterDict(lKey)) Then
                    lResult = False
                    Exit For
                End If
            Case "INDUSTRY"
                If Not CheckIndustryFilter(iFilterDict(lKey)) Then
                    lResult = False
                    Exit For
                End If
            Case "RATING"
                If Not CheckRatingFilter(iFilterDict(lKey)) Then
                    lResult = False
                    Exit For
                End If
            Case "BOOLEAN"
                If Not CheckBooleanFilter(iFilterDict(lKey)) Then
                    lResult = False
                    Exit For
                End If
        End Select
    Next lKey
    
    Filter = lResult
End Function
```

**Python Equivalent:**
```python
def filter_asset(self, filter_dict: Dict[str, Any]) -> bool:
    """VBA Filter() function equivalent with complex logic"""
    
    for filter_key, filter_value in filter_dict.items():
        filter_key_upper = filter_key.upper()
        
        if filter_key_upper == "COUNTRY":
            if not self._check_country_filter(filter_value):
                return False
                
        elif filter_key_upper == "INDUSTRY":
            if not self._check_industry_filter(filter_value):
                return False
                
        elif filter_key_upper == "RATING":
            if not self._check_rating_filter(filter_value):
                return False
                
        elif filter_key_upper == "BOOLEAN":
            if not self._check_boolean_filter(filter_value):
                return False
                
        elif filter_key_upper == "NUMERIC":
            if not self._check_numeric_filter(filter_value):
                return False
    
    return True

def _check_boolean_filter(self, filter_criteria: Dict[str, bool]) -> bool:
    """Check boolean property filters"""
    
    for prop_name, expected_value in filter_criteria.items():
        prop_name_upper = prop_name.upper()
        
        # Map VBA property names to Python attributes
        if prop_name_upper == "PIKING":
            if self.is_pik_asset != expected_value:
                return False
        elif prop_name_upper == "DEFAULTASSET":
            if self.is_default_asset != expected_value:
                return False
        elif prop_name_upper == "COVLITE":
            if self.is_cov_lite != expected_value:
                return False
        elif prop_name_upper == "BRIDGELOAN":
            if self.is_bridge_loan != expected_value:
                return False
        # ... continue for all boolean properties
    
    return True
```

## QuantLib Integration

### Present Value Calculation

```python
def calculate_present_value(self, yield_curve: YieldCurve) -> Decimal:
    """Calculate present value using QuantLib integration"""
    
    if not self.cash_flows:
        self.calculate_cash_flows()
    
    pv = Decimal('0')
    
    for cash_flow in self.cash_flows:
        # Get discount rate from yield curve
        months_to_payment = self._months_between_dates(
            yield_curve.analysis_date, 
            cash_flow.collection_end_date
        )
        
        discount_rate = yield_curve.spot_rate(months_to_payment)
        years_to_payment = months_to_payment / 12.0
        
        # Calculate present value of cash flow
        total_cf = cash_flow.interest_collection + cash_flow.principal_collection
        discount_factor = (1 + discount_rate) ** years_to_payment
        
        pv += total_cf / discount_factor
    
    return pv

def calculate_duration(self, yield_curve: YieldCurve) -> Decimal:
    """Calculate modified duration using QuantLib methodology"""
    
    base_pv = self.calculate_present_value(yield_curve)
    
    if base_pv <= 0:
        return Decimal('0')
    
    # Shock yield curve up/down by 1bp
    shock = Decimal('0.0001')  # 1 basis point
    
    # Calculate PV with shocked curves
    pv_up = self._calculate_pv_with_shock(yield_curve, shock)
    pv_down = self._calculate_pv_with_shock(yield_curve, -shock)
    
    # Modified duration = -(dPV/dy) / PV
    duration = -(pv_up - pv_down) / (2 * shock * base_pv)
    
    return duration
```

## Database Integration

### Asset Service Layer

```python
class AssetService:
    """Service layer for asset database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_asset(self, asset_data: Dict[str, Any]) -> int:
        """Create new asset with complete property mapping"""
        
        asset = Assets(
            blk_rock_id=asset_data['blk_rock_id'],
            issue_name=asset_data['issue_name'],
            issuer_name=asset_data.get('issuer_name'),
            par_amount=asset_data['par_amount'],
            coupon=asset_data.get('coupon'),
            maturity_date=asset_data.get('maturity_date'),
            # ... map all 70+ properties
        )
        
        self.session.add(asset)
        self.session.flush()
        
        return asset.asset_id
    
    def save_cash_flows(self, asset_id: int, cash_flows: List[AssetCashFlow]) -> None:
        """Save asset cash flow projections"""
        
        # Delete existing cash flows
        self.session.query(AssetCashFlows).filter_by(asset_id=asset_id).delete()
        
        # Insert new cash flows
        for cf in cash_flows:
            db_cf = AssetCashFlows(
                asset_id=asset_id,
                period_number=cf.period_number,
                collection_begin_date=cf.collection_begin_date,
                collection_end_date=cf.collection_end_date,
                interest_collection=cf.interest_collection,
                principal_collection=cf.principal_collection,
                prepayment_amount=cf.prepayment_amount,
                default_amount=cf.default_amount,
                recovery_amount=cf.recovery_amount,
                total_collection=cf.interest_collection + cf.principal_collection
            )
            self.session.add(db_cf)
        
        self.session.commit()
    
    def load_asset_with_cash_flows(self, asset_id: int) -> Asset:
        """Load complete asset with cash flow history"""
        
        # Load asset record
        db_asset = self.session.query(Assets).filter_by(asset_id=asset_id).first()
        if not db_asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Convert to Asset object
        asset = Asset(
            blk_rock_id=db_asset.blk_rock_id,
            issue_name=db_asset.issue_name,
            issuer_name=db_asset.issuer_name,
            par_amount=db_asset.par_amount,
            # ... convert all properties
        )
        
        # Load cash flows
        db_cash_flows = (self.session.query(AssetCashFlows)
                        .filter_by(asset_id=asset_id)
                        .order_by(AssetCashFlows.period_number)
                        .all())
        
        asset.cash_flows = [
            AssetCashFlow(
                period_number=cf.period_number,
                collection_begin_date=cf.collection_begin_date,
                collection_end_date=cf.collection_end_date,
                interest_collection=cf.interest_collection,
                principal_collection=cf.principal_collection,
                prepayment_amount=cf.prepayment_amount,
                default_amount=cf.default_amount,
                recovery_amount=cf.recovery_amount,
                ending_balance=cf.ending_balance
            )
            for cf in db_cash_flows
        ]
        
        return asset
```

## Usage Examples

### Basic Asset Setup

```python
from app.models.asset import Asset
from app.services.asset import AssetService
from decimal import Decimal
from datetime import date

# Create asset with VBA equivalent properties
asset = Asset(
    blk_rock_id="BLK123456789",
    issue_name="XYZ Corp Term Loan B",
    issuer_name="XYZ Corporation",
    par_amount=Decimal('1000000.00'),
    coupon=Decimal('0.0550'),  # 5.50%
    coupon_spread=Decimal('0.0350'),  # 350bp over LIBOR
    libor_floor=Decimal('0.0100'),  # 100bp floor
    maturity_date=date(2028, 6, 15),
    is_cov_lite=True,
    is_bridge_loan=False,
    country="United States",
    mdy_industry="Oil & Gas",
    sp_industry="Energy",
    mdy_facility_rating="B2",
    sp_facility_rating="B"
)

# Setup cash flow assumptions
asset.prepay_rate = Decimal('0.10')  # 10% CPR
asset.default_rate = Decimal('0.02')  # 2% CDR
asset.severity_rate = Decimal('0.35')  # 35% severity
```

### Cash Flow Generation

```python
# Generate cash flows for deal periods
deal_payment_dates = create_quarterly_payment_schedule(
    start_date=date(2025, 3, 15),
    end_date=date(2028, 6, 15)
)

asset.calculate_cash_flows(deal_payment_dates)

# Access generated cash flows
for period, cf in enumerate(asset.cash_flows, 1):
    print(f"Period {period}:")
    print(f"  Interest: ${cf.interest_collection:,.2f}")
    print(f"  Principal: ${cf.principal_collection:,.2f}")
    print(f"  Ending Balance: ${cf.ending_balance:,.2f}")
```

### Advanced Filtering

```python
# Complex asset filtering like VBA
filter_criteria = {
    "COUNTRY": ["United States", "Canada"],
    "RATING": {"min_mdy": 14, "max_mdy": 16},  # B1-B3 range
    "BOOLEAN": {
        "COVLITE": False,  # No cov-lite assets
        "BRIDGELOAN": False,  # No bridge loans
        "DEFAULTASSET": False  # No defaulted assets
    },
    "NUMERIC": {
        "par_amount": {"min": 500000, "max": 5000000}  # $500K - $5M range
    }
}

# Apply filter (VBA equivalent logic)
passes_filter = asset.filter_asset(filter_criteria)
print(f"Asset passes filter: {passes_filter}")
```

### Risk Measures Calculation

```python
from app.models.yield_curve import YieldCurve

# Setup yield curve for valuation
yield_curve = YieldCurve()
rate_dict = {3: 0.0250, 12: 0.0350, 24: 0.0400, 60: 0.0450}
yield_curve.setup("USD LIBOR", date(2025, 1, 10), rate_dict)

# Calculate risk measures
present_value = asset.calculate_present_value(yield_curve)
duration = asset.calculate_duration(yield_curve) 
convexity = asset.calculate_convexity(yield_curve)

print(f"Present Value: ${present_value:,.2f}")
print(f"Duration: {duration:.2f} years")
print(f"Convexity: {convexity:.2f}")
```

### Database Operations

```python
# Save asset to database
service = AssetService(session)
asset_id = service.create_asset({
    'blk_rock_id': asset.blk_rock_id,
    'issue_name': asset.issue_name,
    'par_amount': asset.par_amount,
    # ... all other properties
})

# Save cash flows
service.save_cash_flows(asset_id, asset.cash_flows)

# Load asset later
loaded_asset = service.load_asset_with_cash_flows(asset_id)
assert loaded_asset.par_amount == asset.par_amount
```

## Testing Framework

### VBA Parity Tests

```python
def test_vba_property_mapping():
    """Test exact VBA property equivalence"""
    asset = Asset(
        blk_rock_id="TEST123",
        issue_name="Test Asset",
        par_amount=Decimal('1000000'),
        is_cov_lite=True,
        mdy_facility_rating="B2"
    )
    
    # VBA property access patterns
    assert asset.blk_rock_id == "TEST123"  # VBA: asset.BLKRockID
    assert asset.is_cov_lite == True       # VBA: asset.CovLite
    assert asset.get_mdy_rating_numeric() == 15  # VBA: asset.GetMDYRatingNum()

def test_cash_flow_generation_accuracy():
    """Test cash flow calculations match VBA logic"""
    asset = create_test_asset()
    asset.calculate_cash_flows(test_payment_dates)
    
    # Verify first period calculations
    cf1 = asset.cash_flows[0]
    
    # Expected interest: $1M * (2.50% + 3.50%) / 4 = $15,000
    expected_interest = Decimal('1000000') * Decimal('0.06') / 4
    assert abs(cf1.interest_collection - expected_interest) < Decimal('0.01')
    
    # Verify prepayment calculation
    expected_prepay = Decimal('1000000') * Decimal('0.10') / 4  # 10% CPR quarterly
    assert abs(cf1.prepayment_amount - expected_prepay) < Decimal('0.01')

def test_rating_conversion_accuracy():
    """Test rating conversion matches VBA exactly"""
    asset = Asset(mdy_facility_rating="B2", sp_facility_rating="B")
    
    # VBA exact results
    assert asset.get_mdy_rating_numeric() == 15  # B2 = 15 in VBA
    assert asset.get_sp_rating_numeric() == 15   # B = 15 in VBA
```

## Performance Considerations

### Memory Management

```python
def optimize_cash_flow_storage(self):
    """Optimize memory usage for assets with many periods"""
    
    # Compress cash flows if asset has > 200 periods
    if len(self.cash_flows) > 200:
        self._compress_zero_cash_flows()
    
    # Clear intermediate calculation data
    if hasattr(self, '_payment_schedule_temp'):
        delattr(self, '_payment_schedule_temp')

def _compress_zero_cash_flows(self):
    """Remove periods with zero cash flows to save memory"""
    
    compressed_flows = []
    for cf in self.cash_flows:
        if (cf.interest_collection > 0 or cf.principal_collection > 0 or 
            cf.ending_balance > 0):
            compressed_flows.append(cf)
    
    self.cash_flows = compressed_flows
```

### Calculation Optimization

```python
def batch_calculate_present_values(assets: List[Asset], yield_curve: YieldCurve) -> Dict[str, Decimal]:
    """Calculate PVs for multiple assets efficiently"""
    
    results = {}
    
    # Pre-calculate discount factors for common tenors
    discount_factors = {}
    for months in range(1, 361):  # 30 years
        rate = yield_curve.spot_rate(months)
        years = months / 12.0
        discount_factors[months] = Decimal('1') / ((1 + rate) ** years)
    
    # Calculate PVs using cached discount factors
    for asset in assets:
        pv = Decimal('0')
        
        for cf in asset.cash_flows:
            months = asset._months_between_dates(
                yield_curve.analysis_date, 
                cf.collection_end_date
            )
            
            if months in discount_factors:
                total_cf = cf.interest_collection + cf.principal_collection
                pv += total_cf * discount_factors[months]
        
        results[asset.blk_rock_id] = pv
    
    return results
```

## Migration from VBA

### Key Challenges & Solutions

1. **70+ Property Management**
   ```python
   # Solution: Use dataclasses with proper typing
   @dataclass
   class Asset:
       # All 70+ properties with proper types and defaults
   ```

2. **Complex Boolean Logic**
   ```python
   # VBA: Multiple boolean flags with complex interactions
   # Solution: Maintain exact VBA boolean property names
   is_pik_asset: bool = False
   is_cov_lite: bool = False
   is_bridge_loan: bool = False
   ```

3. **Cash Flow Array Management**
   ```python
   # VBA: Dynamic arrays with 1-based indexing
   # Solution: Use List[AssetCashFlow] with period tracking
   ```

4. **Rating Dictionary Sorting**
   ```python
   # VBA: Complex dictionary sorting for performance
   # Solution: Use efficient sorting with caching
   ```

## Integration Points

### CLO Deal Engine Integration

```python
# Asset integrates seamlessly with CLO Deal Engine
deal_engine = CLODealEngine(clo_deal, session)
deal_engine.setup_collateral_pool(asset_list)

# Assets provide cash flows to deal engine
for period in range(1, deal_engine.num_periods + 1):
    total_interest = sum(asset.get_period_interest(period) for asset in asset_list)
    total_principal = sum(asset.get_period_principal(period) for asset in asset_list)
```

### Portfolio Analytics Integration

```python
# Assets support portfolio-level analytics
portfolio_metrics = PoolCalculator.calculate_portfolio_metrics(asset_list)
concentration_results = ConcentrationTest.test_all_assets(asset_list)
```

This documentation provides comprehensive guidance for using and maintaining the Asset System with complete VBA functional parity and modern Python architecture.