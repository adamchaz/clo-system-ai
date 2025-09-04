#!/usr/bin/env python3
"""
Implement the recommended tranche table actions:
1. Drop empty liabilities table
2. Migrate MAG16's 7 tranches to clo_tranches
3. Verify migration
"""

from app.core.database_config import db_config
from sqlalchemy import text
from datetime import datetime

def step1_drop_liabilities_table():
    """Drop the empty liabilities table"""
    
    print("STEP 1: Dropping empty liabilities table")
    print("-" * 50)
    
    try:
        with db_config.get_db_session('postgresql') as db:
            # First verify it's empty
            count_result = db.execute(text("SELECT COUNT(*) FROM liabilities"))
            count = count_result.fetchone()[0]
            
            print(f"Current records in liabilities table: {count}")
            
            if count > 0:
                print("WARNING: Liabilities table is not empty!")
                print("Skipping deletion for safety")
                return False
            
            # Check for foreign key constraints
            fk_check = db.execute(text('''
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND ccu.table_name = 'liabilities'
            '''))
            
            fk_constraints = fk_check.fetchall()
            if fk_constraints:
                print(f"Found {len(fk_constraints)} foreign key constraints referencing liabilities")
                for fk in fk_constraints:
                    print(f"  {fk.table_name}.{fk.column_name}")
                print("Would need to drop constraints first")
            
            # Drop the table
            print("Dropping liabilities table...")
            db.execute(text("DROP TABLE IF EXISTS liabilities CASCADE"))
            db.commit()
            
            print("SUCCESS: Liabilities table dropped")
            return True
            
    except Exception as e:
        print(f"Error dropping liabilities table: {e}")
        import traceback
        traceback.print_exc()
        return False

def step2_migrate_mag16_tranches():
    """Migrate MAG16's 7 tranches to clo_tranches table"""
    
    print("\nSTEP 2: Migrating MAG16 tranches to clo_tranches")
    print("-" * 50)
    
    # MAG16 tranche data from Excel analysis
    mag16_tranches = [
        {
            'tranche_name': 'Class A',
            'initial_balance': 320000000,
            'current_balance': 320000000,
            'coupon_rate': 0.015,  # 150 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.015,
            'seniority_level': 1,
            'payment_rank': 1,
            'interest_deferrable': False
        },
        {
            'tranche_name': 'Class B',
            'initial_balance': 60000000,
            'current_balance': 60000000,
            'coupon_rate': 0.0225,  # 225 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.0225,
            'seniority_level': 2,
            'payment_rank': 2,
            'interest_deferrable': False
        },
        {
            'tranche_name': 'Class C-1',
            'initial_balance': 11579000,
            'current_balance': 11579000,
            'coupon_rate': 0.031,  # 310 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.031,
            'seniority_level': 3,
            'payment_rank': 3,
            'interest_deferrable': True  # PIK
        },
        {
            'tranche_name': 'Class C-2',
            'initial_balance': 18171000,
            'current_balance': 18171000,
            'coupon_rate': 0.030,  # 300 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.030,
            'seniority_level': 4,
            'payment_rank': 4,
            'interest_deferrable': True  # PIK
        },
        {
            'tranche_name': 'Class D',
            'initial_balance': 25250000,
            'current_balance': 25250000,
            'coupon_rate': 0.0405,  # 405 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.0405,
            'seniority_level': 5,
            'payment_rank': 5,
            'interest_deferrable': True  # PIK
        },
        {
            'tranche_name': 'Class E',
            'initial_balance': 25000000,
            'current_balance': 25000000,
            'coupon_rate': 0.0635,  # 635 bps
            'coupon_type': 'Floating',
            'index_name': 'LIBOR',
            'margin': 0.0635,
            'seniority_level': 6,
            'payment_rank': 6,
            'interest_deferrable': True  # PIK
        },
        {
            'tranche_name': 'Sub Notes (Equity)',
            'initial_balance': 46500000,
            'current_balance': 46500000,
            'coupon_rate': None,  # Variable/residual
            'coupon_type': 'Variable',
            'index_name': None,
            'margin': None,
            'seniority_level': 7,
            'payment_rank': 7,
            'interest_deferrable': True
        }
    ]
    
    try:
        with db_config.get_db_session('postgresql') as db:
            # Check if MAG16 tranches already exist
            existing_check = db.execute(text('''
                SELECT COUNT(*) FROM clo_tranches WHERE deal_id = 'MAG16'
            '''))
            existing_count = existing_check.fetchone()[0]
            
            if existing_count > 0:
                print(f"Found {existing_count} existing MAG16 tranches")
                print("Removing existing MAG16 tranches first...")
                db.execute(text("DELETE FROM clo_tranches WHERE deal_id = 'MAG16'"))
            
            # Insert new tranches
            print(f"Inserting {len(mag16_tranches)} MAG16 tranches...")
            
            created_count = 0
            for i, tranche in enumerate(mag16_tranches):
                tranche_id = f"MAG16_T{i+1:02d}"
                
                db.execute(text('''
                    INSERT INTO clo_tranches (
                        tranche_id, deal_id, tranche_name,
                        initial_balance, current_balance,
                        coupon_rate, coupon_type, index_name, margin,
                        seniority_level, payment_rank, interest_deferrable,
                        created_at
                    ) VALUES (
                        :tranche_id, :deal_id, :tranche_name,
                        :initial_balance, :current_balance,
                        :coupon_rate, :coupon_type, :index_name, :margin,
                        :seniority_level, :payment_rank, :interest_deferrable,
                        :created_at
                    )
                '''), {
                    'tranche_id': tranche_id,
                    'deal_id': 'MAG16',
                    'tranche_name': tranche['tranche_name'],
                    'initial_balance': tranche['initial_balance'],
                    'current_balance': tranche['current_balance'],
                    'coupon_rate': tranche['coupon_rate'],
                    'coupon_type': tranche['coupon_type'],
                    'index_name': tranche['index_name'],
                    'margin': tranche['margin'],
                    'seniority_level': tranche['seniority_level'],
                    'payment_rank': tranche['payment_rank'],
                    'interest_deferrable': tranche['interest_deferrable'],
                    'created_at': datetime.now()
                })
                
                created_count += 1
                print(f"  Created: {tranche['tranche_name']} (${tranche['initial_balance']:,})")
            
            db.commit()
            print(f"SUCCESS: {created_count} MAG16 tranches migrated")
            return True
            
    except Exception as e:
        print(f"Error migrating MAG16 tranches: {e}")
        import traceback
        traceback.print_exc()
        return False

def step3_verify_migration():
    """Verify the tranche migration completed successfully"""
    
    print("\nSTEP 3: Verifying migration")
    print("-" * 50)
    
    try:
        with db_config.get_db_session('postgresql') as db:
            # Check if liabilities table is gone
            table_check = db.execute(text('''
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'liabilities'
            '''))
            liabilities_exists = table_check.fetchone()[0] > 0
            
            print(f"Liabilities table exists: {'YES - FAILED' if liabilities_exists else 'NO - SUCCESS'}")
            
            # Check MAG16 tranches
            mag16_check = db.execute(text('''
                SELECT tranche_name, initial_balance, coupon_rate, seniority_level
                FROM clo_tranches 
                WHERE deal_id = 'MAG16'
                ORDER BY payment_rank
            '''))
            
            mag16_tranches = mag16_check.fetchall()
            print(f"\nMAG16 tranches in database: {len(mag16_tranches)}")
            
            total_balance = 0
            for tranche in mag16_tranches:
                balance = float(tranche.initial_balance)
                total_balance += balance
                coupon = f"{float(tranche.coupon_rate)*100:.2f}%" if tranche.coupon_rate else "Variable"
                print(f"  {tranche.tranche_name:<20} ${balance:>12,.0f}  {coupon:>8}  Level {tranche.seniority_level}")
            
            print(f"Total deal size: ${total_balance:,.0f}")
            
            # Check total records in clo_tranches
            total_check = db.execute(text("SELECT COUNT(*) FROM clo_tranches"))
            total_tranches = total_check.fetchone()[0]
            print(f"Total tranches in system: {total_tranches}")
            
            success = not liabilities_exists and len(mag16_tranches) == 7
            print(f"\nVERIFICATION: {'SUCCESS' if success else 'ISSUES FOUND'}")
            
            return success
            
    except Exception as e:
        print(f"Error verifying migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Execute all recommended actions"""
    
    print("Implementing Tranche Table Recommendations")
    print("=" * 60)
    
    success_count = 0
    
    # Step 1: Drop liabilities table
    if step1_drop_liabilities_table():
        success_count += 1
    
    # Step 2: Migrate MAG16 tranches
    if step2_migrate_mag16_tranches():
        success_count += 1
    
    # Step 3: Verify migration
    if step3_verify_migration():
        success_count += 1
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Completed steps: {success_count}/3")
    
    if success_count == 3:
        print("SUCCESS: All recommendations implemented successfully!")
        print("- Empty liabilities table dropped")
        print("- MAG16 tranches migrated to clo_tranches")
        print("- Migration verified")
    else:
        print("PARTIAL SUCCESS: Some issues encountered")
        print("Check logs above for details")

if __name__ == "__main__":
    main()