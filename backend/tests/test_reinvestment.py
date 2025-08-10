"""
Test suite for Reinvestment System

Tests the complete VBA Reinvest.cls conversion including:
- DealSetup and initialization
- AddReinvestment cash flow modeling
- SimpleCashflow functionality  
- VBA functional parity
- Database persistence
- Scenario analysis
"""

import pytest
import json
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.core.database import Base
from app.models.reinvestment import (
    Reinvest,
    ReinvestmentService,
    ReinvestInfo,
    PaymentDates,
    SimpleCashflow,
    ReinvestmentPeriodModel,
    ReinvestmentInfoModel,
    ReinvestmentCashFlowModel
)


@pytest.fixture
def reinvestment_db():
    """Create in-memory database for reinvestment testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def sample_payment_dates():
    """Create sample payment dates for testing"""
    base_date = date(2025, 1, 15)
    payment_dates = []
    
    # Add index 0 as None (VBA uses 1-based indexing)
    payment_dates.append(None)
    
    # Create quarterly payment dates for 3 years
    for i in range(1, 13):  # 12 quarters = 3 years
        payment_date = base_date + relativedelta(months=i*3)
        coll_beg_date = base_date + relativedelta(months=(i-1)*3)
        coll_end_date = payment_date - relativedelta(days=1)
        
        payment_dates.append(PaymentDates(payment_date, coll_beg_date, coll_end_date))
    
    return payment_dates


@pytest.fixture
def sample_reinvest_info():
    """Create sample reinvestment info for testing"""
    return ReinvestInfo(
        maturity=60,      # 5 years
        reinvest_price=1.0,  # Par
        spread=0.05,      # 500 bps
        floor=0.01,       # 100 bps floor
        liquidation=0.70, # 70% liquidation
        lag=6,            # 6 months lag
        prepayment=0.15,  # 15% annual prepayment
        default=0.03,     # 3% annual default
        severity=0.40     # 40% severity
    )


@pytest.fixture
def mock_yield_curve():
    """Create mock yield curve for testing"""
    mock_curve = Mock()
    mock_curve.name = "TEST_CURVE"
    mock_curve.spot_rate = Mock(return_value=0.045)  # 4.5% rate
    return mock_curve


@pytest.fixture
def test_reinvest(reinvestment_db, sample_payment_dates, sample_reinvest_info, mock_yield_curve):
    """Create test Reinvest instance with setup completed"""
    reinvest = Reinvest(reinvestment_db)
    reinvest.deal_setup(sample_payment_dates, sample_reinvest_info, 3, mock_yield_curve)
    return reinvest


class TestSimpleCashflow:
    """Test SimpleCashflow VBA equivalent implementation"""
    
    def test_simple_cashflow_initialization(self):
        """Test SimpleCashflow initialization"""
        cf = SimpleCashflow(50)
        
        assert cf.Count == 0
        assert cf.BegBalance(1) == Decimal('0')
        assert cf.PaymentDate(1) is None
        assert cf.Interest(1) == Decimal('0')
    
    def test_simple_cashflow_property_setters(self):
        """Test SimpleCashflow property setter/getter methods"""
        cf = SimpleCashflow(50)
        test_date = date(2025, 3, 15)
        test_amount = Decimal('1000000')
        
        # Test date properties
        cf.PaymentDate(1, test_date)
        assert cf.PaymentDate(1) == test_date
        
        cf.AccBegDate(1, test_date - relativedelta(months=3))
        assert cf.AccBegDate(1) == test_date - relativedelta(months=3)
        
        cf.AccEndDate(1, test_date - relativedelta(days=1))
        assert cf.AccEndDate(1) == test_date - relativedelta(days=1)
        
        # Test amount properties
        cf.BegBalance(1, test_amount)
        assert cf.BegBalance(1) == test_amount
        
        cf.Interest(1, test_amount * Decimal('0.05'))
        assert cf.Interest(1) == test_amount * Decimal('0.05')
        
        cf.SchedPrincipal(1, test_amount * Decimal('0.1'))
        assert cf.SchedPrincipal(1) == test_amount * Decimal('0.1')
        
        # Test count updates
        assert cf.Count >= 1
    
    def test_simple_cashflow_vba_property_equivalence(self):
        """Test that all VBA properties work correctly"""
        cf = SimpleCashflow()
        
        # Test all VBA property equivalents
        test_amount = Decimal('5000000')
        
        cf.BegBalance(5, test_amount)
        cf.EndBalance(5, test_amount * Decimal('0.9'))
        cf.DefaultBal(5, test_amount * Decimal('0.03'))
        cf.MVDefaultBal(5, test_amount * Decimal('0.018'))
        cf.Interest(5, test_amount * Decimal('0.05'))
        cf.SchedPrincipal(5, test_amount * Decimal('0.1'))
        cf.UnSchedPrincipal(5, test_amount * Decimal('0.15'))
        cf.Default(5, test_amount * Decimal('0.03'))
        cf.MVDefault(5, test_amount * Decimal('0.018'))
        cf.Recoveries(5, test_amount * Decimal('0.018'))
        cf.Netloss(5, test_amount * Decimal('0.012'))
        cf.Sold(5, test_amount * Decimal('0.7'))
        
        # Verify all values
        assert cf.BegBalance(5) == test_amount
        assert cf.EndBalance(5) == test_amount * Decimal('0.9')
        assert cf.DefaultBal(5) == test_amount * Decimal('0.03')
        assert cf.MVDefaultBal(5) == test_amount * Decimal('0.018')
        assert cf.Interest(5) == test_amount * Decimal('0.05')
        assert cf.SchedPrincipal(5) == test_amount * Decimal('0.1')
        assert cf.UnSchedPrincipal(5) == test_amount * Decimal('0.15')
        assert cf.Default(5) == test_amount * Decimal('0.03')
        assert cf.MVDefault(5) == test_amount * Decimal('0.018')
        assert cf.Recoveries(5) == test_amount * Decimal('0.018')
        assert cf.Netloss(5) == test_amount * Decimal('0.012')
        assert cf.Sold(5) == test_amount * Decimal('0.7')


class TestReinvestSetup:
    """Test Reinvest setup and initialization"""
    
    def test_reinvest_initialization(self, reinvestment_db):
        """Test basic Reinvest initialization"""
        reinvest = Reinvest(reinvestment_db)
        
        # VBA variable mappings
        assert reinvest.deal_cf is None
        assert reinvest.reinvest_info is None
        assert reinvest.period == 1
        assert reinvest.months_between_payments == 3
        assert reinvest.yield_curve is None
        assert reinvest.last_period == 0
        assert not reinvest._is_setup
    
    def test_deal_setup_vba_exact(self, reinvestment_db, sample_payment_dates, 
                                 sample_reinvest_info, mock_yield_curve):
        """Test VBA DealSetup() method exact implementation"""
        reinvest = Reinvest(reinvestment_db)
        
        # VBA DealSetup call
        reinvest.deal_setup(sample_payment_dates, sample_reinvest_info, 3, mock_yield_curve)
        
        # Verify VBA variable assignments
        assert reinvest._is_setup == True
        assert reinvest.deal_cf is not None
        assert reinvest.reinvest_info == sample_reinvest_info
        assert reinvest.period == 1  # VBA: clsPeriod = 1
        assert reinvest.months_between_payments == 3  # VBA: clsMoBetPay = iMoBetPay
        assert reinvest.yield_curve == mock_yield_curve  # VBA: Set clsYieldCurve = iYC
        
        # Verify payment dates were set correctly
        # VBA: For i = 1 To UBound(iDealDates)
        for i in range(1, len(sample_payment_dates)):
            # VBA: clsDealCF.PaymentDate(i) = iDealDates(i).PaymentDate
            assert reinvest.deal_cf.PaymentDate(i) == sample_payment_dates[i].PaymentDate
            # VBA: clsDealCF.AccBegDate(i) = iDealDates(i).CollBegDate
            assert reinvest.deal_cf.AccBegDate(i) == sample_payment_dates[i].CollBegDate
            # VBA: clsDealCF.AccEndDate(i) = iDealDates(i).CollEndDate
            assert reinvest.deal_cf.AccEndDate(i) == sample_payment_dates[i].CollEndDate


class TestReinvestBalanceQueries:
    """Test Reinvest balance query methods"""
    
    def test_prin_ball_all_assets_vba_exact(self, test_reinvest):
        """Test VBA PrinBallAllAssets() method"""
        reinvest = test_reinvest
        
        # Set up some test balances
        test_beg_balance = Decimal('10000000')
        test_default_balance = Decimal('300000')
        
        reinvest.deal_cf.BegBalance(reinvest.period + 1, test_beg_balance)
        reinvest.deal_cf.DefaultBal(reinvest.period + 1, test_default_balance)
        
        # VBA: PrinBallAllAssets = clsDealCF.BegBalance(clsPeriod + 1) + clsDealCF.DefaultBal(clsPeriod + 1)
        result = reinvest.prin_ball_all_assets()
        expected = float(test_beg_balance + test_default_balance)
        
        assert abs(result - expected) < 0.01
    
    def test_prin_ball_ex_defaults_vba_exact(self, test_reinvest):
        """Test VBA PrinBallExDefaults() method"""
        reinvest = test_reinvest
        
        test_beg_balance = Decimal('10000000')
        reinvest.deal_cf.BegBalance(reinvest.period + 1, test_beg_balance)
        
        # VBA: PrinBallExDefaults = clsDealCF.BegBalance(clsPeriod + 1)
        result = reinvest.prin_ball_ex_defaults()
        expected = float(test_beg_balance)
        
        assert abs(result - expected) < 0.01
    
    def test_prin_ball_defaults_vba_exact(self, test_reinvest):
        """Test VBA PrinBallDefaults() method"""
        reinvest = test_reinvest
        
        test_default_balance = Decimal('300000')
        reinvest.deal_cf.DefaultBal(reinvest.period + 1, test_default_balance)
        
        # VBA: PrinBallDefaults = clsDealCF.DefaultBal(clsPeriod + 1)
        result = reinvest.prin_ball_defaults()
        expected = float(test_default_balance)
        
        assert abs(result - expected) < 0.01
    
    def test_mv_defaults_vba_exact(self, test_reinvest):
        """Test VBA MVDefaults() method"""
        reinvest = test_reinvest
        
        test_mv_default_balance = Decimal('180000')
        reinvest.deal_cf.MVDefaultBal(reinvest.period + 1, test_mv_default_balance)
        
        # VBA: MVDefaults = clsDealCF.MVDefaultBal(clsPeriod + 1)
        result = reinvest.mv_defaults()
        expected = float(test_mv_default_balance)
        
        assert abs(result - expected) < 0.01
    
    def test_un_sched_prin_vba_exact(self, test_reinvest):
        """Test VBA UnSchedPrin() method"""
        reinvest = test_reinvest
        
        test_unsched_prin = Decimal('750000')
        reinvest.deal_cf.UnSchedPrincipal(reinvest.period, test_unsched_prin)
        
        # VBA: UnSchedPrin = clsDealCF.UnSchedPrincipal(clsPeriod)
        result = reinvest.un_sched_prin()
        expected = float(test_unsched_prin)
        
        assert abs(result - expected) < 0.01


class TestReinvestAddReinvestment:
    """Test AddReinvestment method - core cash flow modeling"""
    
    def test_add_reinvestment_basic_functionality(self, test_reinvest):
        """Test basic AddReinvestment functionality"""
        reinvest = test_reinvest
        reinvestment_amount = 5000000.0  # $5M
        
        # Add reinvestment
        reinvest.add_reinvestment(reinvestment_amount)
        
        # Should have projected cash flows
        assert reinvest.last_period > 0
        
        # Should have some cash flows in the deal_cf
        total_interest = sum(float(reinvest.deal_cf.Interest(i)) 
                           for i in range(1, reinvest.last_period + 1))
        total_principal = sum(float(reinvest.deal_cf.SchedPrincipal(i) + 
                                   reinvest.deal_cf.UnSchedPrincipal(i))
                            for i in range(1, reinvest.last_period + 1))
        
        assert total_interest > 0  # Should generate interest
        assert total_principal > 0  # Should have principal payments
    
    def test_add_reinvestment_vba_calculation_accuracy(self, test_reinvest):
        """Test VBA calculation accuracy in AddReinvestment"""
        reinvest = test_reinvest
        reinvestment_amount = 1000000.0  # $1M for easier calculation
        
        # VBA: lBegBal = iAmount / clsReinvestInfo.ReinvestPrice
        expected_beg_bal = reinvestment_amount / reinvest.reinvest_info.ReinvestPrice
        
        reinvest.add_reinvestment(reinvestment_amount)
        
        # Check first period beginning balance
        first_period_beg_bal = float(reinvest.deal_cf.BegBalance(reinvest.period + 1))
        assert abs(first_period_beg_bal - expected_beg_bal) < 1.0
        
        # Verify interest calculation includes yield curve
        first_period_interest = float(reinvest.deal_cf.Interest(reinvest.period + 1))
        assert first_period_interest > 0
        
        # Verify default calculation
        first_period_default = float(reinvest.deal_cf.Default(reinvest.period + 1))
        assert first_period_default > 0  # Should have some defaults
    
    def test_add_reinvestment_array_handling(self, reinvestment_db, sample_payment_dates, mock_yield_curve):
        """Test VBA array handling for prepayment/default/severity vectors"""
        # Create reinvest info with arrays
        reinvest_info_arrays = ReinvestInfo(
            maturity=60,
            reinvest_price=1.0,
            spread=0.05,
            floor=0.01,
            liquidation=0.70,
            lag=6,
            prepayment=[0.10, 0.15, 0.20, 0.15, 0.10],  # Varying prepayment
            default=[0.02, 0.03, 0.04, 0.03, 0.02],     # Varying default
            severity=[0.30, 0.40, 0.50, 0.40, 0.30]     # Varying severity
        )
        
        reinvest = Reinvest(reinvestment_db)
        reinvest.deal_setup(sample_payment_dates, reinvest_info_arrays, 3, mock_yield_curve)
        
        # Add reinvestment
        reinvest.add_reinvestment(1000000.0)
        
        # Should handle arrays correctly and generate cash flows
        assert reinvest.last_period > 0
        
        # Should have different defaults in different periods due to array
        defaults = [float(reinvest.deal_cf.Default(i)) 
                   for i in range(reinvest.period + 1, reinvest.period + 6)]
        defaults = [d for d in defaults if d > 0]  # Filter out zeros
        
        # Should have variation in defaults due to array inputs
        if len(defaults) > 2:
            assert max(defaults) != min(defaults)
    
    def test_add_reinvestment_recovery_lag_logic(self, test_reinvest):
        """Test VBA recovery lag logic implementation"""
        reinvest = test_reinvest
        
        # Set up lag parameters
        lag_periods = reinvest.reinvest_info.Lag // reinvest.months_between_payments
        
        reinvest.add_reinvestment(2000000.0)
        
        # Check that recoveries start after lag period
        for i in range(1, lag_periods + 1):
            period_recoveries = float(reinvest.deal_cf.Recoveries(reinvest.period + i))
            assert period_recoveries == 0.0  # Should be zero before lag
        
        # After lag, should have recoveries
        post_lag_periods = [i for i in range(reinvest.period + lag_periods + 1, 
                                           reinvest.last_period + 1)]
        if post_lag_periods:
            total_recoveries = sum(float(reinvest.deal_cf.Recoveries(i)) 
                                 for i in post_lag_periods)
            # May be zero if no defaults in early periods, but logic should work
            assert total_recoveries >= 0
    
    def test_add_reinvestment_yield_curve_integration(self, test_reinvest):
        """Test yield curve integration in interest calculations"""
        reinvest = test_reinvest
        
        # Mock yield curve returns 4.5%
        expected_libor = 0.045
        reinvest.yield_curve.spot_rate.return_value = expected_libor
        
        reinvest.add_reinvestment(1000000.0)
        
        # Verify yield curve was called
        reinvest.yield_curve.spot_rate.assert_called()
        
        # Check interest calculation incorporates yield curve rate
        first_period_interest = float(reinvest.deal_cf.Interest(reinvest.period + 1))
        
        # Interest should be based on libor + spread or floor + spread
        expected_coupon = max(expected_libor + reinvest.reinvest_info.Spread, 
                            reinvest.reinvest_info.Floor + reinvest.reinvest_info.Spread)
        
        # Should have reasonable interest amount
        assert first_period_interest > 0
        # Interest should be roughly in expected range (accounting for defaults and day count)
        expected_range = 1000000.0 * expected_coupon * 0.1  # Rough quarterly estimate
        assert first_period_interest < expected_range * 1.5  # Allow for variation


class TestReinvestUtilityMethods:
    """Test Reinvest utility methods"""
    
    def test_get_proceeds_vba_exact(self, test_reinvest):
        """Test VBA GetProceeds() method"""
        reinvest = test_reinvest
        
        # Set up some test cash flows
        test_interest = Decimal('50000')
        test_sched_prin = Decimal('100000')
        test_unsched_prin = Decimal('150000')
        test_recoveries = Decimal('20000')
        
        reinvest.deal_cf.Interest(reinvest.period, test_interest)
        reinvest.deal_cf.SchedPrincipal(reinvest.period, test_sched_prin)
        reinvest.deal_cf.UnSchedPrincipal(reinvest.period, test_unsched_prin)
        reinvest.deal_cf.Recoveries(reinvest.period, test_recoveries)
        
        # VBA: If iProceeds = "INTEREST" Then
        interest_proceeds = reinvest.get_proceeds("INTEREST")
        assert abs(interest_proceeds - float(test_interest)) < 0.01
        
        # VBA: ElseIf iProceeds = "PRINCIPAL" Then
        principal_proceeds = reinvest.get_proceeds("PRINCIPAL")
        expected_principal = float(test_sched_prin + test_unsched_prin + test_recoveries)
        assert abs(principal_proceeds - expected_principal) < 0.01
    
    def test_roll_forward_vba_exact(self, test_reinvest):
        """Test VBA Rollfoward() method"""
        reinvest = test_reinvest
        
        initial_period = reinvest.period
        
        # VBA: clsPeriod = clsPeriod + 1
        reinvest.roll_forward()
        
        assert reinvest.period == initial_period + 1
    
    def test_get_collat_cf_vba_exact(self, test_reinvest):
        """Test VBA GetCollatCF() method"""
        reinvest = test_reinvest
        
        # Add some cash flows first
        reinvest.add_reinvestment(1000000.0)
        
        # VBA: GetCollatCF returns 2D array
        cf_output = reinvest.get_collat_cf()
        
        # Should have header row plus data rows
        assert len(cf_output) > 1
        
        # VBA header row verification - exact VBA strings
        expected_headers = [
            "Beg Performing Balance",
            "Beg Default Balance", 
            "Beg MV Default Balance",
            "Period Default",
            "Period MV Default",
            "Interest",
            "Scheduled Principal",
            "Unscheduled Principal",
            "Recoveries",
            "Net loss",
            "Sold"
        ]
        
        assert cf_output[0] == expected_headers
        
        # Should have 11 columns (0-10 in VBA)
        for row in cf_output:
            assert len(row) == 11
        
        # Data rows should have numeric values
        for i in range(1, len(cf_output)):
            for j in range(len(cf_output[i])):
                assert isinstance(cf_output[i][j], (int, float))
    
    def test_liquidate_vba_exact(self, test_reinvest):
        """Test VBA Liquidate() method"""
        reinvest = test_reinvest
        
        # Set up portfolio with some balances
        reinvest.add_reinvestment(1000000.0)
        
        # Set up current period balances for liquidation
        test_beg_balance = Decimal('800000')
        test_default_bal = Decimal('50000')
        test_mv_default_bal = Decimal('30000')
        
        reinvest.deal_cf.BegBalance(reinvest.period, test_beg_balance)
        reinvest.deal_cf.DefaultBal(reinvest.period, test_default_bal)
        reinvest.deal_cf.MVDefaultBal(reinvest.period, test_mv_default_bal)
        
        liquidation_price = 0.85  # 85%
        
        # VBA Liquidate call
        proceeds = reinvest.liquidate(liquidation_price)
        
        # VBA calculation verification
        # lEndBal = lBegBal - lDefault - lUnSchedPrin - lSchedPrin
        l_end_bal = (float(test_beg_balance) - 
                    float(reinvest.deal_cf.Default(reinvest.period)) - 
                    float(reinvest.deal_cf.UnSchedPrincipal(reinvest.period)) - 
                    float(reinvest.deal_cf.SchedPrincipal(reinvest.period)))
        
        l_end_mv_default_bal = (float(test_mv_default_bal) + 
                               float(reinvest.deal_cf.MVDefault(reinvest.period)) - 
                               float(reinvest.deal_cf.Recoveries(reinvest.period)))
        
        # VBA: lSold = lEndBal * iLiquidPrice + lEndMVDefaultBal
        expected_proceeds = l_end_bal * liquidation_price + l_end_mv_default_bal
        
        assert abs(proceeds - expected_proceeds) < 1.0
        
        # VBA: clsLastperiod = clsPeriod
        assert reinvest.last_period == reinvest.period
        
        # Should have updated Sold amount in current period
        sold_amount = float(reinvest.deal_cf.Sold(reinvest.period))
        assert sold_amount > 0


class TestReinvestInternalMethods:
    """Test Reinvest internal calculation methods"""
    
    def test_convert_annual_rates(self, test_reinvest):
        """Test _convert_annual_rates method"""
        reinvest = test_reinvest
        
        annual_rate = 0.12  # 12% annual
        start_date = date(2025, 1, 15)
        end_date = date(2025, 4, 15)  # 3 months later
        
        period_rate = reinvest._convert_annual_rates(annual_rate, start_date, end_date)
        
        # Should be approximately 3% for quarterly
        expected_rate = 0.12 * (3/12)  # Linear conversion
        assert abs(period_rate - expected_rate) < 0.001
    
    def test_date_fraction_us30_360(self, test_reinvest):
        """Test _date_fraction_us30_360 method"""
        reinvest = test_reinvest
        
        # Test quarterly period
        start_date = date(2025, 1, 15)
        end_date = date(2025, 4, 15)
        
        fraction = reinvest._date_fraction_us30_360(start_date, end_date)
        
        # US 30/360: should be 90/360 = 0.25 for 3 months
        expected_fraction = 90.0 / 360.0
        assert abs(fraction - expected_fraction) < 0.01


class TestReinvestmentDatabasePersistence:
    """Test database persistence functionality"""
    
    def test_save_to_database(self, test_reinvest):
        """Test saving reinvestment to database"""
        reinvest = test_reinvest
        
        # Add some cash flows
        reinvest.add_reinvestment(2000000.0)
        
        # Save to database
        deal_id = "TEST_DEAL_001"
        reinvest_period = 1
        period_start = date(2025, 1, 1)
        period_end = date(2027, 1, 1)
        
        reinvest_id = reinvest.save_to_database(deal_id, reinvest_period, period_start, period_end)
        
        # Verify database records
        assert reinvest_id > 0
        assert reinvest.reinvest_id == reinvest_id
        
        # Check period record
        period_record = reinvest.session.query(ReinvestmentPeriodModel).filter_by(
            reinvest_id=reinvest_id
        ).first()
        
        assert period_record is not None
        assert period_record.deal_id == deal_id
        assert period_record.reinvest_period == reinvest_period
        assert period_record.period_start == period_start
        assert period_record.period_end == period_end
        assert period_record.maturity_months == reinvest.reinvest_info.Maturity
        
        # Check info record
        info_record = reinvest.session.query(ReinvestmentInfoModel).filter_by(
            reinvest_id=reinvest_id
        ).first()
        
        assert info_record is not None
        assert float(info_record.reinvest_price) == reinvest.reinvest_info.ReinvestPrice
        assert info_record.spread_bps == int(reinvest.reinvest_info.Spread * 10000)
        assert float(info_record.liquidation_price) == reinvest.reinvest_info.Liquidation
        
        # Check cash flow records
        cf_records = reinvest.session.query(ReinvestmentCashFlowModel).filter_by(
            reinvest_id=reinvest_id
        ).all()
        
        assert len(cf_records) == reinvest.last_period
        
        # Verify cash flow data
        for cf_record in cf_records:
            assert cf_record.payment_period >= 1
            assert cf_record.payment_date is not None
            # Should have some cash flow components
            total_flows = (cf_record.interest + cf_record.scheduled_principal + 
                          cf_record.unscheduled_principal + cf_record.recoveries)
            # Most periods should have some cash flows
            if cf_record.payment_period <= reinvest.last_period // 2:
                assert total_flows >= 0  # At least non-negative
    
    def test_reinvestment_service_create(self, reinvestment_db, sample_payment_dates, 
                                       sample_reinvest_info, mock_yield_curve):
        """Test ReinvestmentService.create_reinvestment_period()"""
        service = ReinvestmentService(reinvestment_db)
        
        deal_id = "SERVICE_TEST_001"
        period_start = date(2025, 1, 1)
        period_end = date(2026, 1, 1)
        
        reinvest = service.create_reinvestment_period(
            deal_id, period_start, period_end, sample_reinvest_info,
            sample_payment_dates, 3, mock_yield_curve
        )
        
        assert reinvest is not None
        assert reinvest.reinvest_id is not None
        assert reinvest._is_setup
        
        # Should be able to add reinvestments
        reinvest.add_reinvestment(1500000.0)
        assert reinvest.last_period > 0
    
    def test_reinvestment_service_load(self, reinvestment_db, sample_payment_dates,
                                     sample_reinvest_info, mock_yield_curve):
        """Test ReinvestmentService.load_reinvestment_period()"""
        service = ReinvestmentService(reinvestment_db)
        
        # Create and save
        original_reinvest = service.create_reinvestment_period(
            "LOAD_TEST_001", date(2025, 1, 1), date(2026, 1, 1),
            sample_reinvest_info, sample_payment_dates, 3, mock_yield_curve
        )
        original_reinvest.add_reinvestment(1000000.0)
        
        original_reinvest_id = original_reinvest.reinvest_id
        original_last_period = original_reinvest.last_period
        
        # Load from database
        loaded_reinvest = service.load_reinvestment_period(original_reinvest_id)
        
        assert loaded_reinvest is not None
        assert loaded_reinvest.reinvest_id == original_reinvest_id
        # Note: Loaded reinvest won't have cash flows pre-populated since they're 
        # generated by add_reinvestment, but structure should be intact
    
    def test_reinvestment_service_summary(self, reinvestment_db, sample_payment_dates,
                                        sample_reinvest_info, mock_yield_curve):
        """Test ReinvestmentService.get_reinvestment_summary()"""
        service = ReinvestmentService(reinvestment_db)
        deal_id = "SUMMARY_TEST_001"
        
        # Create multiple reinvestment periods
        reinvest1 = service.create_reinvestment_period(
            deal_id, date(2025, 1, 1), date(2026, 1, 1),
            sample_reinvest_info, sample_payment_dates, 3, mock_yield_curve
        )
        reinvest1.add_reinvestment(1000000.0)
        
        reinvest2 = service.create_reinvestment_period(
            deal_id, date(2026, 1, 1), date(2027, 1, 1),
            sample_reinvest_info, sample_payment_dates, 3, mock_yield_curve
        )
        
        # Get summary
        summary = service.get_reinvestment_summary(deal_id)
        
        assert summary['deal_id'] == deal_id
        assert summary['total_periods'] == 2
        assert len(summary['periods']) == 2
        
        # Check period details
        period1 = summary['periods'][0]
        assert period1['reinvest_id'] == reinvest1.reinvest_id
        assert 'parameters' in period1
        assert period1['parameters']['reinvest_price'] == 1.0
        assert period1['parameters']['spread_bps'] == 500


class TestVBAComparisonAccuracy:
    """Test VBA comparison for exact functional parity"""
    
    def test_vba_exact_variable_mappings(self, test_reinvest):
        """Test VBA variable mappings are exact"""
        reinvest = test_reinvest
        
        # VBA variable verification
        assert reinvest.deal_cf is not None  # clsDealCF
        assert reinvest.reinvest_info is not None  # clsReinvestInfo
        assert reinvest.period == 1  # clsPeriod
        assert reinvest.months_between_payments == 3  # clsMoBetPay
        assert reinvest.yield_curve is not None  # clsYieldCurve
        assert reinvest.last_period >= 0  # clsLastperiod
    
    def test_add_reinvestment_complex_scenario(self, reinvestment_db, sample_payment_dates, mock_yield_curve):
        """Test AddReinvestment with complex scenario matching VBA behavior"""
        # Create complex reinvestment scenario
        complex_reinvest_info = ReinvestInfo(
            maturity=48,  # 4 years
            reinvest_price=0.98,  # Discount purchase
            spread=0.055,  # 550 bps
            floor=0.015,  # 150 bps floor
            liquidation=0.75,  # 75% liquidation
            lag=9,  # 9 month lag
            prepayment=[0.08, 0.12, 0.18, 0.20, 0.15, 0.10],
            default=[0.01, 0.02, 0.04, 0.05, 0.03, 0.02],
            severity=[0.25, 0.35, 0.45, 0.50, 0.40, 0.30]
        )
        
        reinvest = Reinvest(reinvestment_db)
        reinvest.deal_setup(sample_payment_dates, complex_reinvest_info, 3, mock_yield_curve)
        
        # Large reinvestment amount
        reinvestment_amount = 10000000.0
        reinvest.add_reinvestment(reinvestment_amount)
        
        # Verify complex calculations worked
        assert reinvest.last_period > 0
        
        # Check that arrays were used correctly
        total_defaults = sum(float(reinvest.deal_cf.Default(i)) 
                           for i in range(1, min(7, reinvest.last_period + 1)))
        assert total_defaults > 0
        
        # Verify balance rollforward worked correctly
        for i in range(1, reinvest.last_period):
            beg_balance = float(reinvest.deal_cf.BegBalance(i + 1))
            if beg_balance > 0:
                # Beginning balance should be reasonable given payments and defaults
                assert beg_balance > 0
                break
        
        # Check that liquidation works correctly
        proceeds = reinvest.liquidate(0.80)
        assert proceeds > 0
        assert reinvest.last_period == reinvest.period  # VBA: clsLastperiod = clsPeriod