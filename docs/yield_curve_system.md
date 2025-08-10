# Yield Curve System Documentation

## Overview

The Yield Curve System provides comprehensive yield curve management for CLO deals with complete VBA functional parity. This system implements spot rate interpolation, forward rate calculations, and zero rate computations for accurate asset valuation and cash flow modeling.

## Architecture

### Core Components

1. **YieldCurve Class** - Main business logic with VBA parity
2. **YieldCurveService** - Database operations and persistence
3. **SQLAlchemy Models** - 4-table database schema
4. **Asset Integration** - Seamless asset pricing and valuation

### Database Schema

```sql
-- Main yield curve configuration
yield_curves (
    curve_id SERIAL PRIMARY KEY,
    curve_name VARCHAR(100) NOT NULL,
    analysis_date DATE NOT NULL,
    curve_type VARCHAR(50) DEFAULT 'SPOT',
    base_currency VARCHAR(3) DEFAULT 'USD',
    day_count_convention VARCHAR(20) DEFAULT 'ACT/365',
    interpolation_method VARCHAR(20) DEFAULT 'LINEAR'
);

-- Rate data points
yield_curve_rates (
    rate_id SERIAL PRIMARY KEY,
    curve_id INTEGER REFERENCES yield_curves(curve_id),
    tenor_months INTEGER NOT NULL,
    rate_value DECIMAL(8,6) NOT NULL,
    rate_type VARCHAR(20) DEFAULT 'SPOT'
);

-- Forward rate calculations
forward_rates (
    forward_id SERIAL PRIMARY KEY,
    curve_id INTEGER REFERENCES yield_curves(curve_id),
    start_months INTEGER NOT NULL,
    end_months INTEGER NOT NULL,
    forward_rate DECIMAL(8,6) NOT NULL,
    calculation_date DATE NOT NULL
);

-- Zero coupon bond prices
zero_rates (
    zero_id SERIAL PRIMARY KEY,
    curve_id INTEGER REFERENCES yield_curves(curve_id),
    maturity_months INTEGER NOT NULL,
    zero_rate DECIMAL(8,6) NOT NULL,
    discount_factor DECIMAL(10,8) NOT NULL
);
```

## VBA Functional Parity

### Method Mapping

| VBA Method | Python Method | Description |
|------------|---------------|-------------|
| `Setup()` | `setup()` | Initialize yield curve with rates |
| `SpotRate()` | `spot_rate()` | Get spot rate for specific tenor |
| `ZeroRate()` | `zero_rate()` | Calculate zero coupon rate |
| `ForwardRate()` | `forward_rate()` | Calculate forward rate between periods |

### Variable Mapping

```python
# VBA → Python exact mapping
clsName → name                    # Curve name
clsAnalysisDate → analysis_date   # Analysis date
clsRateDict → rate_dict          # Rate dictionary {tenor: rate}
clsSetup → _is_setup             # Setup flag
```

## Usage Examples

### Basic Setup

```python
from app.models.yield_curve import YieldCurve
from datetime import date

# Initialize yield curve
yield_curve = YieldCurve()

# Define rate curve (tenor in months → rate)
rate_dict = {
    1: 0.0250,    # 1M: 2.50%
    3: 0.0275,    # 3M: 2.75%
    6: 0.0300,    # 6M: 3.00%
    12: 0.0350,   # 1Y: 3.50%
    24: 0.0400,   # 2Y: 4.00%
    36: 0.0425,   # 3Y: 4.25%
    60: 0.0450,   # 5Y: 4.50%
    120: 0.0475   # 10Y: 4.75%
}

# Setup curve with VBA equivalent parameters
yield_curve.setup(
    i_name="USD LIBOR Curve",
    i_analysis_date=date(2025, 1, 10),
    i_rate_dict=rate_dict
)
```

### Rate Interpolation

```python
# Get spot rate for 18-month tenor (interpolated)
rate_18m = yield_curve.spot_rate(18)
print(f"18M Rate: {rate_18m:.4%}")  # Interpolated between 12M and 24M

# Get exact tenor rate
rate_12m = yield_curve.spot_rate(12)
print(f"12M Rate: {rate_12m:.4%}")  # Exact match from rate_dict

# Zero rate calculation
zero_rate_24m = yield_curve.zero_rate(24)
print(f"24M Zero Rate: {zero_rate_24m:.4%}")
```

### Forward Rate Calculation

```python
# Calculate 1Y forward rate starting in 2Y
forward_rate = yield_curve.forward_rate(24, 36)  # 2Y to 3Y forward
print(f"2Y-3Y Forward Rate: {forward_rate:.4%}")

# Multiple forward rates
forwards = []
for start in range(12, 61, 12):  # Annual forwards up to 5Y
    end = start + 12
    if end <= 60:
        fwd_rate = yield_curve.forward_rate(start, end)
        forwards.append((start, end, fwd_rate))
        print(f"{start//12}Y-{end//12}Y Forward: {fwd_rate:.4%}")
```

### Database Persistence

```python
from app.services.yield_curve import YieldCurveService

# Save to database
service = YieldCurveService(session)
curve_id = yield_curve.save_to_database(service)

# Load from database
loaded_curve = YieldCurve.load_from_database(service, curve_id)

# Verify loaded curve matches original
assert loaded_curve.name == yield_curve.name
assert loaded_curve.analysis_date == yield_curve.analysis_date
assert loaded_curve.rate_dict == yield_curve.rate_dict
```

## VBA Implementation Details

### Setup Method

**VBA Code:**
```vba
Public Sub Setup(iName As String, iAnalysisDate As Date, iRateDict As Dictionary)
    clsName = iName
    clsAnalysisDate = iAnalysisDate
    Set clsRateDict = iRateDict
    clsSetup = True
End Sub
```

**Python Equivalent:**
```python
def setup(self, i_name: str, i_analysis_date: date, i_rate_dict: Dict[int, float]) -> None:
    """VBA Setup() method equivalent"""
    # VBA: clsName = iName
    self.name = i_name
    
    # VBA: clsAnalysisDate = iAnalysisDate
    self.analysis_date = i_analysis_date
    
    # VBA: Set clsRateDict = iRateDict
    self.rate_dict = i_rate_dict.copy()
    
    # VBA: clsSetup = True
    self._is_setup = True
```

### Spot Rate Interpolation

**VBA Code:**
```vba
Public Function SpotRate(iTenor As Integer) As Double
    If clsRateDict.Exists(iTenor) Then
        SpotRate = clsRateDict(iTenor)
    Else
        ' Linear interpolation logic
        Dim lPreviousMonth As Integer, lNextMonth As Integer
        Dim lWeight As Double
        
        ' Find surrounding tenors and interpolate
        SpotRate = ((1 - lWeight) * clsRateDict(lPreviousMonth) + lWeight * clsRateDict(lNextMonth))
    End If
End Function
```

**Python Equivalent:**
```python
def spot_rate(self, i_tenor: int) -> float:
    """VBA SpotRate() function equivalent with exact interpolation logic"""
    if not self._is_setup:
        raise RuntimeError("Must call setup() before using spot_rate()")
    
    # VBA: If clsRateDict.Exists(iTenor) Then SpotRate = clsRateDict(iTenor)
    if i_tenor in self.rate_dict:
        return self.rate_dict[i_tenor]
    
    # VBA linear interpolation logic
    sorted_tenors = sorted(self.rate_dict.keys())
    
    # Find surrounding tenors
    l_previous_month = None
    l_next_month = None
    
    for tenor in sorted_tenors:
        if tenor < i_tenor:
            l_previous_month = tenor
        elif tenor > i_tenor:
            l_next_month = tenor
            break
    
    if l_previous_month is None:
        return self.rate_dict[sorted_tenors[0]]
    if l_next_month is None:
        return self.rate_dict[sorted_tenors[-1]]
    
    # VBA: lWeight calculation and interpolation
    weight = (i_tenor - l_previous_month) / (l_next_month - l_previous_month)
    
    # VBA: SpotRate = ((1 - lWeight) * clsRateDict(lPreviousMonth) + lWeight * clsRateDict(lNextMonth))
    spot_rate = ((1 - weight) * self.rate_dict[l_previous_month] + 
                 weight * self.rate_dict[l_next_month])
    
    return spot_rate
```

### Zero Rate Calculation

```python
def zero_rate(self, i_tenor: int) -> float:
    """Calculate zero coupon rate for given tenor"""
    # For simplicity, zero rate equals spot rate in this implementation
    # More sophisticated models would use bootstrapping
    return self.spot_rate(i_tenor)
```

### Forward Rate Calculation

```python
def forward_rate(self, start_tenor: int, end_tenor: int) -> float:
    """Calculate forward rate between two tenors"""
    if start_tenor >= end_tenor:
        raise ValueError("Start tenor must be less than end tenor")
    
    # Get spot rates
    r1 = self.spot_rate(start_tenor)
    r2 = self.spot_rate(end_tenor)
    
    # Convert months to years
    t1 = start_tenor / 12.0
    t2 = end_tenor / 12.0
    
    # Forward rate formula: (1 + r2)^t2 = (1 + r1)^t1 * (1 + f)^(t2-t1)
    # Solving for f: f = ((1 + r2)^t2 / (1 + r1)^t1)^(1/(t2-t1)) - 1
    
    forward = ((1 + r2) ** t2 / (1 + r1) ** t1) ** (1 / (t2 - t1)) - 1
    
    return forward
```

## Asset Integration

### Asset Pricing Integration

```python
from app.models.asset import Asset

# Asset uses yield curve for pricing
asset = Asset(...)
asset.setup_yield_curve(yield_curve)

# Calculate present value using yield curve
pv = asset.calculate_present_value()

# Calculate duration using yield curve rates
duration = asset.calculate_duration()
```

### Cash Flow Discounting

```python
def discount_cash_flows(self, cash_flows: List[Tuple[date, float]]) -> float:
    """Discount cash flows using yield curve rates"""
    pv = 0.0
    
    for cf_date, cf_amount in cash_flows:
        # Calculate tenor in months
        months = (cf_date - self.analysis_date).days / 30.44  # Average days per month
        
        # Get discount rate from curve
        discount_rate = self.spot_rate(int(months))
        
        # Calculate present value
        years = months / 12.0
        discount_factor = (1 + discount_rate) ** years
        pv += cf_amount / discount_factor
    
    return pv
```

## Performance Considerations

### Interpolation Optimization

```python
def _build_interpolation_cache(self):
    """Pre-build interpolation cache for common tenors"""
    common_tenors = list(range(1, 121))  # 1 month to 10 years
    self._rate_cache = {}
    
    for tenor in common_tenors:
        self._rate_cache[tenor] = self._calculate_spot_rate(tenor)

def spot_rate_cached(self, i_tenor: int) -> float:
    """Cached version for better performance"""
    if i_tenor in self._rate_cache:
        return self._rate_cache[i_tenor]
    return self.spot_rate(i_tenor)
```

### Bulk Rate Calculations

```python
def get_rate_vector(self, tenors: List[int]) -> List[float]:
    """Get rates for multiple tenors efficiently"""
    return [self.spot_rate(tenor) for tenor in tenors]

def get_discount_factors(self, tenors: List[int]) -> List[float]:
    """Get discount factors for multiple tenors"""
    factors = []
    for tenor in tenors:
        rate = self.spot_rate(tenor)
        years = tenor / 12.0
        factor = 1 / (1 + rate) ** years
        factors.append(factor)
    return factors
```

## Testing Framework

### VBA Parity Tests

```python
def test_vba_setup_method():
    """Test VBA Setup() method equivalent"""
    yield_curve = YieldCurve()
    rate_dict = {12: 0.035, 24: 0.040, 36: 0.042}
    
    yield_curve.setup("Test Curve", date(2025, 1, 10), rate_dict)
    
    assert yield_curve.name == "Test Curve"
    assert yield_curve.analysis_date == date(2025, 1, 10)
    assert yield_curve.rate_dict == rate_dict
    assert yield_curve._is_setup == True

def test_vba_interpolation_logic():
    """Test VBA interpolation with exact logic"""
    yield_curve = YieldCurve()
    rate_dict = {12: 0.030, 36: 0.040}
    yield_curve.setup("Test", date(2025, 1, 10), rate_dict)
    
    # Test interpolation at midpoint
    rate_24m = yield_curve.spot_rate(24)
    expected = 0.035  # Midpoint between 3% and 4%
    
    assert abs(rate_24m - expected) < 0.0001

def test_forward_rate_calculation():
    """Test forward rate calculation accuracy"""
    yield_curve = YieldCurve()
    rate_dict = {12: 0.030, 24: 0.035, 36: 0.040}
    yield_curve.setup("Test", date(2025, 1, 10), rate_dict)
    
    # Calculate 1Y forward starting in 1Y
    forward = yield_curve.forward_rate(12, 24)
    
    # Forward should be approximately 4% given the curve shape
    assert 0.038 < forward < 0.042
```

### Integration Tests

```python
def test_asset_integration():
    """Test integration with Asset pricing"""
    from app.models.asset import Asset
    
    # Setup yield curve
    yield_curve = YieldCurve()
    rate_dict = {12: 0.035, 24: 0.040, 36: 0.045}
    yield_curve.setup("Pricing Curve", date(2025, 1, 10), rate_dict)
    
    # Create asset with yield curve
    asset = Asset(par_amount=1000000)
    asset.setup_yield_curve(yield_curve)
    
    # Test pricing functions work
    pv = asset.calculate_present_value()
    assert pv > 0
    
    duration = asset.calculate_duration()
    assert duration > 0
```

### Database Persistence Tests

```python
def test_database_roundtrip():
    """Test save/load database operations"""
    # Create original curve
    original = YieldCurve()
    rate_dict = {1: 0.025, 6: 0.030, 12: 0.035, 24: 0.040}
    original.setup("DB Test Curve", date(2025, 1, 10), rate_dict)
    
    # Save to database
    service = YieldCurveService(session)
    curve_id = original.save_to_database(service)
    
    # Load from database
    loaded = YieldCurve.load_from_database(service, curve_id)
    
    # Verify equivalence
    assert loaded.name == original.name
    assert loaded.analysis_date == original.analysis_date
    assert loaded.rate_dict == original.rate_dict
    
    # Test interpolation works the same
    for tenor in [3, 9, 18, 30]:
        assert abs(loaded.spot_rate(tenor) - original.spot_rate(tenor)) < 1e-6
```

## Advanced Features

### Curve Bootstrapping

```python
def bootstrap_zero_curve(self, bond_prices: Dict[int, float]) -> None:
    """Bootstrap zero curve from bond prices"""
    # Implementation for bootstrapping zero rates from market prices
    # This is a more advanced feature for sophisticated curve construction
    pass

def build_forward_curve(self) -> Dict[Tuple[int, int], float]:
    """Build complete forward rate matrix"""
    forwards = {}
    tenors = sorted(self.rate_dict.keys())
    
    for i, start in enumerate(tenors):
        for end in tenors[i+1:]:
            forward = self.forward_rate(start, end)
            forwards[(start, end)] = forward
    
    return forwards
```

### Curve Analytics

```python
def calculate_curve_metrics(self) -> Dict[str, float]:
    """Calculate various curve metrics"""
    tenors = sorted(self.rate_dict.keys())
    rates = [self.rate_dict[t] for t in tenors]
    
    return {
        'curve_level': sum(rates) / len(rates),
        'curve_slope': (rates[-1] - rates[0]) / (tenors[-1] - tenors[0]),
        'curve_curvature': self._calculate_curvature(),
        'max_rate': max(rates),
        'min_rate': min(rates),
        'rate_volatility': self._calculate_volatility(rates)
    }

def _calculate_curvature(self) -> float:
    """Calculate curve curvature (butterfly measure)"""
    # Simplified curvature calculation
    if len(self.rate_dict) < 3:
        return 0.0
    
    tenors = sorted(self.rate_dict.keys())
    if len(tenors) >= 3:
        short = self.rate_dict[tenors[0]]
        medium = self.rate_dict[tenors[len(tenors)//2]]
        long = self.rate_dict[tenors[-1]]
        
        # Butterfly: 2 * medium - short - long
        return 2 * medium - short - long
    
    return 0.0
```

## Error Handling

### Validation

```python
def validate_setup_parameters(self, i_name: str, i_analysis_date: date, i_rate_dict: Dict[int, float]) -> None:
    """Validate setup parameters"""
    if not i_name or not i_name.strip():
        raise ValueError("Curve name cannot be empty")
    
    if not i_analysis_date:
        raise ValueError("Analysis date is required")
    
    if not i_rate_dict or len(i_rate_dict) < 2:
        raise ValueError("Rate dictionary must contain at least 2 points")
    
    # Validate tenors are positive
    for tenor in i_rate_dict.keys():
        if tenor <= 0:
            raise ValueError(f"Invalid tenor: {tenor}. Tenors must be positive integers")
    
    # Validate rates are reasonable
    for rate in i_rate_dict.values():
        if rate < -0.10 or rate > 1.0:  # -10% to 100% range
            raise ValueError(f"Invalid rate: {rate}. Rates must be between -10% and 100%")

def validate_tenor_request(self, tenor: int) -> None:
    """Validate tenor for rate requests"""
    if tenor <= 0:
        raise ValueError(f"Tenor must be positive, got: {tenor}")
    
    if tenor > 600:  # 50 years maximum
        raise ValueError(f"Tenor too large: {tenor}. Maximum 600 months (50 years)")
```

## Migration from VBA

### Key Differences

1. **Dictionary Access**: VBA Dictionary.Exists() → Python `in` operator
2. **Linear Interpolation**: VBA manual calculation → Python systematic approach
3. **Error Handling**: VBA implicit errors → Python explicit exceptions
4. **Type Safety**: VBA Variant → Python typed parameters

### Preserved Elements

1. **Method Names**: Exact VBA method names (Setup, SpotRate, ZeroRate)
2. **Variable Names**: Direct mapping with underscores
3. **Interpolation Logic**: Identical linear interpolation formula
4. **Setup Pattern**: Same initialization sequence

## Integration Points

### Asset Model Integration

```python
# Asset uses yield curve for valuation
asset.yield_curve = yield_curve
present_value = asset.calculate_present_value()
```

### CLO Deal Engine Integration

```python
# CLO Deal Engine uses yield curve for LIBOR rates
deal_engine.setup_yield_curve(yield_curve)
libor_rate = deal_engine._get_libor_rate(determination_date)
```

### Portfolio Valuation

```python
# Portfolio uses yield curve for mark-to-market
portfolio.setup_yield_curve(yield_curve)
portfolio_value = portfolio.calculate_market_value()
```

This documentation provides comprehensive guidance for using and maintaining the Yield Curve System with complete VBA functional parity and modern Python architecture.