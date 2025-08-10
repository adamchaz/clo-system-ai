"""
Test suite for VBA Accounts.cls Python implementation

Comprehensive testing of AccountsCalculator, AccountsService, and database models
to ensure perfect VBA functional parity.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.core.database import Base
from app.models.accounts import (
    AccountsCalculator, 
    AccountsService, 
    CashType, 
    AccountType, 
    DealAccount, 
    AccountTransaction
)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create standard account types
    service = AccountsService(session)
    service.initialize_account_types()
    
    return session


class TestAccountsCalculator:
    """Test VBA Accounts.cls functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.deal_id = "TEST_DEAL_001"
        self.period_date = date(2025, 1, 15)
        
    def test_empty_accounts_initialization_without_session(self):
        """Test empty accounts start with zero values (no database)"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        assert accounts.interest_proceeds == Decimal('0.00')
        assert accounts.principal_proceeds == Decimal('0.00')
        assert accounts.total_proceeds == Decimal('0.00')
    
    def test_empty_accounts_initialization_with_session(self, in_memory_db):
        """Test empty accounts start with zero values (with database)"""
        accounts = AccountsCalculator(self.deal_id, self.period_date, in_memory_db)
        
        assert accounts.interest_proceeds == Decimal('0.00')
        assert accounts.principal_proceeds == Decimal('0.00')
        assert accounts.total_proceeds == Decimal('0.00')
    
    def test_add_interest_proceeds(self):
        """Test adding interest cash flows - VBA functional parity"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        # VBA: accounts.Add(Interest, 100000.0)
        accounts.add(CashType.INTEREST, Decimal('100000.00'))
        accounts.add(CashType.INTEREST, Decimal('50000.00'))
        
        assert accounts.interest_proceeds == Decimal('150000.00')
        assert accounts.principal_proceeds == Decimal('0.00')
        assert accounts.total_proceeds == Decimal('150000.00')
    
    def test_add_principal_proceeds(self):
        """Test adding principal cash flows - VBA functional parity"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        # VBA: accounts.Add(Principal, 75000.0)
        accounts.add(CashType.PRINCIPAL, Decimal('75000.00'))
        accounts.add(CashType.PRINCIPAL, Decimal('25000.00'))
        
        assert accounts.interest_proceeds == Decimal('0.00')
        assert accounts.principal_proceeds == Decimal('100000.00')
        assert accounts.total_proceeds == Decimal('100000.00')
    
    def test_mixed_cash_flows_vba_parity(self):
        """Test mixed interest and principal flows - exact VBA behavior"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        # Simulate VBA sequence:
        # accounts.Add(Interest, 120000)
        # accounts.Add(Principal, 80000)
        # accounts.Add(Interest, 30000)
        accounts.add(CashType.INTEREST, Decimal('120000.00'))
        accounts.add(CashType.PRINCIPAL, Decimal('80000.00'))
        accounts.add(CashType.INTEREST, Decimal('30000.00'))
        
        # VBA property access:
        # InterestProceeds = 150000
        # PrincipalProceeds = 80000
        # TotalProceeds = 230000
        assert accounts.interest_proceeds == Decimal('150000.00')
        assert accounts.principal_proceeds == Decimal('80000.00')
        assert accounts.total_proceeds == Decimal('230000.00')
    
    def test_property_access_matches_vba(self):
        """Test property getters match VBA behavior exactly"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        accounts.add(CashType.INTEREST, Decimal('123456.78'))
        accounts.add(CashType.PRINCIPAL, Decimal('987654.32'))
        
        # VBA: InterestProceeds property
        assert accounts.interest_proceeds == Decimal('123456.78')
        
        # VBA: PrincipalProceeds property
        assert accounts.principal_proceeds == Decimal('987654.32')
        
        # VBA: TotalProceeds property (computed)
        expected_total = Decimal('123456.78') + Decimal('987654.32')
        assert accounts.total_proceeds == expected_total
    
    def test_database_persistence(self, in_memory_db):
        """Test saving and loading account state"""
        accounts = AccountsCalculator(self.deal_id, self.period_date, in_memory_db)
        
        accounts.add(CashType.INTEREST, Decimal('100000.00'))
        accounts.add(CashType.PRINCIPAL, Decimal('50000.00'))
        saved_account = accounts.save()
        
        assert saved_account is not None
        assert saved_account.deal_id == self.deal_id
        assert saved_account.period_date == self.period_date
        
        # Load new calculator instance
        accounts2 = AccountsCalculator(self.deal_id, self.period_date, in_memory_db)
        
        assert accounts2.interest_proceeds == Decimal('100000.00')
        assert accounts2.principal_proceeds == Decimal('50000.00')
        assert accounts2.total_proceeds == Decimal('150000.00')
    
    def test_invalid_cash_type_error(self):
        """Test error handling for invalid cash type"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        with pytest.raises(ValueError, match="Invalid cash type"):
            accounts.add("INVALID_TYPE", Decimal('100.00'))
    
    def test_transaction_creation(self, in_memory_db):
        """Test detailed transaction record creation"""
        accounts = AccountsCalculator(self.deal_id, self.period_date, in_memory_db)
        
        transaction = accounts.create_transaction(
            CashType.INTEREST, 
            Decimal('75000.00'),
            reference_id="ASSET_001",
            description="Interest from XYZ Corp",
            counterparty="XYZ Corporation"
        )
        
        assert transaction is not None
        assert transaction.cash_type == "INTEREST"
        assert transaction.amount == Decimal('75000.00')
        assert transaction.reference_id == "ASSET_001"
        assert transaction.description == "Interest from XYZ Corp"
        assert transaction.counterparty == "XYZ Corporation"
    
    def test_zero_amounts_handling(self):
        """Test handling of zero amounts"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        accounts.add(CashType.INTEREST, Decimal('0.00'))
        accounts.add(CashType.PRINCIPAL, Decimal('0.00'))
        
        assert accounts.interest_proceeds == Decimal('0.00')
        assert accounts.principal_proceeds == Decimal('0.00')
        assert accounts.total_proceeds == Decimal('0.00')
    
    def test_large_amounts_precision(self):
        """Test precision handling for large amounts"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        # Large amounts with high precision
        large_interest = Decimal('999999999.99')
        large_principal = Decimal('888888888.88')
        
        accounts.add(CashType.INTEREST, large_interest)
        accounts.add(CashType.PRINCIPAL, large_principal)
        
        assert accounts.interest_proceeds == large_interest
        assert accounts.principal_proceeds == large_principal
        assert accounts.total_proceeds == large_interest + large_principal
    
    def test_cumulative_additions(self):
        """Test cumulative additions work correctly"""
        accounts = AccountsCalculator(self.deal_id, self.period_date)
        
        # Multiple small additions
        for i in range(5):
            accounts.add(CashType.INTEREST, Decimal('10000.00'))
            accounts.add(CashType.PRINCIPAL, Decimal('5000.00'))
        
        assert accounts.interest_proceeds == Decimal('50000.00')
        assert accounts.principal_proceeds == Decimal('25000.00')
        assert accounts.total_proceeds == Decimal('75000.00')


class TestAccountsService:
    """Test service layer functionality"""
    
    def test_deal_account_summary(self, in_memory_db):
        """Test account summary generation"""
        service = AccountsService(in_memory_db)
        accounts = service.create_deal_accounts("TEST_DEAL", date(2025, 1, 15))
        
        accounts.add(CashType.INTEREST, Decimal('75000.00'))
        accounts.add(CashType.PRINCIPAL, Decimal('25000.00'))
        accounts.save()
        
        summary = service.get_deal_account_summary("TEST_DEAL", date(2025, 1, 15))
        
        assert summary['deal_id'] == "TEST_DEAL"
        assert summary['interest_proceeds'] == 75000.00
        assert summary['principal_proceeds'] == 25000.00
        assert summary['total_proceeds'] == 100000.00
    
    def test_period_range_summary(self, in_memory_db):
        """Test multi-period summary"""
        service = AccountsService(in_memory_db)
        
        # Create accounts for multiple periods
        periods = [
            (date(2025, 1, 15), Decimal('10000'), Decimal('5000')),
            (date(2025, 2, 15), Decimal('12000'), Decimal('6000')),
            (date(2025, 3, 15), Decimal('14000'), Decimal('7000'))
        ]
        
        for period_date, interest, principal in periods:
            accounts = service.create_deal_accounts("MULTI_PERIOD", period_date)
            accounts.add(CashType.INTEREST, interest)
            accounts.add(CashType.PRINCIPAL, principal)
            accounts.save()
        
        summary = service.get_period_range_summary(
            "MULTI_PERIOD", 
            date(2025, 1, 1), 
            date(2025, 3, 31)
        )
        
        assert len(summary) == 3
        assert summary[0]['interest_proceeds'] == 10000.00
        assert summary[1]['interest_proceeds'] == 12000.00
        assert summary[2]['interest_proceeds'] == 14000.00
        assert summary[0]['total_proceeds'] == 15000.00
        assert summary[1]['total_proceeds'] == 18000.00
        assert summary[2]['total_proceeds'] == 21000.00
    
    def test_account_types_initialization(self, in_memory_db):
        """Test standard account types are created correctly"""
        service = AccountsService(in_memory_db)
        
        # Account types should already be initialized via fixture
        account_types = in_memory_db.query(AccountType).all()
        type_names = [at.type_name for at in account_types]
        
        expected_types = [
            'INTEREST_PROCEEDS', 'PRINCIPAL_PROCEEDS', 'TOTAL_PROCEEDS',
            'RESERVE_ACCOUNT', 'EXPENSE_ACCOUNT', 'COLLECTION_ACCOUNT',
            'REINVESTMENT_ACCOUNT'
        ]
        
        for expected in expected_types:
            assert expected in type_names


class TestDealAccount:
    """Test DealAccount SQLAlchemy model"""
    
    def test_total_proceeds_property(self, in_memory_db):
        """Test computed total proceeds property"""
        account_type = in_memory_db.query(AccountType).filter_by(
            type_name='TOTAL_PROCEEDS'
        ).first()
        
        account = DealAccount(
            deal_id="TEST_DEAL",
            account_type_id=account_type.type_id,
            period_date=date(2025, 1, 15),
            interest_proceeds=Decimal('100000.00'),
            principal_proceeds=Decimal('50000.00'),
            other_receipts=Decimal('25000.00')
        )
        
        assert account.total_proceeds == Decimal('175000.00')
    
    def test_account_relationships(self, in_memory_db):
        """Test SQLAlchemy relationships"""
        service = AccountsService(in_memory_db)
        accounts = service.create_deal_accounts("REL_TEST", date(2025, 1, 15))
        
        accounts.add(CashType.INTEREST, Decimal('50000'))
        saved_account = accounts.save()
        
        transaction = accounts.create_transaction(
            CashType.INTEREST,
            Decimal('50000'),
            reference_id="TEST_REF"
        )
        
        # Test relationships
        assert saved_account.account_type is not None
        assert len(saved_account.transactions) == 1
        assert saved_account.transactions[0].reference_id == "TEST_REF"


class TestVBAFunctionalParity:
    """Comprehensive VBA comparison tests"""
    
    def test_exact_vba_behavior_scenario_1(self):
        """Test scenario matching exact VBA usage pattern"""
        # VBA scenario:
        # Dim accounts As New Accounts
        # accounts.Add Interest, 125000.50
        # accounts.Add Principal, 75000.25
        # Debug.Print accounts.InterestProceeds   ' Should be 125000.50
        # Debug.Print accounts.PrincipalProceeds  ' Should be 75000.25
        # Debug.Print accounts.TotalProceeds      ' Should be 200000.75
        
        accounts = AccountsCalculator("VBA_TEST", date(2025, 1, 15))
        accounts.add(CashType.INTEREST, Decimal('125000.50'))
        accounts.add(CashType.PRINCIPAL, Decimal('75000.25'))
        
        assert accounts.interest_proceeds == Decimal('125000.50')
        assert accounts.principal_proceeds == Decimal('75000.25')
        assert accounts.total_proceeds == Decimal('200000.75')
    
    def test_exact_vba_behavior_scenario_2(self):
        """Test scenario with multiple additions"""
        # VBA scenario:
        # Dim accounts As New Accounts
        # For i = 1 To 10
        #     accounts.Add Interest, 1000
        #     accounts.Add Principal, 500
        # Next i
        # Debug.Print accounts.TotalProceeds  ' Should be 15000
        
        accounts = AccountsCalculator("VBA_TEST_2", date(2025, 1, 15))
        
        for i in range(10):
            accounts.add(CashType.INTEREST, Decimal('1000'))
            accounts.add(CashType.PRINCIPAL, Decimal('500'))
        
        assert accounts.interest_proceeds == Decimal('10000')
        assert accounts.principal_proceeds == Decimal('5000')
        assert accounts.total_proceeds == Decimal('15000')
    
    def test_property_getter_behavior(self):
        """Test that properties behave exactly like VBA properties"""
        accounts = AccountsCalculator("PROP_TEST", date(2025, 1, 15))
        
        # Initially zero (like VBA)
        assert accounts.interest_proceeds == Decimal('0')
        
        # Add some amounts
        accounts.add(CashType.INTEREST, Decimal('12345.67'))
        
        # Property should immediately reflect the change
        assert accounts.interest_proceeds == Decimal('12345.67')
        
        # Multiple property accesses should return same value
        val1 = accounts.interest_proceeds
        val2 = accounts.interest_proceeds
        assert val1 == val2 == Decimal('12345.67')


class TestErrorHandling:
    """Test error conditions and edge cases"""
    
    def test_none_session_handling(self):
        """Test graceful handling when no database session provided"""
        accounts = AccountsCalculator("NO_SESSION", date(2025, 1, 15))
        
        # Should work without session
        accounts.add(CashType.INTEREST, Decimal('1000'))
        assert accounts.interest_proceeds == Decimal('1000')
        
        # Save should return None gracefully
        result = accounts.save()
        assert result is None
        
        # Transaction creation should return None gracefully
        transaction = accounts.create_transaction(CashType.INTEREST, Decimal('100'))
        assert transaction is None
    
    def test_edge_case_dates(self, in_memory_db):
        """Test edge case dates"""
        # Far future date
        future_date = date(2099, 12, 31)
        accounts = AccountsCalculator("FUTURE", future_date, in_memory_db)
        accounts.add(CashType.INTEREST, Decimal('100'))
        
        result = accounts.save()
        assert result.period_date == future_date
        
        # Far past date
        past_date = date(2000, 1, 1)
        accounts2 = AccountsCalculator("PAST", past_date, in_memory_db)
        accounts2.add(CashType.PRINCIPAL, Decimal('200'))
        
        result2 = accounts2.save()
        assert result2.period_date == past_date