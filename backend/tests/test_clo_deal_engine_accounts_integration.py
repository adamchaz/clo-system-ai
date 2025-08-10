"""
Test CLO Deal Engine integration with enhanced Accounts system

Validates that the existing CLO Deal Engine continues to work while
optionally providing enhanced database persistence for account management.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.core.database import Base
from app.models.clo_deal import CLODeal
from app.models.clo_deal_engine import (
    CLODealEngine, 
    AccountType, 
    CashType, 
    Account,
    DealDates,
    ReinvestmentInfo
)
from app.models.accounts import AccountsService


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def sample_clo_deal():
    """Create sample CLO deal for testing"""
    return CLODeal(
        deal_id="TEST_DEAL_001",
        deal_name="Test CLO Deal",
        status="ACTIVE",
        closing_date=date(2025, 1, 1)
    )


@pytest.fixture  
def sample_deal_dates():
    """Create sample deal dates"""
    return DealDates(
        analysis_date=date(2025, 1, 1),
        closing_date=date(2025, 1, 1),
        first_payment_date=date(2025, 4, 15),
        maturity_date=date(2030, 1, 15),
        reinvestment_end_date=date(2027, 1, 15),
        no_call_date=date(2026, 1, 15),
        payment_day=15,
        months_between_payments=3,
        business_day_convention="FOLLOWING",
        determination_date_offset=2,
        interest_determination_date_offset=2
    )


class TestCLODealEngineAccountsIntegration:
    """Test CLO Deal Engine with enhanced accounts system"""

    def test_backward_compatibility_without_persistence(self, sample_clo_deal, in_memory_db):
        """Test existing functionality works without database persistence"""
        engine = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=False)
        
        # Setup accounts without persistence (existing behavior)
        engine.setup_accounts()
        
        # Verify accounts are created and work as before
        assert len(engine.accounts) == len(AccountType)
        
        collection_account = engine.accounts[AccountType.COLLECTION]
        assert collection_account.interest_proceeds == Decimal('0')
        assert collection_account.principal_proceeds == Decimal('0')
        assert collection_account.total_proceeds == Decimal('0')
        
        # Test adding cash flows (existing behavior)
        collection_account.add(CashType.INTEREST, Decimal('100000'))
        collection_account.add(CashType.PRINCIPAL, Decimal('50000'))
        
        assert collection_account.interest_proceeds == Decimal('100000')
        assert collection_account.principal_proceeds == Decimal('50000')
        assert collection_account.total_proceeds == Decimal('150000')
        
        # Verify no database persistence occurred
        assert collection_account.enable_persistence == False
        assert collection_account._accounts_calculator is None

    def test_enhanced_functionality_with_persistence(self, sample_clo_deal, in_memory_db):
        """Test enhanced functionality with database persistence"""
        engine = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        
        # Setup accounts with persistence and specific period date
        period_date = date(2025, 1, 15)
        engine.setup_accounts(period_date=period_date)
        
        # Verify accounts are created with persistence enabled
        assert len(engine.accounts) == len(AccountType)
        assert engine.accounts_service is not None
        
        collection_account = engine.accounts[AccountType.COLLECTION]
        assert collection_account.enable_persistence == True
        assert collection_account._accounts_calculator is not None
        
        # Test adding cash flows with database persistence
        collection_account.add(CashType.INTEREST, Decimal('200000'))
        collection_account.add(CashType.PRINCIPAL, Decimal('100000'))
        
        assert collection_account.interest_proceeds == Decimal('200000')
        assert collection_account.principal_proceeds == Decimal('100000')
        assert collection_account.total_proceeds == Decimal('300000')
        
        # Save to database
        saved_account = collection_account.save()
        assert saved_account is not None
        assert saved_account.deal_id == sample_clo_deal.deal_id
        assert saved_account.period_date == period_date

    def test_transaction_record_creation(self, sample_clo_deal, in_memory_db):
        """Test detailed transaction record creation"""
        engine = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        engine.setup_accounts(period_date=date(2025, 1, 15))
        
        collection_account = engine.accounts[AccountType.COLLECTION]
        
        # Create transaction record
        transaction = collection_account.create_transaction_record(
            CashType.INTEREST,
            Decimal('75000'),
            reference_id="ASSET_12345",
            description="Interest from ABC Corp",
            counterparty="ABC Corporation"
        )
        
        assert transaction is not None
        assert transaction.cash_type == "INTEREST"
        assert transaction.amount == Decimal('75000')
        assert transaction.reference_id == "ASSET_12345"
        assert transaction.description == "Interest from ABC Corp"
        assert transaction.counterparty == "ABC Corporation"

    def test_account_summaries_generation(self, sample_clo_deal, in_memory_db):
        """Test account summary generation for reporting"""
        engine = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        period_date = date(2025, 1, 15)
        engine.setup_accounts(period_date=period_date)
        
        # Add some cash flows to different accounts
        engine.accounts[AccountType.COLLECTION].add(CashType.INTEREST, Decimal('100000'))
        engine.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, Decimal('50000'))
        engine.accounts[AccountType.INTEREST_RESERVE].add(CashType.INTEREST, Decimal('25000'))
        
        # Get account summaries
        summaries = engine.get_account_summaries(period_date)
        
        assert 'COLLECTION' in summaries
        assert summaries['COLLECTION']['interest_proceeds'] == 100000.0
        assert summaries['COLLECTION']['principal_proceeds'] == 50000.0
        assert summaries['COLLECTION']['total_proceeds'] == 150000.0
        
        assert 'INTEREST_RESERVE' in summaries
        assert summaries['INTEREST_RESERVE']['interest_proceeds'] == 25000.0

    def test_account_persistence_across_sessions(self, sample_clo_deal, in_memory_db):
        """Test that account data persists across different engine instances"""
        deal_id = sample_clo_deal.deal_id
        period_date = date(2025, 1, 15)
        
        # First engine instance - create and save data
        engine1 = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        engine1.setup_accounts(period_date=period_date)
        
        engine1.accounts[AccountType.COLLECTION].add(CashType.INTEREST, Decimal('500000'))
        engine1.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, Decimal('250000'))
        engine1.save_all_accounts()
        
        # Second engine instance - should load existing data
        sample_clo_deal_2 = CLODeal(
            deal_id=deal_id,
            deal_name="Test CLO Deal (Reload)",
            status="ACTIVE",
            closing_date=date(2025, 1, 1)
        )
        engine2 = CLODealEngine(sample_clo_deal_2, in_memory_db, enable_account_persistence=True)
        engine2.setup_accounts(period_date=period_date)
        
        # Verify data was loaded from database
        collection_account = engine2.accounts[AccountType.COLLECTION]
        assert collection_account.interest_proceeds == Decimal('500000')
        assert collection_account.principal_proceeds == Decimal('250000')
        assert collection_account.total_proceeds == Decimal('750000')

    def test_mixed_persistence_modes(self, sample_clo_deal, in_memory_db):
        """Test that engines with different persistence settings work independently"""
        # Engine with persistence
        engine_with_db = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        engine_with_db.setup_accounts(period_date=date(2025, 1, 15))
        
        # Engine without persistence
        engine_without_db = CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=False)
        engine_without_db.setup_accounts()
        
        # Both should work independently
        engine_with_db.accounts[AccountType.COLLECTION].add(CashType.INTEREST, Decimal('100000'))
        engine_without_db.accounts[AccountType.COLLECTION].add(CashType.INTEREST, Decimal('200000'))
        
        assert engine_with_db.accounts[AccountType.COLLECTION].interest_proceeds == Decimal('100000')
        assert engine_without_db.accounts[AccountType.COLLECTION].interest_proceeds == Decimal('200000')
        
        # Only the persistent one should save successfully
        result_with_db = engine_with_db.save_all_accounts()
        result_without_db = engine_without_db.save_all_accounts()
        
        assert len(result_with_db) > 0  # Should have saved some accounts
        assert len(result_without_db) == 0  # Should have saved nothing

    def test_vba_functional_parity_maintained(self, sample_clo_deal, in_memory_db):
        """Test that VBA Accounts.cls functionality is preserved exactly"""
        # Test both persistence modes to ensure identical behavior
        engines = [
            CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=False),
            CLODealEngine(sample_clo_deal, in_memory_db, enable_account_persistence=True)
        ]
        
        period_date = date(2025, 1, 15)
        
        for i, engine in enumerate(engines):
            if engine.enable_account_persistence:
                engine.setup_accounts(period_date=period_date)
            else:
                engine.setup_accounts()
            
            account = engine.accounts[AccountType.COLLECTION]
            
            # VBA-equivalent operations
            account.add(CashType.INTEREST, Decimal('123456.78'))  # accounts.Add Interest, 123456.78
            account.add(CashType.PRINCIPAL, Decimal('987654.32'))  # accounts.Add Principal, 987654.32
            
            # VBA property access should be identical
            assert account.interest_proceeds == Decimal('123456.78')  # accounts.InterestProceeds
            assert account.principal_proceeds == Decimal('987654.32')  # accounts.PrincipalProceeds
            assert account.total_proceeds == Decimal('1111111.10')  # accounts.TotalProceeds


class TestAccountsServiceStandalone:
    """Test AccountsService functionality independently"""
    
    def test_accounts_service_initialization(self, in_memory_db):
        """Test AccountsService can be used independently"""
        service = AccountsService(in_memory_db)
        service.initialize_account_types()
        
        # Should have created standard account types
        from app.models.accounts import AccountType as DBAccountType
        account_types = in_memory_db.query(DBAccountType).all()
        assert len(account_types) >= 7  # Should have at least the 7 standard types
        
    def test_standalone_accounts_calculator(self, in_memory_db):
        """Test AccountsCalculator can be used independently"""
        service = AccountsService(in_memory_db)
        service.initialize_account_types()
        
        calculator = service.create_deal_accounts("STANDALONE_TEST", date(2025, 1, 15))
        
        # Test VBA-equivalent functionality
        from app.models.accounts import CashType
        calculator.add(CashType.INTEREST, Decimal('50000'))
        calculator.add(CashType.PRINCIPAL, Decimal('30000'))
        
        assert calculator.interest_proceeds == Decimal('50000')
        assert calculator.principal_proceeds == Decimal('30000')
        assert calculator.total_proceeds == Decimal('80000')
        
        # Save and verify persistence
        saved = calculator.save()
        assert saved.deal_id == "STANDALONE_TEST"
        assert saved.interest_proceeds == Decimal('50000')
        assert saved.principal_proceeds == Decimal('30000')