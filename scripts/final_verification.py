#!/usr/bin/env python3
"""
Final verification of all MAG deals migration
"""
import psycopg2
from psycopg2.extras import DictCursor

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5433,
    database='clo_dev',
    user='postgres',
    password='adamchaz'
)

cursor = conn.cursor(cursor_factory=DictCursor)

print("FINAL MAG DEALS MIGRATION VERIFICATION")
print("=" * 80)

# Get comprehensive status
cursor.execute("""
    SELECT 
        d.deal_id,
        d.target_par_amount,
        COUNT(da.blkrock_id) as asset_count,
        SUM(COALESCE(da.par_amount, 0)) as actual_par,
        (SELECT COUNT(*) FROM clo_tranches WHERE deal_id = d.deal_id) as tranche_count,
        (SELECT COUNT(*) FROM deal_concentration_thresholds WHERE deal_id = d.deal_id) as test_count
    FROM clo_deals d
    LEFT JOIN deal_assets da ON d.deal_id = da.deal_id
    WHERE d.deal_id LIKE 'MAG%'
    GROUP BY d.deal_id, d.target_par_amount
    ORDER BY d.deal_id
""")

results = cursor.fetchall()

print(f"{'Deal':<6} {'Assets':<7} {'Par ($M)':<10} {'Coverage %':<10} {'Tranches':<9} {'Tests':<6} {'Status':<10}")
print("-" * 80)

complete_deals = 0
total_assets = 0
total_par = 0

for row in results:
    deal_id = row['deal_id']
    asset_count = row['asset_count'] or 0
    actual_m = float(row['actual_par']) / 1_000_000 if row['actual_par'] else 0
    target_m = float(row['target_par_amount']) / 1_000_000
    tranche_count = row['tranche_count'] or 0
    test_count = row['test_count'] or 0
    
    coverage = actual_m / target_m * 100 if target_m > 0 else 0
    
    # Determine status
    assets_ok = coverage >= 90
    tranches_ok = tranche_count >= 6
    tests_ok = test_count >= 30
    
    if assets_ok and tranches_ok and tests_ok:
        status = "COMPLETE"
        complete_deals += 1
    elif assets_ok:
        status = "PARTIAL"
    else:
        status = "MINIMAL"
    
    print(f"{deal_id:<6} {asset_count:<7} {actual_m:<10.1f} {coverage:<9.1f} {tranche_count:<9} {test_count:<6} {status:<10}")
    
    total_assets += asset_count
    total_par += actual_m

print("-" * 80)
print(f"TOTAL  {total_assets:<7} {total_par:<10.1f}")
print("=" * 80)

print(f"\nSYSTEM COMPLETION STATUS:")
print(f"Complete deals: {complete_deals}/10 ({complete_deals/10*100:.0f}%)")
print(f"Total assets: {total_assets:,}")
print(f"Total portfolio: ${total_par:.1f}B")

# Show what's complete
complete_list = []
need_tests = []

for row in results:
    deal_id = row['deal_id']
    coverage = float(row['actual_par']) / float(row['target_par_amount']) * 100
    tranches = row['tranche_count'] or 0
    tests = row['test_count'] or 0
    
    if coverage >= 90 and tranches >= 6 and tests >= 30:
        complete_list.append(deal_id)
    elif coverage >= 90 and tranches >= 6 and tests < 30:
        need_tests.append(deal_id)

print(f"\nCOMPLETE DEALS: {complete_list}")
if need_tests:
    print(f"NEED TESTS: {need_tests}")

if complete_deals == 10:
    print("\nSUCCESS: ALL 10 MAG DEALS FULLY MIGRATED!")
else:
    print(f"\nREMAINING: {10-complete_deals} deals need concentration tests")

conn.close()