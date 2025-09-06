#!/usr/bin/env python3
"""
Migrate MAG11 Inputs Worksheet Data
Updates existing MAG11 assets with correct par amounts and identifies missing assets

This script:
1. Loads data from "Mag 11 Inputs" worksheet  
2. Updates par amounts for existing MAG11 assets
3. Identifies missing assets that need to be added
4. Reports on data discrepancies and coverage
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
        
        # Filter out empty rows - keep only rows with BLKRockID
        df = df[df['BLKRockID'].notna() & (df['BLKRockID'] != '')]
        logger.info(f"Found {len(df)} assets with valid BLKRockID")
        
        # Show column info for debugging
        logger.info(f"Available columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        raise

def get_current_mag11_assets(conn):
    """Get current MAG11 assets from database"""
    logger.info("Loading current MAG11 assets from database...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT 
            a.blkrock_id,
            a.issue_name,
            a.par_amount as db_par_amount,
            da.par_amount as deal_par_amount
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = 'MAG11'
        ORDER BY a.blkrock_id
    """)
    
    current_assets = cursor.fetchall()
    logger.info(f"Found {len(current_assets)} existing MAG11 assets in database")
    
    return {asset['blkrock_id']: asset for asset in current_assets}

def analyze_differences(excel_df, current_assets):
    """Analyze differences between Excel and database"""
    logger.info("Analyzing differences between Excel and database...")
    
    excel_ids = set(excel_df['BLKRockID'].astype(str))
    db_ids = set(current_assets.keys())
    
    # Find overlaps and differences
    common_ids = excel_ids & db_ids
    excel_only_ids = excel_ids - db_ids
    db_only_ids = db_ids - excel_ids
    
    logger.info(f"Asset Analysis:")
    logger.info(f"  Common assets (in both): {len(common_ids)}")
    logger.info(f"  Excel-only assets: {len(excel_only_ids)}")
    logger.info(f"  Database-only assets: {len(db_only_ids)}")
    
    # Calculate par amount totals
    excel_total_par = excel_df['Par Amount'].apply(lambda x: safe_convert_numeric(x) or Decimal('0')).sum()
    db_total_par = sum(float(asset['db_par_amount']) for asset in current_assets.values() if asset['db_par_amount'])
    
    logger.info(f"Par Amount Analysis:")
    logger.info(f"  Excel total par: ${excel_total_par:,.2f}")
    logger.info(f"  Database total par: ${db_total_par:,.2f}")
    logger.info(f"  Difference: ${float(excel_total_par) - db_total_par:,.2f}")
    
    return {
        'common_ids': common_ids,
        'excel_only_ids': excel_only_ids,
        'db_only_ids': db_only_ids,
        'excel_total_par': excel_total_par,
        'db_total_par': db_total_par
    }

def update_existing_assets(conn, excel_df, current_assets, common_ids):
    """Update par amounts for existing assets"""
    logger.info(f"Updating par amounts for {len(common_ids)} existing assets...")
    
    cursor = conn.cursor()
    updates_made = 0
    
    # Prepare update data
    update_records = []
    
    for blkrock_id in common_ids:
        excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
        current_asset = current_assets[blkrock_id]
        
        # Get new par amount and spread from Excel
        new_par_amount = safe_convert_numeric(excel_row['Par Amount'])
        new_spread = safe_convert_numeric(excel_row.get('Interest spread'), 6) if 'Interest spread' in excel_row else None
        
        current_par = current_asset['db_par_amount']
        
        # Check if update is needed
        if new_par_amount != current_par:
            update_records.append({
                'blkrock_id': blkrock_id,
                'par_amount': new_par_amount,
                'cpn_spread': new_spread,
                'updated_at': datetime.now()
            })
            
            logger.debug(f"Will update {blkrock_id}: ${current_par} -> ${new_par_amount}")
    
    if update_records:
        # Update assets table
        update_sql = """
        UPDATE assets 
        SET par_amount = %(par_amount)s,
            cpn_spread = %(cpn_spread)s,
            updated_at = %(updated_at)s
        WHERE blkrock_id = %(blkrock_id)s
        """
        
        execute_batch(cursor, update_sql, update_records)
        
        # Also update deal_assets table
        deal_update_sql = """
        UPDATE deal_assets 
        SET par_amount = %(par_amount)s
        WHERE blkrock_id = %(blkrock_id)s AND deal_id = 'MAG11'
        """
        
        execute_batch(cursor, deal_update_sql, update_records)
        
        conn.commit()
        updates_made = len(update_records)
        logger.info(f"Successfully updated {updates_made} existing assets")
    else:
        logger.info("No updates needed - all par amounts match")
    
    return updates_made

def create_missing_assets_report(excel_df, excel_only_ids):
    """Create a report of missing assets that need to be added"""
    logger.info(f"Creating report for {len(excel_only_ids)} missing assets...")
    
    missing_assets = []
    missing_par_total = Decimal('0')
    
    for blkrock_id in excel_only_ids:
        excel_row = excel_df[excel_df['BLKRockID'].astype(str) == blkrock_id].iloc[0]
        par_amount = safe_convert_numeric(excel_row['Par Amount']) or Decimal('0')
        spread = safe_convert_numeric(excel_row.get('Interest spread'), 6) if 'Interest spread' in excel_row else None
        
        missing_assets.append({
            'blkrock_id': blkrock_id,
            'par_amount': par_amount,
            'spread': spread
        })
        missing_par_total += par_amount
    
    logger.info(f"Missing assets represent ${missing_par_total:,.2f} in par amount")
    
    # Sort by par amount descending
    missing_assets.sort(key=lambda x: x['par_amount'], reverse=True)
    
    logger.info("Top 10 missing assets by par amount:")
    for i, asset in enumerate(missing_assets[:10]):
        logger.info(f"  {i+1:2d}. {asset['blkrock_id']}: ${asset['par_amount']:,.2f}")
    
    return missing_assets, missing_par_total

def verify_final_results(conn):
    """Verify the final migration results"""
    logger.info("Verifying final migration results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Get updated totals
    cursor.execute("""
        SELECT 
            COUNT(*) as asset_count,
            SUM(COALESCE(a.par_amount, 0)) as total_par_assets,
            SUM(COALESCE(da.par_amount, 0)) as total_par_deal_assets
        FROM assets a
        JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
        WHERE da.deal_id = 'MAG11'
    """)
    
    result = cursor.fetchone()
    
    # Get target par
    cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = 'MAG11'")
    target_result = cursor.fetchone()
    
    logger.info("FINAL MAG11 MIGRATION RESULTS")
    logger.info("=" * 50)
    logger.info(f"Asset Count: {result['asset_count']}")
    logger.info(f"Target Par Amount: ${float(target_result['target_par_amount']):,.2f}")
    logger.info(f"Actual Par Amount: ${float(result['total_par_assets']):,.2f}")
    logger.info(f"Coverage: {float(result['total_par_assets']) / float(target_result['target_par_amount']) * 100:.1f}%")
    
    return {
        'asset_count': result['asset_count'],
        'actual_par': float(result['total_par_assets']),
        'target_par': float(target_result['target_par_amount'])
    }

def main():
    """Main migration function"""
    logger.info("Starting MAG11 Inputs Migration...")
    logger.info("=" * 80)
    
    try:
        # Load Excel data
        excel_df = load_mag11_inputs()
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        # Get current database assets
        current_assets = get_current_mag11_assets(conn)
        
        # Analyze differences
        analysis = analyze_differences(excel_df, current_assets)
        
        # Update existing assets with new par amounts
        updates_made = update_existing_assets(conn, excel_df, current_assets, analysis['common_ids'])
        
        # Report on missing assets
        missing_assets, missing_par_total = create_missing_assets_report(excel_df, analysis['excel_only_ids'])
        
        # Verify final results
        final_results = verify_final_results(conn)
        
        # Summary
        logger.info("\nMIGRATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"✅ Assets updated: {updates_made}")
        logger.info(f"⚠️  Assets missing: {len(missing_assets)} (${missing_par_total:,.2f})")
        logger.info(f"📊 Final coverage: {final_results['actual_par'] / final_results['target_par'] * 100:.1f}%")
        
        if missing_assets:
            logger.info(f"\n📋 NOTE: {len(missing_assets)} assets from Excel are missing from database")
            logger.info("These assets require complete data (issuer, rating, maturity, etc.) to be added")
            logger.info("Consider using the master 'All Assets' worksheet to find complete details")
        
        logger.info(f"\n✅ MAG11 migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()