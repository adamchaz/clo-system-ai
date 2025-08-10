"""
Tests for Fee Service
Integration tests for fee service coordination and waterfall integration
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.fee import Fee, FeeType
from app.models.clo_deal import CLODeal
from app.models.liability import DayCountConvention
from app.services.fee_service import FeeService, FeeCalculationResult
from app.core.database import Base, engine


class TestFeeService:
    """Test suite for FeeService class"""
    
    @pytest.fixture
    def session(self):
        """Create test database session"""
        Base.metadata.create_all(bind=engine)
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def sample_deal(self, session):
        """Create a sample CLO deal"""
        deal = CLODeal(
            deal_id="TEST_FEE_DEAL",
            deal_name="Test Fee Deal",
            manager_name="Test Manager",
            target_par_amount=Decimal('500000000'),
            payment_frequency=4
        )
        session.add(deal)
        session.commit()
        return deal
    
    @pytest.fixture
    def sample_fees(self, session, sample_deal):
        """Create sample fee configurations"""
        fees = [
            Fee(
                deal_id=sample_deal.deal_id,
                fee_name="Senior Management Fee",
                fee_type=FeeType.BEGINNING.value,
                fee_percentage=Decimal('0.006'),  # 0.6%
                fixed_amount=Decimal('0'),
                day_count_convention=DayCountConvention.ACT_360.value,
                interest_on_fee=False,
                interest_spread=Decimal('0'),
                initial_unpaid_fee=Decimal('0'),
                num_periods=48,
                beginning_fee_basis=Decimal('500000000')
            ),
            Fee(
                deal_id=sample_deal.deal_id,
                fee_name="Subordinate Management Fee",
                fee_type=FeeType.AVERAGE.value,
                fee_percentage=Decimal('0.003'),  # 0.3%
                fixed_amount=Decimal('0'),
                day_count_convention=DayCountConvention.ACT_360.value,
                interest_on_fee=True,
                interest_spread=Decimal('0.01'),
                initial_unpaid_fee=Decimal('50000'),
                num_periods=48,
                beginning_fee_basis=Decimal('500000000')
            ),
            Fee(
                deal_id=sample_deal.deal_id,
                fee_name="Trustee Fee",
                fee_type=FeeType.FIXED.value,
                fee_percentage=Decimal('0'),
                fixed_amount=Decimal('75000'),  # $75K annually
                day_count_convention=DayCountConvention.ACT_365.value,
                interest_on_fee=False,
                interest_spread=Decimal('0'),
                initial_unpaid_fee=Decimal('0'),
                num_periods=48,
                beginning_fee_basis=Decimal('0')
            )
        ]
        
        for fee in fees:
            session.add(fee)
        session.commit()
        return fees
    
    def test_fee_service_initialization(self, session):
        """Test fee service initialization"""
        fee_service = FeeService(session)
        
        assert len(fee_service.fee_calculators) == 0
        assert fee_service.current_period == 1
    
    def test_setup_deal_fees(self, session, sample_deal, sample_fees):
        """Test setting up fee calculators for a deal"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        assert len(fee_service.fee_calculators) == 3
        assert "Senior Management Fee" in fee_service.fee_calculators
        assert "Subordinate Management Fee" in fee_service.fee_calculators
        assert "Trustee Fee" in fee_service.fee_calculators
        
        # Check calculator initialization
        senior_calc = fee_service.fee_calculators["Senior Management Fee"]
        assert senior_calc.fee_type == FeeType.BEGINNING
        assert senior_calc.fee_percentage == Decimal('0.006')
        assert senior_calc.num_periods == 48
    
    def test_setup_deal_fees_creates_defaults(self, session, sample_deal):
        """Test that default fees are created if none exist"""
        fee_service = FeeService(session)
        
        # No fees exist initially
        existing_fees = session.query(Fee).filter_by(deal_id=sample_deal.deal_id).all()
        assert len(existing_fees) == 0
        
        # Setup should create defaults
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Check that default fees were created
        created_fees = session.query(Fee).filter_by(deal_id=sample_deal.deal_id).all()
        assert len(created_fees) == 3  # Default fees created
        assert len(fee_service.fee_calculators) == 3
    
    def test_calculate_fees_single_period(self, session, sample_deal, sample_fees):
        """Test fee calculations for a single period"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate fees for period 1
        fee_basis_amounts = {
            "Senior Management Fee": Decimal('500000000'),  # $500M
            "Subordinate Management Fee": Decimal('480000000'),  # Average of 500M and 460M
            "Trustee Fee": Decimal('0')  # Fixed fee doesn't need basis
        }
        
        result = fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),  # 90 days
            fee_basis_amounts=fee_basis_amounts,
            libor_rate=Decimal('0.03')
        )
        
        assert isinstance(result, FeeCalculationResult)
        assert result.period == 1
        assert len(result.fee_results) == 3
        assert result.total_fees_accrued > 0
        
        # Check individual fee results
        senior_result = result.fee_results["Senior Management Fee"]
        assert senior_result['fee_accrued'] > 0
        assert senior_result['fee_type'] == FeeType.BEGINNING.value
        
        # Senior fee: $500M * 0.6% * (90/360) = $750,000
        expected_senior = Decimal('500000000') * Decimal('0.006') * Decimal('90') / Decimal('360')
        assert abs(Decimal(str(senior_result['fee_accrued'])) - expected_senior) < Decimal('1')
        
        # Subordinate fee should include interest on unpaid balance
        sub_result = result.fee_results["Subordinate Management Fee"]
        assert sub_result['fee_accrued'] > 0
        
        # Trustee fee: $75K * (90/365) = ~$18,493
        trustee_result = result.fee_results["Trustee Fee"]
        expected_trustee = Decimal('75000') * Decimal('90') / Decimal('365')
        assert abs(Decimal(str(trustee_result['fee_accrued'])) - expected_trustee) < Decimal('1')
    
    def test_apply_fee_payments(self, session, sample_deal, sample_fees):
        """Test applying fee payments"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate fees first
        fee_basis_amounts = {
            "Senior Management Fee": Decimal('500000000'),
            "Subordinate Management Fee": Decimal('480000000'),
            "Trustee Fee": Decimal('0')
        }
        
        result = fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts=fee_basis_amounts
        )
        
        # Apply payments (partial payments)
        fee_payments = {
            "Senior Management Fee": Decimal('500000'),  # Partial payment
            "Subordinate Management Fee": Decimal('1000000'),  # Overpayment
            "Trustee Fee": Decimal('10000')  # Partial payment
        }
        
        unused_amounts = fee_service.apply_fee_payments(fee_payments)
        
        # Check unused amounts
        assert "Senior Management Fee" not in unused_amounts  # Fully used
        assert "Subordinate Management Fee" in unused_amounts  # Should have excess
        assert unused_amounts["Subordinate Management Fee"] > 0
        
        # Verify payment applications
        senior_calc = fee_service.fee_calculators["Senior Management Fee"]
        assert senior_calc.fee_paid[1] == Decimal('500000')
    
    def test_get_fee_payment_requirements(self, session, sample_deal, sample_fees):
        """Test getting fee payment requirements"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate fees
        fee_basis_amounts = {
            "Senior Management Fee": Decimal('500000000'),
            "Subordinate Management Fee": Decimal('480000000'),
            "Trustee Fee": Decimal('0')
        }
        
        fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts=fee_basis_amounts
        )
        
        # Get all fee requirements
        requirements = fee_service.get_fee_payment_requirements()
        
        assert 'fees' in requirements
        assert 'totals' in requirements
        assert len(requirements['fees']) == 3
        
        # Check individual fee requirements
        senior_req = requirements['fees']['Senior Management Fee']
        assert 'unpaid_balance' in senior_req
        assert 'fee_accrued' in senior_req
        assert 'total_amount_due' in senior_req
        assert senior_req['unpaid_balance'] > 0
        
        # Check totals
        totals = requirements['totals']
        assert 'total_unpaid_balance' in totals
        assert 'total_fees_accrued' in totals
        assert totals['total_unpaid_balance'] > 0
        
        # Get single fee requirement
        single_req = fee_service.get_fee_payment_requirements("Senior Management Fee")
        assert 'unpaid_balance' in single_req
        assert 'current_period' in single_req
    
    def test_rollforward_all_fees(self, session, sample_deal, sample_fees):
        """Test rollforward functionality"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate and pay fees for period 1
        fee_basis_amounts = {
            "Senior Management Fee": Decimal('500000000'),
            "Subordinate Management Fee": Decimal('480000000'),
            "Trustee Fee": Decimal('0')
        }
        
        fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts=fee_basis_amounts
        )
        
        # Partial payments
        fee_payments = {
            "Senior Management Fee": Decimal('400000'),
            "Subordinate Management Fee": Decimal('200000'),
            "Trustee Fee": Decimal('15000')
        }
        fee_service.apply_fee_payments(fee_payments)
        
        # Rollforward
        fee_service.rollforward_all_fees()
        
        # Check that all calculators are at period 2
        assert fee_service.current_period == 2
        for calculator in fee_service.fee_calculators.values():
            assert calculator.current_period == 2
            assert calculator.beginning_balance[2] > 0  # Should have unpaid balance carried forward
    
    def test_multiple_periods_calculation(self, session, sample_deal, sample_fees):
        """Test multiple period calculations"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        periods_data = [
            {
                'period': 1,
                'begin_date': date(2023, 1, 1),
                'end_date': date(2023, 4, 1),
                'fee_basis_amounts': {
                    "Senior Management Fee": Decimal('500000000'),
                    "Subordinate Management Fee": Decimal('480000000'),
                    "Trustee Fee": Decimal('0')
                }
            },
            {
                'period': 2,
                'begin_date': date(2023, 4, 1),
                'end_date': date(2023, 7, 1),
                'fee_basis_amounts': {
                    "Senior Management Fee": Decimal('460000000'),
                    "Subordinate Management Fee": Decimal('450000000'),
                    "Trustee Fee": Decimal('0')
                }
            }
        ]
        
        total_accrued = Decimal('0')
        
        for period_data in periods_data:
            result = fee_service.calculate_fees(
                deal_id=sample_deal.deal_id,
                period=period_data['period'],
                begin_date=period_data['begin_date'],
                end_date=period_data['end_date'],
                fee_basis_amounts=period_data['fee_basis_amounts']
            )
            
            total_accrued += result.total_fees_accrued
            
            # Partial payments
            fee_service.apply_fee_payments({
                "Senior Management Fee": result.total_fees_accrued / 4,
                "Subordinate Management Fee": result.total_fees_accrued / 4,
                "Trustee Fee": result.total_fees_accrued / 4
            })
            
            if period_data['period'] < len(periods_data):
                fee_service.rollforward_all_fees()
        
        # Verify final state
        assert fee_service.current_period == 3
        assert total_accrued > 0
        
        # Check that all calculators have calculated 2 periods
        for calculator in fee_service.fee_calculators.values():
            assert calculator.last_calculated_period == 2
    
    def test_save_fee_results_to_db(self, session, sample_deal, sample_fees):
        """Test saving fee results to database"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate fees
        fee_basis_amounts = {
            "Senior Management Fee": Decimal('500000000'),
            "Subordinate Management Fee": Decimal('480000000'),
            "Trustee Fee": Decimal('0')
        }
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        
        fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=begin_date,
            end_date=end_date,
            fee_basis_amounts=fee_basis_amounts
        )
        
        # Save results
        fee_service.save_fee_results_to_db(sample_deal.deal_id, 1, begin_date, end_date)
        
        # Verify records were created
        from app.models.fee import FeeCalculation
        
        fee_calcs = session.query(FeeCalculation).filter_by(period_number=1).all()
        assert len(fee_calcs) == 3  # One for each fee
        
        # Check senior management fee calculation
        senior_calc = next((fc for fc in fee_calcs 
                           if fc.fee.fee_name == "Senior Management Fee"), None)
        assert senior_calc is not None
        assert senior_calc.begin_date == begin_date
        assert senior_calc.end_date == end_date
        assert senior_calc.total_fee_accrued > 0
    
    def test_comprehensive_fee_report(self, session, sample_deal, sample_fees):
        """Test comprehensive fee reporting"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate a few periods
        for period in range(1, 4):
            fee_basis_amounts = {
                "Senior Management Fee": Decimal('500000000') - Decimal('20000000') * period,
                "Subordinate Management Fee": Decimal('480000000') - Decimal('15000000') * period,
                "Trustee Fee": Decimal('0')
            }
            
            fee_service.calculate_fees(
                deal_id=sample_deal.deal_id,
                period=period,
                begin_date=date(2023, period, 1),
                end_date=date(2023, period + 3, 1),
                fee_basis_amounts=fee_basis_amounts
            )
            
            # Apply some payments
            fee_service.apply_fee_payments({
                "Senior Management Fee": Decimal('300000'),
                "Subordinate Management Fee": Decimal('150000'),
                "Trustee Fee": Decimal('10000')
            })
            
            if period < 3:
                fee_service.rollforward_all_fees()
        
        # Generate comprehensive report
        report = fee_service.get_comprehensive_fee_report(sample_deal.deal_id)
        
        # Validate report structure
        assert 'deal_id' in report
        assert 'fees' in report
        assert 'summary' in report
        
        # Check fee reports
        assert len(report['fees']) == 3
        
        senior_report = report['fees']['Senior Management Fee']
        assert 'fee_name' in senior_report
        assert 'fee_type' in senior_report
        assert 'periods' in senior_report
        assert 'total_fee_paid' in senior_report
        assert len(senior_report['periods']) == 3
        
        # Check summary
        summary = report['summary']
        assert summary['periods_calculated'] == 3
        assert summary['number_of_fees'] == 3
        assert summary['total_fees_paid'] > 0
        assert summary['total_unpaid_balance'] >= 0
    
    def test_fee_basis_requirements(self, session, sample_deal, sample_fees):
        """Test getting fee basis requirements"""
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        requirements = fee_service.get_fee_basis_requirements()
        
        assert len(requirements) == 3
        assert requirements["Senior Management Fee"] == "beginning_balance"
        assert requirements["Subordinate Management Fee"] == "average_balance"
        assert requirements["Trustee Fee"] == "fixed_amount"
    
    def test_invalid_deal_id(self, session):
        """Test error handling with invalid deal ID"""
        fee_service = FeeService(session)
        
        with pytest.raises(ValueError, match="Deal INVALID_DEAL not found"):
            fee_service.setup_deal_fees("INVALID_DEAL", 48)
    
    def test_fee_with_zero_percentage(self, session, sample_deal):
        """Test fee with zero percentage but positive fixed amount"""
        # Create fee with zero percentage
        zero_fee = Fee(
            deal_id=sample_deal.deal_id,
            fee_name="Zero Percentage Fee",
            fee_type=FeeType.BEGINNING.value,
            fee_percentage=Decimal('0'),
            fixed_amount=Decimal('100000'),  # $100K fixed
            day_count_convention=DayCountConvention.ACT_360.value,
            interest_on_fee=False,
            interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'),
            num_periods=48,
            beginning_fee_basis=Decimal('500000000')
        )
        session.add(zero_fee)
        session.commit()
        
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal.deal_id, 48)
        
        # Calculate fee
        result = fee_service.calculate_fees(
            deal_id=sample_deal.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts={"Zero Percentage Fee": Decimal('500000000')}
        )
        
        # Should only have fixed amount component
        expected_fee = Decimal('100000') * Decimal('90') / Decimal('360')
        fee_result = result.fee_results["Zero Percentage Fee"]
        assert abs(Decimal(str(fee_result['fee_accrued'])) - expected_fee) < Decimal('1')