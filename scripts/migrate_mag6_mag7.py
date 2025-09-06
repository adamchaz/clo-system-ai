#!/usr/bin/env python3
"""
Migrate MAG6 and MAG7 Deal Assets
Migrates asset data from "Mag 6 Inputs" and "Mag 7 Inputs" worksheets to deal_assets table

This script:
1. Loads asset data from MAG6 and MAG7 input worksheets
2. Updates deal_assets table with correct par amounts
3. Adds missing assets that aren't currently in deal_assets
4. Reports comprehensive migration results
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

# Deal configurations
DEAL_CONFIGS = {
    'MAG6': {
        'worksheet': 'Mag 6 Inputs',
        'target_assets': 313  # From analysis
    },
    'MAG7': {
        'worksheet': 'Mag 7 Inputs', 
        'target_assets': 320  # From analysis
    }
}

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

def load_deal_inputs(deal_id):
    """Load deal data from Excel worksheet"""
    config = DEAL_CONFIGS[deal_id]
    worksheet = config['worksheet']
    
    logger.info(f"Loading {deal_id} data from '{worksheet}' worksheet...")
    
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")
    
    try:
        # Read the deal inputs worksheet (header on row 3 = header=2)
        df = pd.read_excel(EXCEL_FILE, sheet_name=worksheet, header=2)
        logger.info(f"Loaded {len(df)} rows from '{worksheet}' worksheet")
        
        # Filter out empty rows - keep only rows with BLKRockID and Par Amount
        df = df[df['BLKRockID'].notna() & (df['BLKRockID'] != '')]
        df = df[df['Par Amount'].notna() & (df['Par Amount'] != 0)]
        logger.info(f"Found {len(df)} {deal_id} assets with valid BLKRockID and Par Amount")
        
        # Convert par amounts to proper format
        df['Par Amount'] = df['Par Amount'].apply(lambda x: safe_convert_numeric(x))
        df = df[df['Par Amount'].notna()]
        logger.info(f"After cleaning: {len(df)} {deal_id} assets with valid par amounts")
        
        # Calculate total portfolio value
        total_par = df['Par Amount'].sum()
        logger.info(f"{deal_id} total portfolio: ${total_par:,.2f}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading Excel file for {deal_id}: {e}")
        raise

def get_current_deal_assets(conn, deal_id):
    """Get current deal assets from database"""
    logger.info(f"Loading current {deal_id} deal_assets from database...")
    
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
    """, (deal_id,))
    
    current_assets = cursor.fetchall()
    logger.info(f"Found {len(current_assets)} existing {deal_id} deal_assets in database")
    
    return {asset['blkrock_id']: asset for asset in current_assets}

def update_deal_assets(conn, deal_id, excel_df, current_deal_assets):
    """Update and add deal_assets records"""
    logger.info(f"Updating {deal_id} deal_assets records...")
    
    cursor = conn.cursor()
    
    # Find assets that exist in both Excel and database
    excel_ids = set(excel_df['BLKRockID'].astype(str))
    db_ids = set(current_deal_assets.keys())
    common_ids = excel_ids & db_ids
    missing_ids = excel_ids - db_ids
    
    logger.info(f"{deal_id} asset analysis:")
    logger.info(f"  Common assets (to update): {len(common_ids)}")
    logger.info(f"  Missing assets (to add): {len(missing_ids)}")
    
    # Update existing records
    updates_made = 0
    update_records = []
    
    for blkrock_id in common_ids:
        excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
        current_record = current_deal_assets[blkrock_id]
        
        new_par_amount = safe_convert_numeric(excel_row['Par Amount'])
        current_par = current_record['par_amount']
        
        # Check if update is needed
        if new_par_amount != current_par:
            update_records.append({
                'deal_id': deal_id,
                'blkrock_id': blkrock_id,
                'par_amount': new_par_amount,
                'position_status': 'Active',
                'created_at': current_record['created_at']
            })
    
    if update_records:
        update_sql = """
        UPDATE deal_assets 
        SET par_amount = %(par_amount)s,
            position_status = %(position_status)s
        WHERE deal_id = %(deal_id)s AND blkrock_id = %(blkrock_id)s
        """
        
        execute_batch(cursor, update_sql, update_records)
        updates_made = len(update_records)
        logger.info(f"Updated {updates_made} existing {deal_id} deal_assets records")
    
    # Add missing records
    additions_made = 0
    if missing_ids:
        # Check which missing assets exist in assets table
        placeholders = ','.join(['%s'] * len(missing_ids))
        cursor.execute(f"""
            SELECT blkrock_id 
            FROM assets 
            WHERE blkrock_id IN ({placeholders})
        """, list(missing_ids))
        
        existing_assets = {row[0] for row in cursor.fetchall()}
        valid_missing_ids = missing_ids & existing_assets
        
        logger.info(f"  {len(valid_missing_ids)} missing assets exist in assets table")
        
        if valid_missing_ids:
            insert_records = []
            total_missing_par = Decimal('0')
            
            for blkrock_id in valid_missing_ids:
                excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
                par_amount = safe_convert_numeric(excel_row['Par Amount'])
                
                insert_records.append({
                    'deal_id': deal_id,
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
                additions_made = len(insert_records)
                logger.info(f"Added {additions_made} missing {deal_id} deal_assets records")
                logger.info(f"Total par amount added: ${total_missing_par:,.2f}")
    
    conn.commit()
    return updates_made, additions_made

def verify_deal_results(conn, deal_id):
    """Verify migration results for a specific deal"""
    logger.info(f"Verifying {deal_id} migration results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get updated totals from deal_assets
    cursor.execute("""
        SELECT 
            COUNT(*) as asset_count,
            SUM(COALESCE(par_amount, 0)) as total_par,
            AVG(COALESCE(par_amount, 0)) as avg_par,
            MAX(COALESCE(par_amount, 0)) as max_par
        FROM deal_assets
        WHERE deal_id = %s
    """, (deal_id,))
    
    result = cursor.fetchone()
    
    # Get target par for comparison
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = %s", (deal_id,))
    target_result = cursor.fetchone()
    
    # Get top 5 holdings
    cursor.execute("""
        SELECT da.blkrock_id, da.par_amount, a.issue_name
        FROM deal_assets da
        LEFT JOIN assets a ON da.blkrock_id = a.blkrock_id
        WHERE da.deal_id = %s AND da.par_amount > 0
        ORDER BY da.par_amount DESC
        LIMIT 5
    """, (deal_id,))
    
    top_holdings = cursor.fetchall()
    
    logger.info(f"{deal_id} FINAL RESULTS")
    logger.info("=" * 60)
    logger.info(f"Asset Count: {result['asset_count']}")
    logger.info(f"Total Par Amount: ${float(result['total_par']):,.2f}")
    logger.info(f"Average Par Amount: ${float(result['avg_par']):,.2f}")
    logger.info(f"Largest Position: ${float(result['max_par']):,.2f}")
    
    if target_result:
        target_par = float(target_result['target_par_amount'])
        actual_par = float(result['total_par'])
        coverage = actual_par / target_par * 100
        logger.info(f"Target Par Amount: ${target_par:,.2f}")
        logger.info(f"Coverage: {coverage:.1f}%")
    
    logger.info(f"\nTop 5 {deal_id} Holdings:")
    for i, holding in enumerate(top_holdings, 1):
        issue_name = holding['issue_name'][:30] if holding['issue_name'] else 'Unknown'
        logger.info(f"  {i}. ${float(holding['par_amount']):,.2f} - {issue_name}")
    
    return {
        'asset_count': result['asset_count'],
        'total_par': float(result['total_par']),
        'target_par': float(target_result['target_par_amount']) if target_result else 0,
        'coverage': coverage if target_result else 0
    }

def main():
    """Main migration function"""
    logger.info("Starting MAG6 and MAG7 Migration...")
    logger.info("=" * 80)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        migration_results = {}
        
        # Process each deal
        for deal_id in ['MAG6', 'MAG7']:
            logger.info(f"\n{'='*20} PROCESSING {deal_id} {'='*20}")
            
            # Load Excel data
            excel_df = load_deal_inputs(deal_id)
            
            # Get current database assets
            current_deal_assets = get_current_deal_assets(conn, deal_id)
            
            # Update deal assets
            updates_made, additions_made = update_deal_assets(conn, deal_id, excel_df, current_deal_assets)
            
            # Verify results
            verification = verify_deal_results(conn, deal_id)
            
            migration_results[deal_id] = {
                'updates_made': updates_made,
                'additions_made': additions_made,
                'verification': verification
            }
        
        # Final summary
        logger.info(f"\n{'='*20} MIGRATION SUMMARY {'='*20}")
        
        total_updates = 0
        total_additions = 0
        
        for deal_id, results in migration_results.items():
            updates = results['updates_made']
            additions = results['additions_made']
            verification = results['verification']
            
            total_updates += updates
            total_additions += additions
            
            logger.info(f"{deal_id}:")
            logger.info(f"  Records updated: {updates}")
            logger.info(f"  Records added: {additions}")
            logger.info(f"  Final asset count: {verification['asset_count']}")
            logger.info(f"  Final par amount: ${verification['total_par']:,.2f}")
            logger.info(f"  Coverage: {verification['coverage']:.1f}%")
        
        logger.info(f"\nTOTAL CHANGES:")
        logger.info(f"  Total updates: {total_updates}")
        logger.info(f"  Total additions: {total_additions}")
        logger.info(f"  Total changes: {total_updates + total_additions}")
        
        logger.info(f"\n✅ MAG6 and MAG7 migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()