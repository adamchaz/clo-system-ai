"""
Test suite for Incentive Fee System

Tests the complete incentive fee functionality including VBA parity,
database persistence, and integration capabilities.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import math

from app.core.database import Base
from app.models.incentive_fee import (
    IncentiveFeeStructure,
    SubordinatedPayment,
    IncentiveFeeCalculation,
    FeePaymentTransaction,
    IRRCalculationHistory
)
from app.services.incentive_fee import IncentiveFee, IncentiveFeeService


@pytest.fixture
def incentive_db():
    """Create in-memory database for incentive fee testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def incentive_fee_service(incentive_db):
    """Create incentive fee service with database session"""
    return IncentiveFeeService(incentive_db)


@pytest.fixture
def sample_fee_structure_data():
    """Sample fee structure data for testing"""
    return {
        'deal_id': 'TEST_INCENTIVE_001',
        'fee_structure_name': 'Standard Incentive Fee',
        'hurdle_rate': 0.08,  # 8%
        'incentive_fee_rate': 0.20,  # 20%
        'closing_date': date(2024, 1, 15),
        'description': 'Test incentive fee structure'
    }


@pytest.fixture
def sample_subordinated_payments():
    """Sample subordinated payments for testing"""
    return {
        date(2024, 4, 15): 1000000.0,   # $1M
        date(2024, 7, 15): 1200000.0,   # $1.2M
        date(2024, 10, 15): 950000.0,   # $950K
        date(2025, 1, 15): 1100000.0    # $1.1M
    }


class TestIncentiveFeeService:
    """Test IncentiveFeeService database operations"""
    
    def test_create_fee_structure(self, incentive_fee_service, sample_fee_structure_data):
        """Test creating fee structure"""
        structure = incentive_fee_service.create_fee_structure(**sample_fee_structure_data)
        
        assert structure.fee_structure_id is not None
        assert structure.deal_id == sample_fee_structure_data['deal_id']
        assert structure.fee_structure_name == sample_fee_structure_data['fee_structure_name']
        assert float(structure.hurdle_rate) == sample_fee_structure_data['hurdle_rate']
        assert float(structure.incentive_fee_rate) == sample_fee_structure_data['incentive_fee_rate']
        assert structure.closing_date == sample_fee_structure_data['closing_date']
        assert structure.is_active == True
        assert structure.threshold_reached == False
        assert structure.cum_discounted_sub_payments == Decimal('0')
    
    def test_load_fee_structure(self, incentive_fee_service, sample_fee_structure_data):
        """Test loading existing fee structure"""
        # Create structure
        original = incentive_fee_service.create_fee_structure(**sample_fee_structure_data)
        
        # Load structure
        loaded = incentive_fee_service.load_fee_structure(original.fee_structure_id)
        
        assert loaded is not None
        assert loaded.fee_structure_id == original.fee_structure_id
        assert loaded.deal_id == original.deal_id
        assert loaded.fee_structure_name == original.fee_structure_name
    
    def test_add_subordinated_payment(self, incentive_fee_service, sample_fee_structure_data):
        """Test adding subordinated payments"""
        structure = incentive_fee_service.create_fee_structure(**sample_fee_structure_data)
        
        payment = incentive_fee_service.add_subordinated_payment(
            structure.fee_structure_id,
            date(2024, 4, 15),
            1000000.0,
            is_historical=True
        )
        
        assert payment.payment_id is not None
        assert payment.fee_structure_id == structure.fee_structure_id
        assert payment.payment_date == date(2024, 4, 15)
        assert payment.payment_amount == Decimal('1000000.0')
        assert payment.is_historical == True
    
    def test_get_subordinated_payments(self, incentive_fee_service, sample_fee_structure_data):
        """Test retrieving subordinated payments"""
        structure = incentive_fee_service.create_fee_structure(**sample_fee_structure_data)
        
        # Add multiple payments
        payment_data = [
            (date(2024, 4, 15), 1000000.0),
            (date(2024, 7, 15), 1200000.0),
            (date(2024, 10, 15), 950000.0)
        ]
        
        for payment_date, amount in payment_data:
            incentive_fee_service.add_subordinated_payment(
                structure.fee_structure_id, payment_date, amount, True
            )
        
        # Get all payments
        payments = incentive_fee_service.get_subordinated_payments(structure.fee_structure_id)
        assert len(payments) == 3
        
        # Verify sorted by date
        assert payments[0].payment_date == date(2024, 4, 15)
        assert payments[1].payment_date == date(2024, 7, 15)
        assert payments[2].payment_date == date(2024, 10, 15)
        
        # Get payments up to specific date
        partial_payments = incentive_fee_service.get_subordinated_payments(
            structure.fee_structure_id, date(2024, 7, 31)
        )
        assert len(partial_payments) == 2


class TestIncentiveFeeVBAParity:
    """Test IncentiveFee class for VBA functional parity"""
    
    def test_vba_setup_method(self, sample_subordinated_payments):
        """Test VBA Setup() method equivalent"""
        incentive_fee = IncentiveFee()
        
        # VBA: Setup(iFeeThreshold, iIncentiveFee, iPaytoSubNotholder)
        incentive_fee.setup(
            i_fee_threshold=0.08,
            i_incentive_fee=0.20,
            i_payto_sub_notholder=sample_subordinated_payments
        )
        
        # Verify VBA variable mapping
        assert incentive_fee.cls_fee_hurdle_rate == 0.08      # clsFeeHurdleRate
        assert incentive_fee.cls_incent_fee == 0.20           # clsIncentFee
        assert incentive_fee.cls_sub_payments_dict == sample_subordinated_payments  # clsSubPaymentsDict
        assert incentive_fee._is_setup == True
    
    def test_vba_deal_setup_method(self, sample_subordinated_payments):
        """Test VBA DealSetup() method equivalent"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        
        # VBA: DealSetup(iNumofPayments, iCloseDate, ianalysisDate)
        incentive_fee.deal_setup(
            i_num_of_payments=20,
            i_close_date=date(2024, 1, 15),
            i_analysis_date=date(2025, 1, 10)
        )
        
        # Verify VBA array initialization
        assert len(incentive_fee.cls_threshold) == 21  # +1 for 1-based indexing
        assert len(incentive_fee.cls_irr) == 21
        assert len(incentive_fee.cls_fee_paid) == 21
        assert incentive_fee.cls_period == 1           # clsPeriod = 1
        assert incentive_fee.cls_closing_date == date(2024, 1, 15)  # clsClosingDate
        
        # Verify future payments removed (VBA logic)
        for payment_date in incentive_fee.cls_sub_payments_dict.keys():
            assert payment_date <= date(2025, 1, 10)
        
        # Verify cumulative discounted payments calculation (VBA exact logic)
        assert incentive_fee.cls_cum_dicounted_sub_payments != 0.0
        assert incentive_fee._is_deal_setup == True
    
    def test_vba_threshold_calculation_logic(self, sample_subordinated_payments):
        """Test VBA threshold calculation with exact logic"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        
        # Test when threshold not reached
        incentive_fee.cls_threshold_reach = False
        incentive_fee.calc(date(2025, 4, 15))
        
        # VBA logic: clsCurrentThreshold = clsCumDicountedSubPayments * (1 + clsFeeHurdleRate) ^ ((iNextPay - clsClosingDate) / 365)
        #            clsCurrentThreshold = -1 * clsCurrentThreshold
        days_diff = (date(2025, 4, 15) - date(2024, 1, 15)).days
        expected_threshold = incentive_fee.cls_cum_dicounted_sub_payments * (1 + 0.08) ** (days_diff / 365.0)
        expected_threshold = -1 * expected_threshold
        
        assert abs(incentive_fee.cls_current_threshold - expected_threshold) < 0.01
        assert incentive_fee.cls_threshold[1] == incentive_fee.cls_current_threshold
        
        # Test when threshold reached
        incentive_fee.cls_threshold_reach = True
        incentive_fee.calc(date(2025, 7, 15))
        assert incentive_fee.cls_current_threshold == 0.0
    
    def test_vba_incentive_fee_threshold_function(self, sample_subordinated_payments):
        """Test VBA IncentiveFeeThreshold() function equivalent"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        incentive_fee.calc(date(2025, 4, 15))
        
        # When threshold not reached
        incentive_fee.cls_threshold_reach = False
        incentive_fee.cls_curr_sub_payments = 500000.0
        
        threshold = incentive_fee.incentive_fee_threshold()
        expected = incentive_fee.cls_threshold[1] - 500000.0
        assert abs(threshold - expected) < 0.01
        
        # When threshold reached
        incentive_fee.cls_threshold_reach = True
        threshold = incentive_fee.incentive_fee_threshold()
        assert threshold == 0.0
    
    def test_vba_payment_to_sub_notholder_method(self, sample_subordinated_payments):
        """Test VBA PaymentToSubNotholder() method equivalent"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        incentive_fee.calc(date(2025, 4, 15))
        
        # VBA: PaymentToSubNotholder(iAmount)
        initial_payments = incentive_fee.cls_curr_sub_payments
        incentive_fee.payment_to_sub_notholder(750000.0)
        
        # VBA: clsCurrSubPayments = clsCurrSubPayments + iAmount
        assert incentive_fee.cls_curr_sub_payments == initial_payments + 750000.0
        
        # Test threshold reached logic
        # VBA: If clsCurrSubPayments >= clsCurrentThreshold Then clsThresholdReach = True
        if incentive_fee.cls_curr_sub_payments >= incentive_fee.cls_current_threshold:
            assert incentive_fee.cls_threshold_reach == True
    
    def test_vba_pay_incentive_fee_method(self, sample_subordinated_payments):
        """Test VBA PayIncentiveFee() method equivalent"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        incentive_fee.calc(date(2025, 4, 15))
        
        # Test when threshold not reached
        incentive_fee.cls_threshold_reach = False
        initial_incentive = incentive_fee.cls_curr_incetive_payments
        
        net_amount = incentive_fee.pay_incentive_fee(1000000.0)
        
        # Should return full amount with no fee deduction
        assert net_amount == 1000000.0
        assert incentive_fee.cls_curr_incetive_payments == initial_incentive
        
        # Test when threshold reached
        incentive_fee.cls_threshold_reach = True
        incentive_fee.cls_curr_incetive_payments = 0.0
        
        net_amount = incentive_fee.pay_incentive_fee(1000000.0)
        
        # VBA: clsCurrIncetivePayments = clsCurrIncetivePayments + iAmount * clsIncentFee
        # VBA: iAmount = iAmount * (1 - clsIncentFee)
        expected_fee = 1000000.0 * 0.20
        expected_net = 1000000.0 * (1 - 0.20)
        
        assert abs(incentive_fee.cls_curr_incetive_payments - expected_fee) < 0.01
        assert abs(net_amount - expected_net) < 0.01
    
    def test_vba_rollfoward_method_with_typo(self, sample_subordinated_payments):
        """Test VBA Rollfoward() method (preserving VBA typo)"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        incentive_fee.calc(date(2025, 4, 15))
        
        # Set up period data
        incentive_fee.cls_curr_sub_payments = 1000000.0
        incentive_fee.cls_curr_incetive_payments = 50000.0
        
        initial_cum_discounted = incentive_fee.cls_cum_dicounted_sub_payments
        initial_period = incentive_fee.cls_period
        
        # VBA: Rollfoward() (note the typo preservation)
        incentive_fee.rollfoward()
        
        # Verify VBA array updates
        # VBA: clsThreshold(clsPeriod) = clsCurrentThreshold
        # VBA: clsFeePaid(clsPeriod) = clsCurrIncetivePayments
        assert incentive_fee.cls_threshold[initial_period] == incentive_fee.cls_current_threshold
        assert incentive_fee.cls_fee_paid[initial_period] == 50000.0
        
        # Verify cumulative discounted payments update
        # VBA: clsCumDicountedSubPayments = clsCumDicountedSubPayments + (clsCurrSubPayments / ((1 + clsFeeHurdleRate) ^ ((clsCurrDate - clsClosingDate) / 365)))
        days_diff = (incentive_fee.cls_curr_date - incentive_fee.cls_closing_date).days
        discount_factor = (1 + 0.08) ** (days_diff / 365.0)
        expected_cum_discounted = initial_cum_discounted + (1000000.0 / discount_factor)
        
        assert abs(incentive_fee.cls_cum_dicounted_sub_payments - expected_cum_discounted) < 0.01
        
        # Verify period advancement and reset
        # VBA: clsPeriod = clsPeriod + 1
        # VBA: clsCurrSubPayments = 0
        # VBA: clsCurrIncetivePayments = 0
        assert incentive_fee.cls_period == initial_period + 1
        assert incentive_fee.cls_curr_sub_payments == 0.0
        assert incentive_fee.cls_curr_incetive_payments == 0.0
        
        # Verify payment was added to dictionary
        # VBA: clsSubPaymentsDict.Add clsCurrDate, clsCurrSubPayments
        assert incentive_fee.cls_curr_date in incentive_fee.cls_sub_payments_dict
        assert incentive_fee.cls_sub_payments_dict[incentive_fee.cls_curr_date] == 1000000.0
    
    def test_vba_fee_paid_function(self, sample_subordinated_payments):
        """Test VBA FeePaid() function equivalent"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        
        # Set up some fee payments
        incentive_fee.cls_fee_paid = [0.0, 25000.0, 30000.0, 40000.0] + [0.0] * 17
        
        total_fees = incentive_fee.fee_paid()
        
        # VBA: For i = LBound(clsFeePaid) To UBound(clsFeePaid)
        #          lTotal = lTotal + clsFeePaid(i)
        #      Next i
        expected_total = sum(incentive_fee.cls_fee_paid)
        assert abs(total_fees - expected_total) < 0.01
    
    def test_vba_output_function_format(self, sample_subordinated_payments):
        """Test VBA Output() function equivalent with exact formatting"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        
        # Set up some data for output
        incentive_fee.cls_period = 4  # Will output periods 1-3
        incentive_fee.cls_threshold = [0.0, -50000.0, 0.0, 0.0] + [0.0] * 17
        incentive_fee.cls_fee_paid = [0.0, 0.0, 25000.0, 30000.0] + [0.0] * 17
        incentive_fee.cls_irr = [0.0, 0.0, 0.075, 0.082] + [0.0] * 17
        
        output = incentive_fee.output()
        
        # VBA output format verification
        # Header: lOutput(0, 0) = "Threshold", lOutput(0, 1) = "Fee Paid", lOutput(0, 2) = "IRR"
        assert output[0] == ["Threshold", "Fee Paid", "IRR"]
        
        # Data rows: For i = 1 To clsPeriod - 1
        assert len(output) == 4  # Header + 3 data rows
        assert output[1] == [-50000.0, 0.0, "0.000%"]      # Period 1
        assert output[2] == [0.0, 25000.0, "7.500%"]       # Period 2
        assert output[3] == [0.0, 30000.0, "8.200%"]       # Period 3


class TestIncentiveFeeXIRRCalculation:
    """Test XIRR calculation for VBA Application.Xirr parity"""
    
    def test_xirr_calculation_simple_case(self):
        """Test XIRR calculation with simple case"""
        incentive_fee = IncentiveFee()
        
        # Simple cash flows: -1000 initial, +600 after 6 months, +600 after 12 months
        cash_flows = [-1000.0, 600.0, 600.0]
        dates = [
            date(2024, 1, 1),
            date(2024, 7, 1),
            date(2025, 1, 1)
        ]
        
        xirr = incentive_fee._calculate_xirr(cash_flows, dates)
        assert xirr is not None
        assert abs(xirr - 0.1269) < 0.01  # Should be approximately 12.69%
    
    def test_xirr_calculation_complex_case(self, sample_subordinated_payments):
        """Test XIRR with complex irregular cash flows"""
        incentive_fee = IncentiveFee()
        
        # Test with subordinated payments (starting with negative investment)
        cash_flows = [-2000000.0] + list(sample_subordinated_payments.values())
        dates = [date(2024, 1, 15)] + list(sample_subordinated_payments.keys())
        
        xirr = incentive_fee._calculate_xirr(cash_flows, dates)
        assert xirr is not None
        assert xirr > 0  # Should be positive return
    
    def test_xirr_calculation_edge_cases(self):
        """Test XIRR edge cases"""
        incentive_fee = IncentiveFee()
        
        # Test with insufficient data
        xirr = incentive_fee._calculate_xirr([100.0], [date(2024, 1, 1)])
        assert xirr is None
        
        # Test with all positive cash flows (should not converge to meaningful result)
        cash_flows = [100.0, 200.0, 300.0]
        dates = [date(2024, 1, 1), date(2024, 4, 1), date(2024, 7, 1)]
        xirr = incentive_fee._calculate_xirr(cash_flows, dates)
        # May return None or very negative value depending on convergence
        
        # Test with zero cash flows
        cash_flows = [-1000.0, 0.0, 1000.0]
        dates = [date(2024, 1, 1), date(2024, 4, 1), date(2024, 7, 1)]
        xirr = incentive_fee._calculate_xirr(cash_flows, dates)
        assert xirr is not None
        assert abs(xirr) < 0.01  # Should be approximately 0%


class TestIncentiveFeeDatabasePersistence:
    """Test database persistence functionality"""
    
    def test_save_to_database(self, incentive_db, sample_subordinated_payments):
        """Test saving incentive fee data to database"""
        incentive_fee = IncentiveFee(incentive_db)
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        # Process a few periods
        incentive_fee.calc(date(2025, 4, 15))
        incentive_fee.cls_curr_sub_payments = 1000000.0
        incentive_fee.cls_curr_incetive_payments = 50000.0
        incentive_fee.rollfoward()
        
        # Save to database
        fee_structure_id = incentive_fee.save_to_database(
            'TEST_DEAL_001', 
            'Test Incentive Fee'
        )
        
        assert fee_structure_id is not None
        assert incentive_fee.fee_structure_id == fee_structure_id
        
        # Verify database records exist
        structure = incentive_db.query(IncentiveFeeStructure).filter_by(
            fee_structure_id=fee_structure_id
        ).first()
        assert structure is not None
        assert structure.deal_id == 'TEST_DEAL_001'
        
        payments = incentive_db.query(SubordinatedPayment).filter_by(
            fee_structure_id=fee_structure_id
        ).all()
        assert len(payments) > 0  # Should have historical + current payments
    
    def test_load_from_database(self, incentive_db, sample_subordinated_payments):
        """Test loading incentive fee data from database"""
        # Create and save incentive fee
        original = IncentiveFee(incentive_db)
        original.setup(0.08, 0.20, sample_subordinated_payments)
        original.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        # Process some periods
        for i in range(1, 4):
            original.calc(date(2025, 1, 15) + relativedelta(months=i*3))
            original.cls_curr_sub_payments = 1000000.0 + i * 50000
            original.cls_curr_incetive_payments = i * 25000
            original.rollfoward()
        
        fee_structure_id = original.save_to_database('TEST_DEAL_002', 'Load Test Fee')
        
        # Load from database
        loaded = IncentiveFee.load_from_database(incentive_db, fee_structure_id)
        
        # Verify loaded data matches original
        assert loaded.fee_structure_id == fee_structure_id
        assert loaded.cls_fee_hurdle_rate == original.cls_fee_hurdle_rate
        assert loaded.cls_incent_fee == original.cls_incent_fee
        assert loaded.cls_closing_date == original.cls_closing_date
        assert loaded.cls_threshold_reach == original.cls_threshold_reach
        assert abs(loaded.cls_cum_dicounted_sub_payments - original.cls_cum_dicounted_sub_payments) < 0.01
        
        # Verify arrays match
        assert len(loaded.cls_threshold) == len(original.cls_threshold)
        assert len(loaded.cls_fee_paid) == len(original.cls_fee_paid)
        assert loaded.cls_period == original.cls_period
        
        # Verify setup flags
        assert loaded._is_setup == True
        assert loaded._is_deal_setup == True


class TestIncentiveFeeComplexScenarios:
    """Test complex scenarios and edge cases"""
    
    def test_negative_threshold_scenario(self):
        """Test scenario where subordinated payments start negative (common in CLOs)"""
        # Payments that start negative (losses) then become positive
        payments = {
            date(2024, 4, 15): -500000.0,   # Loss
            date(2024, 7, 15): -300000.0,   # Loss  
            date(2024, 10, 15): 200000.0,   # Recovery
            date(2025, 1, 15): 1500000.0    # Strong performance
        }
        
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, payments)
        incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        # Should start with negative cumulative discounted payments
        assert incentive_fee.cls_cum_dicounted_sub_payments < 0
        assert incentive_fee.cls_threshold_reach == False  # Threshold not reached initially
        
        # Process first period after positive payment
        incentive_fee.calc(date(2025, 4, 15))
        incentive_fee.payment_to_sub_notholder(1000000.0)
        
        # May now reach threshold
        threshold = incentive_fee.incentive_fee_threshold()
        assert threshold != 0.0  # Should have some threshold to overcome
    
    def test_multiple_period_processing(self, sample_subordinated_payments):
        """Test processing multiple periods with fee calculations"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(20, date(2024, 1, 15), date(2025, 1, 10))
        
        # Process 5 periods
        period_payments = [800000.0, 1200000.0, 900000.0, 1100000.0, 950000.0]
        
        for i, payment in enumerate(period_payments, 1):
            period_date = date(2025, 1, 15) + relativedelta(months=i*3)
            incentive_fee.calc(period_date)
            incentive_fee.payment_to_sub_notholder(payment)
            
            # Apply incentive fee if applicable
            if incentive_fee.cls_threshold_reach:
                net_payment = incentive_fee.pay_incentive_fee(payment * 0.1)  # 10% of payment for fee calc
                assert net_payment <= payment * 0.1  # Should be reduced by fee
            
            incentive_fee.rollfoward()
        
        # Verify progression
        assert incentive_fee.cls_period == 6  # Should be at period 6
        
        # Check total fees paid
        total_fees = incentive_fee.fee_paid()
        assert total_fees >= 0  # Should be non-negative
        
        # Generate output
        output = incentive_fee.output()
        assert len(output) == 6  # Header + 5 data rows
    
    def test_threshold_reached_behavior(self):
        """Test behavior when threshold is reached"""
        # Set up scenario where threshold is reached quickly
        payments = {
            date(2024, 4, 15): 2000000.0,   # Large positive payment
        }
        
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.06, 0.25, payments)  # Lower hurdle, higher fee
        incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        # Process period
        incentive_fee.calc(date(2025, 4, 15))
        incentive_fee.payment_to_sub_notholder(2500000.0)  # Large payment
        
        # Should reach threshold
        if incentive_fee.cls_threshold_reach:
            # Test fee application
            initial_fee = incentive_fee.cls_curr_incetive_payments
            net_payment = incentive_fee.pay_incentive_fee(1000000.0)
            
            # Fee should be 25% of payment
            expected_fee = 1000000.0 * 0.25
            expected_net = 1000000.0 * 0.75
            
            assert abs(incentive_fee.cls_curr_incetive_payments - initial_fee - expected_fee) < 0.01
            assert abs(net_payment - expected_net) < 0.01
        
        incentive_fee.rollfoward()
        
        # Subsequent periods should continue with threshold reached
        incentive_fee.calc(date(2025, 7, 15))
        assert incentive_fee.cls_current_threshold == 0.0  # Should be 0 when reached
    
    def test_irr_calculation_integration(self, sample_subordinated_payments):
        """Test IRR calculation integration with rollforward"""
        incentive_fee = IncentiveFee()
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        # Process period with rollforward
        incentive_fee.calc(date(2025, 4, 15))
        incentive_fee.cls_curr_sub_payments = 1200000.0
        incentive_fee.rollfoward()
        
        # Should have calculated IRR for period 1
        if incentive_fee.cls_period > 1:
            # IRR should be calculated and stored
            irr_value = incentive_fee.cls_irr[1] if len(incentive_fee.cls_irr) > 1 else 0.0
            assert isinstance(irr_value, (int, float))
            
            # Output should format IRR correctly
            output = incentive_fee.output()
            if len(output) > 1:
                irr_formatted = output[1][2]  # IRR column
                assert "%" in str(irr_formatted)  # Should be formatted as percentage
    
    def test_memory_and_state_management(self, sample_subordinated_payments):
        """Test that state is properly managed across operations"""
        incentive_fee = IncentiveFee()
        
        # Test setup requirement
        with pytest.raises(RuntimeError, match="Must call setup\\(\\) before deal_setup\\(\\)"):
            incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        
        incentive_fee.setup(0.08, 0.20, sample_subordinated_payments)
        
        # Test deal_setup requirement
        with pytest.raises(RuntimeError, match="Must call deal_setup\\(\\) before calc\\(\\)"):
            incentive_fee.calc(date(2025, 4, 15))
        
        incentive_fee.deal_setup(10, date(2024, 1, 15), date(2025, 1, 10))
        incentive_fee.calc(date(2025, 4, 15))
        
        # Test rollforward requirement
        with pytest.raises(RuntimeError, match="Must call calc\\(\\) before rollfoward\\(\\)"):
            incentive_fee.cls_curr_date = None
            incentive_fee.rollfoward()
        
        # Verify state flags
        assert incentive_fee._is_setup == True
        assert incentive_fee._is_deal_setup == True