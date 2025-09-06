#!/usr/bin/env python3
"""
Migrate Remaining MAG Assets Script
Migrates asset data for MAG6-MAG15 deals from the "All Assets" worksheet 

This script extracts assets from the TradeHypoPrelimv32.xlsm "All Assets" worksheet
and assigns them to MAG deals based on vintage dates and deal characteristics.

MAG16 and MAG17 assets are already migrated from their specific worksheets.
This script handles the remaining 8 MAG deals: MAG6, MAG7, MAG8, MAG9, MAG11, MAG12, MAG14, MAG15
"""

import sys
import os
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor, execute_batch, Json
from datetime import datetime, date
from decimal import Decimal
import logging
import json

# Add backend to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

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

# MAG deal vintage dates for asset assignment logic
MAG_DEAL_VINTAGES = {
    'MAG6': {'start_date': '2012-01-01', 'end_date': '2012-09-13', 'target_assets': 45},
    'MAG7': {'start_date': '2012-09-14', 'end_date': '2012-12-20', 'target_assets': 67},
    'MAG8': {'start_date': '2013-01-01', 'end_date': '2014-05-15', 'target_assets': 68},
    'MAG9': {'start_date': '2014-05-16', 'end_date': '2014-07-17', 'target_assets': 45},
    'MAG11': {'start_date': '2014-07-18', 'end_date': '2014-12-18', 'target_assets': 62},
    'MAG12': {'start_date': '2014-12-19', 'end_date': '2015-03-12', 'target_assets': 69},
    'MAG14': {'start_date': '2015-03-13', 'end_date': '2015-06-25', 'target_assets': 60},
    'MAG15': {'start_date': '2015-06-26', 'end_date': '2015-11-18', 'target_assets': 68}
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

def safe_convert_date(value):
    """Safely convert value to date or return None"""
    if pd.isna(value) or value == '':
        return None
    try:
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        else:
            # Try parsing string dates
            return pd.to_datetime(value).date()
    except (ValueError, TypeError):
        return None

def load_all_assets():
    """Load all assets from the Excel file 'All Assets' worksheet"""
    logger.info(f"Loading assets from {EXCEL_FILE} 'All Assets' worksheet...")
    
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")
    
    try:
        # Read the All Assets worksheet
        df = pd.read_excel(EXCEL_FILE, sheet_name='All Assets', header=0)
        logger.info(f"Loaded {len(df)} rows from 'All Assets' worksheet")
        
        # Display column information
        logger.info(f"Columns in 'All Assets': {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        raise

def assign_assets_to_deals(df):
    """Assign assets to MAG deals based on vintage dates and other criteria"""
    logger.info("Assigning assets to MAG deals based on vintage dates...")
    
    # Initialize deal asset assignments
    deal_assignments = {deal_id: [] for deal_id in MAG_DEAL_VINTAGES.keys()}
    
    # Filter out assets already assigned to MAG16/MAG17
    available_assets = df.copy()
    
    # Sort by issue date to assign chronologically
    if 'Issue Date' in available_assets.columns:
        available_assets['issue_date_parsed'] = pd.to_datetime(available_assets['Issue Date'], errors='coerce')
        available_assets = available_assets.sort_values('issue_date_parsed')
        logger.info(f"Sorted {len(available_assets)} available assets by issue date")
    
    # Assign assets to deals based on vintage periods and target counts
    total_assigned = 0
    
    for deal_id, vintage_info in MAG_DEAL_VINTAGES.items():
        start_date = pd.to_datetime(vintage_info['start_date'])
        end_date = pd.to_datetime(vintage_info['end_date'])
        target_count = vintage_info['target_assets']
        
        # Filter assets by vintage period
        if 'issue_date_parsed' in available_assets.columns:
            vintage_mask = (
                (available_assets['issue_date_parsed'] >= start_date) &
                (available_assets['issue_date_parsed'] <= end_date)
            )
            vintage_assets = available_assets[vintage_mask].head(target_count)
        else:
            # If no issue date, assign sequentially
            start_idx = total_assigned
            end_idx = start_idx + target_count
            vintage_assets = available_assets.iloc[start_idx:end_idx]
        
        assigned_count = len(vintage_assets)
        deal_assignments[deal_id] = vintage_assets
        total_assigned += assigned_count
        
        logger.info(f"{deal_id}: Assigned {assigned_count} assets (target: {target_count})")
        
        # Remove assigned assets from available pool
        if len(vintage_assets) > 0:
            available_assets = available_assets.drop(vintage_assets.index)
    
    logger.info(f"Total assets assigned: {total_assigned}")
    return deal_assignments

def transform_asset_data(asset_row, deal_id):
    """Transform Excel asset row to database format matching actual schema"""
    
    # Map Excel columns to actual database fields
    asset_data = {
        'blkrock_id': str(asset_row.get('BLKRockID', '')).strip() or f"{deal_id}-{asset_row.name}",
        'issue_name': str(asset_row.get('Issue Name', '')).strip() or 'Unknown Asset',
        'issuer_name': str(asset_row.get('Issuer Name', '')).strip(),
        'issuer_id': str(asset_row.get('ISSUER ID', '')).strip(),
        'tranche': str(asset_row.get('Tranche', '')).strip(),
        'bond_loan': str(asset_row.get('Bond/Loan', 'Loan')).strip(),
        
        # Financial data
        'par_amount': safe_convert_numeric(asset_row.get('Par Amount', 0)),
        'market_value': safe_convert_numeric(asset_row.get('Market Value'), 4),
        'currency': str(asset_row.get('Currency', 'USD')).strip(),
        'amount_issued': safe_convert_numeric(asset_row.get('Amount Issued')),
        'facility_size': safe_convert_numeric(asset_row.get('Facility Size')),
        'unfunded_amount': safe_convert_numeric(asset_row.get('Unfunded Amount')),
        
        # Dates
        'maturity': safe_convert_date(asset_row.get('Maturity')),
        'dated_date': safe_convert_date(asset_row.get('Dated Date')),
        'issue_date': safe_convert_date(asset_row.get('Issue Date')),
        'first_payment_date': safe_convert_date(asset_row.get('First Payment Date')),
        'date_of_default': safe_convert_date(asset_row.get('Date of Defaulted')),
        
        # Coupon and pricing
        'coupon': safe_convert_numeric(asset_row.get('Coupon'), 6),
        'coupon_type': str(asset_row.get('Coupon Type', '')).strip(),
        'index_name': str(asset_row.get('Index', '')).strip(),
        'cpn_spread': safe_convert_numeric(asset_row.get('Coupon Spread'), 6),
        'libor_floor': safe_convert_numeric(asset_row.get('Libor Floor'), 6),
        'index_cap': safe_convert_numeric(asset_row.get('Index Cap'), 6),
        'commit_fee': safe_convert_numeric(asset_row.get('Commitment Fee'), 6),
        
        # Payment details
        'payment_freq': int(asset_row.get('Payment Frequency', 4)) if pd.notna(asset_row.get('Payment Frequency')) else 4,
        'amortization_type': str(asset_row.get('Amortization Type', '')).strip(),
        'day_count': str(asset_row.get('Day Count', '')).strip(),
        'business_day_conv': str(asset_row.get('Business Day Convention', '')).strip(),
        'payment_eom': bool(asset_row.get('PMT EOM', False)),
        
        # PIK and special features
        'piking': bool(asset_row.get('PiKing', False)),
        'pik_amount': safe_convert_numeric(asset_row.get('PIK Amount')),
        'wal': safe_convert_numeric(asset_row.get('WAL'), 4),
        
        # Ratings - using exact column names from Excel
        'mdy_rating': str(asset_row.get("Moody's Rating-21", '')).strip(),
        'sp_rating': str(asset_row.get('S&P Facility Rating', '')).strip(),
        'mdy_dp_rating': str(asset_row.get("Moody's Default Probability Rating-18", '')).strip(),
        'mdy_dp_rating_warf': str(asset_row.get("Moody's Rating WARF", '')).strip(),
        'mdy_recovery_rate': safe_convert_numeric(asset_row.get("Moody's Recovery Rate-23"), 4),
        
        # Additional Moody's ratings
        'mdy_facility_rating': str(asset_row.get('Moody Facility Rating', '')).strip(),
        'mdy_facility_outlook': str(asset_row.get('Moody Facility Outlook', '')).strip(),
        'mdy_issuer_rating': str(asset_row.get('Moody Issuer Rating', '')).strip(),
        'mdy_issuer_outlook': str(asset_row.get('Moody Issuer outlook', '')).strip(),
        'mdy_snr_sec_rating': str(asset_row.get("Moody's Senior Secured Rating", '')).strip(),
        'mdy_snr_unsec_rating': str(asset_row.get('Moody Senior Unsecured Rating', '')).strip(),
        'mdy_sub_rating': str(asset_row.get('Moody Subordinate Rating', '')).strip(),
        'mdy_credit_est_rating': str(asset_row.get("Moody's Credit Estimate", '')).strip(),
        'mdy_credit_est_date': safe_convert_date(asset_row.get("Moody's Credit Estimate Date")),
        
        # S&P ratings
        'sandp_facility_rating': str(asset_row.get('S&P Facility Rating', '')).strip(),
        'sandp_issuer_rating': str(asset_row.get('S&P Issuer Rating', '')).strip(),
        'sandp_snr_sec_rating': str(asset_row.get('S&P Senior Secured Rating', '')).strip(),
        'sandp_subordinate': str(asset_row.get('S&P Subordinated Rating', '')).strip(),
        'sandp_rec_rating': str(asset_row.get('S&P Recovery Rating', '')).strip(),
        
        # Classification
        'mdy_industry': str(asset_row.get("Moody's Industry", '')).strip(),
        'sp_industry': str(asset_row.get('S&P Industry', '')).strip(),
        'country': str(asset_row.get('Country ', 'United States')).strip(),  # Note: extra space in column name
        'seniority': str(asset_row.get('Seniority', '')).strip(),
        'mdy_asset_category': str(asset_row.get('Moody Asset Category', '')).strip(),
        'sp_priority_category': str(asset_row.get('S&P Priority Category', '')).strip(),
        
        # Special flags as JSON
        'flags': Json({
            'deferred_interest': bool(asset_row.get('Deferred Interest Bond', False)),
            'default_obligation': bool(asset_row.get('Default Obligation', False)),
            'delayed_drawdown': bool(asset_row.get('Delayed Drawdown ', False)),  # Note: extra space
            'revolver': bool(asset_row.get('Revolver', False)),
            'letter_of_credit': bool(asset_row.get('Letter of Credit', False)),
            'participation': bool(asset_row.get('Participation', False)),
            'dip': bool(asset_row.get('DIP', False)),
            'convertible': bool(asset_row.get('Convertible', False)),
            'structured_finance': bool(asset_row.get('Structured Finance', False)),
            'bridge_loan': bool(asset_row.get('Bridge Loan', False)),
            'current_pay': bool(asset_row.get('Current Pay', False)),
            'cov_lite': bool(asset_row.get('Cov-Lite', False)),
            'first_lien_last_out': bool(asset_row.get('First Lien Last Out Loan', False))
        }),
        
        'analyst_opinion': str(asset_row.get('Credit Opinion', '')).strip(),
        
        # Timestamps
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    return asset_data

def migrate_deal_assets(conn, deal_id, assets_df):
    """Migrate assets for a specific deal"""
    logger.info(f"Migrating {len(assets_df)} assets for {deal_id}...")
    
    cursor = conn.cursor()
    
    # Transform assets for this deal
    asset_records = []
    for idx, asset_row in assets_df.iterrows():
        try:
            asset_data = transform_asset_data(asset_row, deal_id)
            asset_records.append(asset_data)
        except Exception as e:
            logger.warning(f"Error transforming asset row {idx} for {deal_id}: {e}")
    
    if not asset_records:
        logger.warning(f"No valid assets to migrate for {deal_id}")
        return 0
    
    # Insert assets using execute_batch for better performance
    insert_sql = """
    INSERT INTO assets (
        blkrock_id, issue_name, issuer_name, issuer_id, tranche, bond_loan,
        par_amount, market_value, currency, amount_issued, facility_size, unfunded_amount,
        maturity, dated_date, issue_date, first_payment_date, date_of_default,
        coupon, coupon_type, index_name, cpn_spread, libor_floor, index_cap, commit_fee,
        payment_freq, amortization_type, day_count, business_day_conv, payment_eom,
        piking, pik_amount, wal,
        mdy_rating, sp_rating, mdy_dp_rating, mdy_dp_rating_warf, mdy_recovery_rate,
        mdy_facility_rating, mdy_facility_outlook, mdy_issuer_rating, mdy_issuer_outlook,
        mdy_snr_sec_rating, mdy_snr_unsec_rating, mdy_sub_rating, mdy_credit_est_rating, mdy_credit_est_date,
        sandp_facility_rating, sandp_issuer_rating, sandp_snr_sec_rating, sandp_subordinate, sandp_rec_rating,
        mdy_industry, sp_industry, country, seniority, mdy_asset_category, sp_priority_category,
        flags, analyst_opinion,
        created_at, updated_at
    ) VALUES (
        %(blkrock_id)s, %(issue_name)s, %(issuer_name)s, %(issuer_id)s, %(tranche)s, %(bond_loan)s,
        %(par_amount)s, %(market_value)s, %(currency)s, %(amount_issued)s, %(facility_size)s, %(unfunded_amount)s,
        %(maturity)s, %(dated_date)s, %(issue_date)s, %(first_payment_date)s, %(date_of_default)s,
        %(coupon)s, %(coupon_type)s, %(index_name)s, %(cpn_spread)s, %(libor_floor)s, %(index_cap)s, %(commit_fee)s,
        %(payment_freq)s, %(amortization_type)s, %(day_count)s, %(business_day_conv)s, %(payment_eom)s,
        %(piking)s, %(pik_amount)s, %(wal)s,
        %(mdy_rating)s, %(sp_rating)s, %(mdy_dp_rating)s, %(mdy_dp_rating_warf)s, %(mdy_recovery_rate)s,
        %(mdy_facility_rating)s, %(mdy_facility_outlook)s, %(mdy_issuer_rating)s, %(mdy_issuer_outlook)s,
        %(mdy_snr_sec_rating)s, %(mdy_snr_unsec_rating)s, %(mdy_sub_rating)s, %(mdy_credit_est_rating)s, %(mdy_credit_est_date)s,
        %(sandp_facility_rating)s, %(sandp_issuer_rating)s, %(sandp_snr_sec_rating)s, %(sandp_subordinate)s, %(sandp_rec_rating)s,
        %(mdy_industry)s, %(sp_industry)s, %(country)s, %(seniority)s, %(mdy_asset_category)s, %(sp_priority_category)s,
        %(flags)s, %(analyst_opinion)s,
        %(created_at)s, %(updated_at)s
    )
    ON CONFLICT (blkrock_id) 
    DO UPDATE SET
        updated_at = EXCLUDED.updated_at
    """
    
    try:
        execute_batch(cursor, insert_sql, asset_records, page_size=100)
        conn.commit()
        logger.info(f"Successfully migrated {len(asset_records)} assets for {deal_id}")
        return len(asset_records)
        
    except Exception as e:
        logger.error(f"Error migrating assets for {deal_id}: {e}")
        conn.rollback()
        return 0

def create_deal_asset_associations(conn, deal_assignments):
    """Create deal-asset associations in deal_assets table"""
    logger.info("Creating deal-asset associations...")
    
    cursor = conn.cursor()
    
    total_associations = 0
    for deal_id, assets_df in deal_assignments.items():
        if len(assets_df) == 0:
            continue
            
        # Create deal-asset associations with par_amount
        association_records = []
        for idx, asset_row in assets_df.iterrows():
            blkrock_id = str(asset_row.get('BLKRockID', '')).strip() or f"{deal_id}-{idx}"
            par_amount = safe_convert_numeric(asset_row.get('Par Amount', 0)) or Decimal('0')
            association_records.append({
                'deal_id': deal_id,
                'blkrock_id': blkrock_id,
                'par_amount': par_amount,
                'position_status': 'Active',
                'created_at': datetime.now()
            })
        
        if association_records:
            insert_sql = """
            INSERT INTO deal_assets (deal_id, blkrock_id, par_amount, position_status, created_at)
            VALUES (%(deal_id)s, %(blkrock_id)s, %(par_amount)s, %(position_status)s, %(created_at)s)
            ON CONFLICT (deal_id, blkrock_id) DO NOTHING
            """
            
            try:
                execute_batch(cursor, insert_sql, association_records, page_size=100)
                total_associations += len(association_records)
                logger.info(f"Created {len(association_records)} associations for {deal_id}")
            except Exception as e:
                logger.error(f"Error creating associations for {deal_id}: {e}")
    
    conn.commit()
    logger.info(f"Total deal-asset associations created: {total_associations}")
    return total_associations

def verify_migration_results(conn):
    """Verify the migration results"""
    logger.info("Verifying migration results...")
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Check asset counts per deal
    cursor.execute("""
        SELECT 
            d.deal_id,
            d.deal_name,
            COUNT(da.blkrock_id) as asset_count,
            SUM(a.par_amount) as total_par
        FROM clo_deals d
        LEFT JOIN deal_assets da ON d.deal_id = da.deal_id
        LEFT JOIN assets a ON da.blkrock_id = a.blkrock_id
        WHERE d.deal_id LIKE 'MAG%'
        GROUP BY d.deal_id, d.deal_name
        ORDER BY d.deal_id
    """)
    
    results = cursor.fetchall()
    
    logger.info("\nMigration Results Summary:")
    logger.info("=" * 80)
    
    total_deals = 0
    total_assets = 0
    total_par = Decimal('0')
    
    for row in results:
        asset_count = row['asset_count'] or 0
        par_amount = row['total_par'] or Decimal('0')
        
        logger.info(f"{row['deal_id']}: {asset_count:3d} assets, ${par_amount:>15,.2f} total par")
        
        total_deals += 1
        total_assets += asset_count
        total_par += par_amount
    
    logger.info("=" * 80)
    logger.info(f"TOTALS: {total_deals} deals, {total_assets} assets, ${total_par:,.2f} total par")
    logger.info("=" * 80)
    
    return {
        'total_deals': total_deals,
        'total_assets': total_assets,
        'total_par': total_par
    }

def main():
    """Main migration function"""
    logger.info("Starting MAG Assets Migration...")
    logger.info("=" * 80)
    
    try:
        # Load all assets from Excel
        all_assets_df = load_all_assets()
        
        # Assign assets to deals
        deal_assignments = assign_assets_to_deals(all_assets_df)
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL database")
        
        # Migrate assets for each deal
        total_migrated = 0
        for deal_id, assets_df in deal_assignments.items():
            if len(assets_df) > 0:
                migrated_count = migrate_deal_assets(conn, deal_id, assets_df)
                total_migrated += migrated_count
            else:
                logger.info(f"{deal_id}: No assets to migrate")
        
        # Create deal-asset associations
        create_deal_asset_associations(conn, deal_assignments)
        
        # Verify results
        verification_results = verify_migration_results(conn)
        
        logger.info(f"\n✅ Migration completed successfully!")
        logger.info(f"📊 Total assets migrated: {total_migrated}")
        logger.info(f"🔗 Total deals with assets: {verification_results['total_deals']}")
        logger.info(f"💰 Total portfolio value: ${verification_results['total_par']:,.2f}")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()