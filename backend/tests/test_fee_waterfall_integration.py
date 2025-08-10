"""
Integration tests for Fee-Aware Waterfall Strategy
Tests complete end-to-end functionality including fees, triggers, and waterfall integration
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.clo_deal import CLODeal, CLOTranche
from app.models.fee import Fee, FeeType
from app.models.liability import DayCountConvention
from app.models.fee_aware_waterfall import FeeAwareWaterfallStrategy
from app.services.fee_service import FeeService
from app.services.trigger_service import TriggerService
from app.core.database import Base, engine


class TestFeeWaterfallIntegration:
    """Integration tests for complete fee and waterfall system"""
    
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
    def sample_deal_with_tranches_and_fees(self, session):
        """Create a complete CLO deal with tranches and fees"""
        deal = CLODeal(
            deal_id="INTEGRATED_DEAL",
            deal_name="Integrated CLO Deal",
            manager_name="Test Manager",
            target_par_amount=Decimal('500000000'),
            payment_frequency=4
        )
        session.add(deal)
        
        # Add tranches
        tranches = [
            ("Class A", Decimal('300000000'), 1),
            ("Class B", Decimal('100000000'), 2),
            ("Class C", Decimal('50000000'), 3),
            ("Class D", Decimal('30000000'), 4),
            ("Class E", Decimal('20000000'), 5),
        ]
        
        for tranche_name, balance, seniority in tranches:
            tranche = CLOTranche(
                tranche_id=f"{deal.deal_id}_{tranche_name}",
                deal_id=deal.deal_id,
                tranche_name=tranche_name,
                initial_balance=balance,
                current_balance=balance,
                seniority_level=seniority,
                payment_rank=seniority
            )
            session.add(tranche)
        
        # Add fee configurations
        fees = [
            Fee(
                deal_id=deal.deal_id,
                fee_name="Senior Management Fee",
                fee_type=FeeType.BEGINNING.value,
                fee_percentage=Decimal('0.005'),  # 0.5%
                fixed_amount=Decimal('0'),
                day_count_convention=DayCountConvention.ACT_360.value,
                interest_on_fee=False,
                interest_spread=Decimal('0'),
                initial_unpaid_fee=Decimal('0'),
                num_periods=48,
                beginning_fee_basis=Decimal('500000000')
            ),
            Fee(
                deal_id=deal.deal_id,
                fee_name="Subordinate Management Fee",
                fee_type=FeeType.AVERAGE.value,
                fee_percentage=Decimal('0.003'),  # 0.3%
                fixed_amount=Decimal('0'),
                day_count_convention=DayCountConvention.ACT_360.value,
                interest_on_fee=True,
                interest_spread=Decimal('0.015'),  # 1.5% spread
                initial_unpaid_fee=Decimal('25000'),
                num_periods=48,
                beginning_fee_basis=Decimal('500000000')
            ),
            Fee(
                deal_id=deal.deal_id,
                fee_name="Trustee Fee",
                fee_type=FeeType.FIXED.value,
                fee_percentage=Decimal('0'),
                fixed_amount=Decimal('60000'),  # $60K annually
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
        return deal
    
    def test_integrated_waterfall_setup(self, session, sample_deal_with_tranches_and_fees):
        """Test integrated waterfall strategy setup"""
        # Setup services
        trigger_service = TriggerService(session)
        fee_service = FeeService(session)
        
        trigger_service.setup_deal_triggers(sample_deal_with_tranches_and_fees.deal_id, 48)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        # Create integrated waterfall strategy
        # Note: This is a conceptual test - actual calculator would need to be implemented
        calculator = None  # Would need actual waterfall calculator implementation
        
        # For testing purposes, we'll verify the services are properly set up
        assert len(trigger_service.oc_calculators) == 5  # One per tranche
        assert len(trigger_service.ic_calculators) == 5  # One per tranche
        assert len(fee_service.fee_calculators) == 3    # Three fees
    
    def test_fee_calculation_with_triggers_passing(self, session, sample_deal_with_tranches_and_fees):
        """Test fee calculations when OC/IC triggers are passing"""
        # Setup services
        trigger_service = TriggerService(session)
        fee_service = FeeService(session)
        
        trigger_service.setup_deal_triggers(sample_deal_with_tranches_and_fees.deal_id, 48)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        # Calculate triggers (passing scenario)
        trigger_result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            collateral_balance=Decimal('600000000'),  # High collateral
            liability_balances={
                "Class A": Decimal('300000000'),
                "Class B": Decimal('100000000'),
                "Class C": Decimal('50000000')
            },
            interest_collections=Decimal('30000000'),  # High collections
            interest_due_by_tranche={
                "Class A": Decimal('15000000'),
                "Class B": Decimal('6000000'),
                "Class C": Decimal('4000000')
            }
        )
        
        # Should pass with good ratios
        assert trigger_result.all_oc_pass is True
        assert trigger_result.all_ic_pass is True
        
        # Calculate fees
        fee_result = fee_service.calculate_fees(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),  # 90 days
            fee_basis_amounts={
                "Senior Management Fee": Decimal('500000000'),
                "Subordinate Management Fee": Decimal('450000000'),  # Average basis
                "Trustee Fee": Decimal('0')
            },
            libor_rate=Decimal('0.03')
        )
        
        # Validate fee calculations
        assert fee_result.total_fees_accrued > 0
        assert len(fee_result.fee_results) == 3
        
        # Senior management fee: $500M * 0.5% * (90/360) = $625,000
        senior_result = fee_result.fee_results["Senior Management Fee"]
        expected_senior = Decimal('500000000') * Decimal('0.005') * Decimal('90') / Decimal('360')
        assert abs(Decimal(str(senior_result['fee_accrued'])) - expected_senior) < Decimal('100')
        
        # Subordinate management fee should include interest on unpaid balance
        sub_result = fee_result.fee_results["Subordinate Management Fee"]
        base_sub_fee = Decimal('450000000') * Decimal('0.003') * Decimal('90') / Decimal('360')
        interest_on_unpaid = Decimal('25000') * (Decimal('0.03') + Decimal('0.015')) * Decimal('90') / Decimal('360')
        expected_sub = base_sub_fee + interest_on_unpaid
        assert abs(Decimal(str(sub_result['fee_accrued'])) - expected_sub) < Decimal('100')
    
    def test_fee_calculation_with_triggers_failing(self, session, sample_deal_with_tranches_and_fees):
        """Test fee calculations when OC/IC triggers are failing"""
        # Setup services
        trigger_service = TriggerService(session)
        fee_service = FeeService(session)
        
        trigger_service.setup_deal_triggers(sample_deal_with_tranches_and_fees.deal_id, 48)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        # Calculate triggers (failing scenario)
        trigger_result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            collateral_balance=Decimal('350000000'),  # Low collateral
            liability_balances={
                "Class A": Decimal('300000000'),
                "Class B": Decimal('100000000'),
                "Class C": Decimal('50000000')
            },
            interest_collections=Decimal('15000000'),  # Low collections
            interest_due_by_tranche={
                "Class A": Decimal('18000000'),  # High interest due
                "Class B": Decimal('7000000'),
                "Class C": Decimal('5000000')
            }
        )
        
        # Should fail with poor ratios
        assert trigger_result.all_oc_pass is False or trigger_result.all_ic_pass is False
        
        # Calculate fees (same calculation regardless of trigger status)
        fee_result = fee_service.calculate_fees(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts={
                "Senior Management Fee": Decimal('350000000'),  # Lower basis
                "Subordinate Management Fee": Decimal('350000000'),
                "Trustee Fee": Decimal('0')
            },
            libor_rate=Decimal('0.025')
        )
        
        # Fees should still be calculated (triggers affect payment, not accrual)
        assert fee_result.total_fees_accrued > 0
        
        # In this scenario, subordinate management fees would typically be deferred
        # when IC triggers fail, but they still accrue
        sub_result = fee_result.fee_results["Subordinate Management Fee"]
        assert Decimal(str(sub_result['fee_accrued'])) > 0
    
    def test_fee_payment_application_logic(self, session, sample_deal_with_tranches_and_fees):
        """Test fee payment application and waterfall integration"""
        # Setup services
        fee_service = FeeService(session)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        # Calculate fees for period 1
        fee_result = fee_service.calculate_fees(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 4, 1),
            fee_basis_amounts={
                "Senior Management Fee": Decimal('500000000'),
                "Subordinate Management Fee": Decimal('450000000'),
                "Trustee Fee": Decimal('0')
            }
        )
        
        total_fees_due = fee_result.total_fees_accrued
        
        # Test partial payments
        partial_payments = {
            "Senior Management Fee": total_fees_due * Decimal('0.3'),  # 30%
            "Subordinate Management Fee": total_fees_due * Decimal('0.2'),  # 20%
            "Trustee Fee": total_fees_due * Decimal('0.1')  # 10%
        }
        
        unused_amounts = fee_service.apply_fee_payments(partial_payments)
        
        # Verify payments were applied
        senior_calc = fee_service.fee_calculators["Senior Management Fee"]
        assert senior_calc.fee_paid[1] > 0
        
        # Check unpaid balances
        fee_requirements = fee_service.get_fee_payment_requirements()
        assert fee_requirements['totals']['total_unpaid_balance'] > 0
        
        # Test full payment scenario
        remaining_payments = {}
        for fee_name, fee_req in fee_requirements['fees'].items():
            remaining_payments[fee_name] = Decimal(str(fee_req['unpaid_balance']))
        
        unused_amounts_2 = fee_service.apply_fee_payments(remaining_payments)
        
        # All fees should be paid now
        final_requirements = fee_service.get_fee_payment_requirements()
        assert abs(final_requirements['totals']['total_unpaid_balance']) < Decimal('1')
    
    def test_multi_period_fee_and_trigger_integration(self, session, sample_deal_with_tranches_and_fees):
        """Test multiple period integration of fees and triggers"""
        # Setup services
        trigger_service = TriggerService(session)
        fee_service = FeeService(session)
        
        trigger_service.setup_deal_triggers(sample_deal_with_tranches_and_fees.deal_id, 48)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        # Multi-period scenario
        periods_data = [
            {
                'period': 1,
                'begin_date': date(2023, 1, 1),
                'end_date': date(2023, 4, 1),
                'collateral_balance': Decimal('600000000'),
                'interest_collections': Decimal('30000000'),
                'scenario': 'good'
            },
            {
                'period': 2,
                'begin_date': date(2023, 4, 1),
                'end_date': date(2023, 7, 1),
                'collateral_balance': Decimal('400000000'),
                'interest_collections': Decimal('20000000'),
                'scenario': 'deteriorating'
            },
            {
                'period': 3,
                'begin_date': date(2023, 7, 1),
                'end_date': date(2023, 10, 1),
                'collateral_balance': Decimal('350000000'),
                'interest_collections': Decimal('15000000'),
                'scenario': 'poor'
            }
        ]
        
        total_fees_accrued = Decimal('0')
        total_fees_paid = Decimal('0')
        
        for period_data in periods_data:
            # Calculate triggers
            trigger_result = trigger_service.calculate_triggers(
                deal_id=sample_deal_with_tranches_and_fees.deal_id,
                period=period_data['period'],
                collateral_balance=period_data['collateral_balance'],
                liability_balances={
                    "Class A": Decimal('300000000'),
                    "Class B": Decimal('100000000'),
                    "Class C": Decimal('50000000')
                },
                interest_collections=period_data['interest_collections'],
                interest_due_by_tranche={
                    "Class A": Decimal('15000000'),
                    "Class B": Decimal('6000000'),
                    "Class C": Decimal('4000000')
                }
            )
            
            # Calculate fees
            fee_result = fee_service.calculate_fees(
                deal_id=sample_deal_with_tranches_and_fees.deal_id,
                period=period_data['period'],
                begin_date=period_data['begin_date'],
                end_date=period_data['end_date'],
                fee_basis_amounts={
                    "Senior Management Fee": period_data['collateral_balance'],
                    "Subordinate Management Fee": period_data['collateral_balance'],
                    "Trustee Fee": Decimal('0')
                }
            )
            
            total_fees_accrued += fee_result.total_fees_accrued
            
            # Apply payments based on scenario
            if period_data['scenario'] == 'good':
                # Pay all fees
                payment_factor = Decimal('1.0')
            elif period_data['scenario'] == 'deteriorating':
                # Pay senior fees only
                payment_factor = Decimal('0.6')
            else:  # poor
                # Minimal payments
                payment_factor = Decimal('0.3')
            
            fee_payments = {}
            for fee_name, fee_result in fee_result.fee_results.items():
                payment_amount = Decimal(str(fee_result['unpaid_balance'])) * payment_factor
                fee_payments[fee_name] = payment_amount
            
            fee_service.apply_fee_payments(fee_payments)
            total_fees_paid += sum(fee_payments.values())
            
            # Rollforward
            if period_data['period'] < len(periods_data):
                trigger_service.rollforward_all_triggers()
                fee_service.rollforward_all_fees()
        
        # Final validation
        assert total_fees_accrued > 0
        assert total_fees_paid > 0
        
        # Generate comprehensive reports
        fee_report = fee_service.get_comprehensive_fee_report(sample_deal_with_tranches_and_fees.deal_id)
        trigger_report = trigger_service.get_comprehensive_trigger_report(sample_deal_with_tranches_and_fees.deal_id)
        
        # Validate reports
        assert fee_report['summary']['periods_calculated'] == 3
        assert trigger_report['summary']['periods_calculated'] == 3
        
        # Check that fees accumulated unpaid balances in deteriorating scenario
        unpaid_balance = fee_report['summary']['total_unpaid_balance']
        assert unpaid_balance > 0  # Should have some unpaid fees
    
    def test_database_persistence_integration(self, session, sample_deal_with_tranches_and_fees):
        """Test that fee and trigger results are properly persisted"""
        # Setup services
        trigger_service = TriggerService(session)
        fee_service = FeeService(session)
        
        trigger_service.setup_deal_triggers(sample_deal_with_tranches_and_fees.deal_id, 48)
        fee_service.setup_deal_fees(sample_deal_with_tranches_and_fees.deal_id, 48)
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        
        # Calculate and save both triggers and fees
        trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            collateral_balance=Decimal('500000000'),
            liability_balances={"Class A": Decimal('300000000')},
            interest_collections=Decimal('25000000'),
            interest_due_by_tranche={"Class A": Decimal('15000000')}
        )
        
        fee_service.calculate_fees(
            deal_id=sample_deal_with_tranches_and_fees.deal_id,
            period=1,
            begin_date=begin_date,
            end_date=end_date,
            fee_basis_amounts={"Senior Management Fee": Decimal('500000000')}
        )
        
        # Save to database
        trigger_service.save_trigger_results_to_db(sample_deal_with_tranches_and_fees.deal_id, 1)
        fee_service.save_fee_results_to_db(sample_deal_with_tranches_and_fees.deal_id, 1, begin_date, end_date)
        
        # Verify records exist
        from app.models.oc_trigger import OCTrigger
        from app.models.ic_trigger import ICTrigger
        from app.models.fee import FeeCalculation
        
        oc_records = session.query(OCTrigger).filter_by(
            deal_id=sample_deal_with_tranches_and_fees.deal_id, period_number=1
        ).all()
        
        ic_records = session.query(ICTrigger).filter_by(
            deal_id=sample_deal_with_tranches_and_fees.deal_id, period_number=1
        ).all()
        
        fee_records = session.query(FeeCalculation).filter_by(period_number=1).all()
        
        assert len(oc_records) > 0
        assert len(ic_records) > 0
        assert len(fee_records) > 0
        
        # Verify data integrity
        fee_record = fee_records[0]
        assert fee_record.begin_date == begin_date
        assert fee_record.end_date == end_date
        assert fee_record.total_fee_accrued > 0