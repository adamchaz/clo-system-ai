#!/usr/bin/env python3
"""
Migrate MAG6 and MAG7 Tranche Data to clo_tranches Table
Creates tranche records for MAG6 and MAG7 based on Excel analysis

This script:
1. Creates MAG6 and MAG7 tranche records in clo_tranches table
2. Uses the structure found in analysis of input worksheets
3. Sets up proper seniority levels and payment rankings
4. Reports on migration results
"""

import sys
import os
import psycopg2
from psycopg2.extras import DictCursor, execute_batch
from datetime import datetime
from decimal import Decimal
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

# MAG6 Tranche Data (7 tranches from analysis)
MAG6_TRANCHES = [
    {
        'tranche_id': 'MAG6-A',
        'deal_id': 'MAG6',
        'tranche_name': 'Class A',
        'initial_balance': Decimal('263000000.00'),  # Senior tranche
        'current_balance': Decimal('263000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 1,
        'payment_rank': 1,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG6-B',
        'deal_id': 'MAG6',
        'tranche_name': 'Class B',
        'initial_balance': Decimal('28000000.00'),  # Mezzanine
        'current_balance': Decimal('28000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 2,
        'payment_rank': 2,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG6-C',
        'deal_id': 'MAG6',
        'tranche_name': 'Class C',
        'initial_balance': Decimal('19000000.00'),  # Mezzanine
        'current_balance': Decimal('19000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 3,
        'payment_rank': 3,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG6-D',
        'deal_id': 'MAG6',
        'tranche_name': 'Class D',
        'initial_balance': Decimal('19000000.00'),  # Mezzanine
        'current_balance': Decimal('19000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 4,
        'payment_rank': 4,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG6-E',
        'deal_id': 'MAG6',
        'tranche_name': 'Class E',
        'initial_balance': Decimal('19000000.00'),  # Mezzanine
        'current_balance': Decimal('19000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 5,
        'payment_rank': 5,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG6-X',
        'deal_id': 'MAG6',
        'tranche_name': 'Class X',
        'initial_balance': Decimal('16250000.00'),  # Subordinate
        'current_balance': Decimal('16250000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 6,
        'payment_rank': 6,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG6-SUB',
        'deal_id': 'MAG6',
        'tranche_name': 'Sub Notes',
        'initial_balance': Decimal('37500000.00'),  # Equity
        'current_balance': Decimal('37500000.00'),
        'coupon_rate': None,
        'coupon_type': 'EQUITY',
        'index_name': None,
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 7,
        'payment_rank': 7,
        'interest_deferrable': True
    }
]

# MAG7 Tranche Data (8 tranches from analysis) 
MAG7_TRANCHES = [
    {
        'tranche_id': 'MAG7-A1A',
        'deal_id': 'MAG7',
        'tranche_name': 'Class A-1A',
        'initial_balance': Decimal('375000000.00'),  # Senior
        'current_balance': Decimal('375000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 1,
        'payment_rank': 1,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG7-A1B',
        'deal_id': 'MAG7',
        'tranche_name': 'Class A-1B',
        'initial_balance': Decimal('42000000.00'),  # Senior
        'current_balance': Decimal('42000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 2,
        'payment_rank': 2,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG7-A2',
        'deal_id': 'MAG7',
        'tranche_name': 'Class A-2',
        'initial_balance': Decimal('45000000.00'),  # Senior
        'current_balance': Decimal('45000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 3,
        'payment_rank': 3,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG7-B',
        'deal_id': 'MAG7',
        'tranche_name': 'Class B',
        'initial_balance': Decimal('33000000.00'),  # Mezzanine
        'current_balance': Decimal('33000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 4,
        'payment_rank': 4,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG7-C',
        'deal_id': 'MAG7',
        'tranche_name': 'Class C',
        'initial_balance': Decimal('24000000.00'),  # Mezzanine
        'current_balance': Decimal('24000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 5,
        'payment_rank': 5,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG7-D',
        'deal_id': 'MAG7',
        'tranche_name': 'Class D',
        'initial_balance': Decimal('24000000.00'),  # Mezzanine
        'current_balance': Decimal('24000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 6,
        'payment_rank': 6,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG7-E',
        'deal_id': 'MAG7',
        'tranche_name': 'Class E',
        'initial_balance': Decimal('21000000.00'),  # Subordinate
        'current_balance': Decimal('21000000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 7,
        'payment_rank': 7,
        'interest_deferrable': True
    },
    {
        'tranche_id': 'MAG7-SUB',
        'deal_id': 'MAG7',
        'tranche_name': 'Sub Notes',
        'initial_balance': Decimal('88000000.00'),  # Equity
        'current_balance': Decimal('88000000.00'),
        'coupon_rate': None,
        'coupon_type': 'EQUITY',
        'index_name': None,
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 8,
        'payment_rank': 8,
        'interest_deferrable': True
    }
]

def check_existing_tranches(conn, deal_id):
    """Check if tranches already exist for the deal"""
    logger.info(f"Checking for existing {deal_id} tranches...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM clo_tranches WHERE deal_id = %s", (deal_id,))
    result = cursor.fetchone()
    
    existing_count = result['count']
    logger.info(f"Found {existing_count} existing {deal_id} tranches")
    
    return existing_count

def migrate_deal_tranches(conn, deal_id, tranches_data):
    """Migrate tranches for a specific deal"""
    logger.info(f"Migrating {len(tranches_data)} {deal_id} tranches to database...")
    
    cursor = conn.cursor()
    
    # Prepare insert data
    insert_records = []
    for tranche in tranches_data:
        record = dict(tranche)
        record['created_at'] = datetime.now()
        insert_records.append(record)
    
    # Insert tranches
    insert_sql = """
    INSERT INTO clo_tranches (
        tranche_id, deal_id, tranche_name, initial_balance, current_balance,
        coupon_rate, coupon_type, index_name, margin,
        mdy_rating, sp_rating, seniority_level, payment_rank,
        interest_deferrable, created_at
    ) VALUES (
        %(tranche_id)s, %(deal_id)s, %(tranche_name)s, %(initial_balance)s, %(current_balance)s,
        %(coupon_rate)s, %(coupon_type)s, %(index_name)s, %(margin)s,
        %(mdy_rating)s, %(sp_rating)s, %(seniority_level)s, %(payment_rank)s,
        %(interest_deferrable)s, %(created_at)s
    )
    ON CONFLICT (tranche_id) 
    DO UPDATE SET
        initial_balance = EXCLUDED.initial_balance,
        current_balance = EXCLUDED.current_balance
    """
    
    try:
        execute_batch(cursor, insert_sql, insert_records, page_size=10)
        conn.commit()
        logger.info(f"Successfully migrated {len(insert_records)} {deal_id} tranches")
        return len(insert_records)
        
    except Exception as e:
        logger.error(f"Error migrating {deal_id} tranches: {e}")
        conn.rollback()
        return 0

def verify_deal_tranches(conn, deal_id):
    """Verify tranche migration for a specific deal"""
    logger.info(f"Verifying {deal_id} tranche migration...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            tranche_name,
            initial_balance,
            coupon_type,
            seniority_level,
            payment_rank,
            interest_deferrable
        FROM clo_tranches
        WHERE deal_id = %s
        ORDER BY seniority_level
    """, (deal_id,))
    
    tranches = cursor.fetchall()
    
    if not tranches:
        logger.error(f"No {deal_id} tranches found after migration!")
        return False
    
    logger.info(f"{deal_id} TRANCHE VERIFICATION")
    logger.info("=" * 60)
    logger.info(f"{'Tranche':<12} {'Balance ($M)':<12} {'Type':<10} {'Level':<6} {'Defer':<6}")
    logger.info("-" * 60)
    
    total_balance = Decimal('0')
    for tranche in tranches:
        balance_m = float(tranche['initial_balance']) / 1_000_000
        total_balance += tranche['initial_balance']
        defer_str = 'Yes' if tranche['interest_deferrable'] else 'No'
        
        logger.info(f"{tranche['tranche_name']:<12} {balance_m:<12.1f} {tranche['coupon_type']:<10} {tranche['seniority_level']:<6} {defer_str:<6}")
    
    logger.info("-" * 60)
    total_m = float(total_balance) / 1_000_000
    logger.info(f"{'TOTAL':<12} {total_m:<12.1f}")
    
    # Compare with deal target
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = %s", (deal_id,))
    target = cursor.fetchone()
    
    if target:
        target_m = float(target['target_par_amount']) / 1_000_000
        logger.info(f"\nDEAL COMPARISON:")
        logger.info(f"Total Tranche Balance: ${total_m:.1f}M")
        logger.info(f"Deal Target Par: ${target_m:.1f}M")
        logger.info(f"Tranche to Target Ratio: {total_m / target_m:.2f}")
    
    return True

def main():
    """Main migration function"""
    logger.info("Starting MAG6 and MAG7 Tranche Migration...")
    logger.info("=" * 80)
    
    deal_configs = {
        'MAG6': MAG6_TRANCHES,
        'MAG7': MAG7_TRANCHES
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        migration_results = {}
        
        # Process each deal
        for deal_id, tranches_data in deal_configs.items():
            logger.info(f"\n{'='*20} PROCESSING {deal_id} {'='*20}")
            
            # Check existing
            existing_count = check_existing_tranches(conn, deal_id)
            
            # Migrate tranches
            migrated_count = migrate_deal_tranches(conn, deal_id, tranches_data)
            
            # Verify results
            verification_success = verify_deal_tranches(conn, deal_id)
            
            migration_results[deal_id] = {
                'existing_count': existing_count,
                'migrated_count': migrated_count,
                'verification_success': verification_success
            }
        
        # Summary
        logger.info(f"\n{'='*20} MIGRATION SUMMARY {'='*20}")
        
        total_migrated = 0
        successful_deals = 0
        
        for deal_id, results in migration_results.items():
            migrated = results['migrated_count']
            success = results['verification_success']
            
            total_migrated += migrated
            if success:
                successful_deals += 1
            
            status = '✅ SUCCESS' if success else '❌ FAILED'
            logger.info(f"{deal_id}: {migrated} tranches migrated - {status}")
        
        logger.info(f"\nTOTAL RESULTS:")
        logger.info(f"  Tranches migrated: {total_migrated}")
        logger.info(f"  Successful deals: {successful_deals}/2")
        
        if successful_deals == 2:
            logger.info(f"\n✅ MAG6 and MAG7 tranche migration completed successfully!")
            logger.info("Both deals now have complete liability structures in clo_tranches table")
        else:
            logger.error(f"\n❌ Some tranche migrations failed!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()