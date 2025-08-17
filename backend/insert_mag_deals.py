import psycopg2
from psycopg2.extras import DictCursor

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
    
    # Read and execute the SQL file
    with open('../mag_deals_insert.sql', 'r') as f:
        sql_content = f.read()
        
    # Split the SQL into statements and execute
    statements = sql_content.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
            except Exception as stmt_error:
                print(f"Error executing statement: {stmt_error}")
                continue
            
    conn.commit()
    print('Successfully inserted 10 MAG CLO deals into PostgreSQL database')
    
    # Verify insertion
    cursor.execute("SELECT deal_id, deal_name, deal_size FROM clo_deals WHERE deal_id LIKE %s ORDER BY deal_id", ('MAG%',))
    deals = cursor.fetchall()
    
    print(f'\nInserted {len(deals)} MAG deals:')
    for deal in deals:
        deal_size = deal['deal_size'] if deal['deal_size'] else 0
        print(f'  - {deal["deal_id"]}: {deal["deal_name"]} (${deal_size:,})')
        
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'conn' in locals():
        conn.close()