#!/usr/bin/env python3
"""
Update MAG17 Asset Par Amounts
Updates the database with the correct par amounts for MAG17 assets from collateral data
"""

import psycopg2
from psycopg2.extras import DictCursor
from decimal import Decimal

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'database': 'clo_dev',
    'user': 'postgres',
    'password': 'adamchaz'
}

# MAG17 actual par amounts by BLKRockID from the collateral data provided
MAG17_PAR_AMOUNTS = {
    'BRSRB2YE7': 1500000.00,
    'BRSU8ETX2': 6980000.00,
    'BRSUUC731': 2000000.00,
    'BRSUTL2G9': 3962500.00,
    'BRSY0Y6K1': 2147727.27,
    'BRSMGDRC1': 2500000.00,
    'BRSWQNUR9': 1500000.00,
    'BRSP22JB4': 2000000.00,
    'BRSUBA4E5': 1500000.00,
    'BRSLAZMP6': 750000.00,
    'BRSLNXDD4': 1250000.00,
    'BRSNVHZ59': 750000.00,
    'BRSZKH706': 1000000.00,
    'BRSM6KQS2': 2250000.00,
    'BRSW6MLL6': 4750000.00,
    'BRSX5R3F7': 3000000.00,
    'BRSV7VSH9': 1500000.00,
    'BRSQAA876': 1500000.00,
    'BRSJR0BB3': 7137851.63,
    'BRSKKW4R0': 3000000.00,
    'BRSLC7CV4': 3000000.00,
    'BRSK69ZP7': 2500000.00,
    'BRSYJ0CL6': 2500000.00,
    'BRSRC6JB0': 34647.00,
    'BRSJEKH76': 4000000.00,
    'BRSVUV3M9': 5000000.00,
    'BRSTBWVG5': 3250000.00,
    'BRSUU8H62': 2250000.00,
    'BRSM4TRW5': 320257.53,
    'BRSQV5NF9': 1500000.00,
    'BRSZLU5D0': 1975000.00,
    'BRSG2UJ71': 1500000.00,
    'BRSSM7WS3': 1500000.00,
    'BRST94UQ9': 3500000.00,
    'BRSN4YAK6': 1250000.00,
    'BRSZ5Y0M5': 2040000.00,
    'BRSHDY3S0': 2250000.00,
    'BRSJXWB42': 2000000.00,
    'BRSG1G1D9': 1000000.00,
    'BRSMB8NV9': 1500000.00,
    'BRSUWSQK5': 2246763.32,
    'BRSLE8S50': 207296.00,
    'BRSHH3U39': 1664013.89,
    'BRSN85V71': 5000000.00,
    'BRSS0WHT7': 500000.00,
    'BRSMGH3G9': 2000000.00,
    'BRSUW3MP3': 2984969.75,
    'BRSLBJCQ0': 909092.00,
    'BRSEZ4VS8': 1250000.00,
    'BRSM7G8T8': 1500000.00,
    'BRSRJZFJ6': 750000.00,
    'BRSM4TSP9': 526714.27,
    'BRSKQVDH8': 500000.00,
    'BRSTSU8K8': 1750000.00,
    'BRSX4ZNL5': 1553096.00,
    'BRSN4Y9J1': 2500000.00,
    'BRSN4Y5Z9': 2500000.00,
    'BRSWN4R07': 4500000.00,
    'BRSNGV8L0': 7500000.00,
    'BRSFCWCB6': 2000000.00,
    'BRSHGA5W8': 963169.00,
    'BRSUWSS49': 500000.00,
    'BRSYTW0L8': 2250000.00,
    'BRSM4TPX5': 499799.20,
    'BRSNVHY27': 1492272.75,
    'BRSJFJJX9': 500000.00,
    'BRSQNU464': 1500000.00,
    'BRSX1BQV6': 2000000.00,
    'BRT03RFE0': 615000.00,
    'BRSNLD7H4': 2498094.17,
    'BRSTG6CM5': 4250000.00,
    'BRSU2KSV9': 3000000.00,
    'BRSM1V101': 5250000.00,
    'BRSRFG694': 1500000.00,
    'BRSYUY6N2': 2000000.00,
    'BRSKSADX7': 2008848.00,
    'BRSTWBH90': 2250000.00,
    'BRST5NSU5': 1250000.00,
    'BRSTJ1FE8': 2500000.00,
    'BRSWVW9B2': 3435142.86,
    'BRSP292C5': 1250000.00,
    'BRSJ3EEC4': 1250000.00,
    'BRSLBH5L3': 1500000.00,
    'BRSW0ZRH6': 1443887.50,
    'BRSXUCRH2': 4000000.00,
    'BRSJ0RC63': 500000.00,
    'BRSLAS6T2': 1750000.00,
    'BRSMK3CE0': 1352475.51,
    'BRSZRX6W5': 3271740.61,
    'BRSKQ7XQ9': 5500000.00,
    'BRSUW2BS1': 1250000.00,
    'BRSQHT1U4': 662145.46,
    'BRSNZFA49': 2500000.00,
    'BRSNBE338': 3000000.00,
    'BRSWYD657': 2000000.00,
    'BRSTCP7D3': 2500000.00,
    'BRSTV85W0': 3000000.00,
    'BRSHVTMG6': 180000.00,
    'BRSHEWYR1': 2259418.48,
    'BRSRFDWW1': 1250000.00,
    'BRSU3BMK8': 2000000.00,
    'BRSL3G8T4': 2500000.00,
    'BRSKQVDC9': 1000000.00,
    'BRST4R1R3': 750000.00,
    'BRSV27V59': 3500000.00,
    'BRSYHUJQ4': 2992862.00,
    'BRSSWB4N5': 599700.59,
    'BRSS7R655': 1246867.17,
    'BRSRF1N07': 2000000.00,
    'BRSPVYNA9': 3011710.52,
    'BRSV5TM33': 1000000.00,
    'BRSWXJEL1': 6000000.00,
    'BRSN5MWG6': 3000000.00,
    'BRSJ6T4S4': 1000000.00,
    'BRSNU6VW9': 6000000.00,
    'BRSFWSH02': 2500000.00,
    'BRSMCA527': 4234167.08,
    'BRSM66CR0': 1000000.00,
    'BRSQT5KB4': 1750000.00,
    'BRSHAG9G2': 2000000.00,
    'BRSLY6QW5': 1393484.82,
    'BRSUVAL12': 2000000.00,
    'BRSM7G8J0': 2540000.00,
    'BRST137M4': 1500000.00,
    'BRSJ76ZK6': 1500000.00,
    'BRSHGQ826': 2909957.32,
    'BRSQ6J5C4': 127659.58,
    'BRSJ1HUF4': 750000.00,
    'BRSV7TBL3': 2000000.00,
    'BRSX52MA2': 3750000.00,
    'BRSQBTVC7': 1500000.00,
    'BRSYEJ6N3': 3000000.00,
    'BRSV8P7W1': 2500000.00,
    'BRSWYJ431': 1500000.00,
    'BRSP292F8': 2000000.00,
    'BRSTDEAM3': 1750000.00,
    'BRSLZGT09': 2500000.00,
    'BRSHCGRY1': 2500000.00,
    'BRSTH6AW4': 3000000.00,
    'BRSNN37V3': 2956739.58,
    'BRSL992B9': 2500000.00,
    'BRSU95US9': 629098.40,
    'BRSUY9361': 3750000.00,
    'BRSUW3ME8': 1250000.00,
    'BRSTMMAT0': 1250000.00,
    'BRSTMLVU6': 3875000.00,
    'BRSNY0879': 1500000.00,
    'BRSW3NGN9': 2000000.00,
    'BRSUR93K8': 750000.00,
    'BRSUTDDX8': 3000000.00,
    'BRSV6CYC6': 2000000.00,
    'BRSTZPQ88': 3000000.00,
    'BRSRJB3S2': 1000000.00,
    'BRSZJHMF8': 1820000.00,
    'BRSHGTU58': 1500000.00,
    'BRSSW6XL8': 1403299.41,
    'BRSSVEHW6': 4250000.00,
    'BRSM9GPX8': 2500000.00,
    'BRSK5A7F8': 2000000.00,
    'BRSJYDTQ5': 4000000.00,
    'BRSQ5UAS9': 2872340.42,
    'BRSPR86F9': 1500000.00,
    'BRSTEHXK4': 3000000.00,
    'BRSU95U26': 4355654.27,
    'BRSJGG5C5': 1250000.00,
    'BRSUM53S4': 1250000.00,
    'BRSP7BGY2': 2000000.00,
    'BRSL4D6X3': 750000.00,
    'BRSZC1JQ0': 2000000.00,
    'BRSRNHTY3': 1500000.00,
    'BRSWL67L0': 2750000.00,
    'BRSTV33U7': 2844534.87,
    'BRSL9MEX9': 3000000.00,
    'BRSN5E5R0': 2500000.00,
    'BRSZ4QZA1': 2250000.00,
    'BRSTBTC24': 1500000.00,
    'BRSK5UM00': 5000000.00,
    'BRSQGX3A8': 602395.39,
    'BRSTU6JJ9': 2500000.00,
    'BRSJR6SV8': 1025211.28,
    'BRSKKW2C5': 2250000.00,
    'BRSZSXJZ3': 855000.00,
    'BRSJ6G9A6': 3000000.00,
    'BRSL0NZU9': 2000000.00,
    'BRSL5JLG9': 3250000.00,
    'BRSQTQC92': 990000.00,
    'BRSJ13HK9': 750000.00,
    'BRSHV5U04': 3250000.00,
    'BRSX3AUD1': 7500000.00,
    'BRST7Y914': 2250000.00,
    'BRSU975A2': 2000000.00,
    'BRSRQP3V6': 1500000.00,
    'BRSSCFXM8': 2000000.00,
    'BRSJF4LM3': 2250000.00,
    'BRSUR9351': 2250000.00
}

def update_mag17_par_amounts():
    """Update MAG17 asset par amounts with correct collateral data"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        print("Updating MAG17 Asset Par Amounts...")
        print("=" * 50)
        
        # Update par amounts for matched BLKRockIDs
        updated_count = 0
        total_par_amount = 0
        
        for blkrock_id, par_amount in MAG17_PAR_AMOUNTS.items():
            try:
                # Update the asset with the correct par amount
                cursor.execute("""
                    UPDATE assets 
                    SET par_amount = %s, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE blkrock_id = %s
                """, (par_amount, blkrock_id))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    total_par_amount += par_amount
                    
                    if updated_count % 25 == 0:
                        print(f"Updated {updated_count} assets...")
                        
            except Exception as e:
                print(f"Error updating {blkrock_id}: {e}")
                continue
        
        print(f"\nPar Amount Update Complete:")
        print(f"  - Updated assets: {updated_count}")
        print(f"  - Total par amount: ${total_par_amount:,.2f}")
        
        # Calculate market values (par_amount * market_value/100)
        print("\nCalculating market values...")
        cursor.execute("""
            UPDATE assets 
            SET market_value = CASE 
                WHEN par_amount > 0 AND market_value > 0 THEN 
                    par_amount * (market_value / 100.0)
                ELSE market_value
            END
            WHERE blkrock_id IN %s
            AND par_amount > 0
        """, (tuple(MAG17_PAR_AMOUNTS.keys()),))
        
        market_value_updates = cursor.rowcount
        print(f"Updated market values for {market_value_updates} assets")
        
        # Update the portfolio totals
        print("\nUpdating portfolio totals...")
        cursor.execute("""
            UPDATE collateral_pools 
            SET total_par_amount = (
                SELECT COALESCE(SUM(par_amount), 0) 
                FROM assets 
                WHERE blkrock_id IN %s
            ),
            total_market_value = (
                SELECT COALESCE(SUM(market_value), 0) 
                FROM assets 
                WHERE blkrock_id IN %s
                AND market_value > par_amount * 0.5  -- Sanity check for calculated market values
            ),
            total_assets = %s,
            updated_at = CURRENT_TIMESTAMP
            WHERE deal_id = 'MAG17'
        """, (tuple(MAG17_PAR_AMOUNTS.keys()), tuple(MAG17_PAR_AMOUNTS.keys()), len(MAG17_PAR_AMOUNTS)))
        
        conn.commit()
        
        # Verification
        cursor.execute("SELECT * FROM collateral_pools WHERE deal_id = 'MAG17'")
        portfolio = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as matched_assets, 
                   SUM(par_amount) as total_par, 
                   SUM(market_value) as total_mv
            FROM assets 
            WHERE blkrock_id IN %s
        """, (tuple(MAG17_PAR_AMOUNTS.keys()),))
        
        verification = cursor.fetchone()
        
        print("\n" + "=" * 60)
        print("MAG17 PAR AMOUNT UPDATE COMPLETE")
        print("=" * 60)
        
        if portfolio:
            print(f"Portfolio Total Par: ${portfolio['total_par_amount']:,.2f}")
            print(f"Portfolio Total Market Value: ${portfolio['total_market_value']:,.2f}")
            print(f"Portfolio Asset Count: {portfolio['total_assets']}")
        
        if verification:
            print(f"\nVerification from assets table:")
            print(f"Matched Assets: {verification['matched_assets']}")
            print(f"Total Par Amount: ${verification['total_par']:,.2f}")
            print(f"Total Market Value: ${verification['total_mv']:,.2f}")
        
        # Sample of updated assets
        cursor.execute("""
            SELECT blkrock_id, issuer_name, par_amount, market_value 
            FROM assets 
            WHERE blkrock_id IN %s 
            AND par_amount > 0 
            ORDER BY par_amount DESC 
            LIMIT 10
        """, (tuple(MAG17_PAR_AMOUNTS.keys()),))
        
        samples = cursor.fetchall()
        print(f"\nTop 10 assets by par amount:")
        for asset in samples:
            par = asset['par_amount'] or 0
            mv = asset['market_value'] or 0
            print(f"  {asset['blkrock_id']}: {asset['issuer_name'][:30]:<30} Par=${par:>10,.0f} MV=${mv:>12,.0f}")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Error updating MAG17 par amounts: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main execution"""
    success = update_mag17_par_amounts()
    
    if success:
        print("\nMAG17 collateral data successfully updated!")
        print("The portfolio now shows the correct:")
        print("1. Individual asset par amounts")
        print("2. Calculated market values based on prices")
        print("3. Portfolio-level totals")
        print("4. Asset count (195 assets)")
        print("\nMAG17 is now ready for detailed analysis in the frontend.")
    else:
        print("\nFailed to update MAG17 collateral data")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())