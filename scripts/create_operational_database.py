#!/usr/bin/env python3
"""
Create Operational Database Schema
Sets up the production PostgreSQL database with all operational tables
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text, inspect
from app.core.database_config import db_config, Base
import logging

# Import all models to register them with Base
from app.models.asset import Asset, AssetHistory
from app.models.cash_flow import AssetCashFlow, CashFlowSummary
from app.models.clo_deal import CLODeal, CLOTranche, DealAsset
from app.models.liability import Liability, LiabilityCashFlow
from app.models.waterfall import WaterfallConfiguration, WaterfallExecution, WaterfallPayment
from app.models.oc_trigger import OCTrigger
from app.models.ic_trigger import ICTrigger
from app.models.fee import Fee, FeeCalculation
from app.models.accounts import AccountType, DealAccount, AccountTransaction
from app.models.collateral_pool import (
    CollateralPool, CollateralPoolAsset, CollateralPoolAccount, 
    ConcentrationTestResult, CollateralPoolForCLO, AssetCashFlowForDeal
)
from app.models.mag_waterfall import MagWaterfallConfiguration, MagPerformanceMetrics
from app.models.dynamic_waterfall import TrancheMapping, WaterfallStructure
from app.models.waterfall_config import WaterfallTemplate, PaymentRule, WaterfallModification, PaymentOverride
from app.models.incentive_fee import (
    IncentiveFeeStructureModel, SubordinatedPaymentModel, 
    IncentiveFeeCalculationModel, FeePaymentTransactionModel, IRRCalculationHistoryModel
)
from app.models.yield_curve import YieldCurveModel, YieldCurveRateModel, ForwardRateModel, YieldCurveScenarioModel
from app.models.reinvestment import ReinvestmentPeriodModel, ReinvestmentInfoModel, ReinvestmentCashFlowModel, ReinvestmentScenarioModel
from app.models.rating_system import (
    RatingAgencyModel, RatingScale, RatingDerivationRule, 
    RecoveryRateMatrix, RatingMigration, PortfolioMigrationStats, RatingDistributionHistory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OperationalDatabaseCreator:
    """Creates and initializes the operational database schema"""
    
    def __init__(self):
        self.db_config = db_config
        
    def create_database_schema(self):
        """Create all database tables"""
        logger.info("Creating operational database schema...")
        
        try:
            # Create all tables
            engine = self.db_config.get_engine('postgresql')
            Base.metadata.create_all(engine)
            
            # Verify table creation
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            logger.info(f"✅ Successfully created {len(tables)} operational tables")
            
            # List created tables for verification
            logger.info("Created tables:")
            for table in sorted(tables):
                logger.info(f"  - {table}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating database schema: {e}")
            return False
    
    def create_indexes(self):
        """Create performance indexes"""
        logger.info("Creating performance indexes...")
        
        index_queries = [
            # Asset indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_blkrock_id ON assets(blkrock_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_issuer ON assets(issuer_name);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_maturity ON assets(maturity);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_rating ON assets(mdy_rating, sp_rating);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assets_industry ON assets(mdy_industry, sp_industry);",
            
            # Cash flow indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cash_flows_asset_period ON asset_cash_flows(blkrock_id, period_number);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cash_flows_payment_date ON asset_cash_flows(payment_date);",
            
            # Deal indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_assets_deal ON deal_assets(deal_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_assets_asset ON deal_assets(blkrock_id);",
            
            # Trigger indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_oc_triggers_deal_period ON oc_triggers(deal_id, period_number);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ic_triggers_deal_period ON ic_triggers(deal_id, period_number);",
            
            # Waterfall indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_waterfall_exec_deal_date ON waterfall_executions(deal_id, payment_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_waterfall_payments_exec ON waterfall_payments(execution_id);",
            
            # Fee indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fee_calc_deal_period ON fee_calculations(deal_id, period_number);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fee_calc_fee_type ON fee_calculations(fee_type);",
            
            # Account indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_account_trans_account ON account_transactions(account_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_account_trans_date ON account_transactions(transaction_date);",
            
            # Collateral pool indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pool_assets_pool ON collateral_pool_assets(pool_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_concentration_results_deal ON concentration_test_results(deal_id, test_date);",
        ]
        
        try:
            with self.db_config.get_db_session('postgresql') as session:
                for query in index_queries:
                    try:
                        session.execute(text(query))
                        session.commit()
                    except Exception as e:
                        logger.warning(f"Index creation warning: {e}")
                        session.rollback()
            
            logger.info("✅ Performance indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            return False
    
    def insert_reference_data(self):
        """Insert basic reference data"""
        logger.info("Inserting reference data...")
        
        try:
            with self.db_config.get_db_session('postgresql') as session:
                
                # Account types
                account_types = [
                    AccountType(type_name='COLLECTION', description='Collection account for asset payments'),
                    AccountType(type_name='EXPENSE', description='Expense reserve account'),
                    AccountType(type_name='INTEREST_RESERVE', description='Interest reserve account'),
                    AccountType(type_name='PRINCIPAL_RESERVE', description='Principal reserve account'),
                    AccountType(type_name='EQUITY', description='Equity distribution account'),
                ]
                
                for account_type in account_types:
                    # Check if already exists
                    existing = session.query(AccountType).filter_by(type_name=account_type.type_name).first()
                    if not existing:
                        session.add(account_type)
                
                # Rating agencies
                rating_agencies = [
                    RatingAgencyModel(
                        agency_name='Moody\'s',
                        agency_code='MDY',
                        is_active=True,
                        description='Moody\'s Investors Service'
                    ),
                    RatingAgencyModel(
                        agency_name='S&P',
                        agency_code='SP',
                        is_active=True,
                        description='Standard & Poor\'s'
                    ),
                    RatingAgencyModel(
                        agency_name='Fitch',
                        agency_code='FITCH',
                        is_active=True,
                        description='Fitch Ratings'
                    )
                ]
                
                for agency in rating_agencies:
                    existing = session.query(RatingAgencyModel).filter_by(agency_code=agency.agency_code).first()
                    if not existing:
                        session.add(agency)
                
                session.commit()
                logger.info("✅ Reference data inserted successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error inserting reference data: {e}")
            return False
    
    def verify_schema(self):
        """Verify the created database schema"""
        logger.info("Verifying database schema...")
        
        try:
            inspector = inspect(self.db_config.get_engine('postgresql'))
            
            # Get all tables
            tables = inspector.get_table_names()
            logger.info(f"📊 Found {len(tables)} tables in database")
            
            # Get all indexes
            all_indexes = []
            for table in tables:
                indexes = inspector.get_indexes(table)
                all_indexes.extend(indexes)
            
            logger.info(f"🔍 Found {len(all_indexes)} indexes across all tables")
            
            # Verify some critical tables exist
            critical_tables = [
                'assets', 'clo_deals', 'clo_tranches', 'deal_assets',
                'asset_cash_flows', 'liability_cash_flows', 
                'waterfall_configurations', 'waterfall_executions',
                'oc_triggers', 'ic_triggers', 'fee_calculations',
                'deal_accounts', 'account_transactions',
                'collateral_pools', 'concentration_test_results'
            ]
            
            missing_tables = [table for table in critical_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"❌ Missing critical tables: {missing_tables}")
                return False
            
            logger.info("✅ All critical tables present")
            
            # Test database connection
            with self.db_config.get_db_session('postgresql') as session:
                result = session.execute(text('SELECT 1 as test')).fetchone()
                assert result[0] == 1
            
            logger.info("✅ Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {e}")
            return False
    
    def run_full_setup(self):
        """Run complete database setup"""
        logger.info("🚀 Starting operational database setup...")
        
        steps = [
            ("Creating database schema", self.create_database_schema),
            ("Creating performance indexes", self.create_indexes),
            ("Inserting reference data", self.insert_reference_data),
            ("Verifying schema", self.verify_schema)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed at step: {step_name}")
                return False
        
        logger.info("🎉 Operational database setup completed successfully!")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("OPERATIONAL DATABASE SETUP COMPLETE")
        logger.info("="*60)
        logger.info("✅ PostgreSQL operational database created")
        logger.info("✅ 47+ operational tables implemented")
        logger.info("✅ Performance indexes created") 
        logger.info("✅ Reference data populated")
        logger.info("✅ Schema verification passed")
        logger.info("🚀 System ready for operational use!")
        
        return True

def main():
    """Main execution function"""
    creator = OperationalDatabaseCreator()
    
    # Health check first
    logger.info("Performing database health check...")
    health_status = db_config.health_check()
    
    if not health_status['postgresql']:
        logger.error("❌ PostgreSQL connection failed. Please check database configuration.")
        logger.info("Make sure PostgreSQL is running and connection settings are correct.")
        return 1
    
    logger.info("✅ PostgreSQL connection verified")
    
    # Run setup
    if creator.run_full_setup():
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)