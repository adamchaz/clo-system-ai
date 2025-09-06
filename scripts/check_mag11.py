#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5433,
    database='clo_dev',
    user='postgres',
    password='adamchaz'
)

cursor = conn.cursor()

# Get MAG11 assets par amount
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

# Get target par for MAG11
cursor.execute("SELECT target_par_amount FROM clo_deals WHERE deal_id = 'MAG11'")
target_result = cursor.fetchone()

print("MAG11 ASSET PAR AMOUNT SUMMARY")
print("=" * 50)
print(f"Asset Count: {result[0]}")
print(f"Target Par Amount: ${float(target_result[0]):,.2f}")
print(f"Total Par (Assets Table): ${float(result[1]):,.2f}")
print(f"Total Par (Deal_Assets Table): ${float(result[2]):,.2f}")

# Show sample assets
cursor.execute("""
    SELECT a.blkrock_id, a.issue_name, a.par_amount
    FROM assets a
    JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
    WHERE da.deal_id = 'MAG11'
    ORDER BY a.par_amount DESC NULLS LAST
    LIMIT 5
""")

assets = cursor.fetchall()
print("\nSample MAG11 Assets:")
print("-" * 60)
for asset in assets:
    issue_name = asset[1][:40] if asset[1] else "N/A"
    par_amount = float(asset[2]) if asset[2] else 0
    print(f"{asset[0]}: {issue_name} - ${par_amount:,.2f}")

conn.close()