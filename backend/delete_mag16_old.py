#!/usr/bin/env python3
"""
Delete the old MAG16 record (2015), keep only MAG16-001 (2016)
"""

from app.core.database_config import db_config
from sqlalchemy import text

def delete_old_mag16():
    try:
        with db_config.get_db_session('postgresql') as db:
            # Check current state
            print('Current MAG16 records:')
            result = db.execute(text('''
                SELECT deal_id, deal_name, effective_date, target_par_amount
                FROM clo_deals 
                WHERE deal_id IN ('MAG16', 'MAG16-001')
                ORDER BY deal_id
            '''))
            
            records = result.fetchall()
            for record in records:
                print(f'  {record.deal_id}: {record.deal_name} | Effective: {record.effective_date} | Par: ${record.target_par_amount:,.0f}')
            
            # Delete the MAG16 (2015) record
            print('\nDeleting MAG16 (2015 vintage)...')
            delete_result = db.execute(text('''
                DELETE FROM clo_deals 
                WHERE deal_id = 'MAG16' AND effective_date = '2015-12-18'
            '''))
            
            rows_deleted = delete_result.rowcount
            print(f'Deleted {rows_deleted} record(s)')
            
            # Optionally rename MAG16-001 back to clean name
            print('Updating MAG16-001 name...')
            update_result = db.execute(text('''
                UPDATE clo_deals 
                SET deal_name = 'Magnetar MAG16 CLO',
                    updated_at = CURRENT_TIMESTAMP
                WHERE deal_id = 'MAG16-001'
            '''))
            print(f'Updated {update_result.rowcount} record(s)')
            
            # Commit changes
            db.commit()
            
            # Verify final state
            print('\nFinal state:')
            verify_result = db.execute(text('''
                SELECT deal_id, deal_name, effective_date, target_par_amount
                FROM clo_deals 
                WHERE deal_id LIKE '%MAG16%'
                ORDER BY deal_id
            '''))
            
            final_records = verify_result.fetchall()
            for record in final_records:
                print(f'  {record.deal_id}: {record.deal_name} | Effective: {record.effective_date} | Par: ${record.target_par_amount:,.0f}')
                
            print('\nSuccessfully kept only MAG16-001 record')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_old_mag16()