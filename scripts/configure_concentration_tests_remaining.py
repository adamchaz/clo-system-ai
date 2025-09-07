#!/usr/bin/env python3
"""
Configure Concentration Tests for Remaining MAG Deals
Sets up concentration test configurations for MAG8, MAG9, MAG12, MAG14, MAG15

This script:
1. Uses the correct deal_concentration_thresholds schema (test_id not test_number)
2. Copies concentration test configurations from MAG17 as template
3. Creates deal-specific test configurations
4. Verifies test setup for each deal
"""

import sys
import os
import psycopg2
from psycopg2.extras import DictCursor, execute_batch
from datetime import datetime, date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'database': 'clo_dev',
    'user': 'postgres',
    'password': 'adamchaz'
}

def configure_deal_concentration_tests(conn, deal_id):
    """Configure concentration tests for a specific deal"""
    logger.info(f"Configuring concentration tests for {deal_id}...")
    
    cursor = conn.cursor()
    
    # Check if deal already has concentration test configuration
    cursor.execute("SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = %s", (deal_id,))
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        logger.info(f"{deal_id} already has {existing_count} concentration test configurations")
        return existing_count
    
    # Copy concentration test configurations from MAG17 as template
    # Using correct schema: test_id, not test_number
    cursor.execute("""
        INSERT INTO deal_concentration_thresholds 
        (deal_id, test_id, threshold_value, effective_date, mag_version, created_at)
        SELECT 
            %s as deal_id,
            test_id,
            threshold_value,
            effective_date,
            %s as mag_version,
            CURRENT_TIMESTAMP as created_at
        FROM deal_concentration_thresholds 
        WHERE deal_id = 'MAG17'
    """, (deal_id, deal_id))
    
    conn.commit()
    
    # Count what was inserted
    cursor.execute("SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = %s", (deal_id,))
    new_count = cursor.fetchone()[0]
    
    logger.info(f"Configured {new_count} concentration tests for {deal_id}")
    return new_count

def verify_concentration_tests(conn, deal_id):
    """Verify concentration test configuration for a deal"""
    logger.info(f"Verifying {deal_id} concentration tests...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get test count by type
    cursor.execute("""
        SELECT 
            COUNT(*) as total_tests,
            COUNT(CASE WHEN threshold_value > 0 THEN 1 END) as active_tests,
            MIN(test_id) as min_test_id,
            MAX(test_id) as max_test_id,
            AVG(threshold_value) as avg_threshold
        FROM deal_concentration_thresholds 
        WHERE deal_id = %s
    """, (deal_id,))
    
    result = cursor.fetchone()
    
    logger.info(f"{deal_id} concentration test verification:")
    logger.info(f"  Total tests configured: {result['total_tests']}")
    logger.info(f"  Active tests (threshold > 0): {result['active_tests']}")
    logger.info(f"  Test ID range: {result['min_test_id']} - {result['max_test_id']}")
    logger.info(f"  Average threshold: {float(result['avg_threshold']):.4f}")
    
    return {
        'total_tests': result['total_tests'],
        'active_tests': result['active_tests'],
        'status': 'COMPLETE' if result['total_tests'] >= 30 else 'PARTIAL'
    }

def main():
    """Main concentration tests configuration function"""
    logger.info("Starting Concentration Tests Configuration for Remaining MAG Deals...")
    logger.info("Deals: MAG8, MAG9, MAG12, MAG14, MAG15")
    logger.info("=" * 80)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        configuration_results = {}
        
        # Process each deal
        for deal_id in ['MAG8', 'MAG9', 'MAG12', 'MAG14', 'MAG15']:
            logger.info(f"\n{'='*15} CONFIGURING {deal_id} {'='*15}")
            
            try:
                # Configure concentration tests
                test_count = configure_deal_concentration_tests(conn, deal_id)
                
                # Verify configuration
                verification = verify_concentration_tests(conn, deal_id)
                
                configuration_results[deal_id] = {
                    'tests_configured': test_count,
                    'verification': verification,
                    'success': True
                }
                
            except Exception as e:
                logger.error(f"Error configuring {deal_id} concentration tests: {e}")
                configuration_results[deal_id] = {'error': str(e), 'success': False}
        
        # Final Summary
        logger.info(f"\n{'='*20} CONCENTRATION TESTS SUMMARY {'='*20}")
        
        total_tests = 0
        complete_deals = 0
        failed_deals = 0
        
        for deal_id, results in configuration_results.items():
            if not results.get('success', False):
                logger.error(f"{deal_id}: FAILED - {results.get('error', 'Unknown error')}")
                failed_deals += 1
                continue
            
            verification = results['verification']
            status = verification['status']
            
            if status == 'COMPLETE':
                complete_deals += 1
            
            total_tests += results['tests_configured']
            
            logger.info(f"{deal_id}: {status} - {verification['total_tests']} tests configured "
                       f"({verification['active_tests']} active)")
        
        logger.info(f"\nOVERALL RESULTS:")
        logger.info(f"  Total tests configured: {total_tests}")
        logger.info(f"  Complete deals: {complete_deals}/5")
        logger.info(f"  Failed deals: {failed_deals}/5")
        
        if complete_deals == 5:
            logger.info(f"\n✅ ALL CONCENTRATION TESTS CONFIGURED SUCCESSFULLY!")
            logger.info("All 10 MAG deals now have complete concentration test configurations")
        else:
            logger.warning(f"\n⚠️  {failed_deals} deals had configuration errors")
        
    except Exception as e:
        logger.error(f"❌ Configuration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()