"""
Account management system - VBA Accounts.cls Python implementation

This module implements the VBA Accounts.cls functionality with database persistence.
Provides cash flow aggregation and categorization for waterfall execution.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ..core.database import Base


class CashType(str, Enum):
    """Cash flow type enumeration - matches VBA CashType enum"""
    INTEREST = "INTEREST"
    PRINCIPAL = "PRINCIPAL"


class AccountType(Base):
    """Account type definitions"""
    __tablename__ = 'account_types'
    
    type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(50), nullable=False, unique=True)
    type_category = Column(String(20), nullable=False)
    description = Column(Text)
    is_waterfall_input = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    deal_accounts = relationship("DealAccount", back_populates="account_type")


class DealAccount(Base):
    """Deal-specific account tracking - matches VBA Accounts.cls functionality"""
    __tablename__ = 'deal_accounts'
    
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    account_type_id = Column(Integer, ForeignKey('account_types.type_id'), nullable=False)
    account_name = Column(String(100))
    period_date = Column(Date, nullable=False)
    opening_balance = Column(DECIMAL(18,2), default=Decimal('0.00'))
    interest_proceeds = Column(DECIMAL(18,2), default=Decimal('0.00'))
    principal_proceeds = Column(DECIMAL(18,2), default=Decimal('0.00'))
    other_receipts = Column(DECIMAL(18,2), default=Decimal('0.00'))
    disbursements = Column(DECIMAL(18,2), default=Decimal('0.00'))
    closing_balance = Column(DECIMAL(18,2), default=Decimal('0.00'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    account_type = relationship("AccountType", back_populates="deal_accounts")
    transactions = relationship("AccountTransaction", back_populates="account")
    
    @property
    def total_proceeds(self) -> Decimal:
        """VBA: TotalProceeds property - computed total"""
        interest = self.interest_proceeds or Decimal('0')
        principal = self.principal_proceeds or Decimal('0')
        other = self.other_receipts or Decimal('0')
        return interest + principal + other
    
    def __repr__(self):
        return f"<DealAccount(deal_id='{self.deal_id}', type='{self.account_type.type_name}', total={self.total_proceeds})>"


class AccountTransaction(Base):
    """Detailed account transaction tracking"""
    __tablename__ = 'account_transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('deal_accounts.account_id'), nullable=False)
    transaction_date = Column(DateTime, server_default=func.now())
    transaction_type = Column(String(20), nullable=False)
    cash_type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(18,2), nullable=False)
    counterparty = Column(String(100))
    reference_id = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    account = relationship("DealAccount", back_populates="transactions")


class AccountsCalculator:
    """
    Python implementation of VBA Accounts.cls
    Provides cash flow aggregation and categorization
    """
    
    def __init__(self, deal_id: str, period_date: date, session: Session = None):
        self.deal_id = deal_id
        self.period_date = period_date
        self.session = session
        
        # VBA-equivalent private variables
        self._interest_proceeds = Decimal('0.00')
        self._principal_proceeds = Decimal('0.00')
        
        # Load existing account data if available
        if session:
            self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing account data for the period"""
        # Find existing account for this deal and period
        account = self.session.query(DealAccount).filter_by(
            deal_id=self.deal_id,
            period_date=self.period_date
        ).first()
        
        if account:
            self._interest_proceeds = account.interest_proceeds or Decimal('0.00')
            self._principal_proceeds = account.principal_proceeds or Decimal('0.00')
    
    @property
    def interest_proceeds(self) -> Decimal:
        """VBA: InterestProceeds property"""
        return self._interest_proceeds
    
    @property
    def principal_proceeds(self) -> Decimal:
        """VBA: PrincipalProceeds property"""
        return self._principal_proceeds
    
    @property
    def total_proceeds(self) -> Decimal:
        """VBA: TotalProceeds property"""
        return self._interest_proceeds + self._principal_proceeds
    
    def add(self, cash_type: CashType, amount: Decimal):
        """
        VBA: Add method - adds cash flows by type
        
        Args:
            cash_type: Type of cash flow (INTEREST or PRINCIPAL)
            amount: Amount to add
        """
        if cash_type == CashType.INTEREST:
            self._interest_proceeds += amount
        elif cash_type == CashType.PRINCIPAL:
            self._principal_proceeds += amount
        else:
            raise ValueError(f"Invalid cash type: {cash_type}")
    
    def save(self) -> Optional[DealAccount]:
        """Save account state to database"""
        if not self.session:
            return None
            
        # Find or create account record
        account = self.session.query(DealAccount).filter_by(
            deal_id=self.deal_id,
            period_date=self.period_date
        ).first()
        
        if not account:
            # Get default account type (or create one)
            account_type = self.session.query(AccountType).filter_by(
                type_name='TOTAL_PROCEEDS'
            ).first()
            
            if not account_type:
                # Create default account type if it doesn't exist
                account_type = AccountType(
                    type_name='TOTAL_PROCEEDS',
                    type_category='CASH_FLOW',
                    description='Combined interest and principal proceeds',
                    is_waterfall_input=True
                )
                self.session.add(account_type)
                self.session.flush()
            
            account = DealAccount(
                deal_id=self.deal_id,
                account_type_id=account_type.type_id,
                account_name=f"Account for {self.deal_id}",
                period_date=self.period_date
            )
            self.session.add(account)
        
        # Update amounts
        account.interest_proceeds = self._interest_proceeds
        account.principal_proceeds = self._principal_proceeds
        account.updated_at = func.now()
        
        self.session.commit()
        return account
    
    def create_transaction(self, cash_type: CashType, amount: Decimal, 
                          reference_id: str = None, description: str = None,
                          counterparty: str = None) -> Optional[AccountTransaction]:
        """Create detailed transaction record"""
        if not self.session:
            return None
            
        account = self.save()
        if not account:
            return None
        
        transaction = AccountTransaction(
            account_id=account.account_id,
            transaction_type="ADD",
            cash_type=cash_type.value,
            amount=amount,
            counterparty=counterparty,
            reference_id=reference_id,
            description=description
        )
        
        self.session.add(transaction)
        self.session.commit()
        return transaction


class AccountsService:
    """Service layer for account operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_deal_accounts(self, deal_id: str, period_date: date) -> AccountsCalculator:
        """Create accounts calculator for a deal and period"""
        return AccountsCalculator(deal_id, period_date, self.session)
    
    def get_deal_account_summary(self, deal_id: str, period_date: date) -> Dict:
        """Get account summary for reporting"""
        calculator = AccountsCalculator(deal_id, period_date, self.session)
        
        return {
            'deal_id': deal_id,
            'period_date': period_date,
            'interest_proceeds': float(calculator.interest_proceeds),
            'principal_proceeds': float(calculator.principal_proceeds),
            'total_proceeds': float(calculator.total_proceeds)
        }
    
    def get_period_range_summary(self, deal_id: str, start_date: date, 
                                end_date: date) -> List[Dict]:
        """Get account summary for multiple periods"""
        accounts = self.session.query(DealAccount).filter(
            DealAccount.deal_id == deal_id,
            DealAccount.period_date >= start_date,
            DealAccount.period_date <= end_date
        ).order_by(DealAccount.period_date).all()
        
        return [
            {
                'period_date': account.period_date,
                'interest_proceeds': float(account.interest_proceeds or 0),
                'principal_proceeds': float(account.principal_proceeds or 0),
                'total_proceeds': float(account.total_proceeds)
            }
            for account in accounts
        ]
    
    def initialize_account_types(self):
        """Initialize standard account types"""
        standard_types = [
            ('INTEREST_PROCEEDS', 'CASH_FLOW', 'Interest cash flows from assets', True),
            ('PRINCIPAL_PROCEEDS', 'CASH_FLOW', 'Principal cash flows from assets', True),
            ('TOTAL_PROCEEDS', 'CASH_FLOW', 'Combined interest and principal proceeds', True),
            ('RESERVE_ACCOUNT', 'RESERVE', 'Deal reserve accounts', False),
            ('EXPENSE_ACCOUNT', 'EXPENSE', 'Deal expense accounts', False),
            ('COLLECTION_ACCOUNT', 'OPERATIONAL', 'Primary collection account', True),
            ('REINVESTMENT_ACCOUNT', 'OPERATIONAL', 'Reinvestment period proceeds', True)
        ]
        
        for type_name, category, desc, is_input in standard_types:
            existing = self.session.query(AccountType).filter_by(type_name=type_name).first()
            if not existing:
                account_type = AccountType(
                    type_name=type_name,
                    type_category=category,
                    description=desc,
                    is_waterfall_input=is_input
                )
                self.session.add(account_type)
        
        self.session.commit()