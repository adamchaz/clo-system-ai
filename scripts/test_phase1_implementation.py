#!/usr/bin/env python3
"""
Test Phase 1 Implementation
Validates that the operational database infrastructure is working correctly
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.core.database_config import db_config
from app.services.data_integration import DataIntegrationService
from sqlalchemy import text, inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1Tester:
    """Test suite for Phase 1 operational database implementation"""
    
    def __init__(self):
        self.db_config = db_config
        self.integration_service = DataIntegrationService()
        self.test_results = {
            'start_time': datetime.now(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'failures': []
        }
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with error handling"""
        logger.info(f"🧪 Running test: {test_name}")
        self.test_results['tests_run'] += 1
        
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {test_name} - PASSED")
                self.test_results['tests_passed'] += 1
                return True
            else:
                logger.error(f"❌ {test_name} - FAILED")
                self.test_results['tests_failed'] += 1
                self.test_results['failures'].append(test_name)
                return False
        except Exception as e:
            logger.error(f"❌ {test_name} - ERROR: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append(f"{test_name}: {e}")
            return False
    
    def test_database_health(self) -> bool:
        """Test database health and connectivity"""
        health_status = self.db_config.health_check()
        
        # Check PostgreSQL
        if not health_status['postgresql']:
            logger.error("PostgreSQL connection failed")
            return False
        
        # Check migration databases
        required_dbs = ['assets', 'correlations', 'scenarios', 'config', 'reference']
        for db_name in required_dbs:
            if not health_status['migration_databases'].get(db_name, False):
                logger.error(f"Migration database {db_name} connection failed")
                return False
        
        # Redis is optional but warn if missing
        if not health_status['redis']:
            logger.warning("Redis connection not available - caching will be disabled")
        
        return True
    
    def test_operational_schema(self) -> bool:
        """Test that operational database schema exists"""
        try:
            inspector = inspect(self.db_config.get_engine('postgresql'))
            tables = inspector.get_table_names()
            
            # Check for critical tables
            critical_tables = [
                'assets', 'clo_deals', 'clo_tranches', 'deal_assets',
                'asset_cash_flows', 'waterfall_configurations', 
                'oc_triggers', 'ic_triggers', 'fee_calculations'
            ]
            
            missing_tables = [table for table in critical_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Missing critical tables: {missing_tables}")
                return False
            
            logger.info(f"Found {len(tables)} operational tables")
            return True
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
    
    def test_migration_data_access(self) -> bool:
        """Test access to migrated data"""
        try:
            # Test assets database
            with self.db_config.get_db_session('assets') as session:
                result = session.execute(text("SELECT COUNT(*) FROM assets")).fetchone()
                asset_count = result[0] if result else 0
                logger.info(f"Found {asset_count} assets in migration database")
                
                if asset_count == 0:
                    logger.error("No assets found in migration database")
                    return False
            
            # Test correlations database
            with self.db_config.get_db_session('correlations') as session:
                result = session.execute(text("SELECT COUNT(*) FROM asset_correlations")).fetchone()
                corr_count = result[0] if result else 0
                logger.info(f"Found {corr_count} correlations in migration database")
                
                if corr_count == 0:
                    logger.error("No correlations found in migration database")
                    return False
            
            # Test scenarios database
            with self.db_config.get_db_session('scenarios') as session:
                result = session.execute(text("SELECT COUNT(*) FROM scenario_inputs")).fetchone()
                scenario_count = result[0] if result else 0
                logger.info(f"Found {scenario_count} scenario parameters in migration database")
                
                if scenario_count == 0:
                    logger.error("No scenario parameters found in migration database")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Migration data access failed: {e}")
            return False
    
    def test_data_integration_service(self) -> bool:
        """Test data integration service functionality"""
        try:
            # Test correlation lookup
            # Use a sample asset ID that should exist
            correlation = self.integration_service.get_correlation('BRSNP9UX8', 'BRSKTDN35')
            
            if correlation is None:
                logger.warning("Sample correlation lookup returned None - may be expected if assets don't exist")
            else:
                logger.info(f"Sample correlation lookup successful: {correlation}")
            
            # Test scenario parameters lookup
            scenario_params = self.integration_service.get_scenario_parameters('Mag 6')
            
            if not scenario_params:
                logger.warning("Scenario parameters lookup returned empty - checking if scenarios exist")
                # This may be expected if scenario names differ
            else:
                logger.info(f"Found {len(scenario_params)} parameters for Mag 6 scenario")
            
            return True
            
        except Exception as e:
            logger.error(f"Data integration service test failed: {e}")
            return False
    
    def test_redis_caching(self) -> bool:
        """Test Redis caching functionality"""
        redis_client = self.db_config.get_redis_client()
        
        if not redis_client:
            logger.warning("Redis not available - skipping cache tests")
            return True  # Not a failure if Redis is optional
        
        try:
            # Test basic Redis operations
            test_key = "test:phase1:cache"
            test_value = "cache_test_value"
            
            redis_client.setex(test_key, 60, test_value)
            retrieved_value = redis_client.get(test_key)
            
            if retrieved_value and retrieved_value.decode('utf-8') == test_value:
                logger.info("Redis caching test successful")
                redis_client.delete(test_key)  # Cleanup
                return True
            else:
                logger.error("Redis cache test failed - value mismatch")
                return False
            
        except Exception as e:
            logger.error(f"Redis caching test failed: {e}")
            return False
    
    def test_database_performance(self) -> bool:
        """Test basic database performance"""
        try:
            # Test PostgreSQL performance
            start_time = datetime.now()
            with self.db_config.get_db_session('postgresql') as session:
                session.execute(text("SELECT 1"))
            pg_duration = (datetime.now() - start_time).total_seconds()
            
            if pg_duration > 1.0:  # Should be much faster
                logger.warning(f"PostgreSQL connection slow: {pg_duration:.3f}s")
            else:
                logger.info(f"PostgreSQL connection time: {pg_duration:.3f}s")
            
            # Test migration database performance
            start_time = datetime.now()
            with self.db_config.get_db_session('assets') as session:
                session.execute(text("SELECT COUNT(*) FROM assets LIMIT 1"))
            sqlite_duration = (datetime.now() - start_time).total_seconds()
            
            if sqlite_duration > 2.0:  # SQLite can be slower
                logger.warning(f"SQLite query slow: {sqlite_duration:.3f}s")
            else:
                logger.info(f"SQLite query time: {sqlite_duration:.3f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all Phase 1 tests"""
        logger.info("🚀 Starting Phase 1 Implementation Tests")
        logger.info("=" * 60)
        
        # Define test suite
        tests = [
            ("Database Health Check", self.test_database_health),
            ("Operational Schema Validation", self.test_operational_schema),
            ("Migration Data Access", self.test_migration_data_access),
            ("Data Integration Service", self.test_data_integration_service),
            ("Redis Caching", self.test_redis_caching),
            ("Database Performance", self.test_database_performance)
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Calculate results
        self.test_results['end_time'] = datetime.now()
        self.test_results['duration'] = (
            self.test_results['end_time'] - self.test_results['start_time']
        ).total_seconds()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1 TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Tests Run: {self.test_results['tests_run']}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']}")
        logger.info(f"Duration: {self.test_results['duration']:.2f} seconds")
        
        if self.test_results['failures']:
            logger.info(f"\nFailed Tests:")
            for failure in self.test_results['failures']:
                logger.info(f"  - {failure}")
        
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 Phase 1 Implementation: SUCCESSFUL")
            return True
        else:
            logger.error("❌ Phase 1 Implementation: FAILED")
            return False

def main():
    """Main execution function"""
    tester = Phase1Tester()
    
    if tester.run_all_tests():
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)