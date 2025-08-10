"""Create incentive fee system tables

Revision ID: 005_incentive_fee_system
Revises: 004_reinvestment_system
Create Date: 2025-01-10 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005_incentive_fee_system'
down_revision = '004_reinvestment_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create incentive fee system tables"""
    
    # 1. Incentive Fee Structures master table
    op.create_table(
        'incentive_fee_structures',
        sa.Column('fee_structure_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.String(length=50), nullable=False),
        sa.Column('fee_structure_name', sa.String(length=100), nullable=False),
        sa.Column('hurdle_rate', sa.DECIMAL(precision=6, scale=4), nullable=False),
        sa.Column('incentive_fee_rate', sa.DECIMAL(precision=6, scale=4), nullable=False),
        sa.Column('closing_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('threshold_reached', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('cum_discounted_sub_payments', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('analysis_date', sa.Date(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('fee_structure_id'),
        sa.UniqueConstraint('deal_id', 'fee_structure_name', name='uq_incentive_fee_structures')
    )
    
    # Create index for efficient fee structure lookup
    op.create_index('ix_incentive_fee_structures_deal_id', 'incentive_fee_structures', ['deal_id'])
    op.create_index('ix_incentive_fee_structures_active', 'incentive_fee_structures', ['is_active'])
    
    # 2. Subordinated Payments (payments to subordinated noteholders)
    op.create_table(
        'subordinated_payments',
        sa.Column('payment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fee_structure_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_amount', sa.DECIMAL(precision=18, scale=2), nullable=False),
        sa.Column('discounted_amount', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('days_from_closing', sa.Integer(), nullable=True),
        sa.Column('discount_factor', sa.DECIMAL(precision=10, scale=8), nullable=True),
        sa.Column('is_historical', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('period_number', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('payment_id'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['incentive_fee_structures.fee_structure_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('fee_structure_id', 'payment_date', name='uq_subordinated_payments_date')
    )
    
    # Create indexes for efficient payment lookup
    op.create_index('ix_subordinated_payments_fee_structure', 'subordinated_payments', ['fee_structure_id'])
    op.create_index('ix_subordinated_payments_date', 'subordinated_payments', ['payment_date'])
    op.create_index('ix_subordinated_payments_period', 'subordinated_payments', ['period_number'])
    
    # 3. Incentive Fee Calculations (period-by-period calculations)
    op.create_table(
        'incentive_fee_calculations',
        sa.Column('calculation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fee_structure_id', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('calculation_date', sa.Date(), nullable=False),
        
        # VBA IncentiveFee.cls variables mapped to columns
        sa.Column('current_threshold', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('threshold_reached', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('current_sub_payments', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('current_incentive_payments', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('fee_paid_period', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('cum_discounted_sub_payments', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('period_irr', sa.DECIMAL(precision=8, scale=6), nullable=True, doc='Period IRR calculation'),
        
        # Calculation metadata
        sa.Column('days_from_closing', sa.Integer(), nullable=True),
        sa.Column('hurdle_rate_used', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('incentive_fee_rate_used', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('threshold_shortfall', sa.DECIMAL(precision=18, scale=2), nullable=True, doc='Amount needed to reach threshold'),
        
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('calculation_id'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['incentive_fee_structures.fee_structure_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('fee_structure_id', 'period_number', name='uq_incentive_fee_calculations')
    )
    
    # Create indexes for efficient calculation lookup
    op.create_index('ix_incentive_fee_calculations_fee_structure', 'incentive_fee_calculations', ['fee_structure_id'])
    op.create_index('ix_incentive_fee_calculations_period', 'incentive_fee_calculations', ['period_number'])
    op.create_index('ix_incentive_fee_calculations_date', 'incentive_fee_calculations', ['calculation_date'])
    
    # 4. Fee Payment Transactions (actual fee payments made)
    op.create_table(
        'fee_payment_transactions',
        sa.Column('transaction_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fee_structure_id', sa.Integer(), nullable=False),
        sa.Column('calculation_id', sa.Integer(), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('base_amount', sa.DECIMAL(precision=18, scale=2), nullable=False),
        sa.Column('fee_amount', sa.DECIMAL(precision=18, scale=2), nullable=False),
        sa.Column('net_amount', sa.DECIMAL(precision=18, scale=2), nullable=False),
        sa.Column('fee_rate_applied', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('transaction_id'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['incentive_fee_structures.fee_structure_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['calculation_id'], ['incentive_fee_calculations.calculation_id'], ondelete='SET NULL')
    )
    
    # Create indexes for efficient transaction lookup
    op.create_index('ix_fee_payment_transactions_fee_structure', 'fee_payment_transactions', ['fee_structure_id'])
    op.create_index('ix_fee_payment_transactions_date', 'fee_payment_transactions', ['transaction_date'])
    op.create_index('ix_fee_payment_transactions_type', 'fee_payment_transactions', ['transaction_type'])
    
    # 5. IRR History (tracking IRR calculations over time)
    op.create_table(
        'irr_calculation_history',
        sa.Column('irr_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fee_structure_id', sa.Integer(), nullable=False),
        sa.Column('calculation_date', sa.Date(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('irr_value', sa.DECIMAL(precision=8, scale=6), nullable=True),
        sa.Column('cash_flows_count', sa.Integer(), nullable=True),
        sa.Column('calculation_method', sa.String(length=50), nullable=False, server_default=sa.text("'XIRR'")),
        sa.Column('cash_flows_json', sa.Text(), nullable=True, doc='JSON array of cash flows for verification'),
        sa.Column('dates_json', sa.Text(), nullable=True, doc='JSON array of dates for verification'),
        sa.Column('calculation_successful', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('irr_id'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['incentive_fee_structures.fee_structure_id'], ondelete='CASCADE')
    )
    
    # Create indexes for IRR lookup
    op.create_index('ix_irr_calculation_history_fee_structure', 'irr_calculation_history', ['fee_structure_id'])
    op.create_index('ix_irr_calculation_history_date', 'irr_calculation_history', ['calculation_date'])
    op.create_index('ix_irr_calculation_history_period', 'irr_calculation_history', ['period_number'])
    
    # Insert seed data for common incentive fee structures
    op.execute(text("""
        INSERT INTO incentive_fee_structures (deal_id, fee_structure_name, hurdle_rate, incentive_fee_rate, closing_date, description)
        VALUES 
        ('DEMO_DEAL_001', 'Standard Incentive Fee', 0.0800, 0.2000, '2025-01-15', 'Standard 8% hurdle, 20% incentive fee'),
        ('DEMO_DEAL_002', 'Enhanced Incentive Fee', 0.1000, 0.2500, '2025-02-01', 'Enhanced 10% hurdle, 25% incentive fee'),
        ('TEST_DEAL_001', 'Test Incentive Fee', 0.0600, 0.1500, '2025-01-10', 'Test 6% hurdle, 15% incentive fee')
    """))
    
    # Insert sample subordinated payment history
    op.execute(text("""
        INSERT INTO subordinated_payments (fee_structure_id, payment_date, payment_amount, is_historical)
        SELECT 
            fs.fee_structure_id,
            payment_date,
            payment_amount,
            TRUE
        FROM incentive_fee_structures fs
        CROSS JOIN (
            SELECT '2024-04-15' as payment_date, 1000000.00 as payment_amount UNION ALL
            SELECT '2024-07-15', 1200000.00 UNION ALL
            SELECT '2024-10-15', 950000.00 UNION ALL
            SELECT '2025-01-15', 1100000.00
        ) payments
        WHERE fs.deal_id = 'TEST_DEAL_001'
    """))
    
    # Insert sample fee calculations
    op.execute(text("""
        INSERT INTO incentive_fee_calculations (fee_structure_id, period_number, calculation_date, current_threshold, 
                                               current_sub_payments, fee_paid_period, period_irr)
        SELECT 
            fs.fee_structure_id,
            period_num,
            calc_date,
            threshold_amt,
            sub_payment_amt,
            fee_amt,
            irr_val
        FROM incentive_fee_structures fs
        CROSS JOIN (
            SELECT 1 as period_num, '2024-04-15' as calc_date, -500000.00 as threshold_amt, 
                   1000000.00 as sub_payment_amt, 0.00 as fee_amt, NULL as irr_val UNION ALL
            SELECT 2, '2024-07-15', -200000.00, 1200000.00, 0.00, 0.0650 UNION ALL
            SELECT 3, '2024-10-15', 0.00, 950000.00, 50000.00, 0.0780 UNION ALL
            SELECT 4, '2025-01-15', 0.00, 1100000.00, 75000.00, 0.0820
        ) calcs
        WHERE fs.deal_id = 'TEST_DEAL_001'
    """))


def downgrade() -> None:
    """Drop incentive fee system tables"""
    op.drop_table('irr_calculation_history')
    op.drop_table('fee_payment_transactions')
    op.drop_table('incentive_fee_calculations')
    op.drop_table('subordinated_payments')
    op.drop_table('incentive_fee_structures')