"""
Test Asset Model - Validation of VBA-to-Python conversion
Tests core functionality of Asset.cls conversion including cash flows and filtering
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.asset import Asset, AssetFlags, RatingEnum, CouponTypeEnum, DayCountEnum
from app.models.cash_flow import AssetCashFlow, CashFlowCalculator
from app.core.database import Base


@pytest.fixture
def engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_asset(session):
    """Create sample asset for testing"""
    flags = AssetFlags(
        pik_asset=False,
        default_asset=False,
        cov_lite=True,
        current_pay=True
    )
    
    asset = Asset(
        blkrock_id="TEST001",
        issue_name="Test Corporate Term Loan B",
        issuer_name="Test Corporation",
        par_amount=Decimal('1000000.00'),
        coupon=Decimal('0.0575'),  # 5.75%
        cpn_spread=Decimal('0.0325'),  # 325 bps
        maturity=date(2028, 6, 15),
        dated_date=date(2023, 6, 15),
        first_payment_date=date(2023, 9, 15),
        coupon_type=CouponTypeEnum.FLOAT,
        payment_freq=4,  # Quarterly
        day_count=DayCountEnum.ACTUAL_360,
        mdy_rating="B1",
        sp_rating="B+",
        currency="USD",
        flags=flags.dict(),
        country="US",
        mdy_industry="Software",
        facility_size=Decimal('5000000.00')
    )
    
    session.add(asset)
    session.commit()
    return asset


class TestAssetModel:
    """Test Asset model functionality"""
    
    def test_asset_creation(self, sample_asset):
        """Test basic asset creation and properties"""
        assert sample_asset.blkrock_id == "TEST001"
        assert sample_asset.par_amount == Decimal('1000000.00')
        assert sample_asset.coupon_type == CouponTypeEnum.FLOAT
        assert sample_asset.payment_freq == 4
        
    def test_asset_flags(self, sample_asset):
        """Test asset flags functionality"""
        assert sample_asset.flags['cov_lite'] == True
        assert sample_asset.flags['pik_asset'] == False
        assert sample_asset.is_pik_asset == False
        assert sample_asset.is_defaulted == False
        
    def test_effective_coupon_calculation(self, sample_asset):
        """Test effective coupon calculation"""
        # For floating rate: coupon + spread
        expected_coupon = sample_asset.coupon + sample_asset.cpn_spread
        assert sample_asset.effective_coupon == expected_coupon
        
    def test_interest_accrual_calculation(self, sample_asset):
        """Test interest accrual calculation using QuantLib"""
        start_date = date(2023, 6, 15)
        end_date = date(2023, 9, 15)
        balance = Decimal('1000000.00')
        
        interest = sample_asset.calculate_interest_accrual(start_date, end_date, balance)
        
        # Should be approximately 3 months of interest
        # Using ACTUAL/360 day count: roughly 92/360 * 9% * $1M = $23,000
        assert interest > Decimal('20000')  # Rough validation
        assert interest < Decimal('30000')
        
    def test_cash_flow_generation(self, sample_asset):
        """Test cash flow generation (CalcCF conversion)"""
        analysis_date = date(2023, 6, 15)
        
        # Generate cash flows with some defaults and prepayments
        default_rates = [Decimal('0.00')] * 20  # No defaults initially
        prepay_rates = [Decimal('0.05')] * 20   # 5% CPR
        
        cash_flows = sample_asset.calculate_cash_flows(
            analysis_date=analysis_date,
            default_rate=default_rates,
            prepay_rate=prepay_rates
        )
        
        # Validate structure
        assert 'payment_dates' in cash_flows
        assert 'interest_payments' in cash_flows
        assert 'scheduled_principal' in cash_flows
        assert len(cash_flows['payment_dates']) > 0
        
        # First payment should be the first payment date
        assert cash_flows['payment_dates'][0] == sample_asset.first_payment_date
        
        # Total cash flows should add up to approximately par amount (plus interest)
        total_principal = sum(cash_flows['scheduled_principal']) + sum(cash_flows['unscheduled_principal'])
        assert abs(total_principal - float(sample_asset.par_amount)) < 1000  # Within $1000
        
    def test_apply_filter_basic_comparison(self, sample_asset):
        """Test basic filter functionality (ApplyFilter conversion)"""
        # Test rating comparison
        assert sample_asset.apply_filter("MOODY'S RATING = B1") == True
        assert sample_asset.apply_filter("MOODY'S RATING = B2") == False
        
        # Test industry filter
        assert sample_asset.apply_filter("MOODY'S INDUSTRY = SOFTWARE") == True
        assert sample_asset.apply_filter("S&P INDUSTRY = TECHNOLOGY") == False
        
        # Test numeric comparison
        assert sample_asset.apply_filter("FACILITY SIZE > 1000000") == True
        assert sample_asset.apply_filter("FACILITY SIZE < 1000000") == False
        
    def test_apply_filter_logical_operators(self, sample_asset):
        """Test logical operators in filters"""
        # AND operator
        assert sample_asset.apply_filter("MOODY'S RATING = B1 AND COV-LITE = TRUE") == True
        assert sample_asset.apply_filter("MOODY'S RATING = B1 AND COV-LITE = FALSE") == False
        
        # OR operator  
        assert sample_asset.apply_filter("MOODY'S RATING = B2 OR COV-LITE = TRUE") == True
        assert sample_asset.apply_filter("MOODY'S RATING = B2 OR COV-LITE = FALSE") == False
        
    def test_apply_filter_parentheses(self, sample_asset):
        """Test parentheses in filter expressions"""
        # Complex expression with parentheses
        filter_expr = "(MOODY'S RATING = B1 OR MOODY'S RATING = B2) AND COV-LITE = TRUE"
        assert sample_asset.apply_filter(filter_expr) == True
        
        filter_expr2 = "(MOODY'S RATING = B3 OR MOODY'S RATING = B2) AND COV-LITE = TRUE" 
        assert sample_asset.apply_filter(filter_expr2) == False
        
    def test_rating_validation(self, session):
        """Test rating validation"""
        asset = Asset(
            blkrock_id="TEST002",
            issue_name="Test Asset", 
            issuer_name="Test Issuer",
            par_amount=Decimal('1000000'),
            maturity=date(2025, 12, 31),
            mdy_rating="InvalidRating"
        )
        
        session.add(asset)
        
        # Should raise validation error
        with pytest.raises(ValueError):
            asset.validate_ratings()
            
    def test_financial_data_validation(self, session):
        """Test financial data validation"""
        asset = Asset(
            blkrock_id="TEST003",
            issue_name="Test Asset",
            issuer_name="Test Issuer", 
            par_amount=Decimal('-1000'),  # Invalid negative amount
            maturity=date(2025, 12, 31)
        )
        
        session.add(asset)
        
        # Should raise validation error
        with pytest.raises(ValueError):
            asset.validate_financial_data()


class TestCashFlowCalculations:
    """Test cash flow calculation methods"""
    
    def test_cash_flow_period_calculations(self, session, sample_asset):
        """Test period-based cash flow calculations"""
        # Create sample cash flows
        cash_flows = [
            AssetCashFlow(
                blkrock_id=sample_asset.blkrock_id,
                period_number=1,
                payment_date=date(2023, 9, 15),
                accrual_start_date=date(2023, 6, 15),
                accrual_end_date=date(2023, 9, 15),
                beginning_balance=Decimal('1000000'),
                interest_payment=Decimal('23000'),
                scheduled_principal=Decimal('25000'),
                ending_balance=Decimal('975000')
            ),
            AssetCashFlow(
                blkrock_id=sample_asset.blkrock_id,
                period_number=2,
                payment_date=date(2023, 12, 15),
                accrual_start_date=date(2023, 9, 15),
                accrual_end_date=date(2023, 12, 15),
                beginning_balance=Decimal('975000'),
                interest_payment=Decimal('22000'),
                unscheduled_principal=Decimal('48750'),  # 5% prepayment
                ending_balance=Decimal('926250')
            )
        ]
        
        for cf in cash_flows:
            session.add(cf)
        session.commit()
        
        # Test interest calculation
        interest = CashFlowCalculator.get_interest_in_period(
            cash_flows, date(2023, 6, 1), date(2023, 12, 31)
        )
        assert interest == Decimal('45000')  # 23000 + 22000
        
        # Test principal calculation 
        principal = CashFlowCalculator.get_principal_in_period(
            cash_flows, date(2023, 6, 1), date(2023, 12, 31)
        )
        assert principal == Decimal('73750')  # 25000 + 48750
        
        # Test balance at date
        balance = CashFlowCalculator.get_balance_at_date(
            cash_flows, date(2023, 10, 1)
        )
        assert balance == Decimal('975000')  # After first payment


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])