import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

# MAG deals data extracted from Excel
mag_deals = [
    {
        'deal_id': 'MAG6',
        'deal_name': 'Magnetar MAG6 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2012-09-13',
        'closing_date': '2012-09-13',
        'effective_date': '2012-09-13',
        'maturity_date': '2023-09-15',
        'target_par_amount': 367750000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG7',
        'deal_name': 'Magnetar MAG7 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2012-12-20',
        'closing_date': '2012-12-20',
        'effective_date': '2012-12-20',
        'maturity_date': '2025-01-15',
        'target_par_amount': 552000000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG8',
        'deal_name': 'Magnetar MAG8 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2014-05-15',
        'closing_date': '2014-05-15',
        'effective_date': '2014-05-15',
        'maturity_date': '2026-04-15',
        'target_par_amount': 558720000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG9',
        'deal_name': 'Magnetar MAG9 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2014-07-17',
        'closing_date': '2014-07-17',
        'effective_date': '2014-07-17',
        'maturity_date': '2026-07-25',
        'target_par_amount': 373200000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG11',
        'deal_name': 'Magnetar MAG11 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2014-12-18',
        'closing_date': '2014-12-18',
        'effective_date': '2014-12-18',
        'maturity_date': '2027-01-18',
        'target_par_amount': 507000000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG12',
        'deal_name': 'Magnetar MAG12 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2015-03-12',
        'closing_date': '2015-03-12',
        'effective_date': '2015-03-12',
        'maturity_date': '2027-04-15',
        'target_par_amount': 564000000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG14',
        'deal_name': 'Magnetar MAG14 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2015-06-25',
        'closing_date': '2015-06-25',
        'effective_date': '2015-06-25',
        'maturity_date': '2028-07-18',
        'target_par_amount': 493500000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG15',
        'deal_name': 'Magnetar MAG15 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2015-11-18',
        'closing_date': '2015-11-18',
        'effective_date': '2015-11-18',
        'maturity_date': '2027-10-25',
        'target_par_amount': 559400000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG16',
        'deal_name': 'Magnetar MAG16 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2015-12-18',
        'closing_date': '2015-12-18',
        'effective_date': '2015-12-18',
        'maturity_date': '2028-01-18',
        'target_par_amount': 460000000,
        'deal_status': 'Revolving'
    },
    {
        'deal_id': 'MAG17',
        'deal_name': 'Magnetar MAG17 CLO',
        'manager_name': 'Magnetar Capital',
        'pricing_date': '2016-03-31',
        'closing_date': '2016-03-31',
        'effective_date': '2016-03-31',
        'maturity_date': '2028-04-20',
        'target_par_amount': 462400000,
        'deal_status': 'Revolving'
    }
]

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5433,
        database='clo_dev',
        user='postgres',
        password='adamchaz'
    )
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Insert each MAG deal
    insert_sql = """
    INSERT INTO clo_deals (
        deal_id, deal_name, manager_name, pricing_date, closing_date, 
        effective_date, maturity_date, target_par_amount, deal_status,
        created_at, updated_at
    ) VALUES (
        %(deal_id)s, %(deal_name)s, %(manager_name)s, %(pricing_date)s, %(closing_date)s,
        %(effective_date)s, %(maturity_date)s, %(target_par_amount)s, %(deal_status)s,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT (deal_id) 
    DO UPDATE SET
        deal_name = EXCLUDED.deal_name,
        manager_name = EXCLUDED.manager_name,
        pricing_date = EXCLUDED.pricing_date,
        closing_date = EXCLUDED.closing_date,
        effective_date = EXCLUDED.effective_date,
        maturity_date = EXCLUDED.maturity_date,
        target_par_amount = EXCLUDED.target_par_amount,
        deal_status = EXCLUDED.deal_status,
        updated_at = CURRENT_TIMESTAMP
    """
    
    inserted_count = 0
    for deal in mag_deals:
        try:
            cursor.execute(insert_sql, deal)
            inserted_count += 1
            print(f"Inserted/Updated: {deal['deal_id']} - {deal['deal_name']}")
        except Exception as e:
            print(f"Error inserting {deal['deal_id']}: {e}")
            
    conn.commit()
    print(f'\nSuccessfully migrated {inserted_count} MAG CLO deals to PostgreSQL database')
    
    # Verify insertion
    cursor.execute("SELECT deal_id, deal_name, target_par_amount FROM clo_deals WHERE deal_id LIKE %s ORDER BY deal_id", ('MAG%',))
    deals = cursor.fetchall()
    
    print(f'\nTotal MAG deals in database: {len(deals)}')
    total_amount = 0
    for deal in deals:
        amount = deal['target_par_amount'] if deal['target_par_amount'] else 0
        total_amount += amount
        print(f'  - {deal["deal_id"]}: {deal["deal_name"]} (${amount:,})')
    
    print(f'\nTotal portfolio value: ${total_amount:,}')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'conn' in locals():
        conn.close()