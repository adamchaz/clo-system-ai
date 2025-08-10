"""Create yield curve system tables

Revision ID: 003_yield_curve_system
Revises: 002_rating_system_tables
Create Date: 2025-01-10 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '003_yield_curve_system'
down_revision = '002_rating_system_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create yield curve system tables"""
    
    # 1. Yield Curves master table
    op.create_table(
        'yield_curves',
        sa.Column('curve_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('curve_name', sa.String(length=100), nullable=False),
        sa.Column('curve_type', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('analysis_date', sa.Date(), nullable=False),
        sa.Column('base_date', sa.Date(), nullable=False),
        sa.Column('last_month', sa.Integer(), nullable=False),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('curve_id'),
        sa.UniqueConstraint('curve_name', 'analysis_date', name='uq_yield_curves_name_date')
    )
    
    # Create index for efficient curve lookup
    op.create_index('ix_yield_curves_name_date', 'yield_curves', ['curve_name', 'analysis_date'])
    op.create_index('ix_yield_curves_type_currency', 'yield_curves', ['curve_type', 'currency'])
    
    # 2. Yield Curve Rates (spot rates)
    op.create_table(
        'yield_curve_rates',
        sa.Column('rate_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('curve_id', sa.Integer(), nullable=False),
        sa.Column('maturity_month', sa.Integer(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=True),
        sa.Column('spot_rate', sa.DECIMAL(precision=8, scale=6), nullable=False),
        sa.Column('is_interpolated', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('rate_id'),
        sa.ForeignKeyConstraint(['curve_id'], ['yield_curves.curve_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('curve_id', 'maturity_month', name='uq_yield_curve_rates')
    )
    
    # Create indexes for efficient rate lookup
    op.create_index('ix_yield_curve_rates_curve_month', 'yield_curve_rates', ['curve_id', 'maturity_month'])
    op.create_index('ix_yield_curve_rates_maturity_date', 'yield_curve_rates', ['maturity_date'])
    
    # 3. Forward Rates (calculated from spot rates)
    op.create_table(
        'forward_rates',
        sa.Column('forward_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('curve_id', sa.Integer(), nullable=False),
        sa.Column('forward_date', sa.Date(), nullable=False),
        sa.Column('period_start_date', sa.Date(), nullable=False),
        sa.Column('period_months', sa.Integer(), nullable=False),
        sa.Column('forward_rate', sa.DECIMAL(precision=8, scale=6), nullable=False),
        sa.Column('calculation_method', sa.String(length=50), nullable=False, server_default=sa.text("'VBA_EXACT'")),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('forward_id'),
        sa.ForeignKeyConstraint(['curve_id'], ['yield_curves.curve_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('curve_id', 'forward_date', name='uq_forward_rates')
    )
    
    # Create indexes for efficient forward rate lookup
    op.create_index('ix_forward_rates_curve_date', 'forward_rates', ['curve_id', 'forward_date'])
    op.create_index('ix_forward_rates_period_dates', 'forward_rates', ['period_start_date', 'forward_date'])
    
    # 4. Yield Curve Scenarios (for stress testing and scenario analysis)
    op.create_table(
        'yield_curve_scenarios',
        sa.Column('scenario_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('base_curve_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=100), nullable=False),
        sa.Column('scenario_type', sa.String(length=50), nullable=False),
        sa.Column('shift_type', sa.String(length=20), nullable=False),
        sa.Column('parallel_shift_bps', sa.Integer(), nullable=True),
        sa.Column('steepening_bps', sa.Integer(), nullable=True),
        sa.Column('twist_point_months', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('scenario_id'),
        sa.ForeignKeyConstraint(['base_curve_id'], ['yield_curves.curve_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('base_curve_id', 'scenario_name', name='uq_yield_curve_scenarios')
    )
    
    # Create index for scenario lookup
    op.create_index('ix_yield_curve_scenarios_base_curve', 'yield_curve_scenarios', ['base_curve_id'])
    op.create_index('ix_yield_curve_scenarios_type', 'yield_curve_scenarios', ['scenario_type'])
    
    # Insert seed data for common yield curve types
    op.execute(text("""
        INSERT INTO yield_curves (curve_name, curve_type, currency, analysis_date, base_date, last_month, description)
        VALUES 
        ('USD_TREASURY', 'GOVERNMENT', 'USD', '2025-01-10', '2025-01-01', 360, 'US Treasury yield curve'),
        ('USD_LIBOR', 'INTERBANK', 'USD', '2025-01-10', '2025-01-01', 360, 'USD LIBOR curve (historical)'),
        ('USD_SOFR', 'INTERBANK', 'USD', '2025-01-10', '2025-01-01', 360, 'USD SOFR curve'),
        ('USD_CREDIT_AAA', 'CREDIT', 'USD', '2025-01-10', '2025-01-01', 360, 'AAA Credit spread curve'),
        ('USD_CREDIT_BBB', 'CREDIT', 'USD', '2025-01-10', '2025-01-01', 360, 'BBB Credit spread curve')
    """))
    
    # Insert sample spot rates for USD Treasury curve
    op.execute(text("""
        INSERT INTO yield_curve_rates (curve_id, maturity_month, spot_rate, is_interpolated, source)
        SELECT 
            c.curve_id,
            maturity_month,
            spot_rate,
            FALSE,
            'SEED_DATA'
        FROM yield_curves c
        CROSS JOIN (
            SELECT 1 as maturity_month, 0.0450 as spot_rate UNION ALL
            SELECT 3, 0.0465 UNION ALL
            SELECT 6, 0.0485 UNION ALL
            SELECT 12, 0.0520 UNION ALL
            SELECT 24, 0.0565 UNION ALL
            SELECT 36, 0.0595 UNION ALL
            SELECT 60, 0.0625 UNION ALL
            SELECT 84, 0.0645 UNION ALL
            SELECT 120, 0.0675 UNION ALL
            SELECT 240, 0.0705 UNION ALL
            SELECT 360, 0.0715
        ) rates
        WHERE c.curve_name = 'USD_TREASURY'
    """))


def downgrade() -> None:
    """Drop yield curve system tables"""
    op.drop_table('yield_curve_scenarios')
    op.drop_table('forward_rates')
    op.drop_table('yield_curve_rates')
    op.drop_table('yield_curves')