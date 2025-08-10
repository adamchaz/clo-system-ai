"""
Dynamic Waterfall System - Handles Variable Tranche Structures
Supports CLO deals with different numbers and types of tranches
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal
from datetime import date
from enum import Enum
from abc import ABC, abstractmethod
import json

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .waterfall_types import BaseWaterfallStrategy, WaterfallStep, PaymentPhase
from .clo_deal import CLOTranche


class TrancheType(str, Enum):
    """Standard tranche classifications"""
    SENIOR_AAA = "SENIOR_AAA"           # Class A/AAA notes
    SENIOR_AA = "SENIOR_AA"             # Class B/AA notes  
    SENIOR_A = "SENIOR_A"               # Class C/A notes
    MEZZANINE_BBB = "MEZZANINE_BBB"     # Class D/BBB notes
    MEZZANINE_BB = "MEZZANINE_BB"       # Class E/BB notes
    MEZZANINE_B = "MEZZANINE_B"         # Class F/B notes
    SUBORDINATED = "SUBORDINATED"        # Junior/Equity tranches
    FIRST_LOSS = "FIRST_LOSS"           # Residual equity
    PREFERRED_SHARES = "PREFERRED_SHARES" # Preferred equity
    INCOME_NOTES = "INCOME_NOTES"       # Income/deferrable notes


class PaymentCategory(str, Enum):
    """Payment categories for flexible waterfall construction"""
    EXPENSES = "EXPENSES"               # Fees and expenses
    SENIOR_INTEREST = "SENIOR_INTEREST" # Senior note interest
    MEZZ_INTEREST = "MEZZ_INTEREST"     # Mezzanine note interest
    SUBORDINATED_INTEREST = "SUBORDINATED_INTEREST"
    RESERVES = "RESERVES"               # Reserve account funding
    SENIOR_PRINCIPAL = "SENIOR_PRINCIPAL"
    MEZZ_PRINCIPAL = "MEZZ_PRINCIPAL"
    SUBORDINATED_PRINCIPAL = "SUBORDINATED_PRINCIPAL"
    MANAGEMENT_FEES = "MANAGEMENT_FEES"
    RESIDUAL = "RESIDUAL"


class TrancheMapping(Base):
    """
    Maps deal tranches to standard waterfall categories
    Allows dynamic waterfall construction based on actual tranche structure
    """
    __tablename__ = 'tranche_mappings'
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    tranche_id = Column(String(50), ForeignKey('clo_tranches.tranche_id'), nullable=False)
    
    # Tranche classification
    tranche_type = Column(String(30), nullable=False)  # TrancheType enum
    payment_category = Column(String(30), nullable=False)  # PaymentCategory enum
    
    # Payment priority within category
    category_rank = Column(Integer, nullable=False, default=1)  # 1 = highest priority
    
    # Payment step mapping
    interest_step = Column(String(50))   # Mapped waterfall step for interest
    principal_step = Column(String(50))  # Mapped waterfall step for principal
    
    # Special characteristics
    is_deferrable = Column(Boolean, default=False)
    is_pik_eligible = Column(Boolean, default=False)
    supports_turbo = Column(Boolean, default=True)
    
    # Effective dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date)  # NULL for permanent
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    tranche = relationship("CLOTranche")
    
    def __repr__(self):
        return f"<TrancheMapping({self.deal_id}: {self.tranche_id} → {self.tranche_type})>"


class WaterfallStructure(Base):
    """
    Defines waterfall structure template for different tranche configurations
    Supports 3-tranche, 5-tranche, 7-tranche, and custom structures
    """
    __tablename__ = 'waterfall_structures'
    
    structure_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_name = Column(String(100), nullable=False, unique=True)
    
    # Structure metadata
    min_tranches = Column(Integer, nullable=False)
    max_tranches = Column(Integer, nullable=False)
    typical_tranches = Column(Integer, nullable=False)
    
    # Structure definition (JSON)
    payment_sequence = Column(JSON, nullable=False)  # Ordered list of payment categories
    category_rules = Column(JSON, nullable=False)    # Rules for each category
    
    # Market and regulatory info
    jurisdiction = Column(String(20))
    typical_use_case = Column(Text)
    regulatory_notes = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))
    
    def get_payment_sequence(self) -> List[str]:
        """Get ordered payment sequence"""
        return self.payment_sequence if isinstance(self.payment_sequence, list) else []
    
    def get_category_rules(self) -> Dict[str, Any]:
        """Get category-specific rules"""
        return self.category_rules if isinstance(self.category_rules, dict) else {}


class DynamicWaterfallStrategy(BaseWaterfallStrategy):
    """
    Dynamic waterfall strategy that adapts to actual tranche structure
    Builds payment sequence based on tranche mappings and structure definition
    """
    
    def __init__(self, calculator, structure_name: str = "STANDARD_US_CLO"):
        super().__init__(calculator)
        self.structure = self._load_structure(structure_name)
        self.tranche_mappings = self._load_tranche_mappings()
        self.payment_sequence_cache = None
    
    def get_payment_sequence(self) -> List[WaterfallStep]:
        """Build dynamic payment sequence based on actual tranches"""
        if self.payment_sequence_cache:
            return self.payment_sequence_cache
        
        sequence = []
        
        if not self.structure:
            # Fallback to traditional sequence
            return self._get_fallback_sequence()
        
        # Build sequence from structure definition
        for category in self.structure.get_payment_sequence():
            category_steps = self._get_steps_for_category(category)
            sequence.extend(category_steps)
        
        self.payment_sequence_cache = sequence
        return sequence
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Dynamic trigger checking based on tranche characteristics"""
        
        if not tranche:
            # Non-tranche payments (fees, reserves) usually always pay
            return True
        
        # Get tranche mapping
        mapping = self._get_tranche_mapping(tranche.tranche_id)
        if not mapping:
            return super().check_payment_triggers(step, tranche)
        
        # Check category-specific triggers
        category = mapping.payment_category
        
        if category == PaymentCategory.SENIOR_INTEREST.value:
            # Senior interest usually always pays unless in default
            return not self._is_deal_in_default()
        
        elif category in [PaymentCategory.MEZZ_INTEREST.value, PaymentCategory.SUBORDINATED_INTEREST.value]:
            # Subordinated interest may be deferrable
            if mapping.is_deferrable:
                return self._check_deferral_triggers()
            return True
        
        elif category in [PaymentCategory.SENIOR_PRINCIPAL.value, PaymentCategory.MEZZ_PRINCIPAL.value]:
            # Principal payments require coverage tests
            return (self.calculator._check_overcollateralization_tests() and
                   self.calculator._check_interest_coverage_tests())
        
        elif category == PaymentCategory.SUBORDINATED_PRINCIPAL.value:
            # Subordinated principal may have additional restrictions
            return self._check_subordinated_principal_triggers()
        
        return True
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Dynamic payment calculation based on tranche type and rules"""
        
        if not tranche:
            # Non-tranche payments
            return self._calculate_non_tranche_payment(step)
        
        mapping = self._get_tranche_mapping(tranche.tranche_id)
        if not mapping:
            return super().calculate_payment_amount(step, tranche)
        
        # Get category rules
        category_rules = self.structure.get_category_rules().get(mapping.payment_category, {})
        
        if 'INTEREST' in step.value:
            return self._calculate_tranche_interest(tranche, mapping, category_rules)
        elif 'PRINCIPAL' in step.value:
            return self._calculate_tranche_principal(tranche, mapping, category_rules)
        
        return Decimal('0')
    
    def get_payment_phase(self) -> PaymentPhase:
        """Enhanced phase detection with tranche structure awareness"""
        base_phase = super().get_payment_phase()
        
        # Adjust phase based on tranche structure
        if self._has_income_notes() and base_phase == PaymentPhase.AMORTIZATION:
            # Income notes may extend amortization phase
            return PaymentPhase.AMORTIZATION
        
        return base_phase
    
    def _load_structure(self, structure_name: str) -> Optional[WaterfallStructure]:
        """Load waterfall structure definition"""
        return self.calculator.session.query(WaterfallStructure).filter_by(
            structure_name=structure_name,
            is_active=True
        ).first()
    
    def _load_tranche_mappings(self) -> Dict[str, TrancheMapping]:
        """Load tranche mappings for the deal"""
        mappings = self.calculator.session.query(TrancheMapping).filter(
            TrancheMapping.deal_id == self.deal_id,
            TrancheMapping.effective_date <= self.payment_date
        ).filter(
            (TrancheMapping.expiration_date.is_(None)) |
            (TrancheMapping.expiration_date >= self.payment_date)
        ).all()
        
        return {mapping.tranche_id: mapping for mapping in mappings}
    
    def _get_steps_for_category(self, category: str) -> List[WaterfallStep]:
        """Get waterfall steps for payment category"""
        steps = []
        
        # Get tranches for this category
        category_mappings = [m for m in self.tranche_mappings.values() 
                           if m.payment_category == category]
        
        # Sort by priority rank
        category_mappings.sort(key=lambda m: m.category_rank)
        
        if category == PaymentCategory.EXPENSES.value:
            steps = [WaterfallStep.TRUSTEE_FEES, WaterfallStep.ADMIN_FEES, WaterfallStep.SENIOR_MGMT_FEES]
        
        elif category == PaymentCategory.SENIOR_INTEREST.value:
            for mapping in category_mappings:
                if mapping.interest_step:
                    steps.append(WaterfallStep(mapping.interest_step))
        
        elif category == PaymentCategory.MEZZ_INTEREST.value:
            for mapping in category_mappings:
                if mapping.interest_step:
                    steps.append(WaterfallStep(mapping.interest_step))
        
        elif category == PaymentCategory.SUBORDINATED_INTEREST.value:
            for mapping in category_mappings:
                if mapping.interest_step:
                    steps.append(WaterfallStep(mapping.interest_step))
        
        elif category == PaymentCategory.RESERVES.value:
            steps = [WaterfallStep.INTEREST_RESERVE]
        
        elif category == PaymentCategory.SENIOR_PRINCIPAL.value:
            for mapping in category_mappings:
                if mapping.principal_step:
                    steps.append(WaterfallStep(mapping.principal_step))
        
        elif category == PaymentCategory.MEZZ_PRINCIPAL.value:
            for mapping in category_mappings:
                if mapping.principal_step:
                    steps.append(WaterfallStep(mapping.principal_step))
        
        elif category == PaymentCategory.SUBORDINATED_PRINCIPAL.value:
            for mapping in category_mappings:
                if mapping.principal_step:
                    steps.append(WaterfallStep(mapping.principal_step))
        
        elif category == PaymentCategory.MANAGEMENT_FEES.value:
            steps = [WaterfallStep.JUNIOR_MGMT_FEES, WaterfallStep.INCENTIVE_MGMT_FEES]
        
        elif category == PaymentCategory.RESIDUAL.value:
            steps = [WaterfallStep.RESIDUAL_EQUITY]
        
        return steps
    
    def _get_tranche_mapping(self, tranche_id: str) -> Optional[TrancheMapping]:
        """Get mapping for specific tranche"""
        return self.tranche_mappings.get(tranche_id)
    
    def _calculate_tranche_interest(self, tranche: CLOTranche, mapping: TrancheMapping, 
                                  rules: Dict[str, Any]) -> Decimal:
        """Calculate interest payment for tranche with category rules"""
        base_interest = self.calculator._calculate_interest_due(tranche)
        
        # Apply PIK logic if eligible
        if mapping.is_pik_eligible and self._should_pik_interest(tranche, mapping):
            # Add to principal balance instead of paying cash
            tranche.current_balance = (tranche.current_balance or Decimal('0')) + base_interest
            return Decimal('0')
        
        # Apply payment caps/floors from rules
        if 'interest_cap' in rules:
            base_interest = min(base_interest, Decimal(str(rules['interest_cap'])))
        
        if 'interest_floor' in rules:
            base_interest = max(base_interest, Decimal(str(rules['interest_floor'])))
        
        return base_interest
    
    def _calculate_tranche_principal(self, tranche: CLOTranche, mapping: TrancheMapping,
                                   rules: Dict[str, Any]) -> Decimal:
        """Calculate principal payment for tranche with category rules"""
        
        # Check if turbo payments apply
        if mapping.supports_turbo and self._is_turbo_mode():
            return min(self.calculator.available_cash, 
                      Decimal(str(tranche.current_balance or 0)))
        
        # Standard principal calculation
        base_principal = self.calculator._calculate_principal_payment(tranche)
        
        # Apply payment rules
        if 'principal_cap' in rules:
            base_principal = min(base_principal, Decimal(str(rules['principal_cap'])))
        
        return base_principal
    
    def _calculate_non_tranche_payment(self, step: WaterfallStep) -> Decimal:
        """Calculate non-tranche payments (fees, reserves)"""
        if step == WaterfallStep.TRUSTEE_FEES:
            return self.calculator._calculate_trustee_fee()
        elif step == WaterfallStep.ADMIN_FEES:
            return self.calculator._calculate_admin_fee()
        elif step == WaterfallStep.SENIOR_MGMT_FEES:
            return self.calculator._calculate_senior_mgmt_fee()
        elif step == WaterfallStep.JUNIOR_MGMT_FEES:
            return self.calculator._calculate_junior_mgmt_fee()
        elif step == WaterfallStep.INTEREST_RESERVE:
            return self._calculate_reserve_funding()
        
        return Decimal('0')
    
    def _get_fallback_sequence(self) -> List[WaterfallStep]:
        """Fallback sequence when structure not defined"""
        from .waterfall_types import TraditionalWaterfall
        traditional = TraditionalWaterfall(self.calculator)
        return traditional.get_payment_sequence()
    
    def _is_deal_in_default(self) -> bool:
        """Check if deal is in default"""
        # Implementation would check default triggers
        return False
    
    def _check_deferral_triggers(self) -> bool:
        """Check if interest deferral triggers are met"""
        # Implementation would check specific deferral conditions
        return True
    
    def _check_subordinated_principal_triggers(self) -> bool:
        """Check triggers for subordinated principal payments"""
        # Implementation would check subordinated payment conditions
        return True
    
    def _should_pik_interest(self, tranche: CLOTranche, mapping: TrancheMapping) -> bool:
        """Determine if interest should be PIK'd"""
        if not mapping.is_pik_eligible:
            return False
        
        # PIK based on cash availability
        interest_due = self.calculator._calculate_interest_due(tranche)
        return self.calculator.available_cash < interest_due
    
    def _is_turbo_mode(self) -> bool:
        """Check if waterfall is in turbo mode"""
        # Implementation would check turbo conditions
        return False
    
    def _has_income_notes(self) -> bool:
        """Check if deal has income notes"""
        return any(m.tranche_type == TrancheType.INCOME_NOTES.value 
                  for m in self.tranche_mappings.values())
    
    def _calculate_reserve_funding(self) -> Decimal:
        """Calculate reserve funding requirement"""
        if not self.calculator.config:
            return Decimal('0')
        
        current_reserve = self.calculator._get_current_reserve_balance()
        target_reserve = self.calculator.config.interest_reserve_target or Decimal('0')
        
        return max(target_reserve - current_reserve, Decimal('0'))


class WaterfallStructureBuilder:
    """
    Builder class for creating waterfall structures for different tranche configurations
    """
    
    @classmethod
    def create_standard_structures(cls, session) -> List[WaterfallStructure]:
        """Create standard waterfall structures"""
        structures = []
        
        # 3-Tranche Structure (A, B, Equity)
        three_tranche = WaterfallStructure(
            structure_name="THREE_TRANCHE_CLO",
            min_tranches=3,
            max_tranches=3,
            typical_tranches=3,
            payment_sequence=[
                PaymentCategory.EXPENSES.value,
                PaymentCategory.SENIOR_INTEREST.value,
                PaymentCategory.MEZZ_INTEREST.value,
                PaymentCategory.RESERVES.value,
                PaymentCategory.SENIOR_PRINCIPAL.value,
                PaymentCategory.MEZZ_PRINCIPAL.value,
                PaymentCategory.MANAGEMENT_FEES.value,
                PaymentCategory.SUBORDINATED_INTEREST.value,
                PaymentCategory.SUBORDINATED_PRINCIPAL.value,
                PaymentCategory.RESIDUAL.value
            ],
            category_rules={
                PaymentCategory.SENIOR_INTEREST.value: {"always_pay": True},
                PaymentCategory.MEZZ_INTEREST.value: {"deferrable": False},
                PaymentCategory.SENIOR_PRINCIPAL.value: {"requires_tests": True}
            },
            jurisdiction="US",
            typical_use_case="Simple CLO structures with minimal complexity"
        )
        structures.append(three_tranche)
        
        # 5-Tranche Structure (A, B, C, D, E)
        five_tranche = WaterfallStructure(
            structure_name="FIVE_TRANCHE_CLO",
            min_tranches=5,
            max_tranches=5,
            typical_tranches=5,
            payment_sequence=[
                PaymentCategory.EXPENSES.value,
                PaymentCategory.SENIOR_INTEREST.value,
                PaymentCategory.MEZZ_INTEREST.value,
                PaymentCategory.RESERVES.value,
                PaymentCategory.SENIOR_PRINCIPAL.value,
                PaymentCategory.MEZZ_PRINCIPAL.value,
                PaymentCategory.MANAGEMENT_FEES.value,
                PaymentCategory.SUBORDINATED_INTEREST.value,
                PaymentCategory.SUBORDINATED_PRINCIPAL.value,
                PaymentCategory.RESIDUAL.value
            ],
            category_rules={
                PaymentCategory.MEZZ_INTEREST.value: {"deferrable": True, "pik_eligible": True},
                PaymentCategory.SUBORDINATED_INTEREST.value: {"deferrable": True}
            },
            jurisdiction="US",
            typical_use_case="Standard US CLO with full rating spectrum"
        )
        structures.append(five_tranche)
        
        # 7-Tranche Structure (A1, A2, B, C, D, E, F)
        seven_tranche = WaterfallStructure(
            structure_name="SEVEN_TRANCHE_CLO",
            min_tranches=6,
            max_tranches=8,
            typical_tranches=7,
            payment_sequence=[
                PaymentCategory.EXPENSES.value,
                PaymentCategory.SENIOR_INTEREST.value,
                PaymentCategory.MEZZ_INTEREST.value,
                PaymentCategory.SUBORDINATED_INTEREST.value,
                PaymentCategory.RESERVES.value,
                PaymentCategory.SENIOR_PRINCIPAL.value,
                PaymentCategory.MEZZ_PRINCIPAL.value,
                PaymentCategory.MANAGEMENT_FEES.value,
                PaymentCategory.SUBORDINATED_PRINCIPAL.value,
                PaymentCategory.RESIDUAL.value
            ],
            category_rules={
                PaymentCategory.SUBORDINATED_INTEREST.value: {"deferrable": True, "pik_eligible": True},
                PaymentCategory.SUBORDINATED_PRINCIPAL.value: {"turbo_eligible": False}
            },
            jurisdiction="US",
            typical_use_case="Complex CLO structures with granular rating tranches"
        )
        structures.append(seven_tranche)
        
        # European Structure
        european_structure = WaterfallStructure(
            structure_name="EUROPEAN_CLO",
            min_tranches=4,
            max_tranches=6,
            typical_tranches=5,
            payment_sequence=[
                PaymentCategory.EXPENSES.value,
                PaymentCategory.SENIOR_INTEREST.value,
                PaymentCategory.MEZZ_INTEREST.value,
                PaymentCategory.RESERVES.value,
                PaymentCategory.SENIOR_PRINCIPAL.value,
                PaymentCategory.MEZZ_PRINCIPAL.value,
                PaymentCategory.SUBORDINATED_INTEREST.value,
                PaymentCategory.MANAGEMENT_FEES.value,
                PaymentCategory.SUBORDINATED_PRINCIPAL.value,
                PaymentCategory.RESIDUAL.value
            ],
            category_rules={
                PaymentCategory.SENIOR_INTEREST.value: {"business_day_adj": "Modified Following"},
                PaymentCategory.RESERVES.value: {"regulatory_reserve": True}
            },
            jurisdiction="EU",
            typical_use_case="European CLO with regulatory requirements"
        )
        structures.append(european_structure)
        
        return structures
    
    @classmethod
    def create_tranche_mappings_for_deal(cls, deal_id: str, tranches: List[CLOTranche], 
                                       structure_name: str, session) -> List[TrancheMapping]:
        """Create tranche mappings for specific deal based on structure"""
        mappings = []
        
        # Sort tranches by seniority
        sorted_tranches = sorted(tranches, key=lambda t: t.seniority_level or 999)
        
        for i, tranche in enumerate(sorted_tranches):
            mapping = cls._create_mapping_for_tranche(
                deal_id, tranche, i, len(sorted_tranches), structure_name
            )
            mappings.append(mapping)
        
        return mappings
    
    @classmethod
    def _create_mapping_for_tranche(cls, deal_id: str, tranche: CLOTranche, 
                                  index: int, total_tranches: int, structure_name: str) -> TrancheMapping:
        """Create mapping for individual tranche"""
        
        # Determine tranche type based on position and characteristics
        if index == 0:  # Most senior
            tranche_type = TrancheType.SENIOR_AAA
            payment_category = PaymentCategory.SENIOR_INTEREST
        elif index < total_tranches // 2:  # Senior tranches
            tranche_type = TrancheType.SENIOR_AA if index == 1 else TrancheType.SENIOR_A
            payment_category = PaymentCategory.SENIOR_INTEREST
        elif index < total_tranches - 2:  # Mezzanine tranches
            tranche_type = TrancheType.MEZZANINE_BBB
            payment_category = PaymentCategory.MEZZ_INTEREST
        else:  # Subordinated tranches
            tranche_type = TrancheType.SUBORDINATED
            payment_category = PaymentCategory.SUBORDINATED_INTEREST
        
        # Generate step names
        class_letter = cls._get_class_letter(index)
        interest_step = f"CLASS_{class_letter}_INTEREST"
        principal_step = f"CLASS_{class_letter}_PRINCIPAL"
        
        return TrancheMapping(
            deal_id=deal_id,
            tranche_id=tranche.tranche_id,
            tranche_type=tranche_type.value,
            payment_category=payment_category.value,
            category_rank=index + 1,
            interest_step=interest_step,
            principal_step=principal_step,
            is_deferrable=(payment_category == PaymentCategory.SUBORDINATED_INTEREST),
            is_pik_eligible=(payment_category in [PaymentCategory.MEZZ_INTEREST, PaymentCategory.SUBORDINATED_INTEREST]),
            supports_turbo=(payment_category != PaymentCategory.SUBORDINATED_INTEREST),
            effective_date=date.today()
        )
    
    @classmethod
    def _get_class_letter(cls, index: int) -> str:
        """Get class letter for tranche index"""
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        return letters[index] if index < len(letters) else f"T{index}"