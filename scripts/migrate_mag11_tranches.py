#!/usr/bin/env python3
"""
Migrate MAG11 Tranche Data to clo_tranches Table
Creates tranche records for MAG11 based on the structure found in Excel

This script:
1. Creates MAG11 tranche records in clo_tranches table
2. Uses the structure found in "Mag 11 Inputs" worksheet
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

# MAG11 Tranche Data (from Excel analysis)
MAG11_TRANCHES = [
    {
        'tranche_id': 'MAG11-A1',
        'deal_id': 'MAG11',
        'tranche_name': 'Class A-1',
        'initial_balance': Decimal('349250000.00'),  # $349.25M
        'current_balance': Decimal('349250000.00'),
        'coupon_rate': None,  # Floating rate - to be determined
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,  # To be determined
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 1,
        'payment_rank': 1,
        'interest_deferrable': False
    },
    {
        'tranche_id': 'MAG11-A2',
        'deal_id': 'MAG11',
        'tranche_name': 'Class A-2',
        'initial_balance': Decimal('63750000.00'),  # $63.75M
        'current_balance': Decimal('63750000.00'),
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
        'tranche_id': 'MAG11-B',
        'deal_id': 'MAG11',
        'tranche_name': 'Class B',
        'initial_balance': Decimal('30750000.00'),  # $30.75M
        'current_balance': Decimal('30750000.00'),
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
        'tranche_id': 'MAG11-C',
        'deal_id': 'MAG11',
        'tranche_name': 'Class C',
        'initial_balance': Decimal('33000000.00'),  # $33.0M
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
        'tranche_id': 'MAG11-D',
        'deal_id': 'MAG11',
        'tranche_name': 'Class D',
        'initial_balance': Decimal('30250000.00'),  # $30.25M
        'current_balance': Decimal('30250000.00'),
        'coupon_rate': None,
        'coupon_type': 'FLOATING',
        'index_name': 'LIBOR',
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 5,
        'payment_rank': 5,
        'interest_deferrable': True  # Mezzanine can defer
    },
    {
        'tranche_id': 'MAG11-SUB',
        'deal_id': 'MAG11',
        'tranche_name': 'Sub Notes',
        'initial_balance': Decimal('53750000.00'),  # $53.75M
        'current_balance': Decimal('53750000.00'),
        'coupon_rate': None,  # Equity - residual returns
        'coupon_type': 'EQUITY',
        'index_name': None,
        'margin': None,
        'mdy_rating': None,
        'sp_rating': None,
        'seniority_level': 6,
        'payment_rank': 6,
        'interest_deferrable': True  # Equity can defer
    }
]

def check_existing_tranches(conn):
    """Check if MAG11 tranches already exist"""
    logger.info("Checking for existing MAG11 tranches...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM clo_tranches WHERE deal_id = 'MAG11'")
    result = cursor.fetchone()
    
    existing_count = result['count']
    logger.info(f"Found {existing_count} existing MAG11 tranches")
    
    if existing_count > 0:
        cursor.execute("SELECT tranche_name, initial_balance FROM clo_tranches WHERE deal_id = 'MAG11' ORDER BY seniority_level")
        existing_tranches = cursor.fetchall()
        
        logger.info("Existing MAG11 tranches:")
        for tranche in existing_tranches:
            balance_m = float(tranche['initial_balance']) / 1_000_000
            logger.info(f"  {tranche['tranche_name']}: ${balance_m:.1f}M")
    
    return existing_count

def migrate_tranches(conn):
    """Migrate MAG11 tranches to database"""
    logger.info(f"Migrating {len(MAG11_TRANCHES)} MAG11 tranches to database...")
    
    cursor = conn.cursor()
    
    # Prepare insert data
    insert_records = []
    for tranche in MAG11_TRANCHES:
        record = dict(tranche)  # Copy the dictionary
        record['created_at'] = datetime.now()
        insert_records.append(record)
    
    # Insert tranches using execute_batch for better performance
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
        logger.info(f"Successfully migrated {len(insert_records)} MAG11 tranches")
        return len(insert_records)
        
    except Exception as e:
        logger.error(f"Error migrating tranches: {e}")
        conn.rollback()
        return 0

def verify_migration_results(conn):
    """Verify the migration results"""
    logger.info("Verifying MAG11 tranche migration results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get migrated tranches
    cursor.execute("""
        SELECT 
            tranche_name,
            initial_balance,
            coupon_type,
            seniority_level,
            payment_rank,
            interest_deferrable
        FROM clo_tranches
        WHERE deal_id = 'MAG11'
        ORDER BY seniority_level
    """)
    
    tranches = cursor.fetchall()
    
    if not tranches:
        logger.error("No MAG11 tranches found after migration!")
        return False
    
    logger.info(f"VERIFICATION: Found {len(tranches)} MAG11 tranches in database")
    logger.info("=" * 80)
    logger.info(f"{'Tranche':<12} {'Balance ($M)':<12} {'Type':<10} {'Level':<6} {'Rank':<5} {'Defer':<6}")
    logger.info("-" * 80)
    
    total_balance = Decimal('0')
    for tranche in tranches:
        balance_m = float(tranche['initial_balance']) / 1_000_000
        total_balance += tranche['initial_balance']
        defer_str = 'Yes' if tranche['interest_deferrable'] else 'No'
        
        logger.info(f"{tranche['tranche_name']:<12} {balance_m:<12.1f} {tranche['coupon_type']:<10} {tranche['seniority_level']:<6} {tranche['payment_rank']:<5} {defer_str:<6}")
    
    logger.info("-" * 80)
    total_m = float(total_balance) / 1_000_000
    logger.info(f"{'TOTAL':<12} {total_m:<12.1f}")
    
    # Calculate tranche percentages
    logger.info(f"\nTRANCHE COMPOSITION:")
    senior_balance = sum(t['initial_balance'] for t in tranches if t['seniority_level'] <= 2)
    mezzanine_balance = sum(t['initial_balance'] for t in tranches if 3 <= t['seniority_level'] <= 5)
    equity_balance = sum(t['initial_balance'] for t in tranches if t['seniority_level'] == 6)
    
    senior_pct = float(senior_balance) / float(total_balance) * 100
    mezz_pct = float(mezzanine_balance) / float(total_balance) * 100
    equity_pct = float(equity_balance) / float(total_balance) * 100
    
    logger.info(f"Senior Tranches (A-1, A-2): ${float(senior_balance)/1_000_000:.1f}M ({senior_pct:.1f}%)")
    logger.info(f"Mezzanine Tranches (B, C, D): ${float(mezzanine_balance)/1_000_000:.1f}M ({mezz_pct:.1f}%)")
    logger.info(f"Equity Tranche (Sub Notes): ${float(equity_balance)/1_000_000:.1f}M ({equity_pct:.1f}%)")
    
    # Compare with deal target
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = 'MAG11'")
    target = cursor.fetchone()
    
    if target:
        target_m = float(target['target_par_amount']) / 1_000_000
        logger.info(f"\nCOMPARISON TO DEAL:")
        logger.info(f"Total Tranche Balance: ${total_m:.1f}M")
        logger.info(f"Deal Target Par: ${target_m:.1f}M")
        logger.info(f"Tranche to Target Ratio: {total_m / target_m:.2f}")
    
    return True

def main():
    """Main migration function"""
    logger.info("Starting MAG11 Tranche Migration...")
    logger.info("=" * 80)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        # Check for existing tranches
        existing_count = check_existing_tranches(conn)
        
        # Migrate tranches
        migrated_count = migrate_tranches(conn)
        
        # Verify results
        verification_success = verify_migration_results(conn)
        
        # Summary
        logger.info(f"\nMIGRATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Existing tranches: {existing_count}")
        logger.info(f"Tranches migrated: {migrated_count}")
        logger.info(f"Verification: {'✅ PASSED' if verification_success else '❌ FAILED'}")
        
        if verification_success:
            logger.info(f"\n✅ MAG11 tranche migration completed successfully!")
            logger.info("MAG11 now has complete liability structure in clo_tranches table")
        else:
            logger.error(f"\n❌ MAG11 tranche migration verification failed!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()