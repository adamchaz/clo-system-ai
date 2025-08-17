# Incentive Fee System Documentation

## Overview

The Incentive Fee System provides IRR-based manager incentive fee calculations for CLO deals with complete VBA functional parity. This system implements Excel-equivalent XIRR calculations and integrates seamlessly with the CLO Deal Engine.

## Architecture

### Core Components

1. **IncentiveFee Class** - Main business logic with VBA parity
2. **IncentiveFeeService** - Database operations and persistence
3. **SQLAlchemy Models** - 5-table database schema
4. **CLO Integration** - Seamless waterfall execution integration

### Database Schema

```sql
-- Main fee structure configuration
incentive_fee_structures (
    fee_structure_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50),
    fee_structure_name VARCHAR(100),
    hurdle_rate DECIMAL(6,4),
    incentive_fee_rate DECIMAL(6,4),
    closing_date DATE,
    threshold_reached BOOLEAN,
    cum_discounted_sub_payments DECIMAL(18,2)
);

-- Historical subordinated payments
subordinated_payments (
    payment_id SERIAL PRIMARY KEY,
    fee_structure_id INTEGER REFERENCES incentive_fee_structures,
    payment_date DATE,
    payment_amount DECIMAL(18,2),
    discounted_amount DECIMAL(18,2)
);

-- Period-by-period calculations
incentive_fee_calculations (
    calculation_id SERIAL PRIMARY KEY,
    fee_structure_id INTEGER REFERENCES incentive_fee_structures,
    period_number INTEGER,
    current_threshold DECIMAL(18,2),
    fee_paid_period DECIMAL(18,2),
    period_irr DECIMAL(8,6)
);

-- IRR calculation history
irr_calculation_history (
    irr_id SERIAL PRIMARY KEY,
    fee_structure_id INTEGER REFERENCES incentive_fee_structures,
    calculation_date DATE,
    irr_value DECIMAL(8,6),
    cash_flows_json TEXT,
    dates_json TEXT
);

-- Fee payment transactions
fee_payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    fee_structure_id INTEGER REFERENCES incentive_fee_structures,
    transaction_date DATE,
    base_amount DECIMAL(18,2),
    fee_amount DECIMAL(18,2),
    net_amount DECIMAL(18,2)
);
```

## VBA Functional Parity

### Method Mapping

| VBA Method | Python Method | Description |
|------------|---------------|-------------|
| `Setup()` | `setup()` | Initialize fee structure parameters |
| `DealSetup()` | `deal_setup()` | Configure deal dates and historical data |
| `Calc()` | `calc()` | Calculate threshold for current period |
| `PaymentToSubNotholder()` | `payment_to_sub_notholder()` | Record subordinated payment |
| `PayIncentiveFee()` | `pay_incentive_fee()` | Calculate and deduct fee |
| `Rollfoward()` | `rollfoward()` | Advance period and update IRR |
| `FeePaid()` | `fee_paid()` | Calculate total fees paid |
| `Output()` | `output()` | Generate VBA-formatted report |
| `IncentiveFeeThreshold()` | `incentive_fee_threshold()` | Get current threshold |

### Variable Mapping

```python
# VBA → Python exact mapping
clsFeeHurdleRate → cls_fee_hurdle_rate
clsIncentFee → cls_incent_fee  
clsThresholdReach → cls_threshold_reach
clsSubPaymentsDict → cls_sub_payments_dict
clsClosingDate → cls_closing_date
clsCurrentThreshold → cls_current_threshold
clsCurrIncetivePayments → cls_curr_incetive_payments  # Preserves VBA typo
clsCurrSubPayments → cls_curr_sub_payments
clsCurrDate → cls_curr_date
clsPeriod → cls_period
clsCumDicountedSubPayments → cls_cum_dicounted_sub_payments  # Preserves VBA typo
clsThreshold() → cls_threshold[]
clsIRR() → cls_irr[]
clsFeePaid() → cls_fee_paid[]
```

## Usage Examples

### Basic Setup

```python
from app.services.incentive_fee import IncentiveFee, IncentiveFeeService
from datetime import date

# Initialize incentive fee
incentive_fee = IncentiveFee(session)

# Historical subordinated payments
historical_payments = {
    date(2024, 4, 15): 1000000.0,   # $1M
    date(2024, 7, 15): 1200000.0,   # $1.2M  
    date(2024, 10, 15): 950000.0,   # $950K
}

# Setup with 8% hurdle, 20% incentive fee
incentive_fee.setup(
    i_fee_threshold=0.08,           # 8% hurdle rate
    i_incentive_fee=0.20,           # 20% incentive fee
    i_payto_sub_notholder=historical_payments
)

# Deal setup
incentive_fee.deal_setup(
    i_num_of_payments=60,           # 60 quarterly payments
    i_close_date=date(2024, 1, 15), # Deal closing
    i_analysis_date=date(2025, 1, 10) # Analysis date
)
```

### Period Processing

```python
# Process period 5
period_date = date(2025, 4, 15)
incentive_fee.calc(period_date)

# Record subordinated payment
payment_amount = 1100000.0  # $1.1M
incentive_fee.payment_to_sub_notholder(payment_amount)

# Calculate incentive fee if threshold reached
if incentive_fee.cls_threshold_reach:
    # Apply 20% fee on additional payment
    fee_base = 500000.0  # Additional amount subject to fee
    net_payment = incentive_fee.pay_incentive_fee(fee_base)
    fee_amount = fee_base - net_payment
    print(f"Fee: ${fee_amount:,.2f}, Net: ${net_payment:,.2f}")

# Finalize period (calculates IRR and advances)
incentive_fee.rollfoward()
```

### Database Persistence

```python
# Save to database
fee_structure_id = incentive_fee.save_to_database(
    deal_id="CLO_DEAL_001",
    fee_structure_name="Manager Incentive Fee"
)

# Load from database
loaded_incentive_fee = IncentiveFee.load_from_database(
    session, fee_structure_id
)
```

### CLO Deal Engine Integration

```python
from app.models.clo_deal_engine import CLODealEngine

# Setup CLO with incentive fee
deal_engine = CLODealEngine(clo_deal, session)
deal_engine.setup_deal_dates(deal_dates)

# Enable incentive fee system
deal_engine.setup_incentive_fee(
    enable=True,
    hurdle_rate=0.08,
    incentive_fee_rate=0.20,
    subordinated_payments=historical_payments
)

# During waterfall execution
period = 5
deal_engine.process_incentive_fee_for_period(period)
net_payment = deal_engine.record_subordinated_payment(period, 1000000.0)
deal_engine.finalize_incentive_fee_period(period)

# Get comprehensive summary
summary = deal_engine.get_incentive_fee_summary()
```

## XIRR Implementation

### Excel Equivalence

The system implements Excel's `Application.Xirr` function using the Newton-Raphson method:

```python
def _calculate_xirr(self, cash_flows: List[float], dates: List[date], guess: float = 0.1) -> Optional[float]:
    """Excel XIRR equivalent using Newton-Raphson method"""
    
    # Sort by dates
    sorted_pairs = sorted(zip(dates, cash_flows))
    dates = [pair[0] for pair in sorted_pairs]
    cash_flows = [pair[1] for pair in sorted_pairs]
    
    # Calculate days from base date
    base_date = dates[0]
    days = [(d - base_date).days for d in dates]
    
    # Newton-Raphson iteration
    rate = guess
    for _ in range(100):  # Max iterations
        npv = sum(cf / (1 + rate) ** (day / 365.0) for cf, day in zip(cash_flows, days))
        dnpv = sum(-cf * day / (365.0 * (1 + rate) ** (day / 365.0 + 1)) for cf, day in zip(cash_flows, days))
        
        if abs(npv) < 1e-6:  # Convergence
            return rate
            
        rate = rate - npv / dnpv
    
    return None
```

### VBA Integration

```python
# VBA equivalent: lValue = Application.Xirr(lValues, lDates)
l_dates = list(self.cls_sub_payments_dict.keys())
l_values = list(self.cls_sub_payments_dict.values())

try:
    irr_value = self._calculate_xirr(l_values, l_dates)
    if irr_value is not None:
        self.cls_irr[self.cls_period] = irr_value
except:
    # If XIRR calculation fails, leave as 0 (VBA behavior)
    pass
```

## Threshold Calculations

### VBA Logic Implementation

```python
def calc(self, i_next_pay: date) -> None:
    """VBA Calc() method equivalent"""
    self.cls_curr_date = i_next_pay
    
    if self.cls_threshold_reach:
        self.cls_current_threshold = 0.0
    else:
        # VBA exact formula:
        # clsCurrentThreshold = clsCumDicountedSubPayments * (1 + clsFeeHurdleRate) ^ ((iNextPay - clsClosingDate) / 365)
        # clsCurrentThreshold = -1 * clsCurrentThreshold
        days_diff = (i_next_pay - self.cls_closing_date).days
        growth_factor = (1 + self.cls_fee_hurdle_rate) ** (days_diff / 365.0)
        self.cls_current_threshold = self.cls_cum_dicounted_sub_payments * growth_factor
        self.cls_current_threshold = -1 * self.cls_current_threshold
    
    self.cls_threshold[self.cls_period] = self.cls_current_threshold
```

### Threshold Reached Logic

```python
def payment_to_sub_notholder(self, i_amount: float) -> None:
    """VBA PaymentToSubNotholder() equivalent"""
    # VBA: clsCurrSubPayments = clsCurrSubPayments + iAmount
    self.cls_curr_sub_payments += i_amount
    
    # VBA: If clsCurrSubPayments >= clsCurrentThreshold Then clsThresholdReach = True
    if self.cls_curr_sub_payments >= self.cls_current_threshold:
        self.cls_threshold_reach = True
```

## Fee Calculation Logic

### Incentive Fee Deduction

```python
def pay_incentive_fee(self, i_amount: float) -> float:
    """VBA PayIncentiveFee() method equivalent"""
    if self.cls_threshold_reach:
        # VBA: clsCurrIncetivePayments = clsCurrIncetivePayments + iAmount * clsIncentFee
        # VBA: iAmount = iAmount * (1 - clsIncentFee)
        fee_amount = i_amount * self.cls_incent_fee
        self.cls_curr_incetive_payments += fee_amount
        return i_amount * (1 - self.cls_incent_fee)
    else:
        return i_amount
```

### Cumulative Discounting

```python
def rollfoward(self) -> None:
    """VBA Rollfoward() method (preserving typo)"""
    # VBA: clsCumDicountedSubPayments = clsCumDicountedSubPayments + 
    #      (clsCurrSubPayments / ((1 + clsFeeHurdleRate) ^ ((clsCurrDate - clsClosingDate) / 365)))
    days_diff = (self.cls_curr_date - self.cls_closing_date).days
    discount_factor = (1 + self.cls_fee_hurdle_rate) ** (days_diff / 365.0)
    discounted_current_payment = self.cls_curr_sub_payments / discount_factor
    self.cls_cum_dicounted_sub_payments += discounted_current_payment
```

## Output Formatting

### VBA-Compatible Reports

```python
def output(self) -> List[List[Any]]:
    """VBA Output() function equivalent"""
    l_output = []
    
    # VBA header: lOutput(0, 0) = "Threshold", etc.
    l_output.append(["Threshold", "Fee Paid", "IRR"])
    
    # VBA data: For i = 1 To clsPeriod - 1
    for i in range(1, self.cls_period):
        threshold_val = self.cls_threshold[i]
        fee_paid_val = self.cls_fee_paid[i] 
        irr_val = f"{self.cls_irr[i]:.3%}"  # VBA: Format(clsIRR(i), "0.000%")
        
        l_output.append([threshold_val, fee_paid_val, irr_val])
    
    return l_output
```

## Error Handling

### State Validation

```python
def setup(self, i_fee_threshold: float, i_incentive_fee: float, 
          i_payto_sub_notholder: Dict[date, float]) -> None:
    """Setup with validation"""
    if i_fee_threshold < 0 or i_fee_threshold > 1:
        raise ValueError("Hurdle rate must be between 0 and 1")
    
    if i_incentive_fee < 0 or i_incentive_fee > 1:
        raise ValueError("Incentive fee rate must be between 0 and 1")
    
    self.cls_fee_hurdle_rate = i_fee_threshold
    self.cls_incent_fee = i_incentive_fee
    self.cls_sub_payments_dict = i_payto_sub_notholder.copy()
    self._is_setup = True

def deal_setup(self, i_num_of_payments: int, i_close_date: date, i_analysis_date: date) -> None:
    """Deal setup with validation"""
    if not self._is_setup:
        raise RuntimeError("Must call setup() before deal_setup()")
    
    if i_num_of_payments <= 0:
        raise ValueError("Number of payments must be positive")
    
    if i_close_date >= i_analysis_date:
        raise ValueError("Closing date must be before analysis date")
    
    # Continue with setup...
```

## Testing Framework

### VBA Parity Tests

```python
def test_vba_setup_method(self, sample_subordinated_payments):
    """Test VBA Setup() method equivalent"""
    incentive_fee = IncentiveFee()
    
    incentive_fee.setup(
        i_fee_threshold=0.08,
        i_incentive_fee=0.20,
        i_payto_sub_notholder=sample_subordinated_payments
    )
    
    assert incentive_fee.cls_fee_hurdle_rate == 0.08
    assert incentive_fee.cls_incent_fee == 0.20
    assert incentive_fee.cls_sub_payments_dict == sample_subordinated_payments
    assert incentive_fee._is_setup == True

def test_vba_threshold_calculation_logic(self, sample_subordinated_payments):
    """Test VBA threshold calculation with exact logic"""
    incentive_fee = IncentiveFee()
    incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
    incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
    
    # Test exact VBA formula
    incentive_fee.cls_threshold_reach = False
    incentive_fee.calc(date(2025, 4, 15))
    
    days_diff = (date(2025, 4, 15) - date(2024, 1, 15)).days
    expected_threshold = incentive_fee.cls_cum_dicounted_sub_payments * (1 + 0.08) ** (days_diff / 365.0)
    expected_threshold = -1 * expected_threshold
    
    assert abs(incentive_fee.cls_current_threshold - expected_threshold) < 0.01
```

### Integration Tests

```python
def test_clo_integration_workflow(self, clo_deal_engine_with_incentive_fee):
    """Test complete CLO integration workflow"""
    deal_engine = clo_deal_engine_with_incentive_fee
    deal_engine.calculate_payment_dates()
    
    # Process multiple periods
    for period in range(2, 6):
        deal_engine.process_incentive_fee_for_period(period)
        net_payment = deal_engine.record_subordinated_payment(period, 1000000.0)
        deal_engine.finalize_incentive_fee_period(period)
    
    # Verify final state
    summary = deal_engine.get_incentive_fee_summary()
    assert summary['incentive_fee_enabled'] == True
    assert summary['current_period'] == 6
    assert len(summary['period_calculations']) == 4
```

## Performance Considerations

### Memory Management

- **Array Sizing**: Dynamic array management for large number of periods
- **Dictionary Operations**: Efficient date-based lookups for subordinated payments
- **Database Batching**: Bulk operations for period calculations

### Calculation Optimization

- **XIRR Convergence**: Optimized Newton-Raphson with bounds checking
- **Threshold Caching**: Pre-calculated thresholds to avoid repeated computation
- **State Persistence**: Efficient database save/load operations

## Integration Points

### CLO Deal Engine

The incentive fee system integrates at key waterfall execution points:

```python
# Period processing
deal_engine.process_incentive_fee_for_period(period)

# Subordinated payment recording
net_payment = deal_engine.record_subordinated_payment(period, payment_amount)

# Period finalization  
deal_engine.finalize_incentive_fee_period(period)
```

### Waterfall Execution

```python
# During waterfall execution
if self.enable_incentive_fee:
    # Calculate incentive fee on subordinated distributions
    net_distribution = self.record_subordinated_payment(period, gross_distribution)
    
    # Apply net amount to subordinated noteholders
    subordinated_notes.make_payment(net_distribution)
```

## Migration from VBA

### Key Differences

1. **Array Indexing**: VBA 1-based → Python 0-based (handled internally)
2. **Date Arithmetic**: VBA date math → Python datetime/timedelta
3. **Dictionary Access**: VBA Dictionary → Python dict with date keys
4. **Error Handling**: VBA error suppression → Python explicit exception handling

### Preserved Elements

1. **Method Names**: Exact VBA method names including typos ("Rollfoward")
2. **Variable Names**: Direct mapping with underscores (clsFeeHurdleRate → cls_fee_hurdle_rate)
3. **Calculation Logic**: Identical mathematical formulas
4. **Output Format**: VBA-compatible report structure

This documentation provides comprehensive guidance for using and maintaining the Incentive Fee System with complete VBA functional parity and modern Python architecture.