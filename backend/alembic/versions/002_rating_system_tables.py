"""Rating system infrastructure

Revision ID: 002_rating_system  
Revises: 001_account_management
Create Date: 2025-01-10

Implements VBA RatingDerivations.cls, Ratings.cls, RatingMigrationItem.cls, 
and RatingMigrationOutput.cls functionality with database persistence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_rating_system'
down_revision = '001_account_management'
branch_labels = None
depends_on = None

def upgrade():
    """Create rating system tables"""
    
    # Create rating_agencies table
    op.create_table('rating_agencies',
        sa.Column('agency_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agency_name', sa.String(length=20), nullable=False),
        sa.Column('agency_full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('agency_id'),
        sa.UniqueConstraint('agency_name')
    )
    
    # Create rating_scales table
    op.create_table('rating_scales',
        sa.Column('scale_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('rating_symbol', sa.String(length=10), nullable=False),
        sa.Column('numeric_rank', sa.Integer(), nullable=False),
        sa.Column('rating_category', sa.String(length=20), nullable=True),
        sa.Column('rating_grade', sa.String(length=5), nullable=True),
        sa.Column('is_investment_grade', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_watch', sa.Boolean(), nullable=True, default=False),
        sa.Column('outlook', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agency_id'], ['rating_agencies.agency_id'], ),
        sa.PrimaryKeyConstraint('scale_id'),
        sa.UniqueConstraint('agency_id', 'rating_symbol', name='unique_agency_rating')
    )
    
    # Create rating_derivation_rules table
    op.create_table('rating_derivation_rules',
        sa.Column('rule_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_agency_id', sa.Integer(), nullable=False),
        sa.Column('target_agency_id', sa.Integer(), nullable=False),
        sa.Column('source_rating', sa.String(length=10), nullable=False),
        sa.Column('target_rating', sa.String(length=10), nullable=False),
        sa.Column('adjustment_notches', sa.Integer(), nullable=True, default=0),
        sa.Column('bond_loan_type', sa.String(length=10), nullable=True),
        sa.Column('seniority_level', sa.String(length=30), nullable=True),
        sa.Column('is_structured_finance', sa.Boolean(), nullable=True, default=False),
        sa.Column('rating_threshold', sa.Integer(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_agency_id'], ['rating_agencies.agency_id'], ),
        sa.ForeignKeyConstraint(['target_agency_id'], ['rating_agencies.agency_id'], ),
        sa.PrimaryKeyConstraint('rule_id')
    )
    
    # Create recovery_rate_matrices table
    op.create_table('recovery_rate_matrices',
        sa.Column('matrix_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_category', sa.String(length=50), nullable=False),
        sa.Column('rating_diff_min', sa.Integer(), nullable=False),
        sa.Column('rating_diff_max', sa.Integer(), nullable=False),
        sa.Column('recovery_rate', sa.DECIMAL(precision=6, scale=4), nullable=False),
        sa.Column('confidence_interval', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('data_vintage', sa.Date(), nullable=True),
        sa.Column('is_dip', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('matrix_id')
    )
    
    # Create rating_migrations table
    op.create_table('rating_migrations',
        sa.Column('migration_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.String(length=50), nullable=False),
        sa.Column('migration_date', sa.Date(), nullable=False),
        sa.Column('previous_sp_rating', sa.String(length=10), nullable=True),
        sa.Column('previous_mdy_rating', sa.String(length=10), nullable=True),
        sa.Column('previous_fitch_rating', sa.String(length=10), nullable=True),
        sa.Column('new_sp_rating', sa.String(length=10), nullable=True),
        sa.Column('new_mdy_rating', sa.String(length=10), nullable=True),
        sa.Column('new_fitch_rating', sa.String(length=10), nullable=True),
        sa.Column('notch_change', sa.Integer(), nullable=True, default=0),
        sa.Column('migration_type', sa.String(length=20), nullable=True),
        sa.Column('is_default_event', sa.Boolean(), nullable=True, default=False),
        sa.Column('recovery_amount', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('portfolio_weight_at_migration', sa.DECIMAL(precision=8, scale=6), nullable=True),
        sa.Column('par_amount_at_migration', sa.DECIMAL(precision=18, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.blkrock_id'], ),
        sa.PrimaryKeyConstraint('migration_id')
    )
    
    # Create portfolio_migration_stats table
    op.create_table('portfolio_migration_stats',
        sa.Column('stat_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.String(length=50), nullable=False),
        sa.Column('calculation_date', sa.Date(), nullable=False),
        sa.Column('period_start_date', sa.Date(), nullable=True),
        sa.Column('period_end_date', sa.Date(), nullable=True),
        sa.Column('simulation_number', sa.Integer(), nullable=True, default=1),
        sa.Column('total_upgrades', sa.Integer(), nullable=True, default=0),
        sa.Column('total_downgrades', sa.Integer(), nullable=True, default=0),
        sa.Column('total_defaults', sa.Integer(), nullable=True, default=0),
        sa.Column('period_defaults', sa.Integer(), nullable=True, default=0),
        sa.Column('upgrade_dollar_volume', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('downgrade_dollar_volume', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('default_dollar_volume', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('period_default_dollar_volume', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('performing_balance', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('cumulative_default_rate', sa.DECIMAL(precision=8, scale=6), nullable=True, default=0.000000),
        sa.Column('weighted_average_rating_change', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('portfolio_quality_trend', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['clo_deals.deal_id'], ),
        sa.PrimaryKeyConstraint('stat_id')
    )
    
    # Create rating_distribution_history table for detailed tracking
    op.create_table('rating_distribution_history',
        sa.Column('distribution_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_id', sa.String(length=50), nullable=False),
        sa.Column('calculation_date', sa.Date(), nullable=False),
        sa.Column('simulation_number', sa.Integer(), nullable=False),
        sa.Column('rating_bucket', sa.String(length=10), nullable=False),
        sa.Column('asset_count', sa.Integer(), nullable=True, default=0),
        sa.Column('balance_amount', sa.DECIMAL(precision=18, scale=2), nullable=True, default=0.00),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['clo_deals.deal_id'], ),
        sa.PrimaryKeyConstraint('distribution_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_rating_scales_rank', 'rating_scales', ['numeric_rank'])
    op.create_index('idx_rating_derivation_source', 'rating_derivation_rules', ['source_agency_id', 'source_rating'])
    op.create_index('idx_rating_derivation_target', 'rating_derivation_rules', ['target_agency_id', 'target_rating'])
    op.create_index('idx_recovery_rates_category', 'recovery_rate_matrices', ['asset_category', 'rating_diff_min', 'rating_diff_max'])
    op.create_index('idx_rating_migrations_asset_date', 'rating_migrations', ['asset_id', 'migration_date'])
    op.create_index('idx_portfolio_stats_deal_date', 'portfolio_migration_stats', ['deal_id', 'calculation_date'])
    op.create_index('idx_rating_distribution_deal_sim', 'rating_distribution_history', ['deal_id', 'simulation_number', 'calculation_date'])
    
    # Insert seed data for rating agencies
    op.execute("""
        INSERT INTO rating_agencies (agency_name, agency_full_name) VALUES 
        ('MOODYS', 'Moody''s Investors Service'),
        ('SP', 'S&P Global Ratings'),
        ('FITCH', 'Fitch Ratings');
    """)
    
    # Insert seed data for standardized rating scales (all 21 ratings from VBA)
    op.execute("""
        INSERT INTO rating_scales (agency_id, rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade) 
        SELECT 
            (SELECT agency_id FROM rating_agencies WHERE agency_name = 'SP') as agency_id,
            rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade
        FROM (VALUES
            ('AAA', 1, 'INVESTMENT', 'AAA', true),
            ('AA+', 2, 'INVESTMENT', 'AA', true),
            ('AA', 3, 'INVESTMENT', 'AA', true),
            ('AA-', 4, 'INVESTMENT', 'AA', true),
            ('A+', 5, 'INVESTMENT', 'A', true),
            ('A', 6, 'INVESTMENT', 'A', true),
            ('A-', 7, 'INVESTMENT', 'A', true),
            ('BBB+', 8, 'INVESTMENT', 'BBB', true),
            ('BBB', 9, 'INVESTMENT', 'BBB', true),
            ('BBB-', 10, 'INVESTMENT', 'BBB', true),
            ('BB+', 11, 'SPECULATIVE', 'BB', false),
            ('BB', 12, 'SPECULATIVE', 'BB', false),
            ('BB-', 13, 'SPECULATIVE', 'BB', false),
            ('B+', 14, 'SPECULATIVE', 'B', false),
            ('B', 15, 'SPECULATIVE', 'B', false),
            ('B-', 16, 'SPECULATIVE', 'B', false),
            ('CCC+', 17, 'SPECULATIVE', 'CCC', false),
            ('CCC', 18, 'SPECULATIVE', 'CCC', false),
            ('CCC-', 19, 'SPECULATIVE', 'CCC', false),
            ('CC', 20, 'DEFAULT', 'CC', false),
            ('C', 21, 'DEFAULT', 'C', false)
        ) as ratings(rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade);
    """)
    
    # Insert Moody's ratings
    op.execute("""
        INSERT INTO rating_scales (agency_id, rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade) 
        SELECT 
            (SELECT agency_id FROM rating_agencies WHERE agency_name = 'MOODYS') as agency_id,
            rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade
        FROM (VALUES
            ('Aaa', 1, 'INVESTMENT', 'AAA', true),
            ('Aa1', 2, 'INVESTMENT', 'AA', true),
            ('Aa2', 3, 'INVESTMENT', 'AA', true),
            ('Aa3', 4, 'INVESTMENT', 'AA', true),
            ('A1', 5, 'INVESTMENT', 'A', true),
            ('A2', 6, 'INVESTMENT', 'A', true),
            ('A3', 7, 'INVESTMENT', 'A', true),
            ('Baa1', 8, 'INVESTMENT', 'BBB', true),
            ('Baa2', 9, 'INVESTMENT', 'BBB', true),
            ('Baa3', 10, 'INVESTMENT', 'BBB', true),
            ('Ba1', 11, 'SPECULATIVE', 'BB', false),
            ('Ba2', 12, 'SPECULATIVE', 'BB', false),
            ('Ba3', 13, 'SPECULATIVE', 'BB', false),
            ('B1', 14, 'SPECULATIVE', 'B', false),
            ('B2', 15, 'SPECULATIVE', 'B', false),
            ('B3', 16, 'SPECULATIVE', 'B', false),
            ('Caa1', 17, 'SPECULATIVE', 'CCC', false),
            ('Caa2', 18, 'SPECULATIVE', 'CCC', false),
            ('Caa3', 19, 'SPECULATIVE', 'CCC', false),
            ('Ca', 20, 'DEFAULT', 'CC', false),
            ('C', 21, 'DEFAULT', 'C', false)
        ) as ratings(rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade);
    """)
    
    # Insert Fitch ratings (same as S&P)
    op.execute("""
        INSERT INTO rating_scales (agency_id, rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade) 
        SELECT 
            (SELECT agency_id FROM rating_agencies WHERE agency_name = 'FITCH') as agency_id,
            rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade
        FROM (VALUES
            ('AAA', 1, 'INVESTMENT', 'AAA', true),
            ('AA+', 2, 'INVESTMENT', 'AA', true),
            ('AA', 3, 'INVESTMENT', 'AA', true),
            ('AA-', 4, 'INVESTMENT', 'AA', true),
            ('A+', 5, 'INVESTMENT', 'A', true),
            ('A', 6, 'INVESTMENT', 'A', true),
            ('A-', 7, 'INVESTMENT', 'A', true),
            ('BBB+', 8, 'INVESTMENT', 'BBB', true),
            ('BBB', 9, 'INVESTMENT', 'BBB', true),
            ('BBB-', 10, 'INVESTMENT', 'BBB', true),
            ('BB+', 11, 'SPECULATIVE', 'BB', false),
            ('BB', 12, 'SPECULATIVE', 'BB', false),
            ('BB-', 13, 'SPECULATIVE', 'BB', false),
            ('B+', 14, 'SPECULATIVE', 'B', false),
            ('B', 15, 'SPECULATIVE', 'B', false),
            ('B-', 16, 'SPECULATIVE', 'B', false),
            ('CCC+', 17, 'SPECULATIVE', 'CCC', false),
            ('CCC', 18, 'SPECULATIVE', 'CCC', false),
            ('CCC-', 19, 'SPECULATIVE', 'CCC', false),
            ('CC', 20, 'DEFAULT', 'CC', false),
            ('C', 21, 'DEFAULT', 'C', false)
        ) as ratings(rating_symbol, numeric_rank, rating_category, rating_grade, is_investment_grade);
    """)
    
    # Insert seed data for recovery rate matrices (Moody's methodology)
    op.execute("""
        INSERT INTO recovery_rate_matrices (asset_category, rating_diff_min, rating_diff_max, recovery_rate, is_dip) VALUES
        -- DIP cases
        ('ALL_CATEGORIES', -999, 999, 0.5000, true),
        
        -- Senior Secured Loans
        ('MOODY'S SENIOR SECURED LOAN', 2, 999, 0.6000, false),
        ('MOODY'S SENIOR SECURED LOAN', 1, 1, 0.5000, false),
        ('MOODY'S SENIOR SECURED LOAN', 0, 0, 0.4500, false),
        ('MOODY'S SENIOR SECURED LOAN', -1, -1, 0.4000, false),
        ('MOODY'S SENIOR SECURED LOAN', -2, -2, 0.3000, false),
        ('MOODY'S SENIOR SECURED LOAN', -999, -3, 0.2000, false),
        
        -- Non-Senior Secured Loans  
        ('MOODY'S NON-SENIOR SECURED LOAN', 2, 999, 0.5500, false),
        ('MOODY'S NON-SENIOR SECURED LOAN', 1, 1, 0.4500, false),
        ('MOODY'S NON-SENIOR SECURED LOAN', 0, 0, 0.3500, false),
        ('MOODY'S NON-SENIOR SECURED LOAN', -1, -1, 0.2500, false),
        ('MOODY'S NON-SENIOR SECURED LOAN', -2, -2, 0.1500, false),
        ('MOODY'S NON-SENIOR SECURED LOAN', -999, -3, 0.0500, false),
        
        -- Other categories (bonds, etc)
        ('OTHER', 2, 999, 0.4500, false),
        ('OTHER', 1, 1, 0.3500, false),
        ('OTHER', 0, 0, 0.3000, false),
        ('OTHER', -1, -1, 0.2500, false),
        ('OTHER', -2, -2, 0.1500, false),
        ('OTHER', -999, -3, 0.0500, false);
    """)


def downgrade():
    """Drop rating system tables"""
    
    # Drop indexes
    op.drop_index('idx_rating_distribution_deal_sim')
    op.drop_index('idx_portfolio_stats_deal_date')
    op.drop_index('idx_rating_migrations_asset_date')
    op.drop_index('idx_recovery_rates_category')
    op.drop_index('idx_rating_derivation_target')
    op.drop_index('idx_rating_derivation_source')
    op.drop_index('idx_rating_scales_rank')
    
    # Drop tables in reverse order
    op.drop_table('rating_distribution_history')
    op.drop_table('portfolio_migration_stats')
    op.drop_table('rating_migrations')
    op.drop_table('recovery_rate_matrices')
    op.drop_table('rating_derivation_rules')
    op.drop_table('rating_scales')
    op.drop_table('rating_agencies')