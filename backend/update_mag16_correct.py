#!/usr/bin/env python3
"""
Update MAG16-001 deal_id to MAG16 with proper foreign key handling
"""

from app.core.database_config import db_config
from sqlalchemy import text

def update_mag16_correct():
    try:
        with db_config.get_db_session('postgresql') as db:
            # Disable foreign key checks temporarily
            print('Temporarily disabling foreign key checks...')
            db.execute(text('SET session_replication_role = replica;'))
            
            # Update the main deal_id first
            print('Updating deal_id from MAG16-001 to MAG16...')
            update_result = db.execute(text('''
                UPDATE clo_deals 
                SET deal_id = 'MAG16',
                    updated_at = CURRENT_TIMESTAMP
                WHERE deal_id = 'MAG16-001'
            '''))
            print(f'Updated {update_result.rowcount} clo_deals record(s)')
            
            # Update foreign key references
            print('Updating deal_assets references...')
            assets_update = db.execute(text('''
                UPDATE deal_assets 
                SET deal_id = 'MAG16'
                WHERE deal_id = 'MAG16-001'
            '''))
            print(f'Updated {assets_update.rowcount} deal_assets record(s)')
            
            print('Updating deal_concentration_thresholds references...')
            thresholds_update = db.execute(text('''
                UPDATE deal_concentration_thresholds 
                SET deal_id = 'MAG16'
                WHERE deal_id = 'MAG16-001'
            '''))
            print(f'Updated {thresholds_update.rowcount} threshold record(s)')
            
            # Re-enable foreign key checks
            print('Re-enabling foreign key checks...')
            db.execute(text('SET session_replication_role = DEFAULT;'))
            
            # Commit all changes
            db.commit()
            
            # Verify final state
            print('\nFinal verification:')
            verify_result = db.execute(text('''
                SELECT deal_id, deal_name, effective_date, target_par_amount
                FROM clo_deals 
                WHERE deal_id = 'MAG16'
            '''))
            
            record = verify_result.fetchone()
            if record:
                print(f'  {record.deal_id}: {record.deal_name} | Effective: {record.effective_date} | Par: ${record.target_par_amount:,.0f}')
                print('\nSuccess! URL is now: http://localhost:3002/portfolios/MAG16')
            else:
                print('  No MAG16 record found!')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_mag16_correct()