"""
Test Dynamic Waterfall System
Validates handling of different tranche structures and configurations
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.dynamic_waterfall import (
    TrancheMapping, WaterfallStructure, DynamicWaterfallStrategy,
    WaterfallStructureBuilder, TrancheType, PaymentCategory
)
from app.models.waterfall_types import EnhancedWaterfallCalculator, WaterfallType
from app.models.waterfall import WaterfallConfiguration, WaterfallStep
from app.models.clo_deal import CLODeal, CLOTranche
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


class TestDynamicWaterfallStructures:
    """Test different tranche structure configurations"""
    
    def test_three_tranche_structure(self, session):
        """Test 3-tranche CLO structure (A, B, Equity)"""
        
        # Create deal with 3 tranches
        deal = CLODeal(
            deal_id="THREE-TRANCHE-TEST",
            deal_name="Three Tranche Test",
            effective_date=date(2023, 6, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        
        tranches = [
            CLOTranche(
                tranche_id="3T-A", deal_id=deal.deal_id, tranche_name="Class A Notes",
                initial_balance=Decimal('300000000'), current_balance=Decimal('300000000'),
                coupon_rate=Decimal('0.045'), seniority_level=1
            ),
            CLOTranche(
                tranche_id="3T-B", deal_id=deal.deal_id, tranche_name="Class B Notes", 
                initial_balance=Decimal('50000000'), current_balance=Decimal('50000000'),
                coupon_rate=Decimal('0.075'), seniority_level=2
            ),
            CLOTranche(
                tranche_id="3T-E", deal_id=deal.deal_id, tranche_name="Equity",
                initial_balance=Decimal('25000000'), current_balance=Decimal('25000000'),
                coupon_rate=Decimal('0.000'), seniority_level=3
            )
        ]
        
        for tranche in tranches:
            session.add(tranche)
        session.commit()
        
        # Create structure and mappings
        structures = WaterfallStructureBuilder.create_standard_structures(session)
        three_tranche_structure = next(s for s in structures if s.structure_name == "THREE_TRANCHE_CLO")
        session.add(three_tranche_structure)
        
        mappings = WaterfallStructureBuilder.create_tranche_mappings_for_deal(
            deal.deal_id, tranches, "THREE_TRANCHE_CLO", session
        )
        for mapping in mappings:
            session.add(mapping)
        session.commit()
        
        # Verify mappings
        assert len(mappings) == 3
        
        # Class A should be senior
        class_a_mapping = next(m for m in mappings if m.tranche_id == "3T-A")
        assert class_a_mapping.tranche_type == TrancheType.SENIOR_AAA.value
        assert class_a_mapping.payment_category == PaymentCategory.SENIOR_INTEREST.value
        assert class_a_mapping.interest_step == "CLASS_A_INTEREST"
        assert class_a_mapping.principal_step == "CLASS_A_PRINCIPAL"
        
        # Class B should be mezzanine
        class_b_mapping = next(m for m in mappings if m.tranche_id == "3T-B") 
        assert class_b_mapping.payment_category == PaymentCategory.SENIOR_INTEREST.value  # Still senior in 3-tranche
        assert class_b_mapping.category_rank == 2
        
        # Equity should be subordinated
        equity_mapping = next(m for m in mappings if m.tranche_id == "3T-E")
        assert equity_mapping.tranche_type == TrancheType.SUBORDINATED.value
        assert equity_mapping.payment_category == PaymentCategory.SUBORDINATED_INTEREST.value
    
    def test_five_tranche_structure(self, session):
        """Test standard 5-tranche CLO structure (A, B, C, D, E)"""
        
        # Create deal with 5 tranches
        deal = CLODeal(
            deal_id="FIVE-TRANCHE-TEST",
            deal_name="Five Tranche Test", 
            effective_date=date(2023, 6, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        
        tranches = [
            CLOTranche(tranche_id="5T-A", deal_id=deal.deal_id, tranche_name="Class A", seniority_level=1),
            CLOTranche(tranche_id="5T-B", deal_id=deal.deal_id, tranche_name="Class B", seniority_level=2),
            CLOTranche(tranche_id="5T-C", deal_id=deal.deal_id, tranche_name="Class C", seniority_level=3),
            CLOTranche(tranche_id="5T-D", deal_id=deal.deal_id, tranche_name="Class D", seniority_level=4),
            CLOTranche(tranche_id="5T-E", deal_id=deal.deal_id, tranche_name="Class E", seniority_level=5)
        ]
        
        for tranche in tranches:
            session.add(tranche)
        session.commit()
        
        # Create mappings
        mappings = WaterfallStructureBuilder.create_tranche_mappings_for_deal(
            deal.deal_id, tranches, "FIVE_TRANCHE_CLO", session
        )
        
        for mapping in mappings:
            session.add(mapping)
        session.commit()
        
        # Verify 5-tranche mapping
        assert len(mappings) == 5
        
        # Check senior tranches (A, B)
        senior_mappings = [m for m in mappings if m.payment_category == PaymentCategory.SENIOR_INTEREST.value]
        assert len(senior_mappings) == 2  # A and B
        
        # Check mezzanine tranches (C, D)
        mezz_mappings = [m for m in mappings if m.payment_category == PaymentCategory.MEZZ_INTEREST.value]
        assert len(mezz_mappings) == 2  # C and D
        
        # Check subordinated (E)
        sub_mappings = [m for m in mappings if m.payment_category == PaymentCategory.SUBORDINATED_INTEREST.value]
        assert len(sub_mappings) == 1  # E
        
        # Verify PIK eligibility
        class_d_mapping = next(m for m in mappings if m.tranche_id == "5T-D")
        assert class_d_mapping.is_pik_eligible == True
        
        class_e_mapping = next(m for m in mappings if m.tranche_id == "5T-E") 
        assert class_e_mapping.is_deferrable == True
    
    def test_seven_tranche_structure(self, session):
        """Test complex 7-tranche structure"""
        
        deal = CLODeal(
            deal_id="SEVEN-TRANCHE-TEST",
            deal_name="Seven Tranche Test",
            effective_date=date(2023, 6, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        
        # Create 7 tranches with various characteristics
        tranches = [
            CLOTranche(tranche_id="7T-A1", deal_id=deal.deal_id, tranche_name="Class A1", seniority_level=1),
            CLOTranche(tranche_id="7T-A2", deal_id=deal.deal_id, tranche_name="Class A2", seniority_level=2),
            CLOTranche(tranche_id="7T-B", deal_id=deal.deal_id, tranche_name="Class B", seniority_level=3),
            CLOTranche(tranche_id="7T-C", deal_id=deal.deal_id, tranche_name="Class C", seniority_level=4),
            CLOTranche(tranche_id="7T-D", deal_id=deal.deal_id, tranche_name="Class D", seniority_level=5),
            CLOTranche(tranche_id="7T-E", deal_id=deal.deal_id, tranche_name="Class E", seniority_level=6),
            CLOTranche(tranche_id="7T-F", deal_id=deal.deal_id, tranche_name="Class F", seniority_level=7)
        ]
        
        for tranche in tranches:
            session.add(tranche)
        session.commit()
        
        # Create mappings
        mappings = WaterfallStructureBuilder.create_tranche_mappings_for_deal(
            deal.deal_id, tranches, "SEVEN_TRANCHE_CLO", session
        )
        
        # Verify mapping distribution
        senior_count = sum(1 for m in mappings if m.payment_category == PaymentCategory.SENIOR_INTEREST.value)
        mezz_count = sum(1 for m in mappings if m.payment_category == PaymentCategory.MEZZ_INTEREST.value)
        sub_count = sum(1 for m in mappings if m.payment_category == PaymentCategory.SUBORDINATED_INTEREST.value)
        
        assert senior_count >= 2  # A1, A2 at minimum
        assert mezz_count >= 2    # B, C at minimum  
        assert sub_count >= 2     # E, F at minimum
        assert senior_count + mezz_count + sub_count == 7
    
    def test_custom_tranche_structure(self, session):
        """Test custom tranche structure with unusual configuration"""
        
        deal = CLODeal(
            deal_id="CUSTOM-TRANCHE-TEST",
            deal_name="Custom Structure Test",
            effective_date=date(2023, 6, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        
        # Custom structure: A, B1, B2, C, Preferred, Income Note
        tranches = [
            CLOTranche(tranche_id="CT-A", deal_id=deal.deal_id, tranche_name="Class A", seniority_level=1),
            CLOTranche(tranche_id="CT-B1", deal_id=deal.deal_id, tranche_name="Class B1", seniority_level=2),
            CLOTranche(tranche_id="CT-B2", deal_id=deal.deal_id, tranche_name="Class B2", seniority_level=3),
            CLOTranche(tranche_id="CT-C", deal_id=deal.deal_id, tranche_name="Class C", seniority_level=4),
            CLOTranche(tranche_id="CT-PREF", deal_id=deal.deal_id, tranche_name="Preferred Shares", seniority_level=5),
            CLOTranche(tranche_id="CT-INC", deal_id=deal.deal_id, tranche_name="Income Notes", seniority_level=6)
        ]
        
        for tranche in tranches:
            session.add(tranche)
        session.commit()
        
        # Manual mapping for custom structure
        custom_mappings = [
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="CT-A",
                tranche_type=TrancheType.SENIOR_AAA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=1, interest_step="CLASS_A_INTEREST", principal_step="CLASS_A_PRINCIPAL",
                effective_date=date(2023, 6, 15)
            ),
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="CT-B1", 
                tranche_type=TrancheType.SENIOR_AA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=2, interest_step="CLASS_B1_INTEREST", principal_step="CLASS_B1_PRINCIPAL",
                effective_date=date(2023, 6, 15)
            ),
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="CT-PREF",
                tranche_type=TrancheType.PREFERRED_SHARES.value,
                payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
                category_rank=1, interest_step="PREFERRED_DIVIDENDS", principal_step="PREFERRED_REDEMPTION",
                is_deferrable=True, effective_date=date(2023, 6, 15)
            ),
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="CT-INC",
                tranche_type=TrancheType.INCOME_NOTES.value,
                payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
                category_rank=2, interest_step="INCOME_DISTRIBUTION", 
                is_deferrable=True, is_pik_eligible=True, effective_date=date(2023, 6, 15)
            )
        ]
        
        for mapping in custom_mappings:
            session.add(mapping)
        session.commit()
        
        # Verify custom mappings
        preferred_mapping = next(m for m in custom_mappings if m.tranche_id == "CT-PREF")
        assert preferred_mapping.tranche_type == TrancheType.PREFERRED_SHARES.value
        assert preferred_mapping.is_deferrable == True
        
        income_mapping = next(m for m in custom_mappings if m.tranche_id == "CT-INC") 
        assert income_mapping.tranche_type == TrancheType.INCOME_NOTES.value
        assert income_mapping.is_pik_eligible == True


class TestDynamicWaterfallStrategy:
    """Test dynamic waterfall strategy execution"""
    
    def test_dynamic_payment_sequence_generation(self, session):
        """Test payment sequence generation based on tranche structure"""
        
        # Set up 5-tranche deal
        deal, tranches = self._create_five_tranche_deal(session)
        
        # Create structure
        structure = WaterfallStructure(
            structure_name="TEST_FIVE_TRANCHE",
            min_tranches=5, max_tranches=5, typical_tranches=5,
            payment_sequence=[
                PaymentCategory.EXPENSES.value,
                PaymentCategory.SENIOR_INTEREST.value, 
                PaymentCategory.MEZZ_INTEREST.value,
                PaymentCategory.RESERVES.value,
                PaymentCategory.SENIOR_PRINCIPAL.value,
                PaymentCategory.MEZZ_PRINCIPAL.value,
                PaymentCategory.SUBORDINATED_INTEREST.value,
                PaymentCategory.RESIDUAL.value
            ],
            category_rules={}
        )
        session.add(structure)
        
        # Create mappings
        mappings = [
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="5T-A",
                tranche_type=TrancheType.SENIOR_AAA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=1, interest_step="CLASS_A_INTEREST", principal_step="CLASS_A_PRINCIPAL",
                effective_date=date(2023, 6, 15)
            ),
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="5T-B",
                tranche_type=TrancheType.SENIOR_AA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=2, interest_step="CLASS_B_INTEREST", principal_step="CLASS_B_PRINCIPAL",
                effective_date=date(2023, 6, 15)
            ),
            TrancheMapping(
                deal_id=deal.deal_id, tranche_id="5T-E",
                tranche_type=TrancheType.SUBORDINATED.value,
                payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
                category_rank=1, interest_step="CLASS_E_INTEREST", principal_step="CLASS_E_PRINCIPAL",
                is_deferrable=True, effective_date=date(2023, 6, 15)
            )
        ]
        
        for mapping in mappings:
            session.add(mapping)
        session.commit()
        
        # Create calculator with base config
        config = WaterfallConfiguration(
            deal_id=deal.deal_id,
            config_name="Dynamic Test Config",
            effective_date=date(2023, 6, 15),
            payment_rules='[]'
        )
        session.add(config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        # Create dynamic strategy
        dynamic_strategy = DynamicWaterfallStrategy(calculator, "TEST_FIVE_TRANCHE")
        
        # Test sequence generation
        sequence = dynamic_strategy.get_payment_sequence()
        
        # Should include standard expenses
        assert WaterfallStep.TRUSTEE_FEES in sequence
        assert WaterfallStep.ADMIN_FEES in sequence
        
        # Should include tranche-specific steps
        step_names = [step.value for step in sequence]
        assert "CLASS_A_INTEREST" in step_names
        assert "CLASS_B_INTEREST" in step_names  
        assert "CLASS_E_INTEREST" in step_names
    
    def test_dynamic_trigger_checking(self, session):
        """Test trigger checking based on tranche characteristics"""
        
        deal, tranches = self._create_five_tranche_deal(session)
        
        # Create mapping with deferrable tranche
        mapping = TrancheMapping(
            deal_id=deal.deal_id, tranche_id=tranches[0].tranche_id,
            tranche_type=TrancheType.SUBORDINATED.value,
            payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
            is_deferrable=True, effective_date=date(2023, 6, 15)
        )
        session.add(mapping)
        session.commit()
        
        # Create dynamic strategy
        config = WaterfallConfiguration(
            deal_id=deal.deal_id, config_name="Test", effective_date=date(2023, 6, 15), payment_rules='[]'
        )
        session.add(config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=deal.deal_id, payment_date=date(2023, 9, 15),
            session=session, waterfall_type=WaterfallType.TRADITIONAL
        )
        
        dynamic_strategy = DynamicWaterfallStrategy(calculator)
        
        # Test trigger checking for deferrable tranche
        result = dynamic_strategy.check_payment_triggers(
            WaterfallStep.CLASS_A_INTEREST, tranches[0]
        )
        
        # Should return boolean result
        assert isinstance(result, bool)
    
    def test_pik_interest_handling(self, session):
        """Test PIK interest calculation"""
        
        deal, tranches = self._create_five_tranche_deal(session)
        
        # Create PIK-eligible mapping
        mapping = TrancheMapping(
            deal_id=deal.deal_id, tranche_id=tranches[0].tranche_id,
            tranche_type=TrancheType.SUBORDINATED.value,
            payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
            is_pik_eligible=True, effective_date=date(2023, 6, 15)
        )
        session.add(mapping)
        session.commit()
        
        config = WaterfallConfiguration(
            deal_id=deal.deal_id, config_name="PIK Test", effective_date=date(2023, 6, 15), payment_rules='[]'
        )
        session.add(config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=deal.deal_id, payment_date=date(2023, 9, 15),
            session=session, waterfall_type=WaterfallType.TRADITIONAL
        )
        
        # Set low available cash to trigger PIK
        calculator.available_cash = Decimal('1000')
        
        dynamic_strategy = DynamicWaterfallStrategy(calculator)
        
        # Test PIK calculation
        original_balance = tranches[0].current_balance
        
        payment = dynamic_strategy.calculate_payment_amount(
            WaterfallStep.CLASS_A_INTEREST, tranches[0]
        )
        
        # Should return Decimal
        assert isinstance(payment, Decimal)
    
    def _create_five_tranche_deal(self, session):
        """Helper to create 5-tranche deal"""
        deal = CLODeal(
            deal_id="DYNAMIC-TEST-DEAL",
            deal_name="Dynamic Test Deal",
            effective_date=date(2023, 6, 15),
            first_payment_date=date(2023, 9, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        
        tranches = [
            CLOTranche(
                tranche_id="5T-A", deal_id=deal.deal_id, tranche_name="Class A",
                current_balance=Decimal('100000000'), coupon_rate=Decimal('0.050'), seniority_level=1
            ),
            CLOTranche(
                tranche_id="5T-B", deal_id=deal.deal_id, tranche_name="Class B", 
                current_balance=Decimal('50000000'), coupon_rate=Decimal('0.070'), seniority_level=2
            ),
            CLOTranche(
                tranche_id="5T-E", deal_id=deal.deal_id, tranche_name="Class E",
                current_balance=Decimal('25000000'), coupon_rate=Decimal('0.120'), seniority_level=5
            )
        ]
        
        for tranche in tranches:
            session.add(tranche)
        session.commit()
        
        return deal, tranches


class TestWaterfallStructureBuilder:
    """Test waterfall structure builder utilities"""
    
    def test_standard_structure_creation(self, session):
        """Test creation of standard waterfall structures"""
        
        structures = WaterfallStructureBuilder.create_standard_structures(session)
        
        # Should create multiple structures
        assert len(structures) >= 3
        
        # Check specific structures exist
        structure_names = [s.structure_name for s in structures]
        assert "THREE_TRANCHE_CLO" in structure_names
        assert "FIVE_TRANCHE_CLO" in structure_names
        assert "SEVEN_TRANCHE_CLO" in structure_names
        
        # Verify structure properties
        five_tranche = next(s for s in structures if s.structure_name == "FIVE_TRANCHE_CLO")
        assert five_tranche.typical_tranches == 5
        assert five_tranche.jurisdiction == "US"
        
        sequence = five_tranche.get_payment_sequence()
        assert PaymentCategory.EXPENSES.value in sequence
        assert PaymentCategory.SENIOR_INTEREST.value in sequence
        assert PaymentCategory.RESIDUAL.value in sequence
    
    def test_tranche_mapping_creation(self, session):
        """Test automatic tranche mapping creation"""
        
        # Create test tranches
        tranches = [
            CLOTranche(tranche_id="AUTO-A", tranche_name="Class A", seniority_level=1),
            CLOTranche(tranche_id="AUTO-B", tranche_name="Class B", seniority_level=2),
            CLOTranche(tranche_id="AUTO-C", tranche_name="Class C", seniority_level=3)
        ]
        
        mappings = WaterfallStructureBuilder.create_tranche_mappings_for_deal(
            "AUTO-TEST-DEAL", tranches, "THREE_TRANCHE_CLO", session
        )
        
        # Should create mapping for each tranche
        assert len(mappings) == 3
        
        # Verify mapping properties
        class_a_mapping = mappings[0]
        assert class_a_mapping.tranche_id == "AUTO-A"
        assert class_a_mapping.category_rank == 1
        assert class_a_mapping.interest_step == "CLASS_A_INTEREST"
        assert class_a_mapping.principal_step == "CLASS_A_PRINCIPAL"
        
        # Verify subordinated characteristics
        class_c_mapping = mappings[2]
        assert class_c_mapping.is_deferrable == True
        assert class_c_mapping.tranche_type == TrancheType.SUBORDINATED.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])