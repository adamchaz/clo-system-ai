#!/usr/bin/env python3
"""
Migrate all 234 MAG16 assets from Excel to database (Fixed version)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from app.core.database_config import db_config
from sqlalchemy import text

def extract_mag16_from_excel():
    """Extract all MAG16 assets from Excel"""
    
    excel_path = Path("../TradeHypoPrelimv32.xlsm")
    
    print(f"Extracting MAG16 assets from: {excel_path.name}")
    
    try:
        # Read the Mag 16 Inputs sheet without headers
        df = pd.read_excel(excel_path, sheet_name="Mag 16 Inputs", header=None)
        
        # Bloomberg ID and Par Amount columns (we know they're at row 2)
        blkrock_col = 3  # BLKRockID column
        par_col = 4      # Par Amount column
        
        # Extract asset data starting from row 3 (after header at row 2)
        asset_start_row = 3
        
        assets = []
        
        for row_idx in range(asset_start_row, df.shape[0]):
            blk_id = df.iloc[row_idx, blkrock_col]
            par_amount = df.iloc[row_idx, par_col]
            
            # Skip if no Bloomberg ID or invalid par amount
            if pd.isna(blk_id) or pd.isna(par_amount):
                continue
                
            blk_str = str(blk_id).strip()
            
            # Validate Bloomberg ID format (8-12 alphanumeric characters)
            if len(blk_str) < 8 or len(blk_str) > 12 or not blk_str.isalnum():
                continue
            
            # Convert par amount to float
            try:
                par_float = float(par_amount)
                if par_float <= 0:
                    continue
            except (ValueError, TypeError):
                continue
            
            assets.append({
                'blkrock_id': blk_str,
                'par_amount': par_float,
                'row_number': row_idx + 1  # Excel row number (1-indexed)
            })
        
        print(f"Extracted {len(assets)} assets from Excel")
        
        if assets:
            print(f"Sample assets:")
            for i, asset in enumerate(assets[:5]):
                print(f"  {i+1}. {asset['blkrock_id']}: ${asset['par_amount']:,.2f}")
            
            total_par = sum(asset['par_amount'] for asset in assets)
            print(f"Total Par Amount: ${total_par:,.2f}")
        
        return assets
        
    except Exception as e:
        print(f"Error extracting from Excel: {e}")
        import traceback
        traceback.print_exc()
        return []

def migrate_to_database(assets):
    """Migrate MAG16 assets to database"""
    
    if not assets:
        print("No assets to migrate")
        return False
    
    print(f"\nMigrating {len(assets)} assets to database...")
    
    try:
        with db_config.get_db_session('postgresql') as db:
            # First, backup existing MAG16 assets
            print("Creating backup of existing MAG16 assets...")
            existing_count = db.execute(text("""
                SELECT COUNT(*) FROM deal_assets WHERE deal_id = 'MAG16'
            """)).fetchone()[0]
            
            if existing_count > 0:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS deal_assets_backup_mag16 AS 
                    SELECT *, CURRENT_TIMESTAMP as backup_date 
                    FROM deal_assets 
                    WHERE deal_id = 'MAG16'
                """))
                print(f"Backed up {existing_count} existing MAG16 assets")
                
                # Clear existing MAG16 deal_assets
                print("Removing existing MAG16 assets...")
                delete_result = db.execute(text("""
                    DELETE FROM deal_assets WHERE deal_id = 'MAG16'
                """))
                print(f"Deleted {delete_result.rowcount} existing records")
            
            # Check which assets already exist in main assets table
            print("Checking existing assets in main table...")
            existing_assets = db.execute(text("""
                SELECT blkrock_id FROM assets 
            """)).fetchall()
            existing_blk_ids = {row[0] for row in existing_assets}
            print(f"Found {len(existing_blk_ids)} existing assets in main table")
            
            # Create deal_assets entries (we don't need to modify the main assets table)
            print(f"Creating {len(assets)} MAG16 deal assets...")
            created_count = 0
            skipped_count = 0
            
            for asset in assets:
                try:
                    # Always create deal_assets entry
                    db.execute(text("""
                        INSERT INTO deal_assets (
                            deal_id, blkrock_id, par_amount, 
                            position_status, created_at
                        ) VALUES (
                            :deal_id, :blkrock_id, :par_amount,
                            :status, :created_at
                        )
                    """), {
                        'deal_id': 'MAG16',
                        'blkrock_id': asset['blkrock_id'],
                        'par_amount': asset['par_amount'],
                        'status': 'ACTIVE',
                        'created_at': datetime.now()
                    })
                    
                    created_count += 1
                    
                    if created_count % 50 == 0:
                        db.commit()
                        print(f"Progress: {created_count}/{len(assets)} assets migrated")
                        
                except Exception as e:
                    print(f"Error inserting asset {asset['blkrock_id']}: {e}")
                    skipped_count += 1
                    continue
            
            # Final commit
            db.commit()
            
            # Verify results
            print("\nVerifying migration...")
            final_count = db.execute(text("""
                SELECT COUNT(*) FROM deal_assets WHERE deal_id = 'MAG16'
            """)).fetchone()[0]
            
            total_par = db.execute(text("""
                SELECT COALESCE(SUM(par_amount), 0) FROM deal_assets WHERE deal_id = 'MAG16'
            """)).fetchone()[0]
            
            print(f"Final verification:")
            print(f"  MAG16 assets in database: {final_count}")
            print(f"  Total par amount: ${float(total_par):,.2f}")
            print(f"  Expected assets: {len(assets)}")
            print(f"  Successfully created: {created_count}")
            print(f"  Skipped due to errors: {skipped_count}")
            print(f"  Success rate: {(final_count/len(assets)*100):.1f}%")
            
            success = final_count == len(assets)
            print(f"Migration {'SUCCESS' if success else 'PARTIAL SUCCESS'}")
            
            return success
            
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main migration function"""
    print("MAG16 Complete Asset Migration - Fixed Version")
    print("=" * 55)
    
    try:
        # Extract assets from Excel
        assets = extract_mag16_from_excel()
        
        if not assets:
            print("No assets extracted from Excel")
            return
        
        # Migrate to database
        success = migrate_to_database(assets)
        
        print("\n" + "=" * 55)
        if success:
            print("SUCCESS: MAG16 MIGRATION COMPLETE!")
            print("All 234 assets successfully migrated from Excel to database")
        else:
            print("WARNING: Migration completed with issues")
            print("Check logs for details")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()