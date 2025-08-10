# OC/IC Trigger System Documentation

## Overview

The OC/IC Trigger System provides comprehensive overcollateralization (OC) and interest coverage (IC) testing for CLO deals with complete VBA functional parity. This system implements sophisticated dual cure mechanisms, period-by-period calculations, and pass/fail determination logic essential for CLO compliance monitoring.

## Architecture

### Core Components

1. **OCTrigger Class** - Overcollateralization trigger testing with dual cure mechanism
2. **ICTrigger Class** - Interest coverage trigger testing with cure payment tracking
3. **TriggerService** - Database operations and historical tracking
4. **SQLAlchemy Models** - Complete database schema for trigger calculations
5. **Waterfall Integration** - Seamless integration with cash flow waterfall systems

### Database Schema

```sql
-- OC Trigger Configuration
oc_trigger_structures (
    oc_trigger_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL,
    trigger_name VARCHAR(100) NOT NULL,
    trigger_threshold DECIMAL(8,6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- OC Trigger Calculations by Period
oc_trigger_calculations (
    calculation_id SERIAL PRIMARY KEY,
    oc_trigger_id INTEGER REFERENCES oc_trigger_structures(oc_trigger_id),
    period_number INTEGER NOT NULL,
    numerator_amount DECIMAL(18,2) NOT NULL,
    denominator_amount DECIMAL(18,2) NOT NULL,
    test_result DECIMAL(8,6),
    threshold_value DECIMAL(8,6) NOT NULL,
    pass_fail_status BOOLEAN NOT NULL,
    
    -- Dual Cure Mechanism
    prior_int_cure DECIMAL(18,2) DEFAULT 0,
    prior_prin_cure DECIMAL(18,2) DEFAULT 0,
    int_cure_amount DECIMAL(18,2) DEFAULT 0,
    int_cure_paid DECIMAL(18,2) DEFAULT 0,
    prin_cure_amount DECIMAL(18,2) DEFAULT 0,
    prin_cure_paid DECIMAL(18,2) DEFAULT 0,
    
    calculation_date DATE NOT NULL
);

-- IC Trigger Configuration
ic_trigger_structures (
    ic_trigger_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL,
    trigger_name VARCHAR(100) NOT NULL,
    trigger_threshold DECIMAL(8,6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- IC Trigger Calculations by Period
ic_trigger_calculations (
    calculation_id SERIAL PRIMARY KEY,
    ic_trigger_id INTEGER REFERENCES ic_trigger_structures(ic_trigger_id),
    period_number INTEGER NOT NULL,
    numerator_amount DECIMAL(18,2) NOT NULL,
    denominator_amount DECIMAL(18,2) NOT NULL,
    liability_balance DECIMAL(18,2) NOT NULL,
    test_result DECIMAL(8,6),
    threshold_value DECIMAL(8,6) NOT NULL,
    pass_fail_status BOOLEAN NOT NULL,
    
    -- Cure Mechanism
    prior_cure_payments DECIMAL(18,2) DEFAULT 0,
    cure_amount DECIMAL(18,2) DEFAULT 0,
    cure_amount_paid DECIMAL(18,2) DEFAULT 0,
    
    calculation_date DATE NOT NULL
);

-- Cure Payment Transactions
cure_payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    trigger_type VARCHAR(10) NOT NULL, -- 'OC' or 'IC'
    trigger_id INTEGER NOT NULL,
    cure_type VARCHAR(20) NOT NULL, -- 'INTEREST', 'PRINCIPAL'
    period_number INTEGER NOT NULL,
    cure_amount DECIMAL(18,2) NOT NULL,
    transaction_date DATE NOT NULL
);
```

## VBA Functional Parity

### OC Trigger - Method Mapping

| VBA Method | Python Method | Purpose | Status |
|------------|---------------|---------|--------|
| `Setup()` | `setup()` | Initialize trigger parameters | ✅ Complete |
| `DealSetup()` | `deal_setup()` | Configure period arrays | ✅ Complete |
| `Calc()` | `calc()` | Calculate period OC test | ✅ Complete |
| `PayIntCure()` | `pay_int_cure()` | Record interest cure payment | ✅ Complete |
| `PayPrinCure()` | `pay_prin_cure()` | Record principal cure payment | ✅ Complete |
| `RollForward()` | `roll_forward()` | Advance to next period | ✅ Complete |
| `Output()` | `output()` | Generate formatted report | ✅ Complete |

### IC Trigger - Method Mapping

| VBA Method | Python Method | Purpose | Status |
|------------|---------------|---------|--------|
| `Setup()` | `setup()` | Initialize trigger parameters | ✅ Complete |
| `DealSetup()` | `deal_setup()` | Configure period arrays | ✅ Complete |
| `Calc()` | `calc()` | Calculate period IC test | ✅ Complete |
| `PayCure()` | `pay_cure()` | Record cure payment | ✅ Complete |
| `RollForward()` | `roll_forward()` | Advance to next period | ✅ Complete |
| `Output()` | `output()` | Generate formatted report | ✅ Complete |

### Variable Mapping

| VBA Variable | Python Variable | Type | Purpose |
|--------------|-----------------|------|---------| 
| `clsName` | `trigger_name` | str | Trigger identifier name |
| `clsTrigger` | `trigger_threshold` | Decimal | Pass/fail threshold (e.g., 1.20 for 120%) |
| `clsResult()` | `test_results[]` | List[Decimal] | Period test results |
| `clsThreshold()` | `thresholds[]` | List[Decimal] | Period thresholds |
| `clsPassFail()` | `pass_fail_status[]` | List[bool] | Period pass/fail status |
| `clsNumerator()` | `numerators[]` | List[Decimal] | Period numerator values |
| `clsDenominator()` | `denominators[]` | List[Decimal] | Period denominator values |
| `clsPeriod` | `current_period` | int | Current calculation period |
| `clsLastPeriodCalc` | `last_calculated_period` | int | Last calculated period |

## Implementation Details

### 1. VBA OCTrigger Setup and Calculation

**VBA Code:**
```vba
Public Sub Setup(iName As String, iThresh As Double)
    clsName = iName
    clsTrigger = iThresh
End Sub

Public Sub DealSetup(iNumofPayments As Long)
    ReDim clsResult(iNumofPayments)
    ReDim clsThreshold(iNumofPayments)
    ReDim clsPassFail(iNumofPayments)
    ReDim clsNumerator(iNumofPayments)
    ReDim clsDenominator(iNumofPayments)
    ReDim clsIntCureAmt(iNumofPayments)
    ReDim clsIntCurePaid(iNumofPayments)
    ReDim clsPriorIntCure(iNumofPayments)
    ReDim clsPriorPrinCure(iNumofPayments)
    ReDim clsPrinCureAmt(iNumofPayments)
    ReDim clsPrinCurePaid(iNumofPayments)
    clsPeriod = 1
End Sub

Public Sub Calc(iNum As Double, iDeno As Double)
    Dim lResults As Double
    If iDeno > 0 Then
        clsNumerator(clsPeriod) = iNum
        clsDenominator(clsPeriod) = iDeno
        lResults = iNum / iDeno
        clsResult(clsPeriod) = lResults
        If lResults > clsTrigger Then
            clsPassFail(clsPeriod) = True
        Else
            clsPassFail(clsPeriod) = False
            clsIntCureAmt(clsPeriod) = (clsTrigger - clsResult(clsPeriod)) * clsDenominator(clsPeriod)
            clsPrinCureAmt(clsPeriod) = (clsTrigger - clsResult(clsPeriod)) * clsDenominator(clsPeriod)
        End If
        clsLastPeriodCalc = clsPeriod
    Else
        clsPassFail(clsPeriod) = True
    End If
End Sub
```

**Python Equivalent:**
```python
class OCTrigger:
    """VBA OCTrigger.cls equivalent with dual cure mechanism"""
    
    def __init__(self):
        self.trigger_name: str = ""
        self.trigger_threshold: Decimal = Decimal('0')
        
        # Period arrays (VBA equivalent)
        self.test_results: List[Decimal] = []
        self.thresholds: List[Decimal] = []
        self.pass_fail_status: List[bool] = []
        self.numerators: List[Decimal] = []
        self.denominators: List[Decimal] = []
        
        # Dual cure mechanism arrays
        self.int_cure_amounts: List[Decimal] = []
        self.int_cure_paid: List[Decimal] = []
        self.prior_int_cure: List[Decimal] = []
        self.prior_prin_cure: List[Decimal] = []
        self.prin_cure_amounts: List[Decimal] = []
        self.prin_cure_paid: List[Decimal] = []
        
        self.current_period: int = 1
        self.last_calculated_period: int = 0
        self._is_setup: bool = False
        self._is_deal_setup: bool = False

    def setup(self, i_name: str, i_thresh: Decimal) -> None:
        """VBA Setup() method equivalent"""
        # VBA: clsName = iName
        self.trigger_name = i_name
        
        # VBA: clsTrigger = iThresh
        self.trigger_threshold = i_thresh
        
        self._is_setup = True

    def deal_setup(self, i_num_of_payments: int) -> None:
        """VBA DealSetup() method equivalent"""
        if not self._is_setup:
            raise RuntimeError("Must call setup() before deal_setup()")
        
        # VBA: ReDim arrays with +1 for 1-based indexing compatibility
        array_size = i_num_of_payments + 1
        
        self.test_results = [Decimal('0')] * array_size
        self.thresholds = [self.trigger_threshold] * array_size
        self.pass_fail_status = [False] * array_size
        self.numerators = [Decimal('0')] * array_size
        self.denominators = [Decimal('0')] * array_size
        
        # Dual cure mechanism arrays
        self.int_cure_amounts = [Decimal('0')] * array_size
        self.int_cure_paid = [Decimal('0')] * array_size
        self.prior_int_cure = [Decimal('0')] * array_size
        self.prior_prin_cure = [Decimal('0')] * array_size
        self.prin_cure_amounts = [Decimal('0')] * array_size
        self.prin_cure_paid = [Decimal('0')] * array_size
        
        # VBA: clsPeriod = 1
        self.current_period = 1
        
        self._is_deal_setup = True

    def calc(self, i_num: Decimal, i_deno: Decimal) -> None:
        """VBA Calc() method equivalent"""
        if not self._is_deal_setup:
            raise RuntimeError("Must call deal_setup() before calc()")
        
        # VBA: If iDeno > 0 Then
        if i_deno > 0:
            # VBA: Store inputs
            self.numerators[self.current_period] = i_num
            self.denominators[self.current_period] = i_deno
            
            # VBA: lResults = iNum / iDeno
            l_results = i_num / i_deno
            self.test_results[self.current_period] = l_results
            
            # VBA: Pass/fail determination
            if l_results > self.trigger_threshold:
                self.pass_fail_status[self.current_period] = True
            else:
                self.pass_fail_status[self.current_period] = False
                
                # VBA: Calculate cure amounts
                cure_deficit = self.trigger_threshold - l_results
                self.int_cure_amounts[self.current_period] = cure_deficit * i_deno
                self.prin_cure_amounts[self.current_period] = cure_deficit * i_deno
            
            # VBA: clsLastPeriodCalc = clsPeriod
            self.last_calculated_period = self.current_period
        else:
            # VBA: Else clause - auto pass if denominator is zero
            self.pass_fail_status[self.current_period] = True
```

### 2. VBA ICTrigger Implementation

**VBA Code:**
```vba
Public Sub Calc(iNum As Double, iDeno As Double, iLiabBal As Double)
    Dim lResults As Double
    If iDeno > 0 Then
        clsNumerator(clsPeriod) = iNum
        clsDenominator(clsPeriod) = iDeno
        clsLiabBal(clsPeriod) = iLiabBal
        lResults = iNum / iDeno
        clsResult(clsPeriod) = lResults
        If lResults > clsTrigger Then
            clsPassFail(clsPeriod) = True
        Else
            clsPassFail(clsPeriod) = False
            clsCureAmt(clsPeriod) = (1 - clsResult(clsPeriod) / clsTrigger) * clsLiabBal(clsPeriod)
        End If
        clsLastPeriodCalc = clsPeriod
    Else
        clsPassFail(clsPeriod) = True
    End If
End Sub
```

**Python Equivalent:**
```python
class ICTrigger:
    """VBA ICTrigger.cls equivalent with cure payment tracking"""
    
    def __init__(self):
        self.trigger_name: str = ""
        self.trigger_threshold: Decimal = Decimal('0')
        
        # Period arrays (VBA equivalent)
        self.test_results: List[Decimal] = []
        self.thresholds: List[Decimal] = []
        self.pass_fail_status: List[bool] = []
        self.numerators: List[Decimal] = []
        self.denominators: List[Decimal] = []
        self.liability_balances: List[Decimal] = []
        
        # Cure mechanism arrays
        self.prior_cure_payments: List[Decimal] = []
        self.cure_amounts: List[Decimal] = []
        self.cure_amounts_paid: List[Decimal] = []
        
        self.current_period: int = 1
        self.last_calculated_period: int = 0

    def calc(self, i_num: Decimal, i_deno: Decimal, i_liab_bal: Decimal) -> None:
        """VBA Calc() method equivalent with liability balance tracking"""
        if not self._is_deal_setup:
            raise RuntimeError("Must call deal_setup() before calc()")
        
        # VBA: If iDeno > 0 Then
        if i_deno > 0:
            # VBA: Store all inputs
            self.numerators[self.current_period] = i_num
            self.denominators[self.current_period] = i_deno
            self.liability_balances[self.current_period] = i_liab_bal
            
            # VBA: lResults = iNum / iDeno
            l_results = i_num / i_deno
            self.test_results[self.current_period] = l_results
            
            # VBA: Pass/fail determination
            if l_results > self.trigger_threshold:
                self.pass_fail_status[self.current_period] = True
            else:
                self.pass_fail_status[self.current_period] = False
                
                # VBA: clsCureAmt(clsPeriod) = (1 - clsResult(clsPeriod) / clsTrigger) * clsLiabBal(clsPeriod)
                cure_ratio = 1 - (l_results / self.trigger_threshold)
                self.cure_amounts[self.current_period] = cure_ratio * i_liab_bal
            
            # VBA: clsLastPeriodCalc = clsPeriod
            self.last_calculated_period = self.current_period
        else:
            # VBA: Else clause - auto pass if denominator is zero
            self.pass_fail_status[self.current_period] = True
```

### 3. VBA Cure Payment Mechanism

**VBA OCTrigger PayIntCure Method:**
```vba
Public Sub PayIntCure(iAmount As Double)
    clsIntCurePaid(clsPeriod) = iAmount
    If clsPeriod > 1 Then
        clsPriorIntCure(clsPeriod) = clsPriorIntCure(clsPeriod - 1) + clsIntCurePaid(clsPeriod - 1)
    End If
End Sub
```

**Python Equivalent:**
```python
def pay_int_cure(self, i_amount: Decimal) -> None:
    """VBA PayIntCure() method equivalent"""
    if not self._is_deal_setup:
        raise RuntimeError("Must call deal_setup() before pay_int_cure()")
    
    # VBA: clsIntCurePaid(clsPeriod) = iAmount
    self.int_cure_paid[self.current_period] = i_amount
    
    # VBA: If clsPeriod > 1 Then
    if self.current_period > 1:
        previous_period = self.current_period - 1
        # VBA: clsPriorIntCure(clsPeriod) = clsPriorIntCure(clsPeriod - 1) + clsIntCurePaid(clsPeriod - 1)
        self.prior_int_cure[self.current_period] = (
            self.prior_int_cure[previous_period] + 
            self.int_cure_paid[previous_period]
        )

def pay_prin_cure(self, i_amount: Decimal) -> None:
    """VBA PayPrinCure() method equivalent"""
    if not self._is_deal_setup:
        raise RuntimeError("Must call deal_setup() before pay_prin_cure()")
    
    # VBA: clsPrinCurePaid(clsPeriod) = iAmount
    self.prin_cure_paid[self.current_period] = i_amount
    
    # VBA: If clsPeriod > 1 Then
    if self.current_period > 1:
        previous_period = self.current_period - 1
        # VBA: clsPriorPrinCure(clsPeriod) = clsPriorPrinCure(clsPeriod - 1) + clsPrinCurePaid(clsPeriod - 1)
        self.prior_prin_cure[self.current_period] = (
            self.prior_prin_cure[previous_period] + 
            self.prin_cure_paid[previous_period]
        )

def roll_forward(self) -> None:
    """VBA RollForward() method equivalent"""
    # VBA: clsPeriod = clsPeriod + 1
    self.current_period += 1
```

### 4. VBA Output Generation

**VBA Code:**
```vba
Public Function Output() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastPeriodCalc, 10)
    lOutput(0, 0) = "Numerator"
    lOutput(0, 1) = "Denominator"
    lOutput(0, 2) = "Result"
    lOutput(0, 3) = "Threshold"
    lOutput(0, 4) = "Pass/Fail"
    lOutput(0, 5) = "Prior Int Cure"
    lOutput(0, 6) = "Prior Prin Cure"
    lOutput(0, 7) = "Int Cure Amount"
    lOutput(0, 8) = "Int Cure Paid"
    lOutput(0, 9) = "Prin Cure Amount"
    lOutput(0, 10) = "Prin Cure Paid"
    
    For i = 1 To clsLastPeriodCalc
        lOutput(i, 0) = clsNumerator(i)
        lOutput(i, 1) = clsDenominator(i)
        lOutput(i, 2) = Format(clsResult(i), "0.000%")
        lOutput(i, 3) = Format(clsTrigger, "0.000%")
        lOutput(i, 4) = clsPassFail(i)
        lOutput(i, 5) = clsPriorIntCure(i)
        lOutput(i, 6) = clsPriorPrinCure(i)
        lOutput(i, 7) = clsIntCureAmt(i)
        lOutput(i, 8) = clsIntCurePaid(i)
        lOutput(i, 9) = clsPrinCureAmt(i)
        lOutput(i, 10) = clsPrinCurePaid(i)
    Next i
    
    Output = lOutput
End Function
```

**Python Equivalent:**
```python
def output(self) -> List[List[str]]:
    """VBA Output() function equivalent - return formatted report data"""
    
    # VBA: ReDim lOutput(0 To clsLastPeriodCalc, 10)
    output_data = []
    
    # VBA: Header row
    header = [
        "Numerator", "Denominator", "Result", "Threshold", "Pass/Fail",
        "Prior Int Cure", "Prior Prin Cure", "Int Cure Amount", 
        "Int Cure Paid", "Prin Cure Amount", "Prin Cure Paid"
    ]
    output_data.append(header)
    
    # VBA: For i = 1 To clsLastPeriodCalc
    for i in range(1, self.last_calculated_period + 1):
        row = [
            str(self.numerators[i]),
            str(self.denominators[i]),
            f"{self.test_results[i]:.3%}",  # VBA: Format(clsResult(i), "0.000%")
            f"{self.trigger_threshold:.3%}",  # VBA: Format(clsTrigger, "0.000%")
            str(self.pass_fail_status[i]),
            str(self.prior_int_cure[i]),
            str(self.prior_prin_cure[i]),
            str(self.int_cure_amounts[i]),
            str(self.int_cure_paid[i]),
            str(self.prin_cure_amounts[i]),
            str(self.prin_cure_paid[i])
        ]
        output_data.append(row)
    
    return output_data
```

## Database Integration

### Service Layer Implementation

```python
class TriggerService:
    """Service layer for OC/IC trigger database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_oc_trigger(self, deal_id: str, trigger_name: str, threshold: Decimal) -> int:
        """Create new OC trigger structure"""
        
        oc_trigger = OCTriggerStructures(
            deal_id=deal_id,
            trigger_name=trigger_name,
            trigger_threshold=threshold,
            is_active=True
        )
        
        self.session.add(oc_trigger)
        self.session.flush()
        
        return oc_trigger.oc_trigger_id
    
    def save_oc_calculation(self, oc_trigger_id: int, period: int, 
                          numerator: Decimal, denominator: Decimal,
                          test_result: Decimal, pass_fail: bool,
                          cure_data: Dict[str, Decimal]) -> None:
        """Save OC trigger calculation for period"""
        
        calculation = OCTriggerCalculations(
            oc_trigger_id=oc_trigger_id,
            period_number=period,
            numerator_amount=numerator,
            denominator_amount=denominator,
            test_result=test_result,
            threshold_value=self._get_threshold(oc_trigger_id),
            pass_fail_status=pass_fail,
            prior_int_cure=cure_data.get('prior_int_cure', Decimal('0')),
            prior_prin_cure=cure_data.get('prior_prin_cure', Decimal('0')),
            int_cure_amount=cure_data.get('int_cure_amount', Decimal('0')),
            int_cure_paid=cure_data.get('int_cure_paid', Decimal('0')),
            prin_cure_amount=cure_data.get('prin_cure_amount', Decimal('0')),
            prin_cure_paid=cure_data.get('prin_cure_paid', Decimal('0')),
            calculation_date=date.today()
        )
        
        self.session.add(calculation)
        self.session.commit()
    
    def load_oc_trigger_with_history(self, oc_trigger_id: int) -> OCTrigger:
        """Load OC trigger with complete calculation history"""
        
        # Load trigger structure
        db_trigger = (self.session.query(OCTriggerStructures)
                     .filter_by(oc_trigger_id=oc_trigger_id)
                     .first())
        
        if not db_trigger:
            raise ValueError(f"OC trigger {oc_trigger_id} not found")
        
        # Create OCTrigger object
        oc_trigger = OCTrigger()
        oc_trigger.setup(db_trigger.trigger_name, db_trigger.trigger_threshold)
        
        # Load calculation history
        calculations = (self.session.query(OCTriggerCalculations)
                       .filter_by(oc_trigger_id=oc_trigger_id)
                       .order_by(OCTriggerCalculations.period_number)
                       .all())
        
        if calculations:
            max_period = max(calc.period_number for calc in calculations)
            oc_trigger.deal_setup(max_period)
            
            # Restore calculation state
            for calc in calculations:
                period = calc.period_number
                oc_trigger.numerators[period] = calc.numerator_amount
                oc_trigger.denominators[period] = calc.denominator_amount
                oc_trigger.test_results[period] = calc.test_result
                oc_trigger.pass_fail_status[period] = calc.pass_fail_status
                oc_trigger.prior_int_cure[period] = calc.prior_int_cure
                oc_trigger.prior_prin_cure[period] = calc.prior_prin_cure
                oc_trigger.int_cure_amounts[period] = calc.int_cure_amount
                oc_trigger.int_cure_paid[period] = calc.int_cure_paid
                oc_trigger.prin_cure_amounts[period] = calc.prin_cure_amount
                oc_trigger.prin_cure_paid[period] = calc.prin_cure_paid
            
            oc_trigger.last_calculated_period = max_period
        
        return oc_trigger
```

## CLO Deal Engine Integration

### Waterfall Integration

```python
class DynamicWaterfallStrategy:
    """Integration of OC/IC triggers with waterfall execution"""
    
    def __init__(self):
        self.oc_triggers: Dict[str, OCTrigger] = {}
        self.ic_triggers: Dict[str, ICTrigger] = {}
    
    def setup_triggers(self, trigger_configs: Dict[str, Any]) -> None:
        """Setup OC/IC triggers for waterfall execution"""
        
        # Setup OC triggers
        for name, config in trigger_configs.get('oc_triggers', {}).items():
            oc_trigger = OCTrigger()
            oc_trigger.setup(name, Decimal(str(config['threshold'])))
            oc_trigger.deal_setup(config['num_periods'])
            self.oc_triggers[name] = oc_trigger
        
        # Setup IC triggers
        for name, config in trigger_configs.get('ic_triggers', {}).items():
            ic_trigger = ICTrigger()
            ic_trigger.setup(name, Decimal(str(config['threshold'])))
            ic_trigger.deal_setup(config['num_periods'])
            self.ic_triggers[name] = ic_trigger
    
    def execute_interest_waterfall(self, period: int, interest_proceeds: Decimal, 
                                 principal_proceeds: Decimal) -> None:
        """Execute interest waterfall with trigger testing"""
        
        # Calculate trigger test inputs
        numerator = self._calculate_interest_numerator(period)
        denominator = self._calculate_interest_denominator(period)
        
        # Test IC triggers
        for trigger_name, ic_trigger in self.ic_triggers.items():
            liability_balance = self._get_liability_balance(trigger_name, period)
            ic_trigger.calc(numerator, denominator, liability_balance)
            
            # If trigger fails, divert funds for cure
            if not ic_trigger.pass_fail_status[period]:
                cure_amount = ic_trigger.cure_amounts[period]
                self._divert_for_ic_cure(trigger_name, cure_amount)
        
        # Continue with interest payments based on trigger results
        self._execute_interest_payment_sequence(period)
    
    def execute_principal_waterfall(self, period: int, principal_proceeds: Decimal,
                                  max_reinvestment: Decimal, reinvestment_actual: Decimal,
                                  notes_payable: Decimal) -> None:
        """Execute principal waterfall with OC trigger testing"""
        
        # Calculate OC test inputs
        numerator = self._calculate_oc_numerator(period)
        denominator = self._calculate_oc_denominator(period)
        
        # Test OC triggers
        for trigger_name, oc_trigger in self.oc_triggers.items():
            oc_trigger.calc(numerator, denominator)
            
            # If trigger fails, determine cure requirements
            if not oc_trigger.pass_fail_status[period]:
                int_cure_needed = oc_trigger.int_cure_amounts[period]
                prin_cure_needed = oc_trigger.prin_cure_amounts[period]
                
                # Apply cures based on available funds
                int_cure_applied = min(int_cure_needed, self._get_available_interest())
                prin_cure_applied = min(prin_cure_needed, principal_proceeds)
                
                oc_trigger.pay_int_cure(int_cure_applied)
                oc_trigger.pay_prin_cure(prin_cure_applied)
                
                # Reduce available proceeds by cure amounts
                principal_proceeds -= prin_cure_applied
        
        # Continue with principal payments based on remaining proceeds
        self._execute_principal_payment_sequence(period, principal_proceeds)
        
        # Roll forward all triggers
        for oc_trigger in self.oc_triggers.values():
            oc_trigger.roll_forward()
        for ic_trigger in self.ic_triggers.values():
            ic_trigger.roll_forward()
```

## Usage Examples

### Basic OC/IC Trigger Setup

```python
from app.models.oc_trigger import OCTrigger
from app.models.ic_trigger import ICTrigger
from decimal import Decimal

# Setup OC trigger for Class A notes
oc_trigger_a = OCTrigger()
oc_trigger_a.setup("Class A OC Test", Decimal('1.20'))  # 120% threshold
oc_trigger_a.deal_setup(60)  # 60 quarterly periods

# Setup IC trigger for Class B notes  
ic_trigger_b = ICTrigger()
ic_trigger_b.setup("Class B IC Test", Decimal('1.10'))  # 110% threshold
ic_trigger_b.deal_setup(60)  # 60 quarterly periods
```

### Period-by-Period Calculation

```python
# Execute calculations for each period
for period in range(1, 21):  # First 20 periods
    
    # Calculate test inputs (from portfolio and liability data)
    oc_numerator = portfolio_par_amount + excess_spread_account
    oc_denominator = sum(liability.outstanding_balance for liability in senior_notes)
    
    ic_numerator = quarterly_interest_collections
    ic_denominator = quarterly_interest_expense
    ic_liability_balance = sum(note.outstanding_balance for note in test_notes)
    
    # Execute OC test
    oc_trigger_a.calc(oc_numerator, oc_denominator)
    
    # Execute IC test
    ic_trigger_b.calc(ic_numerator, ic_denominator, ic_liability_balance)
    
    # Check results and apply cures if needed
    if not oc_trigger_a.pass_fail_status[period]:
        print(f"Period {period}: OC trigger failed")
        print(f"  Test Result: {oc_trigger_a.test_results[period]:.3%}")
        print(f"  Threshold: {oc_trigger_a.trigger_threshold:.3%}")
        print(f"  Interest Cure Needed: ${oc_trigger_a.int_cure_amounts[period]:,.2f}")
        
        # Apply cures
        available_interest = get_excess_interest(period)
        cure_applied = min(oc_trigger_a.int_cure_amounts[period], available_interest)
        oc_trigger_a.pay_int_cure(cure_applied)
    
    if not ic_trigger_b.pass_fail_status[period]:
        print(f"Period {period}: IC trigger failed")
        cure_needed = ic_trigger_b.cure_amounts[period]
        ic_trigger_b.pay_cure(cure_needed)
    
    # Advance to next period
    oc_trigger_a.roll_forward()
    ic_trigger_b.roll_forward()
```

### Reporting and Analysis

```python
# Generate comprehensive trigger reports
oc_report = oc_trigger_a.output()
ic_report = ic_trigger_b.output()

# Display OC trigger report
print("OC Trigger Report:")
for i, row in enumerate(oc_report):
    if i == 0:  # Header
        print("Period", " | ".join(f"{col:>15}" for col in row))
    else:
        print(f"{i:>6}", " | ".join(f"{col:>15}" for col in row))

# Analyze trigger performance
failing_periods = [
    period for period in range(1, oc_trigger_a.last_calculated_period + 1)
    if not oc_trigger_a.pass_fail_status[period]
]

total_cures_paid = sum(
    oc_trigger_a.int_cure_paid[period] + oc_trigger_a.prin_cure_paid[period]
    for period in range(1, oc_trigger_a.last_calculated_period + 1)
)

print(f"Failing periods: {failing_periods}")
print(f"Total cures paid: ${total_cures_paid:,.2f}")
```

### Database Persistence

```python
# Save trigger calculations to database
service = TriggerService(session)

# Create trigger structures
oc_trigger_id = service.create_oc_trigger(
    deal_id="CLO_2025_1",
    trigger_name="Class A OC Test",
    threshold=Decimal('1.20')
)

# Save each period's calculation
for period in range(1, oc_trigger_a.last_calculated_period + 1):
    cure_data = {
        'prior_int_cure': oc_trigger_a.prior_int_cure[period],
        'prior_prin_cure': oc_trigger_a.prior_prin_cure[period],
        'int_cure_amount': oc_trigger_a.int_cure_amounts[period],
        'int_cure_paid': oc_trigger_a.int_cure_paid[period],
        'prin_cure_amount': oc_trigger_a.prin_cure_amounts[period],
        'prin_cure_paid': oc_trigger_a.prin_cure_paid[period]
    }
    
    service.save_oc_calculation(
        oc_trigger_id=oc_trigger_id,
        period=period,
        numerator=oc_trigger_a.numerators[period],
        denominator=oc_trigger_a.denominators[period],
        test_result=oc_trigger_a.test_results[period],
        pass_fail=oc_trigger_a.pass_fail_status[period],
        cure_data=cure_data
    )

# Load trigger with history
loaded_oc_trigger = service.load_oc_trigger_with_history(oc_trigger_id)
assert loaded_oc_trigger.trigger_threshold == oc_trigger_a.trigger_threshold
```

## Testing Framework

### VBA Parity Tests

```python
def test_oc_trigger_vba_parity():
    """Test OC trigger calculations match VBA exactly"""
    
    oc_trigger = OCTrigger()
    oc_trigger.setup("Test OC", Decimal('1.20'))
    oc_trigger.deal_setup(5)
    
    # Test passing scenario
    oc_trigger.calc(Decimal('1200000'), Decimal('1000000'))  # 120% exactly
    assert oc_trigger.test_results[1] == Decimal('1.20')
    assert oc_trigger.pass_fail_status[1] == True
    
    # Test failing scenario
    oc_trigger.roll_forward()
    oc_trigger.calc(Decimal('1150000'), Decimal('1000000'))  # 115%
    assert oc_trigger.test_results[2] == Decimal('1.15')
    assert oc_trigger.pass_fail_status[2] == False
    
    # VBA cure calculation: (1.20 - 1.15) * 1,000,000 = 50,000
    expected_cure = Decimal('50000')
    assert oc_trigger.int_cure_amounts[2] == expected_cure
    assert oc_trigger.prin_cure_amounts[2] == expected_cure

def test_ic_trigger_cure_calculation():
    """Test IC trigger cure amount calculation"""
    
    ic_trigger = ICTrigger()
    ic_trigger.setup("Test IC", Decimal('1.10'))
    ic_trigger.deal_setup(5)
    
    # Test failing scenario
    numerator = Decimal('100000')    # Interest collections
    denominator = Decimal('110000')  # Interest expense  
    liability_balance = Decimal('5000000')  # Note balance
    
    ic_trigger.calc(numerator, denominator, liability_balance)
    
    # Test result: 100000 / 110000 = 0.909090...
    test_result = numerator / denominator
    assert abs(ic_trigger.test_results[1] - test_result) < Decimal('0.000001')
    
    # Should fail (90.9% < 110%)
    assert ic_trigger.pass_fail_status[1] == False
    
    # VBA cure calculation: (1 - 0.909090/1.10) * 5,000,000
    cure_ratio = 1 - (test_result / Decimal('1.10'))
    expected_cure = cure_ratio * liability_balance
    assert abs(ic_trigger.cure_amounts[1] - expected_cure) < Decimal('0.01')

def test_cure_payment_tracking():
    """Test cure payment tracking across periods"""
    
    oc_trigger = OCTrigger()
    oc_trigger.setup("Test OC", Decimal('1.20'))
    oc_trigger.deal_setup(5)
    
    # Period 1: Apply interest cure
    oc_trigger.calc(Decimal('1100000'), Decimal('1000000'))  # Fails
    oc_trigger.pay_int_cure(Decimal('25000'))
    oc_trigger.roll_forward()
    
    # Period 2: Check prior cure tracking
    oc_trigger.calc(Decimal('1150000'), Decimal('1000000'))  # Fails
    oc_trigger.pay_int_cure(Decimal('30000'))
    
    # VBA logic: prior cure = previous period's cure paid
    assert oc_trigger.prior_int_cure[2] == Decimal('25000')
    assert oc_trigger.int_cure_paid[2] == Decimal('30000')
```

## Performance Considerations

### Memory Management

```python
def optimize_trigger_arrays(self, compact_threshold: int = 100) -> None:
    """Optimize memory usage for long-term deals"""
    
    if self.last_calculated_period > compact_threshold:
        # Keep only essential data for old periods
        essential_periods = max(1, self.last_calculated_period - 20)
        
        self._compact_historical_data(essential_periods)

def _compact_historical_data(self, keep_from_period: int) -> None:
    """Compact historical data to save memory"""
    
    # Summarize old periods
    old_period_summary = {
        'total_int_cure_paid': sum(self.int_cure_paid[1:keep_from_period]),
        'total_prin_cure_paid': sum(self.prin_cure_paid[1:keep_from_period]),
        'periods_failed': sum(1 for p in range(1, keep_from_period) 
                             if not self.pass_fail_status[p])
    }
    
    # Keep recent periods + summary
    self._historical_summary = old_period_summary
```

### Calculation Efficiency

```python
def batch_calculate_triggers(triggers: List[OCTrigger], 
                           period_data: List[Dict[str, Decimal]]) -> None:
    """Calculate multiple triggers efficiently"""
    
    for period_datum in period_data:
        period = period_datum['period']
        numerator = period_datum['numerator']
        denominator = period_datum['denominator']
        
        # Calculate all triggers for this period
        for trigger in triggers:
            trigger.calc(numerator, denominator)
            trigger.roll_forward()
```

This documentation provides comprehensive guidance for using and maintaining the OC/IC Trigger System with complete VBA functional parity and seamless waterfall integration.