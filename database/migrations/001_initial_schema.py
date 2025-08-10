"""
Initial database migration - CLO Portfolio Management System
Creates all tables, indexes, triggers, and views from schema.sql
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # =============================================================================
    # CORE ASSET TABLES
    # =============================================================================
    
    # Main assets table
    op.create_table(
        'assets',
        sa.Column('blkrock_id', sa.String(50), primary_key=True),
        sa.Column('issue_name', sa.String(255), nullable=False),
        sa.Column('issuer_name', sa.String(255), nullable=False),
        sa.Column('issuer_id', sa.String(50)),
        sa.Column('tranche', sa.String(10)),
        
        # Asset Classification
        sa.Column('bond_loan', sa.String(10)),
        sa.Column('par_amount', sa.Numeric(18,2), nullable=False),
        sa.Column('market_value', sa.Numeric(8,4)),
        sa.Column('currency', sa.String(3), default='USD'),
        
        # Dates
        sa.Column('maturity', sa.Date, nullable=False),
        sa.Column('dated_date', sa.Date),
        sa.Column('issue_date', sa.Date),
        sa.Column('first_payment_date', sa.Date),
        sa.Column('date_of_default', sa.Date),
        
        # Interest Rate Properties
        sa.Column('coupon', sa.Numeric(10,6)),
        sa.Column('coupon_type', sa.String(10)),
        sa.Column('index_name', sa.String(20)),
        sa.Column('cpn_spread', sa.Numeric(10,6)),
        sa.Column('libor_floor', sa.Numeric(10,6)),
        sa.Column('index_cap', sa.Numeric(10,6)),
        sa.Column('payment_freq', sa.Integer),
        
        # Cash Flow Properties
        sa.Column('amortization_type', sa.String(20)),
        sa.Column('day_count', sa.String(20)),
        sa.Column('business_day_conv', sa.String(30)),
        sa.Column('payment_eom', sa.Boolean, default=False),
        sa.Column('amount_issued', sa.Numeric(18,2)),
        
        # PIK Properties
        sa.Column('piking', sa.Boolean, default=False),
        sa.Column('pik_amount', sa.Numeric(18,2)),
        sa.Column('unfunded_amount', sa.Numeric(18,2)),
        
        # Credit Ratings
        sa.Column('mdy_rating', sa.String(10)),
        sa.Column('mdy_dp_rating', sa.String(10)),
        sa.Column('mdy_dp_rating_warf', sa.String(10)),
        sa.Column('mdy_recovery_rate', sa.Numeric(5,4)),
        sa.Column('sp_rating', sa.String(10)),
        
        # Additional Ratings
        sa.Column('mdy_facility_rating', sa.String(10)),
        sa.Column('mdy_facility_outlook', sa.String(10)),
        sa.Column('mdy_issuer_rating', sa.String(10)),
        sa.Column('mdy_issuer_outlook', sa.String(10)),
        sa.Column('mdy_snr_sec_rating', sa.String(10)),
        sa.Column('mdy_snr_unsec_rating', sa.String(10)),
        sa.Column('mdy_sub_rating', sa.String(10)),
        sa.Column('mdy_credit_est_rating', sa.String(10)),
        sa.Column('mdy_credit_est_date', sa.Date),
        
        sa.Column('sandp_facility_rating', sa.String(10)),
        sa.Column('sandp_issuer_rating', sa.String(10)),
        sa.Column('sandp_snr_sec_rating', sa.String(10)),
        sa.Column('sandp_subordinate', sa.String(10)),
        sa.Column('sandp_rec_rating', sa.String(10)),
        
        # Industry Classifications
        sa.Column('mdy_industry', sa.String(100)),
        sa.Column('sp_industry', sa.String(100)),
        sa.Column('country', sa.String(50)),
        sa.Column('seniority', sa.String(20)),
        sa.Column('mdy_asset_category', sa.String(50)),
        sa.Column('sp_priority_category', sa.String(50)),
        
        # Financial Properties
        sa.Column('commit_fee', sa.Numeric(10,6)),
        sa.Column('facility_size', sa.Numeric(18,2)),
        sa.Column('wal', sa.Numeric(8,4)),
        
        # Asset Flags (JSON)
        sa.Column('flags', postgresql.JSONB),
        
        # Analyst Information
        sa.Column('analyst_opinion', sa.Text),
        
        # Audit Fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Asset history table
    op.create_table(
        'asset_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('blkrock_id', sa.String(50), sa.ForeignKey('assets.blkrock_id', ondelete='CASCADE'), nullable=False),
        sa.Column('history_date', sa.Date, nullable=False),
        sa.Column('property_name', sa.String(50), nullable=False),
        sa.Column('property_value', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Asset cash flows table
    op.create_table(
        'asset_cash_flows',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('blkrock_id', sa.String(50), sa.ForeignKey('assets.blkrock_id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_number', sa.Integer, nullable=False),
        
        # Dates
        sa.Column('payment_date', sa.Date, nullable=False),
        sa.Column('accrual_start_date', sa.Date, nullable=False),
        sa.Column('accrual_end_date', sa.Date, nullable=False),
        
        # Balances
        sa.Column('beginning_balance', sa.Numeric(18,2), nullable=False, default=0),
        sa.Column('ending_balance', sa.Numeric(18,2), nullable=False, default=0),
        sa.Column('default_balance', sa.Numeric(18,2), default=0),
        sa.Column('mv_default_balance', sa.Numeric(18,2), default=0),
        
        # Cash Flows
        sa.Column('interest_payment', sa.Numeric(18,2), default=0),
        sa.Column('scheduled_principal', sa.Numeric(18,2), default=0),
        sa.Column('unscheduled_principal', sa.Numeric(18,2), default=0),
        sa.Column('default_amount', sa.Numeric(18,2), default=0),
        sa.Column('mv_default_amount', sa.Numeric(18,2), default=0),
        sa.Column('recoveries', sa.Numeric(18,2), default=0),
        sa.Column('net_loss', sa.Numeric(18,2), default=0),
        
        # Purchases/Sales
        sa.Column('purchases', sa.Numeric(18,2), default=0),
        sa.Column('sales', sa.Numeric(18,2), default=0),
        
        # Total
        sa.Column('total_cash_flow', sa.Numeric(18,2), default=0),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # =============================================================================
    # CLO STRUCTURE TABLES
    # =============================================================================
    
    # CLO deals
    op.create_table(
        'clo_deals',
        sa.Column('deal_id', sa.String(50), primary_key=True),
        sa.Column('deal_name', sa.String(255), nullable=False),
        sa.Column('manager_name', sa.String(100)),
        sa.Column('trustee_name', sa.String(100)),
        
        # Key Dates
        sa.Column('pricing_date', sa.Date),
        sa.Column('closing_date', sa.Date),
        sa.Column('effective_date', sa.Date),
        sa.Column('first_payment_date', sa.Date),
        sa.Column('maturity_date', sa.Date),
        sa.Column('reinvestment_end_date', sa.Date),
        sa.Column('no_call_date', sa.Date),
        
        # Deal Parameters
        sa.Column('target_par_amount', sa.Numeric(18,2)),
        sa.Column('ramp_up_period', sa.Integer),
        sa.Column('payment_frequency', sa.Integer),
        
        # Status
        sa.Column('deal_status', sa.String(20)),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # CLO tranches
    op.create_table(
        'clo_tranches',
        sa.Column('tranche_id', sa.String(50), primary_key=True),
        sa.Column('deal_id', sa.String(50), sa.ForeignKey('clo_deals.deal_id'), nullable=False),
        sa.Column('tranche_name', sa.String(50), nullable=False),
        
        # Tranche Properties
        sa.Column('initial_balance', sa.Numeric(18,2)),
        sa.Column('current_balance', sa.Numeric(18,2)),
        sa.Column('coupon_rate', sa.Numeric(10,6)),
        sa.Column('coupon_type', sa.String(10)),
        sa.Column('index_name', sa.String(20)),
        sa.Column('margin', sa.Numeric(10,6)),
        
        # Rating and Seniority
        sa.Column('mdy_rating', sa.String(10)),
        sa.Column('sp_rating', sa.String(10)),
        sa.Column('seniority_level', sa.Integer),
        
        # Payment Terms
        sa.Column('payment_rank', sa.Integer),
        sa.Column('interest_deferrable', sa.Boolean, default=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Deal assets mapping
    op.create_table(
        'deal_assets',
        sa.Column('deal_id', sa.String(50), sa.ForeignKey('clo_deals.deal_id'), nullable=False),
        sa.Column('blkrock_id', sa.String(50), sa.ForeignKey('assets.blkrock_id'), nullable=False),
        
        # Position Details
        sa.Column('par_amount', sa.Numeric(18,2), nullable=False),
        sa.Column('purchase_price', sa.Numeric(8,6)),
        sa.Column('purchase_date', sa.Date),
        sa.Column('sale_date', sa.Date),
        sa.Column('sale_price', sa.Numeric(8,6)),
        
        # Status
        sa.Column('position_status', sa.String(20), default='ACTIVE'),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('deal_id', 'blkrock_id')
    )
    
    # =============================================================================
    # COMPLIANCE AND TESTING
    # =============================================================================
    
    # Compliance tests
    op.create_table(
        'compliance_tests',
        sa.Column('test_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('test_name', sa.String(100), nullable=False, unique=True),
        sa.Column('test_category', sa.String(50)),
        
        # Test Configuration
        sa.Column('test_formula', sa.Text),
        sa.Column('threshold_value', sa.Numeric(10,6)),
        sa.Column('threshold_type', sa.String(20)),
        
        # Test Metadata
        sa.Column('test_description', sa.Text),
        sa.Column('regulatory_source', sa.String(100)),
        
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Compliance test results
    op.create_table(
        'compliance_test_results',
        sa.Column('result_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('deal_id', sa.String(50), sa.ForeignKey('clo_deals.deal_id'), nullable=False),
        sa.Column('test_id', sa.Integer, sa.ForeignKey('compliance_tests.test_id'), nullable=False),
        sa.Column('test_date', sa.Date, nullable=False),
        
        # Test Results
        sa.Column('calculated_value', sa.Numeric(18,6)),
        sa.Column('threshold_value', sa.Numeric(18,6)),
        sa.Column('pass_fail', sa.Boolean),
        
        # Supporting Data
        sa.Column('numerator', sa.Numeric(18,6)),
        sa.Column('denominator', sa.Numeric(18,6)),
        sa.Column('test_comments', sa.Text),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # =============================================================================
    # REFERENCE DATA
    # =============================================================================
    
    # Rating scales
    op.create_table(
        'rating_scales',
        sa.Column('rating_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('agency', sa.String(20), nullable=False),
        sa.Column('rating_symbol', sa.String(10), nullable=False),
        sa.Column('rating_numeric', sa.Integer, nullable=False),
        sa.Column('warf_factor', sa.Integer)
    )
    
    # Holidays
    op.create_table(
        'holidays',
        sa.Column('holiday_date', sa.Date, primary_key=True),
        sa.Column('holiday_name', sa.String(100)),
        sa.Column('country_code', sa.String(3), default='US')
    )
    
    # =============================================================================
    # INDEXES
    # =============================================================================
    
    # Asset indexes
    op.create_index('idx_assets_issuer', 'assets', ['issuer_name'])
    op.create_index('idx_assets_maturity', 'assets', ['maturity'])
    op.create_index('idx_assets_ratings', 'assets', ['mdy_rating', 'sp_rating'])
    op.create_index('idx_assets_industry', 'assets', ['mdy_industry', 'sp_industry'])
    op.create_index('idx_assets_country', 'assets', ['country'])
    op.create_index('idx_assets_flags', 'assets', ['flags'], postgresql_using='gin')
    
    # Cash flow indexes
    op.create_index('idx_cash_flows_payment_date', 'asset_cash_flows', ['payment_date'])
    op.create_index('idx_cash_flows_asset_period', 'asset_cash_flows', ['blkrock_id', 'period_number'])
    
    # History indexes
    op.create_index('idx_asset_history_date', 'asset_history', ['blkrock_id', 'history_date'])
    op.create_index('idx_asset_history_property', 'asset_history', ['property_name', 'history_date'])
    
    # Deal indexes
    op.create_index('idx_deal_assets_deal', 'deal_assets', ['deal_id'])
    op.create_index('idx_deal_assets_status', 'deal_assets', ['position_status'])
    
    # Compliance indexes
    op.create_index('idx_compliance_results_deal_date', 'compliance_test_results', ['deal_id', 'test_date'])
    op.create_index('idx_compliance_results_pass_fail', 'compliance_test_results', ['pass_fail', 'test_date'])
    
    # Unique constraints
    op.create_unique_constraint('uq_asset_cash_flows_asset_period', 'asset_cash_flows', ['blkrock_id', 'period_number'])
    op.create_unique_constraint('uq_compliance_results', 'compliance_test_results', ['deal_id', 'test_id', 'test_date'])
    op.create_unique_constraint('uq_rating_scales', 'rating_scales', ['agency', 'rating_symbol'])


def downgrade() -> None:
    """Drop all tables and indexes"""
    
    # Drop tables in reverse dependency order
    op.drop_table('compliance_test_results')
    op.drop_table('compliance_tests')
    op.drop_table('deal_assets')
    op.drop_table('clo_tranches')
    op.drop_table('clo_deals')
    op.drop_table('asset_cash_flows')
    op.drop_table('asset_history')
    op.drop_table('rating_scales')
    op.drop_table('holidays')
    op.drop_table('assets')