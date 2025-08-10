"""Account management system tables

Revision ID: 001_account_management
Revises: 
Create Date: 2025-01-10

Implements VBA Accounts.cls functionality with database persistence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_account_management'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create account management tables"""
    
    # Create account_types table
    op.create_table('account_types',
        sa.Column('type_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type_name', sa.String(length=50), nullable=False),
        sa.Column('type_category', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_waterfall_input', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('type_id'),
        sa.UniqueConstraint('type_name')
    )
    
    # Create deal_accounts table
    op.create_table('deal_accounts',
        sa.Column('account_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.String(length=50), nullable=False),
        sa.Column('account_type_id', sa.Integer(), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=True),
        sa.Column('period_date', sa.Date(), nullable=False),
        sa.Column('opening_balance', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('interest_proceeds', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('principal_proceeds', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('other_receipts', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('disbursements', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('closing_balance', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['account_type_id'], ['account_types.type_id'], ),
        sa.ForeignKeyConstraint(['deal_id'], ['clo_deals.deal_id'], ),
        sa.PrimaryKeyConstraint('account_id'),
        sa.UniqueConstraint('deal_id', 'account_type_id', 'period_date', name='unique_deal_account_period')
    )
    
    # Create account_transactions table
    op.create_table('account_transactions',
        sa.Column('transaction_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('cash_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=18, scale=2), nullable=False),
        sa.Column('counterparty', sa.String(length=100), nullable=True),
        sa.Column('reference_id', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['deal_accounts.account_id'], ),
        sa.PrimaryKeyConstraint('transaction_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_deal_accounts_deal_date', 'deal_accounts', ['deal_id', 'period_date'])
    op.create_index('idx_deal_accounts_type', 'deal_accounts', ['account_type_id'])
    op.create_index('idx_account_transactions_account', 'account_transactions', ['account_id'])
    op.create_index('idx_account_transactions_date', 'account_transactions', ['transaction_date'])
    op.create_index('idx_account_transactions_reference', 'account_transactions', ['reference_id'])
    
    # Insert seed data for standard account types
    op.execute("""
        INSERT INTO account_types (type_name, type_category, description, is_waterfall_input) VALUES 
        ('INTEREST_PROCEEDS', 'CASH_FLOW', 'Interest cash flows from assets', true),
        ('PRINCIPAL_PROCEEDS', 'CASH_FLOW', 'Principal cash flows from assets', true),
        ('TOTAL_PROCEEDS', 'CASH_FLOW', 'Combined interest and principal proceeds', true),
        ('RESERVE_ACCOUNT', 'RESERVE', 'Deal reserve accounts', false),
        ('EXPENSE_ACCOUNT', 'EXPENSE', 'Deal expense accounts', false),
        ('COLLECTION_ACCOUNT', 'OPERATIONAL', 'Primary collection account', true),
        ('REINVESTMENT_ACCOUNT', 'OPERATIONAL', 'Reinvestment period proceeds', true)
    """)

def downgrade():
    """Drop account management tables"""
    
    # Drop indexes
    op.drop_index('idx_account_transactions_reference')
    op.drop_index('idx_account_transactions_date')
    op.drop_index('idx_account_transactions_account')
    op.drop_index('idx_deal_accounts_type')
    op.drop_index('idx_deal_accounts_deal_date')
    
    # Drop tables in reverse order
    op.drop_table('account_transactions')
    op.drop_table('deal_accounts') 
    op.drop_table('account_types')