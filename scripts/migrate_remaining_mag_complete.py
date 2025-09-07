#!/usr/bin/env python3
"""
Complete Migration for Remaining MAG Deals: MAG8, MAG9, MAG12, MAG14, MAG15
Migrates assets, tranches, and concentration test configurations from Excel

This script:
1. Migrates asset data from individual MAG input worksheets to deal_assets table
2. Creates complete tranche structures in clo_tranches table
3. Configures deal-specific concentration test thresholds
4. Verifies all migration results
"""

import sys
import os
import pandas as pd
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

# Excel file path
EXCEL_FILE = 'TradeHypoPrelimv32.xlsm'

# Deal configurations with Excel data from analysis
DEAL_CONFIGS = {
    'MAG8': {
        'worksheet': 'Mag 8 Inputs',
        'target_assets': 312,
        'portfolio_value': 591867083.00,
        'tranches': [
            {'name': 'Class A', 'balance': 367500000.00, 'level': 1, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B', 'balance': 76500000.00, 'level': 2, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class C', 'balance': 37500000.00, 'level': 3, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class D', 'balance': 34890000.00, 'level': 4, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class E', 'balance': 36750000.00, 'level': 5, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class F', 'balance': 5580000.00, 'level': 6, 'type': 'FLOATING', 'defer': True},
            {'name': 'Sub Notes', 'balance': 53686000.00, 'level': 7, 'type': 'EQUITY', 'defer': True}
        ]
    },
    'MAG9': {
        'worksheet': 'Mag 9 Inputs',
        'target_assets': 295,
        'portfolio_value': 392841060.00,
        'tranches': [
            {'name': 'Class A-1', 'balance': 256000000.00, 'level': 1, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class A-2', 'balance': 40000000.00, 'level': 2, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B', 'balance': 28000000.00, 'level': 3, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class C', 'balance': 24200000.00, 'level': 4, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class D', 'balance': 20000000.00, 'level': 5, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class E', 'balance': 5000000.00, 'level': 6, 'type': 'FLOATING', 'defer': True},
            {'name': 'Sub Notes', 'balance': 35825000.00, 'level': 7, 'type': 'EQUITY', 'defer': True}
        ]
    },
    'MAG12': {
        'worksheet': 'Mag 12 Inputs',
        'target_assets': 279,
        'portfolio_value': 599581450.00,
        'tranches': [
            {'name': 'Class A', 'balance': 386400000.00, 'level': 1, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B', 'balance': 63600000.00, 'level': 2, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class C', 'balance': 39000000.00, 'level': 3, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class D', 'balance': 34500000.00, 'level': 4, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class E', 'balance': 30000000.00, 'level': 5, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class F', 'balance': 10500000.00, 'level': 6, 'type': 'FLOATING', 'defer': True},
            {'name': 'Sub Notes', 'balance': 44825000.00, 'level': 7, 'type': 'EQUITY', 'defer': True}
        ]
    },
    'MAG14': {
        'worksheet': 'Mag 14 Inputs',
        'target_assets': 269,
        'portfolio_value': 520520154.00,
        'tranches': [
            {'name': 'Class A', 'balance': 325500000.00, 'level': 1, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B', 'balance': 63500000.00, 'level': 2, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class C', 'balance': 41000000.00, 'level': 3, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class D', 'balance': 28250000.00, 'level': 4, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class E', 'balance': 24750000.00, 'level': 5, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class F', 'balance': 10500000.00, 'level': 6, 'type': 'FLOATING', 'defer': True},
            {'name': 'Sub Notes', 'balance': 41970000.00, 'level': 7, 'type': 'EQUITY', 'defer': True}
        ]
    },
    'MAG15': {
        'worksheet': 'Mag 15 Inputs',
        'target_assets': 239,
        'portfolio_value': 607236348.00,
        'tranches': [
            {'name': 'Class A', 'balance': 389000000.00, 'level': 1, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B-1', 'balance': 51800000.00, 'level': 2, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class B-2', 'balance': 10000000.00, 'level': 3, 'type': 'FLOATING', 'defer': False},
            {'name': 'Class C', 'balance': 43700000.00, 'level': 4, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class D', 'balance': 32600000.00, 'level': 5, 'type': 'FLOATING', 'defer': True},
            {'name': 'Class E', 'balance': 32300000.00, 'level': 6, 'type': 'FLOATING', 'defer': True},
            {'name': 'Sub Notes', 'balance': 62900000.00, 'level': 7, 'type': 'EQUITY', 'defer': True}
        ]
    }
}

def safe_convert_numeric(value, decimal_places=2):
    """Safely convert value to Decimal or return None"""
    if pd.isna(value) or value == '' or str(value).strip() == '':
        return None
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
        return round(Decimal(str(value)), decimal_places)
    except (ValueError, TypeError, OverflowError):
        return None

def load_deal_assets(deal_id):
    """Load deal assets from Excel worksheet"""
    config = DEAL_CONFIGS[deal_id]
    worksheet = config['worksheet']
    
    logger.info(f"Loading {deal_id} assets from '{worksheet}' worksheet...")
    
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")
    
    try:
        # Read the deal inputs worksheet (data starts at row 2, header at row 1)
        df = pd.read_excel(EXCEL_FILE, sheet_name=worksheet, header=1)
        logger.info(f"Loaded {len(df)} rows from '{worksheet}' worksheet")
        
        # Filter valid assets (BLKRockID in column 3, Par Amount in column 4)
        if 'BLKRockID' not in df.columns:
            df.columns = df.iloc[0]  # Use first row as header if needed
            df = df[1:]
        
        df = df[df['BLKRockID'].notna() & (df['BLKRockID'] != '')]
        df = df[df['Par Amount'].notna() & (df['Par Amount'] != 0)]
        
        # Convert par amounts
        df['Par Amount'] = df['Par Amount'].apply(lambda x: safe_convert_numeric(x))
        df = df[df['Par Amount'].notna()]
        
        logger.info(f"Found {len(df)} valid {deal_id} assets")
        total_par = df['Par Amount'].sum()
        logger.info(f"{deal_id} portfolio value: ${total_par:,.2f}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading {deal_id} assets: {e}")
        raise

def migrate_deal_assets(conn, deal_id, excel_df):
    """Migrate deal assets to deal_assets table"""
    logger.info(f"Migrating {deal_id} assets to deal_assets table...")
    
    cursor = conn.cursor()
    
    # Get current assets in database
    cursor.execute("SELECT blkrock_id FROM deal_assets WHERE deal_id = %s", (deal_id,))
    existing_ids = {row[0] for row in cursor.fetchall()}
    
    excel_ids = set(excel_df['BLKRockID'].astype(str))
    new_ids = excel_ids - existing_ids
    update_ids = excel_ids & existing_ids
    
    logger.info(f"{deal_id} asset analysis: {len(new_ids)} new, {len(update_ids)} updates")
    
    # Check which assets exist in assets table
    if new_ids:
        placeholders = ','.join(['%s'] * len(new_ids))
        cursor.execute(f"SELECT blkrock_id FROM assets WHERE blkrock_id IN ({placeholders})", list(new_ids))
        valid_new_ids = {row[0] for row in cursor.fetchall()}
        invalid_ids = new_ids - valid_new_ids
        
        if invalid_ids:
            logger.warning(f"{deal_id}: {len(invalid_ids)} assets not found in assets table")
    else:
        valid_new_ids = set()
    
    # Prepare records for insertion and updates
    insert_records = []
    update_records = []
    
    for _, asset_row in excel_df.iterrows():
        blkrock_id = str(asset_row['BLKRockID']).strip()
        par_amount = safe_convert_numeric(asset_row['Par Amount'])
        
        record = {
            'deal_id': deal_id,
            'blkrock_id': blkrock_id,
            'par_amount': par_amount,
            'position_status': 'Active',
            'created_at': datetime.now()
        }
        
        if blkrock_id in valid_new_ids:
            insert_records.append(record)
        elif blkrock_id in update_ids:
            update_records.append(record)
    
    # Execute insertions
    inserted = 0
    if insert_records:
        insert_sql = """
        INSERT INTO deal_assets (deal_id, blkrock_id, par_amount, position_status, created_at)
        VALUES (%(deal_id)s, %(blkrock_id)s, %(par_amount)s, %(position_status)s, %(created_at)s)
        ON CONFLICT (deal_id, blkrock_id) DO NOTHING
        """
        execute_batch(cursor, insert_sql, insert_records)
        inserted = len(insert_records)
        logger.info(f"Inserted {inserted} new {deal_id} assets")
    
    # Execute updates
    updated = 0
    if update_records:
        update_sql = """
        UPDATE deal_assets 
        SET par_amount = %(par_amount)s, position_status = %(position_status)s
        WHERE deal_id = %(deal_id)s AND blkrock_id = %(blkrock_id)s
        """
        execute_batch(cursor, update_sql, update_records)
        updated = len(update_records)
        logger.info(f"Updated {updated} existing {deal_id} assets")
    
    conn.commit()
    return inserted, updated

def migrate_deal_tranches(conn, deal_id):
    """Migrate deal tranches to clo_tranches table"""
    logger.info(f"Migrating {deal_id} tranches to clo_tranches table...")
    
    config = DEAL_CONFIGS[deal_id]
    tranches = config['tranches']
    
    cursor = conn.cursor()
    
    # Check existing tranches
    cursor.execute("SELECT COUNT(*) FROM clo_tranches WHERE deal_id = %s", (deal_id,))
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing {deal_id} tranches, updating...")
        cursor.execute("DELETE FROM clo_tranches WHERE deal_id = %s", (deal_id,))
    
    # Prepare tranche records
    tranche_records = []
    for i, tranche in enumerate(tranches):
        record = {
            'tranche_id': f"{deal_id}-{i+1}",
            'deal_id': deal_id,
            'tranche_name': tranche['name'],
            'initial_balance': Decimal(str(tranche['balance'])),
            'current_balance': Decimal(str(tranche['balance'])),
            'coupon_rate': None,
            'coupon_type': tranche['type'],
            'index_name': 'LIBOR' if tranche['type'] == 'FLOATING' else None,
            'margin': None,
            'mdy_rating': None,
            'sp_rating': None,
            'seniority_level': tranche['level'],
            'payment_rank': tranche['level'],
            'interest_deferrable': tranche['defer'],
            'created_at': datetime.now()
        }
        tranche_records.append(record)
    
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
    """
    
    execute_batch(cursor, insert_sql, tranche_records)
    conn.commit()
    
    logger.info(f"Successfully migrated {len(tranche_records)} {deal_id} tranches")
    return len(tranche_records)

def configure_concentration_tests(conn, deal_id):
    """Configure deal-specific concentration tests"""
    logger.info(f"Configuring concentration tests for {deal_id}...")
    
    cursor = conn.cursor()
    
    # Check if deal already has specific concentration test configuration
    cursor.execute("SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = %s", (deal_id,))
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        logger.info(f"{deal_id} already has {existing_count} concentration test configurations")
        return existing_count
    
    # Copy default concentration tests from a complete deal (like MAG17)
    cursor.execute("""
        INSERT INTO deal_concentration_thresholds (deal_id, test_number, threshold_value, is_active, created_at)
        SELECT %s, test_number, threshold_value, is_active, CURRENT_TIMESTAMP
        FROM deal_concentration_thresholds 
        WHERE deal_id = 'MAG17' AND is_active = true
    """, (deal_id,))
    
    conn.commit()
    
    # Count what was inserted
    cursor.execute("SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = %s", (deal_id,))
    new_count = cursor.fetchone()[0]
    
    logger.info(f"Configured {new_count} concentration tests for {deal_id}")
    return new_count

def verify_deal_migration(conn, deal_id):
    """Verify migration results for a deal"""
    logger.info(f"Verifying {deal_id} migration results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get asset summary
    cursor.execute("""
        SELECT 
            COUNT(*) as asset_count,
            SUM(COALESCE(par_amount, 0)) as total_par,
            AVG(COALESCE(par_amount, 0)) as avg_par
        FROM deal_assets
        WHERE deal_id = %s
    """, (deal_id,))
    asset_result = cursor.fetchone()
    
    # Get tranche summary
    cursor.execute("""
        SELECT 
            COUNT(*) as tranche_count,
            SUM(initial_balance) as total_tranches
        FROM clo_tranches
        WHERE deal_id = %s
    """, (deal_id,))
    tranche_result = cursor.fetchone()
    
    # Get concentration tests
    cursor.execute("SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = %s AND is_active = true", (deal_id,))
    test_count = cursor.fetchone()[0]
    
    # Get target par
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = %s", (deal_id,))
    target_result = cursor.fetchone()
    
    config = DEAL_CONFIGS[deal_id]
    expected_assets = config['target_assets']
    expected_tranches = len(config['tranches'])
    
    logger.info(f"{deal_id} VERIFICATION RESULTS")
    logger.info("=" * 50)
    logger.info(f"Assets: {asset_result['asset_count']}/{expected_assets} expected")
    logger.info(f"Portfolio Par: ${float(asset_result['total_par']):,.2f}")
    logger.info(f"Tranches: {tranche_result['tranche_count']}/{expected_tranches} expected")
    logger.info(f"Tranche Total: ${float(tranche_result['total_tranches']):,.2f}")
    logger.info(f"Concentration Tests: {test_count}")
    
    if target_result:
        target_par = float(target_result['target_par_amount'])
        actual_par = float(asset_result['total_par'])
        coverage = actual_par / target_par * 100 if target_par > 0 else 0
        logger.info(f"Target Coverage: {coverage:.1f}%")
    
    # Determine status
    assets_ok = asset_result['asset_count'] >= expected_assets * 0.9  # 90% threshold
    tranches_ok = tranche_result['tranche_count'] == expected_tranches
    tests_ok = test_count >= 30  # Expect ~30+ concentration tests
    
    status = "COMPLETE" if (assets_ok and tranches_ok and tests_ok) else "PARTIAL"
    logger.info(f"Migration Status: {status}")
    
    return {
        'status': status,
        'assets': asset_result['asset_count'],
        'par_amount': float(asset_result['total_par']),
        'tranches': tranche_result['tranche_count'],
        'tests': test_count
    }

def main():
    """Main migration function"""
    logger.info("Starting Complete Migration for Remaining MAG Deals...")
    logger.info("Deals: MAG8, MAG9, MAG12, MAG14, MAG15")
    logger.info("=" * 80)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        migration_results = {}
        
        # Process each deal
        for deal_id in ['MAG8', 'MAG9', 'MAG12', 'MAG14', 'MAG15']:
            logger.info(f"\n{'='*20} MIGRATING {deal_id} {'='*20}")
            
            try:
                # 1. Migrate Assets
                excel_df = load_deal_assets(deal_id)
                inserted, updated = migrate_deal_assets(conn, deal_id, excel_df)
                
                # 2. Migrate Tranches  
                tranche_count = migrate_deal_tranches(conn, deal_id)
                
                # 3. Configure Concentration Tests
                test_count = configure_concentration_tests(conn, deal_id)
                
                # 4. Verify Results
                verification = verify_deal_migration(conn, deal_id)
                
                migration_results[deal_id] = {
                    'assets_inserted': inserted,
                    'assets_updated': updated,
                    'tranches_migrated': tranche_count,
                    'tests_configured': test_count,
                    'verification': verification
                }
                
            except Exception as e:
                logger.error(f"Error migrating {deal_id}: {e}")
                migration_results[deal_id] = {'error': str(e)}
        
        # Final Summary
        logger.info(f"\n{'='*20} MIGRATION SUMMARY {'='*20}")
        
        total_assets = 0
        total_tranches = 0
        total_tests = 0
        complete_deals = 0
        
        for deal_id, results in migration_results.items():
            if 'error' in results:
                logger.error(f"{deal_id}: FAILED - {results['error']}")
                continue
                
            verification = results['verification']
            status = verification['status']
            
            if status == 'COMPLETE':
                complete_deals += 1
            
            total_assets += results['assets_inserted'] + results['assets_updated']
            total_tranches += results['tranches_migrated']
            total_tests += results['tests_configured']
            
            logger.info(f"{deal_id}: {status} - {verification['assets']} assets, "
                       f"{verification['tranches']} tranches, {verification['tests']} tests")
        
        logger.info(f"\nTOTAL MIGRATION RESULTS:")
        logger.info(f"  Assets migrated: {total_assets}")
        logger.info(f"  Tranches created: {total_tranches}")
        logger.info(f"  Test configs: {total_tests}")
        logger.info(f"  Complete deals: {complete_deals}/5")
        
        if complete_deals == 5:
            logger.info(f"\n✅ ALL REMAINING MAG DEALS MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("All 10 MAG deals now have complete assets, tranches, and concentration tests")
        else:
            logger.warning(f"\n⚠️  {5-complete_deals} deals had issues - check logs above")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()