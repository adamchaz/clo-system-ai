#!/usr/bin/env python3
"""
MAG17 Asset Data Migration Script
Migrates detailed MAG17 asset data from extracted JSON files to PostgreSQL
"""

import json
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, date
from decimal import Decimal
import sys
import os

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'database': 'clo_dev',
    'user': 'postgres',
    'password': 'adamchaz'
}

def load_json_data(file_path):
    """Load data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def convert_value(value):
    """Convert values for database insertion"""
    if value is None or value == "":
        return None
    elif isinstance(value, str):
        if value.lower() in ['null', 'none', '']:
            return None
        return value.strip()
    elif isinstance(value, (int, float)):
        return value
    else:
        return str(value)

def migrate_mag17_assets():
    """Migrate MAG17 asset data to PostgreSQL"""
    
    # Load asset data
    print("Loading MAG17 asset data...")
    asset_data = load_json_data("../mag17_assets_complete.json")
    
    if not asset_data:
        print("Failed to load MAG17 asset data")
        return False
    
    print(f"Loaded {len(asset_data)} MAG17 assets")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check if assets table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'assets'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Assets table does not exist. Creating table...")
            create_assets_table(cursor)
        
        # Prepare insert statement for assets (using actual database schema)
        insert_sql = """
        INSERT INTO assets (
            blkrock_id, issue_name, issuer_name, issuer_id, tranche, bond_loan,
            par_amount, market_value, currency, maturity, issue_date,
            coupon, coupon_type, cpn_spread, libor_floor, payment_freq,
            unfunded_amount, mdy_rating, sp_rating, mdy_recovery_rate,
            mdy_industry, sp_industry, country, seniority, facility_size,
            wal, created_at, updated_at
        ) VALUES (
            %(blkrock_id)s, %(issue_name)s, %(issuer_name)s, %(issuer_id)s, %(tranche)s, %(bond_loan)s,
            %(par_amount)s, %(market_value)s, %(currency)s, %(maturity)s, %(issue_date)s,
            %(coupon)s, %(coupon_type)s, %(cpn_spread)s, %(libor_floor)s, %(payment_freq)s,
            %(unfunded_amount)s, %(mdy_rating)s, %(sp_rating)s, %(mdy_recovery_rate)s,
            %(mdy_industry)s, %(sp_industry)s, %(country)s, %(seniority)s, %(facility_size)s,
            %(wal)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (blkrock_id) 
        DO UPDATE SET
            issue_name = EXCLUDED.issue_name,
            par_amount = EXCLUDED.par_amount,
            market_value = EXCLUDED.market_value,
            updated_at = CURRENT_TIMESTAMP
        """
        
        inserted_count = 0
        skipped_count = 0
        
        for asset in asset_data:
            try:
                # Map asset data to database fields (using actual schema)
                asset_record = {
                    'blkrock_id': convert_value(asset.get('BLKRockID')),
                    'issue_name': convert_value(asset.get('Issue Name')),
                    'issuer_name': convert_value(asset.get('Issuer Name')),
                    'issuer_id': convert_value(asset.get('ISSUER ID')),
                    'tranche': convert_value(asset.get('Tranche')),
                    'bond_loan': convert_value(asset.get('Bond/Loan')),
                    'par_amount': convert_value(asset.get('Par Amount')),
                    'market_value': None,  # Will be calculated
                    'currency': convert_value(asset.get('Currency')),
                    'maturity': convert_value(asset.get('Maturity')),
                    'issue_date': None,  # Not available in this dataset
                    'coupon': convert_value(asset.get('Coupon')),
                    'coupon_type': convert_value(asset.get('Coupon Type')),
                    'cpn_spread': convert_value(asset.get('Coupon Spread')),
                    'libor_floor': convert_value(asset.get('Libor Floor')),
                    'payment_freq': convert_value(asset.get('Payment Frequency')),
                    'unfunded_amount': convert_value(asset.get('Unfunded Amount')),
                    'mdy_rating': convert_value(asset.get("Moody's Rating-21")),
                    'sp_rating': None,  # Not directly available in this dataset
                    'mdy_recovery_rate': convert_value(asset.get("Moody's Recovery Rate-23")),
                    'mdy_industry': convert_value(asset.get("Moody's Industry")),
                    'sp_industry': convert_value(asset.get("S&P Industry")),
                    'country': convert_value(asset.get('Country ')),
                    'seniority': convert_value(asset.get('Seniority')),
                    'facility_size': convert_value(asset.get('Facility Size')),
                    'wal': convert_value(asset.get('WAL'))
                }
                
                # Calculate market value if we have price and par amount
                market_value_raw = convert_value(asset.get('Market Value'))
                par_amount = asset_record.get('par_amount')
                
                if market_value_raw and par_amount:
                    try:
                        price = float(market_value_raw)
                        par = float(par_amount)
                        if price > 0 and par > 0:
                            # Market Value appears to be a price (like 99.292), so calculate actual market value
                            asset_record['market_value'] = (price / 100.0) * par
                    except:
                        pass
                
                # Only insert if we have meaningful data
                if asset_record['issue_name'] or asset_record['issuer_name'] or asset_record['blkrock_id']:
                    cursor.execute(insert_sql, asset_record)
                    inserted_count += 1
                    
                    if inserted_count % 10 == 0:
                        print(f"Processed {inserted_count} assets...")
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error processing asset {asset.get('asset_id', 'unknown')}: {e}")
                skipped_count += 1
                continue
        
        conn.commit()
        
        print(f"\nMAG17 Asset Migration Complete:")
        print(f"  - Successfully inserted: {inserted_count} assets")
        print(f"  - Skipped: {skipped_count} assets")
        
        # Validate insertion - check for MAG17 assets by looking for assets with MAG17-related BLKRockID or issuer
        cursor.execute("""
            SELECT COUNT(*) as count, 
                   SUM(CASE WHEN par_amount IS NOT NULL THEN par_amount ELSE 0 END) as total_par,
                   SUM(CASE WHEN market_value IS NOT NULL THEN market_value ELSE 0 END) as total_market_value
            FROM assets 
            WHERE blkrock_id IS NOT NULL 
            AND (blkrock_id LIKE '%MAG17%' OR issuer_name LIKE '%Magnetar%' OR created_at > NOW() - INTERVAL '5 minutes')
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"  - Total assets in database: {result['count']}")
            if result['total_par']:
                print(f"  - Total par amount: ${result['total_par']:,.2f}")
            if result['total_market_value']:
                print(f"  - Total market value: ${result['total_market_value']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_assets_table(cursor):
    """Create assets table if it doesn't exist"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS assets (
        id SERIAL PRIMARY KEY,
        asset_id VARCHAR(100) UNIQUE NOT NULL,
        deal_id VARCHAR(50) REFERENCES clo_deals(deal_id),
        obligor_name VARCHAR(255),
        issuer_name VARCHAR(255),
        cusip VARCHAR(20),
        bloomberg_id VARCHAR(50),
        outstanding_balance NUMERIC(18,2),
        current_price NUMERIC(12,6),
        market_value NUMERIC(18,2),
        par_amount NUMERIC(18,2),
        coupon_rate NUMERIC(8,6),
        coupon_type VARCHAR(20),
        spread_bps NUMERIC(8,6),
        maturity_date DATE,
        issue_date DATE,
        country VARCHAR(10),
        currency_code VARCHAR(10),
        industry_classification VARCHAR(100),
        seniority_level VARCHAR(50),
        moody_rating VARCHAR(10),
        sp_rating VARCHAR(10),
        fitch_rating VARCHAR(10),
        asset_type VARCHAR(20),
        bond_loan_type VARCHAR(20),
        payment_frequency INTEGER,
        libor_floor NUMERIC(8,6),
        facility_size NUMERIC(18,2),
        unfunded_amount NUMERIC(18,2),
        weighted_avg_life NUMERIC(8,2),
        recovery_rate NUMERIC(6,4),
        default_probability NUMERIC(8,6),
        warf VARCHAR(10),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_assets_deal_id ON assets(deal_id);
    CREATE INDEX IF NOT EXISTS idx_assets_obligor ON assets(obligor_name);
    """
    
    cursor.execute(create_sql)
    print("Created assets table with indexes")

def migrate_mag17_tranches():
    """Migrate MAG17 tranche data"""
    
    print("\nLoading MAG17 tranche data...")
    tranche_data = load_json_data("../mag17_tranches.json")
    
    if not tranche_data:
        print("No tranche data to migrate")
        return True
    
    print(f"Loaded {len(tranche_data)} MAG17 tranches")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check if tranches table exists, create if not
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'clo_tranches'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            create_tranches_table(cursor)
        
        insert_sql = """
        INSERT INTO clo_tranches (
            tranche_id, deal_id, tranche_name, 
            initial_balance, current_balance, margin, 
            seniority_level, payment_rank, created_at
        ) VALUES (
            %(tranche_id)s, %(deal_id)s, %(tranche_name)s,
            %(initial_balance)s, %(current_balance)s, %(margin)s,
            %(seniority_level)s, %(payment_rank)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (tranche_id)
        DO UPDATE SET
            current_balance = EXCLUDED.current_balance
        """
        
        inserted_count = 0
        
        for tranche in tranche_data:
            try:
                props = tranche.get('properties', {})
                
                tranche_record = {
                    'tranche_id': f"MAG17_{tranche.get('class_name', 'UNKNOWN').replace(' ', '_')}",
                    'deal_id': 'MAG17',
                    'tranche_name': tranche.get('class_name'),
                    'initial_balance': convert_value(props.get('Original_Balance')),
                    'current_balance': convert_value(props.get('Current_Balance')),
                    'margin': convert_value(props.get('Spread_bps')),
                    'seniority_level': tranche.get('tranche_number', 999),
                    'payment_rank': tranche.get('tranche_number', 999)
                }
                
                cursor.execute(insert_sql, tranche_record)
                inserted_count += 1
                
            except Exception as e:
                print(f"Error processing tranche {tranche.get('class_name', 'unknown')}: {e}")
                continue
        
        conn.commit()
        print(f"Successfully inserted {inserted_count} MAG17 tranches")
        
        return True
        
    except Exception as e:
        print(f"Tranche migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_tranches_table(cursor):
    """Create tranches table if it doesn't exist"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS clo_tranches (
        id SERIAL PRIMARY KEY,
        tranche_id VARCHAR(100) UNIQUE NOT NULL,
        deal_id VARCHAR(50) REFERENCES clo_deals(deal_id),
        class_name VARCHAR(50),
        tranche_number INTEGER,
        original_balance NUMERIC(18,2),
        current_balance NUMERIC(18,2),
        coupon_rate NUMERIC(8,6),
        spread_bps NUMERIC(8,6),
        rating VARCHAR(10),
        payment_priority INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_tranches_deal_id ON clo_tranches(deal_id);
    """
    
    cursor.execute(create_sql)
    print("Created clo_tranches table")

def main():
    """Main migration execution"""
    print("=" * 60)
    print("MAG17 DETAILED DATA MIGRATION")
    print("=" * 60)
    
    # Migrate assets
    print("\n1. Migrating MAG17 Assets...")
    assets_success = migrate_mag17_assets()
    
    # Migrate tranches
    print("\n2. Migrating MAG17 Tranches...")
    tranches_success = migrate_mag17_tranches()
    
    # Summary
    print("\n" + "=" * 60)
    if assets_success and tranches_success:
        print("MAG17 DETAILED DATA MIGRATION COMPLETED SUCCESSFULLY")
        print("+ Asset data migrated")
        print("+ Tranche data migrated")
        print("+ Database ready for MAG17 analysis")
    else:
        print("MAG17 MIGRATION PARTIALLY COMPLETED")
        if not assets_success:
            print("- Asset migration failed")
        if not tranches_success:
            print("- Tranche migration failed")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())