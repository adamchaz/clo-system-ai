#!/usr/bin/env python3
"""
Run MAG17 Concentration Thresholds Migration
"""

import psycopg2
from app.core.config import settings

def run_migration():
    print('=== Running MAG17 Concentration Thresholds Migration ===')
    
    # Connect to PostgreSQL using correct settings
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            port=settings.postgres_port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute the fixed migration
        with open('migrations/004_fixed_mag17_thresholds.sql', 'r') as f:
            migration_sql = f.read()
        
        print('Executing migration...')
        cursor.execute(migration_sql)
        
        print('Migration completed successfully!')
        print()
        
        # Fetch validation results
        cursor.execute('''
            SELECT 
                test_category,
                COUNT(*) as test_count,
                COUNT(CASE WHEN default_threshold IS NOT NULL THEN 1 END) as with_thresholds
            FROM concentration_test_definitions 
            GROUP BY test_category
            ORDER BY test_category;
        ''')
        
        print('=== Test Definitions by Category ===')
        for row in cursor.fetchall():
            print(f'{row[0]}: {row[1]} tests ({row[2]} with thresholds)')
        
        print()
        
        # Check MAG17 overrides
        cursor.execute('''
            SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = 'MAG17';
        ''')
        mag17_count = cursor.fetchone()[0]
        print(f'MAG17 threshold overrides: {mag17_count}')
        
        # Show key MAG17 thresholds
        cursor.execute('''
            SELECT 
                ctd.test_number,
                ctd.test_name,
                ctd.default_threshold,
                dct.threshold_value as mag17_override
            FROM concentration_test_definitions ctd
            LEFT JOIN deal_concentration_thresholds dct ON ctd.test_id = dct.test_id AND dct.deal_id = 'MAG17'
            WHERE dct.deal_id = 'MAG17' AND ctd.test_number IN (1, 2, 7, 15, 30, 91)
            ORDER BY ctd.test_number;
        ''')
        
        print()
        print('=== Key MAG17 Thresholds ===')
        for row in cursor.fetchall():
            test_name = row[1][:40] + "..." if len(row[1]) > 40 else row[1]
            threshold_pct = row[3] * 100 if row[3] is not None else 0
            print(f'Test {row[0]}: {test_name} = {threshold_pct:.1f}%')
        
        # Test the Senior Secured Loans threshold specifically
        cursor.execute('''
            SELECT 
                ctd.test_name,
                dct.threshold_value
            FROM concentration_test_definitions ctd
            JOIN deal_concentration_thresholds dct ON ctd.test_id = dct.test_id
            WHERE ctd.test_number = 1 AND dct.deal_id = 'MAG17';
        ''')
        
        result = cursor.fetchone()
        if result:
            print()
            print('=== CRITICAL FIX VERIFICATION ===')
            print(f'Senior Secured Loans threshold: {result[1]*100:.1f}% (VBA requirement: 90%)')
            if abs(result[1] - 0.9) < 0.0001:
                print('SUCCESS: Senior Secured Loans threshold correctly set to 90%')
            else:
                print('ERROR: Senior Secured Loans threshold is incorrect')
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Migration failed: {e}')
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print()
        print('=== NEXT STEPS ===')
        print('1. Update concentration test engine to use database thresholds')
        print('2. Test MAG17 concentration calculations')
        print('3. Verify all threshold overrides are working correctly')
    else:
        print('Migration failed - check database connection and permissions')