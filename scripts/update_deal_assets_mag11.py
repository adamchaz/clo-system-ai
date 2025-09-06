#!/usr/bin/env python3
"""
Update DEAL_ASSETS table with MAG11 Inputs data
Updates the deal_assets table with correct par amounts from "Mag 11 Inputs" worksheet

This script:
1. Loads data from "Mag 11 Inputs" worksheet
2. Updates existing deal_assets records with correct par amounts
3. Adds missing assets to deal_assets table
4. Reports on updates made
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
WORKSHEET = 'Mag 11 Inputs'
DEAL_ID = 'MAG11'

def safe_convert_numeric(value, decimal_places=2):
    """Safely convert value to Decimal or return None"""
    if pd.isna(value) or value == '' or str(value).strip() == '':
        return None
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            value = value.replace('$', '').replace(',', '').strip()
        return round(Decimal(str(value)), decimal_places)
    except (ValueError, TypeError, OverflowError):
        return None

def load_mag11_inputs():
    """Load MAG11 data from Excel worksheet"""
    logger.info(f"Loading MAG11 data from {EXCEL_FILE} '{WORKSHEET}' worksheet...")
    
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")
    
    try:
        # Read the MAG11 inputs worksheet
        df = pd.read_excel(EXCEL_FILE, sheet_name=WORKSHEET, header=2)  # Header is on row 3
        logger.info(f"Loaded {len(df)} rows from '{WORKSHEET}' worksheet")
        
        # Filter out empty rows - keep only rows with BLKRockID and Par Amount
        df = df[df['BLKRockID'].notna() & (df['BLKRockID'] != '')]
        df = df[df['Par Amount'].notna() & (df['Par Amount'] != 0)]
        logger.info(f"Found {len(df)} assets with valid BLKRockID and Par Amount")
        
        # Convert par amounts to proper format
        df['Par Amount'] = df['Par Amount'].apply(lambda x: safe_convert_numeric(x))
        df = df[df['Par Amount'].notna()]
        logger.info(f"After cleaning: {len(df)} assets with valid par amounts")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        raise

def get_current_deal_assets(conn):
    """Get current MAG11 deal_assets from database"""
    logger.info(f"Loading current {DEAL_ID} deal_assets from database...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            deal_id,
            blkrock_id,
            par_amount,
            position_status,
            created_at
        FROM deal_assets
        WHERE deal_id = %s
        ORDER BY blkrock_id
    """, (DEAL_ID,))
    
    current_assets = cursor.fetchall()
    logger.info(f"Found {len(current_assets)} existing {DEAL_ID} deal_assets in database")
    
    return {asset['blkrock_id']: asset for asset in current_assets}

def update_existing_deal_assets(conn, excel_df, current_deal_assets):
    """Update existing deal_assets records"""
    logger.info("Updating existing deal_assets records...")
    
    cursor = conn.cursor()
    updates_made = 0
    
    # Find assets that exist in both Excel and database
    excel_ids = set(excel_df['BLKRockID'].astype(str))
    db_ids = set(current_deal_assets.keys())
    common_ids = excel_ids & db_ids
    
    logger.info(f"Found {len(common_ids)} assets to update in deal_assets table")
    
    update_records = []
    
    for blkrock_id in common_ids:
        excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
        current_record = current_deal_assets[blkrock_id]
        
        new_par_amount = safe_convert_numeric(excel_row['Par Amount'])
        current_par = current_record['par_amount']
        
        # Check if update is needed
        if new_par_amount != current_par:
            update_records.append({
                'deal_id': DEAL_ID,
                'blkrock_id': blkrock_id,
                'par_amount': new_par_amount,
                'position_status': 'Active',  # Set to Active for all MAG11 assets
                'created_at': current_record['created_at']  # Keep original created_at
            })
            
            logger.debug(f"Will update {blkrock_id}: ${current_par} -> ${new_par_amount}")
    
    if update_records:
        # Update deal_assets table
        update_sql = """
        UPDATE deal_assets 
        SET par_amount = %(par_amount)s,
            position_status = %(position_status)s
        WHERE deal_id = %(deal_id)s AND blkrock_id = %(blkrock_id)s
        """
        
        execute_batch(cursor, update_sql, update_records)
        conn.commit()
        updates_made = len(update_records)
        logger.info(f"Successfully updated {updates_made} existing deal_assets records")
    else:
        logger.info("No updates needed - all par amounts already match")
    
    return updates_made

def add_missing_deal_assets(conn, excel_df, current_deal_assets):
    """Add missing deal_assets records for assets that exist in Excel but not in deal_assets"""
    logger.info("Adding missing deal_assets records...")
    
    cursor = conn.cursor()
    
    # Find assets in Excel that don't exist in deal_assets
    excel_ids = set(excel_df['BLKRockID'].astype(str))
    db_ids = set(current_deal_assets.keys())
    missing_ids = excel_ids - db_ids
    
    logger.info(f"Found {len(missing_ids)} missing assets to add to deal_assets table")
    
    if not missing_ids:
        logger.info("No missing assets to add")
        return 0
    
    # Check which of these missing assets exist in the assets table
    placeholders = ','.join(['%s'] * len(missing_ids))
    cursor.execute(f"""
        SELECT blkrock_id 
        FROM assets 
        WHERE blkrock_id IN ({placeholders})
    """, list(missing_ids))
    
    existing_assets = {row[0] for row in cursor.fetchall()}
    valid_missing_ids = missing_ids & existing_assets
    invalid_missing_ids = missing_ids - existing_assets
    
    logger.info(f"  {len(valid_missing_ids)} missing assets exist in assets table and can be added")
    logger.info(f"  {len(invalid_missing_ids)} missing assets don't exist in assets table")
    
    if invalid_missing_ids:
        logger.warning(f"Assets not in assets table: {list(invalid_missing_ids)[:10]}...")  # Show first 10
    
    # Add valid missing assets to deal_assets
    insert_records = []
    total_missing_par = Decimal('0')
    
    for blkrock_id in valid_missing_ids:
        excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
        par_amount = safe_convert_numeric(excel_row['Par Amount'])
        
        insert_records.append({
            'deal_id': DEAL_ID,
            'blkrock_id': blkrock_id,
            'par_amount': par_amount,
            'position_status': 'Active',
            'created_at': datetime.now()
        })
        
        total_missing_par += par_amount or Decimal('0')
    
    if insert_records:
        insert_sql = """
        INSERT INTO deal_assets (deal_id, blkrock_id, par_amount, position_status, created_at)
        VALUES (%(deal_id)s, %(blkrock_id)s, %(par_amount)s, %(position_status)s, %(created_at)s)
        ON CONFLICT (deal_id, blkrock_id) DO NOTHING
        """
        
        execute_batch(cursor, insert_sql, insert_records)
        conn.commit()
        
        logger.info(f"Successfully added {len(insert_records)} missing deal_assets records")
        logger.info(f"Total par amount added: ${total_missing_par:,.2f}")
        
        return len(insert_records)
    
    return 0

def verify_final_results(conn):
    """Verify the final results"""
    logger.info("Verifying final deal_assets results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get updated totals from deal_assets
    cursor.execute("""
        SELECT 
            COUNT(*) as asset_count,
            SUM(COALESCE(par_amount, 0)) as total_par
        FROM deal_assets
        WHERE deal_id = %s
    """, (DEAL_ID,))
    
    result = cursor.fetchone()
    
    # Get target par for comparison
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = %s", (DEAL_ID,))
    target_result = cursor.fetchone()
    
    # Get some sample records
    cursor.execute("""
        SELECT da.blkrock_id, da.par_amount, a.issue_name
        FROM deal_assets da
        LEFT JOIN assets a ON da.blkrock_id = a.blkrock_id
        WHERE da.deal_id = %s AND da.par_amount > 0
        ORDER BY da.par_amount DESC
        LIMIT 5
    """, (DEAL_ID,))
    
    samples = cursor.fetchall()
    
    logger.info(f"FINAL {DEAL_ID} DEAL_ASSETS RESULTS")
    logger.info("=" * 60)
    logger.info(f"Asset Count: {result['asset_count']}")
    logger.info(f"Total Par Amount: ${float(result['total_par']):,.2f}")
    logger.info(f"Target Par Amount: ${float(target_result['target_par_amount']):,.2f}")
    logger.info(f"Coverage: {float(result['total_par']) / float(target_result['target_par_amount']) * 100:.1f}%")
    
    logger.info(f"\nTop 5 Holdings in deal_assets:")
    for sample in samples:
        issue_name = sample['issue_name'][:30] if sample['issue_name'] else 'Unknown'
        logger.info(f"  {sample['blkrock_id']}: ${float(sample['par_amount']):,.2f} - {issue_name}")
    
    return {
        'asset_count': result['asset_count'],
        'total_par': float(result['total_par']),
        'target_par': float(target_result['target_par_amount'])
    }

def main():
    """Main update function"""
    logger.info(f"Starting {DEAL_ID} deal_assets update from '{WORKSHEET}' worksheet...")
    logger.info("=" * 80)
    
    try:
        # Load Excel data
        excel_df = load_mag11_inputs()
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        # Get current deal_assets
        current_deal_assets = get_current_deal_assets(conn)
        
        # Update existing records
        updates_made = update_existing_deal_assets(conn, excel_df, current_deal_assets)
        
        # Add missing records
        additions_made = add_missing_deal_assets(conn, excel_df, current_deal_assets)
        
        # Verify final results
        final_results = verify_final_results(conn)
        
        # Summary
        logger.info(f"\nUPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Records updated: {updates_made}")
        logger.info(f"Records added: {additions_made}")
        logger.info(f"Final asset count: {final_results['asset_count']}")
        logger.info(f"Final par amount: ${final_results['total_par']:,.2f}")
        logger.info(f"Final coverage: {final_results['total_par'] / final_results['target_par'] * 100:.1f}%")
        
        logger.info(f"\n✅ {DEAL_ID} deal_assets update completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()