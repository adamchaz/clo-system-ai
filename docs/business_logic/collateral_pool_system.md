# Collateral Pool System Documentation

## Overview

The Collateral Pool System provides comprehensive portfolio aggregation and management for CLO deals with complete VBA functional parity. This system implements sophisticated portfolio-level calculations, cash flow aggregation, concentration testing integration, and seamless deal-level coordination for CLO collateral management.

## Architecture

### Core Components

1. **CollateralPool Class** - Standalone portfolio analysis with concentration testing
2. **CollateralPoolForCLO Class** - Deal-integrated cash flow aggregation and coordination
3. **PoolCalculator** - Portfolio metrics and analytics calculations
4. **PoolService** - Database operations and persistence
5. **ConcentrationTest Integration** - Complete 94+ test integration with objective function optimization

### Key Architectural Distinction

**VBA Comment from CollateralPoolForCLO.cls:**
```vba
'The main difference between the collateralpoolforclo and collateralpool classes. 
'Is that collateralPoolclass allows for other parameters such as compliance test and accounts
'Most people would think that these are members of the clodeal and not the collateral cashflow. 
'The collateralpool can stand alone for compliance test and hypo purposes the
'collateralpoolforclo class can't
```

**Python Implementation:**
- **CollateralPool**: Standalone portfolio analysis, concentration testing, optimization
- **CollateralPoolForCLO**: Deal-integrated cash flow coordination, simplified interface

### Database Schema

```sql
-- Collateral pool configurations
collateral_pools (
    pool_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50),
    pool_name VARCHAR(100) NOT NULL,
    analysis_date DATE NOT NULL,
    is_standalone BOOLEAN DEFAULT TRUE, -- TRUE for CollateralPool, FALSE for CollateralPoolForCLO
    rating_migration_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Pool asset memberships
pool_assets (
    pool_asset_id SERIAL PRIMARY KEY,
    pool_id INTEGER REFERENCES collateral_pools(pool_id),
    asset_id INTEGER REFERENCES assets(asset_id),
    par_amount DECIMAL(18,2) NOT NULL,
    market_value DECIMAL(18,2),
    inclusion_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Pool-level cash flow aggregations
pool_cash_flows (
    cash_flow_id SERIAL PRIMARY KEY,
    pool_id INTEGER REFERENCES collateral_pools(pool_id),
    period_number INTEGER NOT NULL,
    
    -- Beginning Balances
    beg_performing_balance DECIMAL(18,2) DEFAULT 0,
    beg_default_balance DECIMAL(18,2) DEFAULT 0,
    beg_mv_default_balance DECIMAL(18,2) DEFAULT 0,
    
    -- Period Activity
    period_defaults DECIMAL(18,2) DEFAULT 0,
    period_mv_defaults DECIMAL(18,2) DEFAULT 0,
    interest_collections DECIMAL(18,2) DEFAULT 0,
    scheduled_principal DECIMAL(18,2) DEFAULT 0,
    unscheduled_principal DECIMAL(18,2) DEFAULT 0,
    recoveries DECIMAL(18,2) DEFAULT 0,
    net_losses DECIMAL(18,2) DEFAULT 0,
    assets_sold DECIMAL(18,2) DEFAULT 0,
    
    calculation_date DATE NOT NULL
);

-- Pool metrics and analytics
pool_metrics (
    metric_id SERIAL PRIMARY KEY,
    pool_id INTEGER REFERENCES collateral_pools(pool_id),
    metric_date DATE NOT NULL,
    
    -- Aggregate Metrics
    total_par_amount DECIMAL(18,2),
    total_market_value DECIMAL(18,2),
    weighted_avg_coupon DECIMAL(6,4),
    weighted_avg_spread DECIMAL(6,4),
    weighted_avg_life DECIMAL(8,4),
    
    -- Rating Metrics
    weighted_avg_rating_mdy DECIMAL(6,2),
    weighted_avg_rating_sp DECIMAL(6,2),
    
    -- Concentration Metrics
    objective_function_value DECIMAL(12,6),
    concentration_score DECIMAL(8,4),
    
    -- Portfolio Quality
    ccc_and_below_pct DECIMAL(6,4),
    default_assets_pct DECIMAL(6,4),
    performing_assets_pct DECIMAL(6,4)
);

-- Account integrations (for CollateralPool only)
pool_accounts (
    account_id SERIAL PRIMARY KEY,
    pool_id INTEGER REFERENCES collateral_pools(pool_id),
    account_type VARCHAR(50) NOT NULL, -- 'COLLECTION', 'INTEREST_RESERVE', etc.
    interest_balance DECIMAL(18,2) DEFAULT 0,
    principal_balance DECIMAL(18,2) DEFAULT 0,
    total_balance DECIMAL(18,2) GENERATED ALWAYS AS (interest_balance + principal_balance) STORED
);
```

## VBA Functional Parity

### CollateralPool - Method Mapping

| VBA Method | Python Method | Purpose | Status |
|------------|---------------|---------|--------|
| `CheckAccountBalance()` | `check_account_balance()` | Get account balance by type | ✅ Complete |
| `GetBLKRockIDs()` | `get_blk_rock_ids()` | Get asset identifier list | ✅ Complete |
| `GetObjectiveDict()` | `get_objective_dict()` | Get concentration test objectives | ✅ Complete |
| `GetObjectiveValue()` | `get_objective_value()` | Calculate objective function | ✅ Complete |
| `GetAssetObjective()` | `get_asset_objective()` | Asset-specific objective calculation | ✅ Complete |
| `GetCollatParAmount()` | `get_collateral_par_amount()` | Portfolio par amount with filtering | ✅ Complete |
| `CalcConcentrationTest()` | `calc_concentration_test()` | Run all concentration tests | ✅ Complete |

### CollateralPoolForCLO - Method Mapping

| VBA Method | Python Method | Purpose | Status |
|------------|---------------|---------|--------|
| `SetAnalysisDate()` | `set_analysis_date()` | Configure analysis parameters | ✅ Complete |
| `ResetParAmount()` | `reset_par_amount()` | Reset all asset par amounts | ✅ Complete |
| `GetProceeds()` | `get_proceeds()` | Aggregate interest/principal proceeds | ✅ Complete |
| `CalcCF()` | `calc_cf()` | Calculate all asset cash flows | ✅ Complete |
| `GetCollatCF()` | `get_collateral_cf()` | Get aggregated cash flow report | ✅ Complete |

### Variable Mapping

| VBA Variable | Python Variable | Type | Purpose |
|--------------|-----------------|------|---------| 
| `clsAssetsDict` | `assets_dict` | Dict[str, Asset] | Asset dictionary by BLKRockID |
| `clsAccountsDict` | `accounts_dict` | Dict[AccountType, Account] | Account balances |
| `clsConcentrationTest` | `concentration_test` | ConcentrationTest | Concentration testing engine |
| `clsRatingsDeriv` | `ratings_deriv` | RatingDerivations | Rating calculation utilities |
| `clsTestSetting` | `test_settings` | TestSettings | Concentration test configuration |
| `clsDealCFDict` | `deal_cf_dict` | Dict[str, SimpleCashflow] | Asset-level cash flows |
| `clsDealCF` | `deal_cf` | SimpleCashflow | Aggregated portfolio cash flows |
| `clsPeriod` | `current_period` | int | Current calculation period |
| `clsLastperiod` | `last_period` | int | Final calculation period |

## Implementation Details

### 1. VBA CollateralPool Account Management

**VBA Code:**
```vba
Public Function CheckAccountBalance(iType As AccountType, icash As CashType) As Double
    If icash = Principal Then
        CheckAccountBalance = clsAccountsDict(iType).PrincipalProceeds
    ElseIf icash = Interest Then
        CheckAccountBalance = clsAccountsDict(iType).InterestProceeds
    ElseIf icash = Total Then
        CheckAccountBalance = clsAccountsDict(iType).TotalProceeds
    End If
End Function
```

**Python Equivalent:**
```python
class CollateralPool:
    """VBA CollateralPool.cls equivalent with complete portfolio management"""
    
    def __init__(self):
        self.assets_dict: Dict[str, Asset] = {}
        self.accounts_dict: Dict[AccountType, Account] = {}
        self.concentration_test: Optional[ConcentrationTest] = None
        self.ratings_deriv: Optional[RatingDerivations] = None
        self.test_settings: Optional[TestSettings] = None
        
        self.analysis_date: Optional[date] = None
        self.rerun_test: bool = True
        self._is_setup: bool = False

    def check_account_balance(self, i_type: AccountType, i_cash: CashType) -> Decimal:
        """VBA CheckAccountBalance() function equivalent"""
        
        if i_type not in self.accounts_dict:
            return Decimal('0')
        
        account = self.accounts_dict[i_type]
        
        # VBA: Principal/Interest/Total cash type handling
        if i_cash == CashType.PRINCIPAL:
            return account.principal_balance
        elif i_cash == CashType.INTEREST:
            return account.interest_balance
        elif i_cash == CashType.TOTAL:
            return account.total_balance
        else:
            return Decimal('0')

    def get_blk_rock_ids(self) -> List[str]:
        """VBA GetBLKRockIDs() function equivalent"""
        # VBA: GetBLKRockIDs = clsAssetsDict.Keys
        return list(self.assets_dict.keys())

    def get_objective_dict(self) -> Dict[str, Any]:
        """VBA GetObjectiveDict() function equivalent"""
        if not self.concentration_test:
            return {}
        
        # VBA: Set GetObjectiveDict = clsConcentrationTest.GetObjectiveDict
        return self.concentration_test.get_objective_dict()

    def get_objective_value(self) -> Decimal:
        """VBA GetObjectiveValue() function equivalent"""
        
        # VBA: If clsReRunTest Then Call CalcConcentrationTest
        if self.rerun_test:
            self.calc_concentration_test()
        
        if not self.concentration_test:
            return Decimal('0')
        
        # VBA: GetObjectiveValue = clsConcentrationTest.CalcObjectiveFunction
        return self.concentration_test.calc_objective_function()
```

### 2. VBA CollateralPoolForCLO Cash Flow Integration

**VBA Code:**
```vba
Public Sub SetAnalysisDate(iDate As Date, iRating As Boolean)
    clsAnalysisDate = iDate
    clsRatingMigration = iRating
    Call SetUseRM(iRating)
End Sub

Public Function GetProceeds(iProceeds As String)
    Dim lBlkRockID As Variant
    Dim lNumerator As Double
    Dim lCF As SimpleCashflow
    
    For Each lBlkRockID In clsDealCFDict.Keys
        Set lCF = clsDealCFDict(lBlkRockID)
        If iProceeds = "INTEREST" Then
            lNumerator = lNumerator + lCF.Interest(clsPeriod)
        ElseIf iProceeds = "PRINCIPAL" Then
            lNumerator = lNumerator + lCF.SchedPrincipal(clsPeriod) + lCF.UnSchedPrincipal(clsPeriod) + lCF.Recoveries(clsPeriod)
        End If
    Next
    GetProceeds = lNumerator
End Function
```

**Python Equivalent:**
```python
class CollateralPoolForCLO:
    """VBA CollateralPoolForCLO.cls equivalent for deal integration"""
    
    def __init__(self):
        self.assets_dict: Dict[str, Asset] = {}
        self.ratings_deriv: Optional[RatingDerivations] = None
        self.deal_cf_dict: Dict[str, SimpleCashflow] = {}
        self.deal_cf: Optional[SimpleCashflow] = None
        
        self.current_period: int = 1
        self.last_period: int = 0
        self.analysis_date: Optional[date] = None
        self.rating_migration: bool = False

    def set_analysis_date(self, i_date: date, i_rating: bool) -> None:
        """VBA SetAnalysisDate() method equivalent"""
        
        # VBA: clsAnalysisDate = iDate
        self.analysis_date = i_date
        
        # VBA: clsRatingMigration = iRating
        self.rating_migration = i_rating
        
        # VBA: Call SetUseRM(iRating)
        self._set_use_rm(i_rating)

    def reset_par_amount(self) -> None:
        """VBA ResetParAmount() method equivalent"""
        
        # VBA: For Each lBlkRockID In clsAssetsDict.Keys
        for blk_rock_id, asset in self.assets_dict.items():
            # VBA: lParAmount = lAsset.ParAmount
            current_par = asset.par_amount
            
            # VBA: lAsset.AddPar -lParAmount (reset to zero)
            asset.add_par(-current_par)

    def get_proceeds(self, i_proceeds: str) -> Decimal:
        """VBA GetProceeds() function equivalent"""
        
        total_proceeds = Decimal('0')
        
        # VBA: For Each lBlkRockID In clsDealCFDict.Keys
        for blk_rock_id, cash_flow in self.deal_cf_dict.items():
            
            # VBA: Interest vs Principal proceeds
            if i_proceeds.upper() == "INTEREST":
                # VBA: lNumerator = lNumerator + lCF.Interest(clsPeriod)
                total_proceeds += cash_flow.get_interest(self.current_period)
                
            elif i_proceeds.upper() == "PRINCIPAL":
                # VBA: lNumerator = lNumerator + lCF.SchedPrincipal(clsPeriod) + lCF.UnSchedPrincipal(clsPeriod) + lCF.Recoveries(clsPeriod)
                scheduled = cash_flow.get_scheduled_principal(self.current_period)
                unscheduled = cash_flow.get_unscheduled_principal(self.current_period)
                recoveries = cash_flow.get_recoveries(self.current_period)
                total_proceeds += scheduled + unscheduled + recoveries
        
        return total_proceeds

    def calc_cf(self, i_curr_balance: Optional[Decimal] = None,
                i_initial_settlement_date: Optional[date] = None,
                i_analysis_date: Optional[date] = None,
                i_prepay: Optional[Any] = None,
                i_default: Optional[Any] = None,
                i_severity: Optional[Any] = None,
                i_lag_month: Optional[int] = None,
                i_end_cf_date: Optional[date] = None,
                i_yc: Optional[YieldCurve] = None) -> None:
        """VBA CalcCF() method equivalent - calculate all asset cash flows"""
        
        # VBA: For Each lBlkRockID In clsAssetsDict.Keys
        for blk_rock_id, asset in self.assets_dict.items():
            # VBA: lAsset.CalcCF with all optional parameters
            asset.calc_cf(
                curr_balance=i_curr_balance,
                initial_settlement_date=i_initial_settlement_date,
                analysis_date=i_analysis_date,
                prepay=i_prepay,
                default=i_default,
                severity=i_severity,
                lag_month=i_lag_month,
                end_cf_date=i_end_cf_date,
                yield_curve=i_yc
            )
```

### 3. VBA Cash Flow Aggregation and Reporting

**VBA Code:**
```vba
Public Function GetCollatCF() As Variant
    Dim lOutput As Variant
    Dim i As Long
    
    ReDim lOutput(0 To clsLastperiod, 10)
    
    lOutput(0, 0) = "Beg Performing Balance"
    lOutput(0, 1) = "Beg Default Balance"
    lOutput(0, 2) = "Beg MV Default Balance"
    lOutput(0, 3) = "Period Default"
    lOutput(0, 4) = "Period MV Default"
    lOutput(0, 5) = "Interest"
    lOutput(0, 6) = "Scheduled Principal"
    lOutput(0, 7) = "Unscheduled Principal"
    lOutput(0, 8) = "Recoveries"
    lOutput(0, 9) = "Net loss"
    lOutput(0, 10) = "Sold"
    
    For i = 1 To clsLastperiod
        lOutput(i, 0) = clsDealCF.BegBalance(i)
        lOutput(i, 1) = clsDealCF.DefaultBal(i)
        lOutput(i, 2) = clsDealCF.MVDefaultBal(i)
        lOutput(i, 3) = clsDealCF.Default(i)
        lOutput(i, 4) = clsDealCF.MVDefault(i)
        lOutput(i, 5) = clsDealCF.Interest(i)
        lOutput(i, 6) = clsDealCF.SchedPrincipal(i)
        lOutput(i, 7) = clsDealCF.UnSchedPrincipal(i)
        lOutput(i, 8) = clsDealCF.Recoveries(i)
        lOutput(i, 9) = clsDealCF.NetLoss(i)
        lOutput(i, 10) = clsDealCF.Sold(i)
    Next i
    
    GetCollatCF = lOutput
End Function
```

**Python Equivalent:**
```python
def get_collateral_cf(self) -> List[List[str]]:
    """VBA GetCollatCF() function equivalent"""
    
    if not self.deal_cf or self.last_period == 0:
        return []
    
    # VBA: ReDim lOutput(0 To clsLastperiod, 10)
    output_data = []
    
    # VBA: Header row
    header = [
        "Beg Performing Balance", "Beg Default Balance", "Beg MV Default Balance",
        "Period Default", "Period MV Default", "Interest",
        "Scheduled Principal", "Unscheduled Principal", "Recoveries",
        "Net Loss", "Sold"
    ]
    output_data.append(header)
    
    # VBA: For i = 1 To clsLastperiod
    for period in range(1, self.last_period + 1):
        row = [
            str(self.deal_cf.get_beginning_balance(period)),
            str(self.deal_cf.get_default_balance(period)),
            str(self.deal_cf.get_mv_default_balance(period)),
            str(self.deal_cf.get_period_defaults(period)),
            str(self.deal_cf.get_period_mv_defaults(period)),
            str(self.deal_cf.get_interest(period)),
            str(self.deal_cf.get_scheduled_principal(period)),
            str(self.deal_cf.get_unscheduled_principal(period)),
            str(self.deal_cf.get_recoveries(period)),
            str(self.deal_cf.get_net_loss(period)),
            str(self.deal_cf.get_sold(period))
        ]
        output_data.append(row)
    
    return output_data
```

### 4. Collateral Quality Tests and Analytics

```python
class PoolCalculator:
    """Portfolio-level calculation and analytics engine"""
    
    @staticmethod
    def calculate_portfolio_metrics(assets_dict: Dict[str, Asset]) -> Dict[str, Decimal]:
        """Calculate comprehensive portfolio metrics"""
        
        if not assets_dict:
            return {}
        
        total_par = Decimal('0')
        total_market_value = Decimal('0')
        weighted_coupon = Decimal('0')
        weighted_spread = Decimal('0')
        weighted_life = Decimal('0')
        
        rating_sum_mdy = Decimal('0')
        rating_sum_sp = Decimal('0')
        
        ccc_below_par = Decimal('0')
        default_par = Decimal('0')
        performing_par = Decimal('0')
        
        for asset in assets_dict.values():
            par_amount = asset.par_amount
            total_par += par_amount
            
            if asset.market_value:
                total_market_value += asset.market_value
            
            # Weighted calculations
            if asset.coupon:
                weighted_coupon += asset.coupon * par_amount
            if asset.coupon_spread:
                weighted_spread += asset.coupon_spread * par_amount
            if asset.wal:
                weighted_life += asset.wal * par_amount
            
            # Rating calculations
            mdy_rating_num = asset.get_mdy_rating_numeric()
            sp_rating_num = asset.get_sp_rating_numeric()
            rating_sum_mdy += mdy_rating_num * par_amount
            rating_sum_sp += sp_rating_num * par_amount
            
            # Quality metrics
            if mdy_rating_num >= 17:  # CAA1 and below
                ccc_below_par += par_amount
            if asset.is_default_asset:
                default_par += par_amount
            else:
                performing_par += par_amount
        
        # Calculate weighted averages
        metrics = {
            'total_par_amount': total_par,
            'total_market_value': total_market_value,
            'weighted_avg_coupon': weighted_coupon / total_par if total_par > 0 else Decimal('0'),
            'weighted_avg_spread': weighted_spread / total_par if total_par > 0 else Decimal('0'),
            'weighted_avg_life': weighted_life / total_par if total_par > 0 else Decimal('0'),
            'weighted_avg_rating_mdy': rating_sum_mdy / total_par if total_par > 0 else Decimal('0'),
            'weighted_avg_rating_sp': rating_sum_sp / total_par if total_par > 0 else Decimal('0'),
            'ccc_and_below_pct': ccc_below_par / total_par if total_par > 0 else Decimal('0'),
            'default_assets_pct': default_par / total_par if total_par > 0 else Decimal('0'),
            'performing_assets_pct': performing_par / total_par if total_par > 0 else Decimal('0'),
            'asset_count': len(assets_dict)
        }
        
        return metrics

    @staticmethod
    def calculate_concentration_metrics(assets_dict: Dict[str, Asset], 
                                      concentration_test: ConcentrationTest) -> Dict[str, Decimal]:
        """Calculate concentration-specific metrics"""
        
        # Run concentration tests
        test_results = concentration_test.run_all_tests(assets_dict)
        
        # Calculate objective function
        objective_value = concentration_test.calc_objective_function()
        
        # Calculate concentration score (0-100, higher is better)
        passing_tests = sum(1 for result in test_results.values() if result.get('pass_fail', False))
        total_tests = len(test_results)
        concentration_score = (passing_tests / total_tests * 100) if total_tests > 0 else Decimal('0')
        
        return {
            'objective_function_value': objective_value,
            'concentration_score': concentration_score,
            'passing_tests': passing_tests,
            'total_tests': total_tests,
            'failing_test_names': [name for name, result in test_results.items() 
                                 if not result.get('pass_fail', True)]
        }
```

## Database Integration

### Service Layer Implementation

```python
class PoolService:
    """Service layer for collateral pool database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_collateral_pool(self, deal_id: Optional[str], pool_name: str,
                              analysis_date: date, is_standalone: bool = True) -> int:
        """Create new collateral pool structure"""
        
        pool = CollateralPools(
            deal_id=deal_id,
            pool_name=pool_name,
            analysis_date=analysis_date,
            is_standalone=is_standalone,
            is_active=True
        )
        
        self.session.add(pool)
        self.session.flush()
        
        return pool.pool_id
    
    def add_assets_to_pool(self, pool_id: int, asset_ids: List[int]) -> None:
        """Add assets to collateral pool"""
        
        for asset_id in asset_ids:
            # Get asset details
            asset = self.session.query(Assets).filter_by(asset_id=asset_id).first()
            if not asset:
                continue
            
            pool_asset = PoolAssets(
                pool_id=pool_id,
                asset_id=asset_id,
                par_amount=asset.par_amount,
                market_value=asset.market_value,
                inclusion_date=date.today(),
                is_active=True
            )
            self.session.add(pool_asset)
        
        self.session.commit()
    
    def save_pool_cash_flows(self, pool_id: int, cash_flows: List[PoolCashFlowData]) -> None:
        """Save aggregated pool cash flows"""
        
        # Delete existing cash flows
        self.session.query(PoolCashFlows).filter_by(pool_id=pool_id).delete()
        
        # Insert new cash flows
        for cf_data in cash_flows:
            pool_cf = PoolCashFlows(
                pool_id=pool_id,
                period_number=cf_data.period_number,
                beg_performing_balance=cf_data.beg_performing_balance,
                beg_default_balance=cf_data.beg_default_balance,
                beg_mv_default_balance=cf_data.beg_mv_default_balance,
                period_defaults=cf_data.period_defaults,
                period_mv_defaults=cf_data.period_mv_defaults,
                interest_collections=cf_data.interest_collections,
                scheduled_principal=cf_data.scheduled_principal,
                unscheduled_principal=cf_data.unscheduled_principal,
                recoveries=cf_data.recoveries,
                net_losses=cf_data.net_losses,
                assets_sold=cf_data.assets_sold,
                calculation_date=date.today()
            )
            self.session.add(pool_cf)
        
        self.session.commit()
    
    def save_pool_metrics(self, pool_id: int, metrics: Dict[str, Decimal]) -> None:
        """Save portfolio metrics"""
        
        pool_metric = PoolMetrics(
            pool_id=pool_id,
            metric_date=date.today(),
            total_par_amount=metrics.get('total_par_amount'),
            total_market_value=metrics.get('total_market_value'),
            weighted_avg_coupon=metrics.get('weighted_avg_coupon'),
            weighted_avg_spread=metrics.get('weighted_avg_spread'),
            weighted_avg_life=metrics.get('weighted_avg_life'),
            weighted_avg_rating_mdy=metrics.get('weighted_avg_rating_mdy'),
            weighted_avg_rating_sp=metrics.get('weighted_avg_rating_sp'),
            objective_function_value=metrics.get('objective_function_value'),
            concentration_score=metrics.get('concentration_score'),
            ccc_and_below_pct=metrics.get('ccc_and_below_pct'),
            default_assets_pct=metrics.get('default_assets_pct'),
            performing_assets_pct=metrics.get('performing_assets_pct')
        )
        
        self.session.add(pool_metric)
        self.session.commit()
    
    def load_pool_with_assets(self, pool_id: int) -> CollateralPool:
        """Load complete collateral pool with assets and history"""
        
        # Load pool configuration
        db_pool = (self.session.query(CollateralPools)
                  .filter_by(pool_id=pool_id)
                  .first())
        
        if not db_pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        # Create appropriate pool object
        if db_pool.is_standalone:
            pool = CollateralPool()
        else:
            pool = CollateralPoolForCLO()
        
        # Load pool assets
        pool_assets = (self.session.query(PoolAssets)
                      .filter_by(pool_id=pool_id, is_active=True)
                      .all())
        
        assets_dict = {}
        for pool_asset in pool_assets:
            asset = self._load_asset_from_id(pool_asset.asset_id)
            assets_dict[asset.blk_rock_id] = asset
        
        pool.assets_dict = assets_dict
        pool.analysis_date = db_pool.analysis_date
        
        # Load cash flows if available
        cash_flows = (self.session.query(PoolCashFlows)
                     .filter_by(pool_id=pool_id)
                     .order_by(PoolCashFlows.period_number)
                     .all())
        
        if cash_flows:
            pool.last_period = max(cf.period_number for cf in cash_flows)
            # Convert to appropriate cash flow objects
        
        return pool
```

## CLO Deal Engine Integration

### Deal-Level Coordination

```python
class CLODealEngine:
    """Integration of collateral pool with deal engine"""
    
    def __init__(self, deal: CLODeal, session: Session):
        self.deal = deal
        self.session = session
        self.collateral_pool: Optional[CollateralPoolForCLO] = None
        self.pool_service = PoolService(session)
    
    def setup_collateral_pool(self, assets: List[Asset]) -> None:
        """Setup deal-integrated collateral pool"""
        
        self.collateral_pool = CollateralPoolForCLO()
        
        # Convert asset list to dictionary
        assets_dict = {asset.blk_rock_id: asset for asset in assets}
        self.collateral_pool.assets_dict = assets_dict
        
        # Setup analysis parameters
        self.collateral_pool.set_analysis_date(
            self.deal_dates.analysis_date,
            rating_migration=True
        )
    
    def calculate_period_cash_flows(self, period: int) -> Dict[str, Decimal]:
        """Calculate portfolio cash flows for period"""
        
        if not self.collateral_pool:
            return {}
        
        # Set current period
        self.collateral_pool.current_period = period
        
        # Calculate all asset cash flows
        self.collateral_pool.calc_cf(
            i_analysis_date=self.deal_dates.analysis_date,
            i_end_cf_date=self.deal_dates.maturity_date
        )
        
        # Get aggregated proceeds
        interest_proceeds = self.collateral_pool.get_proceeds("INTEREST")
        principal_proceeds = self.collateral_pool.get_proceeds("PRINCIPAL")
        
        return {
            'interest_proceeds': interest_proceeds,
            'principal_proceeds': principal_proceeds,
            'total_proceeds': interest_proceeds + principal_proceeds
        }
    
    def get_portfolio_metrics(self) -> Dict[str, Decimal]:
        """Get current portfolio metrics"""
        
        if not self.collateral_pool:
            return {}
        
        return PoolCalculator.calculate_portfolio_metrics(
            self.collateral_pool.assets_dict
        )
    
    def run_concentration_tests(self) -> Dict[str, Any]:
        """Run concentration tests on current portfolio"""
        
        if not self.collateral_pool:
            return {}
        
        # Setup concentration test
        concentration_test = ConcentrationTest()
        concentration_test.setup_all_tests()
        
        # Run tests
        test_results = concentration_test.run_all_tests(
            self.collateral_pool.assets_dict
        )
        
        # Calculate metrics
        concentration_metrics = PoolCalculator.calculate_concentration_metrics(
            self.collateral_pool.assets_dict,
            concentration_test
        )
        
        return {
            'test_results': test_results,
            'metrics': concentration_metrics
        }
```

## Usage Examples

### Standalone Collateral Pool Setup

```python
from app.models.collateral_pool import CollateralPool
from app.models.concentration_test import ConcentrationTest
from decimal import Decimal

# Create standalone pool for analysis
pool = CollateralPool()

# Add assets to pool
asset_list = load_sample_assets()
assets_dict = {asset.blk_rock_id: asset for asset in asset_list}
pool.assets_dict = assets_dict

# Setup concentration testing
concentration_test = ConcentrationTest()
concentration_test.setup_all_tests()
pool.concentration_test = concentration_test

# Setup accounts for compliance testing
pool.setup_accounts([
    AccountType.COLLECTION,
    AccountType.INTEREST_RESERVE,
    AccountType.PRINCIPAL_ACCOUNT
])

# Calculate objective function
objective_value = pool.get_objective_value()
print(f"Portfolio objective function: {objective_value}")

# Get concentration test results
objective_dict = pool.get_objective_dict()
for test_name, result in objective_dict.items():
    print(f"{test_name}: {result}")
```

### Deal-Integrated Pool Setup

```python
from app.models.collateral_pool_for_clo import CollateralPoolForCLO

# Create deal-integrated pool
pool = CollateralPoolForCLO()

# Setup analysis parameters
pool.set_analysis_date(
    i_date=date(2025, 3, 15),
    i_rating=True  # Enable rating migration
)

# Add assets
assets_dict = {asset.blk_rock_id: asset for asset in deal_assets}
pool.assets_dict = assets_dict

# Calculate cash flows for all assets
pool.calc_cf(
    i_analysis_date=date(2025, 3, 15),
    i_end_cf_date=date(2030, 3, 15)
)

# Get period cash flows
pool.current_period = 1
interest_collections = pool.get_proceeds("INTEREST")
principal_collections = pool.get_proceeds("PRINCIPAL")

print(f"Period 1 Interest: ${interest_collections:,.2f}")
print(f"Period 1 Principal: ${principal_collections:,.2f}")

# Generate cash flow report
cf_report = pool.get_collateral_cf()
for i, row in enumerate(cf_report):
    if i == 0:  # Header
        print(" | ".join(f"{col:>20}" for col in row))
    elif i <= 5:  # First 5 periods
        print(" | ".join(f"{col:>20}" for col in row))
```

### Portfolio Analytics

```python
# Calculate comprehensive metrics
metrics = PoolCalculator.calculate_portfolio_metrics(assets_dict)

print("Collateral Quality Metrics:")
print(f"Total Par Amount: ${metrics['total_par_amount']:,.2f}")
print(f"Weighted Average Coupon: {metrics['weighted_avg_coupon']:.2%}")
print(f"Weighted Average Spread: {metrics['weighted_avg_spread']:.2%}")
print(f"Weighted Average Life: {metrics['weighted_avg_life']:.2f} years")
print(f"CCC and Below: {metrics['ccc_and_below_pct']:.1%}")
print(f"Default Assets: {metrics['default_assets_pct']:.1%}")

# Concentration analysis
concentration_test = ConcentrationTest()
concentration_test.setup_all_tests()

concentration_metrics = PoolCalculator.calculate_concentration_metrics(
    assets_dict, concentration_test
)

print(f"Concentration Score: {concentration_metrics['concentration_score']:.1f}/100")
print(f"Passing Tests: {concentration_metrics['passing_tests']}/{concentration_metrics['total_tests']}")

if concentration_metrics['failing_test_names']:
    print("Failing Tests:")
    for test_name in concentration_metrics['failing_test_names']:
        print(f"  - {test_name}")
```

### Asset Optimization

```python
# Asset addition/removal analysis
from app.models.transaction_type import TransactionType

# Analyze adding new asset
new_asset = create_sample_asset("NEW123456")
add_dict = {new_asset.blk_rock_id: new_asset}

asset_objective = pool.get_asset_objective(add_dict, TransactionType.BUY)
print(f"Adding {new_asset.blk_rock_id} objective impact: {asset_objective}")

# Analyze removing existing asset
existing_asset_id = list(assets_dict.keys())[0]
remove_dict = {existing_asset_id: assets_dict[existing_asset_id]}

asset_objective = pool.get_asset_objective(remove_dict, TransactionType.SELL)
print(f"Removing {existing_asset_id} objective impact: {asset_objective}")

# Portfolio optimization
current_objective = pool.get_objective_value()
print(f"Current portfolio objective: {current_objective}")

# Test various asset swaps
for potential_swap in generate_swap_candidates():
    swap_objective = calculate_swap_objective(potential_swap)
    if swap_objective > current_objective:
        print(f"Beneficial swap found: {potential_swap} (improvement: {swap_objective - current_objective})")
```

### Database Operations

```python
# Create and persist pool
service = PoolService(session)

pool_id = service.create_collateral_pool(
    deal_id="CLO_2025_1",
    pool_name="CLO 2025-1 Collateral Pool",
    analysis_date=date(2025, 3, 15),
    is_standalone=False  # Deal-integrated pool
)

# Add assets to pool
asset_ids = [asset.asset_id for asset in deal_assets]
service.add_assets_to_pool(pool_id, asset_ids)

# Save cash flows
cf_data = convert_to_pool_cash_flow_data(pool.get_collateral_cf())
service.save_pool_cash_flows(pool_id, cf_data)

# Save metrics
portfolio_metrics = PoolCalculator.calculate_portfolio_metrics(assets_dict)
service.save_pool_metrics(pool_id, portfolio_metrics)

# Load pool later
loaded_pool = service.load_pool_with_assets(pool_id)
assert len(loaded_pool.assets_dict) == len(assets_dict)
```

## Testing Framework

### VBA Parity Tests

```python
def test_collateral_pool_account_balance():
    """Test VBA CheckAccountBalance() functionality"""
    
    pool = CollateralPool()
    pool.setup_accounts([AccountType.COLLECTION, AccountType.INTEREST_RESERVE])
    
    # Add funds to collection account
    collection_account = pool.accounts_dict[AccountType.COLLECTION]
    collection_account.add(CashType.INTEREST, Decimal('50000'))
    collection_account.add(CashType.PRINCIPAL, Decimal('75000'))
    
    # Test VBA equivalent calls
    interest_balance = pool.check_account_balance(AccountType.COLLECTION, CashType.INTEREST)
    principal_balance = pool.check_account_balance(AccountType.COLLECTION, CashType.PRINCIPAL)
    total_balance = pool.check_account_balance(AccountType.COLLECTION, CashType.TOTAL)
    
    assert interest_balance == Decimal('50000')
    assert principal_balance == Decimal('75000')
    assert total_balance == Decimal('125000')

def test_pool_for_clo_proceeds_calculation():
    """Test VBA GetProceeds() calculations"""
    
    pool = CollateralPoolForCLO()
    pool.current_period = 1
    
    # Setup mock cash flows
    cf1 = SimpleCashflow()
    cf1.set_interest(1, Decimal('10000'))
    cf1.set_scheduled_principal(1, Decimal('5000'))
    cf1.set_unscheduled_principal(1, Decimal('3000'))
    cf1.set_recoveries(1, Decimal('2000'))
    
    cf2 = SimpleCashflow()
    cf2.set_interest(1, Decimal('8000'))
    cf2.set_scheduled_principal(1, Decimal('4000'))
    cf2.set_unscheduled_principal(1, Decimal('2000'))
    cf2.set_recoveries(1, Decimal('1000'))
    
    pool.deal_cf_dict = {"ASSET1": cf1, "ASSET2": cf2}
    
    # Test VBA GetProceeds logic
    interest_proceeds = pool.get_proceeds("INTEREST")
    principal_proceeds = pool.get_proceeds("PRINCIPAL")
    
    # Expected: Interest = 10000 + 8000 = 18000
    assert interest_proceeds == Decimal('18000')
    
    # Expected: Principal = (5000+3000+2000) + (4000+2000+1000) = 17000
    assert principal_proceeds == Decimal('17000')

def test_portfolio_metrics_accuracy():
    """Test portfolio metric calculations"""
    
    assets = create_test_asset_portfolio()
    metrics = PoolCalculator.calculate_portfolio_metrics(assets)
    
    # Verify total par
    expected_par = sum(asset.par_amount for asset in assets.values())
    assert metrics['total_par_amount'] == expected_par
    
    # Verify weighted average coupon
    coupon_sum = sum(asset.coupon * asset.par_amount for asset in assets.values() if asset.coupon)
    expected_wa_coupon = coupon_sum / expected_par
    assert abs(metrics['weighted_avg_coupon'] - expected_wa_coupon) < Decimal('0.0001')
```

This documentation provides comprehensive guidance for using and maintaining the Collateral Pool System with complete VBA functional parity and seamless CLO deal integration.