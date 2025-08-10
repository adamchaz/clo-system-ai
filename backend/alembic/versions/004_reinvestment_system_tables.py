"""Create reinvestment system tables

Revision ID: 004_reinvestment_system
Revises: 003_yield_curve_system
Create Date: 2025-01-10 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '004_reinvestment_system'
down_revision = '003_yield_curve_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reinvestment system tables"""
    
    # 1. Reinvestment Periods master table
    op.create_table(
        'reinvestment_periods',
        sa.Column('reinvest_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('reinvest_period', sa.Integer(), nullable=False),
        sa.Column('maturity_months', sa.Integer(), nullable=False),
        sa.Column('months_between_payments', sa.Integer(), nullable=False, server_default=sa.text('3')),
        sa.Column('yield_curve_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('reinvest_id'),
        sa.UniqueConstraint('deal_id', 'reinvest_period', name='uq_reinvestment_periods_deal_period')
    )
    
    # Create indexes for efficient reinvestment period lookup
    op.create_index('ix_reinvestment_periods_deal_id', 'reinvestment_periods', ['deal_id'])
    op.create_index('ix_reinvestment_periods_dates', 'reinvestment_periods', ['period_start', 'period_end'])
    
    # 2. Reinvestment Info (parameters for reinvestment modeling)
    op.create_table(
        'reinvestment_info',
        sa.Column('info_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reinvest_id', sa.Integer(), nullable=False),
        sa.Column('reinvest_price', sa.DECIMAL(precision=6, scale=4), nullable=False, server_default=sa.text('1.0000')),
        sa.Column('spread_bps', sa.Integer(), nullable=False, server_default=sa.text('500')),
        sa.Column('floor_rate', sa.DECIMAL(precision=6, scale=4), nullable=False, server_default=sa.text('0.0000')),
        sa.Column('liquidation_price', sa.DECIMAL(precision=6, scale=4), nullable=False, server_default=sa.text('0.7000')),
        sa.Column('lag_periods', sa.Integer(), nullable=False, server_default=sa.text('2')),
        sa.Column('prepayment_rate_annual', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('default_rate_annual', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('severity_rate', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('prepayment_vector', sa.Text(), nullable=True, doc='JSON array of prepayment rates by period'),
        sa.Column('default_vector', sa.Text(), nullable=True, doc='JSON array of default rates by period'),
        sa.Column('severity_vector', sa.Text(), nullable=True, doc='JSON array of severity rates by period'),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('info_id'),
        sa.ForeignKeyConstraint(['reinvest_id'], ['reinvestment_periods.reinvest_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('reinvest_id', name='uq_reinvestment_info_reinvest_id')
    )
    
    # Create index for reinvestment info lookup
    op.create_index('ix_reinvestment_info_reinvest_id', 'reinvestment_info', ['reinvest_id'])
    
    # 3. Reinvestment Cash Flows (detailed cash flow projections)
    op.create_table(
        'reinvestment_cash_flows',
        sa.Column('cash_flow_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reinvest_id', sa.Integer(), nullable=False),
        sa.Column('payment_period', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('accrual_start_date', sa.Date(), nullable=False),
        sa.Column('accrual_end_date', sa.Date(), nullable=False),
        
        # Balance information
        sa.Column('beg_performing_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('beg_default_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('beg_mv_default_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('end_performing_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('end_default_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('end_mv_default_balance', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        
        # Cash flow components (matching VBA SimpleCashflow structure)
        sa.Column('interest', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('scheduled_principal', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('unscheduled_principal', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('period_default', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('period_mv_default', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('recoveries', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('net_loss', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('sold', sa.DECIMAL(precision=18, scale=2), nullable=False, server_default=sa.text('0')),
        
        # Calculation parameters
        sa.Column('coupon_rate', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Period coupon rate used'),
        sa.Column('libor_rate', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Period LIBOR rate'),
        sa.Column('day_count_fraction', sa.DECIMAL(precision=8, scale=6), nullable=True, doc='Day count fraction for period'),
        sa.Column('prepayment_rate_period', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Period prepayment rate'),
        sa.Column('default_rate_period', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Period default rate'),
        sa.Column('severity_rate_period', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Period severity rate'),
        
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('cash_flow_id'),
        sa.ForeignKeyConstraint(['reinvest_id'], ['reinvestment_periods.reinvest_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('reinvest_id', 'payment_period', name='uq_reinvestment_cash_flows')
    )
    
    # Create indexes for efficient cash flow lookup
    op.create_index('ix_reinvestment_cash_flows_reinvest_period', 'reinvestment_cash_flows', ['reinvest_id', 'payment_period'])
    op.create_index('ix_reinvestment_cash_flows_payment_date', 'reinvestment_cash_flows', ['payment_date'])
    
    # 4. Reinvestment Scenarios (for stress testing and scenario analysis)
    op.create_table(
        'reinvestment_scenarios',
        sa.Column('scenario_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('base_reinvest_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=100), nullable=False),
        sa.Column('scenario_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Scenario adjustments
        sa.Column('spread_adjustment_bps', sa.Integer(), nullable=True, doc='Spread adjustment in basis points'),
        sa.Column('prepayment_multiplier', sa.DECIMAL(precision=4, scale=2), nullable=True, doc='Prepayment rate multiplier'),
        sa.Column('default_multiplier', sa.DECIMAL(precision=4, scale=2), nullable=True, doc='Default rate multiplier'),
        sa.Column('severity_adjustment', sa.DECIMAL(precision=4, scale=2), nullable=True, doc='Severity rate adjustment'),
        sa.Column('liquidation_price_override', sa.DECIMAL(precision=6, scale=4), nullable=True, doc='Override liquidation price'),
        
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('scenario_id'),
        sa.ForeignKeyConstraint(['base_reinvest_id'], ['reinvestment_periods.reinvest_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('base_reinvest_id', 'scenario_name', name='uq_reinvestment_scenarios')
    )
    
    # Create index for scenario lookup
    op.create_index('ix_reinvestment_scenarios_base_reinvest', 'reinvestment_scenarios', ['base_reinvest_id'])
    op.create_index('ix_reinvestment_scenarios_type', 'reinvestment_scenarios', ['scenario_type'])
    
    # Insert seed data for common reinvestment configurations
    op.execute(text("""
        INSERT INTO reinvestment_periods (deal_id, period_start, period_end, reinvest_period, maturity_months, months_between_payments, yield_curve_name)
        VALUES 
        ('DEMO_DEAL_001', '2025-01-01', '2027-01-01', 1, 60, 3, 'USD_SOFR'),
        ('DEMO_DEAL_002', '2025-02-01', '2027-02-01', 1, 48, 3, 'USD_LIBOR'),
        ('TEST_DEAL_001', '2025-01-10', '2026-01-10', 1, 36, 3, 'USD_TREASURY')
    """))
    
    # Insert corresponding reinvestment info
    op.execute(text("""
        INSERT INTO reinvestment_info (reinvest_id, reinvest_price, spread_bps, floor_rate, liquidation_price, lag_periods, 
                                     prepayment_rate_annual, default_rate_annual, severity_rate)
        SELECT 
            rp.reinvest_id,
            1.0000,  -- Par purchase price
            500,     -- 500 bps spread
            0.0000,  -- No floor
            0.7000,  -- 70% liquidation price
            2,       -- 2 period lag
            0.1500,  -- 15% annual prepayment
            0.0300,  -- 3% annual default
            0.4000   -- 40% severity
        FROM reinvestment_periods rp
        WHERE rp.deal_id IN ('DEMO_DEAL_001', 'DEMO_DEAL_002', 'TEST_DEAL_001')
    """))
    
    # Insert sample scenarios
    op.execute(text("""
        INSERT INTO reinvestment_scenarios (base_reinvest_id, scenario_name, scenario_type, description, 
                                          prepayment_multiplier, default_multiplier, severity_adjustment)
        SELECT 
            rp.reinvest_id,
            scenario_name,
            scenario_type,
            description,
            prepay_mult,
            default_mult,
            severity_adj
        FROM reinvestment_periods rp
        CROSS JOIN (
            SELECT 'BASE_CASE' as scenario_name, 'STRESS_TEST' as scenario_type, 'Base case assumptions' as description, 
                   1.00 as prepay_mult, 1.00 as default_mult, 0.00 as severity_adj UNION ALL
            SELECT 'SLOW_PREPAY', 'STRESS_TEST', 'Slower prepayment environment', 
                   0.50, 1.00, 0.00 UNION ALL
            SELECT 'HIGH_DEFAULT', 'STRESS_TEST', 'Higher default environment', 
                   1.00, 2.00, 0.10 UNION ALL  
            SELECT 'SEVERE_STRESS', 'STRESS_TEST', 'Severe stress scenario',
                   0.30, 3.00, 0.20
        ) scenarios
        WHERE rp.deal_id = 'TEST_DEAL_001'
    """))


def downgrade() -> None:
    """Drop reinvestment system tables"""
    op.drop_table('reinvestment_scenarios')
    op.drop_table('reinvestment_cash_flows')
    op.drop_table('reinvestment_info')
    op.drop_table('reinvestment_periods')