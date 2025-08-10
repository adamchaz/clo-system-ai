# CLO Waterfall Implementations Guide

## Overview

The CLO system supports multiple waterfall implementations to handle different deal structures, payment priorities, and market conditions. This guide explains the architecture and usage of various waterfall types.

## Waterfall Architecture

### Strategy Pattern Implementation

The system uses the Strategy pattern to handle different waterfall types:

```python
# Base strategy interface
class BaseWaterfallStrategy(ABC):
    @abstractmethod
    def get_payment_sequence(self) -> List[WaterfallStep]
    
    @abstractmethod  
    def check_payment_triggers(self, step, tranche) -> bool
    
    @abstractmethod
    def calculate_payment_amount(self, step, tranche) -> Decimal
```

### Factory Pattern for Creation

```python
# Create different waterfall types
calculator = EnhancedWaterfallCalculator(
    deal_id="DEAL-2023-1",
    payment_date=date(2023, 9, 15),
    session=session,
    waterfall_type=WaterfallType.TURBO
)
```

## Waterfall Types

### 1. Traditional Sequential Pay

**Characteristics:**
- Sequential principal payments (A → B → C → D)
- OC/IC test protection
- Standard expense and interest priorities

**Payment Sequence:**
```
1. Senior Expenses (Trustee, Admin, Sr Mgmt Fees)
2. Interest Payments (Class A → B → C → D)  
3. Reserve Account Funding
4. Principal Payments (Sequential, if tests pass)
5. Junior Fees
6. Subordinated Payments (Class E)
7. Residual to Equity
```

**Use Cases:**
- Standard US CLO structures
- Conservative payment profiles
- Regulatory compliance focus

### 2. Turbo Waterfall

**Characteristics:**
- Accelerated principal payments
- Principal payments before reserve funding
- Faster deleveraging

**Key Differences:**
```python
# Turbo sequence prioritizes principal
sequence = [
    WaterfallStep.TRUSTEE_FEES,
    WaterfallStep.CLASS_A_INTEREST,
    WaterfallStep.CLASS_A_PRINCIPAL,  # Earlier than traditional
    WaterfallStep.INTEREST_RESERVE    # After principal
]
```

**Use Cases:**
- Market volatility periods
- Fast amortization strategies
- Credit enhancement optimization

### 3. PIK Toggle Waterfall

**Characteristics:**
- Interest can be paid in cash or PIK'd
- Automatic PIK election based on cash availability
- Principal balance adjustments

**PIK Logic:**
```python
def calculate_payment_amount(self, step, tranche):
    if 'INTEREST' in step.value and self._is_pik_elected(tranche):
        # Add interest to principal balance
        tranche.current_balance += interest_due
        return Decimal('0')  # No cash payment
    
    return interest_due
```

**Use Cases:**
- Distressed market conditions
- Cash conservation strategies
- Covenant compliance maintenance

### 4. Equity Claw-Back Waterfall

**Characteristics:**
- Equity distributions held in escrow
- Performance hurdle requirements
- Conditional equity releases

**Claw-Back Logic:**
```python
def calculate_payment_amount(self, step, tranche):
    if step == WaterfallStep.RESIDUAL_EQUITY:
        if self._equity_hurdle_met():
            return self.calculator.available_cash
        else:
            # Hold in escrow account
            return Decimal('0')
```

**Use Cases:**
- Performance-based structures
- Manager incentive alignment
- Investor protection mechanisms

### 5. Call Protection Waterfall

**Characteristics:**
- Different logic during call protection period
- Principal payment restrictions
- Step-down provisions

**Phase-Based Logic:**
```python
def check_payment_triggers(self, step, tranche):
    phase = self.get_payment_phase()
    
    if phase == PaymentPhase.CALL_PROTECTION and 'PRINCIPAL' in step.value:
        return self._call_protection_allows_principal_payment(tranche)
```

**Use Cases:**
- Non-call periods
- Investor yield protection  
- Market timing strategies

## Configuration System

### Template-Based Configuration

```python
# Create waterfall template
template = WaterfallTemplate(
    template_name="Standard US CLO",
    waterfall_type=WaterfallType.TRADITIONAL,
    default_config={
        "senior_mgmt_fee_rate": 0.004,
        "interest_reserve_target": 5000000
    }
)
```

### Custom Payment Rules

```python
# Define custom payment rule
rule = PaymentRule(
    step_name=WaterfallStep.CLASS_A_INTEREST.value,
    payment_formula="tranche_balance * coupon_rate / 4",
    payment_cap=Decimal('5000000'),
    trigger_conditions=["OC_TEST_PASS", "IC_TEST_PASS"]
)
```

### Dynamic Modifications

```python
# Temporary waterfall modification
modification = WaterfallModification(
    modification_type="AMENDMENT",
    modification_name="Fee Reduction Amendment",
    modification_rules={
        "payment_rules": [{
            "step_name": "SENIOR_MGMT_FEES",
            "payment_formula": "collateral_balance * 0.002 / 4"
        }]
    },
    effective_date=date(2023, 9, 15),
    expiration_date=date(2024, 3, 15)
)
```

### Payment Overrides

```python
# One-time payment override
override = PaymentOverride(
    payment_date=date(2023, 9, 15),
    step_name=WaterfallStep.CLASS_A_INTEREST.value,
    override_type="AMOUNT",
    override_amount=Decimal('2000000'),
    override_reason="Noteholder-requested adjustment"
)
```

## Implementation Examples

### Creating Custom Waterfall

```python
class CustomWaterfall(BaseWaterfallStrategy):
    def get_payment_sequence(self):
        return [
            WaterfallStep.TRUSTEE_FEES,
            WaterfallStep.CLASS_E_INTEREST,  # Pay subordinated first
            WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.CLASS_A_PRINCIPAL
        ]
    
    def check_payment_triggers(self, step, tranche):
        # Custom trigger logic
        if step == WaterfallStep.CLASS_E_INTEREST:
            return self._special_condition_met()
        return super().check_payment_triggers(step, tranche)

# Register custom strategy
WaterfallStrategyFactory.register_custom_strategy(
    WaterfallType.CUSTOM, CustomWaterfall
)
```

### Configuration Hierarchy

The system processes configurations in this order:

1. **Base Configuration** - Deal-specific waterfall settings
2. **Active Modifications** - Amendments and temporary changes  
3. **Payment Overrides** - Specific date adjustments

```python
# Configuration loading with hierarchy
calculator = ConfigurableWaterfallCalculator(
    deal_id="DEAL-2023-1",
    payment_date=date(2023, 9, 15),
    session=session
)

# Final configuration includes all layers
effective_config = calculator.effective_config
```

## Testing Framework

### Strategy Testing

```python
def test_turbo_waterfall():
    calculator = EnhancedWaterfallCalculator(
        waterfall_type=WaterfallType.TURBO
    )
    
    execution = calculator.execute_waterfall(Decimal('20000000'))
    
    # Verify turbo behavior
    principal_payments = [p for p in execution.payments 
                         if 'PRINCIPAL' in p.payment_step]
    
    assert len(principal_payments) > 0
    assert sum(p.amount_paid for p in principal_payments) > threshold
```

### Configuration Testing

```python
def test_configuration_hierarchy():
    # Base config + modification + override
    calculator = ConfigurableWaterfallCalculator(...)
    
    trustee_rule = calculator.get_payment_rules_for_step("TRUSTEE_FEES")
    
    # Override should take precedence
    assert trustee_rule['override_amount'] == expected_amount
```

## Database Schema

### Configuration Tables

```sql
-- Template definitions
waterfall_templates (template_name, waterfall_type, default_config)

-- Deal-specific rules  
payment_rules (step_name, payment_formula, trigger_conditions)

-- Temporary changes
waterfall_modifications (modification_type, modification_rules, effective_date)

-- One-time adjustments
payment_overrides (payment_date, step_name, override_type, override_amount)
```

### Execution Tables

```sql
-- Waterfall execution records
waterfall_executions (deal_id, payment_date, collection_amount, remaining_cash)

-- Individual payment details  
waterfall_payments (execution_id, payment_step, amount_due, amount_paid)
```

## Best Practices

### Waterfall Selection

1. **Traditional** - Standard deals, regulatory compliance
2. **Turbo** - Market stress, fast deleveraging  
3. **PIK Toggle** - Distressed assets, covenant management
4. **Custom** - Unique deal structures

### Configuration Management

1. **Use Templates** - Start with proven configurations
2. **Version Control** - Track all modifications
3. **Test Thoroughly** - Validate payment logic
4. **Document Changes** - Clear modification rationale

### Performance Optimization

1. **Cache Configurations** - Avoid repeated database queries
2. **Batch Processing** - Group payment calculations
3. **Parallel Execution** - Process multiple deals simultaneously
4. **Memory Management** - Clean up large calculation objects

## Integration Points

### Asset Cash Flows → Waterfall
```python
# Collection period aggregation
collections = asset_service.get_period_collections(deal_id, start_date, end_date)
execution = waterfall_calculator.execute_waterfall(collections.total)
```

### CLO Deal Engine Integration
```python
# Deal engine orchestrates waterfall execution
engine = CLODealEngine(deal, session)
engine.setup_waterfall_strategy(waterfall_strategy)

# Period-by-period execution
engine.execute_deal_calculation()

# Waterfall automatically called for each period
for period in range(1, len(engine.payment_dates) + 1):
    engine._execute_interest_waterfall(period)
    engine._execute_principal_waterfall(period, max_reinvestment)
```

### Liability Integration
```python
# Liability calculations feed into waterfall
for name, calculator in engine.liability_calculators.items():
    calculator.calculate_period(period, libor_rate, last_pay, next_pay)

# Interest due amounts used in waterfall sequence
liability_interest = calculator.get_interest_due(period)
waterfall_strategy.process_interest_payment(liability_interest)
```

### Compliance Tests → Triggers
```python
# Test results influence payment triggers
oc_results = compliance_service.run_oc_tests(deal_id, payment_date)
ic_results = compliance_service.run_ic_tests(deal_id, payment_date)

context = {
    'oc_tests_pass': oc_results.all_pass,
    'ic_tests_pass': ic_results.all_pass
}

# Trigger evaluation uses test results
rule.evaluate_triggers(context)
```

## Magnetar Waterfall Implementation

### Magnetar (Mag 6-17) Waterfall System ✅

The system includes comprehensive support for all Magnetar CLO waterfall variations (Mag 6 through Mag 17) with sophisticated performance-based features:

```python
# Create Magnetar waterfall strategy
mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_17)

# Execute with all advanced features
execution = calculator.execute_waterfall(collection_amount)
```

#### Magnetar Features by Version

| Version | Key Features | Hurdle Rate | Advanced Features |
|---------|-------------|-------------|-------------------|
| Mag 6-7 | Basic turbo principal | 8% | Turbo acceleration |
| Mag 8-9 | + Equity claw-back | 10% | Performance hurdles |
| Mag 10-11 | + Fee deferral | 11% | Management deferrals |
| Mag 12-13 | + Fee sharing | 11.5% | Incentive allocations |
| Mag 14 | + Reinvestment overlay | 12% | Additional fees |
| Mag 15 | + Performance hurdles | 12.5% | IRR-based triggers |
| Mag 16 | + Distribution stopper | 13% | Covenant blockers |
| Mag 17 | + All features | 15% | Complete feature set |

#### Performance-Based Features

**Equity Claw-Back Provisions:**
```python
# Distributions held until hurdle achievement
if not self._performance_hurdle_met():
    return Decimal('0')  # Hold distributions in escrow

# Apply catch-up when hurdle exceeded  
catch_up_rate = self.mag_config.equity_catch_up_rate
return base_distribution * catch_up_rate
```

**Turbo Principal Acceleration:**
```python
# Accelerate principal when OC/IC ratios exceed thresholds
if self._turbo_conditions_met():
    # Move principal payments earlier in sequence
    modified_sequence = self._apply_turbo_modifications(base_sequence)
```

**Management Fee Deferral:**
```python
# Defer fees when equity performance below minimum
if current_equity_irr < minimum_equity_irr:
    # Move management fees later in payment sequence
    deferred_sequence = self._apply_fee_deferral(base_sequence)
```

#### Magnetar Configuration Factory

```python
# Version-specific configuration creation
config = MagWaterfallFactory.create_mag_config(
    deal_id="MAG-17-DEAL",
    mag_version=MagWaterfallType.MAG_17,
    equity_hurdle_rate=Decimal('0.15'),  # 15% hurdle
    management_fee_sharing_pct=Decimal('0.80')  # 80% sharing
)

# Automatic feature enablement by version
features = config.get_enabled_features()
# Returns: ['TURBO_PRINCIPAL', 'EQUITY_CLAW_BACK', 'MANAGEMENT_FEE_DEFERRAL', 
#           'INCENTIVE_FEE_SHARING', 'REINVESTMENT_OVERLAY', 'PERFORMANCE_HURDLE',
#           'DISTRIBUTION_STOPPER', 'CALL_PROTECTION_OVERRIDE', 'EXCESS_SPREAD_CAPTURE']
```

#### Performance Metrics Integration

```python
# Track equity performance for decision making
metrics = MagPerformanceMetrics(
    deal_id=deal_id,
    calculation_date=payment_date,
    equity_irr=Decimal('0.16'),        # 16% annualized IRR
    equity_moic=Decimal('1.35'),       # 135% multiple of invested capital
    oc_test_buffer=Decimal('0.12'),    # 12% overcollateralization buffer
    ic_test_buffer=Decimal('0.18')     # 18% interest coverage buffer
)
```

#### Testing Coverage

- **46 comprehensive tests** covering all Mag versions
- **Version-specific feature validation** for Mag 6-17
- **Performance scenario testing** (stressed and strong markets)
- **Integration testing** with dynamic waterfall system
- **Factory pattern validation** for configuration management

## CLO Deal Engine Architecture

### Master Orchestration
The CLO Deal Engine serves as the master orchestrator for all waterfall operations:

```python
class CLODealEngine:
    """Master orchestration engine coordinating entire deal lifecycle"""
    
    def execute_deal_calculation(self):
        """Main calculation workflow with waterfall integration"""
        for period in range(1, len(self.payment_dates) + 1):
            # Calculate period cash flows
            self.calculate_period(period, liquidate_flag)
            
            # Execute waterfall payments
            if self._is_event_of_default():
                self._execute_eod_waterfall(period)
            else:
                self._execute_interest_waterfall(period)
                max_reinvestment = self.calculate_reinvestment_amount(period)
                self._execute_principal_waterfall(period, max_reinvestment)
```

### Component Coordination
```python
# Engine coordinates all CLO components
engine.setup_liabilities(liability_dict)           # Interest calculations
engine.setup_accounts()                            # Cash management
engine.setup_waterfall_strategy(waterfall_strategy) # Payment logic
engine.setup_reinvestment_info(reinvestment_info)  # Reinvestment rules

# Seamless integration across all systems
engine.execute_deal_calculation()
```

### Testing Integration
With 76+ comprehensive tests covering:
- **Deal Engine Tests** (20+ tests) - Master orchestration functionality
- **Liability Tests** (10+ tests) - Interest calculations and risk measures  
- **Magnetar Tests** (46 tests) - All performance-based waterfall features

This architecture provides flexibility to handle various CLO structures while maintaining consistency and auditability across all waterfall implementations, including sophisticated Magnetar structures with performance-based modifications, all coordinated through the comprehensive CLO Deal Engine system.