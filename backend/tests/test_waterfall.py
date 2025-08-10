"""
Test CLO Waterfall Logic
Validates payment priorities, trigger events, and cash distribution
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.waterfall import (
    WaterfallConfiguration, WaterfallExecution, WaterfallCalculator,
    WaterfallStep, PaymentPriority
)
from app.models.clo_deal import CLODeal, CLOTranche, DealAsset
from app.models.asset import Asset
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
def sample_deal(session):
    """Create sample CLO deal with tranches"""
    
    # Create deal
    deal = CLODeal(
        deal_id="TEST-CLO-2023",
        deal_name="Test CLO 2023-1",
        manager_name="Test Manager",
        effective_date=date(2023, 6, 15),
        first_payment_date=date(2023, 9, 15),
        maturity_date=date(2030, 6, 15),
        target_par_amount=Decimal('400000000'),
        payment_frequency=4,
        deal_status="ACTIVE"
    )
    session.add(deal)
    
    # Create tranches
    tranches = [
        CLOTranche(
            tranche_id="TEST-CLO-2023-A",
            deal_id="TEST-CLO-2023",
            tranche_name="Class A Notes",
            initial_balance=Decimal('280000000'),
            current_balance=Decimal('280000000'),
            coupon_rate=Decimal('0.055'),
            coupon_type="FLOAT",
            seniority_level=1,
            payment_rank=1,
            interest_deferrable=False
        ),
        CLOTranche(
            tranche_id="TEST-CLO-2023-B", 
            deal_id="TEST-CLO-2023",
            tranche_name="Class B Notes",
            initial_balance=Decimal('45000000'),
            current_balance=Decimal('45000000'),
            coupon_rate=Decimal('0.070'),
            coupon_type="FLOAT",
            seniority_level=2,
            payment_rank=2,
            interest_deferrable=False
        ),
        CLOTranche(
            tranche_id="TEST-CLO-2023-E",
            deal_id="TEST-CLO-2023", 
            tranche_name="Class E Notes",
            initial_balance=Decimal('20000000'),
            current_balance=Decimal('20000000'),
            coupon_rate=Decimal('0.150'),
            coupon_type="FIXED",
            seniority_level=5,
            payment_rank=5,
            interest_deferrable=True
        )
    ]
    
    for tranche in tranches:
        session.add(tranche)
    
    session.commit()
    return deal


@pytest.fixture
def waterfall_config(session, sample_deal):
    """Create waterfall configuration"""
    
    config = WaterfallConfiguration(
        deal_id=sample_deal.deal_id,
        config_name="Standard Waterfall",
        effective_date=date(2023, 6, 15),
        payment_rules='[]',  # Simplified for testing
        
        # Reserve requirements
        interest_reserve_target=Decimal('5000000'),
        interest_reserve_cap=Decimal('10000000'),
        
        # Fee rates (annual basis)
        senior_mgmt_fee_rate=Decimal('0.0040'),    # 40bps
        junior_mgmt_fee_rate=Decimal('0.0020'),    # 20bps
        incentive_fee_rate=Decimal('0.2000'),      # 20% above hurdle
        incentive_hurdle_rate=Decimal('0.0800'),   # 8% hurdle
        
        # Fixed fees (annual)
        trustee_fee_annual=Decimal('100000'),      # $100k/year
        admin_fee_cap=Decimal('500000')            # $500k/year cap
    )
    
    session.add(config)
    session.commit()
    return config


@pytest.fixture 
def sample_assets(session, sample_deal):
    """Create sample assets for deal"""
    
    asset = Asset(
        blkrock_id="TEST001",
        issue_name="Test Corporate Loan",
        issuer_name="Test Corporation", 
        par_amount=Decimal('100000000'),
        maturity=date(2028, 6, 15),
        coupon=Decimal('0.0575'),
        coupon_type="FLOAT"
    )
    session.add(asset)
    
    deal_asset = DealAsset(
        deal_id=sample_deal.deal_id,
        blkrock_id="TEST001",
        par_amount=Decimal('100000000'),
        purchase_price=Decimal('1.0000'),
        position_status="ACTIVE"
    )
    session.add(deal_asset)
    
    session.commit()
    return [asset]


class TestWaterfallCalculator:
    """Test waterfall calculation logic"""
    
    def test_waterfall_initialization(self, session, sample_deal, waterfall_config):
        """Test waterfall calculator initialization"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        assert calculator.deal_id == sample_deal.deal_id
        assert calculator.config.config_name == "Standard Waterfall"
        assert calculator.available_cash == Decimal('0')
    
    def test_senior_expenses_calculation(self, session, sample_deal, waterfall_config, sample_assets):
        """Test senior fees and expenses calculation"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Test fee calculations
        trustee_fee = calculator._calculate_trustee_fee()
        assert trustee_fee == Decimal('25000.00')  # $100k/year ÷ 4
        
        admin_fee = calculator._calculate_admin_fee() 
        assert admin_fee == Decimal('125000.00')   # $500k/year ÷ 4
        
        senior_mgmt_fee = calculator._calculate_senior_mgmt_fee()
        # 40bps on $100M collateral ÷ 4 = $100,000
        assert senior_mgmt_fee == Decimal('100000.00')
    
    def test_interest_payments_calculation(self, session, sample_deal, waterfall_config):
        """Test note interest calculations"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        tranches = calculator._get_tranches_by_seniority()
        
        # Class A interest: 5.5% on $280M ÷ 4 = $3.85M
        class_a_interest = calculator._calculate_interest_due(tranches[0])
        assert class_a_interest == Decimal('3850000.00')
        
        # Class B interest: 7.0% on $45M ÷ 4 = $787.5k
        class_b_interest = calculator._calculate_interest_due(tranches[1])
        assert class_b_interest == Decimal('787500.00')
    
    def test_complete_waterfall_execution(self, session, sample_deal, waterfall_config, sample_assets):
        """Test complete waterfall execution"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Execute waterfall with $10M collection
        collection_amount = Decimal('10000000')
        execution = calculator.execute_waterfall(collection_amount)
        
        # Verify execution record
        assert execution.deal_id == sample_deal.deal_id
        assert execution.collection_amount == collection_amount
        assert execution.execution_status == 'COMPLETED'
        assert len(execution.payments) > 0
        
        # Check payments were created
        payment_steps = [p.payment_step for p in execution.payments]
        
        # Should have senior expense payments
        assert WaterfallStep.TRUSTEE_FEES.value in payment_steps
        assert WaterfallStep.ADMIN_FEES.value in payment_steps
        assert WaterfallStep.SENIOR_MGMT_FEES.value in payment_steps
    
    def test_payment_priorities(self, session, sample_deal, waterfall_config):
        """Test payment priority ordering"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Test priority classifications
        assert calculator._get_payment_priority(WaterfallStep.TRUSTEE_FEES.value) == PaymentPriority.SENIOR.value
        assert calculator._get_payment_priority(WaterfallStep.CLASS_A_INTEREST.value) == PaymentPriority.SENIOR.value
        assert calculator._get_payment_priority(WaterfallStep.CLASS_E_INTEREST.value) == PaymentPriority.SUBORDINATED.value
        assert calculator._get_payment_priority(WaterfallStep.RESIDUAL_EQUITY.value) == PaymentPriority.RESIDUAL.value
    
    def test_cash_constraints(self, session, sample_deal, waterfall_config, sample_assets):
        """Test waterfall behavior with limited cash"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Execute with limited cash (only $500k)
        limited_cash = Decimal('500000')
        execution = calculator.execute_waterfall(limited_cash)
        
        # Should complete but with deferred payments
        assert execution.execution_status == 'COMPLETED'
        
        # Check that some payments were made but others deferred
        total_paid = sum(p.amount_paid for p in execution.payments)
        total_deferred = sum(p.amount_deferred for p in execution.payments)
        
        assert total_paid <= limited_cash
        assert total_deferred > 0  # Some payments should be deferred
    
    def test_reserve_funding(self, session, sample_deal, waterfall_config):
        """Test interest reserve account funding"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Mock current reserve balance as $2M (below $5M target)
        calculator._get_current_reserve_balance = lambda: Decimal('2000000')
        
        collection_amount = Decimal('10000000')
        execution = calculator.execute_waterfall(collection_amount)
        
        # Should have reserve funding payment
        reserve_payments = [p for p in execution.payments 
                          if p.payment_step == WaterfallStep.INTEREST_RESERVE.value]
        
        assert len(reserve_payments) > 0
        # Should fund up to target ($5M - $2M = $3M)
        assert reserve_payments[0].amount_paid <= Decimal('3000000')
    
    def test_principal_acceleration(self, session, sample_deal, waterfall_config):
        """Test principal payment acceleration when tests fail"""
        
        calculator = WaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Mock failing OC/IC tests
        calculator._check_overcollateralization_tests = lambda: False
        calculator._check_interest_coverage_tests = lambda: False
        
        collection_amount = Decimal('50000000')  # Large amount
        execution = calculator.execute_waterfall(collection_amount)
        
        # Should have accelerated Class A principal payments
        class_a_principal = [p for p in execution.payments 
                            if p.payment_step == WaterfallStep.CLASS_A_PRINCIPAL.value]
        
        assert len(class_a_principal) > 0
        assert "accelerated" in class_a_principal[0].payment_notes.lower()


class TestWaterfallConfiguration:
    """Test waterfall configuration management"""
    
    def test_configuration_creation(self, session, sample_deal):
        """Test waterfall configuration creation"""
        
        config = WaterfallConfiguration(
            deal_id=sample_deal.deal_id,
            config_name="Test Config",
            effective_date=date(2023, 6, 15),
            payment_rules='{"test": "rules"}',
            senior_mgmt_fee_rate=Decimal('0.004')
        )
        
        session.add(config)
        session.commit()
        
        # Verify saved correctly
        saved_config = session.query(WaterfallConfiguration).filter_by(
            deal_id=sample_deal.deal_id
        ).first()
        
        assert saved_config.config_name == "Test Config"
        assert saved_config.senior_mgmt_fee_rate == Decimal('0.004')
    
    def test_payment_rules_parsing(self, session, sample_deal):
        """Test JSON payment rules parsing"""
        
        rules = [
            {"step": "TRUSTEE_FEES", "priority": 1},
            {"step": "CLASS_A_INTEREST", "priority": 2}
        ]
        
        config = WaterfallConfiguration(
            deal_id=sample_deal.deal_id,
            config_name="Test Config",
            effective_date=date(2023, 6, 15),
            payment_rules=str(rules).replace("'", '"')  # Convert to proper JSON
        )
        
        session.add(config)
        session.commit()
        
        # Test parsing
        parsed_rules = config.get_payment_rules()
        assert len(parsed_rules) == 2
        assert parsed_rules[0]["step"] == "TRUSTEE_FEES"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])