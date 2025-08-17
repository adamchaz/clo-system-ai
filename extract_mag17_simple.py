#!/usr/bin/env python3
"""
Simplified MAG17 CLO Data Extraction Script using pandas
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import logging
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_convert_value(value):
    """Safely convert Excel values to JSON serializable format"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (int, float, np.integer, np.floating)):
        if np.isnan(value):
            return None
        return float(value)
    elif isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime('%Y-%m-%d')
    elif isinstance(value, str):
        return value.strip() if value.strip() else None
    else:
        return str(value)

def extract_mag17_data():
    """Extract MAG17 data from Excel file using pandas"""
    excel_path = r"C:\Users\adamc\OneDrive\Development\CLO System AI\TradeHypoPrelimv32.xlsm"
    output_dir = Path(r"C:\Users\adamc\OneDrive\Development\CLO System AI")
    
    logger.info("Starting MAG17 data extraction with pandas...")
    
    try:
        # Read all sheets first to see what's available
        logger.info("Reading Excel file to identify available sheets...")
        excel_file = pd.ExcelFile(excel_path)
        available_sheets = excel_file.sheet_names
        
        logger.info(f"Available sheets: {available_sheets}")
        
        # Find MAG17 related sheet
        mag17_sheet = None
        for sheet in available_sheets:
            if 'mag' in sheet.lower() and '17' in sheet:
                mag17_sheet = sheet
                break
        
        if not mag17_sheet:
            # Try common variations
            for possible_name in ['Mag 17 Inputs', 'MAG17', 'Mag17', 'MAG 17', 'Mag 17']:
                if possible_name in available_sheets:
                    mag17_sheet = possible_name
                    break
        
        if not mag17_sheet:
            logger.error(f"Could not find MAG17 sheet. Available: {available_sheets}")
            return False
        
        logger.info(f"Found MAG17 sheet: {mag17_sheet}")
        
        # Read the MAG17 sheet
        logger.info("Reading MAG17 worksheet data...")
        df = pd.read_excel(excel_path, sheet_name=mag17_sheet, header=None)
        
        logger.info(f"Sheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Initialize data containers
        extraction_results = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'analysis_date': '2016-03-23',
                'source_file': excel_path,
                'source_sheet': mag17_sheet,
                'deal_name': 'MAG17',
                'deal_full_name': 'Magnetar MAG17 CLO',
                'sheet_dimensions': f"{df.shape[0]}x{df.shape[1]}"
            },
            'assets': [],
            'tranches': [],
            'triggers': [],
            'accounts': [],
            'parameters': {},
            'raw_data_samples': []
        }
        
        # Extract asset data by looking for typical headers
        logger.info("Scanning for asset data...")
        asset_data_found = False
        
        for row_idx in range(min(100, df.shape[0])):  # Scan first 100 rows
            row_data = df.iloc[row_idx].fillna('').astype(str)
            row_text = ' '.join(row_data.str.lower())
            
            # Look for asset-related headers
            asset_indicators = ['obligor', 'cusip', 'balance', 'spread', 'coupon', 'maturity']
            if any(indicator in row_text for indicator in asset_indicators):
                logger.info(f"Found potential asset header row at {row_idx}: {list(row_data[:10])}")
                
                # Extract headers
                headers = [str(cell).strip() for cell in row_data if str(cell).strip()]
                if len(headers) > 5:  # Must have substantial data
                    logger.info(f"Asset headers: {headers[:15]}")  # Show first 15
                    
                    # Extract asset rows
                    assets = []
                    for data_row_idx in range(row_idx + 1, min(row_idx + 300, df.shape[0])):
                        try:
                            data_row = df.iloc[data_row_idx]
                            
                            # Check if row has substantial data
                            non_empty_cells = sum(1 for x in data_row[:10] if pd.notna(x) and str(x).strip())
                            if non_empty_cells < 3:  # Need at least 3 non-empty cells
                                continue
                            
                            # Create asset record
                            asset = {
                                'asset_id': f"MAG17_ASSET_{len(assets) + 1:03d}",
                                'deal_id': 'MAG17',
                                'source_row': data_row_idx + 1  # Excel row number (1-indexed)
                            }
                            
                            # Map data to headers
                            for col_idx, header in enumerate(headers):
                                if col_idx < len(data_row) and col_idx < df.shape[1]:
                                    value = safe_convert_value(data_row.iloc[col_idx])
                                    if value is not None:
                                        # Normalize field name
                                        field_name = header.lower().replace(' ', '_').replace('-', '_')
                                        field_name = ''.join(c for c in field_name if c.isalnum() or c == '_')
                                        asset[field_name] = value
                            
                            # Only include if we have substantial data
                            if len([v for v in asset.values() if v is not None]) > 5:
                                assets.append(asset)
                                
                                # Stop if we've found enough assets or hit empty rows
                                if len(assets) > 0 and len(assets) % 50 == 0:
                                    logger.info(f"Extracted {len(assets)} assets so far...")
                        
                        except Exception as e:
                            logger.debug(f"Error processing asset row {data_row_idx}: {e}")
                            continue
                    
                    if assets:
                        extraction_results['assets'] = assets
                        asset_data_found = True
                        logger.info(f"Successfully extracted {len(assets)} assets")
                        break
        
        # Extract tranche data
        logger.info("Scanning for tranche data...")
        for row_idx in range(min(200, df.shape[0])):
            row_data = df.iloc[row_idx].fillna('')
            first_cell = str(row_data.iloc[0]).strip().upper()
            
            # Look for tranche indicators
            if (first_cell.startswith('CLASS ') or 
                first_cell.startswith('NOTE ') or
                first_cell in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'EQUITY'] or
                'tranche' in str(row_data.iloc[0]).lower()):
                
                tranche = {
                    'tranche_id': f"MAG17_{first_cell.replace(' ', '_')}",
                    'deal_id': 'MAG17',
                    'class_name': first_cell,
                    'source_row': row_idx + 1
                }
                
                # Extract additional data from the row
                for col_idx in range(1, min(10, len(row_data))):
                    value = safe_convert_value(row_data.iloc[col_idx])
                    if value is not None:
                        tranche[f'field_{col_idx}'] = value
                
                extraction_results['tranches'].append(tranche)
        
        logger.info(f"Found {len(extraction_results['tranches'])} tranches")
        
        # Extract trigger/test data
        logger.info("Scanning for OC/IC trigger data...")
        for row_idx in range(min(300, df.shape[0])):
            row_data = df.iloc[row_idx].fillna('')
            first_cell_text = str(row_data.iloc[0]).strip().lower()
            
            # Look for trigger test indicators
            trigger_keywords = ['oc test', 'ic test', 'oc ratio', 'ic ratio', 
                              'overcollateralization', 'interest coverage', 'trigger']
            
            if any(keyword in first_cell_text for keyword in trigger_keywords):
                trigger = {
                    'trigger_id': f"MAG17_TRIGGER_{len(extraction_results['triggers']) + 1}",
                    'deal_id': 'MAG17',
                    'test_name': str(row_data.iloc[0]).strip(),
                    'source_row': row_idx + 1
                }
                
                # Extract trigger values
                for col_idx in range(1, min(5, len(row_data))):
                    value = safe_convert_value(row_data.iloc[col_idx])
                    if value is not None:
                        trigger[f'value_{col_idx}'] = value
                
                extraction_results['triggers'].append(trigger)
        
        logger.info(f"Found {len(extraction_results['triggers'])} trigger tests")
        
        # Extract account data
        logger.info("Scanning for account data...")
        for row_idx in range(min(200, df.shape[0])):
            row_data = df.iloc[row_idx].fillna('')
            first_cell_text = str(row_data.iloc[0]).strip().lower()
            
            if ('account' in first_cell_text or 
                'reserve' in first_cell_text or 
                'collection' in first_cell_text or
                'cash' in first_cell_text):
                
                account = {
                    'account_id': f"MAG17_ACCOUNT_{len(extraction_results['accounts']) + 1}",
                    'deal_id': 'MAG17',
                    'account_name': str(row_data.iloc[0]).strip(),
                    'source_row': row_idx + 1
                }
                
                # Extract account values
                for col_idx in range(1, min(5, len(row_data))):
                    value = safe_convert_value(row_data.iloc[col_idx])
                    if value is not None:
                        account[f'value_{col_idx}'] = value
                
                extraction_results['accounts'].append(account)
        
        logger.info(f"Found {len(extraction_results['accounts'])} accounts")
        
        # Save sample raw data for manual inspection
        logger.info("Collecting raw data samples...")
        for row_idx in range(0, min(50, df.shape[0]), 5):  # Every 5th row for first 50
            row_sample = {
                'row_number': row_idx + 1,
                'data': [safe_convert_value(x) for x in df.iloc[row_idx][:20]]  # First 20 columns
            }
            extraction_results['raw_data_samples'].append(row_sample)
        
        # Save all extracted data
        logger.info("Saving extraction results...")
        
        # Individual JSON files
        output_files = []
        
        # Assets
        assets_file = output_dir / "mag17_assets_complete.json"
        with open(assets_file, 'w') as f:
            json.dump(extraction_results['assets'], f, indent=2)
        output_files.append(assets_file)
        
        # Tranches
        tranches_file = output_dir / "mag17_tranches.json"
        with open(tranches_file, 'w') as f:
            json.dump(extraction_results['tranches'], f, indent=2)
        output_files.append(tranches_file)
        
        # Triggers
        triggers_file = output_dir / "mag17_triggers.json"
        with open(triggers_file, 'w') as f:
            json.dump(extraction_results['triggers'], f, indent=2)
        output_files.append(triggers_file)
        
        # Accounts
        accounts_file = output_dir / "mag17_accounts.json"
        with open(accounts_file, 'w') as f:
            json.dump(extraction_results['accounts'], f, indent=2)
        output_files.append(accounts_file)
        
        # Parameters (deal-level info)
        parameters = {
            'deal_id': 'MAG17',
            'deal_name': 'Magnetar MAG17 CLO',
            'analysis_date': '2016-03-23',
            'total_assets_found': len(extraction_results['assets']),
            'total_tranches_found': len(extraction_results['tranches']),
            'total_triggers_found': len(extraction_results['triggers']),
            'total_accounts_found': len(extraction_results['accounts']),
            'source_sheet': mag17_sheet,
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        parameters_file = output_dir / "mag17_parameters.json"
        with open(parameters_file, 'w') as f:
            json.dump(parameters, f, indent=2)
        output_files.append(parameters_file)
        
        # Complete dataset
        complete_file = output_dir / "mag17_complete_dataset.json"
        with open(complete_file, 'w') as f:
            json.dump(extraction_results, f, indent=2)
        output_files.append(complete_file)
        
        # Generate validation report
        validation_report = generate_validation_report(extraction_results)
        report_file = output_dir / "mag17_validation_report.txt"
        with open(report_file, 'w') as f:
            f.write(validation_report)
        output_files.append(report_file)
        
        # Generate SQL (basic version)
        sql_statements = generate_basic_sql(extraction_results)
        sql_file = output_dir / "mag17_migration.sql"
        with open(sql_file, 'w') as f:
            f.write(sql_statements)
        output_files.append(sql_file)
        
        logger.info(f"\n{'='*60}")
        logger.info("MAG17 DATA EXTRACTION COMPLETED SUCCESSFULLY")
        logger.info('='*60)
        logger.info("\nOutput files generated:")
        for file in output_files:
            logger.info(f"  - {file.name}")
        
        logger.info(f"\nExtraction Summary:")
        logger.info(f"  - Assets: {len(extraction_results['assets'])}")
        logger.info(f"  - Tranches: {len(extraction_results['tranches'])}")
        logger.info(f"  - Triggers: {len(extraction_results['triggers'])}")
        logger.info(f"  - Accounts: {len(extraction_results['accounts'])}")
        logger.info(f"  - Source Sheet: {mag17_sheet}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def generate_validation_report(data):
    """Generate validation report"""
    report = []
    report.append("MAG17 Data Extraction Validation Report")
    report.append("=" * 50)
    report.append(f"Extraction Date: {datetime.now().isoformat()}")
    report.append(f"Analysis Date: 2016-03-23")
    report.append("")
    
    # Summary
    report.append("Extraction Summary:")
    report.append("-" * 20)
    report.append(f"Assets Extracted: {len(data['assets'])}")
    report.append(f"Tranches Extracted: {len(data['tranches'])}")
    report.append(f"Trigger Tests: {len(data['triggers'])}")
    report.append(f"Accounts: {len(data['accounts'])}")
    report.append("")
    
    # Asset analysis
    if data['assets']:
        report.append("Asset Data Analysis:")
        report.append("-" * 20)
        
        # Field coverage
        all_fields = set()
        for asset in data['assets']:
            all_fields.update(asset.keys())
        
        field_counts = {}
        for field in all_fields:
            count = sum(1 for asset in data['assets'] if field in asset and asset[field] is not None)
            field_counts[field] = count
        
        report.append(f"Total unique asset fields: {len(all_fields)}")
        report.append("\nField coverage (top 20):")
        sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        for field, count in sorted_fields:
            pct = (count / len(data['assets'])) * 100
            report.append(f"  {field}: {count} assets ({pct:.1f}%)")
    
    report.append("")
    report.append("Raw Data Samples:")
    report.append("-" * 18)
    for sample in data.get('raw_data_samples', [])[:5]:  # First 5 samples
        non_empty = [x for x in sample['data'] if x is not None][:10]
        report.append(f"Row {sample['row_number']}: {non_empty}")
    
    return "\n".join(report)

def generate_basic_sql(data):
    """Generate basic SQL INSERT statements"""
    sql = []
    sql.append("-- MAG17 CLO Data Migration SQL")
    sql.append("-- Generated: " + datetime.now().isoformat())
    sql.append("")
    
    # Assets table
    if data['assets']:
        sql.append("-- Asset Data")
        sql.append("-- Note: Adjust table schema as needed")
        sql.append("/*")
        sql.append("CREATE TABLE IF NOT EXISTS mag17_assets (")
        sql.append("    asset_id VARCHAR(50) PRIMARY KEY,")
        sql.append("    deal_id VARCHAR(20),")
        sql.append("    source_row INTEGER,")
        sql.append("    data JSON,")
        sql.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        sql.append(");")
        sql.append("*/")
        sql.append("")
        
        for asset in data['assets'][:5]:  # Sample first 5
            asset_json = json.dumps(asset).replace("'", "''")
            sql.append(f"-- INSERT INTO mag17_assets (asset_id, deal_id, source_row, data) VALUES")
            sql.append(f"-- ('{asset['asset_id']}', 'MAG17', {asset.get('source_row', 0)}, '{asset_json}');")
    
    sql.append("")
    sql.append(f"-- Total records to insert:")
    sql.append(f"-- Assets: {len(data['assets'])}")
    sql.append(f"-- Tranches: {len(data['tranches'])}")
    sql.append(f"-- Triggers: {len(data['triggers'])}")
    sql.append(f"-- Accounts: {len(data['accounts'])}")
    
    return "\n".join(sql)

if __name__ == "__main__":
    success = extract_mag17_data()
    exit(0 if success else 1)