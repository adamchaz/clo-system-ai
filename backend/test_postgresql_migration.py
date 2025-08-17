#!/usr/bin/env python3
"""
Integration Test for PostgreSQL Migration
Tests that all migrated data is accessible through the unified PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database_config import db_config
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connections():
    """Test that all database connections work"""
    print("Testing Database Connections")
    print("="*50)
    
    # Test direct PostgreSQL connection
    try:
        with db_config.get_db_session('postgresql') as session:
            result = session.execute(text("SELECT 1")).fetchone()
            print("PASS PostgreSQL direct connection: OK")
    except Exception as e:
        print(f"FAIL PostgreSQL direct connection: {e}")
        return False
    
    # Test legacy database name mappings
    legacy_databases = ['correlations', 'scenarios', 'config', 'reference']
    
    for db_name in legacy_databases:
        try:
            with db_config.get_db_session(db_name) as session:
                result = session.execute(text("SELECT 1")).fetchone()
                print(f"PASS Legacy database '{db_name}': OK")
        except Exception as e:
            print(f"FAIL Legacy database '{db_name}': {e}")
            return False
    
    return True

def test_migrated_data_access():
    """Test access to migrated data using legacy database names"""
    print("\n Testing Migrated Data Access")
    print("="*50)
    
    test_queries = {
        'correlations': {
            'table': 'asset_correlations',
            'query': 'SELECT COUNT(*) as count FROM asset_correlations',
            'expected_min': 238000  # Should have ~238K rows
        },
        'scenarios': {
            'table': 'scenario_inputs',
            'query': 'SELECT COUNT(*) as count FROM scenario_inputs',
            'expected_min': 19000  # Should have ~19K rows
        },
        'config': {
            'table': 'model_parameters', 
            'query': 'SELECT COUNT(*) as count FROM model_parameters',
            'expected_min': 300  # Should have ~356 rows
        },
        'reference': {
            'table': 'reference_data',
            'query': 'SELECT COUNT(*) as count FROM reference_data', 
            'expected_min': 600  # Should have ~694 rows
        }
    }
    
    all_passed = True
    
    for db_name, config in test_queries.items():
        try:
            # Test using legacy database name
            with db_config.get_db_session(db_name) as session:
                result = session.execute(text(config['query'])).fetchone()
                count = result[0]
                
                if count >= config['expected_min']:
                    print(f"PASS {db_name}: {count:,} rows (table: {config['table']})")
                else:
                    print(f"WARN  {db_name}: {count:,} rows - less than expected {config['expected_min']:,}")
                    all_passed = False
                    
        except Exception as e:
            print(f"FAIL {db_name}: Error accessing data - {e}")
            all_passed = False
    
    return all_passed

def test_data_integrity_spot_check():
    """Test data integrity with spot checks"""
    print("\n Testing Data Integrity (Spot Checks)")
    print("="*50)
    
    integrity_tests = [
        {
            'name': 'Correlation Values Range',
            'db': 'correlations',
            'query': '''
                SELECT MIN(correlation_value), MAX(correlation_value), COUNT(*) 
                FROM asset_correlations 
                WHERE correlation_value BETWEEN -1 AND 1
            ''',
            'validation': lambda r: r[2] > 0  # Should have valid correlations
        },
        {
            'name': 'Scenario Parameters',
            'db': 'scenarios', 
            'query': '''
                SELECT COUNT(DISTINCT scenario_name), COUNT(DISTINCT parameter_name), COUNT(*)
                FROM scenario_inputs
                WHERE scenario_name IS NOT NULL AND parameter_name IS NOT NULL
            ''',
            'validation': lambda r: r[0] > 0 and r[1] > 0 and r[2] > 0
        },
        {
            'name': 'Config Parameters Active',
            'db': 'config',
            'query': '''
                SELECT COUNT(*) as active_count
                FROM model_parameters 
                WHERE is_active = true
            ''',
            'validation': lambda r: r[0] > 0  # Should have some active parameters
        },
        {
            'name': 'Reference JSON Data',
            'db': 'reference',
            'query': '''
                SELECT COUNT(*) as json_count
                FROM reference_data 
                WHERE raw_data IS NOT NULL
            ''',
            'validation': lambda r: r[0] > 0  # Should have JSON data
        }
    ]
    
    all_passed = True
    
    for test in integrity_tests:
        try:
            with db_config.get_db_session(test['db']) as session:
                result = session.execute(text(test['query'])).fetchone()
                
                if test['validation'](result):
                    print(f"PASS {test['name']}: PASS")
                else:
                    print(f"FAIL {test['name']}: FAIL - {result}")
                    all_passed = False
                    
        except Exception as e:
            print(f"FAIL {test['name']}: Error - {e}")
            all_passed = False
    
    return all_passed

def test_performance_basic():
    """Basic performance test"""
    print("\n Testing Performance")
    print("="*50)
    
    from datetime import datetime
    
    performance_tests = [
        {
            'name': 'Correlation Lookup',
            'db': 'correlations',
            'query': '''
                SELECT correlation_value FROM asset_correlations 
                WHERE asset1_id LIKE 'ASSET%' LIMIT 100
            '''
        },
        {
            'name': 'Scenario Search',
            'db': 'scenarios',
            'query': '''
                SELECT parameter_value FROM scenario_inputs 
                WHERE scenario_name LIKE 'MAG%' LIMIT 100
            '''
        },
        {
            'name': 'Config Lookup',
            'db': 'config', 
            'query': '''
                SELECT parameter_value FROM model_parameters
                WHERE is_active = true LIMIT 50
            '''
        }
    ]
    
    all_passed = True
    
    for test in performance_tests:
        try:
            start_time = datetime.now()
            
            with db_config.get_db_session(test['db']) as session:
                result = session.execute(text(test['query'])).fetchall()
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if duration < 1.0:  # Should complete within 1 second
                print(f"PASS {test['name']}: {duration:.3f}s ({len(result)} rows)")
            else:
                print(f"WARN  {test['name']}: {duration:.3f}s - slower than expected")
                all_passed = False
                
        except Exception as e:
            print(f"FAIL {test['name']}: Error - {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all integration tests"""
    print(" CLO System PostgreSQL Migration Integration Test")
    print("Testing unified PostgreSQL database with legacy compatibility")
    print("="*70)
    
    test_results = []
    
    # Test 1: Database Connections
    test_results.append(test_database_connections())
    
    # Test 2: Migrated Data Access
    test_results.append(test_migrated_data_access())
    
    # Test 3: Data Integrity
    test_results.append(test_data_integrity_spot_check())
    
    # Test 4: Performance
    test_results.append(test_performance_basic())
    
    # Summary
    print("\n" + "="*70)
    print(" INTEGRATION TEST SUMMARY")
    print("="*70)
    
    test_names = [
        "Database Connections",
        "Migrated Data Access", 
        "Data Integrity Spot Check",
        "Performance Test"
    ]
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "PASS PASS" if result else "FAIL FAIL"
        print(f"  {i+1}. {name}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if all(test_results):
        print(" ALL TESTS PASSED - PostgreSQL Migration Successful!")
        return 0
    else:
        print(" SOME TESTS FAILED - Review issues above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)