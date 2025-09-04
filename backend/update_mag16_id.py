#!/usr/bin/env python3
"""
Update MAG16-001 deal_id to MAG16 for clean URL
"""

from app.core.database_config import db_config
from sqlalchemy import text

def update_mag16_id():
    try:
        with db_config.get_db_session('postgresql') as db:
            # Check current state
            print('Current MAG16 records:')
            result = db.execute(text('''
                SELECT deal_id, deal_name, effective_date, target_par_amount
                FROM clo_deals 
                WHERE deal_id LIKE '%MAG16%'
                ORDER BY deal_id
            '''))
            
            records = result.fetchall()
            for record in records:
                print(f'  {record.deal_id}: {record.deal_name} | Effective: {record.effective_date}')
            
            # Check for foreign key dependencies
            print('\nChecking foreign key dependencies...')
            
            # Check deal_assets
            assets_check = db.execute(text('''
                SELECT COUNT(*) as count FROM deal_assets WHERE deal_id = 'MAG16-001'
            '''))
            assets_count = assets_check.fetchone().count
            print(f'  deal_assets: {assets_count} records')
            
            # Check deal_concentration_thresholds
            try:
                thresholds_check = db.execute(text('''
                    SELECT COUNT(*) as count FROM deal_concentration_thresholds WHERE deal_id = 'MAG16-001'
                '''))
                thresholds_count = thresholds_check.fetchone().count
                print(f'  deal_concentration_thresholds: {thresholds_count} records')
            except:
                print('  deal_concentration_thresholds: table not found or no records')
                thresholds_count = 0
            
            # Update foreign key references first
            if assets_count > 0:
                print('\nUpdating deal_assets references...')
                assets_update = db.execute(text('''
                    UPDATE deal_assets 
                    SET deal_id = 'MAG16'
                    WHERE deal_id = 'MAG16-001'
                '''))
                print(f'Updated {assets_update.rowcount} deal_assets record(s)')
            
            if thresholds_count > 0:
                print('Updating deal_concentration_thresholds references...')
                thresholds_update = db.execute(text('''
                    UPDATE deal_concentration_thresholds 
                    SET deal_id = 'MAG16'
                    WHERE deal_id = 'MAG16-001'
                '''))
                print(f'Updated {thresholds_update.rowcount} threshold record(s)')
            
            # Now update the main deal_id
            print('Updating deal_id from MAG16-001 to MAG16...')
            update_result = db.execute(text('''
                UPDATE clo_deals 
                SET deal_id = 'MAG16',
                    updated_at = CURRENT_TIMESTAMP
                WHERE deal_id = 'MAG16-001'
            '''))
            print(f'Updated {update_result.rowcount} clo_deals record(s)')
            
            # Commit changes
            db.commit()
            
            # Verify final state
            print('\nFinal state:')
            verify_result = db.execute(text('''
                SELECT deal_id, deal_name, effective_date, target_par_amount
                FROM clo_deals 
                WHERE deal_id = 'MAG16'
                ORDER BY deal_id
            '''))
            
            final_records = verify_result.fetchall()
            for record in final_records:
                print(f'  {record.deal_id}: {record.deal_name} | Effective: {record.effective_date} | Par: ${record.target_par_amount:,.0f}')
                
            print('\nURL will now be: http://localhost:3002/portfolios/MAG16')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_mag16_id()